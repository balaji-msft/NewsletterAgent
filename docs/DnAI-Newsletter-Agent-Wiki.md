# DnAI Newsletter Agent

## Overview

The **DnAI Newsletter Agent** is an AI-powered automation tool that compiles a professional monthly HTML newsletter for the DnAI team. It uses **Azure OpenAI (GPT-4.1)** with function calling to gather data from multiple sources—Azure DevOps wikis, ADO work-item queries, local files—and assembles them into a formatted HTML email sent via Power Automate.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     run_local.py (CLI)                      │
│              or  ui/app.py (Streamlit Web UI)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   dnai/agent.py     │
              │  (Orchestrator)     │
              │  Azure OpenAI +     │
              │  Function Calling   │
              └────────┬────────────┘
                       │
         ┌─────────────┼─────────────────┐
         ▼             ▼                 ▼
   dnai/tools.py   dnai/config.py   dnai/prompt.yaml
   (6 tools)       (env config)     (system prompt)
         │
         ▼
   shared/ado_client.py        shared/email_sender.py
   (ADO REST API calls)        (Power Automate webhook)
```

## Newsletter Sections

The DnAI newsletter contains **6 sections**, compiled in order:

| # | Section | Data Source | Tool |
|---|---------|-------------|------|
| 1 | **Hot Topics** | Local files folder | `get_hot_topics_files` |
| 2 | **TSG (Troubleshooting Guides)** | ADO Wiki commits (Fabric wiki) | `get_wiki_commits` |
| 3 | **Fabric Made EEE-z** | ADO Wiki pages (New Feature Readiness) | `get_eeez_features` |
| 4 | **CSS Feedback Items** | ADO Work Item Query (Data-AI-Supportability org) | `get_ado_query_results` |
| 5 | **CSS Taxonomy Changes** | ADO Work Item Query (CSSTaxonomyChange org) | `get_ado_query_results` |
| 6 | **Component V-Team** | Static Markdown file | `get_static_content` |

### Section Details

#### 1. Hot Topics
- Reads all files from a configurable local folder (`HOT_TOPICS_FOLDER`)
- Supports `.md`, `.txt`, `.html`, `.csv`, `.json`, `.xml` formats
- The agent summarizes key topics from all files combined

#### 2. TSG (Troubleshooting Guides)
- Fetches wiki commits from the **Fabric** wiki in the **Supportability** ADO org
- Scoped to a configurable folder (default: `/Fabric Experiences/Power BI`)
- Filtered to the previous calendar month
- Returns deduplicated pages with: **Component**, **Page** (clickable link), **Status** (New/Updated)
- Can be overridden with `-p` flag to target different wiki folders (e.g., `Fabric Experiences/Data Engineering`)

#### 3. Fabric Made EEE-z
- Lists wiki pages under `/New Feature Readiness/{year}/{month}`
- Filtered by title prefix (default: `NF-PBI`, overridable via `-f` flag)
- Fetches two months of data (current + previous) and deduplicates
- Returns title, wiki link, video URL (if available), and content summary

#### 4. CSS Feedback Items
- Executes a saved ADO query in the **Data-AI-Supportability** org
- Parses `[CSSFeedback][Category][...]` title tags into `feedback_category` and `short_title`
- Renders a summary table (count by category) + detailed items table

#### 5. CSS Taxonomy Changes
- Executes a saved ADO query in the **CSSTaxonomyChange** org
- Summarizes taxonomy changes

#### 6. Component V-Team
- Reads a static Markdown file (`Component_V-Teams_PowerBI_CSS_Supportability.md`)
- Converts to HTML with V-Team ownership table and leadership acknowledgements

## Running the Agent

### Prerequisites

1. **Python 3.11+** with virtual environment
2. **Azure OpenAI** access (Entra ID / DefaultAzureCredential)
3. **ADO Personal Access Tokens** for 3 orgs:
   - `ADO_PAT` — Supportability org
   - `CSS_FEEDBACK_PAT` — Data-AI-Supportability org
   - `CSS_TAXONOMY_PAT` — CSSTaxonomyChange org
4. **Power Automate webhook URL** for email delivery
5. Environment variables configured in `local.settings.json`

### CLI Usage (`run_local.py`)

```bash
# Full newsletter (all 6 sections) + send email
python run_local.py --agent dnai --send

# Single section only
python run_local.py --agent dnai --section tsg --send
python run_local.py --agent dnai --section eeez --send
python run_local.py --agent dnai --section hot_topics
python run_local.py --agent dnai --section css_feedback
python run_local.py --agent dnai --section css_taxonomy
python run_local.py --agent dnai --section vteam

# TSG with custom wiki folder path
python run_local.py --agent dnai --section tsg -p "Fabric Experiences/Data Engineering" --send

# EEE-z with custom title filter
python run_local.py --agent dnai --section eeez -f NF-DE --send

# Interactive mode (type prompts manually)
python run_local.py --agent dnai --interactive

# Custom prompt
python run_local.py --agent dnai "Compile only Hot Topics and TSG sections"
```

### CLI Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--agent dnai` | `-a dnai` | Select the DnAI agent |
| `--section SECTION` | `-s` | Run a single section: `hot_topics`, `tsg`, `eeez`, `css_feedback`, `css_taxonomy`, `vteam` |
| `--send` | | Send the output via email after generation |
| `--filter FILTER` | `-f` | EEE-z title filter override (e.g., `NF-PBI`, `NF-DE`, `NF-PLAT`) |
| `--path PATH` | `-p` | TSG wiki folder path override (e.g., `Fabric Experiences/Data Engineering`) |
| `--interactive` | `-i` | Enter interactive prompt mode |

### Web UI (Streamlit)

```bash
python -m streamlit run ui/app.py --server.port 8000
```

The UI provides checkboxes to select individual sections and a "Generate & Send" button.

## Configuration

All configuration is read from environment variables, with `DNAI_*` prefixed vars taking priority over general ones. Set these in `local.settings.json` for local dev or as App Settings in Azure.

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | `https://aisb100.services.ai.azure.com` |
| `MODEL_DEPLOYMENT` | Model deployment name | `gpt-4.1` |
| `ADO_ORG` | Primary ADO org slug | `Supportability` |
| `ADO_PROJECT` | Primary ADO project | — |
| `ADO_PAT` | PAT for Supportability org | — |
| `TSG_REPO_NAME` | Wiki repo name | `Fabric` |
| `TSG_WIKI_NAME` | Wiki name | `Fabric` |
| `DNAI_TSG_WIKI_FOLDER` | Default wiki folder for TSG | `/Fabric Experiences/Power BI` |
| `DNAI_EEEZ_TITLE_FILTER` | EEE-z title filter | `NF-PBI` |
| `CSS_FEEDBACK_PAT` | PAT for Data-AI-Supportability org | — |
| `CSS_FEEDBACK_QUERY_ID` | Saved query GUID for CSS Feedback | — |
| `CSS_TAXONOMY_PAT` | PAT for CSSTaxonomyChange org | — |
| `CSS_TAXONOMY_QUERY_ID` | Saved query GUID for CSS Taxonomy | — |
| `DNAI_HOT_TOPICS_FOLDER` | Local path to Hot Topics files | — |
| `POWER_AUTOMATE_WEBHOOK_URL` | Webhook URL for email delivery | — |
| `DNAI_EMAIL_RECIPIENTS` | Comma-separated recipient emails | — |
| `DNAI_EMAIL_SUBJECT_PREFIX` | Email subject prefix | `DnAI Newsletter` |
| `DNAI_VTEAM_MD_FILE` | Path to V-Team markdown file | `config/Component_V-Teams_PowerBI_CSS_Supportability.md` |

## How It Works

1. **Prompt Loading**: The system prompt is loaded from `dnai/prompt.yaml` with `{{placeholder}}` tokens resolved from config values at runtime.
2. **Agent Loop**: The agent uses Azure OpenAI chat completions with function calling. It iterates up to 15 rounds of tool calls.
3. **Tool Dispatch**: Each tool call is dispatched to the corresponding Python function in `dnai/tools.py`.
4. **HTML Compilation**: The LLM assembles all tool results into a formatted HTML newsletter with inline CSS (for email compatibility).
5. **Email Delivery**: The `send_email` tool posts the HTML to a Power Automate webhook which delivers the email.
6. **Logging**: Each run creates a timestamped log directory under `logs/dnai_{timestamp}/` with tool call inputs/outputs.

## File Structure

```
dnai/
├── __init__.py          # Package init
├── agent.py             # Agent orchestrator (OpenAI function calling loop)
├── config.py            # Environment variable configuration
├── prompt.yaml          # System prompt (editable without code changes)
└── tools.py             # 6 tool implementations + dispatcher
```

## Customizing the Prompt

Edit `dnai/prompt.yaml` to change the agent's behavior without modifying code. The file supports `{{placeholder}}` tokens that are resolved from `config.py` at runtime:

- `{{current_month}}` → e.g., "March 2026"
- `{{tsg_wiki_folder}}` → e.g., "/Fabric Experiences/Power BI"
- `{{css_feedback_query_id}}` → saved ADO query GUID
- `{{email_subject_prefix}}` → e.g., "DnAI Newsletter"

## Azure Deployment

The agent is deployed as an **Azure Web App** running Streamlit:

| Property | Value |
|----------|-------|
| **Webapp Name** | `dnainewsletter` |
| **Resource Group** | `rg-fabricbi-spm` |
| **App Service Plan** | `asp-fabricbi-spm` (B1 Linux) |
| **Python Version** | 3.11 |
| **URL** | `https://dnainewsletter.azurewebsites.net` |
| **Managed Identity** | Enabled (Cognitive Services OpenAI User on aisb100) |
| **Startup Command** | `python -m streamlit run ui/app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false` |

### Deploying Updates

```bash
# From the project root, create a zip with required files
Compress-Archive -Path ui, dnai, shared, config, requirements.txt, run_local.py -DestinationPath deploy.zip -Force

# Deploy via zip push
az webapp deployment source config-zip --name dnainewsletter --resource-group rg-fabricbi-spm --src deploy.zip
```

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| Empty TSG results | Check `-p` path matches wiki folder structure. Ensure leading `/` is present or omitted consistently. The agent normalizes paths automatically. |
| Empty EEE-z results | Verify `month` parameter uses 3-letter abbreviation ("Feb", not 2). Check title filter matches page names. |
| 403 from ADO | PAT may be expired. Rotate via ADO > User Settings > Personal Access Tokens. Need `Code (Read)` + `Work Items (Read)` scopes. |
| Email not sent | Verify `POWER_AUTOMATE_WEBHOOK_URL` is set and the Power Automate flow is enabled. |
| Azure OpenAI auth failure | Ensure managed identity has `Cognitive Services OpenAI User` role on the OpenAI resource. |
