# app/agents/scheduler_agent.py
import time
import schedule

from ..utils.logging_utils import setup_logging
from .extractor import ExtractionAgent
from .translator import TranslationAgent
from .analyzer import KeywordAnalysisAgent
from .notifier import NotificationAgent

logger = setup_logging()

def run_full_pipeline(authority_codes=None, target_language="en", extra_keywords=None):
    # authority_codes = authority_codes or ["BCL", "ECB"]
    authority_codes = authority_codes or ["BCL"]
    logger.info(f"[SchedulerAgent] Running full pipeline for authorities: {authority_codes}")

    # 1. Extraction
    total_new = 0
    for code in authority_codes:
        agent = ExtractionAgent(code)
        new_count = agent.run()
        total_new += new_count

    # 2. Translation
    t_agent = TranslationAgent(target_language=target_language)
    t_agent.run()

    # 3. Analysis
    a_agent = KeywordAnalysisAgent(extra_keywords=extra_keywords)
    a_agent.run()

    # 4. Notifications
    n_agent = NotificationAgent()
    n_agent.run()

    logger.info(f"[SchedulerAgent] Full pipeline done. New docs: {total_new}")

def start_scheduler():
    """
    Example: run every day at 10:00.
    """
    schedule.every().day.at("10:00").do(run_full_pipeline)

    logger.info("[SchedulerAgent] Scheduler started, running in loop...")
    while True:
        schedule.run_pending()
        time.sleep(30)
        