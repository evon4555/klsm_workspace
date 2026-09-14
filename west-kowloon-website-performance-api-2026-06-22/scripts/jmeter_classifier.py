from __future__ import annotations

from typing import Any


SIDE_EFFECT_WORDS = (
    "create",
    "save",
    "update",
    "cancel",
    "delete",
    "remove",
    "clear",
    "pay",
    "refund",
    "bind",
    "upload",
    "active",
    "transfer",
    "accept",
    "send",
    "change",
    "confirm",
    "use",
    "add",
)

DO_NOT_LOAD_WORDS = (
    "captcha",
    "login",
    "logout",
    "payment",
    "cybersource",
    "refund",
    "clearMember",
    "certification",
    "commonUpload",
    "prepareUpload",
    "getUpHeadToken",
    "uploadToken",
    "bindWxUserInfo",
    "createAndLogin",
    "sendActive",
    "sendCode",
    "dynamicCode",
    "transfer/accept",
    "transfer/start",
    "头像",
    "上传",
)

SAFE_READ_WORDS = (
    "get",
    "list",
    "query",
    "detail",
    "info",
    "content",
    "category",
    "stadium",
    "countdown",
    "schedule",
    "tickettype",
    "displayconfig",
)

SCENARIO_PATHS = {
    "/thvendor/ticket/program/getProgramById.xhtml",
    "/thvendor/member/show/listBydate.xhtml",
    "/thvendor/member/show/tickettype/list.xhtml",
    "/thvendor/member/show/order/create.xhtml",
    "/thvendor/member/show/order/cancelOrder.xhtml",
    "/thvendor/member/order/getMemberOrderList.xhtml",
    "/thvendor/member/ticket/scheduleDateListWithSellOut.xhtml",
    "/thvendor/member/ticket/listScheduleByDate.xhtml",
    "/thvendor/member/ticket/getScheduleInfo.xhtml",
    "/thvendor/member/ticket/getSchedulePrices.xhtml",
    "/thvendor/member/ticket/getAvailableSeats2.xhtml",
}


def has_observed_sample(rec: dict[str, Any]) -> bool:
    source = rec.get("source") or []
    return "current_playwright_crawl" in source or "legacy_anticket_har" in source


def is_static_only(rec: dict[str, Any]) -> bool:
    source = set(rec.get("source") or [])
    return bool(source) and source.issubset({"current_spa_static", "current_spa_static_template"})


def is_side_effect_like(rec: dict[str, Any]) -> bool:
    path = str(rec.get("path") or "").lower()
    purpose = str(rec.get("purpose") or "").lower()
    method = str(rec.get("method") or "").upper()
    text = f"{path} {purpose}"
    return method not in {"GET", "HEAD"} or any(word.lower() in text for word in SIDE_EFFECT_WORDS)


def is_do_not_load(rec: dict[str, Any]) -> bool:
    path = str(rec.get("path") or "")
    lower_path = path.lower()
    purpose = str(rec.get("purpose") or "").lower()
    text = f"{lower_path} {purpose}"
    if any(word.lower() in text for word in DO_NOT_LOAD_WORDS):
        return True
    if "/order/pay" in lower_path or lower_path.endswith("/pay.xhtml") or "payorder" in lower_path:
        return True
    if "refundorder" in lower_path or "/refund/" in lower_path:
        return True
    return False


def looks_read_only(rec: dict[str, Any]) -> bool:
    path = str(rec.get("path") or "").lower()
    purpose = str(rec.get("purpose") or "").lower()
    method = str(rec.get("method") or "").upper()
    text = f"{path} {purpose}"
    if method == "HEAD":
        return True
    if method == "GET" and not is_side_effect_like(rec):
        return True
    return any(word in text for word in SAFE_READ_WORDS) and not is_side_effect_like(rec)


def classify_record(rec: dict[str, Any]) -> dict[str, Any]:
    observed = has_observed_sample(rec)
    static_only = is_static_only(rec)
    side_effect = is_side_effect_like(rec)
    do_not_load = is_do_not_load(rec)
    path = str(rec.get("path") or "")

    if do_not_load:
        return {
            "load_test_level": "Do Not Load Test",
            "jmeter_scope": "exclude",
            "risk_level": "high",
            "verification_status": "observed" if observed else "static_only" if static_only else "registered",
            "default_visible": False,
            "recommendation_reason": "验证码、登录、支付、退款、上传、实名/注销或账号绑定类接口，不建议直接压测。",
        }

    if observed and path in SCENARIO_PATHS:
        return {
            "load_test_level": "Scenario Ready",
            "jmeter_scope": "scenario",
            "risk_level": "medium" if side_effect else "low",
            "verification_status": "observed",
            "default_visible": True,
            "recommendation_reason": "已有真实抓包/HAR 样例，可纳入串联场景；写接口必须带清理或取消步骤。",
        }

    if observed and looks_read_only(rec):
        return {
            "load_test_level": "Ready",
            "jmeter_scope": "single_api",
            "risk_level": "low",
            "verification_status": "observed",
            "default_visible": True,
            "recommendation_reason": "已有真实抓包样例，且看起来是查询类接口，适合作为单接口压测候选。",
        }

    if observed and side_effect:
        return {
            "load_test_level": "Scenario Ready",
            "jmeter_scope": "scenario",
            "risk_level": "medium",
            "verification_status": "observed",
            "default_visible": True,
            "recommendation_reason": "已有真实样例但有副作用，应放在受控业务场景中执行。",
        }

    if static_only and side_effect:
        return {
            "load_test_level": "Do Not Load Test",
            "jmeter_scope": "exclude",
            "risk_level": "high",
            "verification_status": "static_only",
            "default_visible": False,
            "recommendation_reason": "仅静态发现且像写操作/副作用接口，先人工确认业务影响。",
        }

    return {
        "load_test_level": "Smoke First",
        "jmeter_scope": "smoke_first",
        "risk_level": "low" if looks_read_only(rec) else "medium",
        "verification_status": "static_only" if static_only else "registered",
        "default_visible": looks_read_only(rec),
        "recommendation_reason": "缺少真实响应样例；先 1 线程 smoke 验证入参、响应和断言，再纳入压测。",
    }


def enrich_record(rec: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(rec)
    enriched.update(classify_record(rec))
    return enriched
