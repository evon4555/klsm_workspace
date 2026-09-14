"""Last-resort upload attempts:
1. POST /api.php?m=file&f=ajaxUpload with cookie AUTH (no Token header) — mimic browser
2. Try /api.php/v1/objects/task/10219/files (some V2 SaaS uses this)
3. Look at /api.php/v1/files via OPTIONS
"""
import os, sys, requests
from pathlib import Path

TOKEN = os.environ.get("ZENTAO_API_V2_TOKEN")
BASE  = "https://lengliwh.chandao.net"

WESTK_ROOT = Path(os.getenv("QA_WESTK_ROOT", Path(__file__).resolve().parents[2])).resolve()
TMP = WESTK_ROOT / "02-automation" / "07-artifacts" / "test_upload.txt"
TMP.parent.mkdir(parents=True, exist_ok=True)
with open(TMP, "wb") as f:
    f.write(b"hello from probe3\n")

# Pre-warm session with token (which is also the cookie value)
s = requests.Session()
s.cookies.set("zentaosid", TOKEN)
s.cookies.set("lang", "zh-cn")
s.cookies.set("device", "desktop")
print("=== session with zentaosid cookie = token value ===")
r = s.get(f"{BASE}/my.html", timeout=10)
print(f"  warmup status={r.status_code}")

print("\n=== A) old ajaxUpload with cookie-only (no Token header) ===")
files = {"files[]": ("probe.txt", open(TMP, "rb"), "text/plain")}
data = {"objectType": "task", "objectID": "10219", "labels[]": ""}
r = s.post(f"{BASE}/api.php?m=file&f=ajaxUpload&onlybody=yes",
           files=files, data=data, timeout=30)
print(f"  status={r.status_code}  body={r.text[:300]}")
files["files[]"][1].close()

print("\n=== B) /file-ajaxUpload-task-10219.html (router path form) ===")
files = {"files[]": ("probe.txt", open(TMP, "rb"), "text/plain")}
r = s.post(f"{BASE}/file-ajaxUpload-task-10219.html",
           files=files, data={"labels[]": ""}, timeout=30)
print(f"  status={r.status_code}  body={r.text[:300]}")
files["files[]"][1].close()

print("\n=== C) /file-ajaxUpload.html with form fields ===")
files = {"files[]": ("probe.txt", open(TMP, "rb"), "text/plain")}
data = {"objectType": "task", "objectID": "10219", "labels[]": ""}
r = s.post(f"{BASE}/file-ajaxUpload.html",
           files=files, data=data, timeout=30)
print(f"  status={r.status_code}  body={r.text[:300]}")
files["files[]"][1].close()

print("\n=== D) /api.php/v1/files with cookie-only, no Token header ===")
files = {"files[]": ("probe.txt", open(TMP, "rb"), "text/plain")}
data = {"object": "task", "objectID": "10219"}
r = s.post(f"{BASE}/api.php/v1/files",
           files=files, data=data, timeout=30)
print(f"  status={r.status_code}  body={r.text[:300]}")
files["files[]"][1].close()
