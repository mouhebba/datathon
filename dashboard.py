from pathlib import Path
import streamlit as st

from app.db import init_db
from app.models import get_recent_documents
from app.agents.scheduler_agent import run_full_pipeline
from app.utils.translation_utils import translate_keywords_gpt

LOG_FILE = Path("logs/app.log")

def show_pipeline_progress():
    status = st.status("Running pipeline...", expanded=True)

    def cb(event, data=None):
        if event == "extract_start":
            status.write(f"🟦 **Agent 1 – Extractor** starting for `{data['authority']}`…")
        elif event == "extract_done":
            status.write(f"✔ **Extractor finished** → {data['new']} new document(s)")
        elif event == "translate_start":
            status.write(f"🟨 **Agent 2 – Translator** translating documents…")
        elif event == "translate_done":
            status.write(f"✔ **Translator finished**")
        elif event == "analysis_start":
            status.write(f"🟧 **Agent 3 – Analysis** running keyword detection…")
        elif event == "analysis_done":
            status.write(f"✔ **Analysis completed**")
        elif event == "notify_start":
            status.write(f"🟪 **Agent 4 – Notification** sending emails…")
        elif event == "notify_done":
            status.write(f"✔ **Notifications sent**")

    return cb, status


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

    # --------------------------
    # LEFT SIDEBAR
    # --------------------------
    # Logo at top
    st.sidebar.image("logo.jpeg", caption="RegulAI Watcher", width=180)
    st.sidebar.markdown("---")

    st.sidebar.header("Configuration")

    # 🌍 Languages with labels
    languages = {
        "English 🇬🇧": "en",
        "French 🇫🇷": "fr",
        "German 🇩🇪": "de",
        "Romanian 🇷🇴": "ro",
    }

    lang_label = st.sidebar.selectbox(
        "Target translation language",
        options=list(languages.keys()),
        index=0,
    )
    target_language = languages[lang_label]

    # Authorities
    authorities = st.sidebar.multiselect(
        "Authorities to monitor",
        options=["BCL", "ECB", "BDF"],
        default=["BCL"],
    )

    # Extra keywords
    extra_keywords_input = st.sidebar.text_area(
        "Extra keywords (comma-separated)",
        value="ESG, climate risk, governance",
    )
    extra_keywords = [k.strip() for k in extra_keywords_input.split(",") if k.strip()]

    # --------------------------
    # Sidebar Buttons
    # --------------------------
    if st.sidebar.button("🚀 Run full pipeline"):
        cb, status = show_pipeline_progress()

        summary = run_full_pipeline(
            authority_codes=authorities,
            target_language=target_language,
            extra_keywords=extra_keywords,
            progress_callback=cb,
        )

        status.update(label="Pipeline finished!", state="complete")

    # Keep translations in session state
    if "translated_keywords" not in st.session_state:
        st.session_state["translated_keywords"] = {}

    # GPT keyword translation
    if st.sidebar.button("🔠 Translate matched keywords (GPT)"):
        docs = get_recent_documents(limit=50)

        with st.spinner(f"Translating keywords to '{target_language}'..."):
            for doc in docs:
                if not doc["matched_keywords"]:
                    continue

                original_kw = [k.strip() for k in doc["matched_keywords"].split(",") if k.strip()]
                translated_kw = translate_keywords_gpt(original_kw, target_language)

                st.session_state["translated_keywords"][doc["id"]] = translated_kw

        st.success("Translation completed!")
        st.rerun()  # <-- 🟩 Forces UI update

    # --------------------------
    # MAIN CONTENT
    # --------------------------
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

            # Show GPT translations
            if doc["id"] in st.session_state["translated_keywords"]:
                t = st.session_state["translated_keywords"][doc["id"]]
                st.write(f"**Translated keywords ({target_language}):** {', '.join(t)}")

            if doc["analysis_summary"]:
                st.markdown("**Summary:**")
                st.write(doc["analysis_summary"])

    # Logs toggle
    if st.checkbox("Show logs", value=False):
        show_logs()


if __name__ == "__main__":
    main()
