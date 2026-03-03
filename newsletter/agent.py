"""
Azure AI Newsletter Agent – Newsletter Compiler.

Uses Azure OpenAI chat completions with function calling (tools).
Authenticates via Entra ID (DefaultAzureCredential).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from newsletter import config
from newsletter import tools
from shared.openai_client import create_openai_client

logger = logging.getLogger("newsletter.agent")

# ── Tool definitions (JSON schemas for the LLM) ────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_hot_topics_files",
            "description": (
                "Read ALL files from the local Hot Topics folder. "
                "Returns a JSON array of {filename, content} for each file. "
                "No parameters needed — uses pre-configured folder path."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_wiki_commits",
            "description": (
                "Fetch recent wiki page changes from the Fabric code wiki, scoped to a "
                "specific folder. Returns a deduplicated JSON array of unique pages with "
                "component (team name like DORE, ASWL), page, and wiki_link."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_filter": {
                        "type": "string",
                        "description": (
                            "Wiki folder path to scope to, e.g. '/Fabric Experiences/Power BI'. "
                            "Defaults to TSG_WIKI_FOLDER config value if omitted."
                        ),
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to look back (default 30).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_eeez_features",
            "description": (
                "List new-feature wiki pages from the Fabric wiki under "
                "/New Feature Readiness/{year}/{month}, filtered to pages "
                "whose title contains a substring (default: NF-PBI). "
                "Returns JSON array with title, path, wiki_link, and page content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Year (e.g. 2026). Defaults to current year.",
                    },
                    "month": {
                        "type": "string",
                        "description": "3-letter month abbreviation (e.g. 'Feb'). Defaults to previous month.",
                    },
                    "title_filter": {
                        "type": "string",
                        "description": "Substring to filter page titles (default: NF-PBI).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ado_query_results",
            "description": (
                "Execute a saved Azure DevOps work-item query and return results as JSON. "
                "Each item includes id, title, state, assignedTo, type, completedWork. "
                "Supports querying different ADO orgs by passing org_url and project."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query_id": {
                        "type": "string",
                        "description": "The GUID of the saved ADO work-item query.",
                    },
                    "org_url": {
                        "type": "string",
                        "description": "ADO organization URL. Defaults to main org if omitted.",
                    },
                    "project": {
                        "type": "string",
                        "description": "ADO project name. Defaults to main project if omitted.",
                    },
                },
                "required": ["query_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_static_content",
            "description": (
                "Return pre-configured static HTML content for a newsletter section."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "section_name": {
                        "type": "string",
                        "description": "Section identifier, e.g. 'vteam'.",
                    },
                },
                "required": ["section_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send the compiled HTML newsletter via email using Power Automate webhook."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Email subject line.",
                    },
                    "html_body": {
                        "type": "string",
                        "description": "Full HTML body of the newsletter email.",
                    },
                    "to_recipients": {
                        "type": "string",
                        "description": "Comma-separated email addresses. Leave empty to use defaults.",
                    },
                },
                "required": ["subject", "html_body"],
            },
        },
    },
]

# ── System prompt ───────────────────────────────────────────────────

CURRENT_MONTH = datetime.now(timezone.utc).strftime("%B %Y")

# ── Prompt loading from prompt.yaml ─────────────────────────────────

_PROMPT_YAML = Path(__file__).with_name("prompt.yaml")


def _load_prompt_yaml() -> dict:
    """Load prompt.yaml and resolve {{placeholder}} tokens from config."""
    with open(_PROMPT_YAML, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    replacements = {
        "current_month": CURRENT_MONTH,
        "tsg_wiki_folder": config.TSG_WIKI_FOLDER,
        "css_feedback_query_id": config.CSS_FEEDBACK_QUERY_ID,
        "css_feedback_org_url": config.CSS_FEEDBACK_ORG_URL,
        "css_feedback_project": config.CSS_FEEDBACK_PROJECT,
        "css_taxonomy_query_id": config.CSS_TAXONOMY_QUERY_ID,
        "css_taxonomy_org_url": config.CSS_TAXONOMY_ORG_URL,
        "css_taxonomy_project": config.CSS_TAXONOMY_PROJECT,
        "email_subject_prefix": config.EMAIL_SUBJECT_PREFIX,
    }

    def _render(text: str) -> str:
        for key, val in replacements.items():
            text = text.replace("{{" + key + "}}", str(val))
        return text

    return {k: _render(v) if isinstance(v, str) else v for k, v in raw.items()}


def get_system_prompt() -> str:
    return _load_prompt_yaml()["system_prompt"]


def get_default_user_prompt() -> str:
    return _load_prompt_yaml()["default_user_prompt"]


SYSTEM_PROMPT = get_system_prompt()

# ── Agent creation & execution ──────────────────────────────────────

MAX_TOOL_ROUNDS = 15


def _dispatch_tool_call(tool_name: str, arguments: dict) -> str:
    func = tools.TOOL_FUNCTIONS.get(tool_name)
    if func is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return func(**arguments)
    except Exception as e:
        logger.exception("Tool %s failed", tool_name)
        return json.dumps({"error": str(e)})


def _create_log_dir() -> Path:
    """Create a timestamped logs directory for this run."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Logs go to <project_root>/logs/
    log_dir = Path(__file__).resolve().parent.parent / "logs" / ts
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _safe_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)


def run_newsletter_agent(user_prompt: str | None = None) -> str:
    """
    Use Azure OpenAI chat completions with function calling to compile
    the newsletter.
    """
    client = create_openai_client(
        endpoint=config.AZURE_OPENAI_ENDPOINT,
        api_version=config.AZURE_OPENAI_API_VERSION,
        deployment=config.MODEL_DEPLOYMENT,
    )
    log_dir = _create_log_dir()
    tool_call_counter = 0
    captured_html: str | None = None
    logger.info("Tool output logs: %s", log_dir)

    oai_tools = [
        {"type": "function", "function": td["function"]}
        for td in TOOL_DEFINITIONS
    ]

    if not user_prompt:
        user_prompt = get_default_user_prompt()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    for round_num in range(MAX_TOOL_ROUNDS):
        logger.info("Chat completion round %d ...", round_num + 1)
        response = client.chat.completions.create(
            model=config.MODEL_DEPLOYMENT,
            messages=messages,
            tools=oai_tools,
            tool_choice="auto",
        )
        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" or choice.message.tool_calls:
            assistant_msg = {
                "role": "assistant",
                "content": choice.message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ],
            }
            messages.append(assistant_msg)

            for tc in choice.message.tool_calls:
                args = json.loads(tc.function.arguments)
                logger.info("Tool call: %s(%s)", tc.function.name, args)

                if tc.function.name == "send_email" and "html_body" in args:
                    captured_html = args["html_body"]

                output = _dispatch_tool_call(tc.function.name, args)

                tool_call_counter += 1
                fname = f"{tool_call_counter:02d}_{_safe_filename(tc.function.name)}.json"
                log_file = log_dir / fname
                log_payload = {
                    "tool": tc.function.name,
                    "arguments": args,
                    "output_length": len(output),
                    "output": output,
                }
                log_file.write_text(
                    json.dumps(log_payload, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                preview = output[:200] + ("..." if len(output) > 200 else "")
                logger.info(
                    "Tool %s returned %d chars → %s  (preview: %s)",
                    tc.function.name, len(output), log_file.name, preview,
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": output,
                })
            continue

        final_text = choice.message.content or ""
        logger.info("Agent finished after %d rounds.", round_num + 1)
        if captured_html:
            logger.info("Returning captured HTML from send_email (%d chars).", len(captured_html))
            return captured_html
        return final_text

    return "Agent hit maximum tool-call rounds without producing a final response."
