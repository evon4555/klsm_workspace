from __future__ import annotations

from pathlib import Path

import ddddocr
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# OCR engine for the 动态码 (image captcha) on the Website login page.
# Module-level singleton — mirrors the pattern in antank_login_page.py.
_ocr = ddddocr.DdddOcr(show_ad=False)


class WebsiteLoginPage:
    """Page object for the West Kowloon ticketing Website email/password login.

    Pure UI automation — fills the real login form with Playwright, no API
    shortcuts. This is the automated counterpart of manual test case
    SIT-TC-WEB-AUTH-009 ("Successful password-mode login").

    Login page : {antank_url}/websitehtml/index.html#/login
    Form fields (email/password is the default tab):
      #login-email     — email
      #login-password  — password
      #login-imgcode   — 动态码 / image captcha
      .submit-btn      — "Log in" button

    The 动态码 is a real distorted-digit captcha, so it is solved with
    ddddocr and retried (refresh + re-solve + re-submit) because OCR is not
    100% accurate — the same strategy AntankLoginPage uses for the SSO login.

    Step screenshots
    ----------------
    If `screenshot_dir` is given, the page object captures a viewport
    screenshot at each distinct (non-repeated) step of the flow and records
    them in `self.screenshots` as a list of (label, path) pairs:
      1. login_page_opened
      2. credentials_and_captcha_filled
      3. login_success   OR   login_failed
    OCR-retry attempts are deliberately NOT screenshotted (they are repeats).
    """

    LOGIN_PATH = "/websitehtml/index.html#/login"

    EMAIL_SEL = "#login-email"
    PASSWORD_SEL = "#login-password"
    CAPTCHA_INPUT_SEL = "#login-imgcode"
    CAPTCHA_IMG_SEL = 'img[src*="captcha.xhtml"]'
    SUBMIT_SEL = ".submit-btn"
    COOKIE_ACCEPT_SEL = ".cookie-accept"
    ERROR_SEL = ".field-error"
    MODE_LINK_SEL = ".mode-link"          # toggles password <-> verification-code mode
    OTP_BOX_SEL = ".otp-box"              # the 6 segmented OTP digit inputs

    def __init__(self, page: Page, base_url: str, screenshot_dir=None) -> None:
        self._page = page
        self._base_url = base_url.rstrip("/")
        self._screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        if self._screenshot_dir:
            self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots: list[tuple[str, str]] = []  # (label, path) captured this run
        self._step_no = 0
        self._form_shot_done = False

    # --- step screenshots -----------------------------------------------------

    def _shot(self, label: str) -> None:
        """Capture a viewport screenshot of the current step.

        Viewport (not full_page) so each screenshot is one normal screen —
        easy to read and to embed into a spreadsheet cell.
        """
        if not self._screenshot_dir:
            return
        self._step_no += 1
        path = self._screenshot_dir / f"{self._step_no:02d}_{label}.png"
        self._page.screenshot(path=str(path))
        self.screenshots.append((label, str(path)))
        print(f"  [screenshot] step {self._step_no}: {label} -> {path}")

    # --- navigation -----------------------------------------------------------

    def open(self) -> None:
        """Open the login page and dismiss the cookie banner if it appears.

        Uses wait_until="commit" (fires when nav request is dispatched) then
        waits for the email-input selector as the real "page is interactive"
        signal. domcontentloaded was observed to never fire on this SPA
        because of type=module scripts — relying on a selector is robust.
        """
        self._page.goto(f"{self._base_url}{self.LOGIN_PATH}",
                        timeout=30000, wait_until="commit")
        # 2026-06-12: SIT cold-start sometimes takes 60-90s for the Vue/SPA to
        # render #login-email after nginx Basic Auth challenge round-trip with
        # a fresh browser context (no asset cache). Bumped 30000 -> 90000.
        self._page.wait_for_selector(self.EMAIL_SEL, state="visible", timeout=90000)
        try:
            self._page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        self._dismiss_cookie_banner()
        self._shot("login_page_opened")

    def _dismiss_cookie_banner(self) -> None:
        """The cookie banner overlaps the "Log in" button — close it first."""
        banner = self._page.locator(self.COOKIE_ACCEPT_SEL)
        if banner.count() and banner.first.is_visible():
            banner.first.click()
            self._page.wait_for_timeout(500)

    # --- form fields ----------------------------------------------------------

    def fill_credentials(self, email: str, password: str) -> None:
        """Fill the email and password fields (动态码 is filled at submit time)."""
        self._page.fill(self.EMAIL_SEL, email)
        self._page.fill(self.PASSWORD_SEL, password)

    def _solve_captcha(self) -> str:
        """Screenshot the 动态码 image and OCR it down to alphanumeric chars."""
        img = self._page.locator(self.CAPTCHA_IMG_SEL).first
        img.wait_for(state="visible", timeout=10000)
        raw = _ocr.classification(img.screenshot())
        return "".join(ch for ch in raw if ch.isalnum())

    def _refresh_captcha(self) -> None:
        """Click the 动态码 image to request a fresh captcha."""
        self._page.locator(self.CAPTCHA_IMG_SEL).first.click()
        self._page.wait_for_timeout(1000)

    def _current_error(self) -> str:
        """Return the first visible form error message — inline (.field-error)
        OR a field-level / toast validation message. '' if none is shown."""
        return (self._page.evaluate(
            r"""() => {
                const sel = '.field-error,.error-msg,[class*=error],'
                  + '[class*=invalid],[class*=tip],[class*=toast]';
                for (const el of document.querySelectorAll(sel)) {
                    const vis = !!(el.offsetWidth || el.offsetHeight
                                   || el.getClientRects().length);
                    const t = (el.innerText || '').trim();
                    if (vis && t && t.length < 200) return t;
                }
                return "";
            }""") or "").strip()

    @staticmethod
    def _is_captcha_error(message: str) -> bool:
        """Return True for image-captcha errors that should be retried."""
        low = (message or "").lower()
        return any(token in low for token in (
            "captcha",
            "dynamic code",
            "verification code",
        ))

    # --- login ----------------------------------------------------------------

    def submit_with_captcha(self, max_attempts: int = 8) -> None:
        """Solve the 动态码, click "Log in", and retry the captcha on failure.

        Credentials must already be filled via fill_credentials(). Refreshing
        the captcha does not clear the email/password fields, so only the
        captcha + submit are repeated. Raises RuntimeError on a non-captcha
        error (e.g. wrong password) or when all captcha attempts are used up.
        """
        for attempt in range(1, max_attempts + 1):
            code = self._solve_captcha()
            print(f"  [login attempt {attempt}/{max_attempts}] 动态码 OCR -> {code!r}")

            # The captcha is 4 characters — a different length means OCR clearly
            # misread it, so refresh without wasting a submit round-trip.
            if len(code) != 4:
                print("  [login] OCR length != 4 — refreshing 动态码")
                self._refresh_captcha()
                continue

            self._page.fill(self.CAPTCHA_INPUT_SEL, code)

            # One screenshot of the fully filled form (first valid attempt only —
            # later retries look the same, so they are not re-captured).
            if not self._form_shot_done:
                self._form_shot_done = True
                self._shot("credentials_and_captcha_filled")

            self._page.click(self.SUBMIT_SEL)
            self._wait_for_login_result()

            if self.is_logged_in():
                print(f"  [login] success on attempt {attempt}")
                # let the home page settle so the screenshot shows a loaded page
                try:
                    self._page.wait_for_load_state("networkidle", timeout=15000)
                except PlaywrightTimeoutError:
                    pass
                self._page.wait_for_timeout(1000)
                self._shot("login_success")
                return

            error = self._current_error()
            if error and not self._is_captcha_error(error):
                # A genuine credential error — retrying the captcha will not help.
                self._shot("login_failed")
                raise RuntimeError(f"Login rejected (non-captcha error): {error}")

            print(f"  [login] 动态码 attempt failed ({error or 'no message'}) — refreshing")
            self._refresh_captcha()

        self._shot("login_failed")
        raise RuntimeError(f"Login failed after {max_attempts} 动态码 attempts")

    def login(self, email: str, password: str, max_attempts: int = 8) -> None:
        """Convenience: fill credentials and submit with captcha retry."""
        self.fill_credentials(email, password)
        self.submit_with_captcha(max_attempts=max_attempts)

    def attempt_login(self, email: str, password: str, max_attempts: int = 8) -> str:
        """Fill credentials, submit (solving the 动态码 with retry), and RETURN
        the outcome instead of raising — for negative login tests (TC010/012).

        Returns "" when login succeeded, otherwise the rejection message
        (e.g. "用户名或密码错误"). The 动态码 is retried so the returned message
        reflects the credential check, not an OCR miss.
        """
        self.fill_credentials(email, password)
        for attempt in range(1, max_attempts + 1):
            code = self._solve_captcha()
            print(f"  [attempt_login {attempt}/{max_attempts}] 动态码 -> {code!r}")
            if len(code) != 4:
                self._refresh_captcha()
                continue
            self._page.fill(self.CAPTCHA_INPUT_SEL, code)
            self._page.click(self.SUBMIT_SEL)
            self._wait_for_login_result()
            if self.is_logged_in():
                return ""
            error = self._current_error()
            if error and not self._is_captcha_error(error):
                return error                       # genuine credential rejection
            self._refresh_captcha()
        return self._current_error() or "login failed (动态码 attempts exhausted)"

    def submit_login_with_captcha_value(self, email: str, password: str,
                                        captcha_value: str) -> str:
        """Fill credentials + a SPECIFIC 动态码 value, submit once, and return
        the inline error ("" if login succeeded) — for the captcha-required
        test (TC031): pass "" for the empty case or a wrong value.
        """
        self.fill_credentials(email, password)
        self._page.fill(self.CAPTCHA_INPUT_SEL, captcha_value)
        self._page.click(self.SUBMIT_SEL)
        self._wait_for_login_result()
        if self.is_logged_in():
            return ""
        return self._current_error()

    def fill_captcha(self, max_attempts: int = 6) -> str:
        """OCR-solve the 动态码 and fill it, refreshing + retrying until OCR
        yields a 4-character code — for tests that need the login form fully
        valid before clicking submit."""
        code = ""
        for _ in range(max_attempts):
            code = self._solve_captcha()
            if len(code) == 4:
                self._page.fill(self.CAPTCHA_INPUT_SEL, code)
                return code
            self._refresh_captcha()
        self._page.fill(self.CAPTCHA_INPUT_SEL, code)
        return code

    def _wait_for_login_result(self) -> None:
        """Wait until the SPA either leaves the #/login route or shows an error."""
        try:
            self._page.wait_for_function(
                """() => {
                    const onLogin = location.hash.includes('/login');
                    const err = document.querySelector('.field-error');
                    return !onLogin || (err && err.offsetParent !== null);
                }""",
                timeout=12000,
            )
        except PlaywrightTimeoutError:
            pass
        self._page.wait_for_timeout(1500)

    # --- assertions / outputs -------------------------------------------------

    def is_logged_in(self) -> bool:
        """True once the browser has left the #/login route."""
        return "#/login" not in self._page.url

    def is_home_page(self) -> bool:
        """True when login succeeded and the login form is no longer shown."""
        if not self.is_logged_in():
            return False
        return not self._page.locator(self.EMAIL_SEL).is_visible()

    def save_screenshot(self, path: str) -> None:
        """Save a full-page screenshot of the current (logged-in) page."""
        self._page.wait_for_load_state("networkidle", timeout=15000)
        self._page.screenshot(path=path, full_page=True)

    # --- OTP-mode login (TC032 / 034 / 035) -----------------------------------

    def switch_to_otp_mode(self) -> None:
        """Click "Log in with verification code" to switch to OTP-mode login."""
        link = self._page.locator(self.MODE_LINK_SEL)
        if link.count():
            link.first.click()
            self._page.wait_for_timeout(1200)

    def otp_boxes_present(self) -> bool:
        """True once the 6 segmented OTP inputs are shown (OTP was requested)."""
        return self._page.locator(self.OTP_BOX_SEL).count() > 0

    def request_verification_code(self, email: str, captcha: str = "auto",
                                  max_attempts: int = 6) -> str:
        """OTP mode: fill email + 动态码, click "Get Verification Code".

        captcha="auto" → OCR-solve the 动态码 with retry; any other value
        (including "") is typed in as-is — for the captcha-required test.
        Returns "" once the OTP entry boxes appear, else the inline error.
        """
        self._page.fill(self.EMAIL_SEL, email)
        if captcha != "auto":
            self._page.fill(self.CAPTCHA_INPUT_SEL, captcha)
            self._page.click(self.SUBMIT_SEL)
            self._page.wait_for_timeout(3000)
            return "" if self.otp_boxes_present() else self._current_error()
        for attempt in range(1, max_attempts + 1):
            code = self._solve_captcha()
            print(f"  [otp-login {attempt}/{max_attempts}] 动态码 -> {code!r}")
            if len(code) != 4:
                self._refresh_captcha()
                continue
            self._page.fill(self.CAPTCHA_INPUT_SEL, code)
            self._page.click(self.SUBMIT_SEL)
            self._page.wait_for_timeout(3000)
            if self.otp_boxes_present():
                return ""
            err = self._current_error()
            if err and not self._is_captcha_error(err):
                return err
            self._refresh_captcha()
        return self._current_error() or "Get Verification Code failed"

    def fill_otp(self, code: str) -> None:
        """Type the OTP into the segmented .otp-box inputs (auto-advances)."""
        boxes = self._page.locator(self.OTP_BOX_SEL)
        if not boxes.count():
            return
        boxes.first.click()
        self._page.keyboard.type(code, delay=90)
        self._page.wait_for_timeout(3000)

    # --- logout (TC013) -------------------------------------------------------

    def logout(self) -> bool:
        """Open the account avatar (which routes to #/my/profile) and click
        the "Sign Out" button (.avatar-popup-btn). Returns True if clicked."""
        avatar = self._page.locator(".avatar-btn")
        if avatar.count():
            avatar.first.click()
            self._page.wait_for_timeout(1500)
        signout = self._page.locator(".avatar-popup-btn")
        if signout.count():
            try:
                signout.first.click(timeout=8000)
            except Exception:                              # noqa: BLE001
                return False
            self._page.wait_for_timeout(2500)
            return True
        return False
