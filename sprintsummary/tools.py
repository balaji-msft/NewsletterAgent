"""
Tool implementations for the Sprint Summary Agent.

Fetches work-item data from the ADO query and returns it for the AI agent
to process into a sprint summary.  Reuses shared.ado_client for the ADO REST calls.
"""
from __future__ import annotations

import json
import logging

from shared import ado_client
from shared.email_sender import send_email as _send_email
from sprintsummary import config as cfg

log = logging.getLogger("sprintsummary.tools")


def get_sprint_query_results() -> str:
    """
    Execute the saved ADO work-item query for Sprint Summary and return results as JSON.

    Each item includes id, title, state, assignedTo, type, completedWork.
    """
    org_url = cfg.SPRINTSUMMARY_ORG_URL
    project = cfg.SPRINTSUMMARY_PROJECT
    query_id = cfg.SPRINTSUMMARY_QUERY_ID
    pat = cfg.SPRINTSUMMARY_PAT or None  # None triggers Entra ID fallback

    log.info(
        "Fetching Sprint Summary query results  org=%s  project=%s  query=%s",
        org_url, project, query_id,
    )

    try:
        items = ado_client.fetch_ado_query_results(org_url, project, pat=pat, query_id=query_id)
    except Exception as e:
        log.exception("Failed to fetch Sprint Summary query results")
        return json.dumps({"error": str(e)})

    log.info("Retrieved %d work items from Sprint Summary query", len(items))
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
    "get_sprint_query_results": get_sprint_query_results,
    "send_email": send_email,
}
