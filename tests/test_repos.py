"""Check repos and wiki info"""
import base64, json, os, requests

with open("local.settings.json") as f:
    settings = json.load(f)
for k, v in settings["Values"].items():
    os.environ.setdefault(k, v)

import config

token = base64.b64encode(f":{config.ADO_PAT}".encode()).decode()
headers = {"Authorization": f"Basic {token}"}

# List repos
print("=== Git Repositories ===")
url = f"{config.ADO_ORG_URL}/{config.ADO_PROJECT}/_apis/git/repositories?api-version=7.1"
resp = requests.get(url, headers=headers, timeout=30)
resp.raise_for_status()
for repo in resp.json().get("value", []):
    print(f"  {repo['name']} (id: {repo['id'][:12]}...)")

# List wikis
print("\n=== Wikis ===")
url = f"{config.ADO_ORG_URL}/{config.ADO_PROJECT}/_apis/wiki/wikis?api-version=7.1"
resp = requests.get(url, headers=headers, timeout=30)
resp.raise_for_status()
for wiki in resp.json().get("value", []):
    print(f"  Wiki: {wiki['name']}")
    print(f"    Type: {wiki.get('type', 'unknown')}")
    print(f"    Repo ID: {wiki.get('repositoryId', 'N/A')}")
    mapped = wiki.get("mappedPath", "N/A")
    print(f"    Mapped path: {mapped}")
    # If project wiki, the repo might have a different name
    if "repositoryId" in wiki:
        repo_url = f"{config.ADO_ORG_URL}/{config.ADO_PROJECT}/_apis/git/repositories/{wiki['repositoryId']}?api-version=7.1"
        r2 = requests.get(repo_url, headers=headers, timeout=30)
        if r2.ok:
            print(f"    Repo name: {r2.json()['name']}")
