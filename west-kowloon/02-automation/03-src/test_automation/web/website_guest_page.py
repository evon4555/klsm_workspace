from __future__ import annotations

from pathlib import Path

import ddddocr
from playwright.sync_api import Page

_ocr = ddddocr.DdddOcr(show_ad=False)


class WebsiteGuestPage:
    """Page object for the West Kowloon Website guest-login flow.

    Pure UI automation — the automated counterpart of manual test cases
    SIT-TC-WEB-AUTH-021 / 022 / 023 / 025.

    From the login page, "Continue as guest" opens the guest panel:
      .guest-btn                       — "Continue as guest" (login page)
      input[placeholder="Dynamic Code"]— 动态码 image captcha (robot check)
      img[src*="captcha.xhtml"]        — the 动态码 image
      .guest-agree-row                 — "I understand and agree to the terms"
      .submit-btn                      — "Continue as guest" (guest panel)

    "Robot verification" = solving the 动态码 + accepting the agreement.
    """

    LOGIN_PATH = "/websitehtml/index.html#/login"

    GUEST_BTN_SEL = ".guest-btn"
    DYN_SEL = 'input[placeholder="Dynamic Code"]'
    CAPTCHA_IMG_SEL = 'img[src*="captcha.xhtml"]'
    AGREE_SEL = ".guest-agree-row"
    SUBMIT_SEL = ".submit-btn"
    COOKIE_ACCEPT_SEL = ".cookie-accept"

    def __init__(self, page: Page, base_url: str, screenshot_dir=None) -> None:
        self._page = page
        self._base_url = base_url.rstrip("/")
        self._screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        if self._screenshot_dir:
            self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots: list[tuple[str, str]] = []
        self._step_no = 0

    def shot(self, label: str) -> None:
        if not self._screenshot_dir:
            return
        self._step_no += 1
        safe = "".join(c if c.isalnum() else "_" for c in label).strip("_")
        path = self._screenshot_dir / f"{self._step_no:02d}_{safe}.png"
        self._page.screenshot(path=str(path))
        self.screenshots.append((label, str(path)))
        print(f"  [screenshot] step {self._step_no}: {label} -> {path}")

    # --- navigation -----------------------------------------------------------

    def open(self) -> None:
        self._page.goto(f"{self._base_url}{self.LOGIN_PATH}",
                        timeout=60000, wait_until="domcontentloaded")
        try:
            self._page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        self._page.wait_for_timeout(1200)
        banner = self._page.locator(self.COOKIE_ACCEPT_SEL)
        if banner.count() and banner.first.is_visible():
            banner.first.click()
            self._page.wait_for_timeout(500)

    def start_guest(self) -> None:
        """Click "Continue as guest" on the login page to open the guest panel."""
        self._page.locator(self.GUEST_BTN_SEL).first.click()
        self._page.wait_for_timeout(1500)

    def guest_panel_shown(self) -> bool:
        """True once the guest panel (with its agreement row) is visible."""
        row = self._page.locator(self.AGREE_SEL)
        return bool(row.count()) and row.first.is_visible()

    def is_guest_session(self) -> bool:
        """True once guest login succeeded and the browser left #/login."""
        return "#/login" not in self._page.url

    # --- 动态码 ---------------------------------------------------------------

    def _solve_dynamic_code(self) -> str:
        img = self._page.locator(self.CAPTCHA_IMG_SEL).first
        img.wait_for(state="visible", timeout=10000)
        raw = _ocr.classification(img.screenshot())
        return "".join(ch for ch in raw if ch.isalnum())

    def _refresh_dynamic_code(self) -> None:
        self._page.locator(self.CAPTCHA_IMG_SEL).first.click()
        self._page.wait_for_timeout(1000)

    def fill_dynamic_code(self, max_attempts: int = 6) -> str:
        code = ""
        for attempt in range(1, max_attempts + 1):
            code = self._solve_dynamic_code()
            print(f"  [guest 动态码 {attempt}/{max_attempts}] -> {code!r}")
            if len(code) == 4:
                self._page.fill(self.DYN_SEL, code)
                return code
            self._refresh_dynamic_code()
        self._page.fill(self.DYN_SEL, code)
        return code

    def fill_dynamic_code_value(self, value: str) -> None:
        self._page.fill(self.DYN_SEL, value)

    # --- agreement / submit ---------------------------------------------------

    def accept_agreement(self) -> None:
        """Click the "I understand and agree to the terms" row."""
        row = self._page.locator(self.AGREE_SEL)
        if row.count():
            row.first.click()
            self._page.wait_for_timeout(400)

    def submit(self) -> bool:
        """Click the guest panel's "Continue as guest" button. Returns False
        WITHOUT clicking if the button is disabled — which is the blocked
        state when robot verification has not been completed."""
        btn = self._page.locator(self.SUBMIT_SEL).first
        if not btn.count() or btn.is_disabled():
            return False
        btn.click()
        self._page.wait_for_timeout(3500)
        return True

    def current_message(self) -> str:
        """Return the first visible error / toast message, or ''."""
        msgs = self._page.evaluate(
            """() => [...document.querySelectorAll(
                  '.error-msg,.field-error,[class*=tip],[class*=toast]')]
                  .map(e => (e.innerText||'').trim()).filter(Boolean)"""
        )
        return msgs[0] if msgs else ""
