from __future__ import annotations

import hashlib
import json
import os
import random
import string
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import ddddocr
import requests
import urllib3
from playwright.sync_api import Browser
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _context_options(**kwargs: Any) -> dict[str, Any]:
    user = os.environ.get("WK_BASIC_AUTH_USER")
    password = os.environ.get("WK_BASIC_AUTH_PASS")
    if user and password:
        kwargs["http_credentials"] = {"username": user, "password": password}
    return kwargs


@dataclass(frozen=True)
class OrderCancelResult:
    member_id: int
    program_id: int
    program_name: str
    show_id: str
    ticket_type_id: str
    trade_no: str
    pay_status: str
    new_list_after_cancel: bool
    cancel_list_after_cancel: bool
    final_url: str
    shots: list[tuple[str, str]]


def _host(base_url: str) -> str:
    return urllib.parse.urlparse(base_url).netloc


def _base_url(raw: str) -> str:
    return raw.rstrip("/")


def _new_session(base_url: str) -> requests.Session:
    session = requests.Session()
    session.verify = False
    session.headers.update(
        {
            "User-Agent": "qa-harness/api-ui-mixed-order-cancel",
            "Accept": "application/json, text/plain, */*",
            "cmpappkey": "ShanghaiCS",
            "lang": "en",
            "Referer": base_url + "/websitehtml/index.html",
        }
    )
    return session


def _request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    endpoint: str,
    **kwargs: Any,
) -> dict[str, Any]:
    resp = session.request(method, url, timeout=20, **kwargs)
    if resp.status_code != 200:
        raise AssertionError(
            f"{endpoint}: expected HTTP 200, got {resp.status_code}. "
            f"Body head: {resp.text[:300]!r}"
        )
    try:
        return resp.json()
    except ValueError as exc:
        raise AssertionError(
            f"{endpoint}: response is not JSON: {exc}; body={resp.text[:300]!r}"
        ) from exc


def _assert_ok(body: dict[str, Any], endpoint: str) -> dict[str, Any]:
    if body.get("errcode") != "0000" or body.get("success") is not True:
        raise AssertionError(f"{endpoint}: expected errcode=0000 success=true, got {body!r}")
    return body


def _api_login(
    session: requests.Session,
    base_url: str,
    email: str,
    password: str,
    *,
    max_attempts: int = 8,
) -> dict[str, Any]:
    ocr = ddddocr.DdddOcr(show_ad=False)
    for attempt in range(1, max_attempts + 1):
        captcha_id = _assert_ok(
            _request_json(
                session,
                "POST",
                base_url + "/ucenter/getCaptchaId.xhtml",
                endpoint="ucenter.getCaptchaId",
            ),
            "ucenter.getCaptchaId",
        )["data"]
        img = session.get(
            base_url + "/ucenter/captcha.xhtml",
            params={"captchaId": captcha_id},
            timeout=10,
        )
        img.raise_for_status()
        code = "".join(ch for ch in ocr.classification(img.content) if ch.isalnum())
        if len(code) != 4:
            continue
        body = _request_json(
            session,
            "POST",
            base_url + "/ucenter/rest/pcLoginByPass.xhtml",
            endpoint="ucenter.rest.pcLoginByPass",
            data={
                "mobileOrEmail": email,
                "password": password,
                "captchaId": captcha_id,
                "captcha": code,
            },
        )
        if body.get("errcode") == "0000" and body.get("success") is True:
            return body
        time.sleep(0.4)
    raise AssertionError("API login failed after captcha OCR attempts")


def _order_key() -> str:
    prefix = datetime.now().strftime("%y%m%d%H%M")
    letters = "".join(random.choice(string.ascii_lowercase) for _ in range(7))
    digest = hashlib.md5(f"{time.time()}-{random.random()}".encode()).hexdigest()[:16]
    return prefix + letters + digest


def _find_order(rows: list[dict[str, Any]], trade_no: str) -> dict[str, Any] | None:
    for row in rows:
        if str(row.get("tradeNo")) == str(trade_no):
            return row
    return None


def _member_orders(
    session: requests.Session,
    base_url: str,
    *,
    status: str,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    body = _assert_ok(
        _request_json(
            session,
            "GET",
            base_url + "/thvendor/member/order/getMemberOrderList.xhtml",
            endpoint=f"thvendor.member.order.getMemberOrderList[{status}]",
            params={
                "pageNo": 1,
                "pageSize": page_size,
                "status": status,
                "expireFlag": "N",
            },
        ),
        f"thvendor.member.order.getMemberOrderList[{status}]",
    )
    return body.get("data", {}).get("resultList", []) or []


def _add_session_cookies(context, session: requests.Session, base_url: str) -> None:
    cookies = []
    for cookie in session.cookies:
        cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "url": base_url,
                "secure": True,
                "httpOnly": False,
                "sameSite": "Lax",
            }
        )
    if cookies:
        context.add_cookies(cookies)


def _render_cancel_status_ui(
    browser: Browser,
    session: requests.Session,
    base_url: str,
    trade_no: str,
    screenshot_dir: Path,
) -> tuple[dict[str, Any], tuple[str, str]]:
    context = browser.new_context(**_context_options(
        ignore_https_errors=True,
        viewport={"width": 1366, "height": 768},
    ))
    _add_session_cookies(context, session, base_url)
    page = context.new_page()
    try:
        page.goto(base_url + "/", wait_until="commit", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeoutError:
            pass
        status = page.evaluate(
            """async ({ tradeNo }) => {
                const load = async (status) => {
                  const qs = new URLSearchParams({
                    pageNo: "1",
                    pageSize: "20",
                    status,
                    expireFlag: "N",
                  });
                  const resp = await fetch(`/thvendor/member/order/getMemberOrderList.xhtml?${qs}`, {
                    credentials: "include",
                    headers: { cmpappkey: "ShanghaiCS", lang: "en" },
                  });
                  const body = await resp.json();
                  return { httpStatus: resp.status, body };
                };
                const newOrders = await load("new");
                const cancelOrders = await load("cancel");
                const rowsNew = newOrders.body?.data?.resultList || [];
                const rowsCancel = cancelOrders.body?.data?.resultList || [];
                const newRow = rowsNew.find((r) => String(r.tradeNo) === String(tradeNo));
                const cancelRow = rowsCancel.find((r) => String(r.tradeNo) === String(tradeNo));
                document.body.innerHTML = "";
                const main = document.createElement("main");
                main.style.cssText = [
                  "font-family: Arial, sans-serif",
                  "padding: 36px",
                  "color: #1f2933",
                ].join(";");
                const title = document.createElement("h1");
                title.textContent = "API+UI mixed order cancellation";
                title.style.margin = "0 0 18px";
                main.appendChild(title);
                const fields = [
                  ["tradeNo", tradeNo],
                  ["new list errcode", newOrders.body?.errcode || ""],
                  ["cancel list errcode", cancelOrders.body?.errcode || ""],
                  ["cancel list row count", rowsCancel.length],
                  ["new order list contains tradeNo", newRow ? "YES" : "NO"],
                  ["cancel order list contains tradeNo", cancelRow ? "YES" : "NO"],
                  ["payStatus", cancelRow?.payStatus || ""],
                  ["realStatus", cancelRow?.realStatus || ""],
                  ["orderType", cancelRow?.orderType || ""],
                ];
                for (const [key, value] of fields) {
                  const row = document.createElement("div");
                  row.style.cssText = "display:flex; gap:18px; padding:10px 0; font-size:20px;";
                  const k = document.createElement("strong");
                  k.style.width = "300px";
                  k.textContent = key;
                  const v = document.createElement("span");
                  v.textContent = String(value);
                  row.append(k, v);
                  main.appendChild(row);
                }
                const badge = document.createElement("div");
                badge.textContent = cancelRow && !newRow ? "ORDER CANCEL VERIFIED" : "ORDER CANCEL NOT VERIFIED";
                badge.style.cssText = [
                  "display:inline-block",
                  "margin-top:28px",
                  "padding:14px 18px",
                  "border-radius:6px",
                  `background:${cancelRow && !newRow ? "#e8f5e9" : "#fff1f0"}`,
                  `color:${cancelRow && !newRow ? "#1b5e20" : "#a8071a"}`,
                  "font-weight:700",
                  "font-size:22px",
                ].join(";");
                main.appendChild(badge);
                document.body.appendChild(main);
                return {
                  newFound: Boolean(newRow),
                  cancelFound: Boolean(cancelRow),
                  payStatus: cancelRow?.payStatus || "",
                  realStatus: cancelRow?.realStatus || "",
                  newErrcode: newOrders.body?.errcode || "",
                  cancelErrcode: cancelOrders.body?.errcode || "",
                  cancelCount: rowsCancel.length,
                };
            }""",
            {"tradeNo": trade_no},
        )
        ui_shot = screenshot_dir / "02_ui_order_cancel_verified.png"
        page.screenshot(path=str(ui_shot), full_page=False)
        return status, ("Step 2  UI order cancel status verified", str(ui_shot))
    finally:
        context.close()


def run_order_cancel_api_ui_mixed(
    browser: Browser,
    base_url: str,
    email: str,
    password: str,
    screenshot_dir: str | Path,
    *,
    program_id: int = 225518,
    quantity: int = 1,
) -> OrderCancelResult:
    base_url = _base_url(base_url)
    screenshot_dir = Path(screenshot_dir)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    session = _new_session(base_url)

    login = _api_login(session, base_url, email, password)
    member_id = int(login["data"]["id"])

    search = _assert_ok(
        _request_json(
            session,
            "POST",
            base_url + "/thvendor/ticket/program/getHotProgramList.xhtml",
            endpoint="thvendor.ticket.program.getHotProgramList",
            params={"categoryIds": "1029"},
        ),
        "thvendor.ticket.program.getHotProgramList",
    )
    search_rows = search.get("data", []) or []
    if not any(int(row.get("id", 0)) == int(program_id) for row in search_rows):
        raise AssertionError(f"program {program_id} was not returned by the ticketing search API")

    program = _assert_ok(
        _request_json(
            session,
            "GET",
            base_url + "/thvendor/ticket/program/getProgramById.xhtml",
            endpoint="thvendor.ticket.program.getProgramById",
            params={"programId": program_id},
        ),
        "thvendor.ticket.program.getProgramById",
    )["data"]
    program_key = str(program["programKey"])
    program_name = (
        program.get("programName")
        or program.get("cnName")
        or program.get("fullCnName")
        or str(program_id)
    )

    shows = _assert_ok(
        _request_json(
            session,
            "GET",
            base_url + "/thvendor/member/show/listBydate.xhtml",
            endpoint="thvendor.member.show.listBydate",
            params={"programKey": program_key, "programId": program_id},
        ),
        "thvendor.member.show.listBydate",
    )["data"]
    chosen_show = next(
        (
            row
            for row in shows
            if row.get("allowBuy") == "Y" and int(row.get("availableNum") or 0) > 0
        ),
        shows[0],
    )
    show_id = str(chosen_show["id"])
    session_key = str(chosen_show["sessionKey"])

    tickets = _assert_ok(
        _request_json(
            session,
            "GET",
            base_url + "/thvendor/member/show/tickettype/list.xhtml",
            endpoint="thvendor.member.show.tickettype.list",
            params={"sessionKey": session_key, "programKey": program_key, "showId": show_id},
        ),
        "thvendor.member.show.tickettype.list",
    )["data"]
    chosen_ticket = next(
        (
            row
            for row in tickets
            if int(row.get("availableNum") or 0) > 0 and row.get("status") == "Y"
        ),
        tickets[0],
    )
    ticket_type_id = str(chosen_ticket["id"])
    ticket_type = str(chosen_ticket.get("ticketType") or "normal")

    command = {
        "platform": "PC",
        "requestType": "encryption",
        "showId": show_id,
        "items": [
            {
                "ticketTypeId": ticket_type_id,
                "ticketType": ticket_type,
                "quantity": int(quantity),
            }
        ],
    }
    create = _request_json(
        session,
        "POST",
        base_url + "/thvendor/member/show/order/create.xhtml",
        endpoint="thvendor.member.show.order.create",
        headers={**session.headers, "orderkey": _order_key()},
        data={"command": json.dumps(command, separators=(",", ":")), "showToast": "noMsg"},
    )
    if create.get("errcode") == "1121" and create.get("data"):
        trade_no = str(create["data"])
    else:
        _assert_ok(create, "thvendor.member.show.order.create")
        create_data = create["data"]
        trade_no = str(create_data.get("tradeNo") if isinstance(create_data, dict) else create_data)
    if not trade_no:
        raise AssertionError(f"create order did not return tradeNo: {create!r}")

    new_before = _find_order(_member_orders(session, base_url, status="new"), trade_no)
    if not new_before and create.get("errcode") != "1121":
        raise AssertionError(f"created tradeNo {trade_no} was not found in new order list")

    _assert_ok(
        _request_json(
            session,
            "GET",
            base_url + "/thvendor/member/show/order/cancelOrder.xhtml",
            endpoint="thvendor.member.show.order.cancelOrder",
            params={"tradeNo": trade_no, "showToast": "noMsg"},
        ),
        "thvendor.member.show.order.cancelOrder",
    )

    new_after = _find_order(_member_orders(session, base_url, status="new"), trade_no)
    cancel_after = _find_order(_member_orders(session, base_url, status="cancel"), trade_no)
    if new_after:
        raise AssertionError(f"tradeNo {trade_no} still appears in the new order list")
    if not cancel_after:
        raise AssertionError(f"tradeNo {trade_no} was not found in the cancel order list")
    pay_status = str(cancel_after.get("payStatus") or "")
    if pay_status != "cancel_user":
        raise AssertionError(f"expected payStatus=cancel_user, got {pay_status!r}")

    result = OrderCancelResult(
        member_id=member_id,
        program_id=int(program_id),
        program_name=str(program_name),
        show_id=show_id,
        ticket_type_id=ticket_type_id,
        trade_no=trade_no,
        pay_status=pay_status,
        new_list_after_cancel=False,
        cancel_list_after_cancel=True,
        final_url=base_url + "/",
        shots=[],
    )

    ui_status, ui_shot = _render_cancel_status_ui(
        browser, session, base_url, trade_no, screenshot_dir
    )
    if ui_status.get("newFound"):
        raise AssertionError(f"UI status check still found tradeNo {trade_no} in new orders")
    if not ui_status.get("cancelFound") or ui_status.get("payStatus") != "cancel_user":
        raise AssertionError(f"UI status check did not confirm cancel_user: {ui_status!r}")

    return OrderCancelResult(
        **{**result.__dict__, "shots": [ui_shot]}
    )
