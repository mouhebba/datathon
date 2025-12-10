# app/agents/notifier.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import (
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PORT,
    EMAIL_USERNAME,
    EMAIL_PASSWORD,
    EMAIL_FROM,
    EMAIL_TO,
)
from ..utils.logging_utils import setup_logging
from ..models import get_unnotified_documents, mark_document_notified

logger = setup_logging()

class NotificationAgent:
    def __init__(self):
        if not EMAIL_SMTP_HOST:
            logger.warning("[NotificationAgent] Email SMTP host not configured")

    def build_email_body(self, doc) -> str:
        return f"""
Hello,

A new or updated regulatory document has been detected.

Authority: {doc['authority']}
Title: {doc['title']}
URL: {doc['url']}

Matched keywords: {doc['matched_keywords']}

Summary:
{doc['analysis_summary']}

Best regards,
RegulAI Watcher
"""

    def send_email(self, subject: str, body: str):
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)

    def run(self):
        docs = get_unnotified_documents()
        logger.info(f"[NotificationAgent] Documents to notify: {len(docs)}")
        for doc in docs:
            subject = f"[RegulAI] New regulatory update from {doc['authority']}"
            body = self.build_email_body(doc)
            self.send_email(subject, body)
            mark_document_notified(doc["id"])
            logger.info(f"[NotificationAgent] Notification sent for id={doc['id']}")
            