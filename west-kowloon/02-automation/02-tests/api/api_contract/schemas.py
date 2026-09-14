"""Pydantic models that pin the response shape (the "contract") of selected
西九 endpoints. Every model is intentionally permissive about *additional*
fields — the contract only fails when a known-required field disappears or
changes type. Backend can keep growing the response; we won't false-fail.

Shape pattern observed in every endpoint:
    { "errcode": "0000", "data": <payload>, "success": true? }

Where:
    errcode    "0000" on success, error code string otherwise
    data       endpoint-specific payload (object or array)
    success    optional boolean (some endpoints have it, some don't)
"""
from __future__ import annotations

from typing import Any, Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """Common response wrapper. Allow extras for future fields."""
    model_config = ConfigDict(extra="allow")

    errcode: str
    data: T
    success: Optional[bool] = None


# ---------------------------------------------------------------------------
# /ucenter/rest/getLogonInfo.xhtml  →  current logon identity
# ---------------------------------------------------------------------------
class LogonInfoData(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    nickname: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    bindEmail: Literal["Y", "N"]
    bindMobile: Literal["Y", "N"]
    memberEncode: str


# ---------------------------------------------------------------------------
# /thvendor/member/info/getMemberInfo.xhtml  →  full member identity record
# ---------------------------------------------------------------------------
class MemberInfoData(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    memberId: int
    name: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    status: Literal["Y", "N"]
    memberLevelId: int
    point: int
    addtime: str
    activeTime: str


# ---------------------------------------------------------------------------
# /thvendor/getStadiums.xhtml  →  list of venues
# ---------------------------------------------------------------------------
class StadiumItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    cnName: Optional[str] = None
    enName: Optional[str] = None
    status: Literal["Y", "N"]


# ---------------------------------------------------------------------------
# /thvendor/membership/getList.xhtml  →  membership plans
# ---------------------------------------------------------------------------
class MembershipItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str
    cardType: str
    price: float


# ---------------------------------------------------------------------------
# /thvendor/program/getCategoryList.xhtml  →  program category list
# ---------------------------------------------------------------------------
class CategoryListData(BaseModel):
    model_config = ConfigDict(extra="allow")
    categoryList: list[str] = Field(min_length=1)


# ---------------------------------------------------------------------------
# /thvendor/ticket/program/getProgramById.xhtml  →  single program detail
# ---------------------------------------------------------------------------
class ProgramByIdData(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    briefName: Optional[str] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# /thvendor/ticket/program/getHotProgramList.xhtml  →  hot programs list
# ---------------------------------------------------------------------------
class HotProgramItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    briefName: Optional[str] = None


# ---------------------------------------------------------------------------
# Registry of contract targets.
#
# Fields:
#   name           pytest test id
#   path           URL path
#   method         GET / POST / ...
#   auth           True → use authed_http, False → anonymous http
#   envelope       pydantic model wrapping expected response
#   query          (optional) static query params
#   request_body   (optional) JSON body for POST/PUT
#   needs_program  (optional) inject a fresh programId from getHotProgramList
#   query_template (optional) used with needs_program: {"programId":"{program_id}"}
# ---------------------------------------------------------------------------
CONTRACT_TARGETS: list[dict[str, Any]] = [
    # =====================================================================
    # ANONYMOUS — config / cms / catalog
    # =====================================================================
    {
        "name": "thvendor.getStadiums",
        "path": "/thvendor/getStadiums.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[list[StadiumItem]],
    },
    {
        "name": "thvendor.membership.getList",
        "path": "/thvendor/membership/getList.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[list[MembershipItem]],
    },
    {
        "name": "thvendor.program.getCategoryList",
        "path": "/thvendor/program/getCategoryList.xhtml",
        "method": "POST",
        "auth": False,
        "envelope": Envelope[CategoryListData],
    },
    {
        "name": "thvendor.ad.getNewAdList",
        "path": "/thvendor/ad/getNewAdList.xhtml",
        "method": "POST",
        "auth": False,
        "envelope": Envelope[Any],
        "request_body": {"showSite": "PCBanner"},
    },
    {
        "name": "thvendor.campaign.listCachedCampaign",
        "path": "/thvendor/campaign/listCachedCampaign.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[Any],
    },
    {
        "name": "thvendor.campaignLabel.listCampaignLabel",
        "path": "/thvendor/campaignLabel/listCampaignLabel.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[Any],
    },
    {
        "name": "thvendor.companyBaseInfo.getDisplayConfig",
        "path": "/thvendor/companyBaseInfo/getDisplayConfig.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[Any],
    },
    {
        "name": "ucenter.member.globalConfig.telephoneCountryCodes",
        "path": "/ucenter/member/globalConfig/telephoneCountryCodes.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[Any],
    },

    # =====================================================================
    # ANONYMOUS — programs / tickets (most need a programId)
    # =====================================================================
    {
        "name": "thvendor.ticket.program.getHotProgramList",
        "path": "/thvendor/ticket/program/getHotProgramList.xhtml",
        "method": "POST",
        "auth": False,
        "envelope": Envelope[list[HotProgramItem]],
        "request_body": {"showSite": "PCrecList1"},
    },
    {
        "name": "thvendor.ticket.program.getProgramById",
        "path": "/thvendor/ticket/program/getProgramById.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[ProgramByIdData],
        "needs_program": True,
        "query_template": {"programId": "{program_id}"},
    },
    {
        "name": "thvendor.programcalendar.querySchedulesByDate",
        "path": "/thvendor/programcalendar/querySchedulesByDate.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[Any],
        "query": {"dateFrom": "2026-05-01", "dateTo": "2026-06-30"},
    },
    {
        "name": "thvendor.program.content.getProgramContentInfo",
        "path": "/thvendor/program/content/getProgramContentInfo.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[Any],
        "needs_program": True,
        "query_template": {"programId": "{program_id}"},
    },
    {
        "name": "thvendor.seat.program.countdown",
        "path": "/thvendor/seat/program/countdown.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[Any],
        "needs_program": True,
        "query_template": {"programId": "{program_id}"},
    },
    {
        "name": "thvendor.stand.program.countdown",
        "path": "/thvendor/stand/program/countdown.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[Any],
        "needs_program": True,
        "query_template": {"programId": "{program_id}"},
    },
    # show.combo.entry.list — needs a COMBO program id, not a regular one;
    # skip until we have a combo-specific id resolver.
    {
        "name": "thvendor.program.promotion.member.list",
        "path": "/thvendor/program/promotion/member/list.xhtml",
        "method": "POST",
        "auth": False,
        "envelope": Envelope[Any],
        "needs_program": True,
        "body_template": {"programId": "{program_id}"},
    },
    {
        "name": "thvendor.program.promotion.package.ticket.list",
        "path": "/thvendor/program/promotion/package/ticket/list.xhtml",
        "method": "POST",
        "auth": False,
        "envelope": Envelope[Any],
        "needs_program": True,
        "body_template": {"programId": "{program_id}"},
    },
    {
        "name": "thvendor.favorites.getFavoritesTotal",
        "path": "/thvendor/favorites/getFavoritesTotal.xhtml",
        "method": "POST",
        "auth": False,
        "envelope": Envelope[Any],
        "needs_program": True,
        "body_template": {"programId": "{program_id}"},
    },
    {
        "name": "thvendor.trans.program.getListByIds",
        "path": "/thvendor/trans/program/getListByIds.xhtml",
        "method": "GET",
        "auth": False,
        "envelope": Envelope[Any],
        "needs_program": True,
        "query_template": {"programIds": "{program_id}", "TRANS": "en"},
    },

    # =====================================================================
    # AUTH-REQUIRED — member identity & profile
    # =====================================================================
    {
        "name": "ucenter.rest.getLogonInfo.POST",
        "path": "/ucenter/rest/getLogonInfo.xhtml",
        "method": "POST",
        "auth": True,
        "envelope": Envelope[LogonInfoData],
    },
    {
        "name": "thvendor.member.info.getMemberInfo",
        "path": "/thvendor/member/info/getMemberInfo.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[MemberInfoData],
    },
    {
        "name": "thvendor.member.info.getPersonalInfo",
        "path": "/thvendor/member/info/getPersonalInfo.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
    },
    {
        "name": "thvendor.member.info.getPersonalInfoDynamicField",
        "path": "/thvendor/member/info/getPersonalInfoDynamicField.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
    },
    {
        "name": "thvendor.member.getCertificationList",
        "path": "/thvendor/member/getCertificationList.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
    },
    {
        "name": "thvendor.member.address.getMemberAddressList",
        "path": "/thvendor/member/address/getMemberAddressList.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
    },

    # =====================================================================
    # AUTH-REQUIRED — orders / tickets / memberships
    # =====================================================================
    {
        "name": "thvendor.member.order.getMemberOrderList",
        "path": "/thvendor/member/order/getMemberOrderList.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
        "query": {"pageNo": "1", "pageSize": "10", "status": "paid", "expireFlag": "N"},
    },
    {
        "name": "thvendor.member.order.getAllValidTicketList",
        "path": "/thvendor/member/order/getAllValidTicketList.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
        "query": {"showToast": "noMsg"},
    },
    {
        "name": "thvendor.member.membership.getMemberships",
        "path": "/thvendor/member/membership/getMemberships.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
        "query": {"pageNo": "1", "pageSize": "60"},
    },
    {
        "name": "thvendor.member.transfer.rule.times",
        "path": "/thvendor/member/transfer/rule/times.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
    },

    # =====================================================================
    # AUTH-REQUIRED — coupons / points / favorites
    # =====================================================================
    {
        "name": "thvendor.member.coupon.getMemberCouponsByStatus",
        "path": "/thvendor/member/coupon/getMemberCouponsByStatus.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
        "query": {"status": "notStart"},
    },
    {
        "name": "thvendor.member.favorites.listFavorites",
        "path": "/thvendor/member/favorites/listFavorites.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
    },
    {
        "name": "thvendor.member.record.getMemberRemainPointBeforeTime",
        "path": "/thvendor/member/record/getMemberRemainPointBeforeTime.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
        # 1122 = "Points expiry time configuration does not exist" — that
        # is a valid business response on a SIT env that hasn't configured
        # point-expiry; the endpoint contract itself is fine.
        "expected_errcode": ["0000", "1122"],
    },
    # listMemberPointReceiveRecord — body has fluctuationType (increase/decrease)
    # per JS bundle; can't confirm the exact accepted value while the SIT
    # account is rate-limited. Re-enable after a clean force-login window.
    # {
    #     "name": "thvendor.member.record.listMemberPointReceiveRecord",
    #     "path": "/thvendor/member/record/listMemberPointReceiveRecord.xhtml",
    #     "method": "POST",
    #     "auth": True,
    #     "envelope": Envelope[Any],
    #     "request_body": {"pageNo": 1, "pageSize": 10, "fluctuationType": "increase"},
    # },
    {
        "name": "thvendor.member.subscription.eventMsg.mine",
        "path": "/thvendor/member/subscription/record/eventMsg/mine.xhtml",
        "method": "GET",
        "auth": True,
        "envelope": Envelope[Any],
    },

    # =====================================================================
    # AUTH-REQUIRED — cart (needs cart state; smoke-level only — accept
    # any errcode that proves the endpoint is reachable with valid session)
    # =====================================================================
    # Cart endpoints intentionally LEFT OUT of contract layer until we have
    # a known-good cart fixture. They sit in smoke as 401-gated and the
    # full cart→checkout flow belongs in functional/E2E layer.
]
