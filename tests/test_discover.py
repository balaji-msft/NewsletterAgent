"""Discover the correct repo path for the Power BI wiki page"""
import base64, json, os, requests

with open("local.settings.json") as f:
    settings = json.load(f)
for k, v in settings["Values"].items():
    os.environ.setdefault(k, v)

import config

token = base64.b64encode(f":{config.ADO_PAT}".encode()).decode()
headers = {"Authorization": f"Basic {token}"}

# 1. Check the wiki page metadata to find the actual path
print("=== Wiki Page Info (pageId 1140586) ===")
wiki_url = (
    f"{config.ADO_ORG_URL}/{config.ADO_PROJECT}"
    f"/_apis/wiki/wikis/Fabric/pages/1140586?api-version=7.1"
)
resp = requests.get(wiki_url, headers=headers, timeout=30)
if resp.ok:
    page = resp.json()
    print(f"  Path: {page.get('path')}")
    print(f"  GitItemPath: {page.get('gitItemPath')}")
    print(f"  SubPages: {page.get('subPages', [])[:3]}")
else:
    print(f"  Error: {resp.status_code} - trying alternate approach")

# 2. Also try the wiki pages list endpoint
print("\n=== Wiki Pages under root ===")
wiki_url2 = (
    f"{config.ADO_ORG_URL}/{config.ADO_PROJECT}"
    f"/_apis/wiki/wikis/Fabric/pages?path=/&recursionLevel=oneLevel&api-version=7.1"
)
resp2 = requests.get(wiki_url2, headers=headers, timeout=30)
if resp2.ok:
    data = resp2.json()
    print(f"  Root path: {data.get('path')}")
    print(f"  Root gitItemPath: {data.get('gitItemPath')}")
    for sp in data.get("subPages", [])[:10]:
        print(f"    SubPage: {sp.get('path')} | gitItemPath: {sp.get('gitItemPath', 'N/A')}")

# 3. Try several path patterns for commits (no URL encoding - let requests handle it)
print("\n=== Testing commit paths ===")
paths_to_try = [
    "/Trident/Fabric Experiences/Power BI",
    "/Fabric Experiences/Power BI",
    "/Power BI",
    "/Power-BI",
    "/Trident/Power-BI",
    "/Trident/Power BI",
]
for path in paths_to_try:
    url = (
        f"{config.ADO_ORG_URL}/{config.ADO_PROJECT}"
        f"/_apis/git/repositories/Fabric/commits"
        f"?searchCriteria.itemPath={path}&$top=1&api-version=7.1"
    )
    resp = requests.get(url, headers=headers, timeout=15)
    count = len(resp.json().get("value", [])) if resp.ok else f"ERR {resp.status_code}"
    print(f"  Path: {path:50s} => {count}")

# 4. Get repo tree to see actual folder structure
print("\n=== Repo tree (top-level items in Fabric repo, master branch) ===")
tree_url = (
    f"{config.ADO_ORG_URL}/{config.ADO_PROJECT}"
    f"/_apis/git/repositories/Fabric/items?recursionLevel=oneLevel&api-version=7.1"
)
resp = requests.get(tree_url, headers=headers, timeout=30)
if resp.ok:
    for item in resp.json().get("value", []):
        print(f"  {item.get('path')}")
