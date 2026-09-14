"""smoke_zentao.py — backend contract smoke for the ZenTao Integration page.

Exercises /api/zentao/dashboard + /api/zentao/execution/{id}/detail with
real ZenTao SaaS data and asserts the response shape / invariants the
frontend depends on. Designed to run in ~5s once the cache is warm.

Run AFTER any change to:
    02-platform/02-dashboard/01-backend/main.py (anything under # ZenTao Integration block)
    or frontend code that consumes /api/zentao/*.

Invocation:
    cd D:\\Workspace\\west-kowloon\\02-automation
    D:\\Workspace\\qa-harness\\02-platform\\01-automation\\.venv\\Scripts\\python.exe 04-tools\\smoke_zentao.py

Exits 0 on all-green, non-zero with a SUMMARY line on any failure.
"""
from __future__ import annotations

import json
import socket
import sys
import time
import urllib.error
import urllib.request

BACKEND = "http://127.0.0.1:8002"
DEFAULT_PRODUCT_ID = 146                                   # 西九 (West Kowloon)

results: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {name}" + (f"  ({detail})" if detail else ""))
    results.append((name, passed, detail))


def port_up(port: int, timeout: float = 1.0) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except OSError:
        return False


def http_get(path: str, timeout: float = 60.0) -> tuple[int, dict | None, float]:
    """Return (status_code, parsed_json|None, elapsed_seconds)."""
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(BACKEND + path, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(body), time.monotonic() - t0
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            return e.code, json.loads(body) if body else None, time.monotonic() - t0
        except Exception:                                          # noqa: BLE001
            return e.code, None, time.monotonic() - t0
    except Exception as e:                                         # noqa: BLE001
        print(f"  [ERR ] http {path}: {e}")
        return 0, None, time.monotonic() - t0


def head_ok(url: str, timeout: float = 8.0) -> bool:
    """Send HEAD; treat 2xx / 3xx as OK (some servers redirect)."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except Exception:                                              # noqa: BLE001
        return False


def main() -> int:
    print(f"\n=== ZenTao Integration · backend smoke ===\n")

    # Pre-flight: backend running?
    if not port_up(8002):
        check("backend up on :8002", False, "start uvicorn first")
        return summarize()
    check("backend up on :8002", True)

    # ─── T1: dashboard happy path ───────────────────────────────────────────
    print("\n--- dashboard endpoint ---")
    status, body, ms = http_get(
        f"/api/zentao/dashboard?product_id={DEFAULT_PRODUCT_ID}&max_iterations=4",
        timeout=180.0,
    )
    check("/dashboard returns 200", status == 200, f"got {status} in {ms:.1f}s")
    if status != 200 or not body:
        return summarize()

    # Required top-level keys
    required = ("iterations", "moreExecutions", "requirementsByIter", "modules",
                "qaThroughput", "autoTrend", "meta")
    for k in required:
        check(f"  dashboard has key `{k}`", k in body)

    # iterations shape
    iters = body.get("iterations", [])
    check("dashboard iters ≥ 1", len(iters) >= 1, f"got {len(iters)}")
    if iters:
        it = iters[0]
        for k in ("id", "name", "code", "startDate", "endDate", "status",
                  "progressPct", "storyTotal", "storyByStatus",
                  "bugActive", "bugClosed", "testCases", "qaTeam",
                  "bugMatrix", "bugMatrixBugs", "bugKpi"):
            check(f"  iter[0] has `{k}`", k in it)
        sbs = it.get("storyByStatus") or {}
        for bucket in ("待评审", "已评审", "进行中", "已完成", "已发布"):
            check(f"  iter[0].storyByStatus has `{bucket}`", bucket in sbs)

        # Per-iter S × Status bug matrix (rows = S1..S4, cols = open/verify/closed)
        bm = it.get("bugMatrix") or []
        check("iter[0].bugMatrix is 4 rows", len(bm) == 4, f"got {len(bm)}")
        if len(bm) == 4:
            check("  each row is 3 cols (open/verify/closed)",
                  all(len(r) == 3 for r in bm),
                  str([len(r) for r in bm]))
            check("  all cells are ints",
                  all(isinstance(v, int) for r in bm for v in r))

        # bugMatrixBugs shape mirrors bugMatrix, counts must match
        bmb = it.get("bugMatrixBugs") or []
        check("iter[0].bugMatrixBugs is 4 rows", len(bmb) == 4, f"got {len(bmb)}")
        if len(bmb) == 4 and len(bm) == 4:
            mismatches = []
            for r in range(4):
                for c in range(3):
                    if len(bmb[r][c]) != bm[r][c]:
                        mismatches.append(f"[{r}][{c}] {len(bmb[r][c])}≠{bm[r][c]}")
            check("  bug-list counts match bugMatrix counts",
                  not mismatches, ", ".join(mismatches[:3]) or "all aligned")

        # bugKpi.total must equal sum of bugMatrix
        kpi = it.get("bugKpi") or {}
        matrix_total = sum(sum(r) for r in bm) if len(bm) == 4 else None
        check("  bugKpi.total == sum(bugMatrix)",
              kpi.get("total") == matrix_total,
              f"kpi={kpi.get('total')} matrix={matrix_total}")
        # bugKpi columns must add up
        check("  bugKpi (open+verifying+closed) == total",
              (kpi.get("open", 0) + kpi.get("verifying", 0) + kpi.get("closed", 0))
              == kpi.get("total", 0),
              f"sum={kpi.get('open',0)+kpi.get('verifying',0)+kpi.get('closed',0)} total={kpi.get('total')}")
        # bugKpi.s1 must equal row 0 sum
        if len(bm) == 4:
            check("  bugKpi.s1 == sum(bugMatrix[0])",
                  kpi.get("s1") == sum(bm[0]),
                  f"s1={kpi.get('s1')} row0={sum(bm[0])}")

    # ─── T2: execution detail for first iter ────────────────────────────────
    if iters:
        first_iter_id = iters[0]["id"]
        exec_id = first_iter_id.replace("iter-", "")
        print(f"\n--- execution detail (iter {exec_id}) ---")
        status, d, ms = http_get(f"/api/zentao/execution/{exec_id}/detail", timeout=30.0)
        check("/execution/{id}/detail returns 200", status == 200, f"in {ms:.1f}s")
        if status == 200 and d:
            check("  has `summary`", "summary" in d)
            check("  has `requirements`", "requirements" in d)
            reqs = d.get("requirements") or []
            if reqs:
                r0 = reqs[0]
                for k in ("id", "storyId", "storyUrl", "title", "status", "qa",
                          "cases", "executedCases", "execRatePct",
                          "caseBreakdown", "caseList", "bugs", "bugList"):
                    check(f"  req[0] has `{k}`", k in r0)
                # Invariant: caseBreakdown.total == sum of 4 buckets
                bd = r0.get("caseBreakdown") or {}
                expect = (bd.get("pass", 0) + bd.get("fail", 0)
                          + bd.get("inProgress", 0) + bd.get("unexecuted", 0))
                check("  caseBreakdown.total == sum(4 buckets)",
                      bd.get("total") == expect,
                      f"total={bd.get('total')} sum={expect}")
                # Invariant: caseList length == total
                check("  caseList.length == caseBreakdown.total",
                      len(r0.get("caseList") or []) == bd.get("total"),
                      f"list={len(r0.get('caseList') or [])} total={bd.get('total')}")
                # Invariant: executedCases == pass + fail
                exp_exec = bd.get("pass", 0) + bd.get("fail", 0)
                check("  executedCases == pass + fail",
                      r0.get("executedCases") == exp_exec,
                      f"exec={r0.get('executedCases')} pf={exp_exec}")
                # Invariant: bugList length == bugs
                check("  bugList.length == bugs count",
                      len(r0.get("bugList") or []) == r0.get("bugs"))
                # storyUrl is well-formed
                surl = r0.get("storyUrl") or ""
                check("  storyUrl matches lengliwh/story-view-N.html",
                      surl.startswith("https://lengliwh.chandao.net/story-view-")
                      and surl.endswith(".html"),
                      surl)

    # ─── T3: cache + refresh contract for /execution/{id}/detail ────────────
    # The Refresh button is useless if `refresh=true` doesn't actually bypass
    # the per-exec cache. Pin this with three calls back-to-back:
    #   first  → cached: False  (cold)
    #   second → cached: True   (5-min TTL hit)
    #   third  → cached: False  (refresh=true wins)
    if iters:
        print("\n--- detail cache + refresh contract ---")
        first_iter_id = iters[0]["id"]
        cache_exec_id = first_iter_id.replace("iter-", "")
        _, d1, _ = http_get(f"/api/zentao/execution/{cache_exec_id}/detail?refresh=true",
                            timeout=30.0)
        _, d2, _ = http_get(f"/api/zentao/execution/{cache_exec_id}/detail",
                            timeout=10.0)
        _, d3, _ = http_get(f"/api/zentao/execution/{cache_exec_id}/detail?refresh=true",
                            timeout=30.0)
        check("warm hit sets cached=True",
              d2 and d2.get("cached") is True,
              f"d2.cached={d2.get('cached') if d2 else None}")
        check("refresh=true returns cached=False",
              d3 and d3.get("cached") is False,
              f"d3.cached={d3.get('cached') if d3 else None}")
        # Sanity: shape must be stable across cache hit
        if d1 and d2:
            check("cached payload shape matches cold payload",
                  set((d1 or {}).keys()) == set((d2 or {}).keys()),
                  "")

    # ─── T4: error paths ────────────────────────────────────────────────────
    print("\n--- error paths ---")
    status, d, _ = http_get("/api/zentao/execution/99999999/detail", timeout=30.0)
    check("detail of nonexistent exec returns 200 with error",
          status == 200 and bool(d) and bool(d.get("error")),
          f"status={status} err={d.get('error') if d else None}")

    # Malformed id triggers FastAPI 422
    status, _, _ = http_get("/api/zentao/execution/abc/detail", timeout=10.0)
    check("detail of malformed id returns 422", status == 422, f"got {status}")

    # ─── T4: URL validity (one bug URL must be live) ────────────────────────
    print("\n--- URL liveness (HEAD probes) ---")
    if iters:
        # Find a requirement with bugs, take its first bugList[0].url
        first_iter_id = iters[0]["id"]
        exec_id = first_iter_id.replace("iter-", "")
        _, d, _ = http_get(f"/api/zentao/execution/{exec_id}/detail", timeout=30.0)
        sample_url = None
        for r in (d.get("requirements") if d else []) or []:
            for b in r.get("bugList") or []:
                if b.get("url"):
                    sample_url = b["url"]
                    break
            if sample_url:
                break
        if sample_url:
            check(f"bug url {sample_url[-40:]} is reachable",
                  head_ok(sample_url))
        else:
            check("bug URL liveness", True, "no bugs to probe — skipped")

    return summarize()


def summarize() -> int:
    print()
    fails = [r for r in results if not r[1]]
    total = len(results)
    if fails:
        print(f"SUMMARY: {len(fails)}/{total} FAILED")
        for n, _, d in fails:
            print(f"  ✗ {n}" + (f": {d}" if d else ""))
        return 1
    print(f"SUMMARY: {total}/{total} PASS — ZenTao backend contract OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
