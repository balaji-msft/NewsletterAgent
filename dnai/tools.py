"""
Tool implementations for the DnAI Newsletter Agent.

Identical behaviour to the Power BI newsletter agent tools, but reads config
from the dnai package so product-specific overrides take effect.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import requests
from datetime import datetime, timedelta, timezone

from dnai import config
from shared import ado_client


# ════════════════════════════════════════════════════════════════════
# Helper – Microsoft Graph authentication
# ════════════════════════════════════════════════════════════════════

def _graph_access_token() -> str:
    from shared import graph_auth
    return graph_auth.get_graph_token()


def _graph_headers() -> dict[str, str]:
    token = _graph_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ════════════════════════════════════════════════════════════════════
# 1. Hot Topics
# ════════════════════════════════════════════════════════════════════

_TEXT_EXTENSIONS = {".md", ".txt", ".html", ".htm", ".csv", ".json", ".xml"}


def get_hot_topics_files() -> str:
    folder = pathlib.Path(config.HOT_TOPICS_FOLDER)
    if not folder.exists():
        return json.dumps({"error": f"Folder not found: {folder}"})

    file_contents = []
    for fpath in sorted(folder.iterdir()):
        if fpath.is_dir():
            continue
        try:
            if fpath.suffix.lower() in _TEXT_EXTENSIONS:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                if len(content) > 4000:
                    content = content[:4000] + "\n... [truncated]"
            else:
                content = f"[Binary file – {fpath.suffix}, {fpath.stat().st_size} bytes]"
            file_contents.append({"filename": fpath.name, "content": content})
        except Exception as e:
            file_contents.append({"filename": fpath.name, "error": str(e)})

    return json.dumps(file_contents, indent=2)


# ════════════════════════════════════════════════════════════════════
# 2. ADO Wiki Commits – TSG
# ════════════════════════════════════════════════════════════════════

def get_wiki_commits(
    folder_filter: str | None = None,
    days_back: int = 30,
    year: int | None = None,
    month: int | None = None,
) -> str:
    import calendar as _cal
    folder_filter = folder_filter or config.TSG_WIKI_FOLDER
    org = config.ADO_ORG
    project = config.ADO_PROJECT
    repo = config.TSG_REPO_NAME
    pat = config.ADO_PAT or None  # None triggers Entra ID fallback

    now = datetime.now(timezone.utc)
    if year and month:
        last_day = _cal.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01T00:00:00Z"
        end_date = f"{year}-{month:02d}-{last_day:02d}T23:59:59Z"
    else:
        start_date = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")
        end_date = now.strftime("%Y-%m-%dT23:59:59Z")

    rows = ado_client.fetch_wiki_commits_for_folder(
        org=org, project=project, repo=repo, pat=pat,
        start_date=start_date, end_date=end_date,
        wiki_name=config.TSG_WIKI_NAME, folder_filter=folder_filter,
    )

    rows = [r for r in rows if r.get("category") in ("NEW", "EDIT", "RENAME")]

    category_priority = {"NEW": 0, "RENAME": 1, "EDIT": 2}
    seen: dict[str, dict] = {}
    base_depth = len([p for p in (folder_filter or "").strip("/").split("/") if p])

    for r in rows:
        link = r.get("wiki_link", "")
        cat = r.get("category", "EDIT")
        wiki_path = r.get("wiki_path", "")
        if wiki_path:
            parts = wiki_path.rsplit("/", 1)
            folder = parts[0] if len(parts) > 1 else ""
            page = parts[-1]
        else:
            decoded = link.split("/wikis/")[-1] if "/wikis/" in link else link
            decoded = decoded.replace("%2F", "/").replace("%3A%3A", "::").replace("-", " ")
            parts = decoded.rsplit("/", 1)
            folder = parts[0] if len(parts) > 1 else ""
            page = parts[-1]

        folder_segments = [p for p in folder.strip("/").split("/") if p]
        component = folder_segments[base_depth] if len(folder_segments) > base_depth else ""

        entry = {"component": component, "page": page, "wiki_link": link}
        if link not in seen or category_priority.get(cat, 9) < category_priority.get(seen[link].get("_cat", "EDIT"), 9):
            entry["_cat"] = cat
            seen[link] = entry

    for v in seen.values():
        cat = v.pop("_cat", "EDIT")
        v["status"] = "New" if cat == "NEW" else "Updated"
    slim_rows = sorted(seen.values(), key=lambda r: (r["component"], r["page"]))
    slim_rows = slim_rows[:50]
    return json.dumps(slim_rows, indent=2)


# ════════════════════════════════════════════════════════════════════
# 3. Fabric Made EEE-z
# ════════════════════════════════════════════════════════════════════

def get_eeez_features(
    year: int | None = None,
    month: str | None = None,
    title_filter: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    year = year or int(config.EEEZ_YEAR or now.year)
    month = month or config.EEEZ_MONTH or _prev_month_abbr(now)
    title_filter = title_filter or config.EEEZ_TITLE_FILTER

    parent_path = f"/New Feature Readiness/{year}/{month}"
    org = config.ADO_ORG
    project = config.ADO_PROJECT
    wiki = config.TSG_WIKI_NAME
    pat = config.ADO_PAT or None

    pages = ado_client.fetch_wiki_child_pages(
        org, project, wiki, pat=pat,
        parent_path=parent_path, title_filter=title_filter,
    )

    for page in pages:
        content = ado_client.fetch_wiki_page_content(
            org, project, wiki, pat=pat, path=page["path"]
        )
        page["content"] = content[:2000] if len(content) > 2000 else content

    return json.dumps(pages, indent=2)


def _prev_month_abbr(dt: datetime) -> str:
    first_of_month = dt.replace(day=1)
    prev = first_of_month - timedelta(days=1)
    return prev.strftime("%b")


# ════════════════════════════════════════════════════════════════════
# 4. ADO Work-Item Queries – CSS Feedback & Taxonomy
# ════════════════════════════════════════════════════════════════════

def get_ado_query_results(
    query_id: str,
    org_url: str | None = None,
    project: str | None = None,
) -> str:
    org_url = org_url or config.ADO_ORG_URL
    project = project or config.ADO_PROJECT

    # Pick the right PAT for the org; empty string → None → Entra ID fallback
    if org_url == config.CSS_TAXONOMY_ORG_URL:
        pat = config.CSS_TAXONOMY_PAT or config.ADO_PAT or None
    elif org_url == config.CSS_FEEDBACK_ORG_URL:
        pat = config.CSS_FEEDBACK_PAT or config.ADO_PAT or None
    else:
        pat = config.ADO_PAT or None

    items = ado_client.fetch_ado_query_results(org_url, project, pat=pat, query_id=query_id)

    bracket_re = re.compile(r"^\[CSSFeedback\]\[([^\]]+)\]\[[^\]]+\]\s*[-:]?\s*(.*)$", re.IGNORECASE)
    for item in items:
        title = item.get("title", "")
        m = bracket_re.match(title)
        if m:
            item["feedback_category"] = m.group(1).strip()
            item["short_title"] = m.group(2).strip()

    return json.dumps(items, indent=2)


# ════════════════════════════════════════════════════════════════════
# 5. Static Content – Component V-Team
# ════════════════════════════════════════════════════════════════════

def get_static_content(section_name: str = "vteam") -> str:
    if section_name == "vteam":
        md_path = config.VTEAM_MD_FILE
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "<p>V-Team file not found.</p>"
    return "<p>No content available.</p>"


# ════════════════════════════════════════════════════════════════════
# 6. Send Email
# ════════════════════════════════════════════════════════════════════

def send_email(
    subject: str,
    html_body: str,
    to_recipients: str | None = None,
) -> str:
    from shared.email_sender import send_email as _send

    to = to_recipients or config.EMAIL_RECIPIENTS
    return _send(
        subject=subject,
        html_body=html_body,
        to_recipients=to,
        webhook_url=config.POWER_AUTOMATE_WEBHOOK_URL,
    )


# ════════════════════════════════════════════════════════════════════
# Tool dispatcher
# ════════════════════════════════════════════════════════════════════

TOOL_FUNCTIONS: dict[str, callable] = {
    "get_hot_topics_files": get_hot_topics_files,
    "get_wiki_commits": get_wiki_commits,
    "get_eeez_features": get_eeez_features,
    "get_ado_query_results": get_ado_query_results,
    "get_static_content": get_static_content,
    "send_email": send_email,
}
