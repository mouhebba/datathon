# dashboard.py
from pathlib import Path
import streamlit as st

from app.db import init_db
from app.models import get_recent_documents
from app.agents.scheduler_agent import run_full_pipeline

LOG_FILE = Path("logs/app.log")

def show_logs():
    st.subheader("📜 Application Logs")

    if not LOG_FILE.exists():
        st.error("Log file not found.")
        return

    with open(LOG_FILE, "r") as f:
        content = f.read()

    st.text_area("Logs", content, height=400)

def main():
    st.set_page_config(page_title="RegulAI Watcher", layout="wide")
    st.title("🧠 RegulAI Watcher – Smart Regulatory Watch Tool")

    init_db()

    st.sidebar.header("Configuration")

    authorities = st.sidebar.multiselect(
        "Authorities to monitor",
        options=["BCL", "ECB", "BDF"],
        default=["BCL"],
    )

    target_language = st.sidebar.selectbox(
        "Target translation language",
        options=["en", "fr", "de"],
        index=0,
    )

    extra_keywords_input = st.sidebar.text_area(
        "Extra keywords (comma-separated)",
        value="ESG, climate risk, governance",
    )
    extra_keywords = [k.strip() for k in extra_keywords_input.split(",") if k.strip()]

    if st.button("Run full pipeline"):
        summary = run_full_pipeline(
            authority_codes=authorities,
            target_language=target_language,
            extra_keywords=extra_keywords,
        )

        if summary["new_documents"] > 0:
            st.success(f"🟢 {summary['new_documents']} new document(s) detected!")
        else:
            st.warning("🟡 No new documents found.")

        with st.expander("Details"):
            for auth, count in summary["authorities"].items():
                st.write(f"**{auth}** → {count} new documents")

    st.header("Recent Documents")
    docs = get_recent_documents(limit=50)

    if not docs:
        st.info("No documents yet. Run the pipeline at least once.")
        return

    for doc in docs:
        with st.expander(f"[{doc['authority']}] {doc['title']}"):
            st.write(f"**URL:** {doc['url']}")
            st.write(f"**File:** `{doc['file_path']}`")
            st.write(f"**Created at:** {doc['created_at']}")
            st.write(f"**Last updated:** {doc['updated_at']}")
            st.write(f"**Matched keywords:** {doc['matched_keywords'] or 'None'}")
            if doc["analysis_summary"]:
                st.markdown("**Summary:**")
                st.write(doc["analysis_summary"])

    # 4️⃣ ⭐ Insert LOGS HERE ⭐
    if st.checkbox("Show logs", value=False):
        show_logs()

if __name__ == "__main__":
    main()
    