"""
Microsoft Graph authentication using MSAL with certificate-based
client credentials flow.  Shared utility — no agent-specific imports.

Env vars: GRAPH_TENANT_ID, GRAPH_CLIENT_ID,
          GRAPH_CERT_THUMBPRINT, GRAPH_CERT_PATH, GRAPH_CERT_PASSWORD
"""
from __future__ import annotations

import json
import logging
import os

import msal
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend

log = logging.getLogger("shared.graph_auth")

_SCOPE = ["https://graph.microsoft.com/.default"]


def _load_cert_credential() -> dict:
    pfx_path = os.environ.get("GRAPH_CERT_PATH", "")
    pfx_password = os.environ.get("GRAPH_CERT_PASSWORD", "")
    thumbprint = os.environ.get("GRAPH_CERT_THUMBPRINT", "")

    if not pfx_path or not thumbprint:
        raise RuntimeError(
            "GRAPH_CERT_PATH and GRAPH_CERT_THUMBPRINT must be set "
            "in environment / local.settings.json"
        )

    with open(pfx_path, "rb") as f:
        pfx_data = f.read()

    password_bytes = pfx_password.encode() if pfx_password else None
    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_data, password_bytes, default_backend()
    )

    private_key_pem = private_key.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    ).decode()
    public_cert_pem = certificate.public_bytes(Encoding.PEM).decode()

    return {
        "private_key": private_key_pem,
        "thumbprint": thumbprint,
        "public_certificate": public_cert_pem,
    }


def _build_msal_app() -> msal.ConfidentialClientApplication:
    client_id = os.environ.get("GRAPH_CLIENT_ID", "")
    tenant_id = os.environ.get("GRAPH_TENANT_ID", "")

    if not client_id:
        raise RuntimeError("GRAPH_CLIENT_ID must be set")

    cert_credential = _load_cert_credential()
    return msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=cert_credential,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )


def get_graph_token() -> str:
    """Acquire a Graph access token using certificate-based client credentials."""
    app = _build_msal_app()
    result = app.acquire_token_for_client(scopes=_SCOPE)

    if result and "access_token" in result:
        log.info("Graph token acquired via certificate credentials flow.")
        return result["access_token"]

    error = result.get("error_description", result.get("error", "Unknown error"))
    raise RuntimeError(f"Certificate credentials auth failed: {error}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    settings_path = os.path.join(os.path.dirname(__file__), "..", "local.settings.json")
    if os.path.exists(settings_path):
        with open(settings_path) as f:
            settings = json.load(f)
        for k, v in settings.get("Values", {}).items():
            if v:
                os.environ[k] = v
    token = get_graph_token()
    print(f"Token acquired successfully (length={len(token)})")
