# app/agents/analyzer.py
from typing import List
from openai import OpenAI

from ..config import OPENAI_API_KEY
from ..utils.logging_utils import setup_logging
from ..models import get_unanalysed_documents, update_document_analysis

logger = setup_logging()

DEFAULT_KEYWORDS = [
    "capital requirements",
    "liquidity",
    "Basel",
    "reporting",
    "leverage ratio",
    "credit risk",
    "operational risk",
]

class KeywordAnalysisAgent:
    def __init__(self, extra_keywords: List[str] | None = None):
        if not OPENAI_API_KEY:
            logger.warning("[KeywordAnalysisAgent] OPENAI_API_KEY is not set!")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.keywords = DEFAULT_KEYWORDS + (extra_keywords or [])

    def analyze(self, text: str) -> tuple[str, List[str]]:
        keywords_str = ", ".join(self.keywords)
        prompt = f"""
You are a regulatory expert. Analyze the following translated regulatory document.

1. Provide a concise summary (max 10 lines).
2. Identify which of these keywords are clearly relevant in the document: {keywords_str}.
3. Do NOT hallucinate; only select a keyword if the topic is actually present.

Return JSON with:
- "summary": string
- "matched_keywords": list of strings
"""
        logger.info("[KeywordAnalysisAgent] Calling OpenAI for analysis...")
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You output only valid JSON."},
                {"role": "user", "content": prompt + "\n\nDocument:\n" + text[:12000]},
            ],
            temperature=0.1,
        )
        content = resp.choices[0].message.content
        # simple eval - in a real system you'd use json.loads and validation
        import json
        data = json.loads(content)
        summary = data.get("summary", "")
        matched_keywords = data.get("matched_keywords", [])
        return summary, matched_keywords

    def run(self):
        docs = get_unanalysed_documents()
        logger.info(f"[KeywordAnalysisAgent] Documents to analyse: {len(docs)}")
        for doc in docs:
            text = doc["translated_text"]
            if not text:
                logger.warning(f"[KeywordAnalysisAgent] No translated_text for id={doc['id']}, skipping")
                continue
            summary, matched = self.analyze(text)
            update_document_analysis(doc["id"], summary, matched)
            logger.info(f"[KeywordAnalysisAgent] Analysed document id={doc['id']} with keywords: {matched}")
            