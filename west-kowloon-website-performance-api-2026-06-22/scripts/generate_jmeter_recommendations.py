from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from jmeter_classifier import enrich_record


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = BASE_DIR / "raw" / "api_samples.redacted.json"
JMETER_DIR = BASE_DIR / "jmeter"


CSV_FIELDS = [
    "load_test_level",
    "jmeter_scope",
    "risk_level",
    "verification_status",
    "method",
    "path",
    "group",
    "purpose",
    "auth_required",
    "source",
    "recommendation_reason",
    "query_params",
    "body_params",
    "headers",
    "response_keys",
]


SCENARIO_STEPS: list[dict[str, str]] = [
    {
        "scenario": "home_browse",
        "step": "1",
        "method": "GET",
        "path": "/thvendor/companyBaseInfo/getDisplayConfig.xhtml",
        "extract": "",
        "use": "站点配置入口",
        "assertion": "HTTP 200; errcode=0000 when JSON has errcode",
    },
    {
        "scenario": "home_browse",
        "step": "2",
        "method": "POST",
        "path": "/thvendor/ad/getNewAdList.xhtml",
        "extract": "",
        "use": "首页广告/轮播",
        "assertion": "HTTP 200; data exists",
    },
    {
        "scenario": "home_browse",
        "step": "3",
        "method": "POST",
        "path": "/thvendor/program/getCategoryList.xhtml",
        "extract": "categoryIds if needed",
        "use": "项目分类",
        "assertion": "HTTP 200; data exists",
    },
    {
        "scenario": "home_browse",
        "step": "4",
        "method": "POST",
        "path": "/thvendor/ticket/program/getHotProgramList.xhtml",
        "extract": "programId/id",
        "use": "为详情页提供 programId",
        "assertion": "HTTP 200; data list not empty",
    },
    {
        "scenario": "show_order_create_cancel",
        "step": "1",
        "method": "GET",
        "path": "/thvendor/ticket/program/getProgramById.xhtml",
        "extract": "programKey",
        "use": "输入 programId，提取 programKey",
        "assertion": "errcode=0000; data.programKey exists",
    },
    {
        "scenario": "show_order_create_cancel",
        "step": "2",
        "method": "GET",
        "path": "/thvendor/member/show/listBydate.xhtml",
        "extract": "showId/id, sessionKey",
        "use": "输入 programKey/programId，选可售场次",
        "assertion": "errcode=0000; data list not empty",
    },
    {
        "scenario": "show_order_create_cancel",
        "step": "3",
        "method": "GET",
        "path": "/thvendor/member/show/tickettype/list.xhtml",
        "extract": "ticketTypeId/id, ticketType",
        "use": "输入 showId/sessionKey/programKey，选可售票种",
        "assertion": "errcode=0000; data list not empty",
    },
    {
        "scenario": "show_order_create_cancel",
        "step": "4",
        "method": "POST",
        "path": "/thvendor/member/show/order/create.xhtml",
        "extract": "tradeNo",
        "use": "生成唯一 orderkey header，创建非座位票未支付订单",
        "assertion": "errcode=0000; success=true; data.tradeNo exists",
    },
    {
        "scenario": "show_order_create_cancel",
        "step": "5",
        "method": "GET",
        "path": "/thvendor/member/show/order/cancelOrder.xhtml",
        "extract": "",
        "use": "使用 tradeNo 立即取消订单",
        "assertion": "errcode=0000; success=true",
    },
    {
        "scenario": "member_read",
        "step": "1",
        "method": "POST",
        "path": "/ucenter/rest/getLogonInfo.xhtml",
        "extract": "member id",
        "use": "验证预置登录态有效",
        "assertion": "errcode=0000; data exists",
    },
    {
        "scenario": "member_read",
        "step": "2",
        "method": "GET",
        "path": "/thvendor/member/info/getMemberInfo.xhtml",
        "extract": "",
        "use": "会员核心信息",
        "assertion": "errcode=0000; data exists",
    },
    {
        "scenario": "member_read",
        "step": "3",
        "method": "GET",
        "path": "/thvendor/member/order/getMemberOrderList.xhtml",
        "extract": "",
        "use": "订单列表读取",
        "assertion": "errcode=0000; data.resultList exists",
    },
    {
        "scenario": "seat_query",
        "step": "1",
        "method": "GET",
        "path": "/thvendor/member/ticket/scheduleDateListWithSellOut.xhtml",
        "extract": "date",
        "use": "座位类场次日期",
        "assertion": "errcode=0000; data exists",
    },
    {
        "scenario": "seat_query",
        "step": "2",
        "method": "POST",
        "path": "/thvendor/member/ticket/listScheduleByDate.xhtml",
        "extract": "scheduleId",
        "use": "按日期查询座位类场次",
        "assertion": "errcode=0000; data exists",
    },
    {
        "scenario": "seat_query",
        "step": "3",
        "method": "POST",
        "path": "/thvendor/member/ticket/getSchedulePrices.xhtml",
        "extract": "ticketPriceId",
        "use": "查询票价",
        "assertion": "errcode=0000; data exists",
    },
    {
        "scenario": "seat_query",
        "step": "4",
        "method": "POST",
        "path": "/thvendor/member/ticket/getAvailableSeats2.xhtml",
        "extract": "available seat, orderKey",
        "use": "查询座位图库存；不建议高并发创建同一座位订单",
        "assertion": "errcode=0000; data exists",
    },
]


def response_keys(sample: Any) -> str:
    if isinstance(sample, dict):
        return ",".join(sample.keys())
    if isinstance(sample, list) and sample and isinstance(sample[0], dict):
        return "list:" + ",".join(sample[0].keys())
    return ""


def row_for(rec: dict[str, Any]) -> dict[str, str]:
    return {
        "load_test_level": str(rec.get("load_test_level") or ""),
        "jmeter_scope": str(rec.get("jmeter_scope") or ""),
        "risk_level": str(rec.get("risk_level") or ""),
        "verification_status": str(rec.get("verification_status") or ""),
        "method": str(rec.get("method") or ""),
        "path": str(rec.get("path") or ""),
        "group": str(rec.get("group") or ""),
        "purpose": str(rec.get("purpose") or ""),
        "auth_required": str(rec.get("auth_required")),
        "source": ",".join(rec.get("source") or []),
        "recommendation_reason": str(rec.get("recommendation_reason") or ""),
        "query_params": json.dumps(rec.get("query_params") or {}, ensure_ascii=False),
        "body_params": json.dumps(rec.get("body_params") or {}, ensure_ascii=False),
        "headers": json.dumps(rec.get("headers") or {}, ensure_ascii=False),
        "response_keys": response_keys(rec.get("response_sample")),
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str] = CSV_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    records = [enrich_record(rec) for rec in raw.values()]

    matrix_rows = [row_for(rec) for rec in records]
    single_rows = [
        row_for(rec)
        for rec in records
        if rec["jmeter_scope"] == "single_api" and rec["risk_level"] == "low"
    ]
    excluded_rows = [
        row_for(rec)
        for rec in records
        if rec["jmeter_scope"] == "exclude" or rec["risk_level"] == "high"
    ]

    scenario_fields = [
        "scenario",
        "step",
        "method",
        "path",
        "load_test_level",
        "risk_level",
        "extract",
        "use",
        "assertion",
        "source",
    ]
    by_key = {(rec["method"], rec["path"]): rec for rec in records}
    scenario_rows: list[dict[str, str]] = []
    for step in SCENARIO_STEPS:
        rec = by_key.get((step["method"], step["path"]))
        scenario_rows.append(
            {
                **step,
                "load_test_level": str(rec.get("load_test_level") if rec else "Smoke First"),
                "risk_level": str(rec.get("risk_level") if rec else "medium"),
                "source": ",".join(rec.get("source") or []) if rec else "",
            }
        )

    write_csv(BASE_DIR / "api_inventory_jmeter.csv", matrix_rows)
    write_csv(JMETER_DIR / "jmeter_single_api_candidates.csv", single_rows)
    write_csv(JMETER_DIR / "jmeter_excluded_risky_apis.csv", excluded_rows)
    write_csv(JMETER_DIR / "jmeter_scenario_candidates.csv", scenario_rows, scenario_fields)

    summary = {
        "total": len(records),
        "single_api_candidates": len(single_rows),
        "scenario_steps": len(scenario_rows),
        "excluded_risky_apis": len(excluded_rows),
        "levels": {},
    }
    for rec in records:
        summary["levels"][rec["load_test_level"]] = summary["levels"].get(rec["load_test_level"], 0) + 1
    (JMETER_DIR / "jmeter_recommendation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
