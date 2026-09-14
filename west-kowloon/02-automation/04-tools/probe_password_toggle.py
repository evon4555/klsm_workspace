"""One-off probe: find the password show/hide toggle on the Website
registration page and the login page (TC045 spec asks both).

Run:
    ENV=sit ./.venv/Scripts/python.exe tools/probe_password_toggle.py

Prints, for each page:
  - the password input's HTML
  - the parent container's HTML (where eye-icon toggles usually live)
  - any sibling/cousin elements whose class hints at show/hide
  - whether clicking such an element flips input[type=password] <-> text
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from playwright.sync_api import sync_playwright

from test_automation.config import get_settings, get_user
from test_automation.web import WebsiteLoginPage, WebsiteRegistrationPage


_PROBE_JS = r"""
(sel) => {
  const inp = document.querySelector(sel);
  if (!inp) return {found:false};
  const out = {found:true, type: inp.type, outerHTML: inp.outerHTML};
  // walk up three ancestors and dump their HTML (truncated)
  let p = inp.parentElement;
  out.ancestors = [];
  for (let i=0; i<4 && p; i++) {
    out.ancestors.push({
      depth: i,
      tag: p.tagName,
      cls: p.className,
      html: (p.outerHTML || '').slice(0, 1200)
    });
    p = p.parentElement;
  }
  // search for likely toggle candidates near the input
  const root = inp.closest('.form-item,.input-wrap,.field,form,body') || document.body;
  const candidates = [];
  root.querySelectorAll('i,span,svg,img,button,a,div').forEach(el => {
    const cls = (el.className && el.className.baseVal !== undefined
                  ? el.className.baseVal : el.className) || '';
    const id  = el.id || '';
    const lc  = (cls+' '+id).toLowerCase();
    if (/eye|pwd|password|visi|toggle|show|hide|plain/.test(lc)) {
      candidates.push({
        tag: el.tagName,
        cls: cls,
        id:  id,
        html: (el.outerHTML || '').slice(0, 300)
      });
    }
  });
  out.candidates = candidates.slice(0, 20);
  return out;
}
"""


def _probe_input(page, sel: str, label: str):
    print(f"\n=== {label} — {sel} ===")
    info = page.evaluate(_PROBE_JS, sel)
    if not info["found"]:
        print("  NOT FOUND")
        return
    print(f"  type = {info['type']}")
    print(f"  outerHTML = {info['outerHTML']}")
    for a in info["ancestors"]:
        print(f"  parent[{a['depth']}] <{a['tag']}> class={a['cls']!r}")
        print(f"    html = {a['html']}")
    print(f"  toggle candidates ({len(info['candidates'])}):")
    for c in info["candidates"]:
        print(f"    <{c['tag']}> class={c['cls']!r} id={c['id']!r}")
        print(f"      {c['html']}")


def main():
    settings = get_settings()
    base = str(settings.antank_url).rstrip("/")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()

        # --- registration page ---
        reg = WebsiteRegistrationPage(page, base)
        reg.open()
        page.fill(reg.PASSWORD_SEL, "Aa12345!")
        page.fill(reg.CONFIRM_SEL, "Aa12345!")
        page.wait_for_timeout(500)
        _probe_input(page, reg.PASSWORD_SEL, "REGISTRATION password")
        _probe_input(page, reg.CONFIRM_SEL,  "REGISTRATION confirm")

        # --- login page (password mode is default) ---
        lp = WebsiteLoginPage(page, base)
        lp.open()
        user = get_user("website_user", settings.env)
        page.fill('input[placeholder="Password"]', user.password)
        page.wait_for_timeout(500)
        _probe_input(page, 'input[placeholder="Password"]', "LOGIN password")

        browser.close()


if __name__ == "__main__":
    main()
