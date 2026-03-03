"""Quick test: verify commits under /Power-BI path"""
import base64, json, os, requests

with open("local.settings.json") as f:
    settings = json.load(f)
for k, v in settings["Values"].items():
    os.environ.setdefault(k, v)

import config

token = base64.b64encode(f":{config.ADO_PAT}".encode()).decode()
headers = {"Authorization": f"Basic {token}"}
url = (
    f"{config.ADO_ORG_URL}/{config.ADO_PROJECT}"
    f"/_apis/git/repositories/{config.TSG_REPO_NAME}/commits"
    f"?searchCriteria.itemPath=/Power-BI&$top=5&api-version=7.1"
)
resp = requests.get(url, headers=headers, timeout=30)
resp.raise_for_status()
commits = resp.json().get("value", [])
print(f"Found {len(commits)} commits under /Power-BI:")
for c in commits:
    date = c["author"]["date"][:10]
    author = c["author"]["name"][:20]
    msg = c["comment"][:70]
    print(f"  {date} | {author} | {msg}")
