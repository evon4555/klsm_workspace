"""Standalone Locust entry for a minimal business order-create check.

This file is intentionally focused:
- setup login only
- no ticketing context lookup
- no external test-data dependency

Use it from the dashboard as:

    Locust File: 02-tests/performance/business_create_order.py
    Mode:        Business: order create

It is an HTTP-level scaffold for the order-create endpoint. Because it does not
prepare real show/ticket data, do not use this file as a final capacity test
until those pieces are added.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import string
import time
from datetime import datetime
from urllib.parse import urlparse

from gevent.lock import Semaphore
from locust import HttpUser, between, task


ORDER_CREATE_PATH = "/thvendor/member/show/order/create.xhtml"
GUEST_LOGIN_PATH = os.environ.get("PERF_GUEST_LOGIN_PATH", "/websitehtml/index.html#/login")
WEBSITE_CAPTCHA_ID_PATH = "/ucenter/getCaptchaId.xhtml"
WEBSITE_CAPTCHA_IMAGE_PATH = "/ucenter/captcha.xhtml"
WEBSITE_LOGIN_PATH = "/ucenter/rest/pcLoginByPass.xhtml"
SESSION_COOKIE_TTL_SECONDS = 20 * 60

_session_cookie_lock = Semaphore()
_session_cookie_cache: list[dict] | None = None
_session_cookie_cached_at = 0.0


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"[perf] invalid {name}={raw!r}; falling back to {default}")
        return default


def _order_key() -> str:
    prefix = datetime.now().strftime("%y%m%d%H%M")
    letters = "".join(random.choice(string.ascii_lowercase) for _ in range(7))
    digest = hashlib.md5(f"{time.time()}-{random.random()}".encode()).hexdigest()[:16]
    return prefix + letters + digest


def _order_command() -> dict:
    return {
        "platform": "PC",
        "requestType": "encryption",
        "showId": os.environ.get("PERF_SHOW_ID", "0"),
        "items": [
            {
                "ticketTypeId": os.environ.get("PERF_TICKET_TYPE_ID", "0"),
                "ticketType": os.environ.get("PERF_TICKET_TYPE", "normal"),
                "quantity": _env_int("PERF_TICKET_QUANTITY", 1),
            }
        ],
    }


def _clean_code(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum())


def _guest_login_via_browser(base_url: str) -> list[dict]:
    """Start a guest session in the browser and return storage-state cookies."""
    import ddddocr
    from playwright.sync_api import sync_playwright

    ocr = ddddocr.DdddOcr(show_ad=False)
    base_url = base_url.rstrip("/")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        try:
            response = page.goto(
                f"{base_url}{GUEST_LOGIN_PATH}",
                timeout=60000,
                wait_until="domcontentloaded",
            )
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(1000)

            status = response.status if response else None
            if status and status >= 400:
                raise RuntimeError(f"guest login page unavailable: HTTP {status}")

            cookie_accept = page.locator(".cookie-accept")
            if cookie_accept.count() and cookie_accept.first.is_visible():
                cookie_accept.first.click()
                page.wait_for_timeout(300)

            page.wait_for_selector(".guest-btn", timeout=10000)
            page.locator(".guest-btn").first.click()
            page.wait_for_selector(".guest-agree-row", timeout=15000)

            agreement_clicked = False
            for _attempt in range(1, 7):
                image = page.locator('img[src*="captcha.xhtml"]').first
                image.wait_for(state="visible", timeout=10000)
                code = _clean_code(ocr.classification(image.screenshot()))
                page.fill('input[placeholder="Dynamic Code"]', code)

                if not agreement_clicked:
                    page.locator(".guest-agree-row").first.click()
                    agreement_clicked = True
                    page.wait_for_timeout(300)

                button = page.locator(".submit-btn").first
                if button.count() and not button.is_disabled():
                    button.click()
                    page.wait_for_timeout(3500)
                    if "#/login" not in page.url:
                        return context.storage_state().get("cookies", [])

                try:
                    image.click()
                    page.wait_for_timeout(800)
                except Exception:
                    pass

            raise RuntimeError("guest login failed after captcha attempts")
        finally:
            context.close()
            browser.close()


def _website_login_via_api(base_url: str) -> list[dict]:
    """Log in through website API setup endpoints without recording Locust stats."""
    import ddddocr
    import requests

    username = (
        os.environ.get("PERF_WEBSITE_USERNAME")
        or os.environ.get("TA_WEBSITE_USERNAME")
        or ""
    ).strip()
    password = (
        os.environ.get("PERF_WEBSITE_PASSWORD")
        or os.environ.get("TA_WEBSITE_PASSWORD")
        or ""
    ).strip()
    if not username or not password:
        raise RuntimeError("TA_WEBSITE_USERNAME/TA_WEBSITE_PASSWORD are not set")

    ocr = ddddocr.DdddOcr(show_ad=False)
    base_url = base_url.rstrip("/")
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json, text/plain, */*",
            "cmpappkey": "ShanghaiCS",
            "lang": "en",
            "Referer": f"{base_url}/websitehtml/index.html",
            "User-Agent": "Mozilla/5.0",
        }
    )

    last_error = ""
    for attempt in range(1, 9):
        try:
            captcha_resp = session.post(
                f"{base_url}{WEBSITE_CAPTCHA_ID_PATH}",
                timeout=15,
            )
            captcha_resp.raise_for_status()
            captcha_id = str((captcha_resp.json() or {}).get("data") or "")
            if not captcha_id:
                last_error = "missing captchaId"
                continue

            image_resp = session.get(
                f"{base_url}{WEBSITE_CAPTCHA_IMAGE_PATH}",
                params={"captchaId": captcha_id},
                timeout=15,
            )
            image_resp.raise_for_status()
            captcha_code = _clean_code(ocr.classification(image_resp.content))
            if len(captcha_code) != 4:
                last_error = f"invalid captcha code length on attempt {attempt}"
                continue

            login_resp = session.post(
                f"{base_url}{WEBSITE_LOGIN_PATH}",
                data={
                    "mobileOrEmail": username,
                    "password": password,
                    "captchaId": captcha_id,
                    "captcha": captcha_code,
                },
                timeout=20,
            )
            login_resp.raise_for_status()
            body = login_resp.json() or {}
            if body.get("success") or body.get("errcode") == "0000":
                host = urlparse(base_url).hostname or ""
                cookies = [
                    {
                        "name": cookie.name,
                        "value": cookie.value,
                        "domain": (cookie.domain or host).lstrip("."),
                        "path": cookie.path or "/",
                    }
                    for cookie in session.cookies
                ]
                if cookies:
                    print(f"[perf] website API session refreshed on attempt {attempt}")
                    return cookies
                last_error = "website login returned no cookies"
                continue

            last_error = str(body.get("msg") or body)
        except Exception as exc:
            last_error = str(exc)

    raise RuntimeError(f"website API login failed: {last_error}")


def _login_cookies(base_url: str) -> list[dict]:
    mode = os.environ.get("PERF_AUTH_MODE", "auto").strip().lower()
    if mode not in {"auto", "guest", "website"}:
        raise RuntimeError(f"unsupported PERF_AUTH_MODE={mode!r}")

    if mode in {"auto", "guest"}:
        try:
            cookies = _guest_login_via_browser(base_url)
            print("[perf] guest session refreshed")
            return cookies
        except Exception as exc:
            if mode == "guest":
                raise
            print(f"[perf] guest session unavailable; using website API login: {exc}")

    return _website_login_via_api(base_url)


def _get_session_cookies(base_url: str, force_refresh: bool = False) -> list[dict]:
    global _session_cookie_cache, _session_cookie_cached_at

    now = time.time()
    if (
        not force_refresh
        and _session_cookie_cache
        and now - _session_cookie_cached_at < SESSION_COOKIE_TTL_SECONDS
    ):
        return _session_cookie_cache

    with _session_cookie_lock:
        now = time.time()
        if (
            not force_refresh
            and _session_cookie_cache
            and now - _session_cookie_cached_at < SESSION_COOKIE_TTL_SECONDS
        ):
            return _session_cookie_cache

        cookies = _login_cookies(base_url)
        if not cookies:
            raise RuntimeError("login setup did not return any cookies")
        _session_cookie_cache = cookies
        _session_cookie_cached_at = time.time()
        return cookies


def _business_body_expired(body: dict | None) -> bool:
    if not isinstance(body, dict):
        return False
    errcode = str(body.get("errcode", "")).lower()
    if errcode in {"1205", "401", "403", "not_login", "notlogin"}:
        return True
    msg = str(body.get("msg") or body.get("message") or "").lower()
    expired_tokens = (
        "login",
        "session",
        "unauthorized",
        "\u672a\u767b\u5f55",  # not logged in
        "\u767b\u5f55",        # login
    )
    return any(token in msg for token in expired_tokens)


class OrderCreateUser(HttpUser):
    """Minimal user that repeatedly calls the order-create business endpoint."""

    wait_time = between(1, 3)

    def on_start(self):
        self.client.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "cmpappkey": "ShanghaiCS",
                "lang": "en",
                "Referer": f"{self.host}/websitehtml/index.html",
            }
        )
        self._apply_session()

    def _apply_session(self, force_refresh: bool = False) -> bool:
        cookie_header = os.environ.get("PERF_COOKIE", "").strip()
        if cookie_header:
            self.client.headers.update({"Cookie": cookie_header})
            return True

        try:
            cookies = _get_session_cookies(self.host, force_refresh=force_refresh)
        except Exception as exc:
            print(f"[perf] session bootstrap failed: {exc}")
            return False

        host = urlparse(self.host).hostname or ""
        for cookie in cookies:
            name = cookie.get("name")
            value = cookie.get("value")
            if not name or value is None:
                continue
            domain = (cookie.get("domain") or host).lstrip(".")
            path = cookie.get("path") or "/"
            self.client.cookies.set(name, value, domain=domain, path=path)
        return True

    def _post_create_order(self) -> str:
        with self.client.post(
            ORDER_CREATE_PATH,
            headers={"orderkey": _order_key()},
            data={
                "command": json.dumps(_order_command(), separators=(",", ":")),
                "showToast": "noMsg",
            },
            name="POST /thvendor/member/show/order/create (target)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
                return "expired" if resp.status_code in {401, 403} else "failed"

            body = None
            try:
                body = resp.json()
            except Exception:
                pass

            if _business_body_expired(body):
                resp.failure("session expired")
                return "expired"

            # This standalone file is deliberately HTTP-level. Business-level
            # success checks need real ticketing data.
            resp.success()
            return "ok"

    @task
    def create_order(self):
        result = self._post_create_order()
        if result == "expired" and self._apply_session(force_refresh=True):
            self._post_create_order()


class BusinessUser(OrderCreateUser):
    """Alias so dashboard Business mix mode can still run this focused file."""


class MixedUser(OrderCreateUser):
    """Alias so dashboard Mixed mode can still run this focused file."""
