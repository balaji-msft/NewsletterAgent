# Newsletter Agent – Azure AI Foundry

An automated newsletter compilation agent powered by **Azure AI Foundry Agent Service**.  
Runs monthly via an Azure Functions timer trigger, gathers data from SharePoint and Azure DevOps, compiles a styled HTML newsletter, and sends it via email.

## Architecture

```
Timer Trigger (monthly)
       │
       ▼
Azure Function  ──▶  AI Foundry Agent (GPT-4o)
                         │
                         ├─ get_sharepoint_file()  → Microsoft Graph
                         ├─ get_ado_commits()       → Azure DevOps Git API
                         ├─ get_ado_query_results() → Azure DevOps WIT API
                         ├─ get_static_content()    → Local config
                         └─ send_email()            → Microsoft Graph Send Mail
```

## Newsletter Sections

| # | Section | Data Source | Tool |
|---|---------|-----------|------|
| 1 | Hot Topics for the Month | SharePoint file | `get_sharepoint_file` |
| 2 | TSG (Troubleshooting Guides) | ADO Git commits | `get_ado_commits` |
| 3 | Fabric Made EEE-z | ADO Git commits (filtered) | `get_ado_commits` |
| 4 | CSS Feedback Items | ADO Work Item Query | `get_ado_query_results` |
| 5 | CSS Taxonomy Changes | ADO Work Item Query | `get_ado_query_results` |
| 6 | Component V-Team | Static config | `get_static_content` |

## Project Structure

```
NewsLetterAgent/
├── config.py              # Environment-based configuration
├── tools.py               # Tool implementations (Graph, ADO APIs)
├── agent.py               # Agent creation, tool dispatch, run loop
├── function_app.py        # Azure Function timer trigger entry point
├── run_local.py           # Manual/local test runner
├── requirements.txt       # Python dependencies
├── host.json              # Azure Functions host config
├── function.json          # Timer trigger binding
├── local.settings.json    # Local dev settings (DO NOT commit)
├── .gitignore
└── spec.txt               # Original spec
```

## Prerequisites

1. **Azure AI Foundry** project with a GPT-4o deployment
2. **Azure DevOps** PAT with read access to Git repos and Work Items
3. **Entra ID App Registration** with Microsoft Graph permissions:
   - `Sites.Read.All` (SharePoint file access)
   - `Mail.Send` (send email as service account)
4. **Python 3.10+**
5. **Azure Functions Core Tools v4**

## Setup

### 1. Clone & install

```bash
cd NewsLetterAgent
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 2. Configure

Edit `local.settings.json` and fill in all `<placeholder>` values:

| Variable | Description |
|----------|-------------|
| `AI_PROJECT_CONNECTION_STRING` | From Azure AI Foundry project → Settings → Connection string |
| `ADO_ORG_URL` | e.g. `https://dev.azure.com/myorg` |
| `ADO_PROJECT` | ADO project name |
| `ADO_PAT` | Personal Access Token with Code (Read) + Work Items (Read) |
| `TSG_REPO_NAME` | Git repo name for TSG commits |
| `CSS_FEEDBACK_QUERY_ID` | GUID of the saved ADO query for CSS Feedback |
| `CSS_TAXONOMY_QUERY_ID` | GUID of the saved ADO query for Taxonomy Changes |
| `GRAPH_TENANT_ID` | Entra ID tenant |
| `GRAPH_CLIENT_ID` | App registration client ID |
| `GRAPH_CLIENT_SECRET` | App registration client secret |
| `SHAREPOINT_SITE_ID` | SharePoint site ID (from Graph Explorer) |
| `SHAREPOINT_FILE_PATH` | Path to the Hot Topics file in SharePoint |
| `EMAIL_SENDER` | UPN or shared mailbox that sends the email |
| `EMAIL_RECIPIENTS` | Comma-separated recipient list |

### 3. Test locally

```bash
python run_local.py
```

### 4. Run as Azure Function locally

```bash
func start
```

### 5. Deploy to Azure

```bash
func azure functionapp publish <your-function-app-name>
```

Make sure all settings from `local.settings.json` → `Values` are added as **Application Settings** in the Azure Function App.

## How It Works

1. **Timer fires** on the 1st of each month at 9 AM UTC
2. `function_app.py` calls `run_newsletter_agent()`
3. `agent.py` creates an AI Foundry Agent with 5 function tools
4. The agent autonomously decides which tools to call and in what order
5. Each tool call is dispatched to the real API implementation in `tools.py`
6. The agent composes the full HTML newsletter from all gathered data
7. The agent calls `send_email` to deliver the newsletter
8. Done — agent is cleaned up

## Customization

- **Add a section**: Define a new tool in `tools.py`, add its schema in `agent.py` → `TOOL_DEFINITIONS`, update the system prompt
- **Change schedule**: Edit the CRON in `function_app.py` (e.g. `0 0 9 * * 1` for every Monday)
- **Change model**: Set `MODEL_DEPLOYMENT` to a different deployment name
