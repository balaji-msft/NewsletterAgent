"""
Sprint Summary Agent.

Uses Azure OpenAI chat completions with function calling to:
1. Fetch work-item data from a saved ADO query
2. Analyse the data and write a concise sprint summary

Authenticates via Entra ID (DefaultAzureCredential).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from sprintsummary import config as cfg
from sprintsummary import tools
from shared.openai_client import create_openai_client

logger = logging.getLogger("sprintsummary.agent")

# ── Tool definition (OpenAI function-calling schema) ────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_sprint_query_results",
            "description": (
                "Execute the saved Azure DevOps work-item query for Sprint Summary data. "
                "Returns a JSON array of work items, each with id, title, state, "
                "assignedTo, type, and completedWork. No parameters needed."
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
            "name": "send_email",
            "description": (
                "Send the compiled Sprint Summary HTML via email using Power Automate webhook."
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
                        "description": "Full HTML body of the Sprint Summary email.",
                    },
                    "to_recipients": {
                        "type": "string",
                        "description": "Semicolon-separated email addresses. Leave empty to use defaults.",
                    },
                },
                "required": ["subject", "html_body"],
            },
        },
    },
]

# ── Prompt loading from prompt.yaml ─────────────────────────────────

CURRENT_MONTH = datetime.now(timezone.utc).strftime("%B %Y")

_PROMPT_YAML = Path(__file__).with_name("prompt.yaml")


def _load_prompt_yaml() -> dict:
    """Load prompt.yaml and resolve {{placeholder}} tokens."""
    with open(_PROMPT_YAML, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    replacements = {
        "current_month": CURRENT_MONTH,
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
DEFAULT_USER_PROMPT = get_default_user_prompt()

# ── Agent machinery ─────────────────────────────────────────────────

MAX_TOOL_ROUNDS = 10


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
    log_dir = Path(__file__).resolve().parent.parent / "logs" / f"sprint_{ts}"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _safe_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)


def run_sprint_summary_agent(user_prompt: str | None = None) -> str:
    """
    Run the Sprint Summary Agent.

    1. Fetches ADO query data via function calling.
    2. Produces an HTML sprint summary of completed work items.

    Returns the final HTML string.
    """
    client = create_openai_client(
        endpoint=cfg.AZURE_OPENAI_ENDPOINT,
        api_version=cfg.AZURE_OPENAI_API_VERSION,
        deployment=cfg.MODEL_DEPLOYMENT,
    )
    log_dir = _create_log_dir()
    tool_call_counter = 0
    captured_html: str | None = None
    logger.info("Sprint Summary tool output logs: %s", log_dir)

    oai_tools = [
        {"type": "function", "function": td["function"]}
        for td in TOOL_DEFINITIONS
    ]

    if not user_prompt:
        user_prompt = DEFAULT_USER_PROMPT

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    for round_num in range(MAX_TOOL_ROUNDS):
        logger.info("Chat completion round %d ...", round_num + 1)
        response = client.chat.completions.create(
            model=cfg.MODEL_DEPLOYMENT,
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
                logger.info(
                    "Tool %s → %d chars → %s",
                    tc.function.name, len(output), log_file.name,
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": output,
                })
            continue

        final_text = choice.message.content or ""
        logger.info("Sprint Summary agent finished after %d rounds.", round_num + 1)
        if captured_html:
            logger.info("Returning captured HTML from send_email (%d chars).", len(captured_html))
            return captured_html
        return final_text

    return "Sprint Summary agent hit maximum tool-call rounds without producing a final response."
