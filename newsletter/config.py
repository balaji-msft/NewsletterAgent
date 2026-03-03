"""
Configuration settings for the Newsletter Agent.
Load from environment variables or Azure App Configuration.
"""
import os

# ── Azure OpenAI (Entra ID auth) ────────────────────────────────────
AZURE_OPENAI_ENDPOINT = os.environ.get(
    "AZURE_OPENAI_ENDPOINT", "https://aisb100.services.ai.azure.com"
)
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT", "gpt-4.1")

# ── Azure DevOps ────────────────────────────────────────────────────
ADO_ORG_URL = os.environ.get("ADO_ORG_URL", "https://dev.azure.com/YOUR_ORG")
ADO_PROJECT = os.environ.get("ADO_PROJECT", "YOUR_PROJECT")
ADO_PAT = os.environ.get("ADO_PAT", "")  # Personal Access Token

# ADO org name (not full URL) – needed by ado_client
ADO_ORG = os.environ.get("ADO_ORG", "Supportability")

# ADO Repos for TSG and Fabric EEE-z sections
TSG_REPO_NAME = os.environ.get("TSG_REPO_NAME", "Fabric")
TSG_WIKI_NAME = os.environ.get("TSG_WIKI_NAME", "Fabric")  # wiki identifier (code wiki name)
TSG_WIKI_FOLDER = os.environ.get(
    "TSG_WIKI_FOLDER", "/Fabric Experiences/Power BI"
)  # wiki folder to scope commits to
FABRIC_REPO_NAME = os.environ.get("FABRIC_REPO_NAME", "Fabric")

# Fabric Made EEE-z (New Feature Readiness wiki pages)
EEEZ_WIKI_FOLDER = os.environ.get(
    "EEEZ_WIKI_FOLDER", "/New Feature Readiness"
)
EEEZ_TITLE_FILTER = os.environ.get("EEEZ_TITLE_FILTER", "NF-PBI")
EEEZ_YEAR = os.environ.get("EEEZ_YEAR", "")   # blank = auto (current year)
EEEZ_MONTH = os.environ.get("EEEZ_MONTH", "")  # blank = auto (prev month abbr)

# ADO Work Item Query IDs
CSS_FEEDBACK_QUERY_ID = os.environ.get("CSS_FEEDBACK_QUERY_ID", "")

# CSS Feedback lives in a DIFFERENT ADO org/project
CSS_FEEDBACK_ORG_URL = os.environ.get(
    "CSS_FEEDBACK_ORG_URL", "https://dev.azure.com/Data-AI-Supportability"
)
CSS_FEEDBACK_PROJECT = os.environ.get("CSS_FEEDBACK_PROJECT", "Data Platform")
CSS_FEEDBACK_PAT = os.environ.get("CSS_FEEDBACK_PAT", "")

# CSS Taxonomy lives in a DIFFERENT ADO org/project
CSS_TAXONOMY_ORG_URL = os.environ.get(
    "CSS_TAXONOMY_ORG_URL", "https://dev.azure.com/CSSTaxonomyChange"
)
CSS_TAXONOMY_PROJECT = os.environ.get(
    "CSS_TAXONOMY_PROJECT", "CSS Commercial Taxonomy Change Management"
)
CSS_TAXONOMY_PAT = os.environ.get("CSS_TAXONOMY_PAT", "")  # may differ from ADO_PAT
CSS_TAXONOMY_QUERY_ID = os.environ.get("CSS_TAXONOMY_QUERY_ID", "")

# ── Hot Topics (local folder) ───────────────────────────────────────
HOT_TOPICS_FOLDER = os.environ.get(
    "HOT_TOPICS_FOLDER", r"C:\work\PBI\PBI-HotTopics"
)

# ── Microsoft Graph (for email) ─────────────────────────────────────
GRAPH_TENANT_ID = os.environ.get("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID", "")
GRAPH_CERT_THUMBPRINT = os.environ.get("GRAPH_CERT_THUMBPRINT", "")
GRAPH_CERT_PATH = os.environ.get("GRAPH_CERT_PATH", "")        # path to .pfx
GRAPH_CERT_PASSWORD = os.environ.get("GRAPH_CERT_PASSWORD", "")  # pfx password

# ── Email ────────────────────────────────────────────────────────────
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "newsletter@yourdomain.com")
EMAIL_RECIPIENTS = os.environ.get("EMAIL_RECIPIENTS", "team@yourdomain.com")  # comma-separated
EMAIL_SUBJECT_PREFIX = os.environ.get("EMAIL_SUBJECT_PREFIX", "Monthly Newsletter")
POWER_AUTOMATE_WEBHOOK_URL = os.environ.get("POWER_AUTOMATE_WEBHOOK_URL", "")

# ── Static Content ──────────────────────────────────────────────────
# Path is relative to the project root (one level up from this file)
VTEAM_MD_FILE = os.environ.get(
    "VTEAM_MD_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "Component_V-Teams_PowerBI_CSS_Supportability.md"),
)
