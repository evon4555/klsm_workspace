"""Try session-cookie path for ZenTao file upload.
Path A: GET /api.php?m=user&f=apilogin to start a session via token, get cookie, then POST file with cookie.
Path B: PUT /tasks/10219 with file via JSON body containing a base64 attachment field (some SaaS support this).
"""
import os, sys, json, base64
from pathlib import Path
import requests

TOKEN = os.environ.get("ZENTAO_API_V2_TOKEN")
BASE  = "https://lengliwh.chandao.net"
HDR   = {"Token": TOKEN}

WESTK_ROOT = Path(os.getenv("QA_WESTK_ROOT", Path(__file__).resolve().parents[2])).resolve()
TMP = WESTK_ROOT / "02-automation" / "07-artifacts" / "test_upload.txt"
TMP.parent.mkdir(parents=True, exist_ok=True)
with open(TMP, "w") as f:
    f.write("hello from claude probe\n")

s = requests.Session()
s.headers.update(HDR)

print("=== A1) GET /api.php/v1/tokens (with Token header) — start session ===")
r = s.get(f"{BASE}/api.php/v1/tokens", timeout=15)
print(f"  status={r.status_code}  cookies={dict(s.cookies)}")

print("\n=== A2) GET /index.php?m=user&f=login (any page) — get a zentao session ===")
r = s.get(f"{BASE}/index.php", timeout=15)
print(f"  status={r.status_code}  cookies={dict(s.cookies)}")

print("\n=== A3) GET /my.html (web entry, often sets session) ===")
r = s.get(f"{BASE}/my.html", timeout=15)
print(f"  status={r.status_code}  cookies={dict(s.cookies)}")

print("\n=== upload attempt with session cookies + Token header ===")
files = {"files[]": ("probe.txt", open(TMP, "rb"), "text/plain")}
data = {"objectType": "task", "objectID": "10219", "labels[]": ""}
r = s.post(f"{BASE}/api.php?m=file&f=ajaxUpload&onlybody=yes",
           files=files, data=data, timeout=30)
print(f"  status={r.status_code}  body={r.text[:400]}")
files["files[]"][1].close()

print("\n=== upload attempt with cookies only (drop Token) ===")
s2 = requests.Session()
# carry only cookies from s
s2.cookies.update(s.cookies)
files = {"files[]": ("probe.txt", open(TMP, "rb"), "text/plain")}
r = s2.post(f"{BASE}/api.php?m=file&f=ajaxUpload&onlybody=yes",
            files=files, data=data, timeout=30)
print(f"  status={r.status_code}  body={r.text[:400]}")
files["files[]"][1].close()

print("\n=== B) PUT /api.php/v1/tasks/10219 with files key in JSON (base64) ===")
b64 = base64.b64encode(open(TMP, "rb").read()).decode()
body = {"files": [{"title": "probe.txt", "fileName": "probe.txt",
                   "content": b64, "extension": "txt"}]}
r = requests.put(f"{BASE}/api.php/v1/tasks/10219",
                 headers={**HDR, "Content-Type": "application/json"},
                 data=json.dumps(body), timeout=30)
print(f"  status={r.status_code}  body={r.text[:400]}")
