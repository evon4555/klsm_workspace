from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from jmeter_classifier import enrich_record


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = BASE_DIR / "raw" / "api_samples.redacted.json"
SCENARIO_PATH = BASE_DIR / "scenario_flows.md"
HTML_PATH = BASE_DIR / "api_browser.html"
OPENAPI_PATH = BASE_DIR / "openapi_like.json"
DEPENDENCY_PATH = BASE_DIR / "api_dependency_map.json"
OPENAPI_QUALITY_PATH = BASE_DIR / "openapi_quality_report.json"


DEPENDENCY_FLOWS: list[dict[str, Any]] = [
    {
        "id": "home_browse",
        "title": "首页浏览链路",
        "risk": "low",
        "goal": "匿名浏览、首页配置、项目列表和项目详情查询压测。",
        "jmeter_notes": [
            "适合单接口和轻量串联压测。",
            "从热门项目列表提取 programId 后进入项目详情。",
        ],
        "steps": [
            {
                "step": 1,
                "method": "GET",
                "path": "/thvendor/companyBaseInfo/getDisplayConfig.xhtml",
                "extract": [],
                "uses": [],
                "assert": ["HTTP 200", "data exists when JSON"],
            },
            {
                "step": 2,
                "method": "POST",
                "path": "/thvendor/ad/getNewAdList.xhtml",
                "extract": [],
                "uses": [],
                "assert": ["HTTP 200", "data exists"],
            },
            {
                "step": 3,
                "method": "POST",
                "path": "/thvendor/ticket/program/getHotProgramList.xhtml",
                "extract": ["programId / id"],
                "uses": [],
                "assert": ["errcode=0000", "data list not empty"],
            },
            {
                "step": 4,
                "method": "GET",
                "path": "/thvendor/ticket/program/getProgramById.xhtml",
                "extract": ["programKey"],
                "uses": ["programId"],
                "assert": ["errcode=0000", "data.programKey exists"],
            },
            {
                "step": 5,
                "method": "GET",
                "path": "/thvendor/program/content/getProgramContentInfo.xhtml",
                "extract": [],
                "uses": ["programId"],
                "assert": ["errcode=0000", "data exists"],
            },
        ],
    },
    {
        "id": "show_order_create_cancel",
        "title": "非座位票下单后取消",
        "risk": "medium",
        "goal": "第一优先级端到端压测链路；创建订单后必须立即取消。",
        "jmeter_notes": [
            "每个线程生成唯一 orderkey header。",
            "create 响应提取 tradeNo，cancelOrder 必须执行。",
            "适合少量账号和可售库存准备后的受控压测。",
        ],
        "steps": [
            {
                "step": 1,
                "method": "GET",
                "path": "/thvendor/ticket/program/getProgramById.xhtml",
                "extract": ["programKey"],
                "uses": ["programId"],
                "assert": ["errcode=0000", "data.programKey exists"],
            },
            {
                "step": 2,
                "method": "GET",
                "path": "/thvendor/member/show/listBydate.xhtml",
                "extract": ["showId / id", "sessionKey"],
                "uses": ["programId", "programKey"],
                "assert": ["errcode=0000", "data list not empty"],
            },
            {
                "step": 3,
                "method": "GET",
                "path": "/thvendor/member/show/tickettype/list.xhtml",
                "extract": ["ticketTypeId / id", "ticketType"],
                "uses": ["showId", "sessionKey", "programKey"],
                "assert": ["errcode=0000", "data list not empty"],
            },
            {
                "step": 4,
                "method": "POST",
                "path": "/thvendor/member/show/order/create.xhtml",
                "extract": ["tradeNo"],
                "uses": ["showId", "ticketTypeId", "ticketType", "quantity", "orderkey"],
                "assert": ["errcode=0000", "success=true", "data.tradeNo exists"],
            },
            {
                "step": 5,
                "method": "GET",
                "path": "/thvendor/member/show/order/cancelOrder.xhtml",
                "extract": [],
                "uses": ["tradeNo"],
                "assert": ["errcode=0000", "success=true"],
            },
            {
                "step": 6,
                "method": "GET",
                "path": "/thvendor/member/order/getMemberOrderList.xhtml",
                "extract": [],
                "uses": ["tradeNo", "status=cancel"],
                "assert": ["errcode=0000", "cancel list contains tradeNo when validating correctness"],
            },
        ],
    },
    {
        "id": "seat_query",
        "title": "座位票查询链路",
        "risk": "low",
        "goal": "压测座位类日期、场次、票价和库存查询，不直接抢座。",
        "jmeter_notes": [
            "查询链路可压；创建座位订单前必须准备大量座位数据。",
            "getAvailableSeats2 提供座位和 orderKey 相关数据。",
        ],
        "steps": [
            {
                "step": 1,
                "method": "GET",
                "path": "/thvendor/member/ticket/scheduleDateListWithSellOut.xhtml",
                "extract": ["date"],
                "uses": ["programId"],
                "assert": ["errcode=0000", "data exists"],
            },
            {
                "step": 2,
                "method": "POST",
                "path": "/thvendor/member/ticket/listScheduleByDate.xhtml",
                "extract": ["scheduleId"],
                "uses": ["programId", "date"],
                "assert": ["errcode=0000", "data list not empty"],
            },
            {
                "step": 3,
                "method": "POST",
                "path": "/thvendor/member/ticket/getScheduleInfo.xhtml",
                "extract": ["venueId / schedule metadata"],
                "uses": ["scheduleId"],
                "assert": ["errcode=0000", "data exists"],
            },
            {
                "step": 4,
                "method": "POST",
                "path": "/thvendor/member/ticket/getSchedulePrices.xhtml",
                "extract": ["ticketPriceId"],
                "uses": ["scheduleId"],
                "assert": ["errcode=0000", "data list not empty"],
            },
            {
                "step": 5,
                "method": "POST",
                "path": "/thvendor/member/ticket/getAvailableSeats2.xhtml",
                "extract": ["seat row/col", "venueAreaId", "orderKey"],
                "uses": ["scheduleId", "ticketPriceId"],
                "assert": ["errcode=0000", "data exists"],
            },
        ],
    },
    {
        "id": "member_read",
        "title": "会员中心读取链路",
        "risk": "low",
        "goal": "验证预置登录态和会员中心读接口吞吐。",
        "jmeter_notes": [
            "不要每个线程走验证码登录。",
            "使用预置 session、免验证码测试登录或压测白名单。",
        ],
        "steps": [
            {
                "step": 1,
                "method": "POST",
                "path": "/ucenter/rest/getLogonInfo.xhtml",
                "extract": ["memberId / id"],
                "uses": ["Cookie/session"],
                "assert": ["errcode=0000", "data exists"],
            },
            {
                "step": 2,
                "method": "GET",
                "path": "/thvendor/member/info/getMemberInfo.xhtml",
                "extract": [],
                "uses": ["Cookie/session"],
                "assert": ["errcode=0000", "data exists"],
            },
            {
                "step": 3,
                "method": "GET",
                "path": "/thvendor/member/info/getPersonalInfo.xhtml",
                "extract": [],
                "uses": ["Cookie/session"],
                "assert": ["errcode=0000", "data exists"],
            },
            {
                "step": 4,
                "method": "GET",
                "path": "/thvendor/member/order/getMemberOrderList.xhtml",
                "extract": [],
                "uses": ["Cookie/session", "pageNo", "pageSize", "status"],
                "assert": ["errcode=0000", "data.resultList exists"],
            },
        ],
    },
]


def infer_schema(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {
            "type": "object",
            "properties": {str(k): infer_schema(v) for k, v in value.items()},
            "example": value,
        }
    if isinstance(value, list):
        item = value[0] if value else {}
        return {"type": "array", "items": infer_schema(item), "example": value}
    if isinstance(value, bool):
        return {"type": "boolean", "example": value}
    if isinstance(value, int):
        return {"type": "integer", "example": value}
    if isinstance(value, float):
        return {"type": "number", "example": value}
    if value is None:
        return {"nullable": True, "example": None}
    return {"type": "string", "example": str(value)}


def param_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return "string"


def evidence_status(rec: dict[str, Any]) -> str:
    source = set(rec.get("source") or [])
    if "current_playwright_crawl" in source or "legacy_anticket_har" in source:
        return "observed"
    if source and source.issubset({"current_spa_static", "current_spa_static_template"}):
        return "staticOnly"
    if "local_wk_endpoints_registry" in source:
        return "registeredOnly"
    return "unknown"


def schema_status(rec: dict[str, Any]) -> str:
    if rec.get("response_sample") is not None:
        return "observedResponseSample"
    if rec.get("body_params") or rec.get("query_params") or rec.get("headers"):
        return "requestShapeOnly"
    return "schemaUnknown"


def openapi_quality(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_evidence: Counter[str] = Counter()
    by_schema: Counter[str] = Counter()
    by_level: Counter[str] = Counter()
    missing_response_examples: list[dict[str, str]] = []
    static_only_operations: list[dict[str, str]] = []
    for rec in records:
        ev = evidence_status(rec)
        schema = schema_status(rec)
        by_evidence[ev] += 1
        by_schema[schema] += 1
        by_level[str(rec.get("load_test_level") or "Unclassified")] += 1
        row = {
            "method": str(rec.get("method") or ""),
            "path": str(rec.get("path") or ""),
            "load_test_level": str(rec.get("load_test_level") or ""),
            "risk_level": str(rec.get("risk_level") or ""),
        }
        if schema == "schemaUnknown":
            missing_response_examples.append(row)
        if ev == "staticOnly":
            static_only_operations.append(row)
    return {
        "total_operations": len(records),
        "by_evidence_status": dict(sorted(by_evidence.items())),
        "by_schema_status": dict(sorted(by_schema.items())),
        "by_load_test_level": dict(sorted(by_level.items())),
        "schema_unknown_operations": missing_response_examples,
        "static_only_operations": static_only_operations,
    }


def build_openapi(records: list[dict[str, Any]]) -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for rec in records:
        method = str(rec["method"]).lower()
        if method not in {"get", "post", "put", "delete", "patch", "head", "options"}:
            continue
        path_item = paths.setdefault(rec["path"], {})
        parameters = []
        for name, value in (rec.get("query_params") or {}).items():
            parameters.append(
                {
                    "name": name,
                    "in": "query",
                    "required": False,
                    "schema": {"type": param_type(value)},
                    "example": value,
                }
            )
        for name, value in (rec.get("headers") or {}).items():
            parameters.append(
                {
                    "name": name,
                    "in": "header",
                    "required": name.lower() in {"cmpappkey", "lang", "orderkey"},
                    "schema": {"type": "string"},
                    "example": value,
                }
            )
        operation: dict[str, Any] = {
            "summary": rec.get("purpose") or rec["path"],
            "tags": [rec.get("group") or "default"],
            "x-auth-required": rec.get("auth_required"),
            "x-source": rec.get("source", []),
            "x-evidence-status": evidence_status(rec),
            "x-schema-status": schema_status(rec),
            "x-load-test-level": rec.get("load_test_level"),
            "x-jmeter-scope": rec.get("jmeter_scope"),
            "x-risk-level": rec.get("risk_level"),
            "x-verification-status": rec.get("verification_status"),
            "x-recommendation-reason": rec.get("recommendation_reason"),
            "parameters": parameters,
            "responses": {
                "200": {
                    "description": "Observed or expected successful response",
                    "content": {
                        "application/json": {
                            "schema": infer_schema(rec.get("response_sample")),
                            "example": rec.get("response_sample"),
                        }
                    },
                }
            },
        }
        if rec.get("body_params"):
            operation["requestBody"] = {
                "required": method in {"post", "put", "patch"},
                "content": {
                    "application/json": {
                        "schema": infer_schema(rec.get("body_params")),
                        "example": rec.get("body_params"),
                    },
                    "application/x-www-form-urlencoded": {
                        "schema": infer_schema(rec.get("body_params")),
                        "example": rec.get("body_params"),
                    },
                },
            }
        path_item[method] = operation
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "West Kowloon Website API Inventory",
            "version": "2026-06-22",
            "description": "Generated from current SPA static analysis, Playwright crawl, local registry, and redacted HAR evidence.",
        },
        "servers": [{"url": "https://anticket.lengliwh.com"}],
        "paths": paths,
    }


def markdown_to_blocks(md: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    current = {"title": "Overview", "body": ""}
    for line in md.splitlines():
        if line.startswith("## "):
            if current["body"].strip():
                blocks.append(current)
            current = {"title": line[3:].strip(), "body": ""}
        elif not line.startswith("# "):
            current["body"] += line + "\n"
    if current["body"].strip():
        blocks.append(current)
    return blocks


def write_html(
    records: list[dict[str, Any]],
    scenario_blocks: list[dict[str, str]],
    dependency_flows: list[dict[str, Any]],
) -> None:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    groups = Counter(r.get("group") or "other" for r in records)
    methods = Counter(r.get("method") or "UNKNOWN" for r in records)
    levels = Counter(r.get("load_test_level") or "Unclassified" for r in records)
    sampled = sum(
        1
        for r in records
        if "current_playwright_crawl" in r.get("source", []) or "legacy_anticket_har" in r.get("source", [])
    )
    static_only = sum(
        1
        for r in records
        if ("current_spa_static" in r.get("source", []) or "current_spa_static_template" in r.get("source", []))
        and "current_playwright_crawl" not in r.get("source", [])
        and "legacy_anticket_har" not in r.get("source", [])
    )
    default_visible = sum(1 for r in records if r.get("default_visible"))
    single_candidates = sum(1 for r in records if r.get("jmeter_scope") == "single_api")
    excluded = sum(1 for r in records if r.get("jmeter_scope") == "exclude")
    data_json = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")
    scenario_json = json.dumps(scenario_blocks, ensure_ascii=False).replace("</", "<\\/")
    dependency_json = json.dumps(dependency_flows, ensure_ascii=False).replace("</", "<\\/")
    group_json = json.dumps(groups, ensure_ascii=False).replace("</", "<\\/")
    method_json = json.dumps(methods, ensure_ascii=False).replace("</", "<\\/")
    level_json = json.dumps(levels, ensure_ascii=False).replace("</", "<\\/")

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>西九官网 API Browser</title>
  <style>
    :root {{
      --bg: #f6f7f8;
      --surface: #ffffff;
      --line: #d8dee5;
      --line-strong: #aeb8c4;
      --text: #17202a;
      --muted: #607080;
      --subtle: #eef2f5;
      --accent: #0f766e;
      --accent-soft: #d9f2ef;
      --blue: #2563eb;
      --green: #15803d;
      --amber: #b45309;
      --red: #b91c1c;
      --slate: #475569;
      --mono: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      --sans: Inter, "Segoe UI", Arial, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--sans);
      color: var(--text);
      background: var(--bg);
      letter-spacing: 0;
    }}
    button, input, select {{ font: inherit; }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 30;
      min-height: 64px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      padding: 12px 22px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, .94);
      backdrop-filter: blur(14px);
    }}
    .brand {{
      min-width: 250px;
    }}
    .brand h1 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.2;
      font-weight: 760;
    }}
    .brand p {{
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 12px;
    }}
    .tabs {{
      display: inline-flex;
      align-items: center;
      gap: 2px;
      padding: 3px;
      border: 1px solid var(--line);
      background: var(--subtle);
      border-radius: 8px;
    }}
    .tab {{
      border: 0;
      background: transparent;
      color: var(--muted);
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      white-space: nowrap;
    }}
    .tab.active {{
      background: var(--surface);
      color: var(--text);
      box-shadow: 0 1px 2px rgba(15, 23, 42, .08);
    }}
    .workspace {{
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr) 430px;
      min-height: calc(100vh - 64px);
    }}
    .sidebar, .inspector {{
      background: var(--surface);
      border-right: 1px solid var(--line);
      overflow: auto;
      max-height: calc(100vh - 64px);
      position: sticky;
      top: 64px;
      align-self: start;
    }}
    .inspector {{
      border-right: 0;
      border-left: 1px solid var(--line);
    }}
    .filter-section {{
      padding: 18px;
      border-bottom: 1px solid var(--line);
    }}
    .filter-title {{
      margin: 0 0 10px;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 720;
    }}
    .search {{
      width: 100%;
      border: 1px solid var(--line-strong);
      background: #fff;
      border-radius: 8px;
      padding: 10px 11px;
      outline: none;
    }}
    .search:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-soft);
    }}
    .filter-list {{
      display: grid;
      gap: 6px;
    }}
    .filter-btn {{
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border: 0;
      background: transparent;
      padding: 8px 9px;
      border-radius: 7px;
      cursor: pointer;
      color: var(--text);
      text-align: left;
    }}
    .filter-btn:hover {{ background: var(--subtle); }}
    .filter-btn.active {{
      background: var(--accent-soft);
      color: #075f58;
      font-weight: 700;
    }}
    .count {{
      font-family: var(--mono);
      font-size: 11px;
      color: var(--muted);
    }}
    .toggle-row {{
      display: flex;
      align-items: center;
      gap: 9px;
      color: var(--text);
      font-size: 13px;
      padding: 7px 0;
    }}
    .hint {{
      margin: 9px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }}
    .main {{
      min-width: 0;
      padding: 22px;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 1px;
      border: 1px solid var(--line);
      background: var(--line);
      margin-bottom: 18px;
    }}
    .metric {{
      background: var(--surface);
      padding: 15px 16px;
      min-height: 84px;
    }}
    .metric .value {{
      font-family: var(--mono);
      font-size: 26px;
      font-weight: 800;
      margin-bottom: 6px;
    }}
    .metric .label {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }}
    .toolbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin: 0 0 12px;
    }}
    .result-count {{
      color: var(--muted);
      font-size: 13px;
    }}
    .endpoint-list {{
      display: grid;
      gap: 8px;
    }}
    .endpoint-row {{
      width: 100%;
      border: 1px solid var(--line);
      background: var(--surface);
      border-radius: 8px;
      padding: 13px 14px;
      cursor: pointer;
      text-align: left;
      transition: border-color .14s ease, transform .14s ease, background .14s ease;
    }}
    .endpoint-row:hover {{
      border-color: var(--line-strong);
      transform: translateY(-1px);
    }}
    .endpoint-row.selected {{
      border-color: var(--accent);
      background: #fbfffe;
      box-shadow: inset 3px 0 0 var(--accent);
    }}
    .endpoint-head {{
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }}
    .path {{
      font-family: var(--mono);
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    .purpose {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }}
    .meta-line {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      height: 22px;
      padding: 0 7px;
      border-radius: 5px;
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 760;
      white-space: nowrap;
    }}
    .GET {{ background: #dbeafe; color: var(--blue); }}
    .POST {{ background: #dcfce7; color: var(--green); }}
    .HEAD {{ background: #e2e8f0; color: var(--slate); }}
    .UNKNOWN {{ background: #fef3c7; color: var(--amber); }}
    .auth-yes {{ background: #fee2e2; color: var(--red); }}
    .auth-no {{ background: #ecfdf5; color: var(--green); }}
    .source {{ background: #f1f5f9; color: var(--slate); }}
    .level-ready {{ background: #dcfce7; color: #166534; }}
    .level-scenario {{ background: #e0f2fe; color: #075985; }}
    .level-smoke {{ background: #fef3c7; color: #92400e; }}
    .level-exclude {{ background: #fee2e2; color: #991b1b; }}
    .risk-high {{ background: #fee2e2; color: #991b1b; }}
    .risk-medium {{ background: #fff7ed; color: #9a3412; }}
    .risk-low {{ background: #ecfdf5; color: #166534; }}
    .inspector-inner {{
      padding: 18px;
    }}
    .detail-title {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 12px;
    }}
    .detail-title h2 {{
      margin: 0;
      font-family: var(--mono);
      font-size: 16px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}
    .detail-purpose {{
      margin: 0 0 14px;
      color: var(--muted);
      line-height: 1.45;
      font-size: 13px;
    }}
    .action-row {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin: 0 0 14px;
    }}
    .small-btn {{
      border: 1px solid var(--line);
      background: var(--surface);
      border-radius: 7px;
      padding: 7px 9px;
      cursor: pointer;
      font-size: 12px;
    }}
    .small-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .section {{
      border-top: 1px solid var(--line);
      padding: 14px 0;
    }}
    .section h3 {{
      margin: 0 0 9px;
      font-size: 13px;
      color: var(--text);
    }}
    pre {{
      margin: 0;
      background: #0f172a;
      color: #e5edf6;
      border-radius: 8px;
      padding: 12px;
      overflow: auto;
      max-height: 360px;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.5;
    }}
    .empty {{
      color: var(--muted);
      background: var(--subtle);
      border: 1px dashed var(--line-strong);
      padding: 12px;
      border-radius: 8px;
      font-size: 13px;
    }}
    .scenario-view {{
      display: none;
      max-width: 1120px;
      margin: 0 auto;
    }}
    .dependency-view {{
      display: none;
      max-width: 1320px;
      margin: 0 auto;
    }}
    .scenario-view.active, .dependency-view.active, .docs-view.active {{ display: block; }}
    .docs-view {{ display: none; }}
    .scenario-grid {{
      display: grid;
      gap: 12px;
    }}
    .scenario-block {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .scenario-block h2 {{
      margin: 0 0 10px;
      font-size: 18px;
    }}
    .scenario-block pre {{
      background: #f8fafc;
      color: var(--text);
      border: 1px solid var(--line);
      max-height: none;
      white-space: pre-wrap;
    }}
    .flow-shell {{
      display: grid;
      gap: 18px;
    }}
    .flow-block {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    .flow-header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 14px;
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfd;
    }}
    .flow-header h2 {{
      margin: 0 0 6px;
      font-size: 18px;
    }}
    .flow-header p {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }}
    .flow-steps {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 0;
      border-bottom: 1px solid var(--line);
    }}
    .flow-step {{
      min-height: 260px;
      padding: 15px;
      border-right: 1px solid var(--line);
      position: relative;
    }}
    .flow-step:last-child {{ border-right: 0; }}
    .flow-step::after {{
      content: "→";
      position: absolute;
      right: -8px;
      top: 22px;
      width: 16px;
      height: 16px;
      line-height: 16px;
      text-align: center;
      color: var(--muted);
      background: var(--surface);
      font-weight: 800;
    }}
    .flow-step:last-child::after {{ content: ""; }}
    .step-index {{
      font-family: var(--mono);
      color: var(--muted);
      font-size: 11px;
      margin-bottom: 8px;
    }}
    .step-path {{
      margin: 9px 0;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }}
    .field-list {{
      display: grid;
      gap: 6px;
      margin-top: 11px;
    }}
    .field-line {{
      display: grid;
      gap: 3px;
      padding-top: 8px;
      border-top: 1px solid var(--subtle);
      font-size: 12px;
    }}
    .field-line strong {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
    }}
    .field-line span {{
      font-family: var(--mono);
      overflow-wrap: anywhere;
    }}
    .flow-notes {{
      padding: 14px 18px;
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }}
    .toast {{
      position: fixed;
      right: 18px;
      bottom: 18px;
      background: #0f172a;
      color: #fff;
      padding: 10px 12px;
      border-radius: 8px;
      opacity: 0;
      transform: translateY(8px);
      transition: opacity .18s ease, transform .18s ease;
      pointer-events: none;
      font-size: 13px;
      z-index: 60;
    }}
    .toast.show {{ opacity: 1; transform: translateY(0); }}
    mark {{
      background: #fef08a;
      padding: 0 2px;
      border-radius: 3px;
    }}
    @media (max-width: 1180px) {{
      .workspace {{ grid-template-columns: 260px minmax(0, 1fr); }}
      .inspector {{
        position: fixed;
        inset: 64px 0 0 auto;
        width: min(460px, 96vw);
        transform: translateX(100%);
        transition: transform .18s ease;
        z-index: 40;
        box-shadow: -20px 0 40px rgba(15, 23, 42, .18);
      }}
      .inspector.open {{ transform: translateX(0); }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 760px) {{
      .topbar {{ align-items: flex-start; flex-direction: column; gap: 10px; }}
      .tabs {{ width: 100%; }}
      .tab {{ flex: 1; }}
      .workspace {{ display: block; }}
      .sidebar {{
        position: static;
        max-height: none;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
      .filter-section {{ padding: 12px 16px; }}
      .main {{ padding: 16px; }}
      .summary {{ grid-template-columns: 1fr; }}
      .inspector {{ top: 0; height: 100vh; }}
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">
      <h1>西九官网 API Browser</h1>
      <p>Generated {html.escape(generated_at)} · {len(records)} endpoint records · anticket.lengliwh.com</p>
    </div>
    <nav class="tabs" aria-label="Views">
      <button class="tab active" data-tab="docs">接口</button>
      <button class="tab" data-tab="scenarios">场景</button>
      <button class="tab" data-tab="dependencies">依赖图</button>
      <button class="tab" id="downloadOpenApi">OpenAPI JSON</button>
    </nav>
  </header>

  <div class="docs-view active" id="docsView">
    <div class="workspace">
      <aside class="sidebar">
        <section class="filter-section">
          <p class="filter-title">Search</p>
          <input class="search" id="searchInput" placeholder="path / purpose / source" />
        </section>
        <section class="filter-section">
          <p class="filter-title">Group</p>
          <div class="filter-list" id="groupFilters"></div>
        </section>
        <section class="filter-section">
          <p class="filter-title">Method</p>
          <div class="filter-list" id="methodFilters"></div>
        </section>
        <section class="filter-section">
          <p class="filter-title">压测等级</p>
          <div class="filter-list" id="levelFilters"></div>
        </section>
        <section class="filter-section">
          <p class="filter-title">来源/证据</p>
          <label class="toggle-row"><input type="checkbox" id="showAll" /> 显示需验证/高风险全部接口</label>
          <label class="toggle-row"><input type="checkbox" id="sampledOnly" /> 只看有抓包样例</label>
          <label class="toggle-row"><input type="checkbox" id="authOnly" /> 只看登录态接口</label>
          <label class="toggle-row"><input type="checkbox" id="writeOnly" /> 只看写/副作用接口</label>
          <p class="hint">默认隐藏高风险或静态副作用接口；抓包样例优先，静态发现代表前端包里存在调用代码，但入参/响应可能还要二次验证。</p>
        </section>
      </aside>

      <main class="main">
        <section class="summary" aria-label="Summary">
          <div class="metric"><div class="value">{len(records)}</div><div class="label">接口记录</div></div>
          <div class="metric"><div class="value">{default_visible}</div><div class="label">默认显示，已隐藏高风险接口</div></div>
          <div class="metric"><div class="value">{single_candidates}</div><div class="label">单接口压测候选</div></div>
          <div class="metric"><div class="value">{excluded}</div><div class="label">排除/不建议直接压测</div></div>
        </section>
        <div class="toolbar">
          <div class="result-count" id="resultCount"></div>
          <button class="small-btn" id="clearFilters">清空筛选</button>
        </div>
        <section class="endpoint-list" id="endpointList"></section>
      </main>

      <aside class="inspector" id="inspector">
        <div class="inspector-inner" id="detail"></div>
      </aside>
    </div>
  </div>

  <main class="scenario-view" id="scenarioView">
    <div class="main">
      <section class="summary">
        <div class="metric"><div class="value">4</div><div class="label">建议串联场景</div></div>
        <div class="metric"><div class="value">1</div><div class="label">优先链路: 非座位票创建后取消</div></div>
        <div class="metric"><div class="value">0</div><div class="label">不保存真实凭据</div></div>
        <div class="metric"><div class="value">JMeter</div><div class="label">面向参数化与断言</div></div>
      </section>
      <section class="scenario-grid" id="scenarioGrid"></section>
    </div>
  </main>

  <main class="dependency-view" id="dependencyView">
    <div class="main">
      <section class="summary">
        <div class="metric"><div class="value">4</div><div class="label">依赖链路</div></div>
        <div class="metric"><div class="value">programKey</div><div class="label">项目详情到场次查询</div></div>
        <div class="metric"><div class="value">tradeNo</div><div class="label">下单到取消订单</div></div>
        <div class="metric"><div class="value">orderkey</div><div class="label">创建订单请求头</div></div>
      </section>
      <section class="flow-shell" id="dependencyGrid"></section>
    </div>
  </main>

  <div class="toast" id="toast">Copied</div>

  <script id="apiData" type="application/json">{data_json}</script>
  <script id="scenarioData" type="application/json">{scenario_json}</script>
  <script id="dependencyData" type="application/json">{dependency_json}</script>
  <script id="groupCounts" type="application/json">{group_json}</script>
  <script id="methodCounts" type="application/json">{method_json}</script>
  <script id="levelCounts" type="application/json">{level_json}</script>
  <script>
    const records = JSON.parse(document.getElementById('apiData').textContent);
    const scenarios = JSON.parse(document.getElementById('scenarioData').textContent);
    const dependencies = JSON.parse(document.getElementById('dependencyData').textContent);
    const groupCounts = JSON.parse(document.getElementById('groupCounts').textContent);
    const methodCounts = JSON.parse(document.getElementById('methodCounts').textContent);
    const levelCounts = JSON.parse(document.getElementById('levelCounts').textContent);
    const state = {{ group: 'all', method: 'all', level: 'all', q: '', showAll: false, sampledOnly: false, authOnly: false, writeOnly: false, selected: null }};
    const writeWords = ['create', 'save', 'update', 'cancel', 'delete', 'remove', 'pay', 'refund', 'bind', 'upload', 'order'];

    const $ = (id) => document.getElementById(id);
    const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
    const pretty = (value) => value === null || value === undefined || (typeof value === 'object' && Object.keys(value).length === 0)
      ? '<div class="empty">无样例 / 未抓到</div>'
      : '<pre>' + esc(JSON.stringify(value, null, 2)) + '</pre>';
    const hasSample = (r) => r.source.includes('current_playwright_crawl') || r.source.includes('legacy_anticket_har');
    const isWrite = (r) => r.method !== 'GET' || writeWords.some(w => r.path.toLowerCase().includes(w));

    function methodBadge(method) {{
      return `<span class="badge ${{esc(method)}}">${{esc(method)}}</span>`;
    }}
    function authBadge(auth) {{
      return `<span class="badge ${{auth ? 'auth-yes' : 'auth-no'}}">${{auth ? 'LOGIN' : 'PUBLIC'}}</span>`;
    }}
    function sourceBadges(r) {{
      return r.source.slice(0, 4).map(s => `<span class="badge source">${{esc(s.replace('current_', '').replace('_', ' '))}}</span>`).join('');
    }}
    function levelClass(level) {{
      if (level === 'Ready') return 'level-ready';
      if (level === 'Scenario Ready') return 'level-scenario';
      if (level === 'Smoke First') return 'level-smoke';
      return 'level-exclude';
    }}
    function levelBadge(r) {{
      return `<span class="badge ${{levelClass(r.load_test_level)}}">${{esc(r.load_test_level || 'Unclassified')}}</span>`;
    }}
    function riskBadge(r) {{
      return `<span class="badge risk-${{esc(r.risk_level || 'medium')}}">${{esc((r.risk_level || 'medium').toUpperCase())}}</span>`;
    }}

    function renderFilterButtons(container, entries, active, onClick) {{
      container.innerHTML = '';
      const all = document.createElement('button');
      all.className = 'filter-btn' + (active === 'all' ? ' active' : '');
      all.innerHTML = `<span>All</span><span class="count">${{records.length}}</span>`;
      all.onclick = () => onClick('all');
      container.appendChild(all);
      Object.entries(entries).sort((a,b) => a[0].localeCompare(b[0])).forEach(([name, count]) => {{
        const btn = document.createElement('button');
        btn.className = 'filter-btn' + (active === name ? ' active' : '');
        btn.innerHTML = `<span>${{esc(name)}}</span><span class="count">${{count}}</span>`;
        btn.onclick = () => onClick(name);
        container.appendChild(btn);
      }});
    }}

    function filteredRecords() {{
      const q = state.q.trim().toLowerCase();
      return records.filter(r => {{
        if (state.group !== 'all' && r.group !== state.group) return false;
        if (state.method !== 'all' && r.method !== state.method) return false;
        if (state.level !== 'all' && r.load_test_level !== state.level) return false;
        if (!state.showAll && !r.default_visible) return false;
        if (state.sampledOnly && !hasSample(r)) return false;
        if (state.authOnly && !r.auth_required) return false;
        if (state.writeOnly && !isWrite(r)) return false;
        if (!q) return true;
        return [
          r.method,
          r.path,
          r.group,
          r.purpose,
          r.load_test_level,
          r.risk_level,
          r.recommendation_reason,
          r.source.join(' ')
        ].join(' ').toLowerCase().includes(q);
      }});
    }}

    function renderList() {{
      renderFilterButtons($('groupFilters'), groupCounts, state.group, v => {{ state.group = v; renderList(); }});
      renderFilterButtons($('methodFilters'), methodCounts, state.method, v => {{ state.method = v; renderList(); }});
      renderFilterButtons($('levelFilters'), levelCounts, state.level, v => {{ state.level = v; renderList(); }});
      const rows = filteredRecords();
      $('resultCount').textContent = `${{rows.length}} / ${{records.length}} endpoints`;
      if (!state.selected || !rows.find(r => key(r) === state.selected)) {{
        state.selected = rows[0] ? key(rows[0]) : null;
      }}
      $('endpointList').innerHTML = rows.map(r => `
        <button class="endpoint-row ${{key(r) === state.selected ? 'selected' : ''}}" data-key="${{esc(key(r))}}">
          <div class="endpoint-head">${{methodBadge(r.method)}}<span class="path">${{highlight(r.path)}}</span></div>
          <p class="purpose">${{highlight(r.purpose || '')}}</p>
          <div class="meta-line">${{levelBadge(r)}}${{riskBadge(r)}}${{authBadge(r.auth_required)}}<span class="badge source">${{esc(r.group)}}</span>${{sourceBadges(r)}}</div>
        </button>
      `).join('') || '<div class="empty">没有匹配的接口</div>';
      document.querySelectorAll('.endpoint-row').forEach(btn => {{
        btn.onclick = () => {{
          state.selected = btn.dataset.key;
          renderList();
          renderDetail();
          if (window.innerWidth <= 1180) $('inspector').classList.add('open');
        }};
      }});
      renderDetail();
    }}

    function highlight(text) {{
      const q = state.q.trim();
      if (!q) return esc(text);
      const idx = String(text).toLowerCase().indexOf(q.toLowerCase());
      if (idx < 0) return esc(text);
      return esc(String(text).slice(0, idx)) + '<mark>' + esc(String(text).slice(idx, idx + q.length)) + '</mark>' + esc(String(text).slice(idx + q.length));
    }}

    function key(r) {{ return `${{r.method}} ${{r.path}}`; }}
    function selectedRecord() {{ return records.find(r => key(r) === state.selected) || filteredRecords()[0]; }}
    function curl(r) {{
      const headers = Object.entries(r.headers || {{}}).map(([k,v]) => ` -H "${{k}}: ${{String(v).replaceAll('"', '\\\\\\"')}}"`).join('');
      const query = Object.keys(r.query_params || {{}}).length ? '?' + new URLSearchParams(r.query_params).toString() : '';
      const data = Object.keys(r.body_params || {{}}).length ? ` --data '${{JSON.stringify(r.body_params)}}'` : '';
      return `curl -X ${{r.method}} "https://anticket.lengliwh.com${{r.path}}${{query}}"${{headers}}${{data}}`;
    }}

    function renderDetail() {{
      const r = selectedRecord();
      if (!r) {{
        $('detail').innerHTML = '<div class="empty">请选择接口</div>';
        return;
      }}
      $('detail').innerHTML = `
        <div class="detail-title">${{methodBadge(r.method)}}<h2>${{esc(r.path)}}</h2></div>
        <p class="detail-purpose">${{esc(r.purpose || '')}}</p>
        <div class="action-row">
          <button class="small-btn" data-copy="path">复制路径</button>
          <button class="small-btn" data-copy="curl">复制 cURL</button>
          <button class="small-btn" id="closeInspector">关闭</button>
        </div>
        <div class="meta-line">${{levelBadge(r)}}${{riskBadge(r)}}${{authBadge(r.auth_required)}}<span class="badge source">${{esc(r.group)}}</span>${{sourceBadges(r)}}</div>
        <section class="section"><h3>压测建议</h3><pre>${{esc(r.recommendation_reason || '')}}</pre></section>
        <section class="section"><h3>Query 入参</h3>${{pretty(r.query_params)}}</section>
        <section class="section"><h3>Body 入参</h3>${{pretty(r.body_params)}}</section>
        <section class="section"><h3>Headers</h3>${{pretty(r.headers)}}</section>
        <section class="section"><h3>Response 样例</h3>${{pretty(r.response_sample)}}</section>
        <section class="section"><h3>JMeter 断言提示</h3><pre>${{esc(assertionHint(r))}}</pre></section>
        <section class="section"><h3>Notes</h3>${{pretty({{status_samples: r.status_samples, source: r.source, notes: r.notes}})}}</section>
      `;
      document.querySelectorAll('[data-copy]').forEach(btn => {{
        btn.onclick = () => copy(btn.dataset.copy === 'curl' ? curl(r) : r.path);
      }});
      const close = $('closeInspector');
      if (close) close.onclick = () => $('inspector').classList.remove('open');
    }}

    function assertionHint(r) {{
      const lines = [];
      lines.push(`HTTP ${{r.status_samples && r.status_samples.length ? r.status_samples.join(' / ') : '200'}}`);
      if (r.response_sample && typeof r.response_sample === 'object') {{
        if ('errcode' in r.response_sample) lines.push('JSON Assertion: $.errcode == 0000');
        if ('success' in r.response_sample) lines.push('JSON Assertion: $.success == true');
        if ('data' in r.response_sample) lines.push('JSON Assertion: $.data exists');
      }}
      if (!hasSample(r)) lines.push('静态发现接口: 先用 1 线程 smoke 验证入参和响应，再纳入压测。');
      if (r.path.toLowerCase().includes('order/create')) lines.push('订单创建后必须串联取消接口，避免未支付订单堆积。');
      if (r.path.toLowerCase().includes('captcha') || r.path.toLowerCase().includes('login')) lines.push('验证码/登录接口不建议直接高并发压测。');
      return lines.join('\\n');
    }}

    function renderScenarios() {{
      $('scenarioGrid').innerHTML = scenarios.map(s => `
        <article class="scenario-block">
          <h2>${{esc(s.title)}}</h2>
          <pre>${{esc(s.body.trim())}}</pre>
        </article>
      `).join('');
    }}

    function listText(items) {{
      if (!items || !items.length) return '<span>无</span>';
      return items.map(item => `<span>${{esc(item)}}</span>`).join('');
    }}

    function renderDependencies() {{
      $('dependencyGrid').innerHTML = dependencies.map(flow => `
        <article class="flow-block">
          <header class="flow-header">
            <div>
              <h2>${{esc(flow.title)}}</h2>
              <p>${{esc(flow.goal)}}</p>
            </div>
            <span class="badge risk-${{esc(flow.risk)}}">${{esc(flow.risk.toUpperCase())}}</span>
          </header>
          <div class="flow-steps">
            ${{flow.steps.map(step => `
              <section class="flow-step">
                <div class="step-index">STEP ${{step.step}}</div>
                <div>${{methodBadge(step.method)}}</div>
                <div class="step-path">${{esc(step.path)}}</div>
                <div class="field-list">
                  <div class="field-line"><strong>Uses</strong>${{listText(step.uses)}}</div>
                  <div class="field-line"><strong>Extract</strong>${{listText(step.extract)}}</div>
                  <div class="field-line"><strong>Assert</strong>${{listText(step.assert)}}</div>
                </div>
              </section>
            `).join('')}}
          </div>
          <div class="flow-notes">
            ${{flow.jmeter_notes.map(note => `<div>${{esc(note)}}</div>`).join('')}}
          </div>
        </article>
      `).join('');
    }}

    function copy(text) {{
      navigator.clipboard?.writeText(text).then(() => toast('已复制')).catch(() => toast('复制失败'));
    }}
    function toast(text) {{
      $('toast').textContent = text;
      $('toast').classList.add('show');
      setTimeout(() => $('toast').classList.remove('show'), 1200);
    }}

    $('searchInput').oninput = e => {{ state.q = e.target.value; renderList(); }};
    $('showAll').onchange = e => {{ state.showAll = e.target.checked; renderList(); }};
    $('sampledOnly').onchange = e => {{ state.sampledOnly = e.target.checked; renderList(); }};
    $('authOnly').onchange = e => {{ state.authOnly = e.target.checked; renderList(); }};
    $('writeOnly').onchange = e => {{ state.writeOnly = e.target.checked; renderList(); }};
    $('clearFilters').onclick = () => {{
      Object.assign(state, {{ group: 'all', method: 'all', level: 'all', q: '', showAll: false, sampledOnly: false, authOnly: false, writeOnly: false }});
      $('searchInput').value = '';
      $('showAll').checked = false;
      $('sampledOnly').checked = false;
      $('authOnly').checked = false;
      $('writeOnly').checked = false;
      renderList();
    }};
    document.querySelectorAll('.tab').forEach(tab => {{
      tab.onclick = () => {{
        if (tab.id === 'downloadOpenApi') {{
          window.location.href = 'openapi_like.json';
          return;
        }}
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const isDocs = tab.dataset.tab === 'docs';
        const isDependencies = tab.dataset.tab === 'dependencies';
        $('docsView').classList.toggle('active', isDocs);
        $('scenarioView').classList.toggle('active', tab.dataset.tab === 'scenarios');
        $('dependencyView').classList.toggle('active', isDependencies);
      }};
    }});

    renderScenarios();
    renderDependencies();
    renderList();
  </script>
</body>
</html>
"""
    HTML_PATH.write_text(html_text, encoding="utf-8")


def main() -> int:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    records = [enrich_record(rec) for rec in raw.values()]
    openapi = build_openapi(records)
    OPENAPI_PATH.write_text(json.dumps(openapi, ensure_ascii=False, indent=2), encoding="utf-8")
    OPENAPI_QUALITY_PATH.write_text(
        json.dumps(openapi_quality(records), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    DEPENDENCY_PATH.write_text(
        json.dumps(DEPENDENCY_FLOWS, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    scenario_md = SCENARIO_PATH.read_text(encoding="utf-8") if SCENARIO_PATH.exists() else ""
    write_html(records, markdown_to_blocks(scenario_md), DEPENDENCY_FLOWS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
