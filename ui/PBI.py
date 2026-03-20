"""
Streamlit UI — Power BI Newsletter Agent.

Launch:  streamlit run ui/PBI.py --server.port 8001
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import streamlit as st

# ── Bootstrap: load local.settings.json before any agent imports ────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

_settings_path = os.path.join(_ROOT, "local.settings.json")
if os.path.exists(_settings_path):
    with open(_settings_path) as f:
        _settings = json.load(f)
    for k, v in _settings.get("Values", {}).items():
        if v:
            os.environ.setdefault(k, v)

# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Power BI Newsletter Agent",
    page_icon="⚡",
    layout="wide",
)

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚡ Power BI Newsletter Agent")
    st.markdown("---")
    st.caption(f"Date: {datetime.now().strftime('%B %d, %Y')}")

# ── Agent description ──────────────────────────────────────────────
st.markdown("""
### ⚡ Power BI Newsletter Agent

Compiles a **monthly HTML newsletter** focused on **Power BI**.

**Sections:**
1. **Hot Topics** — Key themes from the Hot Topics folder
2. **TSG (Troubleshooting Guides)** — New/updated wiki pages under `/Fabric Experiences/Power BI`
3. **Fabric Made EEE-z** — New feature readiness pages (NF-PBI filter)
4. **CSS Feedback Items** — CSS feedback work items grouped by category
5. **CSS Taxonomy Changes** — Taxonomy change requests from CSSTaxonomyChange org
6. **Component V-Team** — Power BI V-Team ownership table

Uses product-specific config (POWERBI_* env vars) while sharing the same tool logic.
""")

st.markdown("---")

# ── Section prompts ─────────────────────────────────────────────────
SECTION_PROMPTS = {
    "hot_topics": (
        "Please compile ONLY the **Hot Topics** section of the newsletter. "
        "Call get_hot_topics_files, summarize the content, and return a "
        "standalone HTML fragment for this section. Do NOT call any other tools."
    ),
    "tsg": (
        "Please compile ONLY the **TSG (Troubleshooting Guides)** section. "
        "Call get_wiki_commits with the configured folder and year/month for "
        "the previous calendar month (e.g. year=2026, month=2 for February), "
        "then render the Component | Page table as an HTML fragment. "
        "Do NOT call any other tools."
    ),
    "eeez": (
        "Please compile ONLY the **Fabric Made EEE-z** section. "
        "Call get_eeez_features, render the features table as an HTML fragment. "
        "Do NOT call any other tools."
    ),
    "css_feedback": (
        "Please compile ONLY the **CSS Feedback Items** section. "
        "Call get_ado_query_results with the CSS Feedback query_id, org_url, "
        "and project, then render the results as an HTML table fragment. "
        "Do NOT call any other tools."
    ),
    "css_taxonomy": (
        "Please compile ONLY the **CSS Taxonomy Changes** section. "
        "Call get_ado_query_results with the CSS Taxonomy query_id, org_url, "
        "and project, then summarize the changes as an HTML fragment. "
        "Do NOT call any other tools."
    ),
    "vteam": (
        "Please compile ONLY the **Component V-Team** section. "
        "Call get_static_content with section_name 'vteam', convert the "
        "markdown to a well-formatted HTML fragment with the ownership table "
        "and thank-you list. Do NOT call any other tools."
    ),
}

# ── ADO & Wiki Configuration ───────────────────────────────────────
with st.expander("⚙️ ADO & Wiki Configuration", expanded=True):
    st.caption("Override defaults for this run. Leave blank to use environment defaults.")

    _def_wiki = os.environ.get(
        "POWERBI_TSG_WIKI_FOLDER",
        os.environ.get("TSG_WIKI_FOLDER", "/Fabric Experiences/Power BI"))
    _def_eeez = os.environ.get(
        "POWERBI_EEEZ_TITLE_FILTER",
        os.environ.get("EEEZ_TITLE_FILTER", "NF-PBI"))
    _def_fb_qid = os.environ.get(
        "POWERBI_CSS_FEEDBACK_QUERY_ID",
        os.environ.get("CSS_FEEDBACK_QUERY_ID", ""))
    _def_tax_qid = os.environ.get(
        "POWERBI_CSS_TAXONOMY_QUERY_ID",
        os.environ.get("CSS_TAXONOMY_QUERY_ID", ""))
    _def_email = os.environ.get(
        "POWERBI_EMAIL_RECIPIENTS",
        os.environ.get("EMAIL_RECIPIENTS", ""))

    col1, col2 = st.columns(2)
    with col1:
        cfg_wiki_folder = st.text_input(
            "TSG Wiki Folder", value=_def_wiki,
            help="Wiki folder path for TSG commits, e.g. '/Fabric Experiences/Power BI'")
        cfg_feedback_qid = st.text_input(
            "CSS Feedback Query ID", value=_def_fb_qid,
            help="GUID of the saved ADO query for CSS Feedback items")
    with col2:
        cfg_eeez_filter = st.text_input(
            "EEE-z Title Filter", value=_def_eeez,
            help="Substring to filter feature readiness pages, e.g. 'NF-PBI'")
        cfg_taxonomy_qid = st.text_input(
            "CSS Taxonomy Query ID", value=_def_tax_qid,
            help="GUID of the saved ADO query for CSS Taxonomy changes")
    cfg_email_recipients = st.text_input(
        "📧 To List (Email Recipients)", value=_def_email,
        help="Comma-separated email addresses for newsletter delivery")
    cfg_hot_topics = st.text_area(
        "🔥 Hot Topics", height=120,
        placeholder="Paste hot-topics content here. Leave empty to read from configured folder.",
        help="If provided, this content will be used instead of reading files from the Hot Topics folder.")
    cfg_vteam = st.text_area(
        "👥 Component V-Team", height=120,
        placeholder="Paste V-Team markdown here. Leave empty to read from configured file.",
        help="If provided, this content will be used instead of reading from the V-Team markdown file.")

# ── Section & Email options ─────────────────────────────────────────
col_sec, col_email = st.columns([2, 1])
with col_sec:
    section = st.selectbox(
        "Section (optional)",
        ["Full Newsletter", "hot_topics", "tsg", "eeez", "css_feedback", "css_taxonomy", "vteam"],
    )
with col_email:
    st.write("")  # vertical spacer
    send_email = st.checkbox("📧 Send email after generation", value=False)

# Custom prompt override
custom_prompt = st.text_area(
    "✏️ Custom prompt (leave empty for default)",
    height=80,
    placeholder="e.g. 'Focus only on Power BI items this month'",
)

# ── Run button ──────────────────────────────────────────────────────

if st.button("🚀 Run Power BI Newsletter Agent", type="primary", use_container_width=True):

    with st.status("Running agent...", expanded=True) as status:

        # Determine prompt
        if custom_prompt.strip():
            prompt = custom_prompt.strip()
        elif section and section != "Full Newsletter":
            prompt = SECTION_PROMPTS[section]
        else:
            prompt = None  # use default

        # ── Apply ADO / Wiki config overrides ────────────────────────
        from powerbi import config as _agent_cfg

        if cfg_wiki_folder:
            _agent_cfg.TSG_WIKI_FOLDER = cfg_wiki_folder
        if cfg_eeez_filter:
            _agent_cfg.EEEZ_TITLE_FILTER = cfg_eeez_filter
        if cfg_feedback_qid:
            _agent_cfg.CSS_FEEDBACK_QUERY_ID = cfg_feedback_qid
        if cfg_taxonomy_qid:
            _agent_cfg.CSS_TAXONOMY_QUERY_ID = cfg_taxonomy_qid
        if cfg_email_recipients:
            _agent_cfg.EMAIL_RECIPIENTS = cfg_email_recipients

        # Build tool-parameter override instructions for the user prompt
        _overrides = []
        if cfg_wiki_folder:
            _overrides.append(
                f"- For TSG section: call get_wiki_commits with folder_filter='{cfg_wiki_folder}'")
        if cfg_feedback_qid:
            _overrides.append(
                f"- For CSS Feedback: call get_ado_query_results with query_id='{cfg_feedback_qid}'")
        if cfg_taxonomy_qid:
            _overrides.append(
                f"- For CSS Taxonomy: call get_ado_query_results with query_id='{cfg_taxonomy_qid}'")
        if cfg_eeez_filter:
            _overrides.append(
                f"- For Fabric Made EEE-z: call get_eeez_features with title_filter='{cfg_eeez_filter}'")
        if cfg_hot_topics:
            _overrides.append(
                "- For Hot Topics: Do NOT call get_hot_topics_files. "
                "Use the following content as the Hot Topics data instead:\n"
                f"```\n{cfg_hot_topics}\n```")
        if cfg_vteam:
            _overrides.append(
                "- For Component V-Team: Do NOT call get_static_content. "
                "Use the following markdown as the V-Team content instead:\n"
                f"```\n{cfg_vteam}\n```")
        if _overrides:
            _override_block = (
                "\n\nIMPORTANT — Use these exact parameter values when calling tools:\n"
                + "\n".join(_overrides)
            )
            if prompt:
                prompt += _override_block
            else:
                prompt = "Generate the full newsletter." + _override_block

        # Run the agent
        try:
            st.write("⏳ Starting Power BI Newsletter agent...")
            from powerbi.agent import run_powerbi_newsletter_agent
            result = run_powerbi_newsletter_agent(user_prompt=prompt)
            label = section if section != "Full Newsletter" else "Power BI Newsletter"

            status.update(label=f"✅ {label} — Done!", state="complete", expanded=False)

        except Exception as e:
            status.update(label="❌ Agent failed", state="error")
            st.error(f"Error: {e}")
            st.stop()

    # ── Display result ──────────────────────────────────────────────
    st.markdown("### 📄 Output")

    tab_preview, tab_html = st.tabs(["Preview", "Raw HTML"])

    with tab_preview:
        st.components.v1.html(result, height=800, scrolling=True)

    with tab_html:
        st.code(result, language="html")

    # ── Save to file ────────────────────────────────────────────────
    out_dir = os.path.join(_ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)
    suffix = f"_{section}" if section and section != "Full Newsletter" else ""
    out_path = os.path.join(out_dir, f"powerbi_output{suffix}.html")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    st.success(f"Saved to `{out_path}`")

    # ── Download button ─────────────────────────────────────────────
    st.download_button(
        label="⬇️ Download HTML",
        data=result,
        file_name=os.path.basename(out_path),
        mime="text/html",
    )

    # ── Optional email ──────────────────────────────────────────────
    if send_email:
        st.write("📧 Sending email...")
        try:
            from powerbi import config as pbi_cfg
            from powerbi.tools import send_email as pbi_send
            _to = cfg_email_recipients or pbi_cfg.EMAIL_RECIPIENTS
            subj = f"{pbi_cfg.EMAIL_SUBJECT_PREFIX} - {label}"
            pbi_send(subject=subj, html_body=result, to_recipients=_to)
            st.success(f"Email sent to {_to}")
        except Exception as e:
            st.error(f"Email failed: {e}")
