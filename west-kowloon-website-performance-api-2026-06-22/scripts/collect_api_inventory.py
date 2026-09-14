from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import re
import string
import sys
import time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import urllib3
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "raw"
EVIDENCE_DIR = BASE_DIR / "evidence"

SITE = "https://anticket.lengliwh.com"
INDEX_PATH = "/websitehtml/index.html"
ENV_PATH = Path("D:/Workspace/west-kowloon/02-automation/06-envs/.env.sit")
REGISTRY_PATH = Path("D:/Workspace/west-kowloon/02-automation/02-tests/api/data/wk_endpoints.yml")
LEGACY_HAR_PATH = Path("C:/Users/klsm/Downloads/wangyifan/anticket-jmeter/anticket.lengliwh.com.har")

PREFIXES = ("ucenter", "thvendor", "pay", "sms", "wkcda", "menpiao", "cms", "home")
ENDPOINT_RE = re.compile(
    r"(?P<path>/(?:"
    + "|".join(re.escape(p) for p in PREFIXES)
    + r")/[A-Za-z0-9_./?=&%:{}${}\[\],~+@!#-]*?(?:\.xhtml|\.json))"
)
TEMPLATE_ENDPOINT_RE = re.compile(
    r"\$\{(?P<var>[A-Za-z_$][\w$]*)\}"
    r"(?P<suffix>/[A-Za-z0-9_./?=&%:{}${}\[\],~+@!#-]*?(?:\.xhtml|\.json))"
)
JS_REF_RE = re.compile(r"['\"](?P<path>[^'\"]+\.js(?:\?[^'\"]*)?)['\"]")
ROUTE_RE = re.compile(r"['\"](?P<route>/[A-Za-z0-9_/:?=&.%#-]{1,120})['\"]")

SENSITIVE_KEY_RE = re.compile(
    r"password|passwd|pwd|token|cookie|session|authorization|auth|captcha|mobileOrEmail|email|phone|mobile|idNo|identity|nickname|memberName|realName|firstName|lastName|credential|certificate",
    re.IGNORECASE,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


STATIC_INFERENCES: dict[str, dict[str, Any]] = {
    "/ucenter/guest/createAndLogin.xhtml": {
        "method": "POST",
        "purpose": "游客账号创建并登录",
        "body_params": {"_front_end_data_object": "静态推断；需按实际游客登录/绑定流程补字段"},
    },
    "/ucenter/member/bindWxUserInfo.xhtml": {
        "method": "POST",
        "purpose": "绑定微信用户信息",
        "body_params": {"_front_end_data_object": "静态推断；需按微信绑定流程补字段"},
    },
    "/ucenter/member/getUpHeadToken.xhtml": {
        "method": "GET",
        "purpose": "获取头像/图片上传 token",
    },
    "/thvendor/member/common/getDynamicCode.xhtml": {
        "method": "GET",
        "purpose": "获取电子票动态码",
        "query_params": {"uuid": "${uuid}", "needServiceTime": "true"},
    },
    "/pay/cybersource/payment/create.xhtml": {
        "method": "POST",
        "purpose": "创建 CyberSource 支付请求/支付参数",
        "body_params": {"_payment_payload": "静态推断；本次未走支付页，需支付流程抓包补完整字段"},
    },
    "/sms/common/commonUpload.xhtml": {
        "method": "POST",
        "purpose": "通用文件上传",
        "body_params": {"file": "<binary>", "uploadToken": "${uploadToken}"},
        "headers": {"content-type": "multipart/form-data"},
    },
    "/thvendor/common/prepareUpload.xhtml": {
        "method": "GET",
        "purpose": "准备上传并获取 uploadToken",
    },
    "/thvendor/tools/qrcode.xhtml": {
        "method": "GET",
        "purpose": "生成二维码图片",
        "query_params": {"text": "${text}", "backColor": "ffffff", "frontColor": "000000"},
    },
}


def load_env_file(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    if not path.exists():
        return vals
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        vals[key.strip()] = value.strip()
    return vals


def redact_scalar(key: str, value: Any) -> Any:
    if value is None:
        return None
    if SENSITIVE_KEY_RE.search(str(key)):
        return "***REDACTED***"
    text = str(value)
    site_user = os.environ.get("WK_SITE_USER") or os.environ.get("TA_WEBSITE_USERNAME") or ""
    sensitive_values = [site_user]
    if "@" in site_user:
        sensitive_values.append(site_user.split("@", 1)[0])
    for sensitive_value in sensitive_values:
        if sensitive_value and sensitive_value.casefold() in text.casefold():
            return "***REDACTED***"
    if len(text) > 180:
        return text[:180] + "...<truncated>"
    return value


def redact(obj: Any, key: str = "") -> Any:
    if isinstance(obj, dict):
        return {k: redact(v, str(k)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, key) for v in obj[:20]]
    return redact_scalar(key, obj)


def parse_query(query: str) -> dict[str, Any]:
    parsed = urllib.parse.parse_qs(query, keep_blank_values=True)
    return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}


def parse_post_data(text: str | None, mime: str | None = None) -> Any:
    if not text:
        return {}
    text = text.strip()
    if not text:
        return {}
    if "json" in (mime or "").lower() or text[:1] in "{[":
        try:
            return json.loads(text)
        except Exception:
            return text[:500]
    parsed = urllib.parse.parse_qs(text, keep_blank_values=True)
    if parsed:
        result: dict[str, Any] = {}
        for k, v in parsed.items():
            item: Any = v[0] if len(v) == 1 else v
            if isinstance(item, str) and item[:1] in "{[":
                try:
                    item = json.loads(item)
                except Exception:
                    pass
            result[k] = item
        return result
    return text[:500]


def response_sample(text: str | None, content_type: str = "") -> Any:
    if not text:
        return None
    text = text.strip()
    if not text:
        return None
    if "json" in content_type.lower() or text[:1] in "{[":
        try:
            return json.loads(text)
        except Exception:
            return text[:800]
    return text[:800]


def normalize_path(url_or_path: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url_or_path)
    if parsed.scheme:
        return parsed.path, parsed.query
    if "?" in url_or_path:
        path, query = url_or_path.split("?", 1)
        return path, query
    return url_or_path, ""


def infer_template_prefix(body: str, start: int, var_name: str) -> str | None:
    before = body[max(0, start - 5000):start]
    pattern = re.compile(
        r"(?:const|let|var)\s+"
        + re.escape(var_name)
        + r"\s*=\s*['\"](?P<prefix>/(?:"
        + "|".join(re.escape(p) for p in PREFIXES)
        + r"))['\"]"
    )
    matches = list(pattern.finditer(before))
    if not matches:
        return None
    return matches[-1].group("prefix")


def infer_method_from_context(body: str, start: int, path: str) -> str:
    inference = STATIC_INFERENCES.get(path, {})
    if inference.get("method"):
        return str(inference["method"]).upper()

    context = body[max(0, start - 500): min(len(body), start + 900)]
    method_match = re.search(r"method\s*:\s*['\"](?P<method>get|post|put|delete|patch|head)['\"]", context, re.I)
    if method_match:
        return method_match.group("method").upper()
    fetch_match = re.search(r"fetch\([^)]*method\s*:\s*['\"](?P<method>GET|POST|PUT|DELETE|PATCH|HEAD)['\"]", context, re.I)
    if fetch_match:
        return fetch_match.group("method").upper()
    if "Jf.get(" in context or ".get(" in context[:300]:
        return "GET"
    if "Jf.post(" in context or "cSe(" in context or ".post(" in context[:300]:
        return "POST"
    return "UNKNOWN"


def endpoint_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def infer_group(path: str) -> str:
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "other"
    if parts[0] == "ucenter":
        return "auth"
    if len(parts) > 2 and parts[1] == "member":
        if "order" in parts:
            return "member-order"
        if "ticket" in parts or "cart" in parts or "show" in parts:
            return "ticketing"
        return "member"
    if "ticket" in parts or "program" in parts or "show" in parts:
        return "ticketing"
    if "pay" in parts or "cybersource" in path.lower():
        return "payment"
    if "campaign" in parts or "ad" in parts or "content" in parts:
        return "cms"
    return parts[0]


def purpose_from_path(path: str, notes: str = "") -> str:
    if notes:
        return notes
    if path in STATIC_INFERENCES and STATIC_INFERENCES[path].get("purpose"):
        return str(STATIC_INFERENCES[path]["purpose"])
    mapping = {
        "getCaptchaId": "获取验证码会话 ID",
        "pcLoginByPass": "账号密码登录，带图片验证码",
        "getLogonInfo": "获取当前登录会员信息",
        "telephoneCountryCodes": "获取电话国家/地区码",
        "getHotProgramList": "获取首页/列表热门项目",
        "getProgramById": "获取项目详情主数据",
        "getProgramContentInfo": "获取项目富文本/详情内容",
        "scheduleDateListWithSellOut": "获取有售罄标记的场次日期",
        "listScheduleByDate": "按日期获取座位类场次",
        "getScheduleInfo": "获取座位类场次信息",
        "getSchedulePrices": "获取座位类票价",
        "getAvailableSeats2": "获取座位图可售座位和 orderKey",
        "getSpecialSeatOverlay": "获取特殊座位覆盖层",
        "discount": "查询座位/票价优惠",
        "create2": "创建座位类订单",
        "listBydate": "获取非座位类场次列表",
        "tickettype": "获取非座位类票种列表",
        "order/create": "创建非座位类订单",
        "cancelOrder": "取消未支付订单",
        "getMemberOrderList": "获取会员订单列表",
        "getAllValidTicketList": "获取有效票列表",
        "getMemberInfo": "获取会员核心信息",
        "getPersonalInfo": "获取个人资料",
        "getMemberCouponsByStatus": "按状态获取会员优惠券",
        "listFavorites": "获取收藏列表",
        "isFavorites": "判断项目是否已收藏",
        "getFavoritesTotal": "获取项目收藏数量",
        "initTicketCart": "初始化购票购物车",
        "getCartDetail": "获取购物车详情",
        "getNewAdList": "获取广告/轮播数据",
        "getCategoryList": "获取项目分类",
        "getStadiums": "获取场馆列表",
        "getDisplayConfig": "获取站点展示配置",
    }
    for needle, text in mapping.items():
        if needle in path:
            return text
    lower = path.lower()
    if "refund" in lower:
        return "退票/退款相关接口"
    if "cancel" in lower:
        return "取消/撤销相关接口"
    if "/pay" in lower or lower.endswith("/pay.xhtml") or "payorder" in lower:
        return "支付/重新支付相关接口"
    if "create" in lower or "save" in lower or "add" in lower:
        return "创建/保存相关接口"
    if "update" in lower or "change" in lower or "modify" in lower:
        return "更新/变更相关接口"
    if "delete" in lower or "remove" in lower or "clear" in lower:
        return "删除/移除相关接口"
    if "list" in lower or "page" in lower:
        return "列表/分页查询接口"
    if "detail" in lower or "info" in lower:
        return "详情查询接口"
    if "discount" in lower or "coupon" in lower or "promo" in lower:
        return "优惠/折扣相关接口"
    if "membership" in lower:
        return "会员卡/会员权益相关接口"
    if "cart" in lower:
        return "购物车相关接口"
    return "静态包发现，未在本次抓包中拿到业务说明"


def make_session(basic_user: str, basic_pass: str) -> requests.Session:
    session = requests.Session()
    session.auth = (basic_user, basic_pass)
    session.verify = False
    session.headers.update(
        {
            "User-Agent": "codex-west-kowloon-api-inventory/2026-06-22",
            "Accept": "application/json, text/plain, */*",
            "cmpappkey": "ShanghaiCS",
            "lang": "en",
            "Referer": SITE + INDEX_PATH,
        }
    )
    return session


def absolutize(base_url: str, ref: str) -> str:
    return urllib.parse.urljoin(base_url, ref)


def static_discovery(session: requests.Session) -> tuple[dict[str, dict[str, Any]], list[str]]:
    index_url = SITE + INDEX_PATH
    index = session.get(index_url, timeout=20)
    index.raise_for_status()

    queue: list[str] = []
    seen_assets: set[str] = set()

    for match in JS_REF_RE.finditer(index.text):
        queue.append(absolutize(index_url, match.group("path")))

    endpoints: dict[str, dict[str, Any]] = {}
    routes: set[str] = set()

    while queue and len(seen_assets) < 350:
        url = queue.pop(0)
        if url in seen_assets:
            continue
        seen_assets.add(url)
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code != 200:
                continue
            body = resp.text
        except Exception:
            continue

        def add_static_endpoint(raw_path: str, start: int, source: str) -> None:
            path, query = normalize_path(raw_path)
            inference = STATIC_INFERENCES.get(path, {})
            method = infer_method_from_context(body, start, path)
            key = endpoint_key(method, path)
            rec = endpoints.setdefault(
                key,
                {
                    "method": method,
                    "path": path,
                    "source": [],
                    "query_params": {},
                    "body_params": {},
                    "headers": {},
                    "response_sample": None,
                    "status_samples": [],
                    "notes": [],
                },
            )
            rec["source"].append(source)
            if query:
                rec["query_params"].update(redact(parse_query(query)))
            if inference.get("query_params"):
                rec["query_params"].update(redact(inference["query_params"]))
            if inference.get("body_params"):
                rec["body_params"].update(redact(inference["body_params"]))
            if inference.get("headers"):
                rec["headers"].update(redact(inference["headers"]))
            if inference.get("purpose"):
                rec["purpose"] = inference["purpose"]
            if source.endswith("_template"):
                rec["notes"].append("静态模板路径展开；本次未必现场触发")

        for match in ENDPOINT_RE.finditer(body):
            add_static_endpoint(match.group("path"), match.start(), "current_spa_static")

        for match in TEMPLATE_ENDPOINT_RE.finditer(body):
            prefix = infer_template_prefix(body, match.start(), match.group("var"))
            if not prefix:
                continue
            add_static_endpoint(prefix + match.group("suffix"), match.start(), "current_spa_static_template")

        for match in ROUTE_RE.finditer(body):
            route = match.group("route")
            if route.startswith("/") and not route.startswith("//") and ".xhtml" not in route and len(route) > 1:
                if not any(route.endswith(ext) for ext in (".js", ".css", ".png", ".jpg", ".svg")):
                    routes.add(route)

        for match in JS_REF_RE.finditer(body):
            ref = match.group("path")
            if ref.startswith("http"):
                next_url = ref
            elif ref.startswith("/"):
                next_url = SITE + ref
            else:
                next_url = urllib.parse.urljoin(url, ref)
            if "anticket.lengliwh.com" in next_url and next_url not in seen_assets:
                queue.append(next_url)

    return endpoints, sorted(routes)


def load_registry() -> dict[str, dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        return {}
    raw = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    records: dict[str, dict[str, Any]] = {}
    for ep in raw.get("endpoints", []):
        method = str(ep.get("method") or "UNKNOWN").upper()
        path = str(ep.get("path") or "")
        if not path:
            continue
        records[endpoint_key(method, path)] = {
            "method": method,
            "path": path,
            "source": ["local_wk_endpoints_registry"],
            "query_params": {},
            "body_params": {},
            "headers": {},
            "response_sample": None,
            "status_samples": [],
            "auth_required": ep.get("auth_required"),
            "notes": [str(ep.get("notes") or "")],
            "purpose": str(ep.get("notes") or ""),
        }
    return records


def parse_har(path: Path, label: str) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    records: dict[str, dict[str, Any]] = {}
    for ent in raw.get("log", {}).get("entries", []):
        req = ent.get("request", {}) or {}
        resp = ent.get("response", {}) or {}
        url = req.get("url", "")
        if "anticket.lengliwh.com" not in url:
            continue
        path_only, query = normalize_path(url)
        if not (path_only.endswith(".xhtml") or path_only.endswith(".json") or "/api/" in path_only):
            continue
        method = str(req.get("method") or "GET").upper()
        key = endpoint_key(method, path_only)
        headers = {
            h.get("name", ""): h.get("value", "")
            for h in req.get("headers", []) or []
            if h.get("name", "").lower() in {"content-type", "cmpappkey", "lang", "orderkey", "accept"}
        }
        post = req.get("postData") or {}
        mime = post.get("mimeType") or ""
        body_text = post.get("text")
        if not body_text and post.get("params"):
            body_text = urllib.parse.urlencode({p["name"]: p.get("value", "") for p in post.get("params", [])})
        content = resp.get("content", {}) or {}
        content_type = content.get("mimeType") or ""
        sample = response_sample(content.get("text"), content_type)
        rec = records.setdefault(
            key,
            {
                "method": method,
                "path": path_only,
                "source": [],
                "query_params": {},
                "body_params": {},
                "headers": {},
                "response_sample": None,
                "status_samples": [],
                "notes": [],
            },
        )
        rec["source"].append(label)
        rec["query_params"].update(redact(parse_query(query)))
        body_params = parse_post_data(body_text, mime)
        if isinstance(body_params, dict):
            rec["body_params"].update(redact(body_params))
        elif body_params:
            rec["body_params"]["raw"] = redact(body_params)
        rec["headers"].update(redact(headers))
        if sample is not None and rec["response_sample"] is None:
            rec["response_sample"] = redact(sample)
        if resp.get("status") is not None:
            rec["status_samples"].append(resp.get("status"))
    return records


def order_key() -> str:
    prefix = datetime.now().strftime("%y%m%d%H%M")
    letters = "".join(random.choice(string.ascii_lowercase) for _ in range(7))
    digest = hashlib.md5(f"{time.time()}-{random.random()}".encode()).hexdigest()[:16]
    return prefix + letters + digest


def dynamic_crawl(
    basic_user: str,
    basic_pass: str,
    site_user: str,
    site_pass: str,
) -> dict[str, dict[str, Any]]:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
    import ddddocr

    records: dict[str, dict[str, Any]] = {}
    ocr = ddddocr.DdddOcr(show_ad=False)

    default_routes = [
        "/websitehtml/index.html#/",
        "/websitehtml/index.html#/projects",
        "/websitehtml/index.html#/calendar",
        "/websitehtml/index.html#/activity/list",
        "/websitehtml/index.html#/news/list",
        "/websitehtml/index.html#/search",
        "/websitehtml/index.html#/about",
        "/websitehtml/index.html#/membership",
        "/websitehtml/index.html#/cart",
        "/websitehtml/index.html#/my",
        "/websitehtml/index.html#/my/orders",
        "/websitehtml/index.html#/my/tickets",
        "/websitehtml/index.html#/my/profile",
        "/websitehtml/index.html#/my/cards",
        "/websitehtml/index.html#/my/coupons",
        "/websitehtml/index.html#/my/wishlist",
        "/websitehtml/index.html#/my/identity",
        "/websitehtml/index.html#/my/points",
        "/websitehtml/index.html#/my/shipping",
        "/websitehtml/index.html#/my/priority",
        "/websitehtml/index.html#/settings",
    ]

    def add_from_response(resp) -> None:
        try:
            req = resp.request
            url = resp.url
            if "anticket.lengliwh.com" not in url:
                return
            parsed = urllib.parse.urlparse(url)
            path = parsed.path
            if not (path.endswith(".xhtml") or path.endswith(".json") or req.resource_type in {"xhr", "fetch"}):
                return
            method = req.method.upper()
            key = endpoint_key(method, path)
            rec = records.setdefault(
                key,
                {
                    "method": method,
                    "path": path,
                    "source": [],
                    "query_params": {},
                    "body_params": {},
                    "headers": {},
                    "response_sample": None,
                    "status_samples": [],
                    "notes": [],
                },
            )
            rec["source"].append("current_playwright_crawl")
            rec["query_params"].update(redact(parse_query(parsed.query)))
            pdata = parse_post_data(req.post_data, req.header_value("content-type") or "")
            if isinstance(pdata, dict):
                rec["body_params"].update(redact(pdata))
            elif pdata:
                rec["body_params"]["raw"] = redact(pdata)
            headers = {}
            for hn in ("content-type", "cmpappkey", "lang", "orderkey", "accept"):
                hv = req.header_value(hn)
                if hv:
                    headers[hn] = hv
            rec["headers"].update(redact(headers))
            ctype = resp.headers.get("content-type", "")
            if rec["response_sample"] is None and ("json" in ctype.lower() or path.endswith(".xhtml")):
                try:
                    txt = resp.text()
                    rec["response_sample"] = redact(response_sample(txt, ctype))
                except Exception:
                    pass
            rec["status_samples"].append(resp.status)
        except Exception:
            return

    def solve_and_login(page) -> bool:
        page.goto(SITE + "/websitehtml/index.html#/login", wait_until="commit", timeout=60000)
        page.wait_for_selector("#login-email", timeout=90000)
        try:
            if page.locator(".cookie-accept").count() and page.locator(".cookie-accept").first.is_visible():
                page.locator(".cookie-accept").first.click()
        except Exception:
            pass
        page.fill("#login-email", site_user)
        page.fill("#login-password", site_pass)
        for _ in range(10):
            img = page.locator('img[src*="captcha.xhtml"]').first
            img.wait_for(state="visible", timeout=15000)
            code = "".join(ch for ch in ocr.classification(img.screenshot()) if ch.isalnum())
            if len(code) != 4:
                img.click()
                page.wait_for_timeout(900)
                continue
            page.fill("#login-imgcode", code)
            page.click(".submit-btn")
            page.wait_for_timeout(2500)
            if "#/login" not in page.url:
                return True
            try:
                img.click()
            except Exception:
                pass
            page.wait_for_timeout(900)
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            ignore_https_errors=True,
            http_credentials={"username": basic_user, "password": basic_pass},
            viewport={"width": 1366, "height": 768},
        )
        context.on("response", add_from_response)
        page = context.new_page()
        login_ok = False
        try:
            login_ok = solve_and_login(page)
        except Exception as exc:
            (RAW_DIR / "dynamic_login_error.txt").write_text(repr(exc), encoding="utf-8")

        for route in default_routes:
            try:
                page.goto(SITE + route, wait_until="commit", timeout=45000)
                try:
                    page.wait_for_load_state("networkidle", timeout=12000)
                except PlaywrightTimeoutError:
                    pass
                page.wait_for_timeout(1200)
            except Exception:
                continue

        # Resolve a few project ids through the current page session and visit
        # read-only detail pages. No add-to-cart, no seat pick, no checkout.
        try:
            program_ids = page.evaluate(
                """async () => {
                    const resp = await fetch('/thvendor/ticket/program/getHotProgramList.xhtml', {
                      method: 'POST',
                      credentials: 'include',
                      headers: {
                        'content-type': 'application/json',
                        'cmpappkey': 'ShanghaiCS',
                        'lang': 'en'
                      },
                      body: JSON.stringify({ showSite: 'PCrecList1' })
                    });
                    const body = await resp.json();
                    const rows = Array.isArray(body.data) ? body.data : (body.data?.list || []);
                    return rows.map((r) => r.id || r.programId).filter(Boolean).slice(0, 5);
                }"""
            )
            for pid in program_ids:
                for prefix in ("/detail/show/", "/detail/ticket/"):
                    try:
                        page.goto(SITE + f"/websitehtml/index.html#{prefix}{pid}", wait_until="commit", timeout=45000)
                        try:
                            page.wait_for_load_state("networkidle", timeout=12000)
                        except PlaywrightTimeoutError:
                            pass
                        page.wait_for_timeout(1800)
                    except Exception:
                        continue
        except Exception:
            pass

        context.close()
        browser.close()

    for rec in records.values():
        if login_ok:
            rec["notes"].append("current crawl reached logged-in state")
    return records


def merge_records(*sources: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    by_path_method: dict[tuple[str, str], str] = {}

    def find_existing(method: str, path: str) -> str | None:
        exact = endpoint_key(method, path)
        if exact in merged:
            return exact
        if method == "UNKNOWN":
            # Prefer a concrete-method record if we already have one for path.
            for (m, p), key in by_path_method.items():
                if p == path and m != "UNKNOWN":
                    return key
        else:
            unk = endpoint_key("UNKNOWN", path)
            if unk in merged:
                return unk
        return None

    for source in sources:
        for key, rec in source.items():
            method = str(rec.get("method") or "UNKNOWN").upper()
            path = str(rec.get("path") or "")
            if not path:
                continue
            existing_key = find_existing(method, path)
            if existing_key is None:
                merged_key = endpoint_key(method, path)
                merged[merged_key] = {
                    "method": method,
                    "path": path,
                    "group": infer_group(path),
                    "purpose": rec.get("purpose") or purpose_from_path(path),
                    "auth_required": rec.get("auth_required"),
                    "source": [],
                    "query_params": {},
                    "body_params": {},
                    "headers": {},
                    "response_sample": None,
                    "status_samples": [],
                    "notes": [],
                }
                by_path_method[(method, path)] = merged_key
                existing_key = merged_key
            target = merged[existing_key]
            # Upgrade UNKNOWN method to concrete method when possible.
            if target["method"] == "UNKNOWN" and method != "UNKNOWN":
                old_key = existing_key
                new_key = endpoint_key(method, path)
                target["method"] = method
                merged[new_key] = target
                del merged[old_key]
                by_path_method[(method, path)] = new_key
                existing_key = new_key
            target["source"].extend(rec.get("source", []))
            target["query_params"].update(rec.get("query_params", {}))
            target["body_params"].update(rec.get("body_params", {}))
            target["headers"].update(rec.get("headers", {}))
            if target["response_sample"] is None and rec.get("response_sample") is not None:
                target["response_sample"] = rec.get("response_sample")
            target["status_samples"].extend(rec.get("status_samples", []))
            if rec.get("auth_required") is not None:
                target["auth_required"] = rec.get("auth_required")
            if rec.get("purpose"):
                target["purpose"] = rec.get("purpose")
            target["notes"].extend([n for n in rec.get("notes", []) if n])

    for rec in merged.values():
        rec["source"] = sorted(set(rec["source"]))
        rec["status_samples"] = sorted(set(int(s) for s in rec["status_samples"] if isinstance(s, int)))
        rec["notes"] = sorted(set(n for n in rec["notes"] if n))
        if rec["auth_required"] is None:
            if rec["path"].startswith("/thvendor/member/") or rec["path"].startswith("/ucenter/rest/getLogonInfo"):
                rec["auth_required"] = True
            else:
                rec["auth_required"] = False
        rec["purpose"] = purpose_from_path(rec["path"], rec.get("purpose", ""))

    sampled_paths = {
        rec["path"]
        for rec in merged.values()
        if "current_playwright_crawl" in rec["source"] or "legacy_anticket_har" in rec["source"]
    }
    pruned: dict[str, dict[str, Any]] = {}
    for key, rec in merged.items():
        static_only = set(rec["source"]).issubset({"current_spa_static", "current_spa_static_template"})
        no_observed_shape = (
            not rec["status_samples"]
            and rec["response_sample"] is None
            and not rec["query_params"]
            and not rec["body_params"]
            and not rec["headers"]
        )
        if rec["path"] in sampled_paths and static_only and no_observed_shape:
            continue
        pruned[key] = rec
    return dict(sorted(pruned.items(), key=lambda item: (item[1]["group"], item[1]["path"], item[1]["method"])))


def write_inventory_csv(records: dict[str, dict[str, Any]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "method",
                "path",
                "group",
                "purpose",
                "auth_required",
                "query_params",
                "body_params",
                "headers",
                "response_keys",
                "status_samples",
                "source",
            ],
        )
        writer.writeheader()
        for rec in records.values():
            sample = rec.get("response_sample")
            if isinstance(sample, dict):
                response_keys = ",".join(sample.keys())
            elif isinstance(sample, list) and sample and isinstance(sample[0], dict):
                response_keys = "list:" + ",".join(sample[0].keys())
            else:
                response_keys = ""
            writer.writerow(
                {
                    "method": rec["method"],
                    "path": rec["path"],
                    "group": rec["group"],
                    "purpose": rec["purpose"],
                    "auth_required": rec["auth_required"],
                    "query_params": json.dumps(rec["query_params"], ensure_ascii=False),
                    "body_params": json.dumps(rec["body_params"], ensure_ascii=False),
                    "headers": json.dumps(rec["headers"], ensure_ascii=False),
                    "response_keys": response_keys,
                    "status_samples": ",".join(map(str, rec["status_samples"])),
                    "source": ",".join(rec["source"]),
                }
            )


def json_block(value: Any) -> str:
    if value in ({}, [], None):
        return "`无样例 / 未抓到`"
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) > 2500:
        text = text[:2500] + "\n...<truncated>"
    return f"```json\n{text}\n```"


def write_markdown(records: dict[str, dict[str, Any]], path: Path) -> None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records.values():
        groups[rec["group"]].append(rec)

    lines: list[str] = []
    lines.append("# 西九官网性能测试 API 文档")
    lines.append("")
    lines.append(f"- 生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 目标站点: `{SITE}{INDEX_PATH}#/`")
    lines.append("- 用途: JMeter 单接口压测与串联 scenario 压测设计")
    lines.append("- 安全处理: 输出已脱敏 Cookie、Session、Token、密码、验证码、邮箱、手机号等敏感值")
    lines.append("")
    lines.append("## 覆盖来源")
    lines.append("")
    lines.append("- `current_spa_static`: 当前官网前端包静态扫描")
    lines.append("- `current_playwright_crawl`: 当前官网真实浏览器登录态/未登录态页面抓包")
    lines.append("- `legacy_anticket_har`: 既有 anticket HAR，包含历史下单/取消链路样例")
    lines.append("- `local_wk_endpoints_registry`: `D:\\Workspace\\west-kowloon` 内现有接口登记")
    lines.append("")
    lines.append("## JMeter 通用约定")
    lines.append("")
    lines.append("- 公共 Header: `cmpappkey=ShanghaiCS`, `lang=en`, `Accept=application/json, text/plain, */*`。")
    lines.append("- 外层 Basic Auth: 官网入口需要 Basic Auth，JMeter 需配置 HTTP Authorization Manager。不要把真实密码提交到仓库。")
    lines.append("- 登录验证码: `/ucenter/rest/pcLoginByPass.xhtml` 依赖图片验证码，不适合直接做高并发登录压测；建议使用预置 session、测试专用免验证码登录或压测白名单。")
    lines.append("- 业务断言: 不只看 HTTP 200；优先断言 JSON 中 `errcode=0000`、`success=true`，列表接口再断言 `data` 或 `resultList` 非空。")
    lines.append("- 下单链路: 单接口压测可做查询类接口；创建订单接口必须串联取消接口，并控制数据量、库存和并发，避免未支付订单堆积。")
    lines.append("")
    lines.append("## API 总览")
    lines.append("")
    lines.append("| 分组 | 方法 | 路径 | 登录态 | 用途 |")
    lines.append("|---|---:|---|---|---|")
    for rec in records.values():
        lines.append(
            f"| {rec['group']} | `{rec['method']}` | `{rec['path']}` | {rec['auth_required']} | {rec['purpose']} |"
        )
    lines.append("")

    for group, rows in groups.items():
        lines.append(f"## {group}")
        lines.append("")
        for rec in rows:
            lines.append(f"### `{rec['method']} {rec['path']}`")
            lines.append("")
            lines.append(f"- 用途: {rec['purpose']}")
            lines.append(f"- 是否需要登录态: `{rec['auth_required']}`")
            lines.append(f"- 证据来源: `{', '.join(rec['source'])}`")
            if rec["status_samples"]:
                lines.append(f"- 抓到的 HTTP 状态: `{', '.join(map(str, rec['status_samples']))}`")
            if rec["headers"]:
                lines.append("- Header / 相关请求头样例:")
                lines.append(json_block(rec["headers"]))
            lines.append("- Query 入参:")
            lines.append(json_block(rec["query_params"]))
            lines.append("- Body 入参:")
            lines.append(json_block(rec["body_params"]))
            lines.append("- 出参样例:")
            lines.append(json_block(rec["response_sample"]))
            if rec["notes"]:
                lines.append("- 备注:")
                for note in rec["notes"][:5]:
                    lines.append(f"  - {note}")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_scenario_doc(path: Path) -> None:
    text = """# JMeter 场景建议

## 单接口压测优先级

1. 公共读接口: 首页配置、广告、分类、热门项目、项目详情、详情内容、场次/票种查询。
2. 登录态读接口: 会员信息、订单列表、优惠券、收藏、有效票列表。
3. 写接口低并发验证: 收藏、购物车初始化、创建订单、取消订单。
4. 不建议直接高并发: 验证码登录、账号注销、支付参数、支付网关、座位类抢同一座位。

## Scenario 1: 首页浏览

`getDisplayConfig -> getNewAdList -> getCategoryList -> getHotProgramList -> getProgramById -> getProgramContentInfo`

用途: 验证匿名浏览、首页和项目详情吞吐。

JMeter 关联:
- 从 `getHotProgramList` 提取 `programId` / `id`
- 传给 `getProgramById` 和 `getProgramContentInfo`

## Scenario 2: 非座位票下单后取消

`getProgramById -> listBydate -> tickettype/list -> show/order/create -> show/order/cancelOrder -> getMemberOrderList(status=cancel)`

用途: 第一优先级端到端压测链路，历史 HAR 和自动化都证明比座位票更稳定。

JMeter 关联:
- `getProgramById` 提取 `programKey`
- `listBydate` 提取 `showId`、`sessionKey`
- `tickettype/list` 提取 `ticketTypeId`、`ticketType`
- `show/order/create` 请求头生成唯一 `orderkey`
- `show/order/create` 响应提取 `tradeNo`
- `cancelOrder` 使用 `tradeNo`

控制点:
- 每个创建订单线程必须执行取消订单
- 断言 `errcode=0000` 和 `success=true`
- 压测前准备足够库存，避免库存不足被误判为性能问题

## Scenario 3: 座位票查询链路

`scheduleDateListWithSellOut -> listScheduleByDate -> getScheduleInfo -> getSchedulePrices -> getAvailableSeats2 -> getSpecialSeatOverlay -> seatplan JSON`

用途: 座位图查询、价格和库存查询压测。

控制点:
- 查询链路可压；创建座位订单 `order/create2` 不建议高并发抢同一座位
- 若要压创建，必须准备大量可售座位并做座位数据参数化
- `getAvailableSeats2` 返回或参与生成的 `orderKey` 需要传给 `order/create2` 的 `orderkey` Header

## Scenario 4: 会员中心读取

`getLogonInfo -> getMemberInfo -> getPersonalInfo -> getMemberOrderList -> getMemberCouponsByStatus -> listFavorites`

用途: 登录态读接口压测。

控制点:
- 避免每个线程都走验证码登录
- 建议预置 Cookie/session 或测试专用免验证码登录
- 每个线程使用独立账号或独立 session，避免服务端 session 互相覆盖
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    env = load_env_file(ENV_PATH)
    basic_user = os.environ.get("WK_BASIC_AUTH_USER") or env.get("WK_BASIC_AUTH_USER")
    basic_pass = os.environ.get("WK_BASIC_AUTH_PASS") or env.get("WK_BASIC_AUTH_PASS")
    site_user = os.environ.get("WK_SITE_USER") or os.environ.get("TA_WEBSITE_USERNAME")
    site_pass = os.environ.get("WK_SITE_PASS") or os.environ.get("TA_WEBSITE_PASSWORD")
    if not basic_user or not basic_pass:
        print("missing Basic Auth config", file=sys.stderr)
        return 2
    if not site_user or not site_pass:
        print("missing site login config", file=sys.stderr)
        return 2

    session = make_session(basic_user, basic_pass)

    print("[1/5] static SPA discovery")
    static_records, routes = static_discovery(session)
    (RAW_DIR / "static_routes.json").write_text(json.dumps(routes, ensure_ascii=False, indent=2), encoding="utf-8")
    (RAW_DIR / "static_records.json").write_text(
        json.dumps(static_records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"      static endpoints: {len(static_records)}")

    print("[2/5] local registry")
    registry_records = load_registry()
    print(f"      registry endpoints: {len(registry_records)}")

    print("[3/5] legacy HAR")
    har_records = parse_har(LEGACY_HAR_PATH, "legacy_anticket_har")
    print(f"      legacy HAR endpoints: {len(har_records)}")

    print("[4/5] logged-in browser crawl")
    dynamic_records = dynamic_crawl(basic_user, basic_pass, site_user, site_pass)
    (RAW_DIR / "dynamic_records_redacted.json").write_text(
        json.dumps(dynamic_records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"      dynamic endpoints: {len(dynamic_records)}")

    print("[5/5] merge + write docs")
    records = merge_records(registry_records, static_records, har_records, dynamic_records)
    (RAW_DIR / "api_samples.redacted.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_inventory_csv(records, BASE_DIR / "api_inventory.csv")
    write_markdown(records, BASE_DIR / "api_documentation.md")
    write_scenario_doc(BASE_DIR / "scenario_flows.md")

    readme = f"""# 西九官网性能测试 API 资料包

生成日期: {datetime.now(timezone.utc).isoformat(timespec='seconds')}

主要文件:
- `api_documentation.md`: 面向 JMeter 的接口文档，含入参、出参、认证、断言建议
- `api_inventory.csv`: 接口清单，适合筛选/导入
- `scenario_flows.md`: 单接口与串联压测场景建议
- `raw/api_samples.redacted.json`: 脱敏后的结构化样例
- `scripts/collect_api_inventory.py`: 本次采集脚本

注意:
- 本目录不保存真实站内密码、验证码、Cookie、Session 或 Token。
- 验证码登录不适合直接高并发压测；JMeter 应使用预置 session、免验证码测试登录或压测白名单。
- 写接口压测前需要和业务确认数据隔离、库存准备和清理规则。
"""
    (BASE_DIR / "README.md").write_text(readme, encoding="utf-8")
    print(f"      merged endpoints: {len(records)}")
    print(f"      output: {BASE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
