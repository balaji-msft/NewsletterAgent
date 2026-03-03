"""
Tool implementations for the Fabric BI MoR Callout Agent.

Fetches work-item data from the ADO query and returns it for the AI agent
to process into MoR callouts.  Reuses shared.ado_client for the ADO REST calls.
"""
from __future__ import annotations

import json
import logging

from shared import ado_client
from shared.email import send_email as _send_email
from fabricbimor import config as cfg

log = logging.getLogger("fabricbimor.tools")


def get_mor_query_results() -> str:
    """
    Execute the saved ADO work-item query for MoR and return results as JSON.

    Query: https://dev.azure.com/Data-AI-Supportability/Data%20Platform/
           _queries/query-edit/fbac8f3c-4da6-4ccd-92f7-fa0dc5d4f275/

    Each item includes id, title, state, assignedTo, type, completedWork.
    """
    org_url = cfg.FABRICBIMOR_ORG_URL
    project = cfg.FABRICBIMOR_PROJECT
    query_id = cfg.FABRICBIMOR_QUERY_ID
    pat = cfg.FABRICBIMOR_PAT

    if not pat:
        return json.dumps({"error": "FABRICBIMOR_PAT (or CSS_FEEDBACK_PAT) not set."})

    log.info(
        "Fetching MoR query results  org=%s  project=%s  query=%s",
        org_url, project, query_id,
    )

    try:
        items = ado_client.fetch_ado_query_results(org_url, project, pat, query_id)
    except Exception as e:
        log.exception("Failed to fetch MoR query results")
        return json.dumps({"error": str(e)})

    log.info("Retrieved %d work items from MoR query", len(items))
    return json.dumps(items, indent=2)


def send_email(
    subject: str,
    html_body: str,
    to_recipients: str | None = None,
) -> str:
    """Send an HTML email via Power Automate HTTP webhook."""
    to = to_recipients or cfg.EMAIL_RECIPIENTS
    return _send_email(
        subject=subject,
        html_body=html_body,
        to_recipients=to,
        webhook_url=cfg.POWER_AUTOMATE_WEBHOOK_URL,
    )


# ── Tool dispatcher ─────────────────────────────────────────────────

TOOL_FUNCTIONS: dict[str, callable] = {
    "get_mor_query_results": get_mor_query_results,
    "send_email": send_email,
}
