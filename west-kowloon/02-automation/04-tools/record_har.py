"""record_har.py — drive a real Chromium so you can crawl a site by hand
while Playwright records every request to a HAR file. After you press
Enter the script parses the HAR, diffs the URLs against the existing
wk_endpoints.yml registry, and prints what's new.

Usage (from the automation/ directory, with .venv active):

  python tools/record_har.py
      → opens the WK website, you log in + click around,
        press Enter, HAR is written + diff printed.

  python tools/record_har.py --url https://staging.example.com
      → record a different site

  python tools/record_har.py --no-record --har path/to/recorded.har
      → skip the browser, just analyse an already-recorded HAR
        (useful if you exported one from Chrome DevTools).

Output:
  07-artifacts/api_smoke/recorded.har            (raw)
  07-artifacts/api_smoke/endpoints_from_har.yml  (extracted, diff-style)

The HAR file contains request/response headers AND cookies — treat it
as sensitive and don't commit it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import yaml

# Repo-relative paths so this script works from anywhere.
_THIS = Path(__file__).resolve()
_AUTOMATION = _THIS.parent.parent
_ARTIFACT_DIR = _AUTOMATION / "07-artifacts" / "api_smoke"
_REGISTRY = _AUTOMATION / "02-tests" / "api" / "data" / "wk_endpoints.yml"

DEFAULT_URL = "https://anticket.lengliwh.com/websitehtml/index.html#/login"
DEFAULT_HAR = _ARTIFACT_DIR / "recorded.har"
DEFAULT_OUT = _ARTIFACT_DIR / "endpoints_from_har.yml"

# Only treat these resource types as API calls (skip css/img/font/document).
_API_RESOURCE_TYPES = {"xhr", "fetch", "websocket"}
# Some servers tag JSON-returning .xhtml as "document" — also catch those by URL.
_API_PATH_RE = re.compile(r"\.(xhtml|json)(\?|$)|/(api|rest|openapi)/")


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------
def record_har(target_url: str, har_path: Path) -> None:
    """Launch headed Chromium, record HAR until user presses Enter."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright not installed. From automation/:", file=sys.stderr)
        print("       pip install -e \".[web]\" && playwright install chromium", file=sys.stderr)
        sys.exit(2)

    har_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[record] HAR → {har_path}")
    print(f"[record] launching headed Chromium…")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            record_har_path=str(har_path),
            record_har_content="embed",        # keep bodies so we can see response shape
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.goto(target_url, wait_until="domcontentloaded")
        print()
        print("=" * 72)
        print("  Browser is open. Do this:")
        print("    1. Log in (use a test account, NOT a real customer)")
        print("    2. Visit every page / module you want covered")
        print("       — home, projects, my orders, cart, checkout, profile, ...")
        print("    3. Come back here and press ENTER to stop recording")
        print("=" * 72)
        try:
            input("\n  >>> press ENTER when done... ")
        except (EOFError, KeyboardInterrupt):
            print("\n[record] aborted")
        finally:
            context.close()
            browser.close()

    print(f"[record] recorded HAR: {har_path}  ({har_path.stat().st_size // 1024} KB)")


# ---------------------------------------------------------------------------
# Parsing + diff
# ---------------------------------------------------------------------------
def parse_har(har_path: Path, site_host: str) -> list[dict[str, Any]]:
    """Return one entry per unique (method, path) where the URL is on the target host
    and looks like an API call."""
    raw = json.loads(har_path.read_text(encoding="utf-8"))
    entries = raw.get("log", {}).get("entries", [])

    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for ent in entries:
        req = ent.get("request", {})
        resp = ent.get("response", {}) or {}
        url = req.get("url", "")
        method = (req.get("method") or "GET").upper()
        rtype = (ent.get("_resourceType") or "").lower()

        if not url.startswith("http"):
            continue
        u = urllib.parse.urlparse(url)
        if u.netloc != site_host:
            continue
        if rtype not in _API_RESOURCE_TYPES and not _API_PATH_RE.search(u.path):
            continue

        key = (method, u.path)
        if key in seen:
            continue

        # Try to peek at response content-type / status for tagging.
        content_type = ""
        for h in resp.get("headers", []) or []:
            if h.get("name", "").lower() == "content-type":
                content_type = h.get("value", "")
                break

        seen[key] = {
            "method": method,
            "path": u.path,
            "status": resp.get("status"),
            "content_type": content_type.split(";")[0].strip(),
            "resource_type": rtype,
            "sample_query": u.query[:120],
        }

    return sorted(seen.values(), key=lambda r: (r["path"], r["method"]))


def load_registry(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        (ep["method"].upper(), ep["path"])
        for ep in raw.get("endpoints", [])
    }


def diff_and_emit(har_rows: list[dict[str, Any]], registry: set[tuple[str, str]], out_path: Path) -> dict[str, int]:
    new_rows = [r for r in har_rows if (r["method"], r["path"]) not in registry]
    known = [r for r in har_rows if (r["method"], r["path"]) in registry]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "playwright recorded HAR",
        "summary": {
            "captured_unique_endpoints": len(har_rows),
            "already_in_registry": len(known),
            "new_to_registry": len(new_rows),
        },
        "new_endpoints": [
            {
                "method": r["method"],
                "path": r["path"],
                "status_observed": r["status"],
                "content_type": r["content_type"],
                "resource_type": r["resource_type"],
                "sample_query": r["sample_query"],
            }
            for r in new_rows
        ],
    }
    out_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    return payload["summary"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", default=DEFAULT_URL,
                   help=f"site to open (default: {DEFAULT_URL})")
    p.add_argument("--har", type=Path, default=DEFAULT_HAR,
                   help=f"HAR file path (default: {DEFAULT_HAR})")
    p.add_argument("--no-record", action="store_true",
                   help="skip recording, just parse the HAR at --har")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT,
                   help=f"diff output (default: {DEFAULT_OUT})")
    p.add_argument("--registry", type=Path, default=_REGISTRY,
                   help="endpoint registry to diff against")
    args = p.parse_args()

    if not args.no_record:
        record_har(args.url, args.har)
    elif not args.har.exists():
        print(f"ERROR: --no-record set but {args.har} doesn't exist", file=sys.stderr)
        return 2

    site_host = urllib.parse.urlparse(args.url).netloc
    print(f"\n[parse] reading {args.har}")
    rows = parse_har(args.har, site_host)
    print(f"[parse] found {len(rows)} unique (method, path) on host {site_host}")

    registry = load_registry(args.registry)
    summary = diff_and_emit(rows, registry, args.out)

    print()
    print(f"  captured unique endpoints:  {summary['captured_unique_endpoints']}")
    print(f"  already in registry:        {summary['already_in_registry']}")
    print(f"  NEW (not in registry):      {summary['new_to_registry']}")
    print()
    print(f"  full diff:  {args.out}")
    if summary["new_to_registry"]:
        print(f"  → review the 'new_endpoints' section and merge into {args.registry.name} by hand.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
