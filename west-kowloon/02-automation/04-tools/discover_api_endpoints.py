"""discover_api_endpoints.py — extract API endpoints from a Vue/Vite SPA.

Approach:
  1. Fetch the entry HTML (index.html) and find the main bundle hash.
  2. Fetch the main bundle and extract every chunk filename.
  3. Fetch each chunk and grep for endpoint string literals.
  4. Probe each candidate with HTTP GET to see whether it actually exists
     (4xx / 5xx still mean "the path is real", just not exposed anonymously).
  5. Print a YAML-shaped report.

Use:
  python 04-tools/discover_api_endpoints.py \
      --site https://anticket.lengliwh.com \
      --html-path /websitehtml/index.html \
      --static-path /websitehtml/static \
      --probe

  # To update the on-disk registry:
  python 04-tools/discover_api_endpoints.py --probe --update

This is intentionally NOT auto-run — re-discovery is a deliberate act
because the SPA's bundle hash changes on every deploy.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

import requests
import yaml

DEFAULT_SITE = "https://anticket.lengliwh.com"
DEFAULT_HTML = "/websitehtml/index.html"
DEFAULT_STATIC = "/websitehtml/static"

# Endpoint prefix whitelist — narrows the very wide grep to real paths.
# Add prefixes here as new modules join the SPA.
WK_PREFIXES = ("ucenter", "thvendor", "pay", "sms", "wkcda", "menpiao", "cms", "home")

PATH_RE = re.compile(r'"(/(?:' + "|".join(WK_PREFIXES) + r')/[a-zA-Z0-9_/-]+\.xhtml)"')
CHUNK_RE = re.compile(r'\b([A-Z][A-Za-z0-9_-]*-[A-Za-z0-9]+\.js)\b')


def _fetch(url: str, *, timeout: float = 15.0) -> str:
    r = requests.get(url, timeout=timeout, verify=False)
    r.raise_for_status()
    return r.text


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--site", default=DEFAULT_SITE)
    p.add_argument("--html-path", default=DEFAULT_HTML, help="path of the SPA index.html")
    p.add_argument("--static-path", default=DEFAULT_STATIC, help="path prefix where bundle chunks live")
    p.add_argument("--probe", action="store_true", help="also HTTP-probe each discovered endpoint")
    p.add_argument("--update", action="store_true", help="rewrite 02-tests/api/data/wk_endpoints.yml with the result used by api_smoke")
    p.add_argument("--out", help="optional file to write report (defaults to stdout)")
    args = p.parse_args()

    requests.packages.urllib3.disable_warnings()       # type: ignore[attr-defined]

    site = args.site.rstrip("/")
    static_base = site + args.static_path

    print(f"[discover] index:  {site}{args.html_path}", file=sys.stderr)
    index_html = _fetch(site + args.html_path)
    main_match = re.search(r'src="([^"]*index-[A-Za-z0-9]+\.js)"', index_html)
    if not main_match:
        print("[discover] cannot find main bundle <script> in index.html", file=sys.stderr)
        return 2
    main_rel = main_match.group(1)
    if not main_rel.startswith("http"):
        main_url = site + main_rel
    else:
        main_url = main_rel

    print(f"[discover] main:   {main_url}", file=sys.stderr)
    main_js = _fetch(main_url)

    chunk_names = sorted(set(CHUNK_RE.findall(main_js)))
    print(f"[discover] chunks: {len(chunk_names)}", file=sys.stderr)

    bodies: dict[str, str] = {"_main": main_js}
    for name in chunk_names:
        url = f"{static_base}/{name}"
        try:
            bodies[name] = _fetch(url, timeout=12.0)
        except requests.RequestException as exc:
            print(f"[discover]   skip {name}: {exc}", file=sys.stderr)

    paths: set[str] = set()
    for body in bodies.values():
        paths.update(PATH_RE.findall(body))
    paths_sorted = sorted(paths)
    print(f"[discover] endpoints: {len(paths_sorted)}", file=sys.stderr)

    # Optional live probe to capture actual status code.
    probed: dict[str, int | None] = {}
    if args.probe:
        for ep in paths_sorted:
            try:
                r = requests.get(site + ep, timeout=6.0, verify=False, allow_redirects=False)
                probed[ep] = r.status_code
            except requests.RequestException as exc:
                probed[ep] = None
            print(f"[discover]   [{probed[ep]}]  {ep}", file=sys.stderr)
            time.sleep(0.05)         # be polite

    # Build the YAML view (rough — leaves notes blank; humans fill them).
    entries = []
    for ep in paths_sorted:
        actual = probed.get(ep)
        auth = actual in (401, 403) if actual is not None else None
        expected = (
            [401, 403] if auth
            else [200, 400] if actual == 400
            else [200]
        )
        # Naming: turn /a/b/c/d.xhtml into a.b.c.d
        name = ep.lstrip("/").removesuffix(".xhtml").replace("/", ".")
        group = ep.split("/")[1]
        entries.append({
            "name": name,
            "path": ep,
            "method": "GET",
            "auth_required": bool(auth),
            "expected_status": expected,
            "group": group,
            "notes": "",
        })

    report = {
        "project": "西九",
        "website_url": site,
        "discovered_at": time.strftime("%Y-%m-%d"),
        "discovery_method": "SPA chunk static analysis + live probe",
        "endpoints": entries,
    }
    text = yaml.safe_dump(report, allow_unicode=True, sort_keys=False)

    if args.update:
        target = Path(__file__).resolve().parent.parent / "02-tests" / "api" / "data" / "wk_endpoints.yml"
        # Don't blow away any human-written notes — write to a .new file and ask user to merge.
        out_path = target.with_suffix(".yml.new")
        out_path.write_text(text, encoding="utf-8")
        print(f"\n[discover] wrote {out_path}\n  → review diff vs {target} and merge by hand.", file=sys.stderr)
    elif args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[discover] wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
