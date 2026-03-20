"""
Streamlit UI — DnAI Newsletter Agent.

Launch:  streamlit run ui/app.py --server.port 8000
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
    page_title="DnAI Newsletter Agent",
    page_icon="📬",
    layout="wide",
)

# ── Custom theme ────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Main background ── */
[data-testid="stAppViewContainer"] {
    background: #f8fafc;
}
[data-testid="stHeader"] {
    background: #f8fafc;
}
[data-testid="stMain"] {
    background: #f8fafc;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1e3a5f;
    border-right: none;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stCaption * {
    color: #94a3b8 !important;
}

/* ── Expander: same background as page ── */
[data-testid="stExpander"] {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px;
    box-shadow: none;
}
[data-testid="stExpander"] details {
    background: #f8fafc !important;
    border: none !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] details > summary {
    background: #f8fafc !important;
    color: #1e293b !important;
    font-weight: 600;
    border-radius: 10px;
}
[data-testid="stExpanderToggleIcon"] {
    color: #1e293b !important;
}
details[data-testid="stExpander"] > summary {
    background: #f8fafc !important;
}
[data-testid="stExpander"] summary {
    color: #1e293b !important;
    font-weight: 600;
}
[data-testid="stExpander"] summary:hover {
    color: #2563eb !important;
}

/* ── Labels — force all form labels visible ── */
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
[data-testid="stCheckbox"] label,
[data-testid="stTextInput"] label p,
[data-testid="stTextArea"] label p,
[data-testid="stSelectbox"] label p,
[data-testid="stCheckbox"] label p,
.stTextInput label, .stTextArea label, .stSelectbox label, .stCheckbox label,
.stTextInput label p, .stTextArea label p, .stSelectbox label p, .stCheckbox label p,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
[data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"],
[data-testid="stExpander"] p,
[data-testid="stExpander"] span {
    color: #1e293b !important;
    font-weight: 500 !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    color: #1e293b !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    background: #ffffff !important;
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    color: #1e293b !important;
}

/* ── Primary button ── */
[data-testid="stBaseButton-primary"] {
    background: #2563eb !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: #ffffff !important;
    padding: 0.5rem 1.5rem !important;
    transition: background 0.15s, box-shadow 0.15s;
}
[data-testid="stBaseButton-primary"]:hover {
    background: #1d4ed8 !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] button {
    color: #64748b !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #2563eb !important;
    border-bottom: 2px solid #2563eb;
    font-weight: 600;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 8px;
}

/* ── Status widget ── */
[data-testid="stStatusWidget"] {
    background: #ffffff;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}

/* ── Dividers ── */
hr {
    border-color: #e2e8f0 !important;
}

/* ── Headings ── */
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 {
    color: #1e293b !important;
    font-weight: 700 !important;
}
[data-testid="stAppViewContainer"] .stCaption,
[data-testid="stAppViewContainer"] .stCaption p {
    color: #64748b !important;
}

/* ── Checkbox label & icon ── */
[data-testid="stCheckbox"] label span,
[data-testid="stCheckbox"] label p,
[data-testid="stCheckbox"] label div,
[data-testid="stCheckbox"] label span[data-testid="stMarkdownContainer"],
[data-testid="stCheckbox"] label span[data-testid="stMarkdownContainer"] p,
[data-testid="stCheckbox"] label > span:last-child,
[data-testid="stCheckbox"] label > span:last-child p {
    color: #1e293b !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* ── Help text tooltips ── */
[data-testid="stTooltipIcon"] {
    color: #64748b !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background: #f1f5f9 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    color: #334155 !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📬 DnAI Newsletter Agent")
    st.markdown("---")
    st.caption(f"Date: {datetime.now().strftime('%B %d, %Y')}")

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

# ── Main area ───────────────────────────────────────────────────────
st.markdown("### 📬 DnAI Newsletter Agent")
st.caption("Compiles a monthly HTML newsletter with configurable ADO queries, wiki folders, and content sources.")
st.markdown("---")

# ── Configuration ──────────────────────────────────────────────────
with st.expander("⚙️ Configuration", expanded=True):
    _def_wiki = os.environ.get("DNAI_TSG_WIKI_FOLDER",
                               os.environ.get("TSG_WIKI_FOLDER", "/Fabric Experiences/Power BI"))
    _def_eeez = os.environ.get("DNAI_EEEZ_TITLE_FILTER",
                               os.environ.get("EEEZ_TITLE_FILTER", "NF-PBI"))
    _def_fb_qid = os.environ.get("DNAI_CSS_FEEDBACK_QUERY_ID",
                                 os.environ.get("CSS_FEEDBACK_QUERY_ID", ""))
    _def_tax_qid = os.environ.get("DNAI_CSS_TAXONOMY_QUERY_ID",
                                  os.environ.get("CSS_TAXONOMY_QUERY_ID", ""))
    _def_email = os.environ.get("DNAI_EMAIL_RECIPIENTS",
                                os.environ.get("EMAIL_RECIPIENTS", ""))

    col1, col2 = st.columns(2)
    with col1:
        cfg_wiki_folder = st.text_input("TSG Wiki Folder", value=_def_wiki,
            help="Wiki folder path for TSG commits, e.g. '/Fabric Experiences/Power BI'")
        cfg_feedback_qid = st.text_input("CSS Feedback Query ID", value=_def_fb_qid,
            help="GUID of the saved ADO query for CSS Feedback items")
    with col2:
        cfg_eeez_filter = st.text_input("EEE-z Title Filter", value=_def_eeez,
            help="Substring to filter feature readiness pages, e.g. 'NF-PBI'")
        cfg_taxonomy_qid = st.text_input("CSS Taxonomy Query ID", value=_def_tax_qid,
            help="GUID of the saved ADO query for CSS Taxonomy changes")

    cfg_email_recipients = st.text_input("📧 To List (Email Recipients)", value=_def_email,
        help="Comma-separated email addresses for newsletter delivery")
    cfg_hot_topics = st.text_area("🔥 Hot Topics", height=100,
        placeholder="Paste hot-topics content here. Leave empty to read from configured folder.")
    cfg_vteam = st.text_area("👥 Component V-Team", height=100,
        placeholder="Paste V-Team markdown here. Leave empty to read from configured file.")

# ── Section checkboxes ───────────────────────────────────────────────
st.markdown("#### 📋 Select Sections to Include")
SECTION_LABELS = {
    "hot_topics": "🔥 Hot Topics",
    "tsg": "📖 TSG (Troubleshooting Guides)",
    "eeez": "⚡ Fabric Made EEE-z",
    "css_feedback": "💬 CSS Feedback Items",
    "css_taxonomy": "🏷️ CSS Taxonomy Changes",
    "vteam": "👥 Component V-Team",
}

col_chk1, col_chk2, col_chk3 = st.columns(3)
with col_chk1:
    sel_hot_topics = st.checkbox(SECTION_LABELS["hot_topics"], value=True)
    sel_tsg = st.checkbox(SECTION_LABELS["tsg"], value=True)
with col_chk2:
    sel_eeez = st.checkbox(SECTION_LABELS["eeez"], value=True)
    sel_css_feedback = st.checkbox(SECTION_LABELS["css_feedback"], value=True)
with col_chk3:
    sel_css_taxonomy = st.checkbox(SECTION_LABELS["css_taxonomy"], value=True)
    sel_vteam = st.checkbox(SECTION_LABELS["vteam"], value=True)

_section_selection = {
    "hot_topics": sel_hot_topics,
    "tsg": sel_tsg,
    "eeez": sel_eeez,
    "css_feedback": sel_css_feedback,
    "css_taxonomy": sel_css_taxonomy,
    "vteam": sel_vteam,
}
selected_sections = [k for k, v in _section_selection.items() if v]

col_email_opt, _ = st.columns([1, 2])
with col_email_opt:
    send_email = st.checkbox("📧 Send email after generation", value=False)

custom_prompt = st.text_area("✏️ Custom prompt (optional)", height=60,
    placeholder="e.g. 'Focus only on Power BI items this month'")

# ── Run ─────────────────────────────────────────────────────────────
if st.button("🚀 Run Newsletter Agent", type="primary", use_container_width=True):

    if not selected_sections and not custom_prompt.strip():
        st.warning("Please select at least one section or enter a custom prompt.")
        st.stop()

    with st.status("Running agent...", expanded=True) as status:

        # Determine prompt from selected sections
        if custom_prompt.strip():
            prompt = custom_prompt.strip()
        elif len(selected_sections) == 1:
            prompt = SECTION_PROMPTS[selected_sections[0]]
        elif selected_sections:
            _parts = [SECTION_PROMPTS[s] for s in selected_sections]
            prompt = (
                "Generate the newsletter with ONLY the following sections "
                "(in the order listed). Skip all other sections.\n\n"
                + "\n\n".join(
                    f"--- Section: {SECTION_LABELS[s]} ---\n{SECTION_PROMPTS[s]}"
                    for s in selected_sections
                )
            )
        else:
            prompt = None

        # Patch config
        from dnai import config as _cfg
        if cfg_wiki_folder:
            _cfg.TSG_WIKI_FOLDER = cfg_wiki_folder
        if cfg_eeez_filter:
            _cfg.EEEZ_TITLE_FILTER = cfg_eeez_filter
        if cfg_feedback_qid:
            _cfg.CSS_FEEDBACK_QUERY_ID = cfg_feedback_qid
        if cfg_taxonomy_qid:
            _cfg.CSS_TAXONOMY_QUERY_ID = cfg_taxonomy_qid
        if cfg_email_recipients:
            _cfg.EMAIL_RECIPIENTS = cfg_email_recipients

        # Build override instructions
        _overrides = []
        if cfg_wiki_folder:
            _overrides.append(f"- For TSG section: call get_wiki_commits with folder_filter='{cfg_wiki_folder}'")
        if cfg_feedback_qid:
            _overrides.append(f"- For CSS Feedback: call get_ado_query_results with query_id='{cfg_feedback_qid}'")
        if cfg_taxonomy_qid:
            _overrides.append(f"- For CSS Taxonomy: call get_ado_query_results with query_id='{cfg_taxonomy_qid}'")
        if cfg_eeez_filter:
            _overrides.append(f"- For Fabric Made EEE-z: call get_eeez_features with title_filter='{cfg_eeez_filter}'")
        if cfg_hot_topics:
            _overrides.append(
                "- For Hot Topics: Do NOT call get_hot_topics_files. "
                f"Use the following content instead:\n```\n{cfg_hot_topics}\n```")
        if cfg_vteam:
            _overrides.append(
                "- For Component V-Team: Do NOT call get_static_content. "
                f"Use the following markdown instead:\n```\n{cfg_vteam}\n```")
        if _overrides:
            _block = "\n\nIMPORTANT — Use these exact parameter values when calling tools:\n" + "\n".join(_overrides)
            prompt = (prompt or "Generate the full newsletter.") + _block

        # Run agent
        try:
            st.write("⏳ Running DnAI Newsletter agent...")
            from dnai.agent import run_dnai_newsletter_agent
            result = run_dnai_newsletter_agent(user_prompt=prompt)
            label = ", ".join(SECTION_LABELS[s] for s in selected_sections) if len(selected_sections) < len(SECTION_LABELS) else "DnAI Newsletter"
            status.update(label=f"✅ {label} — Done!", state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ Agent failed", state="error")
            st.error(f"Error: {e}")
            st.stop()

    # ── Output ──────────────────────────────────────────────────────
    st.markdown("### 📄 Output")
    tab_preview, tab_html = st.tabs(["Preview", "Raw HTML"])
    with tab_preview:
        st.components.v1.html(result, height=800, scrolling=True)
    with tab_html:
        st.code(result, language="html")

    # Save
    out_dir = os.path.join(_ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)
    suffix = f"_{'_'.join(selected_sections)}" if len(selected_sections) < len(SECTION_LABELS) else ""
    out_path = os.path.join(out_dir, f"dnai_output{suffix}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    st.success(f"Saved to `{out_path}`")

    st.download_button("⬇️ Download HTML", data=result,
                       file_name=os.path.basename(out_path), mime="text/html")

    # Email
    if send_email:
        st.write("📧 Sending email...")
        try:
            from dnai.tools import send_email as _send
            _to = cfg_email_recipients or _cfg.EMAIL_RECIPIENTS
            _send(subject=f"{_cfg.EMAIL_SUBJECT_PREFIX} - {label}",
                  html_body=result, to_recipients=_to)
            st.success(f"Email sent to {_to}")
        except Exception as e:
            st.error(f"Email failed: {e}")
