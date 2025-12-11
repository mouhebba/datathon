# app/agents/extractor.py

import hashlib
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..config import DOCS_DIR, AUTHORITIES
from ..models import get_document_by_hash, insert_document
from ..utils.logging_utils import setup_logging

logger = setup_logging()

class ExtractionAgent:

    def __init__(self, authority_code: str):
        if authority_code not in AUTHORITIES:
            raise ValueError(f"Unknown authority: {authority_code}")
        self.code = authority_code
        self.config = AUTHORITIES[authority_code]
        self.docs_page = self.config["docs_page"]

    def normalize_url(self, href: str) -> str:
        return urljoin(self.docs_page, href)

    def fetch_document_links(self):
        logger.info(f"[{self.code}] Fetching page: {self.docs_page}")
        html = requests.get(self.docs_page, timeout=30)
        html.raise_for_status()
        soup = BeautifulSoup(html.text, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            if not href.lower().endswith(".pdf"):
                continue

            links.append({
                "url": self.normalize_url(href),
                "title": a.get_text(strip=True) or href.split("/")[-1],
            })

        logger.info(f"[{self.code}] Found {len(links)} PDF links")
        return links

    def get_file_bytes(self, url: str) -> bytes:
        logger.info(f"[{self.code}] Downloading for hash check: {url}")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content

    def compute_hash(self, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    def save_file(self, file_bytes: bytes, filename: str) -> Path:
        folder = DOCS_DIR / self.code
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / filename
        path.write_bytes(file_bytes)
        return path

    # -----------------------------------------------------------
    # ✅ FINAL FIXED PIPELINE — IDENTITY BASED ON HASH (perfect)
    # -----------------------------------------------------------
    def run(self) -> int:
        links = self.fetch_document_links()
        new_count = 0

        for item in links:
            url = item["url"]
            title = item["title"]

            # Step 1 — Download file into memory
            file_bytes = self.get_file_bytes(url)

            # Step 2 — Compute hash before saving
            content_hash = self.compute_hash(file_bytes)

            # Step 3 — Check DB for existing version
            existing = get_document_by_hash(self.code, content_hash)
            if existing:
                logger.info(f"[{self.code}] Duplicate detected, skipping: {url}")
                continue

            # Step 4 — Save file using HASH-BASED filename
            clean_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in title)[:60]
            filename = f"{content_hash}_{clean_title}.pdf"
            pdf_path = self.save_file(file_bytes, filename)

            # Step 5 — Insert into DB
            insert_document(
                authority=self.code,
                title=title,
                url=url,
                file_path=str(pdf_path),
                content_hash=content_hash,
            )

            logger.info(f"[{self.code}] NEW document added: {pdf_path}")
            new_count += 1

        logger.info(f"[{self.code}] Total NEW documents this run: {new_count}")
        return new_count