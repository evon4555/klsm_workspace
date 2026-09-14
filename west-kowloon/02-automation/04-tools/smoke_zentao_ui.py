"""smoke_zentao_ui.py — Playwright UI smoke for the ZenTao Integration page.

Spins up headless Chromium, navigates to the dev server, clicks through every
interactive element on the ZenTao Integration page, and saves screenshots
so visual regressions can be reviewed. Designed to catch the bug classes that
backend contract smoke can't:
    - state-edge bugs (initial mount, empty data)
    - modal open/close logic
    - clickable elements actually firing
    - layout glitches (via screenshots)

Run AFTER any change to:
    02-platform/02-dashboard/02-frontend/src/pages/ZenTaoDashboardPage.jsx
    02-platform/02-dashboard/02-frontend/src/App.jsx (menu wiring)
    backend /api/zentao/* response shape

Invocation:
    cd D:\\Workspace\\west-kowloon\\02-automation
    D:\\Workspace\\qa-harness\\02-platform\\01-automation\\.venv\\Scripts\\python.exe 04-tools\\smoke_zentao_ui.py

Pre-flight: both ports must be up (8002 backend, 5174 frontend).
Exits 0 on all-green, non-zero on any failure.
"""
from __future__ import annotations

import socket
import sys
from datetime import datetime
from pathlib import Path

FRONTEND = "http://127.0.0.1:5174"
HERE = Path(__file__).resolve().parent
EVIDENCE_ROOT = HERE.parent.parent / "evidence" / "zentao_ui_smoke"

results: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {name}" + (f"  ({detail})" if detail else ""))
    results.append((name, passed, detail))


def note(name: str, detail: str = "") -> None:
    """Soft check — print INFO, don't affect pass/fail tally. Used when a
    branch is unreachable in current data (e.g., heatmap all-zero, no
    pinned-exec dropdown items)."""
    print(f"  [SKIP] {name}" + (f"  ({detail})" if detail else ""))


def visible_modal_title(page) -> str:
    """Return the title text of the currently-open modal. Antd v5 keeps
    ALL Modal nodes in the DOM and toggles `display:none` on the wrap; we
    have to scope by visibility, otherwise `.ant-modal-title.first` picks
    a stale (closed) modal."""
    for w in page.locator(".ant-modal-wrap").all():
        try:
            if w.is_visible():
                return w.locator(".ant-modal-title").first.inner_text()
        except Exception:                                              # noqa: BLE001
            continue
    return ""


def close_modal(page):
    """Close any open Antd modal reliably. Multiple Modals are rendered in
    the DOM at once (each with its own ant-modal-wrap); we close the
    currently-visible one(s), then wait until ALL wraps are hidden so the
    next click isn't intercepted."""
    visible_close = page.locator(".ant-modal-close").filter(
        has_text="" if False else None)
    # The visible close button (others are display:none). Click whichever is.
    for btn in page.locator(".ant-modal-close").all():
        try:
            if btn.is_visible():
                btn.click(timeout=2000)
        except Exception:                                              # noqa: BLE001
            pass
    # Wait until no modal-wrap is visible.
    for _ in range(20):
        any_visible = False
        for w in page.locator(".ant-modal-wrap").all():
            try:
                if w.is_visible():
                    any_visible = True
                    break
            except Exception:                                          # noqa: BLE001
                pass
        if not any_visible:
            return
        page.wait_for_timeout(100)


def port_up(port: int, timeout: float = 1.0) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except OSError:
        return False


def main() -> int:
    print(f"\n=== ZenTao Integration · UI smoke ===\n")

    if not port_up(5174):
        check("frontend up on :5174", False, "start vite dev first")
        return summarize(None)
    if not port_up(8002):
        check("backend up on :8002", False, "start uvicorn first")
        return summarize(None)
    check("ports up", True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    shot_dir = EVIDENCE_ROOT / ts
    shot_dir.mkdir(parents=True, exist_ok=True)
    print(f"DEBUG: shot_dir = {shot_dir}", flush=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()
        # Capture JS console errors so we can diagnose silent React crashes.
        console_errors: list[str] = []
        page.on("pageerror", lambda e: console_errors.append(str(e)))
        page.on("console", lambda m: (
            console_errors.append(f"[{m.type}] {m.text}")
            if m.type in ("error",) else None
        ))
        # Capture detail-endpoint requests so we can verify the 刷新 button
        # fans out a `refresh=true` call to currently-pinned lazy execs.
        detail_requests: list[str] = []
        all_zentao_requests: list[str] = []
        def _on_req(req):
            if "/api/zentao/" in req.url:
                all_zentao_requests.append(req.url)
            if "/api/zentao/execution/" in req.url and "/detail" in req.url:
                detail_requests.append(req.url)
        page.on("request", _on_req)

        try:
            # ─── Step 1: open frontend ─────────────────────────────────────
            page.goto(FRONTEND, wait_until="domcontentloaded", timeout=30000)
            check("page loaded", True)

            # ─── Step 2: click the ZenTao Integration menu item ────────────
            menu = page.get_by_role("menuitem", name="ZenTao Integration")
            check("menu item visible", menu.is_visible())
            menu.click()

            # Wait for the page title to appear (10s cap; first hit may be cold)
            page.wait_for_selector("text=ZenTao Integration", timeout=15000)
            check("page header renders", True)

            # Wait for iteration cards (first card has 'Phase' equiv badge)
            page.wait_for_selector("text=EXEC-", timeout=60000)
            check("iteration cards loaded", True)

            page.screenshot(path=str(shot_dir / "01_loaded.png"), full_page=True)

            # ─── Step 3: count visible iteration cards ─────────────────────
            # Only the iteration cards are hoverable (other cards aren't).
            # This is more stable than text-matching "EXEC-".
            cards = page.locator(".ant-card-hoverable").all()
            visible_count = len(cards)
            check("visible iteration cards == 4", visible_count == 4,
                  f"got {visible_count}")

            # ─── Step 4: 测试用例 tag click → caseModal opens ──────────────
            # First requirement of the first iter has DEMO data; the 测试用例
            # cyan tag should be present and clickable.
            req_table = page.locator("text=需求明细").first
            check("requirements table visible", req_table.is_visible())

            # Demo first-row should show a 60-count case tag with [DEMO] marker
            demo_tag = page.locator("text=DEMO").first
            if demo_tag.is_visible():
                check("DEMO badge visible on first req", True)
            else:
                check("DEMO badge visible on first req", False,
                      "demo data missing — first req may have real cases")

            # Click first row's case-count tag (cyan tag with N + arrow icon)
            # Use the first ant-tag with cursor:pointer that has a number
            cases_tag = page.locator('.ant-tag').filter(has_text="60").first
            if cases_tag.count() > 0:
                cases_tag.click()
                page.wait_for_selector(".ant-modal-content", timeout=5000)
                modal_title = page.locator(".ant-modal-title").first
                title_text = modal_title.inner_text()
                check("case modal title mentions 测试用例",
                      "测试用例" in title_text, title_text[:50])
                # Count list items
                items = page.locator(".ant-modal-body").locator("div").filter(
                    has_text="DEMO").all()
                check("case modal lists items",
                      len(items) >= 1, f"got {len(items)} item divs")
                page.screenshot(path=str(shot_dir / "02_case_modal.png"))
                # Close modal via Escape
                close_modal(page)
            else:
                check("case modal: 60-count tag found", False,
                      "no demo data — skipping this step")

            # ─── Step 5: Pass chip click → bucketed modal ──────────────────
            pass_chip = page.get_by_text("Pass(5)").first
            if pass_chip.count() > 0:
                pass_chip.click()
                page.wait_for_selector(".ant-modal-content", timeout=5000)
                title = visible_modal_title(page)
                check("pass chip → modal title mentions Pass",
                      "Pass" in title, title[:60])
                page.screenshot(path=str(shot_dir / "03_pass_chip_modal.png"))
                close_modal(page)
            else:
                check("Pass(5) chip clickable", False,
                      "chip not found — demo data missing or label changed")

            # ─── Step 6: 需求状态分布 legend click → modal ─────────────────
            # Use data-testid for deterministic selection. Find a row whose
            # data-value > 0 (the others have no onClick handler).
            rows = page.locator("[data-testid='donut-legend-row']").all()
            clickable_rows = [r for r in rows
                              if int(r.get_attribute("data-value") or "0") > 0]
            if not clickable_rows:
                note("donut legend click → modal",
                     "selected exec has all-zero storyByStatus, skipping")
            else:
                page.screenshot(path=str(shot_dir / "04a_pre_donut.png"))
                row = clickable_rows[0]
                label = row.get_attribute("data-label")
                value = row.get_attribute("data-value")
                print(f"DEBUG: clicking donut row label={label} value={value} "
                      f"({len(clickable_rows)} clickable rows total)", flush=True)
                try:
                    row.click(timeout=3000, force=True)
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(shot_dir / "04b_post_donut_click.png"))
                    page.wait_for_selector(".ant-modal-wrap:not([style*='display: none']) .ant-modal-content", timeout=3000)
                    title = visible_modal_title(page)
                    check(f"donut legend `{label}` opens modal",
                          "需求状态" in title or label in title, title[:60])
                    page.screenshot(path=str(shot_dir / "04_donut_modal.png"))
                    close_modal(page)
                except Exception as e:                                 # noqa: BLE001
                    check(f"donut legend `{label}` opens modal", False,
                          str(e)[:60])
                    if console_errors:
                        print(f"DEBUG: console errors so far: {console_errors[-3:]}",
                              flush=True)

            # ─── Step 7: bug-overview matrix structure ────────────────────
            # The 缺陷概览 panel always renders the 4×3 BugMatrix for the
            # currently-selected execution, regardless of bug count: expect
            # 12 data cells + 4 row-totals + 3 col-totals + 1 grand-total.
            cells_count = len(page.locator("[data-testid='heatmap-cell']").all())
            rt_count = len(page.locator("[data-testid='row-total']").all())
            ct_count = len(page.locator("[data-testid='col-total']").all())
            grand_count = len(page.locator("[data-testid='grand-total']").all())
            check("bug-matrix structure (12+4+3+1)",
                  cells_count == 12 and rt_count == 4
                  and ct_count == 3 and grand_count == 1,
                  f"cells={cells_count} row={rt_count} "
                  f"col={ct_count} grand={grand_count}")

            # Step 7b: cell click only fires when matrix has data. For the
            # first iter this is usually zero — the meaningful click test
            # runs in Step 10 after 国际版 is loaded (has 80+ bugs).
            all_cells = page.locator("[data-testid='heatmap-cell']").all()
            non_zero = [c for c in all_cells
                        if int(c.get_attribute("data-count") or "0") > 0]
            if not non_zero:
                note("heatmap cell click (first iter)",
                     "first iter all-zero — will retest after 国际版 load")
            else:
                cell = non_zero[0]
                sev = cell.get_attribute("data-sev")
                status_col = cell.get_attribute("data-status")
                try:
                    cell.click(timeout=3000)
                    page.wait_for_selector(".ant-modal-wrap:not([style*='display: none']) .ant-modal-content", timeout=3000)
                    title = visible_modal_title(page)
                    check(f"heatmap cell S{sev}/col{status_col} → modal",
                          True, title[:60])
                    page.screenshot(path=str(shot_dir / "05_heatmap_modal.png"))
                    close_modal(page)
                except Exception as e:                                 # noqa: BLE001
                    check(f"heatmap cell S{sev}/col{status_col} → modal",
                          False, str(e)[:60])

            # ─── Step 8: QA workload card click → qa modal ─────────────────
            qa_rows = page.locator("[data-testid='qa-workload-row']").all()
            check("QA workload card has rows", len(qa_rows) > 0,
                  f"{len(qa_rows)} QA rows")
            if qa_rows:
                qa_name = qa_rows[0].get_attribute("data-qa")
                try:
                    qa_rows[0].click(timeout=3000)
                    page.wait_for_selector(".ant-modal-wrap:not([style*='display: none']) .ant-modal-content", timeout=3000)
                    title = visible_modal_title(page)
                    check(f"QA `{qa_name}` row → modal",
                          "负责" in title, title[:60])
                    page.screenshot(path=str(shot_dir / "06_qa_modal.png"))
                    close_modal(page)
                except Exception as e:                                 # noqa: BLE001
                    check(f"QA `{qa_name}` row → modal", False, str(e)[:60])

            # ─── Step 9: dropdown search ───────────────────────────────────
            # Find the Select containing the "其他" placeholder; clicking its
            # search input opens the dropdown reliably (placeholder is occluded).
            select_search = page.locator(".ant-select", has=page.locator(
                ".ant-select-selection-placeholder", has_text="其他"))\
                .locator(".ant-select-selection-search-input").first
            if select_search.count() > 0:
                try:
                    select_search.click(timeout=3000)
                    page.wait_for_selector(".ant-select-dropdown", timeout=3000)
                    page.keyboard.type("国际版", delay=20)
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(shot_dir / "07_dropdown_search.png"))
                    option = page.locator(".ant-select-item-option")\
                        .filter(has_text="国际版").first
                    check("dropdown search '国际版' finds match",
                          option.count() > 0,
                          "exec '国际版官网V1.0' should be findable")
                    page.keyboard.press("Escape")
                except Exception as e:                                 # noqa: BLE001
                    check("dropdown search finds match", False, str(e)[:60])
            else:
                note("dropdown search", "all execs already visible, no dropdown")

            page.screenshot(path=str(shot_dir / "08_final.png"), full_page=True)

            # ─── Step 10: long-data layout (select 国际版 with 21 reqs) ────
            # Regression guard for the asymmetry bug — when the selected exec
            # has many requirements, the table must scroll internally (not
            # paginate) so the left card height stays close to the right
            # column. We assert the table scroll body is rendered AND there
            # is no .ant-pagination element.
            select_search = page.locator(".ant-select", has=page.locator(
                ".ant-select-selection-placeholder", has_text="其他"))\
                .locator(".ant-select-selection-search-input").first
            if select_search.count() > 0:
                try:
                    select_search.click(timeout=3000)
                    page.wait_for_selector(".ant-select-dropdown", timeout=3000)
                    page.keyboard.type("国际版", delay=20)
                    page.wait_for_timeout(500)
                    option = page.locator(".ant-select-item-option")\
                        .filter(has_text="国际版").first
                    if option.count() > 0:
                        option.click()
                        # Lazy-load + promote — backend cold path can take 8s+
                        page.wait_for_timeout(10000)
                        # Count actual table rows rendered (works for either
                        # half-width or full-width parens in the title text).
                        n_reqs = page.locator(".ant-table-row").count()
                        check("国际版 selected and loaded",
                              n_reqs > 10, f"rows={n_reqs}")
                        if n_reqs > 10:
                            # Must use scroll, not pagination
                            has_scroll = page.locator(".ant-table-body").count() > 0
                            has_pagination = page.locator(".ant-pagination").count() > 0
                            check("long-data table uses scroll (not pagination)",
                                  has_scroll and not has_pagination,
                                  f"scroll={has_scroll} pagination={has_pagination}")
                            page.screenshot(path=str(shot_dir / "09_long_data.png"),
                                            full_page=True)

                        # ─── Bug matrix on 国际版 (80+ active bugs) ────────
                        all_cells = page.locator("[data-testid='heatmap-cell']").all()
                        non_zero = [c for c in all_cells
                                    if int(c.get_attribute("data-count") or "0") > 0]
                        check("国际版 bug matrix has non-zero cells",
                              len(non_zero) > 0, f"non-zero cells: {len(non_zero)}")
                        if non_zero:
                            cell = non_zero[0]
                            sev = cell.get_attribute("data-sev")
                            sc = cell.get_attribute("data-status")
                            cnt = cell.get_attribute("data-count")
                            cell.click(timeout=3000)
                            page.wait_for_selector(
                                ".ant-modal-wrap:not([style*='display: none']) "
                                ".ant-modal-content", timeout=3000)
                            title = visible_modal_title(page)
                            check(f"国际版 heatmap S{sev}/col{sc} click → modal",
                                  ("S" in title and "·" in title) or "缺陷" in title,
                                  title[:60])
                            page.screenshot(path=str(shot_dir / "10_heatmap_cell_modal.png"))
                            close_modal(page)

                        # Row total click — find a non-zero row-total
                        row_totals = page.locator("[data-testid='row-total']").all()
                        nz_rows = [r for r in row_totals
                                   if (r.inner_text() or "0").strip().isdigit()
                                   and int(r.inner_text().strip()) > 0]
                        if nz_rows:
                            sev = nz_rows[0].get_attribute("data-sev")
                            nz_rows[0].click(timeout=3000)
                            page.wait_for_selector(
                                ".ant-modal-wrap:not([style*='display: none']) "
                                ".ant-modal-content", timeout=3000)
                            title = visible_modal_title(page)
                            check(f"row-total S{sev} · 全部 → modal",
                                  "全部" in title or "S" in title, title[:60])
                            page.screenshot(path=str(shot_dir / "11_row_total_modal.png"))
                            close_modal(page)

                        # Column total click — find a non-zero col-total
                        col_totals = page.locator("[data-testid='col-total']").all()
                        nz_cols = [c for c in col_totals
                                   if (c.inner_text() or "0").strip().isdigit()
                                   and int(c.inner_text().strip()) > 0]
                        if nz_cols:
                            sc = nz_cols[0].get_attribute("data-status")
                            nz_cols[0].click(timeout=3000)
                            page.wait_for_selector(
                                ".ant-modal-wrap:not([style*='display: none']) "
                                ".ant-modal-content", timeout=3000)
                            title = visible_modal_title(page)
                            check(f"col-total col{sc} → modal",
                                  "全部" in title, title[:60])
                            page.screenshot(path=str(shot_dir / "12_col_total_modal.png"))
                            close_modal(page)

                        # Grand total click — single element
                        grand = page.locator("[data-testid='grand-total']").first
                        if grand.count() > 0 and (grand.inner_text() or "0").strip().isdigit() \
                                and int(grand.inner_text().strip()) > 0:
                            grand.click(timeout=3000)
                            page.wait_for_selector(
                                ".ant-modal-wrap:not([style*='display: none']) "
                                ".ant-modal-content", timeout=3000)
                            title = visible_modal_title(page)
                            check("grand-total → 全部缺陷 modal",
                                  "全部缺陷" in title, title[:60])
                            page.screenshot(path=str(shot_dir / "13_grand_total_modal.png"))
                            close_modal(page)
                except Exception as e:                                 # noqa: BLE001
                    check("国际版 long-data scenario", False, str(e)[:60])

            # ─── Step 11: 刷新 must fan out to pinned lazy execs ───────────
            # By this point 国际版 (exec 614) is loaded via dropdown — it is a
            # pinned LAZY exec (not in top-N). When user clicks 刷新, the
            # dashboard endpoint refetches with refresh=true, but pinned-lazy
            # execs use a separate per-exec cache that the dashboard call does
            # NOT invalidate. The frontend must explicitly re-fetch them with
            # refresh=true. Verify the network call actually fires.
            try:
                # Snapshot ALL zentao request log so we can diff just post-click calls
                snap_detail = len(detail_requests)
                snap_all = len(all_zentao_requests)

                # Locate the 刷新 button (top-right of the page header)
                refresh_btn = page.get_by_role("button", name="刷新")
                if refresh_btn.count() == 0:
                    check("刷新 button visible", False, "not found")
                else:
                    refresh_btn.first.click(timeout=3000)
                    # Wait for dashboard cold refetch (~10s) + lazy fanout (~5s)
                    page.wait_for_timeout(15000)

                    new_all = all_zentao_requests[snap_all:]
                    new_calls = detail_requests[snap_detail:]
                    # Confirm dashboard refetch fired with refresh=true
                    dashboard_refresh_calls = [
                        u for u in new_all
                        if "/api/zentao/dashboard" in u and "refresh=true" in u
                    ]
                    check("刷新 fires /api/zentao/dashboard?refresh=true",
                          len(dashboard_refresh_calls) >= 1,
                          f"all post-click zentao calls={len(new_all)}; "
                          f"dashboard?refresh=true: {len(dashboard_refresh_calls)}")
                    # Confirm fanout to pinned 614
                    refresh_calls_to_614 = [
                        u for u in new_calls
                        if "/execution/614/detail" in u and "refresh=true" in u
                    ]
                    check("刷新 fans out /execution/614/detail?refresh=true",
                          len(refresh_calls_to_614) >= 1,
                          f"new detail calls={len(new_calls)}; "
                          f"614?refresh=true: {len(refresh_calls_to_614)}; "
                          f"sample new calls: {new_all[:3]}")
                    page.screenshot(path=str(shot_dir / "14_after_refresh.png"),
                                    full_page=True)
            except Exception as e:                                     # noqa: BLE001
                check("刷新 fan-out scenario", False, str(e)[:60])

        finally:
            browser.close()

    return summarize(shot_dir)


def summarize(shot_dir: Path | None) -> int:
    print()
    fails = [r for r in results if not r[1]]
    total = len(results)
    if shot_dir:
        print(f"screenshots → {shot_dir}")
    if fails:
        print(f"SUMMARY: {len(fails)}/{total} FAILED")
        for n, _, d in fails:
            # 'x' instead of ✗ — Windows GBK console can't print ✗
            print(f"  x {n}" + (f": {d}" if d else ""))
        return 1
    print(f"SUMMARY: {total}/{total} PASS — ZenTao UI smoke OK")
    return 0


if __name__ == "__main__":
    import traceback
    try:
        sys.exit(main())
    except Exception:                                                  # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)
