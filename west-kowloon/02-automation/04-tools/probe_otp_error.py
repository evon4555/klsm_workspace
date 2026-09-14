"""Probe the SIT login OTP step: request the code with the registered email,
type 111111, and report the visible error so we know WHY login fails (rate
limit vs wrong-code vs other)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from playwright.sync_api import sync_playwright

from test_automation.config import get_settings, get_user
from test_automation.web import WebsiteLoginPage


def main():
    settings = get_settings()
    user = get_user("website_user", settings.env)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        lp = WebsiteLoginPage(page, str(settings.antank_url))
        lp.open()
        lp.switch_to_otp_mode()
        err = lp.request_verification_code(user.username)
        print(f"OTP-request err = {err!r}")
        print(f"otp_boxes_present = {lp.otp_boxes_present()}")
        print(f"url after request = {page.url}")
        lp.fill_otp("111111")
        page.wait_for_timeout(4000)
        # try to capture any visible message on the page
        msg = page.evaluate(r"""() => {
            const sel = '.error-msg,.field-error,[class*=error],[class*=invalid],'
                      + '[class*=tip],[class*=msg],[role=alert]';
            const out = [];
            for (const el of document.querySelectorAll(sel)) {
                const vis = !!(el.offsetWidth || el.offsetHeight);
                const t = (el.innerText || '').trim();
                if (vis && t && t.length < 200) out.push(t);
            }
            return out;
        }""")
        print(f"visible messages after fill_otp: {msg}")
        print(f"final url           = {page.url}")
        print(f"is_logged_in        = {lp.is_logged_in()}")
        page.wait_for_timeout(5000)        # leave window open briefly for inspection
        browser.close()


if __name__ == "__main__":
    main()
