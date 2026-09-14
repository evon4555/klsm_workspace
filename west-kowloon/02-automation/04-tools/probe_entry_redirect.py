"""One-off probe for TC057: from a non-auth page, what triggers login/register
and does the app preserve a redirect-back to the entry page?

Run:
    ENV=sit ./.venv/Scripts/python.exe tools/probe_entry_redirect.py

Reports:
  - the entry URL (homepage) and any header "Log in / Sign up" link found
  - the URL after clicking that link (any redirect/return query params?)
  - direct navigation to #/register: any way to inject a return URL?
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from playwright.sync_api import sync_playwright

from test_automation.config import get_settings


def _dump_anchors_with_keyword(page, label, keywords):
    print(f"\n--- {label} candidates (text contains any of {keywords}) ---")
    found = page.evaluate(r"""
        (keywords) => {
            const out = [];
            const all = document.querySelectorAll('a,button,[role=button],span,div,li');
            for (const el of all) {
                const t = (el.innerText || '').trim();
                if (!t || t.length > 40) continue;
                const low = t.toLowerCase();
                if (!keywords.some(k => low.includes(k.toLowerCase()))) continue;
                const vis = !!(el.offsetWidth || el.offsetHeight);
                if (!vis) continue;
                let attrs = '';
                for (const a of el.attributes) attrs += ' ' + a.name + '=' + JSON.stringify(a.value);
                out.push({ tag: el.tagName, text: t, attrs: attrs.slice(0, 200) });
                if (out.length >= 20) break;
            }
            return out;
        }
    """, keywords)
    for it in found:
        print(f"  <{it['tag']}> {it['text']!r} {it['attrs']}")


def main():
    settings = get_settings()
    base = str(settings.antank_url).rstrip("/")
    home_url = f"{base}/websitehtml/index.html#/"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()

        # --- visit homepage ---
        print(f"\n=== HOMEPAGE: {home_url} ===")
        page.goto(home_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=20000)
        page.wait_for_timeout(2000)
        print(f"  current url = {page.url}")
        _dump_anchors_with_keyword(page, "Log in / Sign up / 登录",
                                   ["log in", "login", "sign in", "sign up", "register",
                                    "登录", "注册"])

        # --- visit #/register directly with a synthetic ?redirect param ---
        for trial in (
            f"{base}/websitehtml/index.html#/register",
            f"{base}/websitehtml/index.html#/register?redirect=/",
            f"{base}/websitehtml/index.html?redirect=/#/register",
        ):
            print(f"\n=== DIRECT NAV: {trial} ===")
            page.goto(trial, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=20000)
            page.wait_for_timeout(1500)
            print(f"  url after nav = {page.url}")

        browser.close()


if __name__ == "__main__":
    main()
