"""
Configuration for the Fabric BI MoR (Monthly Operational Review) Callout Agent.

Reads from environment variables (or local.settings.json via the runner).
Completely separate from the newsletter agent config.
"""
import os

# ── Azure OpenAI (Entra ID auth) ────────────────────────────────────
AZURE_OPENAI_ENDPOINT = os.environ.get(
    "AZURE_OPENAI_ENDPOINT", "https://aisb100.services.ai.azure.com"
)
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT", "gpt-4.1")

# ── ADO Query for MoR ───────────────────────────────────────────────
# Source: https://dev.azure.com/Data-AI-Supportability/Data%20Platform/_queries/query-edit/fbac8f3c-4da6-4ccd-92f7-fa0dc5d4f275/
FABRICBIMOR_ORG_URL = os.environ.get(
    "FABRICBIMOR_ORG_URL", "https://dev.azure.com/Data-AI-Supportability"
)
FABRICBIMOR_PROJECT = os.environ.get("FABRICBIMOR_PROJECT", "Data Platform")
FABRICBIMOR_QUERY_ID = os.environ.get(
    "FABRICBIMOR_QUERY_ID", "fbac8f3c-4da6-4ccd-92f7-fa0dc5d4f275"
)
FABRICBIMOR_PAT = os.environ.get("FABRICBIMOR_PAT", "") or os.environ.get("CSS_FEEDBACK_PAT", "")

# ── Email (Power Automate webhook) ───────────────────────────────
EMAIL_RECIPIENTS = os.environ.get("MOR_EMAIL_RECIPIENTS", "") or os.environ.get("EMAIL_RECIPIENTS", "")
EMAIL_SUBJECT_PREFIX = os.environ.get(
    "FABRICBIMOR_EMAIL_SUBJECT", "Fabric BI - MoR Callouts"
)
POWER_AUTOMATE_WEBHOOK_URL = os.environ.get("POWER_AUTOMATE_WEBHOOK_URL", "")
