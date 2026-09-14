from __future__ import annotations

from pathlib import Path

import ddddocr
from playwright.sync_api import Page

# OCR engine for the 动态码 image captcha — module-level singleton.
_ocr = ddddocr.DdddOcr(show_ad=False)


class WebsiteForgotPasswordPage:
    """Page object for the West Kowloon Website "forgot password" reset flow.

    Pure UI automation — the automated counterpart of manual test cases
    SIT-TC-WEB-AUTH-015 / 016 / 033.

    Forgot-password page : {antank_url}/websitehtml/index.html#/forget
    Form (email tab is the default; same shape as the registration page):
      input[placeholder="Email"]                 — email
      input[placeholder="Dynamic Code"]          — 动态码 image captcha
      img[src*="captcha.xhtml"]                  — the 动态码 image
      input[placeholder="Verification Code"]     — email OTP
      .get-code-btn                              — request the email OTP
      input[placeholder="New password"]          — new password
      input[placeholder="Confirm new password"]  — confirm new password
      .submit-btn                                — "Continue"
      .error-msg                                 — inline validation message

    Like registration, the 动态码 is OCR-solved and the email OTP is the fixed
    SIT test value 111111 — accepted only after "Get Code" has been clicked.
    """

    FORGET_PATH = "/websitehtml/index.html#/forget"

    EMAIL_SEL = 'input[placeholder="Email"]'
    DYN_SEL = 'input[placeholder="Dynamic Code"]'
    CAPTCHA_IMG_SEL = 'img[src*="captcha.xhtml"]'
    VCODE_SEL = 'input[placeholder="Verification Code"]'
    GETCODE_SEL = '.get-code-btn'
    NEWPWD_SEL = 'input[placeholder="New password"]'
    CONFIRM_SEL = 'input[placeholder="Confirm new password"]'
    SUBMIT_SEL = '.submit-btn'
    ERROR_SEL = '.error-msg'
    COOKIE_ACCEPT_SEL = '.cookie-accept'

    def __init__(self, page: Page, base_url: str, screenshot_dir=None) -> None:
        self._page = page
        self._base_url = base_url.rstrip("/")
        self._screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        if self._screenshot_dir:
            self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots: list[tuple[str, str]] = []
        self._step_no = 0

    # --- step screenshots -----------------------------------------------------

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
        self._page.goto(f"{self._base_url}{self.FORGET_PATH}",
                        timeout=60000, wait_until="domcontentloaded")
        try:
            self._page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        self._page.wait_for_selector(self.EMAIL_SEL, state="visible", timeout=20000)
        banner = self._page.locator(self.COOKIE_ACCEPT_SEL)
        if banner.count() and banner.first.is_visible():
            banner.first.click()
            self._page.wait_for_timeout(500)
        self._page.wait_for_timeout(400)

    def is_on_forget_page(self) -> bool:
        return "#/forget" in self._page.url

    # --- form fields ----------------------------------------------------------

    def fill_email(self, email: str) -> None:
        self._page.fill(self.EMAIL_SEL, email)

    def fill_verification_code(self, code: str) -> None:
        self._page.fill(self.VCODE_SEL, code)

    def fill_new_passwords(self, password: str, confirm: str | None = None) -> None:
        self._page.fill(self.NEWPWD_SEL, password)
        self._page.fill(self.CONFIRM_SEL, confirm if confirm is not None else password)

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
            print(f"  [动态码 OCR {attempt}/{max_attempts}] -> {code!r}")
            if len(code) == 4:
                self._page.fill(self.DYN_SEL, code)
                return code
            self._refresh_dynamic_code()
        self._page.fill(self.DYN_SEL, code)
        return code

    def fill_dynamic_code_value(self, value: str) -> None:
        """Type a specific value into the 动态码 field (for the captcha test)."""
        self._page.fill(self.DYN_SEL, value)

    def captcha_image_src(self) -> str:
        img = self._page.locator(self.CAPTCHA_IMG_SEL).first
        return img.get_attribute("src") or ""

    # --- email OTP ------------------------------------------------------------

    def get_code_button_state(self) -> tuple[str, bool]:
        btn = self._page.locator(self.GETCODE_SEL).first
        if not btn.count():
            return ("", False)
        return (btn.inner_text().strip(), btn.is_disabled())

    def resend_is_cooling_down(self) -> bool:
        text, disabled = self.get_code_button_state()
        return disabled and any(ch.isdigit() for ch in text)

    def request_otp_until_sent(self, max_attempts: int = 8) -> bool:
        """Solve the 动态码 and click "Get Code" until the OTP request is
        accepted (the resend control enters its countdown cooldown)."""
        for attempt in range(1, max_attempts + 1):
            self.fill_dynamic_code()
            btn = self._page.locator(self.GETCODE_SEL).first
            if btn.count() and not btn.is_disabled():
                btn.click()
                self._page.wait_for_timeout(2500)
            if self.resend_is_cooling_down():
                print(f"  [otp] Get Code accepted (attempt {attempt})")
                return True
            self._refresh_dynamic_code()
        print("  [otp] WARNING: Get Code never accepted")
        return False

    # --- submit ---------------------------------------------------------------

    def submit(self) -> None:
        self._page.locator(self.SUBMIT_SEL).first.click()
        self._page.wait_for_timeout(3000)

    def current_error(self) -> str:
        """First visible validation / error message — inline or field-level."""
        return (self._page.evaluate(
            r"""() => {
                const sel = '.error-msg,.field-error,[class*=error],'
                  + '[class*=invalid],[class*=tip]';
                for (const el of document.querySelectorAll(sel)) {
                    const vis = !!(el.offsetWidth || el.offsetHeight
                                   || el.getClientRects().length);
                    const t = (el.innerText || '').trim();
                    if (vis && t && t.length < 200) return t;
                }
                return "";
            }""") or "").strip()

    @staticmethod
    def _is_dynamic_code_error(msg: str) -> bool:
        """Decide whether a submit-form error is the 动态码 (captcha) class,
        i.e. retryable by refresh+re-OCR. Email-OTP failures
        ('邮箱验证码错误...') are a separate, non-retryable class.
        """
        if not msg:
            return False
        if "邮箱" in msg or "邮件" in msg:
            return False
        low = msg.lower()
        return (
            "动态" in msg or "图形" in msg
            or "dynamic" in low or "captcha" in low
        )

    def submit_until_settled(self, max_attempts: int = 8) -> str:
        """Solve the 动态码, click "Continue", retry on a 动态码 error.
        Returns the final inline error ('' if the reset completed)."""
        error = ""
        for attempt in range(1, max_attempts + 1):
            self.fill_dynamic_code()
            self._page.locator(self.SUBMIT_SEL).first.click()
            self._page.wait_for_timeout(3000)
            error = self.current_error()
            print(f"  [submit {attempt}/{max_attempts}] error -> {error!r}")
            if not self._is_dynamic_code_error(error):
                return error
            self._refresh_dynamic_code()
        return error
