# app/agents/extractor.py

import hashlib
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

from ..config import DOCS_DIR, AUTHORITIES
from ..utils.logging_utils import setup_logging
from ..models import get_document_by_hash, insert_document

logger = setup_logging()

class ExtractionAgent:
    """
    Generic extraction agent for any authority defined in AUTHORITIES.
    Fixes:
    - MissingSchema error (via urljoin)
    - Handles relative URLs
    - Safe filenames
    """

    def __init__(self, authority_code: str):
        if authority_code not in AUTHORITIES:
            raise ValueError(f"Unknown authority: {authority_code}")

        self.code = authority_code
        self.config = AUTHORITIES[authority_code]

        self.docs_page = self.config["docs_page"]
        self.base_url = self.config["base_url"]

    # -----------------------------------------------
    # URL NORMALIZATION FIX (prevents MissingSchema)
    # -----------------------------------------------
    def normalize_url(self, href: str) -> str:
        """
        This fixes all Invalid URL errors.
        - Converts relative URLs to absolute URLs
        - Leaves absolute URLs unchanged
        """
        return urljoin(self.docs_page, href)

    # -----------------------------------------------
    # Extract PDF links from authority public page
    # -----------------------------------------------
    def fetch_document_links(self):
        logger.info(f"[{self.code}] Fetching page: {self.docs_page}")

        response = requests.get(self.docs_page, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links = []

        # Find <a href="...pdf">
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            if href.lower().endswith(".pdf"):
                full_url = self.normalize_url(href)
                title = a.get_text(strip=True) or href.split("/")[-1]

                pdf_links.append({
                    "url": full_url,
                    "title": title
                })

        logger.info(f"[{self.code}] Found {len(pdf_links)} PDF links")
        return pdf_links

    # -----------------------------------------------
    # Safe filename for saving PDFs
    # -----------------------------------------------
    def clean_filename(self, text: str) -> str:
        return "".join(c if c.isalnum() or c in "._- " else "_" for c in text)[:120]

    # -----------------------------------------------
    # Download the PDF
    # -----------------------------------------------
    def download_file(self, url: str, title: str) -> Path:
        logger.info(f"[{self.code}] Downloading: {url}")

        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        # Storage path
        folder = DOCS_DIR / self.code
        folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{self.clean_filename(title)}.pdf"

        pdf_path = folder / filename
        pdf_path.write_bytes(resp.content)

        logger.info(f"[{self.code}] Saved file: {pdf_path}")
        return pdf_path

    # -----------------------------------------------
    # Hash for version detection
    # -----------------------------------------------
    def compute_hash(self, pdf_path: Path) -> str:
        data = pdf_path.read_bytes()
        return hashlib.sha256(data).hexdigest()

    # -----------------------------------------------
    # Main pipeline
    # -----------------------------------------------
    def run(self) -> int:
        """
        Returns number of NEW or UPDATED documents.
        """

        links = self.fetch_document_links()
        new_count = 0

        for item in links:
            url = item["url"]
            title = item["title"]

            # Download
            pdf_path = self.download_file(url, title)

            # Compute file hash
            content_hash = self.compute_hash(pdf_path)

            # Check duplicates
            exists = get_document_by_hash(self.code, content_hash)
            if exists:
                logger.info(f"[{self.code}] Duplicate detected, skipping: {url}")
                continue

            # Insert into DB
            insert_document(
                authority=self.code,
                title=title,
                url=url,
                file_path=str(pdf_path),
                content_hash=content_hash,
            )

            new_count += 1

        logger.info(f"[{self.code}] Total new documents: {new_count}")
        return new_count