# app/config.py
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
load_dotenv(BASE_DIR / ".env")

# Paths
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "documents"
DB_DIR = BASE_DIR / "db"
LOG_DIR = BASE_DIR / "logs"

DB_PATH = DB_DIR / "metadata.db"
LOG_FILE = LOG_DIR / "app.log"

# Make sure directories exist
for d in [DATA_DIR, DOCS_DIR, DB_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Email settings
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

# Authorities configuration (you’ll adapt the URLs)
AUTHORITIES = {
    "BCL": {
        "code": "BCL",
        "base_url": "https://www.bcl.lu",
        "docs_page": "https://www.bcl.lu/en/Media-and-publications/Legal-powers/index.html",
    },
    "ECB": {
        "code": "ECB",
        "base_url": "https://www.ecb.europa.eu",
        "docs_page": "https://www.ecb.europa.eu/pub/legal/html/index.en.html",
    },
    "BDF": {
        "code": "BDF",
        "base_url": "https://www.banque-france.fr",
        "docs_page": "https://www.banque-france.fr/la-banque-de-france/communiques",
    },
}
