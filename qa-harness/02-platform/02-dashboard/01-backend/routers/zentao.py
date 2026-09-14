"""ZenTao dashboard, task-matrix, and testcase-generation routes."""

import json
import time as _time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from story_case_generator import (
    STORY_RULES,
    generate_login_registration_core_workbook,
    generate_story_workbook,
    generated_file_path,
)


router = APIRouter()
ZENTAO_BASE = "https://lengliwh.chandao.net"
ZENTAO_DEFAULT_PRODUCT_ID = 146


def configure_router(
    *,
    zt_session,
    zentao_token,
    zentao_refresh_configured,
    token_status_provider,
    project_config,
    project_key,
    as_float,
):
    global _zt_session, _zentao_token, _zentao_refresh_configured
    global _token_status_provider, _project_config, _project_key, _as_float
    _zt_session = zt_session
    _zentao_token = zentao_token
    _zentao_refresh_configured = zentao_refresh_configured
    _token_status_provider = token_status_provider
    _project_config = project_config
    _project_key = project_key
    _as_float = as_float
    return router



# ===========================================================================
# ZenTao Integration dashboard — aggregate endpoint
#
# Single endpoint that returns everything the ZenTaoDashboardPage needs:
# iterations, requirements, modules, QA throughput, bug heatmap, automation
# trend. Cached 5 min to avoid hammering the SaaS.
#
# Token: read from ZENTAO_API_V2_TOKEN (Windows user env or process env)
# Base:  https://lengliwh.chandao.net/api.php/v1
# Default product: 146 (西九 / West Kowloon)
# ===========================================================================

_ZT_DASHBOARD_CACHE: dict[str, tuple[float, dict]] = {}
_ZT_DASHBOARD_TTL = 300.0  # 5 minutes
_ZT_QA_TASK_MATRIX_CACHE: dict[str, tuple[float, dict]] = {}
_ZT_QA_TASK_MATRIX_TTL = 1800.0  # 30 minutes; this scans all executions.
_ZT_LAST_ERROR: Optional[str] = None


def _zt_get(
    path: str,
    token: Optional[str] = None,
    params: Optional[dict] = None,
    critical: bool = False,
) -> Optional[dict]:
    """Wrapper for ZenTao REST GET. Returns parsed JSON or None on failure."""
    global _ZT_LAST_ERROR
    try:
        url = f"{ZENTAO_BASE}/api.php/v1{path}"
        active_token = token or _zentao_token()
        if not active_token:
            if critical:
                _ZT_LAST_ERROR = "ZenTao API token unavailable and auto-refresh is not configured."
            return None
        resp = _zt_session().get(url, headers={"Token": active_token}, params=params, timeout=15)
        if resp.status_code == 401:
            refreshed = _zentao_token(force_refresh=True)
            if refreshed:
                resp = _zt_session().get(
                    url,
                    headers={"Token": refreshed},
                    params=params,
                    timeout=15,
                )
        if resp.status_code != 200:
            if critical:
                if resp.status_code == 401:
                    if _zentao_refresh_configured():
                        _ZT_LAST_ERROR = "ZenTao API token unauthorized; backend auto-refresh was attempted but did not recover."
                    else:
                        _ZT_LAST_ERROR = "ZenTao API token unauthorized and backend auto-refresh is not configured. Set ZENTAO_ACCOUNT/ZENTAO_PASSWORD."
                else:
                    _ZT_LAST_ERROR = f"ZenTao GET {path} HTTP {resp.status_code}: {resp.text[:200]}"
            return None
        return resp.json()
    except Exception as exc:                                       # noqa: BLE001
        if critical:
            _ZT_LAST_ERROR = f"ZenTao GET {path} failed: {type(exc).__name__}: {exc}"
        return None


def _zt_post_json(
    path: str,
    body: dict,
    token: Optional[str] = None,
    timeout: int = 30,
) -> tuple[int, Optional[dict], str]:
    """ZenTao POST with the same dashboard-owned token retry policy."""
    url = f"{ZENTAO_BASE}/api.php/v1{path}"
    active_token = token or _zentao_token()
    if not active_token:
        return 0, None, "ZenTao API token unavailable and auto-refresh is not configured."

    headers = {"Token": active_token, "Content-Type": "application/json"}
    try:
        resp = _zt_session().post(url, headers=headers, json=body, timeout=timeout)
        if resp.status_code == 401:
            refreshed = _zentao_token(force_refresh=True)
            if refreshed:
                resp = _zt_session().post(
                    url,
                    headers={"Token": refreshed, "Content-Type": "application/json"},
                    json=body,
                    timeout=timeout,
                )
        text = resp.text
        try:
            data = resp.json()
        except Exception:                                     # noqa: BLE001
            data = None
        return resp.status_code, data, text
    except Exception as exc:                                  # noqa: BLE001
        return 0, None, f"{type(exc).__name__}: {exc}"


@router.get("/api/zentao/auth-status")
def zentao_auth_status():
    """Non-secret ZenTao auth diagnostics for dashboard operation."""
    status = _token_status_provider()
    token = _zentao_token()
    return {
        "base": ZENTAO_BASE,
        "autoRefreshConfigured": _zentao_refresh_configured(),
        "hasToken": bool(token),
        "tokenSource": status.get("tokenSource", "unset"),
        "lastRefreshAt": status.get("lastRefreshAt"),
        "lastRefreshError": status.get("lastRefreshError"),
    }


@router.get("/api/zentao/products")
def zentao_products(refresh: bool = False):
    """Return selectable ZenTao products for the integration page."""
    token = _zentao_token()
    if not token:
        return {"products": [], "error": "ZENTAO_API_V2_TOKEN not set"}

    global _ZT_LAST_ERROR
    _ZT_LAST_ERROR = None
    resp = _zt_get("/products", token, {"limit": 500}, critical=True)
    products = (resp or {}).get("products") or (resp or {}).get("data") or []
    if not products and _ZT_LAST_ERROR:
        products = [{"id": ZENTAO_DEFAULT_PRODUCT_ID, "name": "西九", "code": "", "status": "unknown"}]
    return {
        "products": [
            {
                "id": int(p.get("id")),
                "name": p.get("name") or f"Product {p.get('id')}",
                "code": p.get("code") or "",
                "status": p.get("status") or "",
            }
            for p in products
            if p.get("id") is not None
        ],
        "error": _ZT_LAST_ERROR,
        "cached": False,
    }


class StoryTestcaseGenerateRequest(BaseModel):
    """Body for POST /api/zentao/story/{story_id}/testcases/generate."""
    execution_id: int = 614
    include_login_registration_core: bool = False


@router.post("/api/zentao/story/{story_id}/testcases/generate")
def zentao_generate_story_testcases(
    story_id: int,
    req: StoryTestcaseGenerateRequest,
):
    """Generate a West Kowloon style xlsx test-case file for one ZenTao story.

    The current implementation uses local story mappings for the West Kowloon
    split stories 4161 and 4266. The workbook is written to the project
    story-splits folder and returned with a dashboard download URL.
    """
    try:
        result = generate_story_workbook(story_id)
        result["executionId"] = req.execution_id
        result["downloadUrl"] = f"/api/zentao/generated-testcases/{result['filename']}"
        if req.include_login_registration_core:
            core = generate_login_registration_core_workbook()
            core["downloadUrl"] = f"/api/zentao/generated-testcases/{core['filename']}"
            result["loginRegistrationCore"] = core
        return result
    except Exception as exc:                                      # noqa: BLE001
        return {"error": str(exc), "storyId": story_id}


@router.get("/api/zentao/generated-testcases/{filename}")
def zentao_download_generated_testcases(filename: str):
    """Download a generated story-split xlsx file."""
    try:
        path = generated_file_path(filename)
    except Exception as exc:                                      # noqa: BLE001
        return {"error": str(exc)}
    if not path.exists():
        return {"error": f"generated file not found: {filename}"}
    return FileResponse(
        str(path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


_STORY_STAGE_ZH = {
    "wait":      "待评审",
    "planned":   "已评审",
    "projected": "已评审",
    "developing":"进行中",
    "developed": "进行中",
    "testing":   "进行中",
    "tested":    "已完成",
    "verified":  "已完成",
    "released":  "已发布",
    "closed":    "已发布",
}


def _story_stage_zh(stage: Optional[str]) -> str:
    return _STORY_STAGE_ZH.get((stage or "").lower(), "进行中")


def _name_of(field) -> str:
    """ZenTao API sometimes returns user/module fields as a dict and sometimes
    as a plain string. Normalise to a display name."""
    if isinstance(field, dict):
        return field.get("realname") or field.get("name") or field.get("account") or ""
    if isinstance(field, str):
        return field
    return ""


def _is_auto(case: dict) -> bool:
    """Heuristic for "this test case has automation". ZenTao stores it in
    different fields across versions — accept any truthy variant."""
    v = case.get("auto") or case.get("automation") or case.get("scriptStatus")
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v != 0
    if isinstance(v, str):
        return v.lower() in ("auto", "yes", "y", "true", "1", "automated")
    return False


def _safe_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except Exception:                                              # noqa: BLE001
        return None


TASK_STATUS_META = {
    "wait":    {"label": "未开始", "color": "#8c8c8c"},
    "doing":   {"label": "进行中", "color": "#faad14"},
    "pause":   {"label": "暂停", "color": "#722ed1"},
    "done":    {"label": "已完成", "color": "#52c41a"},
    "closed":  {"label": "已关闭", "color": "#1677ff"},
    "cancel":  {"label": "已取消", "color": "#bfbfbf"},
    "changed": {"label": "已变更", "color": "#13c2c2"},
}
TASK_STATUS_ORDER = ["wait", "doing", "pause", "done", "closed", "cancel", "changed"]
EXECUTION_STATUS_SCAN = ["doing", "wait", "suspended", "closed"]
TESTTASK_STATUS_MAP = {
    "wait": "wait",
    "doing": "doing",
    "done": "closed",
    "closed": "closed",
    "suspended": "pause",
}
STATUS_TEXT_MAP = {
    "未开始": "wait",
    "进行中": "doing",
    "已完成": "done",
    "已关闭": "closed",
    "暂停": "pause",
    "已取消": "cancel",
    "已变更": "changed",
}


def _account_of(field) -> str:
    if isinstance(field, dict):
        return field.get("account") or ""
    return ""


def _qa_owner_index(qa_users: list[dict]) -> dict[str, str]:
    index: dict[str, str] = {}
    for u in qa_users:
        owner = _name_of(u.get("realname")) or str(u.get("account") or "").strip()
        if not owner:
            continue
        for candidate in (u.get("account"), u.get("realname"), owner):
            key = str(candidate or "").strip().casefold()
            if key:
                index[key] = owner
    return index


def _task_owner_candidates(task: dict) -> list[str]:
    candidates: list[str] = []
    for field_name in ("assignedTo", "owner"):
        field = task.get(field_name)
        if isinstance(field, dict):
            candidates.extend([
                field.get("account"),
                field.get("realname"),
                field.get("name"),
            ])
        elif isinstance(field, str):
            candidates.append(field)
    candidates.extend([
        task.get("assignedToRealName"),
        task.get("ownerRealName"),
    ])
    # ZenTao closes-out: closed tasks have assignedTo=null and
    # assignedToRealName="Closed"; the QA who actually did the work moves to
    # finishedBy. Without this fallback, every closed task drops off the
    # owner's count (e.g. 魏梦 was showing 32 instead of ~648).
    assigned = task.get("assignedTo")
    assigned_label = str(task.get("assignedToRealName") or "").strip().lower()
    if assigned in (None, "") or assigned_label == "closed":
        fb = task.get("finishedBy")
        if isinstance(fb, dict):
            candidates.extend([
                fb.get("account"),
                fb.get("realname"),
                fb.get("name"),
            ])
        elif isinstance(fb, str):
            candidates.append(fb)
    return [
        str(v).strip() for v in candidates
        if str(v or "").strip() and str(v).strip().lower() != "closed"
    ]


def _resolve_task_owner(task: dict, qa_index: dict[str, str]) -> str:
    for candidate in _task_owner_candidates(task):
        owner = qa_index.get(candidate.casefold())
        if owner:
            return owner
    return ""


def _is_qa_task(task: dict) -> bool:
    """Filter for tasks that count as QA work in the task-count matrix.

    ZenTao's `/executions/{id}/tasks` returns ALL task types (devel/test/ui/
    affair/study/design/...). The 任务数量分布 widget only wants test work.
    But the `type` field is mislabelled often enough — many entries with
    type='devel' are clearly tests by name (e.g. '【测试】...') — so we also
    accept tasks whose name starts with the 【测试】 marker.
    """
    if task.get("type") == "test":
        return True
    name = task.get("name") or ""
    return "【测试】" in name


def _task_status_key(task: dict, source: str) -> str:
    raw_status = str(task.get("rawStatus") or task.get("status") or "").strip().lower()
    if source == "testtask":
        raw_status = TESTTASK_STATUS_MAP.get(raw_status, raw_status)
    if raw_status in TASK_STATUS_META:
        return raw_status
    status_text = str(task.get("status") or "").strip()
    return STATUS_TEXT_MAP.get(status_text, "other")


def _build_task_matrix_from_tasks(tasks: list[dict], qa_users: list[dict], fetched_executions: int,
                                 fetched_testtasks: int = 0,
                                 testtasks: Optional[list[dict]] = None) -> dict:
    from collections import defaultdict as _dd

    qa_index = _qa_owner_index(qa_users)
    status_seen: set[str] = set()
    tasks_by_owner: dict[str, dict[str, list[dict]]] = _dd(lambda: _dd(list))
    seen_task_ids = set()

    for t in tasks:
        task_id = t.get("id")
        task_key = f"task:{task_id}" if task_id else None
        if task_key and task_key in seen_task_ids:
            continue
        if task_key:
            seen_task_ids.add(task_key)

        if not _is_qa_task(t):
            continue
        owner = _resolve_task_owner(t, qa_index)
        if not owner:
            continue
        status_key = _task_status_key(t, "task")
        status_seen.add(status_key)
        raw_status = str(t.get("rawStatus") or t.get("status") or "").strip() or "其它"
        account = _account_of(t.get("assignedTo")) or str(t.get("assignedToRealName") or "").strip()
        ex_id = t.get("execution") or t.get("executionID") or t.get("executionId")
        raw_story = t.get("story")
        if isinstance(raw_story, dict):
            raw_story = raw_story.get("id")
        try:
            story_id = int(raw_story or 0)
        except (TypeError, ValueError):
            story_id = 0
        tasks_by_owner[owner][status_key].append({
            "id": task_id,
            "name": t.get("name") or "",
            "status": status_key,
            "statusLabel": TASK_STATUS_META.get(status_key, {"label": raw_status or "其它"})["label"],
            "owner": owner,
            "account": account,
            "date": (
                t.get("realStarted") or t.get("assignedDate") or t.get("openedDate")
                or t.get("finishedDate") or t.get("closedDate") or ""
            ),
            "executionId": ex_id,
            "executionName": t.get("executionName") or "",
            "storyId": story_id or None,
            "url": f"{ZENTAO_BASE}/task-view-{task_id}.html" if task_id else "",
        })

    # Testtasks (测试单) are a separate ZenTao entity, not 任务 — they used to be
    # added to this matrix and inflated QA counts by ~80 across the team. The
    # widget's title is "QA 任务数量 · 人员 × 状态", so we restrict to /tasks
    # only. `testtasks` arg kept (callers count them for the summary banner)
    # but no longer contributes rows.

    columns = [
        {
            "key": key,
            "label": TASK_STATUS_META[key]["label"],
            "color": TASK_STATUS_META[key]["color"],
        }
        for key in TASK_STATUS_ORDER
    ]
    if "other" in status_seen:
        columns.append({"key": "other", "label": "其它", "color": "#595959"})
    if not columns:
        columns = [
            {"key": key, "label": TASK_STATUS_META[key]["label"], "color": TASK_STATUS_META[key]["color"]}
            for key in ["wait", "doing", "done", "closed"]
        ]

    def _row_total(owner: str) -> int:
        return sum(len(tasks_by_owner[owner].get(col["key"], [])) for col in columns)

    owners = sorted(
        {(_name_of(u.get("realname")) or str(u.get("realname") or u.get("account") or "")) for u in qa_users},
        key=lambda owner: (-_row_total(owner), owner),
    )
    matrix = []
    matrix_tasks = []
    for owner in owners:
        by_status = tasks_by_owner.get(owner, {})
        matrix.append([len(by_status.get(col["key"], [])) for col in columns])
        matrix_tasks.append([by_status.get(col["key"], []) for col in columns])

    by_status_totals = {
        col["key"]: sum(row[idx] for row in matrix)
        for idx, col in enumerate(columns)
    }
    return {
        "scope": "all-executions",
        "peopleType": "qa",
        "statusColumns": columns,
        "ownerRows": owners,
        "matrix": matrix,
        "matrixTasks": matrix_tasks,
        "summary": {
            "total": sum(by_status_totals.values()),
            "people": len(owners),
            "qaWithTasks": sum(1 for owner in owners if _row_total(owner) > 0),
            "byStatus": by_status_totals,
            "fetchedExecutions": fetched_executions,
            "fetchedTesttasks": fetched_testtasks,
            "sourceTaskCount": len(tasks),
        },
        "fetchedAt": datetime.utcnow().isoformat(),
    }


def _collect_testtasks() -> list[dict]:
    from concurrent.futures import ThreadPoolExecutor

    first = _zt_get("/testtasks", _zentao_token(), {"page": 1}, critical=True) or {}
    rows = first.get("testtasks") or []
    total = int(first.get("total") or len(rows) or 0)
    limit = int(first.get("limit") or 20)
    if total <= len(rows) or limit <= 0:
        return rows

    pages = (total + limit - 1) // limit

    def _fetch_page(page: int) -> list[dict]:
        resp = _zt_get("/testtasks", _zentao_token(), {"page": page}, critical=True) or {}
        return resp.get("testtasks") or []

    with ThreadPoolExecutor(max_workers=min(4, max(1, pages - 1))) as pool:
        for page_rows in pool.map(_fetch_page, range(2, pages + 1)):
            rows.extend(page_rows)
    return rows


def _fetch_qa_task_matrix(
    refresh: bool = False,
    execution_id: int = 0,
    project: str = "west-kowloon",
) -> dict:
    global _ZT_QA_TASK_MATRIX_CACHE
    project_key = _project_key(project)
    cache_key = f"{project_key}:execution:{execution_id or 'all'}"
    now = _time.time()
    cached = _ZT_QA_TASK_MATRIX_CACHE.get(cache_key)
    if not refresh and cached and (now - cached[0]) < _ZT_QA_TASK_MATRIX_TTL:
        payload = dict(cached[1])
        payload["cached"] = True
        return payload

    token = _zentao_token()
    if not token:
        return {"error": "ZENTAO_API_V2_TOKEN not set", "cached": False}

    users_resp = _zt_get("/users", token, {"limit": 500}, critical=True) or {}
    users = users_resp.get("users") or users_resp.get("data") or []
    qa_users = [
        u for u in users
        if (u.get("role") or "").lower() == "qa" and u.get("account")
    ]

    executions_by_id: dict[int, dict] = {}
    if execution_id:
        executions_by_id[int(execution_id)] = {"id": int(execution_id), "name": f"Execution {execution_id}"}
    else:
        for status in EXECUTION_STATUS_SCAN:
            resp = _zt_get("/executions", token, {"limit": 500, "status": status}, critical=True) or {}
            for ex in (resp.get("data") or resp.get("executions") or []):
                try:
                    ex_id = int(ex.get("id") or 0)
                except Exception:                                  # noqa: BLE001
                    ex_id = 0
                if ex_id:
                    executions_by_id[ex_id] = ex

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _fetch_tasks(ex_id: int) -> tuple[int, Optional[list[dict]]]:
        # Per-call retry — ZenTao SaaS occasionally drops requests under load
        # (no HTTP error, just a None from _zt_get). Without retry we'd silently
        # under-count by ~10-30 tasks across the 688-execution scan.
        for attempt in range(3):
            resp = _zt_get(f"/executions/{ex_id}/tasks", token, {"limit": 500})
            if resp is not None:
                rows = resp.get("data") or resp.get("tasks") or []
                ex_name = executions_by_id.get(ex_id, {}).get("name") or ""
                for row in rows:
                    row.setdefault("execution", ex_id)
                    row.setdefault("executionName", ex_name)
                return ex_id, rows
            _time.sleep(0.4 * (attempt + 1))
        return ex_id, None  # persistent failure

    testtasks = _collect_testtasks()
    all_tasks: list[dict] = []
    failed_exec_ids: list[int] = []
    # 8 workers, not 32 — ZenTao SaaS rate-limits aggressive concurrency, and
    # the silent failures cost more than the wall-clock savings.
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_fetch_tasks, ex_id) for ex_id in executions_by_id]
        for fut in as_completed(futures):
            try:
                ex_id, rows = fut.result()
            except Exception:                                  # noqa: BLE001
                continue
            if rows is None:
                failed_exec_ids.append(ex_id)
            else:
                all_tasks.extend(rows)

    payload = _build_task_matrix_from_tasks(
        all_tasks,
        qa_users,
        len(executions_by_id),
        fetched_testtasks=len(testtasks),
        testtasks=testtasks,
    )
    payload["project"] = project_key
    payload["scope"] = f"execution:{execution_id}" if execution_id else "all-executions"
    payload["cached"] = False
    payload["summary"]["sourceTestTaskCount"] = len(testtasks)
    payload["summary"]["failedExecCount"] = len(failed_exec_ids)
    if failed_exec_ids:
        payload["summary"]["failedExecSample"] = sorted(failed_exec_ids)[:10]
    _ZT_QA_TASK_MATRIX_CACHE[cache_key] = (now, payload)
    return payload


@router.get("/api/zentao/qa-task-matrix")
def zentao_qa_task_matrix(
    refresh: bool = False,
    project: str = "west-kowloon",
    execution_id: int = 0,
):
    """QA task count matrix scoped to the selected dashboard project."""
    cfg = _project_config(project)
    project_key = cfg["key"]
    effective_execution_id = execution_id or int(cfg.get("zentaoExecutionId") or 0)
    if not effective_execution_id:
        payload = _build_task_matrix_from_tasks([], [], 0, fetched_testtasks=0, testtasks=[])
        payload.update({
            "project": project_key,
            "scope": "unmapped-project",
            "cached": False,
            "_note": f"No ZenTao execution is mapped for project {project_key}.",
        })
        return payload
    return _fetch_qa_task_matrix(
        refresh=refresh,
        execution_id=effective_execution_id,
        project=project_key,
    )


_ZT_EXEC_DETAIL_CACHE: dict[int, tuple[float, dict]] = {}


def _build_iter_detail(ex: dict, token: str,
                       sub_responses: Optional[dict] = None) -> dict:
    """Compute one execution's full detail from its sub-resources.

    If `sub_responses` is provided (during a batched dashboard build), reuse
    them — otherwise spawn 4 parallel ZenTao calls. Returns
    `{summary, requirements}` ready to merge into the dashboard payload."""
    ex_id = ex.get("id")
    # Fetch sub-resources (stories, bugs, testcases) + testtasks
    # (testtasks is a flat list across all executions — we filter client-side)
    if sub_responses is None:
        from concurrent.futures import ThreadPoolExecutor
        def _f(resource):
            if resource == "testtasks":
                # flat /testtasks endpoint, filter by execution after
                return resource, _zt_get("/testtasks", token, {"limit": 500}) or {}
            limit = 500 if resource in ("bugs", "testcases", "tasks") else 200
            return resource, _zt_get(f"/executions/{ex_id}/{resource}", token,
                                      {"limit": limit}) or {}
        with ThreadPoolExecutor(max_workers=5) as pool:
            sub_responses = dict(pool.map(_f, ["stories", "bugs", "testcases", "testtasks", "tasks"]))

    sr_stories = sub_responses.get("stories", {}) if isinstance(sub_responses, dict) else {}
    sr_bugs = sub_responses.get("bugs", {}) if isinstance(sub_responses, dict) else {}
    sr_cases = sub_responses.get("testcases", {}) if isinstance(sub_responses, dict) else {}
    sr_tasks = sub_responses.get("testtasks", {}) if isinstance(sub_responses, dict) else {}
    sr_devtasks = sub_responses.get("tasks", {}) if isinstance(sub_responses, dict) else {}

    stories = sr_stories.get("data") or sr_stories.get("stories") or []
    bugs = sr_bugs.get("data") or sr_bugs.get("bugs") or []
    cases = sr_cases.get("data") or sr_cases.get("cases") or []
    all_testtasks = sr_tasks.get("data") or sr_tasks.get("testtasks") or []
    dev_tasks = sr_devtasks.get("data") or sr_devtasks.get("tasks") or []

    from collections import Counter as _Counter
    from collections import defaultdict as _dd

    def _story_id(raw) -> int:
        if isinstance(raw, dict):
            raw = raw.get("id")
        try:
            return int(raw or 0)
        except (TypeError, ValueError):
            return 0

    def _is_test_task(t: dict) -> bool:
        name = (t.get("name") or "").lower()
        return "测试" in name or "test" in name

    def _task_owner(t: dict) -> str:
        owner = _name_of(t.get("assignedTo")).strip()
        # ZenTao may surface pseudo assignees for closed/pooled work. They
        # are not real people and should not be counted as current ownership.
        return "" if owner.lower() in {"closed", "null", "none"} else owner

    def _is_current_task(t: dict) -> bool:
        status = (t.get("status") or "").lower()
        return status not in {"done", "closed", "cancel", "cancelled"}

    def _task_date(t: dict) -> str:
        return (t.get("realStarted") or t.get("assignedDate")
                or t.get("openedDate") or t.get("finishedDate") or "")

    def _task_sort_key(t: dict):
        return _task_date(t)

    def _task_evidence(t: dict, source: str) -> dict:
        return {
            "source": source,
            "id": t.get("id"),
            "name": t.get("name") or "",
            "status": t.get("status") or "",
            "owner": _task_owner(t),
            "date": _task_date(t),
        }

    task_status_meta = {
        "wait":    {"label": "未开始", "color": "#8c8c8c"},
        "doing":   {"label": "进行中", "color": "#faad14"},
        "done":    {"label": "已完成", "color": "#52c41a"},
        "closed":  {"label": "已关闭", "color": "#1677ff"},
        "pause":   {"label": "暂停", "color": "#722ed1"},
        "cancel":  {"label": "已取消", "color": "#bfbfbf"},
        "changed": {"label": "已变更", "color": "#13c2c2"},
    }
    task_status_order = ["wait", "doing", "done", "closed", "pause", "cancel", "changed"]
    task_matrix_map: dict[str, dict[str, list[dict]]] = _dd(lambda: _dd(list))
    task_status_seen: set[str] = set()
    for t in dev_tasks:
        raw_status = (t.get("status") or "unknown").lower()
        status_key = raw_status if raw_status in task_status_meta else "other"
        task_status_seen.add(status_key)
        owner = _task_owner(t) or "Unassigned"
        task_id = t.get("id")
        sid = _story_id(t.get("story"))
        task_matrix_map[owner][status_key].append({
            "id": task_id,
            "name": t.get("name") or "",
            "status": status_key,
            "statusLabel": task_status_meta.get(status_key, {
                "label": raw_status or "其它",
            })["label"],
            "owner": owner,
            "date": _task_date(t),
            "storyId": sid or None,
            "url": f"{ZENTAO_BASE}/task-view-{task_id}.html" if task_id else "",
        })

    task_status_columns = [
        {
            "key": key,
            "label": task_status_meta.get(key, {"label": "其它"})["label"],
            "color": task_status_meta.get(key, {"color": "#595959"})["color"],
        }
        for key in task_status_order
        if key in task_status_seen
    ]
    if "other" in task_status_seen:
        task_status_columns.append({"key": "other", "label": "其它", "color": "#595959"})
    if not task_status_columns:
        task_status_columns = [
            {"key": key, "label": task_status_meta[key]["label"], "color": task_status_meta[key]["color"]}
            for key in ["wait", "doing", "done", "closed"]
        ]

    def _owner_sort(item):
        owner, by_status = item
        total = sum(len(v) for v in by_status.values())
        return (owner == "Unassigned", -total, owner)

    task_owner_rows = []
    task_matrix = []
    task_matrix_tasks = []
    for owner, by_status in sorted(task_matrix_map.items(), key=_owner_sort):
        task_owner_rows.append(owner)
        task_matrix.append([len(by_status.get(col["key"], [])) for col in task_status_columns])
        task_matrix_tasks.append([by_status.get(col["key"], []) for col in task_status_columns])

    task_status_totals = {
        col["key"]: sum(row[idx] for row in task_matrix)
        for idx, col in enumerate(task_status_columns)
    }
    task_kpi = {
        "total": sum(task_status_totals.values()),
        "people": len(task_owner_rows),
        "byStatus": task_status_totals,
    }

    # Group every test-like task by Story. We only count a person as the
    # current test owner when there is a not-closed test task currently
    # assigned to them. Historical test tasks remain evidence but do not drive
    # ownership, because they can be stale and caused false attribution
    # (for example STORY-3884).
    test_tasks_by_story: dict[int, list[dict]] = _dd(list)
    for t in dev_tasks:
        sid = _story_id(t.get("story"))
        if not sid or not _is_test_task(t):
            continue
        test_tasks_by_story[sid].append(t)

    for task_list in test_tasks_by_story.values():
        task_list.sort(key=_task_sort_key, reverse=True)

    def _resolve_story_test_owner(sid: int, story_cases: list[dict]) -> dict:
        tasks = test_tasks_by_story.get(sid, [])
        current_tasks = [
            t for t in tasks
            if _is_current_task(t) and _task_owner(t)
        ]
        if current_tasks:
            task = current_tasks[0]
            return {
                "owner": _task_owner(task),
                "source": "current_test_task",
                "confidence": "high",
                "evidence": (
                    [_task_evidence(task, "current_test_task")]
                    + [_task_evidence(t, "other_current_test_task") for t in current_tasks[1:4]]
                    + [_task_evidence(t, "historical_test_task") for t in tasks if t not in current_tasks][:3]
                ),
            }

        unassigned_current_tasks = [
            t for t in tasks
            if _is_current_task(t) and not _task_owner(t)
        ]
        evidence = (
            [_task_evidence(t, "unassigned_current_test_task") for t in unassigned_current_tasks[:3]]
            + [_task_evidence(t, "historical_test_task") for t in tasks if t not in unassigned_current_tasks][:4]
        )
        case_authors = _Counter(
            _name_of(c.get("openedBy"))
            for c in story_cases
            if _name_of(c.get("openedBy"))
        )
        for owner, count in case_authors.most_common(3):
            evidence.append({
                "source": "test_case_author",
                "owner": owner,
                "count": count,
            })

        return {
            "owner": "Unassigned",
            "source": "none" if not evidence else "evidence_only",
            "confidence": "none" if not evidence else "low",
            "evidence": evidence,
        }

    story_status = {"待评审": 0, "已评审": 0, "进行中": 0, "已完成": 0, "已发布": 0}
    for s in stories:
        story_status[_story_stage_zh(s.get("stage"))] = story_status.get(_story_stage_zh(s.get("stage")), 0) + 1

    bug_active = sum(1 for b in bugs if (b.get("status") or "").lower() == "active")
    bug_closed = sum(1 for b in bugs if (b.get("status") or "").lower() == "closed")
    bug_p0 = sum(1 for b in bugs if int(b.get("pri") or 99) == 1
                  and (b.get("status") or "").lower() == "active")
    bug_p1 = sum(1 for b in bugs if int(b.get("pri") or 99) == 2
                  and (b.get("status") or "").lower() == "active")

    # 4×3 matrix: rows = S1..S4, cols = open / verifying / closed.
    # Status bucketing (ZenTao SaaS observed values):
    #   active, delay   → open    (pending fix)
    #   resolved, confirmed → verifying  (fixed, awaiting QA verification)
    #   closed          → closed
    bug_status_col = {
        "active": 0, "delay": 0,
        "resolved": 1, "confirmed": 1,
        "closed": 2,
    }
    bug_matrix = [[0]*3 for _ in range(4)]
    bug_matrix_bugs: list = [[[] for _ in range(3)] for _ in range(4)]
    for b in bugs:
        st = (b.get("status") or "").lower()
        col = bug_status_col.get(st)
        if col is None:
            continue
        try:
            sev = int(b.get("severity") or 0)
        except Exception:                                          # noqa: BLE001
            continue
        if not (1 <= sev <= 4):
            continue
        bug_matrix[sev-1][col] += 1
        bug_matrix_bugs[sev-1][col].append({
            "id": b.get("id"),
            "title": b.get("title") or "(no title)",
            "status": st,
            "severity": sev,
            "pri": int(b.get("pri") or 0) or None,
            "assignedTo": _name_of(b.get("assignedTo")) or "",
            "url": f"{ZENTAO_BASE}/bug-view-{b.get('id')}.html",
        })
    bug_kpi = {
        "total": sum(sum(r) for r in bug_matrix),
        "open":      sum(r[0] for r in bug_matrix),
        "verifying": sum(r[1] for r in bug_matrix),
        "closed":    sum(r[2] for r in bug_matrix),
        "s1": sum(bug_matrix[0]),
        "s2": sum(bug_matrix[1]),
        "s3": sum(bug_matrix[2]),
        "s4": sum(bug_matrix[3]),
    }

    total_cases = len(cases)
    auto_cases = sum(1 for c in cases if _is_auto(c))

    qa_team_map: dict[str, dict] = {}
    for c in cases:
        qa = _name_of(c.get("openedBy"))
        if not qa:
            continue
        d = qa_team_map.setdefault(qa, {"cases": 0, "auto": 0})
        d["cases"] += 1
        if _is_auto(c):
            d["auto"] += 1

    today = datetime.now()
    start_d = _safe_date(ex.get("begin") or ex.get("openedDate"))
    end_d = _safe_date(ex.get("end") or ex.get("deadline"))
    total_days = max(1, (end_d - start_d).days) if (start_d and end_d) else 0
    days_left = max(0, (end_d - today).days) if end_d else 0

    status_lc = (ex.get("status") or "").lower()
    zh_status = {"doing": "active", "wait": "planning",
                 "suspended": "closing", "closed": "done"}.get(status_lc, "active")

    summary = {
        "id": f"iter-{ex_id}",
        "name": ex.get("name") or f"执行 {ex_id}",
        "code": f"EXEC-{ex_id}",
        "startDate": (start_d.strftime("%Y-%m-%d") if start_d else ""),
        "endDate":   (end_d.strftime("%Y-%m-%d") if end_d else ""),
        "status": zh_status,
        "daysLeft": days_left,
        "totalDays": total_days,
        "progressPct": int(_as_float(ex.get("progress"))),
        "storyTotal": len(stories),
        "storyByStatus": story_status,
        "bugActive": bug_active, "bugClosed": bug_closed,
        "bugP0": bug_p0, "bugP1": bug_p1,
        "bugMatrix": bug_matrix,
        "bugMatrixBugs": bug_matrix_bugs,
        "bugKpi": bug_kpi,
        "taskStatusColumns": task_status_columns,
        "taskOwnerRows": task_owner_rows,
        "taskMatrix": task_matrix,
        "taskMatrixTasks": task_matrix_tasks,
        "taskKpi": task_kpi,
        "testCases": total_cases, "autoTestCases": auto_cases,
        "qaTeam": [
            {"name": k, "cases": v["cases"], "auto": v["auto"]}
            for k, v in sorted(qa_team_map.items(), key=lambda x: -x[1]["cases"])
        ][:5],
        "detailLoaded": True,
    }

    # Build a {story_id -> [bug list]} map from this execution's bugs.
    # Each item is the minimal info the frontend modal needs to show + link out.
    bug_by_story: dict = _dd(list)
    for b in bugs:
        sid = b.get("story") or 0
        if not sid:
            continue
        bug_by_story[sid].append({
            "id": b.get("id"),
            "title": b.get("title") or "(no title)",
            "status": (b.get("status") or "active"),
            "severity": int(b.get("severity") or 0) or None,
            "pri": int(b.get("pri") or 0) or None,
            "assignedTo": _name_of(b.get("assignedTo")) or "",
            "url": f"{ZENTAO_BASE}/bug-view-{b.get('id')}.html",
        })

    # Per-story case stats (if cases happen to be fetched for the iter)
    cases_by_story: dict = _dd(list)
    for c in cases:
        sid = c.get("story") or 0
        if sid:
            cases_by_story[sid].append(c)

    def _case_url(case_id) -> str:
        """ZenTao case ids look like 'case_1797' — strip prefix for the URL."""
        cid = case_id
        if isinstance(cid, str) and cid.startswith("case_"):
            cid = cid[5:]
        try:
            return f"{ZENTAO_BASE}/testcase-view-{int(cid)}.html"
        except (TypeError, ValueError):
            return f"{ZENTAO_BASE}/testcase-view-{cid}.html"

    def _bucket_for(result: str, status: str) -> str:
        """Map ZenTao case state → one of pass/fail/inProgress/unexecuted."""
        r = (result or "").lower()
        if r == "pass":
            return "pass"
        if r == "fail":
            return "fail"
        if r in ("blocked", "n/a"):
            return "inProgress"
        # Empty result — case has not been run yet
        return "inProgress" if (status or "").lower() == "doing" else "unexecuted"

    requirements = []
    for idx, s in enumerate(stories[:50]):
        sid = s.get("id")
        story_bugs = bug_by_story.get(sid, [])
        story_cases = cases_by_story.get(sid, [])
        owner_info = _resolve_story_test_owner(_story_id(sid), story_cases)
        total_c = len(story_cases)

        # Build the bucketed breakdown + per-case list for the modal
        breakdown = {"pass": 0, "fail": 0, "inProgress": 0, "unexecuted": 0, "total": total_c}
        case_list = []
        for c in story_cases:
            bucket = _bucket_for(c.get("lastRunResult"), c.get("status"))
            breakdown[bucket] += 1
            case_list.append({
                "id": c.get("id"),
                "title": c.get("title") or "(no title)",
                "lastRunResult": c.get("lastRunResult") or "",
                "status": c.get("status") or "",
                "bucket": bucket,
                "lastRunner": _name_of(c.get("lastRunner")) or "",
                "url": _case_url(c.get("id")),
            })

        # Demo data injection — first row of each iteration that has no real
        # cases gets a sample breakdown (5 pass / 10 fail / 15 in-prog / 30
        # unexec = 50% executed). Lets the user see what the chips look like
        # before real case linkage is wired up.
        is_demo = (idx == 0 and total_c == 0)
        if is_demo:
            counts = [("pass", 5), ("fail", 10), ("inProgress", 15), ("unexecuted", 30)]
            breakdown = {k: n for k, n in counts}
            breakdown["total"] = sum(n for _, n in counts)
            case_list = []
            seq = 1
            label_zh = {"pass": "通过", "fail": "失败",
                         "inProgress": "进行中", "unexecuted": "未执行"}
            for bucket, n in counts:
                for _ in range(n):
                    fake_id = f"demo_{ex_id}_{seq:03d}"
                    case_list.append({
                        "id": fake_id,
                        "title": f"[DEMO] {label_zh[bucket]} 用例样例 #{seq}",
                        "lastRunResult": bucket if bucket in ("pass", "fail") else "",
                        "status": "doing" if bucket == "inProgress" else ("normal" if bucket == "unexecuted" else "done"),
                        "bucket": bucket,
                        "lastRunner": "",
                        "url": "",
                        "demo": True,
                    })
                    seq += 1

        executed_c = breakdown["pass"] + breakdown["fail"]
        exec_rate_pct = round(executed_c / breakdown["total"] * 100) if breakdown["total"] else None

        # Highest-priority bug surfaces in the row tag (P1 = most urgent)
        worst_pri = min((b.get("pri") or 99) for b in story_bugs) if story_bugs else None
        severity_tag = f"P{worst_pri}" if worst_pri and worst_pri <= 4 else "—"

        requirements.append({
            "id": f"STORY-{sid}",
            "storyId": sid,
            "storyUrl": f"{ZENTAO_BASE}/story-view-{sid}.html",
            "title": s.get("title") or s.get("name") or "—",
            "status": _story_stage_zh(s.get("stage")),
            "qa": owner_info["owner"],
            "qaSource": owner_info["source"],
            "qaConfidence": owner_info["confidence"],
            "qaEvidence": owner_info["evidence"],
            "cases": breakdown["total"],
            "executedCases": executed_c,
            "execRatePct": exec_rate_pct,
            "caseBreakdown": breakdown,
            "caseList": case_list,
            "isDemo": is_demo,
            "bugs": len(story_bugs),
            "bugList": story_bugs,
            "severity": severity_tag,
        })

    return {"summary": summary, "requirements": requirements}


def _exec_summary_minimal(e: dict) -> dict:
    """Light execution record — no sub-data fetched yet. Used in
    `moreExecutions` (the dropdown candidates)."""
    start_d = _safe_date(e.get("begin") or e.get("openedDate"))
    end_d = _safe_date(e.get("end") or e.get("deadline"))
    status_lc = (e.get("status") or "").lower()
    zh_status = {"doing": "active", "wait": "planning",
                 "suspended": "closing", "closed": "done"}.get(status_lc, "active")
    return {
        "id": f"iter-{e.get('id')}",
        "name": e.get("name") or f"执行 {e.get('id')}",
        "code": f"EXEC-{e.get('id')}",
        "startDate": (start_d.strftime("%Y-%m-%d") if start_d else ""),
        "endDate":   (end_d.strftime("%Y-%m-%d") if end_d else ""),
        "status": zh_status,
        "progressPct": int(_as_float(e.get("progress"))),
        "project": e.get("project"),
        "detailLoaded": False,
    }


@router.get("/api/zentao/execution/{exec_id}/detail")
def zentao_execution_detail(exec_id: int, refresh: bool = False):
    """Per-execution detail (stories, bugs, testcases). Cached 5 min.
    Frontend calls this lazily when user picks an execution from the dropdown."""
    now = _time.time()
    if not refresh:
        hit = _ZT_EXEC_DETAIL_CACHE.get(exec_id)
        if hit and (now - hit[0]) < _ZT_DASHBOARD_TTL:
            cached = dict(hit[1])
            cached["cached"] = True
            return cached
    token = _zentao_token()
    if not token:
        return {"error": "ZENTAO_API_V2_TOKEN not set"}

    ex = _zt_get(f"/executions/{exec_id}", token) or {}
    if not ex or not ex.get("id"):
        return {"error": f"execution {exec_id} not found"}

    detail = _build_iter_detail(ex, token)
    detail["cached"] = False
    _ZT_EXEC_DETAIL_CACHE[exec_id] = (now, detail)
    return detail


def _empty_dashboard(error_msg: str = "") -> dict:
    return {
        "iterations": [], "moreExecutions": [],
        "requirementsByIter": {}, "modules": [],
        "qaThroughput": [],
        "autoTrend": [],
        "meta": {"error": error_msg, "cached": False,
                 "fetchedAt": datetime.now().isoformat()},
    }


def _local_story_generation_requirements() -> list[dict]:
    story_ids = [4161, 4266]
    requirements = []
    for sid in story_ids:
        rule = STORY_RULES[sid]
        requirements.append({
            "id": f"STORY-{sid}",
            "storyId": sid,
            "storyUrl": f"{ZENTAO_BASE}/execution-storyView-{sid}-614.html",
            "title": rule.title,
            "status": "进行中",
            "qa": "王一凡",
            "cases": 0,
            "executedCases": 0,
            "execRatePct": None,
            "caseBreakdown": {"pass": 0, "fail": 0, "inProgress": 0, "unexecuted": 0, "total": 0},
            "caseList": [],
            "isDemo": False,
            "bugs": 0,
            "bugList": [],
            "severity": "—",
        })
    return requirements


def _local_story_generation_iteration(requirements: list[dict]) -> dict:
    iteration = {
        "id": "iter-614",
        "name": "Execution 614 - local story generation fallback",
        "code": "EXEC-614",
        "startDate": "",
        "endDate": "",
        "status": "active",
        "daysLeft": 0,
        "totalDays": 0,
        "progressPct": 0,
        "storyTotal": len(requirements),
        "storyByStatus": {"待评审": 0, "已评审": 0, "进行中": len(requirements), "已完成": 0, "已发布": 0},
        "bugActive": 0,
        "bugClosed": 0,
        "bugP0": 0,
        "bugP1": 0,
        "bugMatrix": [[0, 0, 0] for _ in range(4)],
        "bugMatrixBugs": [[[], [], []] for _ in range(4)],
        "bugKpi": {"total": 0, "open": 0, "verifying": 0, "closed": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0},
        "testCases": 0,
        "autoTestCases": 0,
        "qaTeam": [{"name": "王一凡", "cases": 0, "auto": 0}],
        "detailLoaded": True,
    }
    return iteration


def _local_story_generation_dashboard(error_msg: str = "") -> dict:
    """Offline fallback so story-scoped generation still works during token refresh."""
    requirements = _local_story_generation_requirements()
    return {
        "iterations": [_local_story_generation_iteration(requirements)],
        "moreExecutions": [],
        "requirementsByIter": {"iter-614": requirements},
        "modules": [],
        "qaThroughput": [],
        "autoTrend": [],
        "meta": {
            "error": error_msg,
            "fallback": "local-story-generation",
            "cached": False,
            "fetchedAt": datetime.now().isoformat(),
        },
    }


def _merge_local_story_generation_entries(result: dict) -> dict:
    """Expose local story-case generation even if ZenTao omits story details."""
    iter_key = "iter-614"
    requirements_by_iter = result.setdefault("requirementsByIter", {})
    requirements = requirements_by_iter.setdefault(iter_key, [])
    existing_ids = {
        int(r.get("storyId"))
        for r in requirements
        if str(r.get("storyId") or "").isdigit()
    }
    additions = [
        r for r in _local_story_generation_requirements()
        if int(r["storyId"]) not in existing_ids
    ]
    if not additions:
        return result

    requirements.extend(additions)
    iterations = result.setdefault("iterations", [])
    more_executions = result.setdefault("moreExecutions", [])
    # Look in BOTH iterations and moreExecutions — historically this only
    # checked iterations and synthesised a duplicate iter-614 with the bogus
    # name 'Execution 614 - local story generation fallback', clobbering the
    # real '国际版官网V1.0' label in the dropdown / per-iter cards.
    target = (
        next((it for it in iterations if it.get("id") == iter_key), None)
        or next((it for it in more_executions if it.get("id") == iter_key), None)
    )
    if not target:
        # Real iter-614 not in this response at all (offline / token failure).
        # Only here is fabricating a placeholder appropriate.
        iterations.append(_local_story_generation_iteration(requirements))
    else:
        target["storyTotal"] = max(int(target.get("storyTotal") or 0), len(requirements))
        story_by_status = target.setdefault(
            "storyByStatus",
            {"待评审": 0, "已评审": 0, "进行中": 0, "已完成": 0, "已发布": 0},
        )
        story_by_status["进行中"] = max(int(story_by_status.get("进行中") or 0), len(additions))

    result.setdefault("meta", {})["localStoryGeneration"] = "story-4161-4266"
    return result


@router.get("/api/zentao/dashboard")
def zentao_dashboard(
    product_id: int = 0,                # 0 = all active executions (no product filter)
    refresh: bool = False,
    max_iterations: int = 6,
    project: str = "west-kowloon",
):
    """Aggregate ZenTao data for the ZenTao Integration page.

    Returns: {iterations, moreExecutions, requirementsByIter, modules,
    qaThroughput, autoTrend, meta}. Each iteration carries its own
    bugMatrix / bugMatrixBugs / bugKpi (per-exec bug breakdown).
    Cached 5 minutes per project/product/execution — pass
    refresh=true to bypass."""
    cfg = _project_config(project)
    project_key = cfg["key"]
    mapped_product_id = int(cfg.get("zentaoProductId") or 0)
    mapped_execution_id = int(cfg.get("zentaoExecutionId") or 0)
    execution_scoped = mapped_execution_id > 0
    if not mapped_product_id and not mapped_execution_id:
        empty = _empty_dashboard(f"No ZenTao product or execution is mapped for project {project_key}.")
        empty["meta"].update({
            "project": project_key,
            "productId": None,
            "executionId": None,
            "scope": "unmapped-project",
        })
        return empty
    if mapped_product_id:
        product_id = mapped_product_id

    cache_key = (
        f"project:{project_key}:product:{product_id}:"
        f"execution:{mapped_execution_id or 'all'}:max:{max_iterations}"
    )
    now = _time.time()

    if not refresh:
        hit = _ZT_DASHBOARD_CACHE.get(cache_key)
        if hit and (now - hit[0]) < _ZT_DASHBOARD_TTL:
            cached_result = dict(hit[1])
            cached_result["meta"] = {**cached_result.get("meta", {}), "cached": True}
            return cached_result

    token = _zentao_token()
    if not token:
        if project_key == "west-kowloon":
            return _local_story_generation_dashboard("ZENTAO_API_V2_TOKEN not set")
        empty = _empty_dashboard("ZENTAO_API_V2_TOKEN not set")
        empty["meta"].update({
            "project": project_key,
            "productId": product_id,
            "executionId": mapped_execution_id or None,
            "scope": f"execution:{mapped_execution_id}" if mapped_execution_id else "unmapped-project",
        })
        return empty
    global _ZT_LAST_ERROR
    _ZT_LAST_ERROR = None

    # --- 1. Executions list ------------------------------------------------
    # In platform mode the selected dashboard project owns the ZenTao scope.
    # Prefer the execution explicitly mapped in PROJECT_CATALOG; otherwise fall
    # back to the historical all-active behavior for unmapped/internal views.
    from concurrent.futures import ThreadPoolExecutor
    if execution_scoped:
        mapped_exec = _zt_get(f"/executions/{mapped_execution_id}", token, critical=True) or {}
        executions = [mapped_exec] if mapped_exec.get("id") else []
    else:
        def _fetch_status(status: str):
            return _zt_get("/executions", token,
                           {"limit": 100, "status": status}, critical=True) or {}
        with ThreadPoolExecutor(max_workers=2) as _list_pool:
            doing_resp, wait_resp = _list_pool.map(_fetch_status, ["doing", "wait"])
        execs_doing = doing_resp.get("executions") or doing_resp.get("data") or []
        execs_wait  = wait_resp.get("executions")  or wait_resp.get("data")  or []
        executions = execs_doing + execs_wait
    if not executions and _ZT_LAST_ERROR:
        if project_key == "west-kowloon":
            return _local_story_generation_dashboard(_ZT_LAST_ERROR)
        empty = _empty_dashboard(_ZT_LAST_ERROR)
        empty["meta"].update({
            "project": project_key,
            "productId": product_id,
            "executionId": mapped_execution_id or None,
            "scope": f"execution:{mapped_execution_id}" if mapped_execution_id else "unmapped-project",
        })
        return empty
    if not executions and execution_scoped:
        empty = _empty_dashboard(f"Mapped ZenTao execution {mapped_execution_id} not found")
        empty["meta"].update({
            "project": project_key,
            "productId": product_id,
            "executionId": mapped_execution_id,
            "scope": f"execution:{mapped_execution_id}",
        })
        return empty

    today = datetime.now()
    # "最近活跃优先" — use realBegan (actually started) when present, else
    # planned begin, else openedDate. Also prefer 'doing' over 'wait'.
    def _exec_sort_key(e):
        status_rank = {"doing": 2, "suspended": 1, "wait": 0}.get(
            (e.get("status") or "").lower(), 0)
        d = (_safe_date(e.get("realBegan"))
             or _safe_date(e.get("begin"))
             or _safe_date(e.get("openedDate")))
        ts = d.timestamp() if d else 0
        return (status_rank, ts)
    if execution_scoped:
        active_execs = executions[:1]
    else:
        executions.sort(key=_exec_sort_key, reverse=True)
        active_execs = [
            e for e in executions
            if (e.get("status") or "").lower() in ("doing", "wait", "suspended")
        ][:max_iterations]

    iterations = []
    requirements_by_iter = {}

    # Parallel-fetch every (exec_id, resource) sub-call PLUS the two
    # product-level fetches in one big pool. ZenTao SaaS is ~1-2s per call
    # — 16 workers brings 26 fetches from ~52s down to ~5-8s.
    from concurrent.futures import ThreadPoolExecutor
    SUB_RESOURCES = ("stories", "bugs", "testcases", "tasks")
    iter_tasks = [(ex.get("id"), r) for ex in active_execs if ex.get("id") for r in SUB_RESOURCES]

    def _fetch_iter(args):
        ex_id, resource = args
        # Use bigger page sizes for bugs/cases/tasks (some execs have 200+ each)
        limit = 500 if resource in ("bugs", "testcases", "tasks") else 200
        return ("iter", ex_id, resource,
                _zt_get(f"/executions/{ex_id}/{resource}", token, {"limit": limit}) or {})

    def _fetch_product_cases():
        if product_id > 0 and not execution_scoped:
            return ("product", "cases",
                    _zt_get(f"/products/{product_id}/testcases", token, {"limit": 500}) or {})
        return ("product", "cases", {})

    def _fetch_product_bugs():
        if product_id > 0 and not execution_scoped:
            return ("product", "bugs",
                    _zt_get(f"/products/{product_id}/bugs", token, {"limit": 500, "status": "active"}) or {})
        return ("product", "bugs", {})

    def _fetch_testtasks():
        # Shared across all per-iter builds — one /testtasks call total
        return ("global", "testtasks",
                _zt_get("/testtasks", token, {"limit": 500}) or {})

    sub_responses: dict[tuple, dict] = {}
    product_cases_resp: dict = {}
    product_bugs_resp: dict = {}
    testtasks_resp: dict = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(_fetch_iter, t) for t in iter_tasks]
        futures.append(pool.submit(_fetch_product_cases))
        futures.append(pool.submit(_fetch_product_bugs))
        futures.append(pool.submit(_fetch_testtasks))
        for fut in futures:
            res = fut.result()
            if res[0] == "iter":
                _, ex_id, resource, resp = res
                sub_responses[(ex_id, resource)] = resp
            elif res[0] == "product" and res[1] == "cases":
                product_cases_resp = res[2]
            elif res[0] == "product" and res[1] == "bugs":
                product_bugs_resp = res[2]
            elif res[0] == "global" and res[1] == "testtasks":
                testtasks_resp = res[2]

    for ex in active_execs:
        ex_id = ex.get("id")
        if not ex_id:
            continue
        # Pull the 3 pre-fetched sub-responses for this exec + the shared
        # testtasks response. Let the helper turn them into a summary +
        # requirements list (with per-story bug list, exec-wide QA owner).
        per_iter_subs = {
            "stories":   sub_responses.get((ex_id, "stories"), {}),
            "bugs":      sub_responses.get((ex_id, "bugs"), {}),
            "testcases": sub_responses.get((ex_id, "testcases"), {}),
            "tasks":     sub_responses.get((ex_id, "tasks"), {}),
            "testtasks": testtasks_resp,
        }
        built = _build_iter_detail(ex, token, sub_responses=per_iter_subs)
        iterations.append(built["summary"])
        requirements_by_iter[built["summary"]["id"]] = built["requirements"]
        # Also seed the per-exec detail cache so any later dropdown click is instant.
        _ZT_EXEC_DETAIL_CACHE[ex_id] = (now, built)

    # Light list of every other active/wait execution — frontend uses these to
    # populate the searchable dropdown without firing N sub-fetches up front.
    seen_ids = {ex.get("id") for ex in active_execs}
    more_executions = [] if execution_scoped else [
        _exec_summary_minimal(e)
        for e in executions
        if e.get("id") and e["id"] not in seen_ids
        and (e.get("status") or "").lower() in ("doing", "wait", "suspended")
    ]

    # --- 2. All testcases for the product (for modules / QA throughput / trend)
    # If no product was selected, aggregate across the iterations we already
    # have (less data but no extra ZenTao round-trips).
    all_cases: list[dict] = []
    if product_id > 0 and not execution_scoped:
        all_cases_resp = product_cases_resp
        all_cases = (all_cases_resp.get("data")
                     or all_cases_resp.get("cases")
                     or all_cases_resp.get("testcases") or [])
    else:
        # Project execution scope, or no product selected: reuse the testcases
        # already fetched per execution. Sum them up, dedupe by case id.
        seen = set()
        for ex in active_execs:
            cr = sub_responses.get((ex.get("id"), "testcases"), {})
            for c in (cr.get("data") or cr.get("cases") or cr.get("testcases") or []):
                cid = c.get("id")
                if cid and cid not in seen:
                    seen.add(cid)
                    all_cases.append(c)

    # Module rollup
    module_counts: dict[str, dict] = {}
    for c in all_cases:
        mod = _name_of(c.get("module")) or "未分类"
        d = module_counts.setdefault(mod, {"cases": 0, "auto": 0})
        d["cases"] += 1
        if _is_auto(c):
            d["auto"] += 1
    modules = [
        {"name": k, "cases": v["cases"], "auto": v["auto"]}
        for k, v in sorted(module_counts.items(), key=lambda x: -x[1]["cases"])
    ][:12]

    # --- 3. (was global S×P heatmap — superseded by per-iter bugMatrix.) -

    # --- 4. QA throughput across recent months ---------------------------
    from collections import defaultdict
    qa_iter_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in all_cases:
        opened = c.get("openedDate") or ""
        if not opened:
            continue
        month_key = opened[:7]
        qa_name = _name_of(c.get("openedBy"))
        if not qa_name:
            continue
        qa_iter_counts[qa_name][month_key] += 1

    all_months = sorted({m for q, ms in qa_iter_counts.items() for m in ms})[-4:]
    top_qas = sorted(qa_iter_counts.items(), key=lambda x: -sum(x[1].values()))[:5]
    qa_throughput = [
        {
            "qa": qa,
            "data": [{"iter": m[-2:], "cases": qa_iter_counts[qa].get(m, 0)} for m in all_months],
        }
        for qa, _ in top_qas
    ]

    # --- 5. Automation trend (cumulative auto% by month, last 6) ---------
    auto_trend = []
    today_dt = datetime.now().replace(day=1)
    for i in range(5, -1, -1):
        target_m = (today_dt - timedelta(days=i*32)).strftime("%Y-%m")
        label = target_m[-2:]
        cases_up_to_m = [c for c in all_cases if (c.get("openedDate") or "")[:7] <= target_m]
        if not cases_up_to_m:
            auto_trend.append({"month": label, "pct": 0})
            continue
        auto_n = sum(1 for c in cases_up_to_m if _is_auto(c))
        auto_trend.append({"month": label, "pct": round(auto_n / len(cases_up_to_m) * 100)})

    # Total active bugs across loaded execs — for the meta strip only.
    total_active_bugs = 0
    if product_id > 0 and not execution_scoped:
        total_active_bugs = sum(
            1 for b in (product_bugs_resp.get("data")
                        or product_bugs_resp.get("bugs") or [])
            if (b.get("status") or "").lower() == "active"
        )
    else:
        seen: set = set()
        for ex in active_execs:
            br = sub_responses.get((ex.get("id"), "bugs"), {})
            for b in (br.get("data") or br.get("bugs") or []):
                if (b.get("status") or "").lower() != "active":
                    continue
                bid = b.get("id")
                if bid and bid not in seen:
                    seen.add(bid)
                    total_active_bugs += 1

    result = {
        "iterations": iterations,
        "moreExecutions": more_executions,
        "requirementsByIter": requirements_by_iter,
        "modules": modules,
        "qaThroughput": qa_throughput,
        "autoTrend": auto_trend,
        "meta": {
            "productId": product_id,
            "project": project_key,
            "executionId": mapped_execution_id or None,
            "scope": f"execution:{mapped_execution_id}" if mapped_execution_id else "all-active-executions",
            "fetchedAt": datetime.now().isoformat(),
            "cached": False,
            "activeIterations": len(active_execs),
            "totalActive": len(active_execs) + len(more_executions),
            "totalCasesInProduct": len(all_cases),
            "totalActiveBugs": total_active_bugs,
            "error": None,
        },
    }
    if project_key == "west-kowloon":
        result = _merge_local_story_generation_entries(result)
    _ZT_DASHBOARD_CACHE[cache_key] = (now, result)
    return result




zt_get = _zt_get
zt_post_json = _zt_post_json


def dashboard_cache():
    return _ZT_DASHBOARD_CACHE
