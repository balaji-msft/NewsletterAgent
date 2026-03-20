"""
Azure DevOps client — shared across all agents.
Handles wiki-backed repos, code wiki path mapping, commit scanning,
and work-item query execution.

Authentication: Uses Entra ID (DefaultAzureCredential) by default.
Falls back to PAT-based auth when a PAT is explicitly provided.
"""
from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote, unquote

import requests
from azure.identity import DefaultAzureCredential

log = logging.getLogger("shared.ado")

_DASH_PLACEHOLDER = "\x00"

# Azure DevOps resource ID for Entra ID tokens
_ADO_RESOURCE = "499b84ac-1321-427f-aa17-267ca6975798/.default"

_credential = DefaultAzureCredential()
_token_lock = threading.Lock()


# ── helpers ───────────────────────────────────────────────────────────

def _get_ado_headers() -> dict[str, str]:
    """Get Authorization header using Entra ID bearer token."""
    with _token_lock:
        token = _credential.get_token(_ADO_RESOURCE)
    return {"Authorization": f"Bearer {token.token}"}


def _auth_kwargs(pat: str | None) -> dict:
    """Return either auth= or headers= kwargs for requests, depending on auth mode."""
    if pat:
        return {"auth": ("", pat)}
    return {"headers": _get_ado_headers()}


def _check_auth(resp: requests.Response, context: str = "") -> None:
    is_html = "text/html" in resp.headers.get("content-type", "")
    looks_like_signin = is_html or "Sign In" in resp.text[:200]
    if resp.status_code in (401, 403) or looks_like_signin:
        raise PermissionError(
            f"ADO authentication failed ({context}). "
            "Check your Entra ID identity (or PAT) has the required scopes and has not expired."
        )


def _categorize(change_type: str) -> str:
    ct = change_type.lower()
    if "add" in ct:
        return "NEW"
    if "edit" in ct:
        return "EDIT"
    if "delete" in ct:
        return "DELETE"
    if "rename" in ct:
        return "RENAME"
    return "OTHER"


def _git_path_to_wiki_path(git_path: str, mapped_path: str = "/") -> str:
    path = git_path
    if path.endswith(".md"):
        path = path[:-3]
    if mapped_path and mapped_path != "/":
        prefix = mapped_path.rstrip("/")
        if path.startswith(prefix):
            path = path[len(prefix):] or "/"
    path = path.replace("%2D", _DASH_PLACEHOLDER)
    path = path.replace("-", " ")
    path = path.replace(_DASH_PLACEHOLDER, "-")
    path = unquote(path)
    return path


def _wiki_link(org: str, project: str, wiki: str, wiki_path: str) -> str:
    encoded_path = quote(wiki_path, safe="/")
    return f"https://{org}.visualstudio.com/{project}/_wiki/wikis/{wiki}?pagePath={encoded_path}"


# ── public API ────────────────────────────────────────────────────────

def fetch_wikis(org: str, project: str, pat: str | None = None) -> list[dict]:
    p = quote(project, safe="")
    url = f"https://dev.azure.com/{org}/{p}/_apis/wiki/wikis?api-version=7.1"
    resp = requests.get(url, **_auth_kwargs(pat), timeout=15)
    _check_auth(resp, "wiki list")
    if resp.status_code != 200:
        return []
    return resp.json().get("value", [])


def match_wiki_for_repo(wikis: list[dict], repo: str) -> tuple[str, str, str]:
    for w in wikis:
        if w["name"] == repo or w["repositoryId"] == repo:
            return w["name"], w.get("mappedPath", "/"), w["type"]
    return repo, "/", "unknown"


def fetch_wiki_page(
    org: str, project: str, wiki: str, pat: str | None = None,
    path: str = "/", recursion: str = "oneLevel", include_content: bool = False,
) -> dict | None:
    p = quote(project, safe="")
    w = quote(wiki, safe="")
    encoded_path = quote(path, safe="/")
    url = (
        f"https://dev.azure.com/{org}/{p}/_apis/wiki/wikis/{w}/pages"
        f"?path={encoded_path}"
        f"&recursionLevel={recursion}"
        f"&includeContent={'true' if include_content else 'false'}"
        f"&api-version=7.1"
    )
    resp = requests.get(url, **_auth_kwargs(pat), timeout=30)
    _check_auth(resp, f"wiki page {path}")
    if resp.status_code != 200:
        log.warning("Wiki page %s returned %d", path, resp.status_code)
        return None
    return resp.json()


def fetch_wiki_child_pages(
    org: str, project: str, wiki: str, pat: str | None = None,
    parent_path: str = "/", title_filter: str = "",
) -> list[dict]:
    page = fetch_wiki_page(org, project, wiki, pat, parent_path, recursion="oneLevel")
    if page is None:
        return []

    children = page.get("subPages", [])
    results = []
    for child in children:
        child_path = child.get("path", "")
        title = child_path.rsplit("/", 1)[-1]
        if title.startswith("."):
            continue
        if title_filter and title_filter.lower() not in title.lower():
            continue
        link = _wiki_link(org, project, wiki, child_path)
        results.append({"title": title, "path": child_path, "wiki_link": link})

    log.info("Listed %d child pages under %s (filter=%s)", len(results), parent_path, title_filter)
    return results


def fetch_wiki_page_content(
    org: str, project: str, wiki: str, pat: str | None = None, path: str = "/",
) -> str:
    page = fetch_wiki_page(org, project, wiki, pat, path, include_content=True)
    if page is None:
        return ""
    return page.get("content", "")


def fetch_commits(
    org: str, project: str, repo: str, pat: str | None = None,
    start_date: str = "", end_date: str = "", item_path: str = "",
) -> list[dict]:
    p = quote(project, safe="")
    r = quote(repo, safe="")
    base_url = (
        f"https://dev.azure.com/{org}/{p}/_apis/git/repositories/{r}/commits"
        f"?searchCriteria.fromDate={start_date}"
        f"&searchCriteria.toDate={end_date}"
        f"&$top=1000"
        f"&api-version=7.1-preview.1"
    )
    if item_path:
        base_url += f"&searchCriteria.itemPath={quote(item_path, safe='/')}"

    auth_kw = _auth_kwargs(pat)
    all_commits: list[dict] = []
    skip = 0
    while True:
        url = f"{base_url}&$skip={skip}" if skip else base_url
        resp = requests.get(url, **auth_kw, timeout=60)
        _check_auth(resp, "commits")
        if resp.status_code != 200:
            raise RuntimeError(f"ADO error {resp.status_code}: {resp.text[:300]}")
        batch = resp.json().get("value", [])
        if not batch:
            break
        all_commits.extend(batch)
        if len(batch) < 1000:
            break
        skip += len(batch)
    return all_commits


def fetch_commit_changes(
    org: str, project: str, repo: str, pat: str | None = None, commit_id: str = "",
) -> list[dict]:
    p = quote(project, safe="")
    r = quote(repo, safe="")
    url = (
        f"https://dev.azure.com/{org}/{p}/_apis/git/repositories/{r}"
        f"/commits/{commit_id}/changes?api-version=7.1-preview.1"
    )
    resp = requests.get(url, **_auth_kwargs(pat), timeout=30)
    if resp.status_code != 200:
        return []
    return resp.json().get("changes", [])


def fetch_wiki_commits_for_folder(
    org: str, project: str, repo: str, pat: str | None = None,
    start_date: str = "", end_date: str = "",
    wiki_name: str = "", folder_filter: str = "",
) -> list[dict]:
    wikis = fetch_wikis(org, project, pat)
    effective_wiki, mapped_path, wiki_type = match_wiki_for_repo(wikis, wiki_name or repo)
    log.info("Wiki resolved: name=%s type=%s mappedPath=%s", effective_wiki, wiki_type, mapped_path)

    item_path = ""
    if wiki_type == "codeWiki" and mapped_path and mapped_path != "/":
        item_path = mapped_path.rstrip("/")

    commits = fetch_commits(org, project, repo, pat, start_date, end_date, item_path=item_path)
    log.info("Fetched %d commits", len(commits))

    git_folder_prefix = ""
    if folder_filter and mapped_path:
        ff = folder_filter if folder_filter.startswith("/") else f"/{folder_filter}"
        git_folder = ff.replace(" ", "-")
        mp = mapped_path.rstrip("/")
        git_folder_prefix = f"{mp}{git_folder}".lower()
        log.info("Git folder prefix filter: %s", git_folder_prefix)

    rows: list[dict] = []

    def _process_commit(commit):
        commit_id = commit["commitId"]
        author = commit["author"]["name"]
        date = commit["author"]["date"]
        message = commit.get("comment", "")
        changes = fetch_commit_changes(org, project, repo, pat, commit_id)
        result = []
        for change in changes:
            item = change.get("item", {})
            file_path = item.get("path", "")
            if not file_path.endswith(".md"):
                continue
            if git_folder_prefix and not file_path.lower().startswith(git_folder_prefix):
                continue
            change_type = change.get("changeType", "edit")
            category = _categorize(change_type)
            wiki_path = _git_path_to_wiki_path(file_path, mapped_path)
            wiki_link_url = _wiki_link(org, project, effective_wiki, wiki_path)
            result.append({
                "date": date[:10], "author": author, "message": message,
                "filename": wiki_path.split("/")[-1], "wiki_path": wiki_path,
                "full_git_path": file_path, "category": category,
                "change_type": change_type, "wiki_link": wiki_link_url,
                "commit_id": commit_id[:8],
                "commit_link": f"https://dev.azure.com/{org}/{project}/_git/{repo}/commit/{commit_id}",
            })
        return result

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_process_commit, c): c for c in commits}
        for fut in as_completed(futures):
            try:
                rows.extend(fut.result())
            except Exception as e:
                log.warning("Commit processing error: %s", e)

    rows.sort(key=lambda r: r["date"], reverse=True)
    log.info("Processed %d wiki changes (folder_filter=%s)", len(rows), folder_filter)
    return rows


def fetch_ado_query_results(
    org_url: str, project: str, pat: str | None = None, query_id: str = "",
) -> list[dict]:
    auth_kw = _auth_kwargs(pat)
    p = quote(project, safe="")
    url = f"{org_url}/{p}/_apis/wit/wiql/{query_id}?api-version=7.1"
    resp = requests.get(url, **auth_kw, timeout=60)
    _check_auth(resp, "work item query")
    if resp.status_code != 200:
        raise RuntimeError(f"Query failed HTTP {resp.status_code}: {resp.text[:300]}")
    query_result = resp.json()

    work_item_ids = [wi["id"] for wi in query_result.get("workItems", [])]
    if not work_item_ids:
        return []

    items: list[dict] = []
    for i in range(0, len(work_item_ids), 200):
        batch = work_item_ids[i: i + 200]
        ids_param = ",".join(str(x) for x in batch)
        detail_url = (
            f"{org_url}/{p}/_apis/wit/workitems?ids={ids_param}"
            f"&fields=System.Id,System.Title,System.State,"
            f"System.AssignedTo,System.CreatedDate,System.WorkItemType,"
            f"Microsoft.VSTS.Scheduling.CompletedWork"
            f"&api-version=7.1"
        )
        r = requests.get(detail_url, **auth_kw, timeout=60)
        _check_auth(r, "work item details")
        if r.status_code != 200:
            continue
        for wi in r.json().get("value", []):
            fields = wi.get("fields", {})
            items.append({
                "id": fields.get("System.Id"),
                "title": fields.get("System.Title"),
                "state": fields.get("System.State"),
                "assignedTo": fields.get("System.AssignedTo", {}).get("displayName", ""),
                "type": fields.get("System.WorkItemType"),
                "completedWork": fields.get("Microsoft.VSTS.Scheduling.CompletedWork", 0),
            })
    return items
