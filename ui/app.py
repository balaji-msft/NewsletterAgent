"""
Streamlit UI for Newsletter & MoR Agents.

Launch:  streamlit run ui/app.py
"""
from __future__ import annotations

import json
import os
import sys
import threading
import logging
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
    page_title="Fabric BI AI Agent Hub",
    page_icon="📬",
    layout="wide",
)

# ── Agent descriptions ──────────────────────────────────────────────

NEWSLETTER_INFO = """
### 📰 Newsletter Agent

Compiles a **monthly HTML newsletter** for the Fabric BI CSS Supportability team.

**What it does:**
1. **Hot Topics** — Reads files from a Sharepoint folder and summarises key themes
2. **TSG (Troubleshooting Guides)** — Scans Azure DevOps wiki commits for new/updated guides
3. **Fabric Made EEE-z** — Lists new feature readiness wiki pages for the month
4. **CSS Feedback Items** — Queries ADO work items for CSS feedback, grouped by category
5. **CSS Taxonomy Changes** — Queries a separate ADO org for taxonomy change requests
6. **Component V-Team** — Includes  V-Team ownership content

The agent autonomously calls the right tools, gathers all data, composes a professional
HTML newsletter with inline CSS, and optionally emails it via Power Automate.
"""

MOR_INFO = """
### 📊 MoR Callout Agent (Fabric BI)

Generates **Monthly Operational Review (MoR) callouts** for leadership slide decks.

**What it does:**
1. Fetches **211+ work items** from a saved Azure DevOps query covering:
   - Product Improvements
   - CRI Escalations
   - Engineer Readiness (CSS Content)
   - Customer Content & Documentation
2. Analyses the data by component, theme, and readiness type
3. Produces **executive-level bullet callouts** in HTML — grouped by theme,
   starting with component names and counts
4. Excludes "Business Operations" items automatically
5. Optionally emails the result via Power Automate

Output is VP-ready: concise, data-backed, professionally formatted.
"""

SPRINT_SUMMARY_INFO = """
### 🏃 Sprint Summary Agent

Generates a **Sprint Summary** of completed work items for the current sprint.

**What it does:**
1. Fetches work items from the same ADO query as MoR Callouts
2. Identifies items **completed** (Closed / Done / Resolved) during the sprint
3. Groups deliverables by **theme / component** (Product Improvements, CRI Escalations,
   CSS Content, Customer Content, Engineer Readiness)
4. Produces a professional HTML report with:
   - Sprint Highlights (top 3-5 achievements)
   - By-the-Numbers summary (totals, breakdowns, carry-overs)
   - Themed sections with bullet-list accomplishments
5. Optionally emails the result via Power Automate

Celebrates team wins and gives leadership visibility into sprint delivery.
"""

POWERBI_NEWSLETTER_INFO = """
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
"""

FABRICPLATFORM_NEWSLETTER_INFO = """
### 🏗️ Fabric Platform Newsletter Agent

Compiles a **monthly HTML newsletter** focused on **Fabric Platform**.

**Sections:**
1. **Hot Topics** — Key themes from the Hot Topics folder
2. **TSG (Troubleshooting Guides)** — New/updated wiki pages under `/Fabric Platform`
3. **Fabric Made EEE-z** — New feature readiness pages (NF-PAT filter)
4. **CSS Feedback Items** — CSS feedback work items grouped by category
5. **CSS Taxonomy Changes** — Taxonomy change requests from CSSTaxonomyChange org
6. **Fabric Platform Component V-Team** — Fabric Platform Component V-Team ownership table

Uses product-specific config (FABRICPLATFORM_* env vars) while sharing the same tool logic.
"""

# ── Sidebar ─────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🤖 AI Agent Hub")
    st.markdown("---")

    agent_choice = st.radio(
        "**Select Agent**",
        [ "Power BI Newsletter", "Fabric Platform Newsletter",
         "MoR Callouts", "Sprint Summary"],
        index=0,
    )

    st.markdown("---")

    if agent_choice in ("Newsletter", "Power BI Newsletter", "Fabric Platform Newsletter"):
        section = st.selectbox(
            "Section (optional)",
            ["Full Newsletter", "hot_topics", "tsg", "eeez", "css_feedback", "css_taxonomy", "vteam"],
        )
    else:
        section = None

    send_email = st.checkbox("📧 Send email after generation", value=False)

    st.markdown("---")
    st.caption(f"Date: {datetime.now().strftime('%B %d, %Y')}")

# ── Section prompts (newsletter only) ───────────────────────────────

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

if agent_choice == "Newsletter":
    st.markdown(NEWSLETTER_INFO)
elif agent_choice == "Power BI Newsletter":
    st.markdown(POWERBI_NEWSLETTER_INFO)
elif agent_choice == "Fabric Platform Newsletter":
    st.markdown(FABRICPLATFORM_NEWSLETTER_INFO)
elif agent_choice == "MoR Callouts":
    st.markdown(MOR_INFO)
else:
    st.markdown(SPRINT_SUMMARY_INFO)

st.markdown("---")

# Custom prompt override
custom_prompt = st.text_area(
    "✏️ Custom prompt (leave empty for default)",
    height=80,
    placeholder="e.g. 'Focus only on Power BI items this month'",
)

# ── Run button ──────────────────────────────────────────────────────

if st.button("🚀 Run Agent", type="primary", use_container_width=True):

    with st.status("Running agent...", expanded=True) as status:

        # Determine prompt
        if custom_prompt.strip():
            prompt = custom_prompt.strip()
        elif agent_choice == "Newsletter" and section and section != "Full Newsletter":
            prompt = SECTION_PROMPTS[section]
        else:
            prompt = None  # use default

        # Run the appropriate agent
        try:
            if agent_choice == "Newsletter":
                st.write("⏳ Starting Newsletter agent...")
                from newsletter.agent import run_newsletter_agent
                result = run_newsletter_agent(user_prompt=prompt)
                label = section if section != "Full Newsletter" else "Full Newsletter"
            elif agent_choice == "Power BI Newsletter":
                st.write("⏳ Starting Power BI Newsletter agent...")
                from powerbi.agent import run_powerbi_newsletter_agent
                result = run_powerbi_newsletter_agent(user_prompt=prompt)
                label = section if section != "Full Newsletter" else "Power BI Newsletter"
            elif agent_choice == "Fabric Platform Newsletter":
                st.write("⏳ Starting Fabric Platform Newsletter agent...")
                from fabricplatform.agent import run_fabricplatform_newsletter_agent
                result = run_fabricplatform_newsletter_agent(user_prompt=prompt)
                label = section if section != "Full Newsletter" else "Fabric Platform Newsletter"
            elif agent_choice == "MoR Callouts":
                st.write("⏳ Starting MoR Callout agent...")
                from fabricbimor.agent import run_mor_agent
                result = run_mor_agent(user_prompt=prompt)
                label = "MoR Callouts"
            else:
                st.write("⏳ Starting Sprint Summary agent...")
                from sprintsummary.agent import run_sprint_summary_agent
                result = run_sprint_summary_agent(user_prompt=prompt)
                label = "Sprint Summary"

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
    if agent_choice == "Newsletter":
        suffix = f"_{section}" if section and section != "Full Newsletter" else ""
        out_path = os.path.join(out_dir, f"newsletter_output{suffix}.html")
    elif agent_choice == "Power BI Newsletter":
        suffix = f"_{section}" if section and section != "Full Newsletter" else ""
        out_path = os.path.join(out_dir, f"powerbi_output{suffix}.html")
    elif agent_choice == "Fabric Platform Newsletter":
        suffix = f"_{section}" if section and section != "Full Newsletter" else ""
        out_path = os.path.join(out_dir, f"fabricplatform_output{suffix}.html")
    elif agent_choice == "MoR Callouts":
        out_path = os.path.join(out_dir, "fabricbimor_output.html")
    else:
        out_path = os.path.join(out_dir, "sprintsummary_output.html")

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
            if agent_choice == "Newsletter":
                from newsletter import config as nl_cfg
                from newsletter.tools import send_email as nl_send
                subj = f"{nl_cfg.EMAIL_SUBJECT_PREFIX} - {label}"
                nl_send(subject=subj, html_body=result, to_recipients=nl_cfg.EMAIL_RECIPIENTS)
                st.success(f"Email sent to {nl_cfg.EMAIL_RECIPIENTS}")
            elif agent_choice == "Power BI Newsletter":
                from powerbi import config as pbi_cfg
                from powerbi.tools import send_email as pbi_send
                subj = f"{pbi_cfg.EMAIL_SUBJECT_PREFIX} - {label}"
                pbi_send(subject=subj, html_body=result, to_recipients=pbi_cfg.EMAIL_RECIPIENTS)
                st.success(f"Email sent to {pbi_cfg.EMAIL_RECIPIENTS}")
            elif agent_choice == "Fabric Platform Newsletter":
                from fabricplatform import config as fp_cfg
                from fabricplatform.tools import send_email as fp_send
                subj = f"{fp_cfg.EMAIL_SUBJECT_PREFIX} - {label}"
                fp_send(subject=subj, html_body=result, to_recipients=fp_cfg.EMAIL_RECIPIENTS)
                st.success(f"Email sent to {fp_cfg.EMAIL_RECIPIENTS}")
            elif agent_choice == "MoR Callouts":
                from fabricbimor import config as mor_cfg
                from fabricbimor.tools import send_email as mor_send
                subj = mor_cfg.EMAIL_SUBJECT_PREFIX
                mor_send(subject=subj, html_body=result, to_recipients=mor_cfg.EMAIL_RECIPIENTS)
                st.success(f"Email sent to {mor_cfg.EMAIL_RECIPIENTS}")
            else:
                from sprintsummary import config as sprint_cfg
                from sprintsummary.tools import send_email as sprint_send
                subj = sprint_cfg.EMAIL_SUBJECT_PREFIX
                sprint_send(subject=subj, html_body=result, to_recipients=sprint_cfg.EMAIL_RECIPIENTS)
                st.success(f"Email sent to {sprint_cfg.EMAIL_RECIPIENTS}")
        except Exception as e:
            st.error(f"Email failed: {e}")
