"""Probe SIT UI to capture facts that can move yellow / TBD test cases to
confirmed status:

  TC046 / TC047 — does the mobile registration / login tab exist in the UI?
  TC059-063   — which 3rd-party providers actually appear on the login page?
  TC065       — OTP digit-count (count the .otp-box inputs)
  TC070       — forgot-password reset model: does the page collect a new
                password directly (reset-token model), or does it imply a
                temporary password is emailed?
  TC034 / TC035 — does OTP-mode login HAVE a password field (per spec) or
                  not (per implementation we saw)?
  TC030       — does the 动态码 refresh both on click AND auto on wrong input?
  TC022       — robot-verification UI on guest login (does it actually exist?)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from playwright.sync_api import sync_playwright

from test_automation.config import get_settings


def _visible_texts(page, selector: str, limit: int = 20) -> list[str]:
    return page.evaluate(r"""
        ({sel, limit}) => {
            const out = [];
            for (const el of document.querySelectorAll(sel)) {
                const vis = !!(el.offsetWidth || el.offsetHeight);
                if (!vis) continue;
                const t = (el.innerText || '').trim();
                if (t) out.push(t);
                if (out.length >= limit) break;
            }
            return out;
        }
    """, {"sel": selector, "limit": limit})


def main():
    facts: dict = {}
    settings = get_settings()
    base = str(settings.antank_url).rstrip("/")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        # --- registration page ---
        page.goto(f"{base}/websitehtml/index.html#/register", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=20000)
        page.wait_for_timeout(1500)
        facts["tc046_mobile_register_tab"] = _visible_texts(
            page, ".tab-row button, .tab-left, .tab-right")
        facts["tc046_register_inputs"] = _visible_texts(
            page, "input[placeholder]")
        # captcha refresh behavior — click image and re-read src
        facts["tc030_captcha_initial_src"] = page.evaluate(
            "() => { const i=document.querySelector('.captcha-box img'); "
            "return i ? i.src : null }")
        page.click(".captcha-box img")
        page.wait_for_timeout(700)
        facts["tc030_captcha_after_click_src"] = page.evaluate(
            "() => { const i=document.querySelector('.captcha-box img'); "
            "return i ? i.src : null }")

        # --- login page (password mode is default) ---
        page.goto(f"{base}/websitehtml/index.html#/login", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=20000)
        page.wait_for_timeout(1500)
        facts["tc047_login_phone_tab"] = _visible_texts(
            page, ".tab-row button, .tab-left, .tab-right")
        # 3rd-party providers: any social login icons / buttons?
        facts["tc059_063_thirdparty_section_texts"] = _visible_texts(
            page,
            ".third-party,.social-login,[class*=oauth],[class*=provider],"
            ".login-with,.thirdparty,.social",
            limit=10)
        # broad sweep — any link/button whose alt/aria/text mentions a provider
        facts["tc059_063_provider_hints"] = page.evaluate(r"""
            () => {
                const NAMES = ['google','facebook','twitter','x','tiktok',
                               'wechat','weixin','apple'];
                const out = new Set();
                for (const el of document.querySelectorAll('*')) {
                    const blob = ((el.alt||'') + ' '
                                + (el.getAttribute&&el.getAttribute('aria-label')||'') + ' '
                                + (el.title||'') + ' '
                                + (el.innerText||'').slice(0,40)).toLowerCase();
                    for (const n of NAMES) if (blob.includes(n)) out.add(n);
                }
                return [...out];
            }
        """)

        # --- switch to OTP mode and count OTP boxes (TC065) ---
        link = page.locator(".mode-link")
        if link.count():
            link.first.click()
            page.wait_for_timeout(800)
        facts["tc034_otp_mode_inputs"] = _visible_texts(page, "input[placeholder]")
        # request OTP (needs 动态码) so boxes appear, then count them
        # — but we want to avoid burning OTP. Instead inspect static markup.
        otp_box_count_static = page.evaluate(
            "() => document.querySelectorAll('.otp-box').length")
        facts["tc065_otp_box_count_before_request"] = otp_box_count_static
        # — but the .otp-box may only render after Get Code. Use the form
        #   placeholder for the verification code field as a fallback signal.
        facts["tc032_034_otp_mode_has_password_field"] = page.evaluate(
            "() => !!document.querySelector('input[type=password],input[placeholder=Password],input.pwd-input')")

        # --- forgot password page (TC015 / TC070) — actual SPA route is #/forget ---
        page.goto(f"{base}/websitehtml/index.html#/forget",
                  timeout=60000)
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(1500)
        facts["tc015_070_forgot_inputs"] = _visible_texts(
            page, "input[placeholder]")
        facts["tc015_070_forgot_buttons"] = _visible_texts(
            page, "button, .submit-btn, .get-code-btn", limit=10)
        facts["tc015_070_forgot_url_landed"] = page.url
        facts["tc015_070_forgot_body_keywords"] = page.evaluate(r"""
            () => {
                const body = (document.body.innerText||'').toLowerCase();
                const hits = [];
                for (const kw of ['temp', '临时', '临时密码', 'temporary password',
                                  'reset link', '链接', 'new password', '新密码',
                                  'set password', '设置密码']) {
                    if (body.includes(kw.toLowerCase())) hits.push(kw);
                }
                return hits;
            }
        """)

        # --- guest login — actually on #/login with a "Guest" entry; probe it ---
        page.goto(f"{base}/websitehtml/index.html#/login", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(1500)
        facts["tc022_login_page_full_button_texts"] = _visible_texts(
            page, "button, a, .submit-btn, [role=button]", limit=30)
        # Look for any element whose text suggests guest entry
        facts["tc022_guest_entry_candidates"] = page.evaluate(r"""
            () => {
                const out = [];
                for (const el of document.querySelectorAll('a,button,div,span')) {
                    const t = (el.innerText||'').trim();
                    if (!t || t.length > 30) continue;
                    if (/guest|游客|visitor|continue without/i.test(t)) {
                        out.push({tag: el.tagName, text: t});
                    }
                }
                return out.slice(0, 10);
            }
        """)

        browser.close()

    print(json.dumps(facts, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
