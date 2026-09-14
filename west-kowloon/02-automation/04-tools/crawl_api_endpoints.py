"""crawl_api_endpoints.py — autonomous headless API discovery.

Logs into the WK website with the credentials from envs/.env.<ENV>, walks
a list of routes while listening to every XHR/fetch, then diffs the
captured endpoints against the on-disk registry. Reuses the session
cookie via storage_state.json so subsequent runs do not re-login (and
do not consume captcha attempts) until the cookie expires.

Usage (from automation/, with .venv active):

  python tools/crawl_api_endpoints.py                       # ENV=sit (default)
  python tools/crawl_api_endpoints.py --env uat
  python tools/crawl_api_endpoints.py --force-login          # ignore cached session
  python tools/crawl_api_endpoints.py --pages /my/orders /my/cards   # subset

Outputs:
  07-artifacts/api_smoke/storage_state.json          (logged-in cookie jar)
  07-artifacts/api_smoke/crawled.har                 (raw network capture)
  07-artifacts/api_smoke/endpoints_from_crawl.yml    (diff vs registry)

This script intentionally does NOT submit forms, click "buy", or write any
state on the server — it only navigates and observes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Paths + env
# ---------------------------------------------------------------------------
_THIS = Path(__file__).resolve()
_AUTOMATION = _THIS.parent.parent              # automation/
sys.path.insert(0, str(_AUTOMATION / "03-src"))   # so we can import test_automation.web

_ARTIFACT_DIR = _AUTOMATION / "07-artifacts" / "api_smoke"
_REGISTRY_PATH = _AUTOMATION / "02-tests" / "api" / "data" / "wk_endpoints.yml"
_STATE_PATH = _ARTIFACT_DIR / "storage_state.json"
_HAR_PATH = _ARTIFACT_DIR / "crawled.har"
_DIFF_PATH = _ARTIFACT_DIR / "endpoints_from_crawl.yml"

# Storage state is considered fresh enough to skip re-login if newer than this.
_STATE_TTL_SECONDS = 6 * 3600


def _load_env(env_name: str) -> None:
    env_file = _AUTOMATION / "06-envs" / f".env.{env_name}"
    if not env_file.exists():
        raise SystemExit(f"ERROR: env file not found: {env_file}")
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def _context_options(**kwargs: Any) -> dict[str, Any]:
    user = os.environ.get("WK_BASIC_AUTH_USER")
    password = os.environ.get("WK_BASIC_AUTH_PASS")
    if user and password:
        kwargs["http_credentials"] = {"username": user, "password": password}
    return kwargs


# ---------------------------------------------------------------------------
# Routes to walk after login. Add more as the app grows.
# ---------------------------------------------------------------------------
DEFAULT_ROUTES = [
    # public / before login
    "/websitehtml/index.html#/",
    "/websitehtml/index.html#/projects",
    "/websitehtml/index.html#/calendar",
    "/websitehtml/index.html#/activity/list",
    "/websitehtml/index.html#/news/list",
    "/websitehtml/index.html#/search",
    "/websitehtml/index.html#/about",
    # after login (member-scoped)
    "/websitehtml/index.html#/my",
    "/websitehtml/index.html#/my/orders",
    "/websitehtml/index.html#/my/tickets",
    "/websitehtml/index.html#/my/profile",
    "/websitehtml/index.html#/my/cards",
    "/websitehtml/index.html#/my/coupons",
    "/websitehtml/index.html#/my/wishlist",
    "/websitehtml/index.html#/my/identity",
    "/websitehtml/index.html#/my/points",
    "/websitehtml/index.html#/my/shipping",
    "/websitehtml/index.html#/my/priority",
    "/websitehtml/index.html#/membership",
    "/websitehtml/index.html#/cart",
    "/websitehtml/index.html#/settings",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_state_fresh() -> bool:
    if not _STATE_PATH.exists():
        return False
    age = time.time() - _STATE_PATH.stat().st_mtime
    return age < _STATE_TTL_SECONDS


def _api_shape(url: str) -> bool:
    """Cheap filter: is this URL plausibly an API call (not a static asset)?"""
    p = urllib.parse.urlparse(url)
    if p.path.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg",
                        ".woff", ".woff2", ".ttf", ".ico", ".map")):
        return False
    if "/static/" in p.path:
        return False
    return True


# ---------------------------------------------------------------------------
# Phase 1: login (or reuse cached session)
# ---------------------------------------------------------------------------
def login_and_save_state(base_url: str, email: str, password: str) -> None:
    """Drive WebsiteLoginPage to log in, then dump cookies to storage_state.json."""
    from playwright.sync_api import sync_playwright
    from test_automation.web.website_login_page import WebsiteLoginPage

    print("[login] no fresh session — running headless login flow")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(**_context_options(ignore_https_errors=True))
        page = ctx.new_page()
        try:
            login_page = WebsiteLoginPage(page, base_url, screenshot_dir=_ARTIFACT_DIR)
            login_page.open()
            login_page.login(email=email, password=password, max_attempts=8)
            print("[login] success — saving storage state")
            _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            ctx.storage_state(path=str(_STATE_PATH))
        except Exception as exc:
            shot = _ARTIFACT_DIR / "login_error.png"
            try:
                page.screenshot(path=str(shot))
                print(f"[login] FAILED — screenshot at {shot}", file=sys.stderr)
            except Exception:
                pass
            raise
        finally:
            ctx.close()
            browser.close()


# ---------------------------------------------------------------------------
# Phase 2: crawl pages, capture XHR
# ---------------------------------------------------------------------------
def _fetch_program_ids_via_api(base_url: str, cookies: list[dict[str, Any]], max_n: int = 3) -> list[int]:
    """Hit the public hot-programs API to harvest a few program IDs we can
    then deep-link into. Cookies are passed in case the endpoint personalises
    by member, but the call works anonymously too."""
    import requests
    s = requests.Session()
    for c in cookies:
        if "lengliwh" in c.get("domain", ""):
            s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c.get("path", "/"))
    s.headers.update({
        "cmpappkey": "ShanghaiCS",
        "lang": "en",
        "Referer": f"{base_url}/websitehtml/index.html",
        "Accept": "application/json, text/plain, */*",
    })
    try:
        r = s.post(f"{base_url}/thvendor/ticket/program/getHotProgramList.xhtml",
                   json={"showSite": "PCrecList1"}, timeout=10, verify=False)
        body = r.json()
        items = body.get("data") or body.get("data", {}).get("list") or []
        if isinstance(items, dict):
            items = items.get("list", [])
        ids = []
        for it in items:
            pid = it.get("id") or it.get("programId")
            if pid:
                ids.append(int(pid))
            if len(ids) >= max_n:
                break
        return ids
    except Exception as exc:
        print(f"[crawl]   getHotProgramList failed: {type(exc).__name__}: {exc}")
        return []


def crawl(base_url: str, routes: list[str], output_har: Path, *, deep: bool = False) -> list[dict[str, Any]]:
    from playwright.sync_api import sync_playwright

    captured: list[dict[str, Any]] = []
    site_host = urllib.parse.urlparse(base_url).netloc

    output_har.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(**_context_options(
            storage_state=str(_STATE_PATH),
            record_har_path=str(output_har),
            ignore_https_errors=True,
        ))

        def on_request_finished(req):
            try:
                if site_host not in req.url:
                    return
                if not _api_shape(req.url):
                    return
                resp = req.response()
                status = resp.status if resp else None
                u = urllib.parse.urlparse(req.url)
                captured.append({
                    "method": req.method,
                    "path": u.path,
                    "query": u.query,
                    "status": status,
                    "resource_type": req.resource_type,
                })
            except Exception:
                # Don't let a single bad event abort the whole crawl.
                pass

        ctx.on("requestfinished", on_request_finished)

        page = ctx.new_page()

        for i, route in enumerate(routes, 1):
            url = base_url.rstrip("/") + route
            print(f"[crawl] {i:>2}/{len(routes)}  {route}")
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
                # Give late XHRs a chance to fire.
                page.wait_for_timeout(1500)
            except Exception as exc:
                print(f"[crawl]    skipped: {type(exc).__name__}: {str(exc)[:100]}")

        # Deep mode — visit a few program detail pages. The SPA uses
        # /detail/show/:id and /detail/ticket/:id (per route definition in
        # the bundle), but project cards are clickable divs (not <a href>),
        # so we resolve program IDs via the hot-programs API and navigate
        # directly. Read-only — no cart adds, no seat picks, no checkout.
        if deep:
            print("[crawl] --deep — resolving program IDs via API")
            state = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
            program_ids = _fetch_program_ids_via_api(base_url, state.get("cookies", []), max_n=3)
            print(f"[crawl]   got program IDs: {program_ids}")
            for j, pid in enumerate(program_ids, 1):
                for route_prefix in ("/detail/show/", "/detail/ticket/"):
                    target = f"{base_url.rstrip('/')}/websitehtml/index.html#{route_prefix}{pid}"
                    print(f"[crawl]   deep {j}.{route_prefix.strip('/')}  → #{route_prefix}{pid}")
                    try:
                        page.goto(target, timeout=30000, wait_until="domcontentloaded")
                        try:
                            page.wait_for_load_state("networkidle", timeout=10000)
                        except Exception:
                            pass
                        page.wait_for_timeout(2500)
                    except Exception as exc:
                        print(f"[crawl]      skipped: {type(exc).__name__}: {str(exc)[:100]}")

        ctx.close()
        browser.close()

    print(f"[crawl] captured {len(captured)} API-shaped requests across {len(routes)} routes")
    return captured


# ---------------------------------------------------------------------------
# Phase 3: diff vs registry
# ---------------------------------------------------------------------------
def diff_and_write(captured: list[dict[str, Any]], registry_path: Path, out_path: Path) -> dict[str, int]:
    # Dedupe by (method, path).
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for c in captured:
        key = (c["method"], c["path"])
        if key not in seen:
            seen[key] = c

    # Load registry.
    registry: set[tuple[str, str]] = set()
    if registry_path.exists():
        raw = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        registry = {(e["method"].upper(), e["path"]) for e in raw.get("endpoints", [])}

    rows = sorted(seen.values(), key=lambda r: (r["path"], r["method"]))
    new = [r for r in rows if (r["method"], r["path"]) not in registry]
    known = [r for r in rows if (r["method"], r["path"]) in registry]

    payload = {
        "source": "playwright autonomous crawler",
        "crawled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": {
            "unique_captured": len(rows),
            "already_in_registry": len(known),
            "new_to_registry": len(new),
        },
        "new_endpoints": [
            {
                "method": r["method"],
                "path": r["path"],
                "status_observed": r["status"],
                "resource_type": r["resource_type"],
                "sample_query": r.get("query", "")[:160],
            }
            for r in new
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return payload["summary"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--env", default=os.environ.get("ENV", "sit"),
                   help="env name (default: $ENV or 'sit')")
    p.add_argument("--force-login", action="store_true",
                   help="ignore cached storage_state.json and re-login")
    p.add_argument("--pages", nargs="+", default=None,
                   help="restrict to these route paths (default: walk all DEFAULT_ROUTES)")
    p.add_argument("--deep", action="store_true",
                   help="after the shallow walk, navigate into a few project "
                        "detail pages to capture detail-level endpoints "
                        "(read-only — no cart adds, no seat picks)")
    args = p.parse_args()

    _load_env(args.env)
    base = os.environ.get("TA_ANTANK_URL", "https://anticket.lengliwh.com").rstrip("/")
    email = os.environ.get("TA_WEBSITE_USERNAME")
    password = os.environ.get("TA_WEBSITE_PASSWORD")
    if not email or not password:
        print("ERROR: TA_WEBSITE_USERNAME / TA_WEBSITE_PASSWORD missing in env", file=sys.stderr)
        return 2

    print(f"[crawl] target = {base}  env = {args.env}  user = {email[:3]}***")

    if args.force_login or not _is_state_fresh():
        login_and_save_state(base, email, password)
    else:
        age_min = (time.time() - _STATE_PATH.stat().st_mtime) / 60
        print(f"[crawl] reusing storage_state.json ({age_min:.0f} min old)")

    routes = args.pages or DEFAULT_ROUTES
    captured = crawl(base, routes, _HAR_PATH, deep=args.deep)
    summary = diff_and_write(captured, _REGISTRY_PATH, _DIFF_PATH)

    print()
    print(f"  unique captured:     {summary['unique_captured']}")
    print(f"  already registered:  {summary['already_in_registry']}")
    print(f"  NEW to registry:     {summary['new_to_registry']}")
    print()
    print(f"  HAR:    {_HAR_PATH}")
    print(f"  Diff:   {_DIFF_PATH}")
    if summary["new_to_registry"]:
        print(f"\n  → Review the 'new_endpoints' section in {_DIFF_PATH.name} and merge into")
        print(f"    {_REGISTRY_PATH.relative_to(_AUTOMATION)} by hand.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
