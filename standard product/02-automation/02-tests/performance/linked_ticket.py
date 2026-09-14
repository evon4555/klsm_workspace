"""Locust entry for Standard Product linked-ticket cart flow.

The script is project-local by design. It does not depend on West Kowloon
automation files. Runtime data comes from a local CSV because the flow needs
member cookies plus real show and seat identifiers.
"""

from __future__ import annotations

import csv
import base64
import itertools
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import gevent
from gevent.lock import Semaphore
from locust import HttpUser, constant, events, task


AUTOMATION_ROOT = Path(
    os.environ.get("QA_PROJECT_AUTOMATION_ROOT")
    or Path(__file__).resolve().parents[2]
)
DEFAULT_LOCAL_CSV = AUTOMATION_ROOT / "06-envs" / "linked_ticket_params.local.csv"
DEFAULT_TOOLS_CSV = Path(
    r"D:\workspace_tools\Load Test\jmeter\carts_ticket_checkout\carts_ticket_checkout_params.local.csv"
)
PARAMS_CSV = Path(
    os.environ.get("STD_LINKED_TICKET_CSV")
    or os.environ.get("TA_LINKED_TICKET_CSV")
    or (DEFAULT_LOCAL_CSV if DEFAULT_LOCAL_CSV.exists() else DEFAULT_TOOLS_CSV)
)

ENABLE_PROMETHEUS = os.environ.get("LOCUST_PROMETHEUS", "").strip() == "1"
RECORD_TRANSACTIONS = os.environ.get("PERF_RECORD_TRANSACTIONS", "1").strip() != "0"
USE_CSV_COOKIES = os.environ.get("PERF_USE_CSV_COOKIES", "0").strip() == "1"
GUEST_LOGIN_PATH = os.environ.get("PERF_GUEST_LOGIN_PATH", "/websitehtml/index.html#/login")
WEBSITE_CAPTCHA_ID_PATH = "/ucenter/getCaptchaId.xhtml"
WEBSITE_CAPTCHA_IMAGE_PATH = "/ucenter/captcha.xhtml"
WEBSITE_LOGIN_PATH = "/ucenter/rest/pcLoginByPass.xhtml"
SESSION_COOKIE_TTL_SECONDS = 20 * 60

_csv_rows_lock = Semaphore()
_csv_rows: list[dict[str, str]] | None = None
_csv_cycle = None
_session_cookie_lock = Semaphore()
_session_cookie_cache: list[dict] | None = None
_session_cookie_cached_at = 0.0


def _load_rows() -> list[dict[str, str]]:
    if not PARAMS_CSV.exists():
        raise RuntimeError(
            "Standard Product linked-ticket CSV not found. Set "
            "STD_LINKED_TICKET_CSV or create 06-envs/linked_ticket_params.local.csv"
        )
    with PARAMS_CSV.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if not rows:
        raise RuntimeError(f"Standard Product linked-ticket CSV has no rows: {PARAMS_CSV}")
    return rows


def _next_row() -> dict[str, str]:
    global _csv_rows, _csv_cycle
    with _csv_rows_lock:
        if _csv_cycle is None:
            _csv_rows = _load_rows()
            _csv_cycle = itertools.cycle(_csv_rows)
            print(f"[perf] standard-product linked-ticket data loaded: {len(_csv_rows)} row(s)")
        return dict(next(_csv_cycle))


def _first(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return ""


def _int_value(row: dict[str, str], key: str, default: int = 0) -> int:
    raw = _first(row, key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"[perf] invalid {name}={raw!r}; falling back to {default}")
        return default


def _json_value(row: dict[str, str], key: str, default):
    raw = _first(row, key)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _clean_code(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum())


def _compact_json(data: dict) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _basic_auth_pair() -> tuple[str, str] | None:
    user = (
        os.environ.get("PERF_BASIC_AUTH_USER")
        or os.environ.get("TA_BASIC_AUTH_USER")
        or os.environ.get("WK_BASIC_AUTH_USER")
        or ""
    ).strip()
    password = (
        os.environ.get("PERF_BASIC_AUTH_PASS")
        or os.environ.get("TA_BASIC_AUTH_PASS")
        or os.environ.get("WK_BASIC_AUTH_PASS")
        or ""
    ).strip()
    if not user or not password:
        return None
    return user, password


def _basic_auth_header() -> str | None:
    pair = _basic_auth_pair()
    if not pair:
        return None
    token = base64.b64encode(f"{pair[0]}:{pair[1]}".encode("utf-8")).decode()
    return f"Basic {token}"


def _fire_transaction(name: str, started_at: float, failure: str | None) -> None:
    if not RECORD_TRANSACTIONS:
        return
    events.request.fire(
        request_type="TXN",
        name=name,
        response_time=(time.perf_counter() - started_at) * 1000,
        response_length=0,
        exception=RuntimeError(failure) if failure else None,
    )


if ENABLE_PROMETHEUS:
    try:
        from prometheus_client import Counter, Gauge, Histogram, start_http_server

        REQUEST_LATENCY = Histogram(
            "locust_request_latency_seconds",
            "Request latency in seconds",
            ["name", "method"],
            buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        )
        REQUEST_COUNT = Counter(
            "locust_request_count_total",
            "Total request count",
            ["name", "method", "status"],
        )
        ACTIVE_USERS = Gauge("locust_active_users", "Number of active virtual users")
        _active_user_poller_stop = False

        def _poll_active_users(environment):
            while not _active_user_poller_stop:
                try:
                    ACTIVE_USERS.set(environment.runner.user_count)
                except Exception:
                    pass
                gevent.sleep(1)

        @events.request.add_listener
        def on_request(
            request_type,
            name,
            response_time,
            response_length,
            exception,
            **kwargs,
        ):
            REQUEST_LATENCY.labels(name=name, method=request_type).observe(
                response_time / 1000
            )
            status = "failure" if exception else "success"
            REQUEST_COUNT.labels(name=name, method=request_type, status=status).inc()

        @events.test_start.add_listener
        def on_test_start(environment, **kwargs):
            global _active_user_poller_stop
            start_http_server(9646, addr="0.0.0.0")
            ACTIVE_USERS.set(0)
            _active_user_poller_stop = False
            gevent.spawn(_poll_active_users, environment)
            print("[perf] Prometheus metrics available at http://0.0.0.0:9646/metrics")

        @events.test_stop.add_listener
        def on_test_stop(environment, **kwargs):
            global _active_user_poller_stop
            _active_user_poller_stop = True
            ACTIVE_USERS.set(0)

        print("[perf] Prometheus export enabled")
    except ImportError:
        print("[perf] prometheus_client not installed, skipping Prometheus export")
        ENABLE_PROMETHEUS = False


def _guest_login_via_browser(base_url: str) -> list[dict]:
    """Start a guest website session and return storage-state cookies."""
    import ddddocr
    from playwright.sync_api import sync_playwright

    ocr = ddddocr.DdddOcr(show_ad=False)
    base_url = base_url.rstrip("/")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        basic_pair = _basic_auth_pair()
        context_kwargs = {"ignore_https_errors": True}
        if basic_pair:
            context_kwargs["http_credentials"] = {
                "username": basic_pair[0],
                "password": basic_pair[1],
            }
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        try:
            page.goto(
                f"{base_url}{GUEST_LOGIN_PATH}",
                timeout=60000,
                wait_until="domcontentloaded",
            )
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(1000)

            cookie_accept = page.locator(".cookie-accept")
            if cookie_accept.count() and cookie_accept.first.is_visible():
                cookie_accept.first.click()
                page.wait_for_timeout(300)

            page.wait_for_selector(".guest-btn", timeout=15000)
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
    """Refresh a website member session through API login setup endpoints."""
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
    basic_pair = _basic_auth_pair()
    if basic_pair:
        session.auth = basic_pair
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
    storage_state = (
        os.environ.get("PERF_STORAGE_STATE")
        or os.environ.get("TA_WEBSITE_STORAGE_STATE")
        or ""
    ).strip()
    if storage_state:
        state_path = Path(storage_state)
        data = json.loads(state_path.read_text(encoding="utf-8"))
        cookies = [
            cookie
            for cookie in data.get("cookies", [])
            if isinstance(cookie, dict)
        ]
        if cookies:
            print(f"[perf] website session loaded from storage state: {state_path}")
            return cookies
        raise RuntimeError(f"storage state has no cookies: {state_path}")

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


class LinkedTicketUser(HttpUser):
    """Repeatedly add and cancel a linked admission plus seat ticket cart pair."""

    wait_time = constant(_float_env("PERF_LINKED_TICKET_WAIT_SECONDS", 10.0))

    def on_start(self) -> None:
        self.client.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "cmpappkey": "ShanghaiCS",
                "lang": "en",
                "Origin": self.host.rstrip("/"),
                "Referer": f"{self.host.rstrip('/')}/websitehtml/index.html",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 "
                    "Safari/537.36"
                ),
            }
        )
        basic_header = _basic_auth_header()
        if basic_header:
            self.client.headers.update({"Authorization": basic_header})
        if not USE_CSV_COOKIES:
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

    def _apply_csv_row(self, row: dict[str, str]) -> None:
        if not USE_CSV_COOKIES:
            return
        host = urlparse(self.host).hostname or "anticket.lengliwh.com"
        cookies = {
            "Authorization": _first(row, "cookie_authorization"),
            "member_uskey_": _first(row, "cookie_member_uskey"),
            "fctkid": _first(row, "cookie_fctkid"),
            "ukeyage": _first(row, "cookie_ukeyage"),
        }
        for name, value in cookies.items():
            if value:
                self.client.cookies.set(name, value, domain=host, path="/")

    def _business_success(self, response, label: str) -> bool:
        if response.status_code != 200:
            response.failure(f"{label} HTTP status is not 200: {response.status_code}")
            return False
        try:
            body = response.json()
        except Exception as exc:
            response.failure(f"{label} response is not JSON: {exc}")
            return False

        if body.get("errcode") == "0000" and body.get("success") is True:
            response.success()
            return True

        response.failure(
            f"{label} business failed: errcode={body.get('errcode')} "
            f"success={body.get('success')} msg={body.get('msg')}"
        )
        return False

    def _get_cart_number(self) -> str | None:
        with self.client.post(
            "/thvendor/member/cart/initTicketCart.xhtml",
            data={"platform": "PC"},
            name="Get Cart Number",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}")
                return None
            try:
                body = response.json()
            except Exception as exc:
                response.failure(f"cart response is not JSON: {exc}")
                return None

            trade_no = str((body.get("data") or {}).get("tradeNo") or "")
            if not trade_no:
                response.failure("tradeNo not found")
                return None

            response.success()
            return trade_no

    def _cancel_ticket(
        self,
        *,
        trade_no: str,
        module_type: str,
        session_id: str,
        name: str,
    ) -> bool:
        with self.client.post(
            "/thvendor/member/cart/cancelCartItemsBySession.xhtml",
            data={
                "tradeNo": trade_no,
                "moduleType": module_type,
                "sessionId": session_id,
            },
            name=name,
            catch_response=True,
        ) as response:
            return self._business_success(response, name)

    def _add_show_item(self, row: dict[str, str], trade_no: str) -> bool:
        show_id = _first(row, "showId_linkedTicket", "showId")
        ticket_type_id = _first(row, "showTicketTypeId_linkedTicket", "showTicketTypeId")
        lock_req = {
            "showId": show_id,
            "tradeNo": trade_no,
            "items": [
                {
                    "ticketTypeId": ticket_type_id,
                    "ticketType": _first(row, "showTicketType") or "normal",
                    "quantity": _int_value(row, "showQuantity", 1),
                }
            ],
        }
        with self.client.post(
            "/thvendor/member/cart/show/addShowItems.xhtml",
            data={
                "showToast": _first(row, "showToast") or "noMsg",
                "lockReq": _compact_json(lock_req),
            },
            name="Add Show Item - linked admission",
            catch_response=True,
        ) as response:
            return self._business_success(response, "addShowItems")

    def _add_seat_item(self, row: dict[str, str], trade_no: str) -> bool:
        lock_req = {
            "scheduleId": _first(row, "seatScheduleId"),
            "tradeNo": trade_no,
            "items": [
                {
                    "venueAreaId": _int_value(row, "seatVenueAreaId"),
                    "rowNo": _first(row, "seatRowNo"),
                    "colNo": _first(row, "seatColNo"),
                }
            ],
            "generalAreas": _json_value(row, "seatGeneralAreas", []),
        }
        with self.client.post(
            "/thvendor/member/cart/ticket/addSeatItems.xhtml",
            data={
                "showToast": _first(row, "showToast") or "noMsg",
                "lockReq": _compact_json(lock_req),
            },
            name="Add Seat Item - linked seat",
            catch_response=True,
        ) as response:
            return self._business_success(response, "addSeatItems")

    @task
    def linked_ticket_cart_flow(self) -> None:
        row = _next_row()
        self._apply_csv_row(row)

        show_id = _first(row, "showId_linkedTicket", "showId")
        seat_schedule_id = _first(row, "seatScheduleId")

        prepare_started = time.perf_counter()
        prepare_failure = None
        trade_no = self._get_cart_number()
        if not trade_no:
            prepare_failure = "tradeNo not found"
            trade_no = "CART_NUMBER_NOT_FOUND"

        if not self._cancel_ticket(
            trade_no=trade_no,
            module_type="show",
            session_id=show_id,
            name="Cancel Show Ticket",
        ):
            prepare_failure = prepare_failure or "Cancel Show Ticket failed"

        if not self._cancel_ticket(
            trade_no=trade_no,
            module_type="ticket",
            session_id=seat_schedule_id,
            name="Cancel Seat Ticket",
        ):
            prepare_failure = prepare_failure or "Cancel Seat Ticket failed"

        _fire_transaction("01 - Prepare Clean Cart", prepare_started, prepare_failure)

        linked_started = time.perf_counter()
        linked_failure = None
        if not self._add_show_item(row, trade_no):
            linked_failure = linked_failure or "Add Show Item failed"

        gevent.sleep(2)

        if not self._add_seat_item(row, trade_no):
            linked_failure = linked_failure or "Add Seat Item failed"

        if not self._cancel_ticket(
            trade_no=trade_no,
            module_type="show",
            session_id=show_id,
            name="Cancel Show Ticket - linked admission",
        ):
            linked_failure = linked_failure or "Cancel linked admission failed"

        if not self._cancel_ticket(
            trade_no=trade_no,
            module_type="ticket",
            session_id=seat_schedule_id,
            name="Cancel Seat Ticket - linked seat",
        ):
            linked_failure = linked_failure or "Cancel linked seat failed"

        _fire_transaction(
            "02 - Add / Remove Linked Ticket project",
            linked_started,
            linked_failure,
        )


class MixedUser(LinkedTicketUser):
    """Dashboard compatibility alias; runs the linked-ticket flow."""


class BusinessUser(LinkedTicketUser):
    """Dashboard compatibility alias; runs the linked-ticket flow."""


class OrderCreateUser(LinkedTicketUser):
    """Dashboard compatibility alias; runs the linked-ticket flow."""


class OrderCancelUser(LinkedTicketUser):
    """Dashboard compatibility alias; runs the linked-ticket flow."""


class LoginUser(LinkedTicketUser):
    """Dashboard compatibility alias; runs the linked-ticket flow."""
