"""
Shared Azure OpenAI client factory.
Creates an AzureOpenAI client authenticated via Entra ID (DefaultAzureCredential).
"""
from __future__ import annotations

import logging
import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

log = logging.getLogger("shared.openai_client")


def create_openai_client(
    endpoint: str | None = None,
    api_version: str | None = None,
    deployment: str | None = None,
) -> AzureOpenAI:
    """Create an AzureOpenAI client with Entra ID auth.

    Falls back to env vars: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION,
    MODEL_DEPLOYMENT.
    """
    endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    api_version = api_version or os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    deployment = deployment or os.environ.get("MODEL_DEPLOYMENT", "gpt-4.1")

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version=api_version,
    )
    log.info("OpenAI client ready  endpoint=%s  model=%s", endpoint, deployment)
    return client
