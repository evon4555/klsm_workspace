import importlib
import sys
from datetime import datetime, timedelta


def test_test_run_history_includes_api_and_excludes_performance(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard-history-test.db"
    monkeypatch.setenv("QA_DASHBOARD_DB_PATH", str(db_path))
    sys.modules.pop("main", None)
    sys.modules.pop("database", None)
    main = importlib.import_module("main")

    try:
        main.init_db()
        db = main.get_db()
        started_at = datetime(2026, 9, 16, 9, 0, 0)
        functional = main.TestRun(
            started_at=started_at,
            finished_at=started_at + timedelta(minutes=1),
            status="passed",
            env="sit",
            project_key="west-kowloon",
            run_kind="full",
            total=1,
            passed=1,
        )
        performance = main.TestRun(
            started_at=started_at + timedelta(hours=1),
            finished_at=started_at + timedelta(hours=1, minutes=1),
            status="failed",
            env="sit",
            project_key="west-kowloon",
            run_kind="performance",
            total=9,
            failed=9,
        )
        api = main.TestRun(
            started_at=started_at + timedelta(hours=2),
            finished_at=started_at + timedelta(hours=2, minutes=1),
            status="passed",
            env="sit",
            project_key="west-kowloon",
            run_kind="api",
            total=2,
            passed=2,
        )
        db.add_all([functional, performance, api])
        db.commit()
        functional_id = functional.id
        performance_id = performance.id
        api_id = api.id
        db.close()

        default_history = main.list_runs(project="west-kowloon")
        all_history = main.list_runs(project="west-kowloon", kind="all")

        assert [run["id"] for run in default_history] == [api_id, functional_id]
        assert {run["id"] for run in all_history} == {functional_id, performance_id, api_id}

        def fail_if_token_is_requested():
            raise AssertionError("ZenTao token lookup must be skipped when no bugs exist")

        monkeypatch.setattr(main, "_zentao_token", fail_if_token_is_requested)
        scenarios_without_bugs = [{"id": 1, "bugs": []}, {"id": 2, "bugs": None}]
        assert main._enrich_bug_statuses(scenarios_without_bugs) == scenarios_without_bugs
    finally:
        database = sys.modules.get("database")
        if database is not None:
            database.engine.dispose()
        sys.modules.pop("main", None)
        sys.modules.pop("database", None)
