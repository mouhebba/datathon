# main.py
from app.db import init_db
from app.agents.scheduler_agent import run_full_pipeline

if __name__ == "__main__":
    # Initialize DB if needed
    init_db()
    # Run a single full pass (you can call this from Streamlit too)
    run_full_pipeline()
    