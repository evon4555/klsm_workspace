"""Locust entry for the West Kowloon linked-ticket cart flow.

This mirrors the JMeter thread group:

    TG - Linked Ticket

from:

    D:/workspace_tools/Load Test/jmeter/westk load test scripts/
    westk_website_load_test.jmx

The data file is read as a cyclic CSV, matching JMeter's
Recycle on EOF=true / Stop thread on EOF=false behavior.
"""

from __future__ import annotations

import csv
import itertools
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import gevent
from gevent.lock import Semaphore
from locust import HttpUser, constant, events, task


DEFAULT_PARAMS_CSV = (
    r"D:\workspace_tools\Load Test\jmeter\westk load test scripts\westk_params.csv"
)
PARAMS_CSV = Path(
    os.environ.get("WESTK_LINKED_TICKET_CSV")
    or os.environ.get("WESTK_PARAMS_CSV")
    or DEFAULT_PARAMS_CSV
)

LINKED_TICKET_MODE = os.environ.get("PERF_MODE", "mixed").strip().lower()
ENABLE_PROMETHEUS = os.environ.get("LOCUST_PROMETHEUS", "").strip() == "1"
RECORD_TRANSACTIONS = os.environ.get("PERF_RECORD_TRANSACTIONS", "1").strip() != "0"

_csv_rows_lock = Semaphore()
_csv_rows: list[dict[str, str]] | None = None
_csv_cycle = None


def _load_rows() -> list[dict[str, str]]:
    if not PARAMS_CSV.exists():
        raise RuntimeError(f"Linked-ticket CSV not found: {PARAMS_CSV}")
    with PARAMS_CSV.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if not rows:
        raise RuntimeError(f"Linked-ticket CSV has no data rows: {PARAMS_CSV}")
    return rows


def _next_row() -> dict[str, str]:
    global _csv_rows, _csv_cycle
    with _csv_rows_lock:
        if _csv_cycle is None:
            _csv_rows = _load_rows()
            _csv_cycle = itertools.cycle(_csv_rows)
            print(f"[perf] linked-ticket data loaded: {len(_csv_rows)} row(s)")
        return dict(next(_csv_cycle))


def _int_value(row: dict[str, str], key: str, default: int = 0) -> int:
    raw = str(row.get(key, "")).strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _json_value(row: dict[str, str], key: str, default):
    raw = str(row.get(key, "")).strip()
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _compact_json(data: dict) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


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


class LinkedTicketUser(HttpUser):
    """Repeatedly add and cancel a linked admission + seat ticket cart pair."""

    wait_time = constant(0)

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

    def _apply_csv_row(self, row: dict[str, str]) -> None:
        host = urlparse(self.host).hostname or "anticket.lengliwh.com"
        cookies = {
            "Authorization": row.get("cookie_authorization", ""),
            "member_uskey_": row.get("cookie_member_uskey", ""),
            "fctkid": row.get("cookie_fctkid", ""),
            "ukeyage": row.get("cookie_ukeyage", ""),
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
        lock_req = {
            "showId": row.get("showId_linkedTicket", ""),
            "tradeNo": trade_no,
            "items": [
                {
                    "ticketTypeId": row.get("showTicketTypeId_linkedTicket", ""),
                    "ticketType": "normal",
                    "quantity": _int_value(row, "showQuantity", 1),
                }
            ],
        }
        with self.client.post(
            "/thvendor/member/cart/show/addShowItems.xhtml",
            data={
                "showToast": row.get("showToast", ""),
                "lockReq": _compact_json(lock_req),
            },
            name="Add Show Item - linked admission",
            catch_response=True,
        ) as response:
            return self._business_success(response, "addShowItems")

    def _add_seat_item(self, row: dict[str, str], trade_no: str) -> bool:
        lock_req = {
            "scheduleId": row.get("seatScheduleId", ""),
            "tradeNo": trade_no,
            "items": [
                {
                    "venueAreaId": _int_value(row, "seatVenueAreaId"),
                    "rowNo": row.get("seatRowNo", ""),
                    "colNo": row.get("seatColNo", ""),
                }
            ],
            "generalAreas": _json_value(row, "seatGeneralAreas", []),
        }
        with self.client.post(
            "/thvendor/member/cart/ticket/addSeatItems.xhtml",
            data={
                "showToast": row.get("showToast", ""),
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

        prepare_started = time.perf_counter()
        prepare_failure = None
        trade_no = self._get_cart_number()
        if not trade_no:
            prepare_failure = "tradeNo not found"
            trade_no = "CART_NUMBER_NOT_FOUND"

        if not self._cancel_ticket(
            trade_no=trade_no,
            module_type="show",
            session_id=row.get("showId_linkedTicket", ""),
            name="Cancel Show Ticket",
        ):
            prepare_failure = prepare_failure or "Cancel Show Ticket failed"

        if not self._cancel_ticket(
            trade_no=trade_no,
            module_type="ticket",
            session_id=row.get("seatScheduleId", ""),
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
            session_id=row.get("showId_linkedTicket", ""),
            name="Cancel Show Ticket - linked admission",
        ):
            linked_failure = linked_failure or "Cancel linked admission failed"

        if not self._cancel_ticket(
            trade_no=trade_no,
            module_type="ticket",
            session_id=row.get("seatScheduleId", ""),
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
