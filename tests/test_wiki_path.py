"""Test commits under the correct wiki path in the Fabric repo"""
import base64, json, os, requests

with open("local.settings.json") as f:
    settings = json.load(f)
for k, v in settings["Values"].items():
    os.environ.setdefault(k, v)

import config

token = base64.b64encode(f":{config.ADO_PAT}".encode()).decode()
headers = {"Authorization": f"Basic {token}"}

# The wiki "Fabric" maps to /Trident in the repo
# Wiki page path: /Fabric Experiences/Power BI
# Repo path: /Trident/Fabric Experiences/Power BI
path = "/Trident/Fabric Experiences/Power BI"

url = (
    f"{config.ADO_ORG_URL}/{config.ADO_PROJECT}"
    f"/_apis/git/repositories/Fabric/commits"
    f"?searchCriteria.itemPath={requests.utils.quote(path)}"
    f"&$top=10&api-version=7.1"
)
print(f"URL: {url}\n")
resp = requests.get(url, headers=headers, timeout=30)
resp.raise_for_status()
commits = resp.json().get("value", [])
print(f"Found {len(commits)} commits under '{path}':")
for c in commits:
    date = c["author"]["date"][:10]
    author = c["author"]["name"][:25]
    msg = c["comment"][:80]
    print(f"  {date} | {author} | {msg}")
