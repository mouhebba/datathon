# app/agents/translator.py
from pathlib import Path
from typing import Optional, List

import requests

from ..config import LIBRETRANSLATE_URL
from ..utils.logging_utils import setup_logging
from ..utils.pdf_utils import extract_text_from_pdf
from ..models import get_untranslated_documents, update_document_translation

logger = setup_logging()


def chunk_text(text: str, max_chars: int = 3000) -> List[str]:
    """
    Découpe le texte en morceaux pour éviter d'envoyer des payloads trop gros à l'API.
    On découpe simplement par blocs de caractères.
    """
    chunks = []
    current = 0
    n = len(text)
    while current < n:
        end = min(current + max_chars, n)
        chunks.append(text[current:end])
        current = end
    return chunks


class TranslationAgent:
    def __init__(self, target_language: str = "fr", source_language: str = "en"):
        """
        target_language : langue cible (ex : 'fr')
        source_language : langue source (ex : 'en' ou 'auto')
        """
        if not LIBRETRANSLATE_URL:
            logger.warning("[TranslationAgent] LIBRETRANSLATE_URL is not set!")
        self.target_language = target_language
        self.source_language = source_language
        self.base_url = LIBRETRANSLATE_URL

    def translate_chunk(self, text: str) -> str:
        """
        Appelle l'API LibreTranslate (ou équivalent) sur un seul morceau de texte.
        """
        if not text.strip():
            return ""

        payload = {
            "q": text,
            "source": self.source_language,   # 'auto' possible selon le serveur
            "target": self.target_language,
            "format": "text",
        }

        logger.info("[TranslationAgent] Calling translation API...")
        try:
            resp = requests.post(self.base_url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            translated = data.get("translatedText", "")
            if not translated:
                logger.warning("[TranslationAgent] Empty translation received from API.")
            return translated
        except Exception as e:
            logger.error(f"[TranslationAgent] Error calling translation API: {e}")
            return ""

    def translate_text(self, text: str) -> str:
        """
        Traduit un texte potentiellement long :
        - découpe en morceaux
        - traduit chaque morceau
        - re-concatène
        """
        chunks = chunk_text(text, max_chars=3000)
        translated_chunks = []
        for i, ch in enumerate(chunks):
            logger.info(f"[TranslationAgent] Translating chunk {i+1}/{len(chunks)}")
            translated_chunks.append(self.translate_chunk(ch))
        return "\n".join(translated_chunks)

    def run(self):
        """
        Récupère les documents non traduits, extrait le texte PDF,
        l'envoie à l'API de traduction, et met à jour la base.
        """
        docs = get_untranslated_documents()
        logger.info(f"[TranslationAgent] Documents to translate: {len(docs)}")

        for doc in docs:
            file_path = doc["file_path"]
            logger.info(f"[TranslationAgent] Processing document id={doc['id']} path={file_path}")

            text = extract_text_from_pdf(Path(file_path))
            if not text or not text.strip():
                logger.warning(f"[TranslationAgent] Empty or no text extracted for {file_path}, skipping")
                continue

            translated = self.translate_text(text)
            if not translated.strip():
                logger.warning(f"[TranslationAgent] No translation produced for document id={doc['id']}")
                continue

            update_document_translation(doc["id"], translated)
            logger.info(f"[TranslationAgent] Translated document id={doc['id']}")
