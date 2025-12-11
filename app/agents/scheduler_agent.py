# app/agents/scheduler_agent.py
import time
import schedule

from ..utils.logging_utils import setup_logging
from .extractor import ExtractionAgent
from .translator import TranslationAgent
from .analyzer import KeywordAnalysisAgent
from .notifier import NotificationAgent

logger = setup_logging()

def run_full_pipeline(authority_codes=None, target_language="en", extra_keywords=None, progress_callback=None):
    authority_codes = authority_codes or ["BCL"]
    logger.info(f"[SchedulerAgent] Running full pipeline for authorities: {authority_codes}")

    summary = {
        "new_documents": 0,
        "authorities": {}
    }

    # 1. Extraction
    for code in authority_codes:
        if progress_callback:
            progress_callback("extract_start", {"authority": code})

        e_agent = ExtractionAgent(code)
        new_count = e_agent.run()

        summary["authorities"][code] = new_count
        summary["new_documents"] += new_count

        if progress_callback:
            progress_callback("extract_done", {"authority": code, "new": new_count})

    # 2. Translation
    if progress_callback:
        progress_callback("translate_start")

    t_agent = TranslationAgent(target_language)
    t_agent.run()

    if progress_callback:
        progress_callback("translate_done")

    # 3. Analysis
    if progress_callback:
        progress_callback("analysis_start")

    a_agent = KeywordAnalysisAgent(extra_keywords)
    a_agent.run()

    if progress_callback:
        progress_callback("analysis_done")

    # 4. Notifications
    if progress_callback:
        progress_callback("notify_start")

    n_agent = NotificationAgent()
    n_agent.run()

    if progress_callback:
        progress_callback("notify_done")

    logger.info(f"[SchedulerAgent] Pipeline completed. New docs: {summary['new_documents']}")
    return summary
        