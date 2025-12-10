# app/agents/extractor.py
import hashlib
from pathlib import Path
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from ..config import DOCS_DIR, AUTHORITIES
from ..utils.logging_utils import setup_logging
from ..models import get_document_by_hash, insert_document

logger = setup_logging()

class ExtractionAgent:
    def __init__(self, authority_code: str):
        if authority_code not in AUTHORITIES:
            raise ValueError(f"Unknown authority: {authority_code}")
        self.config = AUTHORITIES[authority_code]
        self.authority_code = authority_code

    def fetch_document_links(self) -> List[Dict]:
        """
        Very simplified example:
        - GET the docs_page
        - Find <a> links ending with .pdf
        You will adapt this to the real structure of BCL/ECB/BdF.
        """
        url = self.config["docs_page"]
        logger.info(f"[ExtractionAgent] Fetching page: {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(".pdf"):
                full_url = href
                if full_url.startswith("/"):
                    full_url = self.config["base_url"].rstrip("/") + href
                title = a.get_text(strip=True) or "Untitled"
                links.append({"url": full_url, "title": title})
        logger.info(f"[ExtractionAgent] Found {len(links)} PDF links")
        return links

    def download_file(self, url: str, title: str) -> Path:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        authority_dir = DOCS_DIR / self.authority_code
        authority_dir.mkdir(parents=True, exist_ok=True)

        # simple filename
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in "._-" else "_" for c in title)[:80]
        filename = f"{timestamp}_{safe_title}.pdf"
        pdf_path = authority_dir / filename
        pdf_path.write_bytes(resp.content)
        logger.info(f"[ExtractionAgent] Downloaded {url} -> {pdf_path}")
        return pdf_path

    def compute_hash(self, pdf_path: Path) -> str:
        data = pdf_path.read_bytes()
        return hashlib.sha256(data).hexdigest()

    def run(self) -> int:
        """
        Returns number of NEW documents inserted (new or changed).
        """
        links = self.fetch_document_links()
        new_count = 0
        for link in links:
            pdf_path = self.download_file(link["url"], link["title"])
            content_hash = self.compute_hash(pdf_path)

            existing = get_document_by_hash(self.authority_code, content_hash)
            if existing:
                logger.info(f"[ExtractionAgent] Existing document (hash match), skipping: {link['url']}")
                continue

            insert_document(
                authority=self.authority_code,
                title=link["title"],
                url=link["url"],
                file_path=str(pdf_path),
                content_hash=content_hash,
            )
            new_count += 1

        logger.info(f"[ExtractionAgent] New or changed documents: {new_count}")
        return new_count
    