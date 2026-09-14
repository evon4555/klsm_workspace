"""L1 contract tests — verify selected 西九 endpoints respond with the
declared JSON shape. Catches breaking schema changes without needing a
behavioural test.

Each target in schemas.CONTRACT_TARGETS becomes one parametrized test:
  - issues the live HTTP call
  - parses the response body
  - validates against the pydantic envelope/data model
  - asserts errcode == "0000"

Auth-required targets share the cookie jar from
07-artifacts/api_smoke/storage_state.json (saved by the crawler).
Run the crawler once to refresh that file when the cookie expires.
"""
from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from .schemas import CONTRACT_TARGETS


def _resolve_program_id(http, base_url: str) -> int:
    """Pull a real program id from the hot list — used for tests that
    take `programId` as a param. Cached per-session via the fixture below
    so we don't hammer the upstream."""
    r = http.post(
        base_url + "/thvendor/ticket/program/getHotProgramList.xhtml",
        json={"showSite": "PCrecList1"}, timeout=10,
    )
    body = r.json()
    items = body.get("data") or []
    if not items:
        pytest.skip("no hot programs available — cannot resolve a programId")
    return items[0]["id"]


@pytest.fixture(scope="session")
def hot_program_id(http, base_url) -> int:
    return _resolve_program_id(http, base_url)


@pytest.mark.parametrize("target", CONTRACT_TARGETS, ids=[t["name"] for t in CONTRACT_TARGETS])
def test_contract(
    target: dict[str, Any],
    base_url: str,
    http,
    request,
) -> None:
    # Only request authed_http when the target actually needs it, so that
    # anonymous-target tests don't get skipped when the session refresh
    # is in cooldown.
    session = request.getfixturevalue("authed_http") if target["auth"] else http
    url = base_url + target["path"]

    # Resolve query / body — supports static query, request_body, and
    # needs_program (inject fresh programId from hot list into either
    # query (query_template) or body (body_template)).
    query = dict(target.get("query") or {})
    body = target.get("request_body")
    if target.get("needs_program"):
        program_id = request.getfixturevalue("hot_program_id")
        for k, v in (target.get("query_template") or {}).items():
            query[k] = str(v).format(program_id=program_id)
        body_template = target.get("body_template") or {}
        if body_template:
            body = {k: int(str(v).format(program_id=program_id)) if str(v) == "{program_id}"
                       else str(v).format(program_id=program_id)
                    for k, v in body_template.items()}

    resp = session.request(
        target["method"], url, timeout=10,
        params=query or None, json=body,
    )
    assert resp.status_code == 200, (
        f"{target['name']}: expected 200, got {resp.status_code}. "
        f"Body head: {resp.text[:200]!r}"
    )

    try:
        envelope = target["envelope"].model_validate(resp.json())
    except ValidationError as exc:
        pytest.fail(f"{target['name']}: schema mismatch\n{exc}")

    expected_codes = target.get("expected_errcode") or ["0000"]
    assert envelope.errcode in expected_codes, (
        f"{target['name']}: errcode={envelope.errcode!r}, expected one of {expected_codes}. "
        f"Full body: {resp.text[:300]!r}"
    )
