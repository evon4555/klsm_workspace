"""Probe ZenTao file-upload endpoint with requests (well-formed multipart).
Goal: figure out what shape actually works on lengliwh.chandao.net SaaS."""
import os
import sys
from pathlib import Path
import requests

TOKEN = os.environ.get("ZENTAO_API_V2_TOKEN")
if not TOKEN:
    print("ERROR: ZENTAO_API_V2_TOKEN env not set in this shell.")
    sys.exit(1)
BASE = "https://lengliwh.chandao.net"
HDR = {"Token": TOKEN}

WESTK_ROOT = Path(os.getenv("QA_WESTK_ROOT", Path(__file__).resolve().parents[2])).resolve()
TMP = WESTK_ROOT / "02-automation" / "07-artifacts" / "test_upload.txt"
TMP.parent.mkdir(parents=True, exist_ok=True)
with open(TMP, "w") as f:
    f.write("hello from claude probe\n")

trials = [
    # (label, url, files, data)
    ("v1 /files, field='files[]'",
     f"{BASE}/api.php/v1/files",
     {"files[]": (TMP.name, open(TMP, "rb"), "text/plain")},
     {"object": "task", "objectID": "10219", "labels[]": "automation"}),
    ("v1 /files, field='file' single",
     f"{BASE}/api.php/v1/files",
     {"file": (TMP.name, open(TMP, "rb"), "text/plain")},
     {"object": "task", "objectID": "10219"}),
    ("old ajaxUpload, field='files[]'",
     f"{BASE}/api.php?m=file&f=ajaxUpload",
     {"files[]": (TMP.name, open(TMP, "rb"), "text/plain")},
     {"objectType": "task", "objectID": "10219", "labels[]": "automation"}),
    ("old ajaxUpload + onlybody=yes",
     f"{BASE}/api.php?m=file&f=ajaxUpload&objectType=task&objectID=10219&onlybody=yes",
     {"files[]": (TMP.name, open(TMP, "rb"), "text/plain")},
     {}),
]

for label, url, files, data in trials:
    print(f"\n=== {label} ===")
    try:
        r = requests.post(url, headers=HDR, files=files, data=data, timeout=30)
        print(f"  status={r.status_code}")
        body = r.text[:400]
        print(f"  body  ={body}")
    except Exception as e:
        print(f"  EXC: {e!r}")
    finally:
        for fh in files.values():
            try: fh[1].close()
            except Exception: pass
