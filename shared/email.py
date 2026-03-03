"""
Shared email utility — sends HTML email via Power Automate webhook.
Used by both the Newsletter and MoR agents.
"""
from __future__ import annotations

import logging
import requests

log = logging.getLogger("shared.email")


def send_email(
    subject: str,
    html_body: str,
    to_recipients: str,
    webhook_url: str,
) -> str:
    """Send an HTML email via Power Automate HTTP webhook.

    Args:
        subject:       Email subject line.
        html_body:     Full HTML body.
        to_recipients: Semicolon-separated email addresses.
        webhook_url:   Power Automate webhook URL.

    Returns:
        Success or error message string.
    """
    if not webhook_url:
        return "POWER_AUTOMATE_WEBHOOK_URL not set – email not sent."

    payload = {
        "subject": subject,
        "html_body": html_body,
        "to_recipients": to_recipients,
    }
    resp = requests.post(webhook_url, json=payload, timeout=120)
    resp.raise_for_status()
    log.info("Email sent to %s", to_recipients)
    return f"Email sent successfully to {to_recipients}"
