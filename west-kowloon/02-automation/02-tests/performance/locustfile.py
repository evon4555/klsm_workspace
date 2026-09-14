"""
Locust Performance Test 鈥?Antank ticket system load testing.

Uses the real anticket.lengliwh.com SSO login flow:
  1. GET  /sso/getCaptchaId.xhtml       鈫?captchaId
  2. GET  /sso/captcha.xhtml?captchaId= 鈫?captcha image 鈫?OCR
  3. POST /sso/tbsDoubleCheck.xhtml     鈫?pre-check (AES-encrypted credentials)
  4. POST /sso/login.xhtml              鈫?session cookie set

Then exercises real endpoints:
  - GET  /mainframe/index.html#/home    (home page)
  - GET  /menpiao/index.html            (ticket system SPA)
  - POST /theatre/home/program/op/save  (create program via API)

Usage:
    # Headless mode (for CI/Dashboard integration):
    locust -f 02-tests/performance/locustfile.py --headless -u 10 -r 2 --run-time 60s --host https://anticket.lengliwh.com

    # With web UI:
    locust -f 02-tests/performance/locustfile.py --host https://anticket.lengliwh.com

    # With Prometheus metrics export:
    LOCUST_PROMETHEUS=1 locust -f 02-tests/performance/locustfile.py --headless -u 10 -r 2 --run-time 120s

Environment variables:
    PERF_USERNAME   鈥?login username; no default is stored in source
    PERF_PASSWORD   鈥?login password; no default is stored in source
    LOCUST_PROMETHEUS 鈥?set to "1" to enable Prometheus metrics on :9646
"""

import base64
import hashlib
import json
import os
import random
import string
import time
from datetime import datetime

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from locust import HttpUser, task, between, events

# ---------------------------------------------------------------------------
# AES encryption 鈥?replicates the app's Ra() JS function
# ---------------------------------------------------------------------------

_AES_KEY = "zTw=d0!tD1hGD|B?L`O(6ZS|=wRrGwZy".encode("utf-8")


def _encrypt_credentials(username: str, password: str) -> str:
    """AES-ECB-PKCS7 encrypt login credentials, return base64 string."""
    plaintext = json.dumps(
        {"username": username, "password": password}, separators=(",", ":")
    )
    cipher = AES.new(_AES_KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(plaintext.encode("utf-8"), 16))
    return base64.b64encode(encrypted).decode()


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


# ---------------------------------------------------------------------------
# Captcha OCR (lazy-loaded to avoid slowing import for non-login tasks)
# ---------------------------------------------------------------------------

_ocr_instance = None


def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        import ddddocr
        _ocr_instance = ddddocr.DdddOcr(show_ad=False)
    return _ocr_instance


# ---------------------------------------------------------------------------
# Optional: Prometheus metrics export
# ---------------------------------------------------------------------------

ENABLE_PROMETHEUS = os.environ.get("LOCUST_PROMETHEUS", "").strip() == "1"

if ENABLE_PROMETHEUS:
    try:
        import gevent
        from prometheus_client import Counter, Histogram, Gauge, start_http_server

        REQUEST_LATENCY = Histogram(
            "locust_request_latency_seconds",
            "Request latency in seconds",
            ["name", "method"],
            buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )
        REQUEST_COUNT = Counter(
            "locust_request_count_total",
            "Total request count",
            ["name", "method", "status"],
        )
        ACTIVE_USERS = Gauge(
            "locust_active_users",
            "Number of active virtual users",
        )

        # spawning_complete only fires once at the end of the ramp, so a gauge
        # update there makes the curve look like a step. Poll runner.user_count
        # every 1s instead so Prometheus sees the ramp-up in real time.
        _active_user_poller_stop = False

        def _poll_active_users(environment):
            while not _active_user_poller_stop:
                try:
                    ACTIVE_USERS.set(environment.runner.user_count)
                except Exception:
                    pass
                gevent.sleep(1)

        @events.request.add_listener
        def on_request(request_type, name, response_time, response_length, exception, **kwargs):
            REQUEST_LATENCY.labels(name=name, method=request_type).observe(response_time / 1000)
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


# ---------------------------------------------------------------------------
# Antank virtual user
# ---------------------------------------------------------------------------

# Credentials must come from env/config placeholders; do not store defaults in source.
DEFAULT_USERNAME = os.environ.get("PERF_USERNAME") or os.environ.get("TA_USER1_USERNAME", "")
DEFAULT_PASSWORD = os.environ.get("PERF_PASSWORD") or os.environ.get("TA_USER1_PASSWORD", "")
DEFAULT_WEBSITE_USERNAME = os.environ.get("PERF_WEBSITE_USERNAME") or os.environ.get("TA_WEBSITE_USERNAME", DEFAULT_USERNAME)
DEFAULT_WEBSITE_PASSWORD = os.environ.get("PERF_WEBSITE_PASSWORD") or os.environ.get("TA_WEBSITE_PASSWORD", DEFAULT_PASSWORD)
VALID_PERF_MODES = {"mixed", "login", "business", "order_create", "order_cancel"}
PERF_MODE = os.environ.get("PERF_MODE", "mixed").strip().lower()
if PERF_MODE not in VALID_PERF_MODES:
    print(f"[perf] unknown PERF_MODE={PERF_MODE!r}; falling back to mixed")
    PERF_MODE = "mixed"

# Business mode avoids SSO/captcha by default. Only enable writes when a valid
# pre-authenticated session strategy is available for this process.
PERF_BUSINESS_WRITE = os.environ.get("PERF_BUSINESS_WRITE", "").strip() == "1"
PERF_KEEP_CREATED_ORDERS = os.environ.get("PERF_KEEP_CREATED_ORDERS", "").strip() == "1"
PERF_PROGRAM_ID = _env_int("PERF_PROGRAM_ID", 225518)
PERF_TICKET_QUANTITY = _env_int("PERF_TICKET_QUANTITY", 1)

def _sso_ecd() -> str:
    if not DEFAULT_USERNAME or not DEFAULT_PASSWORD:
        raise RuntimeError(
            "Set PERF_USERNAME/PERF_PASSWORD or TA_USER1_USERNAME/TA_USER1_PASSWORD "
            "before running SSO-based Locust users."
        )
    return _encrypt_credentials(DEFAULT_USERNAME, DEFAULT_PASSWORD)


class AntankUser(HttpUser):
    """Simulates a real user interacting with the Antank ticket system.

    Login uses the full SSO flow: captcha 鈫?AES encryption 鈫?session cookie.
    Subsequent requests use the session cookie automatically (Locust keeps cookies).
    """

    abstract = True
    wait_time = between(1, 3)

    # Track login state
    logged_in = False

    def on_start(self):
        """Perform SSO login before starting tasks."""
        self._login(max_attempts=5)

    def _login(self, max_attempts: int = 5):
        """Full SSO login flow with captcha OCR retry."""
        for attempt in range(max_attempts):
            try:
                # Step 1: get captcha ID
                resp = self.client.get(
                    "/sso/getCaptchaId.xhtml",
                    name="SSO: getCaptchaId",
                )
                if resp.status_code != 200:
                    continue
                captcha_id = resp.json().get("data", "")
                if not captcha_id:
                    continue

                # Step 2: get captcha image and solve via OCR
                resp = self.client.get(
                    "/sso/captcha.xhtml",
                    params={"captchaId": captcha_id},
                    name="SSO: captcha image",
                )
                if resp.status_code != 200:
                    continue

                captcha_code = _get_ocr().classification(resp.content)
                print(f"  [login attempt {attempt + 1}] captcha={captcha_code}")

                form_data = {
                    "ecd": _sso_ecd(),
                    "captchaId": captcha_id,
                    "captcha": captcha_code,
                }

                # Step 3: double-check (pre-validation)
                self.client.post(
                    "/sso/tbsDoubleCheck.xhtml",
                    data=form_data,
                    name="SSO: doubleCheck",
                )

                # Step 4: actual login
                resp = self.client.post(
                    "/sso/login.xhtml",
                    data=form_data,
                    name="SSO: login",
                )
                body = resp.json()
                if body.get("success"):
                    print(f"  [login] success on attempt {attempt + 1}")
                    self.logged_in = True
                    return

                print(f"  [login] failed: {body.get('msg', body)}")

            except Exception as exc:
                print(f"  [login] error on attempt {attempt + 1}: {exc}")

        print(f"  [login] FAILED after {max_attempts} attempts 鈥?user will run without auth")

    # -----------------------------------------------------------------------
    # Tasks 鈥?weighted to simulate realistic traffic patterns
    # -----------------------------------------------------------------------

    @task(5)
    def load_home_page(self):
        """Load the main home page (most common action)."""
        self.client.get(
            "/mainframe/index.html",
            name="GET /mainframe/index.html (home)",
        )

    @task(4)
    def load_menpiao_spa(self):
        """Load the ticket management SPA (闂ㄧエ绁ㄥ姟绯荤粺)."""
        self.client.get(
            "/menpiao/index.html",
            name="GET /menpiao/index.html (ticket SPA)",
        )

    @task(3)
    def get_captcha_id(self):
        """Exercise the captcha endpoint (lightweight API call)."""
        self.client.get(
            "/sso/getCaptchaId.xhtml",
            name="GET /sso/getCaptchaId (API)",
        )

    @task(1)
    def create_program(self):
        """Create a test program via API (write operation)."""
        if not self.logged_in:
            return

        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        rand_suffix = random.randint(1000, 9999)

        self.client.post(
            "/theatre/home/program/op/save.xhtml",
            data={
                "defaultLang": "en",
                "supportLang": "en",
                "cnName": f"perf test {ts}_{rand_suffix}",
                "briefName": f"perf{ts}{rand_suffix}",
                "stadiumId": "69844",
                "venueId": "1708",
                "durationType": "period",
                "startTime": "2026-12-01 00:00:00",
                "endTime": "2026-12-01 23:59:59",
                "minPrice": "0",
                "maxPrice": "1",
                "showMode": "calendar",
                "saleType": "sale",
                "available": "Y",
                "supportSeat": "N",
                "multiGroupCheck": "N",
                "allowInvoice": "N",
                "pushInvoice": "N",
                "consumerInvoiceTime": "paid",
                "bizScenario": "program",
                "blackLimit": "Y",
                "category": "",
                "smallCategory": "",
                "tag": "",
                "approvalNum": "",
                "programCode": "",
                "certLevel": "",
                "productType": "",
            },
            name="POST /theatre/program/save (create program)",
        )

    @task(2)
    def login_flow(self):
        """Re-exercise the full login flow (stress-test SSO)."""
        try:
            resp = self.client.get(
                "/sso/getCaptchaId.xhtml",
                name="SSO flow: getCaptchaId",
            )
            if resp.status_code != 200:
                return

            captcha_id = resp.json().get("data", "")
            if not captcha_id:
                return

            resp = self.client.get(
                "/sso/captcha.xhtml",
                params={"captchaId": captcha_id},
                name="SSO flow: captcha image",
            )
            if resp.status_code != 200:
                return

            captcha_code = _get_ocr().classification(resp.content)

            form_data = {
                "ecd": _sso_ecd(),
                "captchaId": captcha_id,
                "captcha": captcha_code,
            }

            self.client.post(
                "/sso/tbsDoubleCheck.xhtml",
                data=form_data,
                name="SSO flow: doubleCheck",
            )

            self.client.post(
                "/sso/login.xhtml",
                data=form_data,
                name="SSO flow: login",
            )
        except Exception:
            pass


class BasePerfUser(HttpUser):
    """Shared helpers for the selectable Locust user classes."""

    abstract = True
    wait_time = between(1, 3)

    def on_start(self):
        self.logged_in = False
        self.website_logged_in = False
        self.member_id = None
        self.ticketing_context = None
        self.client.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "cmpappkey": "ShanghaiCS",
                "lang": "en",
                "Referer": f"{self.host}/websitehtml/index.html",
            }
        )
        cookie = os.environ.get("PERF_COOKIE", "").strip()
        if cookie:
            self.client.headers.update({"Cookie": cookie})
            self.logged_in = True
            self.website_logged_in = True

    def _request_api_json(
        self,
        method: str,
        path: str,
        *,
        name: str,
        expected_success: bool = True,
        **kwargs,
    ):
        with self.client.request(
            method,
            path,
            name=name,
            catch_response=True,
            **kwargs,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
                return None
            try:
                body = resp.json()
            except Exception as exc:
                resp.failure(f"invalid JSON response: {exc}")
                return None
            if expected_success and (
                body.get("errcode") != "0000" or body.get("success") is not True
            ):
                resp.failure(
                    f"business failed: errcode={body.get('errcode')} "
                    f"success={body.get('success')} msg={body.get('msg')}"
                )
                return None
            return body

    def perform_website_login(self, max_attempts: int = 8) -> bool:
        for attempt in range(max_attempts):
            captcha = self._request_api_json(
                "POST",
                "/ucenter/getCaptchaId.xhtml",
                name="SETUP Website Login: getCaptchaId",
            )
            if not captcha:
                continue
            captcha_id = captcha.get("data", "")
            if not captcha_id:
                continue

            image = self.client.get(
                "/ucenter/captcha.xhtml",
                params={"captchaId": captcha_id},
                name="SETUP Website Login: captcha image",
            )
            if image.status_code != 200:
                continue

            captcha_code = "".join(
                ch for ch in _get_ocr().classification(image.content) if ch.isalnum()
            )
            if len(captcha_code) != 4:
                continue

            body = self._request_api_json(
                "POST",
                "/ucenter/rest/pcLoginByPass.xhtml",
                name="SETUP Website Login: pcLoginByPass",
                data={
                    "mobileOrEmail": DEFAULT_WEBSITE_USERNAME,
                    "password": DEFAULT_WEBSITE_PASSWORD,
                    "captchaId": captcha_id,
                    "captcha": captcha_code,
                },
            )
            if body:
                self.website_logged_in = True
                data = body.get("data") or {}
                self.member_id = data.get("id")
                print(f"  [website login] success on attempt {attempt + 1}")
                return True

        print(f"  [website login] FAILED after {max_attempts} attempts")
        return False

    def ensure_website_login(self) -> bool:
        if self.website_logged_in:
            return True
        return self.perform_website_login(max_attempts=8)

    def ensure_ticketing_context(self) -> bool:
        if self.ticketing_context:
            return True
        if not self.ensure_website_login():
            return False

        search = self._request_api_json(
            "POST",
            "/thvendor/ticket/program/getHotProgramList.xhtml",
            name="SETUP Ticketing: getHotProgramList",
            params={"categoryIds": "1029"},
        )
        if not search:
            return False
        search_rows = search.get("data", []) or []
        if not any(int(row.get("id", 0)) == int(PERF_PROGRAM_ID) for row in search_rows):
            print(f"  [ticketing setup] program {PERF_PROGRAM_ID} not in hot list")

        program_body = self._request_api_json(
            "GET",
            "/thvendor/ticket/program/getProgramById.xhtml",
            name="SETUP Ticketing: getProgramById",
            params={"programId": PERF_PROGRAM_ID},
        )
        if not program_body:
            return False
        program = program_body.get("data") or {}
        program_key = str(program.get("programKey") or "")
        if not program_key:
            print("  [ticketing setup] missing programKey")
            return False

        shows_body = self._request_api_json(
            "GET",
            "/thvendor/member/show/listBydate.xhtml",
            name="SETUP Ticketing: listBydate",
            params={"programKey": program_key, "programId": PERF_PROGRAM_ID},
        )
        if not shows_body:
            return False
        shows = shows_body.get("data") or []
        if not shows:
            print("  [ticketing setup] no shows returned")
            return False
        chosen_show = next(
            (
                row
                for row in shows
                if row.get("allowBuy") == "Y" and int(row.get("availableNum") or 0) > 0
            ),
            shows[0],
        )
        show_id = str(chosen_show.get("id") or "")
        session_key = str(chosen_show.get("sessionKey") or "")
        if not show_id or not session_key:
            print("  [ticketing setup] missing showId/sessionKey")
            return False

        tickets_body = self._request_api_json(
            "GET",
            "/thvendor/member/show/tickettype/list.xhtml",
            name="SETUP Ticketing: tickettype/list",
            params={"sessionKey": session_key, "programKey": program_key, "showId": show_id},
        )
        if not tickets_body:
            return False
        tickets = tickets_body.get("data") or []
        if not tickets:
            print("  [ticketing setup] no ticket types returned")
            return False
        chosen_ticket = next(
            (
                row
                for row in tickets
                if int(row.get("availableNum") or 0) > 0 and row.get("status") == "Y"
            ),
            tickets[0],
        )
        ticket_type_id = str(chosen_ticket.get("id") or "")
        ticket_type = str(chosen_ticket.get("ticketType") or "normal")
        if not ticket_type_id:
            print("  [ticketing setup] missing ticketTypeId")
            return False

        self.ticketing_context = {
            "program_key": program_key,
            "show_id": show_id,
            "ticket_type_id": ticket_type_id,
            "ticket_type": ticket_type,
        }
        return True

    def create_show_order(self, name: str = "POST /thvendor/member/show/order/create"):
        if not self.ensure_ticketing_context():
            return None

        ctx = self.ticketing_context
        command = {
            "platform": "PC",
            "requestType": "encryption",
            "showId": ctx["show_id"],
            "items": [
                {
                    "ticketTypeId": ctx["ticket_type_id"],
                    "ticketType": ctx["ticket_type"],
                    "quantity": PERF_TICKET_QUANTITY,
                }
            ],
        }
        with self.client.post(
            "/thvendor/member/show/order/create.xhtml",
            headers={"orderkey": _order_key()},
            data={
                "command": json.dumps(command, separators=(",", ":")),
                "showToast": "noMsg",
            },
            name=name,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
                return None
            try:
                body = resp.json()
            except Exception as exc:
                resp.failure(f"invalid JSON response: {exc}")
                return None

            trade_no = ""
            if body.get("errcode") == "1121" and body.get("data"):
                trade_no = str(body["data"])
                resp.success()
            elif body.get("errcode") == "0000" and body.get("success") is True:
                data = body.get("data")
                trade_no = str(data.get("tradeNo") if isinstance(data, dict) else data)
            else:
                resp.failure(
                    f"business failed: errcode={body.get('errcode')} "
                    f"success={body.get('success')} msg={body.get('msg')}"
                )
                return None

            if not trade_no:
                resp.failure(f"missing tradeNo in response: {body}")
                return None
            return trade_no

    def cancel_show_order(self, trade_no: str, name: str = "GET /thvendor/member/show/order/cancelOrder") -> bool:
        if not trade_no:
            return False
        body = self._request_api_json(
            "GET",
            "/thvendor/member/show/order/cancelOrder.xhtml",
            name=name,
            params={"tradeNo": trade_no, "showToast": "noMsg"},
        )
        return bool(body)

    def create_show_order_single(self):
        trade_no = self.create_show_order(
            name="POST /thvendor/member/show/order/create (target)"
        )
        if trade_no and not PERF_KEEP_CREATED_ORDERS:
            self.cancel_show_order(
                trade_no,
                name="CLEANUP GET /thvendor/member/show/order/cancelOrder",
            )

    def cancel_show_order_single(self):
        trade_no = self.create_show_order(
            name="SETUP POST /thvendor/member/show/order/create for cancel"
        )
        if trade_no:
            self.cancel_show_order(
                trade_no,
                name="GET /thvendor/member/show/order/cancelOrder (target)",
            )

    def _get_captcha_id(self, name: str):
        with self.client.get(
            "/sso/getCaptchaId.xhtml",
            name=name,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
                return None
            try:
                captcha_id = resp.json().get("data", "")
            except Exception as exc:
                resp.failure(f"invalid captcha id response: {exc}")
                return None
            if not captcha_id:
                resp.failure("missing captchaId")
                return None
            return captcha_id

    def _submit_login(self, form_data: dict, name: str) -> bool:
        with self.client.post(
            "/sso/login.xhtml",
            data=form_data,
            name=name,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
                return False
            try:
                body = resp.json()
            except Exception as exc:
                resp.failure(f"invalid login response: {exc}")
                return False
            if body.get("success"):
                return True
            msg = body.get("msg", body)
            resp.failure(f"login business failed: {msg}")
            print(f"  [login] failed: {msg}")
            return False

    def perform_login(self, max_attempts: int = 5, prefix: str = "SSO", update_state: bool = True) -> bool:
        for attempt in range(max_attempts):
            try:
                captcha_id = self._get_captcha_id(name=f"{prefix}: getCaptchaId")
                if not captcha_id:
                    continue

                resp = self.client.get(
                    "/sso/captcha.xhtml",
                    params={"captchaId": captcha_id},
                    name=f"{prefix}: captcha image",
                )
                if resp.status_code != 200:
                    continue

                captcha_code = _get_ocr().classification(resp.content)
                print(f"  [login attempt {attempt + 1}] captcha={captcha_code}")

                form_data = {
                    "ecd": _sso_ecd(),
                    "captchaId": captcha_id,
                    "captcha": captcha_code,
                }

                self.client.post(
                    "/sso/tbsDoubleCheck.xhtml",
                    data=form_data,
                    name=f"{prefix}: doubleCheck",
                )

                if self._submit_login(form_data, name=f"{prefix}: login"):
                    print(f"  [login] success on attempt {attempt + 1}")
                    if update_state:
                        self.logged_in = True
                    return True
            except Exception as exc:
                print(f"  [login] error on attempt {attempt + 1}: {exc}")

        print(f"  [login] FAILED after {max_attempts} attempts - user will run without auth")
        return False

    def load_home_page(self):
        self.client.get(
            "/mainframe/index.html",
            name="GET /mainframe/index.html (home)",
        )

    def load_menpiao_spa(self):
        self.client.get(
            "/menpiao/index.html",
            name="GET /menpiao/index.html (ticket SPA)",
        )

    def get_captcha_id_api(self):
        self._get_captcha_id(name="GET /sso/getCaptchaId (API)")

    def create_program(self):
        if not self.logged_in:
            return

        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        rand_suffix = random.randint(1000, 9999)

        self.client.post(
            "/theatre/home/program/op/save.xhtml",
            data={
                "defaultLang": "en",
                "supportLang": "en",
                "cnName": f"perf test {ts}_{rand_suffix}",
                "briefName": f"perf{ts}{rand_suffix}",
                "stadiumId": "69844",
                "venueId": "1708",
                "durationType": "period",
                "startTime": "2026-12-01 00:00:00",
                "endTime": "2026-12-01 23:59:59",
                "minPrice": "0",
                "maxPrice": "1",
                "showMode": "calendar",
                "saleType": "sale",
                "available": "Y",
                "supportSeat": "N",
                "multiGroupCheck": "N",
                "allowInvoice": "N",
                "pushInvoice": "N",
                "consumerInvoiceTime": "paid",
                "bizScenario": "program",
                "blackLimit": "Y",
                "category": "",
                "smallCategory": "",
                "tag": "",
                "approvalNum": "",
                "programCode": "",
                "certLevel": "",
                "productType": "",
            },
            name="POST /theatre/program/save (create program)",
        )

    def login_flow_once(self):
        self.perform_login(max_attempts=1, prefix="SSO flow", update_state=False)


class MixedUser(BasePerfUser):
    """End-to-end mixed flow: startup login, business pages, SSO probes, writes."""

    tasks = {
        BasePerfUser.load_home_page: 5,
        BasePerfUser.load_menpiao_spa: 4,
        BasePerfUser.get_captcha_id_api: 3,
        BasePerfUser.create_program: 1,
        BasePerfUser.login_flow_once: 2,
    }

    def on_start(self):
        super().on_start()
        if not self.logged_in:
            self.perform_login(max_attempts=5, prefix="SSO", update_state=True)


class LoginUser(BasePerfUser):
    """Login-only flow for SSO/captcha capacity and business failure rate."""

    tasks = {BasePerfUser.login_flow_once: 1}


class BusinessUser(BasePerfUser):
    """Business-only read flow. Set PERF_COOKIE and PERF_BUSINESS_WRITE=1 for writes."""

    tasks = {
        BasePerfUser.load_home_page: 5,
        BasePerfUser.load_menpiao_spa: 4,
    }


if PERF_BUSINESS_WRITE:
    BusinessUser.tasks = {
        BasePerfUser.load_home_page: 5,
        BasePerfUser.load_menpiao_spa: 4,
        BasePerfUser.create_program: 1,
    }


class TicketingBaseUser(BasePerfUser):
    """Shared setup for ticketing write examples."""

    abstract = True

    def on_start(self):
        super().on_start()
        self.ensure_ticketing_context()


class OrderCreateUser(TicketingBaseUser):
    """Single target example: create a show order.

    The task cleans up by cancelling the created order unless
    PERF_KEEP_CREATED_ORDERS=1 is set.
    """

    tasks = {BasePerfUser.create_show_order_single: 1}


class OrderCancelUser(TicketingBaseUser):
    """Single target example: cancel a show order.

    Each iteration creates a fresh unpaid order as SETUP, then measures the
    cancelOrder endpoint as the target request.
    """

    tasks = {BasePerfUser.cancel_show_order_single: 1}

