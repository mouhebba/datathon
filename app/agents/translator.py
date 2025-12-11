# app/agents/translator.py
from pathlib import Path
from typing import List

from deep_translator import GoogleTranslator

from ..utils.logging_utils import setup_logging
from ..utils.pdf_utils import extract_text_from_pdf
from ..models import get_untranslated_documents, update_document_translation

logger = setup_logging()


def chunk_text(text: str, max_chars: int = 3000) -> List[str]:
    chunks = []
    current = 0
    n = len(text)
    while current < n:
        end = min(current + max_chars, n)
        chunks.append(text[current:end])
        current = end
    return chunks


class TranslationAgent:
    def __init__(self, target_language="en", source_language="auto"):
        self.target_language = target_language
        self.source_language = source_language
        self.translator = GoogleTranslator(
            source=self.source_language,
            target=self.target_language
        )

    def translate_chunk(self, text: str) -> str:
        if not text.strip():
            return ""
        try:
            logger.info("[TranslationAgent] Calling GoogleTranslator...")
            return self.translator.translate(text)
        except Exception as e:
            logger.error(f"[TranslationAgent] Error translating chunk: {e}")
            return ""

    def translate_text(self, text: str) -> str:
        chunks = chunk_text(text, max_chars=2000)
        translated_chunks = []
        for i, ch in enumerate(chunks):
            logger.info(f"[TranslationAgent] Translating chunk {i+1}/{len(chunks)}")
            translated_chunks.append(self.translate_chunk(ch))
        return "\n\n".join(translated_chunks)

    def run(self):
        docs = get_untranslated_documents()
        logger.info(f"[TranslationAgent] Documents to translate: {len(docs)}")

        for doc in docs:
            file_path = Path(doc["file_path"])
            logger.info(f"[TranslationAgent] Processing document id={doc['id']} path={file_path}")

            if not file_path.exists():
                logger.error(f"[TranslationAgent] File not found: {file_path}")
                continue

            text = extract_text_from_pdf(file_path)
            if not text.strip():
                logger.warning(f"[TranslationAgent] No text extracted from {file_path}")
                continue

            translated = self.translate_text(text)
            if not translated.strip():
                logger.warning(f"[TranslationAgent] Empty translation for {doc['id']}")
                continue

            update_document_translation(doc["id"], translated)
            logger.info(f"[TranslationAgent] Translated document id={doc['id']}")
