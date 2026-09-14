"""API smoke tests for the 西九 public website.

This is the L0 layer of the API test pyramid:
  L0  smoke         — does the endpoint respond? non-5xx? gate behaves?  ← here
  L1  contract      — response shape matches spec                            (todo)
  L2  functional    — business behavior end-to-end (login → token → use)    (todo)
  L3  integration   — multi-step user journeys (cart → checkout)             (todo)

One test per endpoint via pytest parametrize, named by endpoint.name so
the pytest output reads like a status board.

Verdict rules (matches the dashboard's status pill):
  up        actual status in expected_status AND latency <= slow_ms
  degraded  actual status in expected_status BUT latency > slow_ms
  down      anything else (wrong status, timeout, network error, 5xx)
"""
from __future__ import annotations

import time
from typing import Any

import pytest
import requests


def _verdict(actual: int | None, expected: list[int], latency_ms: float, slow_ms: float) -> str:
    if actual is None:
        return "down"
    if actual not in expected:
        return "down"
    if latency_ms > slow_ms:
        return "degraded"
    return "up"


def _body_says_error(resp) -> str | None:
    """Detect the '200 OK but body says it failed' pattern. Returns the
    error reason string if the JSON envelope reports a non-success state,
    or None if the response is fine / not JSON / no envelope."""
    try:
        body = resp.json()
    except Exception:
        return None
    if not isinstance(body, dict):
        return None
    errcode = body.get("errcode")
    success = body.get("success")
    # success=False is the strongest signal; errcode != "0000" is the
    # other side of the same envelope.
    if success is False:
        return f"body.success=false (errcode={errcode!r}, msg={str(body.get('msg', ''))[:120]!r})"
    if errcode is not None and errcode != "0000" and errcode != 0:
        # Some endpoints (auth-required called anonymously) legitimately
        # return non-0000; only treat as error when status would've been 200.
        if resp.status_code == 200:
            return f"body.errcode={errcode!r}"
    return None


def _ids(endpoints: list[dict[str, Any]]) -> list[str]:
    return [ep["name"] for ep in endpoints]


@pytest.fixture(scope="session")
def wk_endpoints(endpoints_registry: dict[str, Any]) -> list[dict[str, Any]]:
    return endpoints_registry["endpoints"]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize test_endpoint with one case per registered endpoint."""
    if "endpoint" not in metafunc.fixturenames:
        return
    # We need to read the YAML here too (fixture chain can't run at collection time).
    from pathlib import Path
    import yaml
    data_path = Path(__file__).resolve().parent.parent / "data" / "wk_endpoints.yml"
    registry = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    eps = registry["endpoints"]
    metafunc.parametrize("endpoint", eps, ids=_ids(eps))


def test_endpoint(
    endpoint: dict[str, Any],
    base_url: str,
    http: requests.Session,
    smoke_thresholds: dict[str, float],
    smoke_results,
    endpoints_registry: dict[str, Any],
) -> None:
    method = endpoint["method"].upper()
    url = base_url + endpoint["path"]
    expected = list(endpoint["expected_status"])
    slow_ms = smoke_thresholds["slow_ms"]
    timeout_s = smoke_thresholds["timeout_s"]

    actual: int | None = None
    latency_ms: float = 0.0
    error: str | None = None

    body_err: str | None = None
    t0 = time.perf_counter()
    try:
        resp = http.request(method, url, timeout=timeout_s, allow_redirects=False)
        actual = resp.status_code
        # Catch "200 OK but body says failed" — only matters for anonymously-OK
        # endpoints; auth-required ones that we expect to 401 don't have this
        # ambiguity because the status itself is the signal.
        if not endpoint["auth_required"] and actual == 200:
            body_err = _body_says_error(resp)
    except requests.RequestException as exc:
        error = type(exc).__name__
    finally:
        latency_ms = (time.perf_counter() - t0) * 1000.0

    status = _verdict(actual, expected, latency_ms, slow_ms)
    # body_err is captured for transparency (shown in dashboard) but does NOT
    # change the smoke verdict — "200 + errcode 1101" usually means our
    # GET-with-no-body doesn't satisfy the endpoint's input contract, which
    # is the L1 contract layer's job to validate, not smoke's. Smoke only
    # cares "is the service responding at all".

    smoke_results.record(
        project=endpoints_registry["project"],
        website_url=endpoints_registry["website_url"],
        name=endpoint["name"],
        path=endpoint["path"],
        method=method,
        auth_required=endpoint["auth_required"],
        expected_status=expected,
        actual_status_code=actual,
        latency_ms=round(latency_ms, 1),
        status=status,
        group=endpoint.get("group", ""),
        notes=endpoint.get("notes", ""),
        error=error,
        body_warning=body_err,   # surfaced in dashboard as a secondary signal
    )

    # Assert the smoke verdict — "down" fails, "degraded" passes but logs.
    if status == "down":
        msg = (
            f"endpoint {endpoint['name']} returned {actual} "
            f"(expected one of {expected}); error={error}; latency={latency_ms:.0f}ms"
        )
        pytest.fail(msg)
