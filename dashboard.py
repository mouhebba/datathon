# dashboard.py
import streamlit as st

from app.db import init_db
from app.models import get_recent_documents
from app.agents.scheduler_agent import run_full_pipeline

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

    if st.sidebar.button("Run full pipeline now"):
        with st.spinner("Running pipeline..."):
            run_full_pipeline(
                authority_codes=authorities,
                target_language=target_language,
                extra_keywords=extra_keywords,
            )
        st.success("Pipeline finished.")

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

if __name__ == "__main__":
    main()
    