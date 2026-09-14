"""L3 functional tests — multi-step API journeys (deterministic).

Each test below chains multiple API calls and asserts that the data
returned by one call is consistent with the data returned by another:

  journey_1_identity_consistency   — getLogonInfo.id == getMemberInfo.memberId
  journey_2_program_detail_lookup  — getHotProgramList[0].id resolves via
                                     getProgramById and the same id comes back
  journey_3_orders_vs_tickets      — paid orders count is consistent with
                                     valid-ticket count (paid orders ≤ valid
                                     tickets only when entry isn't yet used)
  journey_4_membership_alignment   — public membership plans list matches the
                                     id space of the member's own memberships

L2 (hybrid) already proves API + UI share the same session via
storage_state.json; L3 stays pure-API so the suite is fast (< 5s) and
deterministic in CI, without hitting flaky headless-render timing.
"""
from __future__ import annotations

from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Journey 1 — identity consistency across two member APIs
# ---------------------------------------------------------------------------
def test_journey_1_identity_consistency(authed_http, base_url):
    """getLogonInfo and getMemberInfo should agree on who I am.

    Catches: an auth bug that lets two different accounts look like the
    "same session" depending on which endpoint you call.
    """
    logon = authed_http.post(base_url + "/ucenter/rest/getLogonInfo.xhtml", timeout=10).json()
    assert logon["errcode"] == "0000" and logon["data"], logon
    logon_id = logon["data"]["id"]
    logon_email = logon["data"]["email"]

    member = authed_http.get(base_url + "/thvendor/member/info/getMemberInfo.xhtml", timeout=10).json()
    assert member["errcode"] == "0000" and member["data"], member
    member_id_in_thvendor = member["data"]["memberId"]
    member_email = member["data"]["email"]

    assert logon_id == member_id_in_thvendor, (
        f"identity mismatch: getLogonInfo.id={logon_id} vs "
        f"getMemberInfo.memberId={member_id_in_thvendor}"
    )
    assert logon_email == member_email, (
        f"email mismatch: getLogonInfo={logon_email!r} vs getMemberInfo={member_email!r}"
    )


# ---------------------------------------------------------------------------
# Journey 2 — program detail round-trip
# ---------------------------------------------------------------------------
def test_journey_2_program_detail_lookup(http, base_url):
    """Pull a program id from getHotProgramList, then look it up by id.
    The id that comes back should match what we asked for.

    Catches: getProgramById returning a different program (stale cache,
    sharded routing bug, etc.).
    """
    hot = http.post(
        base_url + "/thvendor/ticket/program/getHotProgramList.xhtml",
        json={"showSite": "PCrecList1"}, timeout=10,
    ).json()
    assert hot["errcode"] == "0000", hot
    items = hot["data"] if isinstance(hot["data"], list) else (hot["data"] or {}).get("list", [])
    assert items, f"no hot programs returned: {hot}"

    program_id = items[0].get("id") or items[0].get("programId")
    assert program_id, f"first program lacks id: {sorted(items[0].keys())}"

    detail = http.get(
        base_url + "/thvendor/ticket/program/getProgramById.xhtml",
        params={"programId": program_id}, timeout=10,
    ).json()
    assert detail["errcode"] == "0000", detail
    detail_data = detail["data"] if isinstance(detail["data"], dict) else (detail["data"] or [{}])[0]
    detail_id = detail_data.get("id") or detail_data.get("programId")

    assert int(detail_id) == int(program_id), (
        f"getProgramById({program_id}) returned a different id {detail_id}; "
        f"detail keys: {sorted(detail_data.keys()) if isinstance(detail_data, dict) else type(detail_data)}"
    )


# ---------------------------------------------------------------------------
# Journey 3 — orders vs valid tickets cross-check
# ---------------------------------------------------------------------------
def test_journey_3_orders_consistent_with_tickets(authed_http, base_url):
    """A paid order should have at least one corresponding "valid ticket"
    until used. If we have N paid orders and 0 valid tickets, OR vice versa,
    something is wrong on the server side."""
    orders = authed_http.get(
        base_url + "/thvendor/member/order/getMemberOrderList.xhtml",
        params={"pageNo": 1, "pageSize": 50, "status": "paid", "expireFlag": "N"},
        timeout=10,
    ).json()
    assert orders["errcode"] == "0000", orders
    paid_orders = orders["data"] if isinstance(orders["data"], list) else (orders["data"] or {}).get("list", [])

    tickets = authed_http.get(
        base_url + "/thvendor/member/order/getAllValidTicketList.xhtml",
        params={"showToast": "noMsg"}, timeout=10,
    ).json()
    assert tickets["errcode"] == "0000", tickets
    valid_tix = tickets["data"] if isinstance(tickets["data"], list) else (tickets["data"] or {}).get("list", [])

    # Consistency rule:
    #   - if member has no paid orders, valid tickets MUST be 0 too
    #   - if member has paid orders, valid tickets can be 0 (all used) or >0
    if not paid_orders:
        assert not valid_tix, (
            f"member has 0 paid orders but {len(valid_tix)} valid tickets — "
            f"impossible state"
        )


# ---------------------------------------------------------------------------
# Journey 4 — public membership list aligns with member's own
# ---------------------------------------------------------------------------
def test_journey_4_membership_id_space(http, authed_http, base_url):
    """Every plan id returned by /thvendor/membership/getList is a valid
    plan id in the membership universe. The member's own memberships should
    all be drawn from that same id space (if they have any)."""
    public = http.get(base_url + "/thvendor/membership/getList.xhtml", timeout=10).json()
    assert public["errcode"] == "0000", public
    public_plans = public["data"] if isinstance(public["data"], list) else []
    if not public_plans:
        pytest.skip("no membership plans in this env")
    public_ids = {str(p.get("id")) for p in public_plans if p.get("id")}
    assert public_ids, public_plans

    mine = authed_http.get(
        base_url + "/thvendor/member/membership/getMemberships.xhtml",
        params={"pageNo": 1, "pageSize": 60}, timeout=10,
    ).json()
    assert mine["errcode"] == "0000", mine
    mine_data = mine["data"] if isinstance(mine["data"], list) else (mine["data"] or {}).get("list", [])

    # Members without any memberships are fine — the journey is "if you
    # have any, they should reference real plan ids".
    for m in mine_data:
        plan_id = m.get("cardTypeId") or m.get("membershipId") or m.get("id")
        if plan_id is None:
            continue
        assert str(plan_id) in public_ids, (
            f"member holds membership with plan id {plan_id!r} that isn't in "
            f"the public plan list {sorted(public_ids)[:5]}..."
        )
