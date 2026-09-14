from __future__ import annotations

from pathlib import Path

import ddddocr
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# OCR engine for the 动态码 (image captcha) on the Website registration page.
# Module-level singleton — mirrors website_login_page.py / antank_login_page.py.
_ocr = ddddocr.DdddOcr(show_ad=False)


class WebsiteRegistrationPage:
    """Page object for the West Kowloon ticketing Website native registration.

    Pure UI automation — drives the real registration form with Playwright,
    no API shortcuts. This is the automated counterpart of manual test cases
    SIT-TC-WEB-AUTH-001 .. 008.

    Registration page : {antank_url}/websitehtml/index.html#/register
    Form fields (email tab is the default; fields have no id/name, so they
    are addressed by their placeholder text):
      input[placeholder="Email"]              — email
      input[placeholder="Dynamic Code"]       — 动态码 / image captcha
      .captcha-box img                        — the 动态码 image
      input[placeholder="Verification Code"]  — email OTP
      .get-code-btn                           — request the email OTP
      input[placeholder="Password"]           — password
      input[placeholder="Confirm password"]   — confirm password
      .submit-btn                             — "Continue"
      .error-msg                              — inline validation message
      .terms-link (text "Privacy Policy")     — opens the policy modal
      .terms-dialog / .terms-mask             — the policy modal + overlay
      .terms-text                             — implied-consent sentence

    The 动态码 is a real distorted-digit captcha, solved with ddddocr and
    retried, exactly like website_login_page.py.

    Step screenshots
    ----------------
    `shot(label)` captures a viewport screenshot of the current step into
    `screenshot_dir` and records it in `self.screenshots` as (label, path).
    Callers (the evidence script / step definitions) decide which distinct,
    non-repeated steps to capture.
    """

    REGISTER_PATH = "/websitehtml/index.html#/register"

    EMAIL_SEL = 'input[placeholder="Email"]'
    DYN_SEL = 'input[placeholder="Dynamic Code"]'
    CAPTCHA_IMG_SEL = ".captcha-box img"
    VCODE_SEL = 'input[placeholder="Verification Code"]'
    GETCODE_SEL = ".get-code-btn"
    PASSWORD_SEL = 'input[placeholder="Password"]'
    CONFIRM_SEL = 'input[placeholder="Confirm password"]'
    SUBMIT_SEL = ".submit-btn"
    ERROR_SEL = ".error-msg"
    COOKIE_ACCEPT_SEL = ".cookie-accept"
    TERMS_TEXT_SEL = ".terms-text"
    PRIVACY_LINK_SEL = ".terms-link"
    TERMS_DIALOG_SEL = ".terms-dialog"
    TERMS_MASK_SEL = ".terms-mask"
    # Since ~2026-05-26 the registration form requires an explicit checkbox
    # tick before submission. The checkbox is usually a hidden <input> behind
    # a custom-styled label/span containing the "I have read and agree to..."
    # text. accept_terms() tries multiple selectors to be tolerant of UI churn.
    TERMS_CHECKBOX_SEL = '.terms-check, .agree-check, input[type="checkbox"]'

    def __init__(self, page: Page, base_url: str, screenshot_dir=None) -> None:
        self._page = page
        self._base_url = base_url.rstrip("/")
        self._screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        if self._screenshot_dir:
            self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots: list[tuple[str, str]] = []  # (label, path) captured this run
        self._step_no = 0

    # --- step screenshots -----------------------------------------------------

    def shot(self, label: str) -> None:
        """Capture a viewport screenshot of the current step.

        Viewport (not full_page) so each screenshot is one normal screen —
        easy to read and to embed into a spreadsheet cell.
        """
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
        """Open the registration page and dismiss the cookie banner if shown.

        Uses wait_until="domcontentloaded" because the SPA's "load" event waits
        for every lazy asset and can hang >60s on slow SIT links — even when
        the form itself is already interactive. The real readiness signal is
        the email-input selector below.
        """
        self._page.goto(f"{self._base_url}{self.REGISTER_PATH}",
                        timeout=60000, wait_until="domcontentloaded")
        try:
            self._page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass  # SPA may keep XHRs in flight; selector check below is enough
        # 2026-06-12: SIT cold-start sometimes takes 60-90s for the SPA to
        # render the email input after nginx Basic Auth round-trip; bumped
        # 20000 -> 90000.
        self._page.wait_for_selector(self.EMAIL_SEL, state="visible", timeout=90000)
        self._dismiss_cookie_banner()
        self._page.wait_for_timeout(500)

    def _dismiss_cookie_banner(self) -> None:
        """The cookie banner overlaps the form — close it first."""
        banner = self._page.locator(self.COOKIE_ACCEPT_SEL)
        if banner.count() and banner.first.is_visible():
            banner.first.click()
            self._page.wait_for_timeout(500)

    def is_on_register_page(self) -> bool:
        """True while the browser is still on the #/register route."""
        return "#/register" in self._page.url

    # --- form fields ----------------------------------------------------------

    def fill_email(self, email: str) -> None:
        self._page.fill(self.EMAIL_SEL, email)

    def fill_verification_code(self, code: str) -> None:
        self._page.fill(self.VCODE_SEL, code)

    def accept_terms(self) -> bool:
        """Tick the "I have read and agree to our Terms of Service and Privacy
        Policy" checkbox (required since 2026-05-26 product change). Returns
        True if a checkbox was toggled on, False otherwise.

        Implementation note: we directly toggle the underlying
        `<input type="checkbox">` with `force=True` to bypass any styled
        label/span overlay. Clicking the visible LABEL text would also
        accidentally trigger the .terms-link inside it (which opens the
        Privacy Policy modal and blocks subsequent clicks).
        """
        cb = self._page.locator('input[type="checkbox"]').first
        if cb.count() == 0:
            return False
        try:
            cb.check(force=True, timeout=2000)
            self._page.wait_for_timeout(200)
            return True
        except Exception:
            return False

    def fill_passwords(self, password: str, confirm: str | None = None) -> None:
        self._page.fill(self.PASSWORD_SEL, password)
        self._page.fill(self.CONFIRM_SEL, confirm if confirm is not None else password)

    # --- 动态码 (image captcha) ----------------------------------------------

    def _solve_dynamic_code(self) -> str:
        """Screenshot the 动态码 image and OCR it down to alphanumeric chars."""
        img = self._page.locator(self.CAPTCHA_IMG_SEL).first
        img.wait_for(state="visible", timeout=10000)
        raw = _ocr.classification(img.screenshot())
        return "".join(ch for ch in raw if ch.isalnum())

    def _refresh_dynamic_code(self) -> None:
        """Click the 动态码 image to request a fresh captcha."""
        self._page.locator(self.CAPTCHA_IMG_SEL).first.click()
        self._page.wait_for_timeout(1000)

    def fill_dynamic_code(self, max_attempts: int = 6) -> str:
        """OCR-solve the 动态码 and type it in. Refresh + retry until OCR
        yields a 4-character code. Returns the code that was filled."""
        code = ""
        for attempt in range(1, max_attempts + 1):
            code = self._solve_dynamic_code()
            print(f"  [动态码 OCR attempt {attempt}/{max_attempts}] -> {code!r}")
            if len(code) == 4:
                self._page.fill(self.DYN_SEL, code)
                return code
            self._refresh_dynamic_code()
        # last resort — fill whatever OCR produced so the step is still visible
        self._page.fill(self.DYN_SEL, code)
        return code

    def fill_dynamic_code_value(self, value: str) -> None:
        """Type a specific value into the 动态码 field — for the captcha-
        required test (TC029): pass "" for the empty case or a wrong value."""
        self._page.fill(self.DYN_SEL, value)

    def captcha_image_src(self) -> str:
        """Return the 动态码 image's src attribute. The src carries a random
        token, so it changes whenever the captcha is refreshed."""
        img = self._page.locator(self.CAPTCHA_IMG_SEL).first
        return img.get_attribute("src") or ""

    def refresh_captcha(self) -> None:
        """Click the 动态码 image to load a fresh captcha (public wrapper)."""
        self._refresh_dynamic_code()

    # --- email OTP ------------------------------------------------------------

    def request_otp(self) -> None:
        """Click "Get Code" to request the email OTP. Best-effort: if the
        button is mid-cooldown it is simply left alone."""
        btn = self._page.locator(self.GETCODE_SEL).first
        if btn.count() and not btn.is_disabled():
            btn.click()
            self._page.wait_for_timeout(2500)

    def get_code_button_state(self) -> tuple[str, bool]:
        """Return (button text, disabled?) for the "Get Code" / resend button."""
        btn = self._page.locator(self.GETCODE_SEL).first
        if not btn.count():
            return ("", False)
        return (btn.inner_text().strip(), btn.is_disabled())

    def resend_is_cooling_down(self) -> bool:
        """True when the resend control is disabled and shows a countdown
        (a number, optionally with an 's' suffix) instead of "Get Code"."""
        text, disabled = self.get_code_button_state()
        has_count = any(ch.isdigit() for ch in text)
        return disabled and has_count

    def request_otp_until_sent(self, max_attempts: int = 8) -> bool:
        """Solve the 动态码 and click "Get Code" until the OTP request is
        accepted — the resend control then enters its countdown cooldown.

        The email must already be filled. "Get Code" needs a correct 动态码;
        if OCR misread it the request is rejected and no cooldown starts, so
        the 动态码 is refreshed and retried. Without this step the entered
        Verification Code is rejected as "邮箱验证码已失效". Returns True once
        the OTP has been requested.
        """
        for attempt in range(1, max_attempts + 1):
            self.fill_dynamic_code()
            self.request_otp()
            if self.resend_is_cooling_down():
                print(f"  [otp] Get Code accepted — OTP requested (attempt {attempt})")
                return True
            print(f"  [otp] Get Code not accepted (attempt {attempt}) — refreshing 动态码")
            self._refresh_dynamic_code()
        print("  [otp] WARNING: Get Code never accepted")
        return False

    # --- submit ---------------------------------------------------------------

    def submit(self) -> None:
        self._page.locator(self.SUBMIT_SEL).first.click()
        self._page.wait_for_timeout(3000)

    def current_error(self) -> str:
        """Return the first visible validation / error message — inline
        (.error-msg) OR field-level (e.g. "Please enter the dynamic code"
        rendered under a field). Returns '' if none is shown."""
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

    def registration_succeeded(self) -> bool:
        """True when registration completed — the browser left #/register, or
        the "Registration successful" confirmation modal is shown."""
        if "#/register" not in self._page.url:
            return True
        return bool(self._page.evaluate(
            """() => /registration successful|注册成功|sign ?up successful/i
                       .test(document.body.innerText || '')"""))

    @staticmethod
    def _is_dynamic_code_error(msg: str) -> bool:
        """A 动态码 (image-captcha) error — worth refreshing and retrying.
        The email-OTP error contains 邮箱, so it is explicitly excluded."""
        if not msg or "邮箱" in msg:
            return False
        low = msg.lower()
        return ("动态" in msg or "图形" in msg
                or "dynamic" in low or "captcha" in low)

    def submit_until_settled(self, max_attempts: int = 8) -> str:
        """Solve the 动态码, click "Continue", and retry the 动态码 on an
        image-captcha error. Returns the final inline error message — for the
        OTP-gated cases this settles on the email-OTP error (邮箱验证码错误).

        Email / verification-code / password fields must already be filled."""
        error = ""
        for attempt in range(1, max_attempts + 1):
            self.fill_dynamic_code()
            self._page.locator(self.SUBMIT_SEL).first.click()
            self._page.wait_for_timeout(3000)
            error = self.current_error()
            print(f"  [submit attempt {attempt}/{max_attempts}] error -> {error!r}")
            if not self._is_dynamic_code_error(error):
                return error
            self._refresh_dynamic_code()
        return error

    # --- privacy policy modal -------------------------------------------------

    def open_privacy_policy(self) -> None:
        """Click the "Privacy Policy" link and wait for the policy modal."""
        link = self._page.locator(self.PRIVACY_LINK_SEL, has_text="Privacy")
        link.first.click()
        self._page.wait_for_selector(self.TERMS_DIALOG_SEL, state="visible",
                                     timeout=10000)
        self._page.wait_for_timeout(800)

    def privacy_dialog_visible(self) -> bool:
        dlg = self._page.locator(self.TERMS_DIALOG_SEL)
        return bool(dlg.count()) and dlg.first.is_visible()

    def privacy_dialog_title(self) -> str:
        dlg = self._page.locator(self.TERMS_DIALOG_SEL)
        if not dlg.count():
            return ""
        try:
            return dlg.first.inner_text().strip().splitlines()[0]
        except Exception:
            return ""

    def close_privacy_policy(self) -> None:
        """Close the policy modal — Escape works; fall back to the buttons."""
        self._page.keyboard.press("Escape")
        self._page.wait_for_timeout(600)
        if self.privacy_dialog_visible():
            for sel in (".terms-dialog__close", ".terms-dialog__btn"):
                btn = self._page.locator(sel)
                if btn.count() and btn.first.is_visible():
                    btn.first.click()
                    self._page.wait_for_timeout(600)
                    break

    def email_value(self) -> str:
        """Current value of the email field — used to confirm form data is
        preserved after the privacy modal is closed."""
        return self._page.locator(self.EMAIL_SEL).first.input_value()
