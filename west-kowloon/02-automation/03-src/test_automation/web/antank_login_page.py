from __future__ import annotations

import base64
import json

import ddddocr
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from playwright.sync_api import Page

_ocr = ddddocr.DdddOcr(show_ad=False)

# AES-ECB key extracted from the app's LoginForm JS bundle
_AES_KEY = "zTw=d0!tD1hGD|B?L`O(6ZS|=wRrGwZy".encode("utf-8")


def _encrypt_credentials(username: str, password: str) -> str:
    """Replicate the app's Ra() function: AES-ECB-PKCS7(JSON({username, password}))."""
    plaintext = json.dumps({"username": username, "password": password}, separators=(",", ":"))
    cipher = AES.new(_AES_KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(plaintext.encode("utf-8"), 16))
    return base64.b64encode(encrypted).decode()


class AntankLoginPage:
    """Handles Antank SSO login via Playwright API (page.request).

    Flow:
      1. API: GET /sso/getCaptchaId.xhtml        → captchaId
      2. API: GET /sso/captcha.xhtml?captchaId=  → captcha image → OCR
      3. API: POST /sso/tbsDoubleCheck.xhtml      → pre-check
      4. API: POST /sso/login.xhtml               → session cookie set
    No browser UI interaction needed.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        self._page = page
        self._base_url = base_url.rstrip("/")
        self._api = page.request  # Playwright APIRequestContext — shares cookies with browser

    def login(self, username: str, password: str, max_attempts: int = 5) -> None:
        """Full API login — browser never renders a page."""
        ecd = _encrypt_credentials(username, password)

        for attempt in range(max_attempts):
            # Step 1: get captchaId
            captcha_id = self._get_captcha_id()

            # Step 2: get captcha image → OCR
            captcha_code = self._solve_captcha(captcha_id)
            print(f"  [login attempt {attempt + 1}] captcha={captcha_code}")

            payload = {"ecd": ecd, "captchaId": captcha_id, "captcha": captcha_code}

            # Step 3: double-check
            self._api.post(
                f"{self._base_url}/sso/tbsDoubleCheck.xhtml",
                form=payload,
            )

            # Step 4: actual login
            resp = self._api.post(
                f"{self._base_url}/sso/login.xhtml",
                form=payload,
            )
            body = resp.json()
            if body.get("success"):
                print(f"  [login] success on attempt {attempt + 1}")
                return

            print(f"  [login] failed: {body.get('msg', body)}")

        raise RuntimeError(f"Login failed after {max_attempts} attempts")

    def _get_captcha_id(self) -> str:
        resp = self._api.get(f"{self._base_url}/sso/getCaptchaId.xhtml")
        data = resp.json()
        return data["data"]

    def _solve_captcha(self, captcha_id: str) -> str:
        resp = self._api.get(
            f"{self._base_url}/sso/captcha.xhtml",
            params={"captchaId": captcha_id},
        )
        return _ocr.classification(resp.body())

    def navigate_to_home(self) -> None:
        """Load the home page using the session cookie set by API login."""
        self._page.goto(f"{self._base_url}/mainframe/index.html#/home", timeout=30000)
        self._page.wait_for_load_state("networkidle", timeout=15000)

    def is_logged_in(self) -> bool:
        return "#/login" not in self._page.url
