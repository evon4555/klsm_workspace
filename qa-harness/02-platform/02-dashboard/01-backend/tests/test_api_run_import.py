import importlib
import sys
from datetime import datetime, timedelta, timezone


def test_api_import_creates_visible_run_with_case_ids(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard-api-import.db"
    monkeypatch.setenv("QA_DASHBOARD_DB_PATH", str(db_path))
    sys.modules.pop("main", None)
    sys.modules.pop("database", None)
    main = importlib.import_module("main")

    try:
        main.init_db()
        started = datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc)
        request = main.ApiRunImportRequest(
            project="west-kowloon",
            env="sit",
            run_token="pytest-123",
            started_at=started,
            finished_at=started + timedelta(seconds=10),
            tests=[
                main.ApiTestResultImport(
                    case_id="API-SMOKE::GET-CAPTCHA",
                    name="GET captcha",
                    layer="api_smoke",
                    status="passed",
                    duration_s=0.25,
                    source="api_smoke/test_wk_smoke.py::test_endpoint[get-captcha]",
                ),
                main.ApiTestResultImport(
                    case_id="API-CONTRACT::MEMBER",
                    name="Member contract",
                    layer="api_contract",
                    status="skipped",
                    error_msg="authentication unavailable",
                ),
            ],
        )

        imported = main.import_api_run(request)
        duplicate = main.import_api_run(request)
        history = main.list_runs(project="west-kowloon")
        detail = main.get_run_detail(imported["id"])

        assert imported["imported"] is True
        assert duplicate["imported"] is False
        assert len(history) == 1
        assert history[0]["run_kind"] == "api"
        assert history[0]["total"] == 2
        assert history[0]["passed"] == 1
        assert history[0]["skipped"] == 1
        assert [row["case_id"] for row in detail["scenarios"]] == [
            "API-SMOKE::GET-CAPTCHA",
            "API-CONTRACT::MEMBER",
        ]
        assert [row["automation_type"] for row in detail["scenarios"]] == ["API", "API"]
        assert all(row["automation_location"] is None for row in detail["scenarios"])
    finally:
        database = sys.modules.get("database")
        if database is not None:
            database.engine.dispose()
        sys.modules.pop("main", None)
        sys.modules.pop("database", None)
