"""Self-test for the dashboard 'open bug' feature, exercising every spec
the user laid out. Creates bugs in ZenTao, verifies each property, then
deletes everything and resets the DB so no test residue is left behind.

Spec being verified (Evan, 2026-05-23):
  1. Title format:  [模块] 简要场景 — 用例未通过 / Failed   (no [Auto], no
     full SIT-TC-WEB-AUTH-XXX prefix, no '(run #?)')
  2. assignedTo == wangyifan for every auto-bug
  3. Body sections (Chinese): 缺陷概述 / 测试环境 / 重现步骤 / 错误信息
     / API 错误 / 截图
  4. Gherkin Given/When/Then extracted from 01-features/*.feature
  5. Screenshots embedded as <img src="http://..."> pointing back at the
     dashboard's /screenshots static mount (data: URLs are stripped by
     ZenTao SaaS sanitization — confirmed earlier)
  6. Same-title submit is idempotent; different-title submit creates a new bug
  7. PASSED scenarios can also have bugs opened (preemptive flake tracking)
"""
from __future__ import annotations
import os, sys, json, re, sqlite3, time
from pathlib import Path
import requests

TOKEN = os.environ.get("ZENTAO_API_V2_TOKEN")
if not TOKEN:
    sys.exit("ERROR: ZENTAO_API_V2_TOKEN not set")
ZENTAO = "https://lengliwh.chandao.net"
DASH = os.getenv("QA_DASHBOARD_URL", "http://127.0.0.1:8002").rstrip("/")
REPO_ROOT = Path(os.getenv("QA_HARNESS_ROOT", "D:/Workspace/qa-harness")).resolve()
DB_PATH = str(REPO_ROOT / "02-platform" / "02-dashboard" / "01-backend" / "dashboard.db")
H_TOK = {"Token": TOKEN}

results: list[tuple[bool, str]] = []
created_bug_ids: set[int] = set()
created_sb_ids: set[int] = set()


def check(cond: bool, msg: str):
    results.append((cond, msg))
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {msg}")


def open_bug(scenario_id: int, title: str | None = None) -> dict:
    body = {} if title is None else {"title": title}
    r = requests.post(f"{DASH}/api/scenarios/{scenario_id}/open-bug",
                      headers={"Content-Type": "application/json"},
                      data=json.dumps(body), timeout=60)
    return r.json()


def get_bug(bug_id: int) -> dict:
    return requests.get(f"{ZENTAO}/api.php/v1/bugs/{bug_id}",
                        headers=H_TOK, timeout=15).json()


# --- pick scenarios to exercise ---
def pick_scenarios():
    failed_runs = (51, 52)
    passed_runs = (49, 50)
    failed_s = passed_s = None
    for rid in failed_runs:
        r = requests.get(f"{DASH}/api/runs/{rid}", timeout=10).json()
        f = [s for s in r["scenarios"] if s["status"] == "failed"]
        if f:
            failed_s = f[0]; break
    for rid in passed_runs:
        r = requests.get(f"{DASH}/api/runs/{rid}", timeout=10).json()
        p = [s for s in r["scenarios"] if s["status"] == "passed"]
        if p:
            passed_s = p[0]; break
    return failed_s, passed_s


def case1_failed_scenario_default_template(failed_s):
    print(f"\n=== CASE 1: open bug on FAILED scenario {failed_s['id']} "
          f"(default template) ===")
    r = open_bug(failed_s["id"])
    check(bool(r.get("bug_id")), f"bug created (bug_id={r.get('bug_id')})")
    if not r.get("bug_id"):
        print("    response:", r); return None
    bid = r["bug_id"]; created_bug_ids.add(bid)

    b = get_bug(bid)
    title = b["title"]
    check(title.startswith("[注册]") or title.startswith("[登录]")
          or title.startswith("[忘记密码]") or title.startswith("[游客]"),
          f"title starts with [module]: {title!r}")
    check("[Auto]" not in title, "title has NO [Auto]")
    check("(run #" not in title, "title has NO (run #)")
    check(not re.search(r"SIT-TC-WEB-AUTH-\d+\s+\w", title),
          "title has NO full SIT-TC-WEB-AUTH-XXX prefix in scenario name part")
    check("用例未通过" in title or "Failed" in title,
          "title indicates expectation not met")

    assigned = (b.get("assignedTo") or {}).get("account")
    check(assigned == "wangyifan", f"assignedTo=wangyifan (got {assigned!r})")

    steps = b["steps"]
    for sec in ("缺陷概述", "测试环境", "重现步骤", "错误信息",
                "API 错误", "截图"):
        check(sec in steps, f"body has '{sec}' section")
    check(re.search(r"<li><code>(Given|When|Then|And)\s", steps) is not None,
          "body has Gherkin step lines extracted from .feature")
    http_imgs = re.findall(r'<img[^>]+src="(http://[^"]+)"', steps)
    check(len(http_imgs) >= 1,
          f"body has at least 1 HTTP img URL (found {len(http_imgs)})")

    # Verify the static URL actually serves the image
    if http_imgs:
        try:
            head = requests.get(http_imgs[0], timeout=8)
            check(head.status_code == 200 and head.content[:4] == b"\x89PNG",
                  f"first img URL serves a valid PNG ({head.status_code}, "
                  f"{len(head.content)} bytes)")
        except Exception as e:
            check(False, f"first img URL fetch failed: {e}")
    return bid


def case2_idempotent_same_title(failed_s, first_bug_id):
    print(f"\n=== CASE 2: re-open with DEFAULT title — should dedup to "
          f"existing bug {first_bug_id} ===")
    r = open_bug(failed_s["id"])
    check(r.get("already_opened") is True,
          "response includes already_opened=true")
    check(r.get("bug_id") == first_bug_id,
          f"returned bug_id is the existing one ({first_bug_id})")


def case3_different_title_creates_new(failed_s):
    print(f"\n=== CASE 3: open with DIFFERENT title — should create NEW bug ===")
    new_title = "[E2E self-test by claude] different title creates a new bug"
    r = open_bug(failed_s["id"], title=new_title)
    check(bool(r.get("bug_id")) and not r.get("already_opened"),
          f"new bug created (bug_id={r.get('bug_id')})")
    if r.get("bug_id"):
        created_bug_ids.add(r["bug_id"])
        b = get_bug(r["bug_id"])
        check(b["title"] == new_title,
              f"title preserved as submitted: {b['title']!r}")
    return r.get("bug_id")


def case4_passed_scenario(passed_s):
    print(f"\n=== CASE 4: open bug on PASSED scenario {passed_s['id']} ===")
    r = open_bug(passed_s["id"])
    check(bool(r.get("bug_id")),
          f"bug created on PASSED scenario (bug_id={r.get('bug_id')})")
    if r.get("bug_id"):
        created_bug_ids.add(r["bug_id"])
        b = get_bug(r["bug_id"])
        check("待跟进" in b["title"] or "Watch" in b["title"],
              f"PASSED-scenario title uses 'Watch' wording: {b['title']!r}")


def case5_multibug_count_via_api(failed_s):
    print(f"\n=== CASE 5: confirm scenario now has multiple bugs visible in "
          f"/api/runs ===")
    rid = failed_s["run_id"] if "run_id" in failed_s else None
    if not rid:
        # scenario has no run_id field in our dict — fall back via DB
        c = sqlite3.connect(DB_PATH)
        rid = c.execute("SELECT run_id FROM test_scenarios WHERE id=?",
                        (failed_s["id"],)).fetchone()[0]
        c.close()
    run = requests.get(f"{DASH}/api/runs/{rid}", timeout=10).json()
    s = next(x for x in run["scenarios"] if x["id"] == failed_s["id"])
    bugs = s.get("bugs") or []
    check(len(bugs) >= 2,
          f"scenario has >=2 bugs in API response (got {len(bugs)})")
    statuses = [b.get("status") for b in bugs]
    check(all(s in ("active", "resolved", "closed", "unknown")
              for s in statuses),
          f"every bug has a recognised status: {statuses}")


def cleanup():
    print(f"\n=== CLEANUP: delete {len(created_bug_ids)} test bug(s) + "
          f"reset DB ===")
    for bid in sorted(created_bug_ids):
        r = requests.delete(f"{ZENTAO}/api.php/v1/bugs/{bid}",
                            headers=H_TOK, timeout=15)
        print(f"  ZenTao DELETE bug {bid}: {r.status_code}")
    c = sqlite3.connect(DB_PATH)
    n = c.execute("DELETE FROM scenario_bugs WHERE zentao_bug_id IN "
                  "(" + ",".join(str(x) for x in created_bug_ids) + ")"
                  ).rowcount if created_bug_ids else 0
    c.commit(); c.close()
    print(f"  scenario_bugs rows deleted: {n}")

    # Verify ZenTao is back to 0 bugs by wangyifan
    bugs = requests.get(
        f"{ZENTAO}/api.php/v1/products/146/bugs?limit=50",
        headers=H_TOK, timeout=15).json()
    mine = [b for b in bugs.get("bugs", [])
            if (b.get("openedBy") or {}).get("account") == "wangyifan"]
    print(f"  bugs left by wangyifan in product 146: {len(mine)}")
    if mine:
        for b in mine:
            print(f"    ! left behind: {b['id']} {b['title'][:70]}")


def summarize():
    print("\n" + "=" * 60)
    n_pass = sum(1 for ok, _ in results if ok)
    n_fail = len(results) - n_pass
    print(f"SUMMARY: {n_pass}/{len(results)} checks passed, {n_fail} failed")
    if n_fail:
        print("\nFAILED checks:")
        for ok, m in results:
            if not ok:
                print(f"  - {m}")
    return n_fail == 0


def main():
    failed_s, passed_s = pick_scenarios()
    print(f"failed scenario picked: id={failed_s['id']} name={failed_s['name'][:60]}")
    print(f"passed scenario picked: id={passed_s['id']} name={passed_s['name'][:60]}")

    bid1 = case1_failed_scenario_default_template(failed_s)
    if bid1:
        case2_idempotent_same_title(failed_s, bid1)
    case3_different_title_creates_new(failed_s)
    if passed_s:
        case4_passed_scenario(passed_s)
    case5_multibug_count_via_api(failed_s)

    cleanup()
    ok = summarize()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
