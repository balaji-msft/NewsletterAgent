"""
Configuration for the Sprint Summary Agent.

Reads from environment variables (or local.settings.json via the runner).
Reuses the same ADO query as fabricbimor by default; override via
SPRINTSUMMARY_* env vars if needed.
"""
import os

# ── Azure OpenAI (Entra ID auth) ────────────────────────────────────
AZURE_OPENAI_ENDPOINT = os.environ.get(
    "AZURE_OPENAI_ENDPOINT", "https://aisb100.services.ai.azure.com"
)
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT", "gpt-4.1")

# ── ADO Query (defaults to same as fabricbimor) ─────────────────────
SPRINTSUMMARY_ORG_URL = os.environ.get(
    "SPRINTSUMMARY_ORG_URL",
    os.environ.get("FABRICBIMOR_ORG_URL", "https://dev.azure.com/Data-AI-Supportability"),
)
SPRINTSUMMARY_PROJECT = os.environ.get(
    "SPRINTSUMMARY_PROJECT",
    os.environ.get("FABRICBIMOR_PROJECT", "Data Platform"),
)
SPRINTSUMMARY_QUERY_ID = os.environ.get(
    "SPRINTSUMMARY_QUERY_ID",
    os.environ.get("FABRICBIMOR_QUERY_ID", "fbac8f3c-4da6-4ccd-92f7-fa0dc5d4f275"),
)
SPRINTSUMMARY_PAT = (
    os.environ.get("SPRINTSUMMARY_PAT", "")
    or os.environ.get("FABRICBIMOR_PAT", "")
    or os.environ.get("CSS_FEEDBACK_PAT", "")
)

# ── Email (Power Automate webhook) ───────────────────────────────
EMAIL_RECIPIENTS = (
    os.environ.get("SPRINTSUMMARY_EMAIL_RECIPIENTS", "")
    or os.environ.get("MOR_EMAIL_RECIPIENTS", "")
    or os.environ.get("EMAIL_RECIPIENTS", "")
)
EMAIL_SUBJECT_PREFIX = os.environ.get(
    "SPRINTSUMMARY_EMAIL_SUBJECT", "Fabric BI - Sprint Summary"
)
POWER_AUTOMATE_WEBHOOK_URL = os.environ.get("POWER_AUTOMATE_WEBHOOK_URL", "")
