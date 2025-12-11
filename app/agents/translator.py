# app/agents/translator.py
from http import client
from pathlib import Path
from typing import Optional
from openai import OpenAI

from ..config import OPENAI_API_KEY
from ..utils.logging_utils import setup_logging
from ..utils.pdf_utils import extract_text_from_pdf
from ..models import get_untranslated_documents, update_document_translation

logger = setup_logging()

class TranslationAgent:
    def __init__(self, target_language: str = "en"):
        if not OPENAI_API_KEY:
            logger.warning("[TranslationAgent] OPENAI_API_KEY is not set!")
        self.target_language = target_language
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def translate_text(self, text: str) -> str:
        """
        Simple translation using OpenAI ChatCompletion (you can refine prompt).
        """
        logger.info("[TranslationAgent] Calling OpenAI for translation...")
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional legal translator. Translate the following regulatory text into {self.target_language}."
                },
                {
                    "role": "user",
                    "content": text[:6000]  # crude truncation to avoid huge prompts
                }
            ],
            temperature=0.1,
        )
        return resp.choices[0].message.content
    
    def translate_keywords_gpt(keywords, target_lang):
        """Translate a list of keywords using GPT."""
        if not keywords:
            return []

        prompt = (
            f"Translate the following keywords into {target_lang}. "
            "Return only a comma-separated list.\n\n"
            f"{', '.join(keywords)}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",   # cheap + fast, change if needed
            messages=[
                {"role": "system", "content": "You are a translation assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0,
        )

        translated = response.choices[0].message.content
        return [k.strip() for k in translated.split(",")]

    def run(self):
        docs = get_untranslated_documents()
        logger.info(f"[TranslationAgent] Documents to translate: {len(docs)}")
        for doc in docs:
            file_path = doc["file_path"]
            text = extract_text_from_pdf(Path(file_path))
            if not text.strip():
                logger.warning(f"[TranslationAgent] Empty text for {file_path}, skipping")
                continue
            translated = self.translate_text(text)
            update_document_translation(doc["id"], translated)
            logger.info(f"[TranslationAgent] Translated document id={doc['id']}")
            