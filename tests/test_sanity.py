"""
Sanity test – check each tool individually via the real tool functions.
Run: python test_sanity.py
"""
import json
import os
import time

# Load settings from local.settings.json into env vars
with open("local.settings.json", "r") as f:
    settings = json.load(f)
for k, v in settings.get("Values", {}).items():
    os.environ.setdefault(k, v)

import config
import tools

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

results = []


def report(name, status, detail=""):
    results.append((name, status, detail))
    icon = {"PASS": "+", "FAIL": "!", "SKIP": "~"}[status]
    print(f"  [{icon}] {name}: {status}" + (f" - {detail}" if detail else ""))


print("=" * 60)
print("NEWSLETTER AGENT - SANITY TEST")
print("=" * 60)

# ── 1. get_wiki_commits (TSG) ──────────────────────────────────────
print("\n1. get_wiki_commits (TSG - Fabric wiki, Power BI folder)")
try:
    t0 = time.time()
    result = tools.get_wiki_commits(days_back=30)
    elapsed = time.time() - t0
    rows = json.loads(result)
    report("Wiki Commits (TSG)", PASS, f"{len(rows)} changes in {elapsed:.1f}s")
    if rows:
        r = rows[0]
        print(f"       Latest: {r['date']} - {r['author']} - {r['category']} - {r['filename'][:50]}")
        categories = {}
        for row in rows:
            cat = row["category"]
            categories[cat] = categories.get(cat, 0) + 1
        print(f"       Categories: {categories}")
except Exception as e:
    report("Wiki Commits (TSG)", FAIL, str(e))

# ── 2. get_eeez_features (Fabric Made EEE-z) ──────────────────────
print("\n2. get_eeez_features (New Feature Readiness, NF-PBI)")
try:
    t0 = time.time()
    result = tools.get_eeez_features()
    elapsed = time.time() - t0
    pages = json.loads(result)
    report("EEE-z Features", PASS, f"{len(pages)} NF-PBI pages in {elapsed:.1f}s")
    for p in pages:
        print(f"       - {p['title']}")
except Exception as e:
    report("EEE-z Features", FAIL, str(e))

# ── 3. get_ado_query_results (CSS Feedback) ────────────────────────
print("\n3. get_ado_query_results (CSS Feedback)")
try:
    qid = config.CSS_FEEDBACK_QUERY_ID
    if not qid or qid.startswith("<"):
        report("CSS Feedback Query", SKIP, "Query ID not configured")
    else:
        result = tools.get_ado_query_results(
            query_id=qid,
            org_url=config.CSS_FEEDBACK_ORG_URL,
            project=config.CSS_FEEDBACK_PROJECT,
        )
        items = json.loads(result)
        report("CSS Feedback Query", PASS, f"{len(items)} work items")
        if items:
            print(f"       First: [{items[0]['state']}] {items[0]['title'][:60]}")
except Exception as e:
    report("CSS Feedback Query", FAIL, str(e))

# ── 4. get_ado_query_results (CSS Taxonomy - different org) ────────
print("\n4. get_ado_query_results (CSS Taxonomy - different org)")
try:
    qid = config.CSS_TAXONOMY_QUERY_ID
    if not qid or qid.startswith("<"):
        report("CSS Taxonomy Query", SKIP, "Query ID not configured")
    else:
        result = tools.get_ado_query_results(
            query_id=qid,
            org_url=config.CSS_TAXONOMY_ORG_URL,
            project=config.CSS_TAXONOMY_PROJECT,
        )
        items = json.loads(result)
        report("CSS Taxonomy Query", PASS, f"{len(items)} work items")
        if items:
            print(f"       First: [{items[0]['state']}] {items[0]['title'][:60]}")
except Exception as e:
    report("CSS Taxonomy Query", FAIL, str(e))

# ── 5. get_hot_topics_files (Local folder) ─────────────────────────
print("\n5. get_hot_topics_files (Local Hot Topics folder)")
try:
    folder = config.HOT_TOPICS_FOLDER
    if not folder or not os.path.isdir(folder):
        report("Hot Topics Files", SKIP, f"Folder not found: {folder}")
    else:
        result = tools.get_hot_topics_files()
        files = json.loads(result)
        report("Hot Topics Files", PASS, f"{len(files)} files")
        for f in files:
            print(f"       - {f.get('filename', '?')}")
except Exception as e:
    report("Hot Topics Files", FAIL, str(e))

# ── 6. get_static_content (V-Team) ────────────────────────────────
print("\n6. get_static_content (V-Team)")
try:
    result = tools.get_static_content("vteam")
    if result and len(result) > 5:
        report("Static Content", PASS, f"{len(result)} chars")
    else:
        report("Static Content", FAIL, "Empty or too short")
except Exception as e:
    report("Static Content", FAIL, str(e))

# ── 7. Azure AI Foundry SDK ───────────────────────────────────────
print("\n7. Azure AI Foundry - SDK import & client")
try:
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = config.AI_PROJECT_ENDPOINT
    if not endpoint or endpoint.startswith("<"):
        report("AI Foundry Client", SKIP, "Endpoint not configured")
    else:
        credential = DefaultAzureCredential()
        client = AIProjectClient(endpoint=endpoint, credential=credential)
        report("AI Foundry Client", PASS, f"SDK ready, endpoint: {endpoint[:50]}...")
except ImportError as e:
    report("AI Foundry Client", FAIL, f"Missing package: {e}")
except Exception as e:
    report("AI Foundry Client", FAIL, str(e))

# ── Summary ─────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
skipped = sum(1 for _, s, _ in results if s == SKIP)
print(f"  Passed: {passed}  |  Failed: {failed}  |  Skipped: {skipped}")
if failed:
    print("\nFailed tests:")
    for name, status, detail in results:
        if status == FAIL:
            print(f"  - {name}: {detail}")
print()
