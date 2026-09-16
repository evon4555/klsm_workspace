"""Application-boundary contracts for the Dashboard's domain routers.

These are not product/SIT API tests. They call the real FastAPI routes while
replacing external services, subprocesses, databases, and project files with
controlled test doubles.
"""

from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import api_monitor, observability, package_health, performance, zentao


def _client(router) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _configure_performance(tmp_path: Path, metrics_config=None) -> None:
    performance.configure_router(
        project_key=lambda project: project,
        automation_paths=lambda project: {"evidence_root": tmp_path},
        workspace_root=tmp_path,
        metrics_client_instance=SimpleNamespace(),
        metrics_config_instance=metrics_config
        or SimpleNamespace(grafana_dashboard_uid=""),
        perf_artifact_prefix=tmp_path / "perf_latest",
        perf_log_limit=200,
        perf_state_ref=_idle_perf_state(),
        as_float=lambda value: float(value or 0),
        as_int=lambda value: int(float(value or 0)),
    )


def _configure_api_monitor(tmp_path: Path) -> None:
    api_monitor.configure_router(
        project_key=lambda project: project,
        project_match_values=lambda project: {project},
        automation_paths=lambda project: {
            "artifacts_root": tmp_path,
            "automation_root": tmp_path,
        },
    )


def _configure_zentao() -> None:
    zentao.configure_router(
        zt_session=lambda: None,
        zentao_token=lambda: None,
        zentao_refresh_configured=lambda: False,
        token_status_provider=lambda: {},
        project_config=lambda project: {
            "key": project,
            "zentaoProductId": None,
            "zentaoExecutionId": None,
        },
        project_key=lambda project: project,
        as_float=lambda value: float(value or 0),
    )


def _configure_package_health(tmp_path: Path) -> None:
    package_health.configure_router(
        package_scanner_module=None,
        workspace_root=tmp_path,
        repo_root=tmp_path,
        project_key=lambda project: project,
        project_workspace_root=lambda project: tmp_path / project,
        case_id_from_scenario_fields=lambda name, tags: None,
    )


def _idle_perf_state(project=None) -> dict:
    return {
        "status": "idle",
        "project": project,
        "run_id": None,
        "pid": None,
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "config": None,
        "artifacts_prefix": "unused",
        "logs": [],
        "error": None,
        "total_requests": 0,
        "total_failures": 0,
        "error_rate": 0,
    }


def test_performance_status_contract_for_selected_project(monkeypatch, tmp_path):
    _configure_performance(tmp_path)
    artifact_prefix = tmp_path / "performance" / "latest" / "perf_latest"
    monkeypatch.setattr(performance, "_project_key", lambda project: project)
    monkeypatch.setattr(performance, "_perf_state_dict", lambda: _idle_perf_state())
    monkeypatch.setattr(performance, "_perf_artifact_prefix", lambda project: artifact_prefix)

    response = _client(performance.router).get(
        "/api/perf/status", params={"project": "west-kowloon"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "idle"
    assert payload["project"] == "west-kowloon"
    assert payload["artifacts_prefix"] == str(artifact_prefix)
    assert payload["logs"] == []
    assert payload["total_requests"] == 0
    assert payload["total_failures"] == 0
    assert payload["error_rate"] == 0


def test_performance_status_isolated_between_projects(monkeypatch, tmp_path):
    _configure_performance(tmp_path)
    artifact_prefix = tmp_path / "perf_latest"
    monkeypatch.setattr(performance, "_project_key", lambda project: project)
    monkeypatch.setattr(
        performance,
        "_perf_state_dict",
        lambda: {**_idle_perf_state("standard product"), "status": "running", "pid": 123},
    )
    monkeypatch.setattr(performance, "_perf_artifact_prefix", lambda project: artifact_prefix)

    payload = _client(performance.router).get(
        "/api/perf/status", params={"project": "west-kowloon"}
    ).json()

    assert payload["status"] == "idle"
    assert payload["project"] == "west-kowloon"
    assert payload["pid"] is None
    assert payload["message"] == "No performance run is active for this project."


def test_performance_grafana_empty_configuration_contract(monkeypatch, tmp_path):
    _configure_performance(
        tmp_path,
        metrics_config=SimpleNamespace(grafana_dashboard_uid=""),
    )

    response = _client(performance.router).get("/api/perf/grafana/panels")

    assert response.status_code == 200
    assert response.json() == {
        "panels": [],
        "dashboard_url": "",
        "message": "GRAFANA_DASHBOARD_UID not configured",
    }


def test_observability_status_contract_without_real_services(monkeypatch):
    class MetricsStub:
        async def check_pyroscope(self):
            return True

        async def check_loki(self):
            return False

        async def check_toxiproxy(self):
            return True

    observability.configure_router(
        metrics_client_instance=MetricsStub(),
        metrics_config_instance=SimpleNamespace(
            pyroscope_url="http://pyroscope.test",
            loki_url="http://loki.test",
            toxiproxy_url="http://toxiproxy.test",
        ),
    )

    response = _client(observability.router).get("/api/observability/status")

    assert response.status_code == 200
    assert response.json() == {
        "pyroscope": {"connected": True, "url": "http://pyroscope.test"},
        "loki": {"connected": False, "url": "http://loki.test"},
        "toxiproxy": {"connected": True, "url": "http://toxiproxy.test"},
    }


def test_api_monitor_status_isolated_between_projects(monkeypatch, tmp_path):
    _configure_api_monitor(tmp_path)
    monkeypatch.setattr(api_monitor, "_project_key", lambda project: project)
    monkeypatch.setattr(
        api_monitor,
        "_api_smoke_state_dict",
        lambda: {
            "running": True,
            "status": "running",
            "project": "standard product",
            "started_at": "2026-08-06T00:00:00",
            "finished_at": None,
            "exit_code": None,
            "env": "sit",
            "command": "pytest",
            "log": ["running"],
            "error": None,
            "artifact_updated": False,
        },
    )

    response = _client(api_monitor.router).get(
        "/api/api-monitor/run-smoke", params={"project": "west-kowloon"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["running"] is False
    assert payload["status"] == "idle"
    assert payload["project"] == "west-kowloon"
    assert payload["log"] == []
    assert payload["artifact_updated"] is False


def test_api_monitor_empty_artifact_contract(monkeypatch, tmp_path):
    class DatabaseStub:
        def close(self):
            return None

    _configure_api_monitor(tmp_path)
    missing_path = tmp_path / "api_smoke" / "latest.json"
    monkeypatch.setattr(api_monitor, "_project_key", lambda project: project)
    monkeypatch.setattr(api_monitor, "_api_smoke_path", lambda project: missing_path)
    monkeypatch.setattr(api_monitor, "get_db", lambda: DatabaseStub())
    monkeypatch.setattr(
        api_monitor,
        "_ingest_latest_api_smoke_json",
        lambda db, project: None,
    )

    response = _client(api_monitor.router).get(
        "/api/api-monitor/endpoints", params={"project": "west-kowloon"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"] == "west-kowloon"
    assert payload["projectKey"] == "west-kowloon"
    assert payload["ran_at"] is None
    assert payload["summary"] == {
        "total": 0,
        "up": 0,
        "degraded": 0,
        "down": 0,
        "skipped": 0,
    }
    assert payload["endpoints"] == []
    assert "No smoke run on record yet" in payload["_note"]


def test_zentao_auth_contract_never_returns_token_value(monkeypatch):
    _configure_zentao()
    monkeypatch.setattr(zentao, "_zentao_token", lambda: "secret-token-value")
    monkeypatch.setattr(zentao, "_zentao_refresh_configured", lambda: True)
    monkeypatch.setattr(
        zentao,
        "_token_status_provider",
        lambda: {
            "tokenSource": "auto-refresh",
            "lastRefreshAt": "2026-08-06T00:00:00",
            "lastRefreshError": None,
        },
    )

    response = _client(zentao.router).get("/api/zentao/auth-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["hasToken"] is True
    assert payload["autoRefreshConfigured"] is True
    assert payload["tokenSource"] == "auto-refresh"
    assert "secret-token-value" not in response.text


def test_zentao_unmapped_project_dashboard_contract(monkeypatch):
    _configure_zentao()
    monkeypatch.setattr(
        zentao,
        "_project_config",
        lambda project: {
            "key": "jockey club",
            "zentaoProductId": None,
            "zentaoExecutionId": None,
        },
    )

    response = _client(zentao.router).get(
        "/api/zentao/dashboard", params={"project": "jockey club"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["iterations"] == []
    assert payload["requirementsByIter"] == {}
    assert payload["modules"] == []
    assert payload["qaThroughput"] == []
    assert payload["autoTrend"] == []
    assert payload["meta"]["project"] == "jockey club"
    assert payload["meta"]["scope"] == "unmapped-project"
    assert "No ZenTao product or execution is mapped" in payload["meta"]["error"]


def test_zentao_mapped_execution_is_default_not_the_only_option(monkeypatch):
    _configure_zentao()
    monkeypatch.setattr(
        zentao,
        "_project_config",
        lambda project: {
            "key": "west-kowloon",
            "zentaoProductId": 146,
            "zentaoExecutionId": 614,
        },
    )
    monkeypatch.setattr(zentao, "_zentao_token", lambda: "test-token")
    monkeypatch.setattr(zentao, "_ZT_DASHBOARD_CACHE", {})

    def fake_get(path, token, params=None, critical=False):
        if path == "/executions" and (params or {}).get("status") == "doing":
            return {
                "executions": [
                    {"id": 700, "name": "Another active project", "status": "doing"},
                    {"id": 614, "name": "International Website V1.0", "status": "doing"},
                ]
            }
        if path == "/executions" and (params or {}).get("status") == "wait":
            return {"executions": []}
        if path == "/testtasks":
            return {"data": []}
        if path.startswith("/products/"):
            return {"data": []}
        if path.startswith("/executions/"):
            return {"data": []}
        return {}

    monkeypatch.setattr(zentao, "_zt_get", fake_get)

    response = _client(zentao.router).get(
        "/api/zentao/dashboard",
        params={"project": "west-kowloon", "max_iterations": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["iterations"]] == ["iter-614"]
    assert [item["id"] for item in payload["moreExecutions"]] == ["iter-700"]
    assert payload["meta"]["executionId"] == 614
    assert payload["meta"]["scope"] == "all-active-executions"


def test_package_health_list_contract(monkeypatch, tmp_path):
    class ScannerStub:
        STAGE_DEFS = [{"id": "01-input", "label": "Input"}]

        @staticmethod
        def scan_workspace(workspace_root: Path, project: str):
            assert project == "west-kowloon"
            return [SimpleNamespace(id="package-1")]

        @staticmethod
        def to_jsonable(package):
            return {"id": package.id, "qa_readiness": "in-progress"}

    _configure_package_health(tmp_path)
    monkeypatch.setattr(package_health, "package_scanner", ScannerStub())
    monkeypatch.setattr(package_health, "_workspace_root", tmp_path)

    response = _client(package_health.router).get(
        "/api/quality-system/packages", params={"project": "west-kowloon"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"] == "west-kowloon"
    assert payload["package_count"] == 1
    assert payload["stage_defs"] == [{"id": "01-input", "label": "Input"}]
    assert payload["packages"] == [
        {"id": "package-1", "qa_readiness": "in-progress"}
    ]
    assert payload["scanned_at"]


def test_package_health_missing_scanner_contract(monkeypatch, tmp_path):
    _configure_package_health(tmp_path)
    monkeypatch.setattr(package_health, "package_scanner", None)

    response = _client(package_health.router).get(
        "/api/quality-system/packages", params={"project": "west-kowloon"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "error": "package_scanner not available",
        "packages": [],
    }
