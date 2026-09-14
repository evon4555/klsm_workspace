"""Probe ZenTao bug-create: discover required fields. Try minimal first,
then layer fields. DO NOT actually leave the bug behind — delete after probe
if creation succeeds."""
import os, json, requests, sys

TOKEN = os.environ.get("ZENTAO_API_V2_TOKEN")
BASE  = "https://lengliwh.chandao.net"
PROD  = 146  # 西九
H = {"Token": TOKEN, "Content-Type": "application/json"}

print("=== 1) minimal: title only ===")
r = requests.post(f"{BASE}/api.php/v1/products/{PROD}/bugs",
                  headers=H, data=json.dumps({"title": "[probe] delete me"}),
                  timeout=30)
print(f"  status={r.status_code}  body={r.text[:500]}")
created_id = None
try:
    j = r.json()
    if isinstance(j, dict) and j.get("id"):
        created_id = j["id"]
    elif isinstance(j, dict) and isinstance(j.get("data"), dict) and j["data"].get("id"):
        created_id = j["data"]["id"]
except Exception:
    pass

print("\n=== 2) richer fields (title + steps + severity + type + pri) ===")
body = {
    "title": "[probe2] delete me — testing field acceptance",
    "steps": "<p>Repro: open the website</p><p>Click X</p><p><b>Expected:</b> Y</p><p><b>Actual:</b> error</p>",
    "severity": 3,
    "pri": 3,
    "type": "codeerror",
    "openedBuild": "trunk",
}
r2 = requests.post(f"{BASE}/api.php/v1/products/{PROD}/bugs",
                   headers=H, data=json.dumps(body), timeout=30)
print(f"  status={r2.status_code}  body={r2.text[:500]}")
try:
    j2 = r2.json()
    bid = j2.get("id") or (j2.get("data") or {}).get("id")
    if bid:
        print(f"  -> created bug id = {bid}")
        if not created_id: created_id = bid
        # try second one too — pick the smaller one to delete first
except Exception:
    pass

# Clean up: delete any bug we accidentally left behind
for bid in {created_id, bid if 'bid' in dir() else None} - {None}:
    print(f"\n=== cleanup: DELETE bug {bid} ===")
    rd = requests.delete(f"{BASE}/api.php/v1/bugs/{bid}", headers=H, timeout=20)
    print(f"  status={rd.status_code}  body={rd.text[:200]}")
