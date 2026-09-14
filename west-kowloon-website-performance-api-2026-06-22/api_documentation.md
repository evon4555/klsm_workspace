# 西九官网性能测试 API 文档

- 生成日期: 2026-06-22 17:59:59
- 目标站点: `https://anticket.lengliwh.com/websitehtml/index.html#/`
- 用途: JMeter 单接口压测与串联 scenario 压测设计
- 安全处理: 输出已脱敏 Cookie、Session、Token、密码、验证码、邮箱、手机号等敏感值

## 覆盖来源

- `current_spa_static`: 当前官网前端包静态扫描
- `current_playwright_crawl`: 当前官网真实浏览器登录态/未登录态页面抓包
- `legacy_anticket_har`: 既有 anticket HAR，包含历史下单/取消链路样例
- `local_wk_endpoints_registry`: `D:\Workspace\west-kowloon` 内现有接口登记

## JMeter 通用约定

- 公共 Header: `cmpappkey=ShanghaiCS`, `lang=en`, `Accept=application/json, text/plain, */*`。
- 外层 Basic Auth: 官网入口需要 Basic Auth，JMeter 需配置 HTTP Authorization Manager。不要把真实密码提交到仓库。
- 登录验证码: `/ucenter/rest/pcLoginByPass.xhtml` 依赖图片验证码，不适合直接做高并发登录压测；建议使用预置 session、测试专用免验证码登录或压测白名单。
- 业务断言: 不只看 HTTP 200；优先断言 JSON 中 `errcode=0000`、`success=true`，列表接口再断言 `data` 或 `resultList` 非空。
- 下单链路: 单接口压测可做查询类接口；创建订单接口必须串联取消接口，并控制数据量、库存和并发，避免未支付订单堆积。

## API 总览

| 分组 | 方法 | 路径 | 登录态 | 用途 |
|---|---:|---|---|---|
| auth | `GET` | `/ucenter/captcha.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| auth | `GET` | `/ucenter/getCaptchaId.xhtml` | False | Issues a captcha session id used by login / register flows. |
| auth | `POST` | `/ucenter/getCaptchaId.xhtml` | False | 获取验证码会话 ID |
| auth | `POST` | `/ucenter/guest/createAndLogin.xhtml` | False | 游客账号创建并登录 |
| auth | `POST` | `/ucenter/member/bindEmail.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| auth | `POST` | `/ucenter/member/bindMobile.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| auth | `POST` | `/ucenter/member/bindWxUserInfo.xhtml` | False | 绑定微信用户信息 |
| auth | `GET` | `/ucenter/member/getUpHeadToken.xhtml` | False | 获取头像/图片上传 token |
| auth | `GET` | `/ucenter/member/globalConfig/telephoneCountryCodes.xhtml` | False | Returns the list of supported country codes shown in the phone dropdown. |
| auth | `GET` | `/ucenter/openapi/openlogin/getAuthUrl.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| auth | `POST` | `/ucenter/openapi/openlogin/pollResult.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| auth | `POST` | `/ucenter/rest/createAndLoginWithBindEmail.xhtml` | False | 创建/保存相关接口 |
| auth | `POST` | `/ucenter/rest/createAndLoginWithBindMobile.xhtml` | False | 创建/保存相关接口 |
| auth | `POST` | `/ucenter/rest/getLogonInfo.xhtml` | True | 获取当前登录会员信息 |
| auth | `GET` | `/ucenter/rest/logout.xhtml` | False | Logout endpoint. |
| auth | `POST` | `/ucenter/rest/logout.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| auth | `POST` | `/ucenter/rest/pcLoginByPass.xhtml` | False | 账号密码登录，带图片验证码 |
| auth | `POST` | `/ucenter/rest/sendBindMsg.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| auth | `POST` | `/ucenter/rest/sendEmailDynamic.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| cms | `POST` | `/thvendor/ad/getNewAdList.xhtml` | False | [crawler] Banner / ad list shown on home + landing pages. |
| cms | `POST` | `/thvendor/campaign/getCachedCampaign.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| cms | `POST` | `/thvendor/campaign/getChargeType.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| cms | `GET` | `/thvendor/campaign/listCachedCampaign.xhtml` | False | [crawler] Cached campaign list (homepage). |
| cms | `GET` | `/thvendor/campaign/order/getCampaignOrderConstant.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `POST` | `/thvendor/member/address/getMemberAddressById.xhtml` | True | 创建/保存相关接口 |
| member | `GET` | `/thvendor/member/address/getMemberAddressList.xhtml` | True | [crawler] Member shipping address list. |
| member | `POST` | `/thvendor/member/address/remove.xhtml` | True | 创建/保存相关接口 |
| member | `POST` | `/thvendor/member/address/save.xhtml` | True | 创建/保存相关接口 |
| member | `POST` | `/thvendor/member/campaign/approval/approvalDetail.xhtml` | True | 详情查询接口 |
| member | `POST` | `/thvendor/member/campaign/approval/cancel.xhtml` | True | 取消/撤销相关接口 |
| member | `GET` | `/thvendor/member/campaign/approval/create.xhtml` | True | 创建/保存相关接口 |
| member | `POST` | `/thvendor/member/certification/getVerifyType.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `GET` | `/thvendor/member/clearMember/checkCode.xhtml` | True | Step 3 of account-deletion — verify the entered code. |
| member | `POST` | `/thvendor/member/clearMember/checkCode.xhtml` | True | 删除/移除相关接口 |
| member | `GET` | `/thvendor/member/clearMember/confirm.xhtml` | True | Final step of account-deletion — submit deletion request. |
| member | `GET` | `/thvendor/member/clearMember/reasonList.xhtml` | True | List of selectable reasons for leaving (account deletion). |
| member | `GET` | `/thvendor/member/clearMember/sendCode.xhtml` | True | Step 2 of account-deletion — send the verification code. |
| member | `POST` | `/thvendor/member/clearMember/sendCode.xhtml` | True | 删除/移除相关接口 |
| member | `GET` | `/thvendor/member/clearMember/validateWay.xhtml` | True | Step 1 of account-deletion — which channel (email/SMS) to verify on. |
| member | `POST` | `/thvendor/member/clearMember/validateWay.xhtml` | True | 删除/移除相关接口 |
| member | `GET` | `/thvendor/member/common/getDynamicCode.xhtml` | True | 获取电子票动态码 |
| member | `GET` | `/thvendor/member/common/getFreightByArea.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `GET` | `/thvendor/member/coupon/getByStatus.xhtml` | True | 优惠/折扣相关接口 |
| member | `GET` | `/thvendor/member/coupon/getMemberCouponsByStatus.xhtml` | True | [crawler] My coupons, filtered by status (notStart / inUse / expired). |
| member | `POST` | `/thvendor/member/coupon/orderDetail.xhtml` | True | 详情查询接口 |
| member | `POST` | `/thvendor/member/donation/addDonation.xhtml` | True | 创建/保存相关接口 |
| member | `POST` | `/thvendor/member/donation/cancelDonation.xhtml` | True | 取消/撤销相关接口 |
| member | `GET` | `/thvendor/member/donation/getDonationConfig.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `GET` | `/thvendor/member/favorites/deleteFavoriteById.xhtml` | True | 删除/移除相关接口 |
| member | `POST` | `/thvendor/member/favorites/isFavorites.xhtml` | True | [deep-crawler] Did the logged-in member favourite this program. |
| member | `GET` | `/thvendor/member/favorites/listFavorites.xhtml` | True | [crawler] My wishlist / favorites. |
| member | `GET` | `/thvendor/member/favorites/saveFavorites.xhtml` | True | 创建/保存相关接口 |
| member | `GET` | `/thvendor/member/general/getShowTicketInfo.xhtml` | True | 详情查询接口 |
| member | `GET` | `/thvendor/member/getCertificationList.xhtml` | True | [crawler] ID certification status (real-name). |
| member | `GET` | `/thvendor/member/getPaymentGatewayList.xhtml` | True | 列表/分页查询接口 |
| member | `POST` | `/thvendor/member/getPaymentGatewayList.xhtml` | True | 列表/分页查询接口 |
| member | `GET` | `/thvendor/member/info/getMemberInfo.xhtml` | True | [crawler] Logged-in member's core info bundle. |
| member | `GET` | `/thvendor/member/info/getPersonalInfo.xhtml` | True | [crawler] Profile page data. |
| member | `GET` | `/thvendor/member/info/getPersonalInfoDynamicField.xhtml` | True | [crawler] Dynamic / custom profile fields. |
| member | `POST` | `/thvendor/member/mall/getFreightByArea.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `POST` | `/thvendor/member/memberRemindEvent/list.xhtml` | True | 列表/分页查询接口 |
| member | `GET` | `/thvendor/member/memberRemindEvent/save.xhtml` | True | 创建/保存相关接口 |
| member | `POST` | `/thvendor/member/membership/activeMembership.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `GET` | `/thvendor/member/membership/activeMembershipWithPersionInfo.xhtml` | True | 详情查询接口 |
| member | `GET` | `/thvendor/member/membership/bindPerson/acceptBind.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `POST` | `/thvendor/member/membership/bindPerson/startBind.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `POST` | `/thvendor/member/membership/cancelOrder.xhtml` | True | 取消未支付订单 |
| member | `POST` | `/thvendor/member/membership/getMembershipDetail.xhtml` | True | 详情查询接口 |
| member | `POST` | `/thvendor/member/membership/getMembershipEncode.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `GET` | `/thvendor/member/membership/getMembershipPersonEncode.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `GET` | `/thvendor/member/membership/getMemberships.xhtml` | True | [crawler] My membership cards list. |
| member | `POST` | `/thvendor/member/membership/getOrderDetail.xhtml` | True | 详情查询接口 |
| member | `POST` | `/thvendor/member/membership/getOrderList.xhtml` | True | 列表/分页查询接口 |
| member | `POST` | `/thvendor/member/membership/gotoPay.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `GET` | `/thvendor/member/membership/sendActiveEmail.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `GET` | `/thvendor/member/membership/sendActiveMobile.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `GET` | `/thvendor/member/membership/transfer/acceptTransfer.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `GET` | `/thvendor/member/membership/transfer/listTransferRecords.xhtml` | True | 列表/分页查询接口 |
| member | `GET` | `/thvendor/member/membership/transfer/startTransfer.xhtml` | True | 会员卡/会员权益相关接口 |
| member | `GET` | `/thvendor/member/membershiporder/refund/applay.xhtml` | True | 退票/退款相关接口 |
| member | `GET` | `/thvendor/member/partnerMember/available/list.xhtml` | True | 列表/分页查询接口 |
| member | `GET` | `/thvendor/member/partnerMember/identity/bind.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `POST` | `/thvendor/member/partnerMember/identity/list.xhtml` | True | 列表/分页查询接口 |
| member | `GET` | `/thvendor/member/partnerMember/identity/unbind.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `GET` | `/thvendor/member/record/getMemberRemainPointBeforeTime.xhtml` | True | [crawler] Remaining points expiring soon. |
| member | `POST` | `/thvendor/member/record/listMemberPointReceiveRecord.xhtml` | True | [crawler] Point-earning history. |
| member | `GET` | `/thvendor/member/removeCertification.xhtml` | True | 删除/移除相关接口 |
| member | `POST` | `/thvendor/member/saveCertification.xhtml` | True | 创建/保存相关接口 |
| member | `GET` | `/thvendor/member/subscription/record/eventMsg/getLastSubscriptionRecord.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `GET` | `/thvendor/member/subscription/record/eventMsg/mine.xhtml` | True | My event subscriptions / message inbox. |
| member | `HEAD` | `/thvendor/member/subscription/record/eventMsg/mine.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `GET` | `/thvendor/member/subscription/record/v2/save.xhtml` | True | 创建/保存相关接口 |
| member | `POST` | `/thvendor/member/toggleSelf.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `POST` | `/thvendor/member/transfer/pageList.xhtml` | True | 列表/分页查询接口 |
| member | `GET` | `/thvendor/member/transfer/rule/times.xhtml` | True | [crawler] Ticket-transfer rule: allowed times per ticket. |
| member | `GET` | `/thvendor/member/wxMsg/cancle/subscribe/schedule/remind.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member | `GET` | `/thvendor/member/wxMsg/subscribe/schedule/remind.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member-order | `POST` | `/thvendor/member/campaign/order/cancelOrder.xhtml` | True | 取消未支付订单 |
| member-order | `GET` | `/thvendor/member/campaign/order/create.xhtml` | True | 创建非座位类订单 |
| member-order | `GET` | `/thvendor/member/campaign/order/orderDetail.xhtml` | True | 详情查询接口 |
| member-order | `GET` | `/thvendor/member/campaign/order/pageList.xhtml` | True | 列表/分页查询接口 |
| member-order | `GET` | `/thvendor/member/campaign/order/pay.xhtml` | True | 支付/重新支付相关接口 |
| member-order | `POST` | `/thvendor/member/membership/order/create.xhtml` | True | 创建非座位类订单 |
| member-order | `GET` | `/thvendor/member/membership/order/discount/cancelDiscount.xhtml` | True | 查询座位/票价优惠 |
| member-order | `POST` | `/thvendor/member/membership/order/discount/confirmDiscount.xhtml` | True | 查询座位/票价优惠 |
| member-order | `GET` | `/thvendor/member/membership/order/discount/getDiscountRepo.xhtml` | True | 查询座位/票价优惠 |
| member-order | `GET` | `/thvendor/member/membership/order/discount/useDiscount.xhtml` | True | 查询座位/票价优惠 |
| member-order | `POST` | `/thvendor/member/membership/order/discount/usePoint.xhtml` | True | 查询座位/票价优惠 |
| member-order | `GET` | `/thvendor/member/membership/order/renewPayOrder.xhtml` | True | 支付/重新支付相关接口 |
| member-order | `POST` | `/thvendor/member/order/budgetTicketsRefundPlan.xhtml` | True | 退票/退款相关接口 |
| member-order | `GET` | `/thvendor/member/order/getAllValidTicketList.xhtml` | True | [crawler] My valid tickets (entry-ready). |
| member-order | `GET` | `/thvendor/member/order/getMemberOrderList.xhtml` | True | [crawler] My orders, paginated + filterable by status. |
| member-order | `GET` | `/thvendor/member/order/getTicketInfo.xhtml` | True | 详情查询接口 |
| member-order | `POST` | `/thvendor/member/order/refundOrderDetails.xhtml` | True | 退票/退款相关接口 |
| member-order | `POST` | `/thvendor/member/show/combo/order/cancelOrder.xhtml` | True | 取消未支付订单 |
| member-order | `POST` | `/thvendor/member/show/combo/order/create.xhtml` | True | 创建非座位类订单 |
| member-order | `POST` | `/thvendor/member/show/combo/order/orderDetail.xhtml` | True | 详情查询接口 |
| member-order | `POST` | `/thvendor/member/show/combo/order/pay.xhtml` | True | 支付/重新支付相关接口 |
| member-order | `POST` | `/thvendor/member/show/combo/order/repeatedPayOrder.xhtml` | True | 支付/重新支付相关接口 |
| member-order | `POST` | `/thvendor/member/show/combo/order/updateContact.xhtml` | True | 更新/变更相关接口 |
| member-order | `POST` | `/thvendor/member/show/combo/order/updateDelivery.xhtml` | True | 更新/变更相关接口 |
| member-order | `POST` | `/thvendor/member/show/combo/order/updateTransport.xhtml` | True | 更新/变更相关接口 |
| member-order | `GET` | `/thvendor/member/show/order/budgetTicketsRefundPlan.xhtml` | True | 退票/退款相关接口 |
| member-order | `GET` | `/thvendor/member/show/order/cancelOrder.xhtml` | True | 取消未支付订单 |
| member-order | `GET` | `/thvendor/member/show/order/changeOrderCerts.xhtml` | True | 更新/变更相关接口 |
| member-order | `POST` | `/thvendor/member/show/order/create.xhtml` | True | 创建非座位类订单 |
| member-order | `GET` | `/thvendor/member/show/order/orderDetail.xhtml` | True | 详情查询接口 |
| member-order | `POST` | `/thvendor/member/show/order/pay.xhtml` | True | 支付/重新支付相关接口 |
| member-order | `POST` | `/thvendor/member/show/order/refundOrder.xhtml` | True | 退票/退款相关接口 |
| member-order | `POST` | `/thvendor/member/show/order/refundOrderDetails.xhtml` | True | 退票/退款相关接口 |
| member-order | `GET` | `/thvendor/member/show/order/saveOutOfStockRegistration.xhtml` | True | 创建/保存相关接口 |
| member-order | `POST` | `/thvendor/member/show/order/updateShowOrderContactName.xhtml` | True | 更新/变更相关接口 |
| member-order | `POST` | `/thvendor/member/show/order/updateShowOrderExpressFee.xhtml` | True | 更新/变更相关接口 |
| member-order | `POST` | `/thvendor/member/show/order/updateShowOrderTransport.xhtml` | True | 更新/变更相关接口 |
| member-order | `GET` | `/thvendor/member/ticket/order/autoLock.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member-order | `POST` | `/thvendor/member/ticket/order/cancelOrder.xhtml` | True | 取消未支付订单 |
| member-order | `POST` | `/thvendor/member/ticket/order/changeOrderCerts.xhtml` | True | 更新/变更相关接口 |
| member-order | `GET` | `/thvendor/member/ticket/order/create.xhtml` | True | 创建非座位类订单 |
| member-order | `POST` | `/thvendor/member/ticket/order/create2.xhtml` | True | 创建座位类订单 |
| member-order | `POST` | `/thvendor/member/ticket/order/createOrder.xhtml` | True | 创建非座位类订单 |
| member-order | `POST` | `/thvendor/member/ticket/order/detail.xhtml` | True | 详情查询接口 |
| member-order | `POST` | `/thvendor/member/ticket/order/payOrder.xhtml` | True | 支付/重新支付相关接口 |
| member-order | `POST` | `/thvendor/member/ticket/order/refundOrder.xhtml` | True | 退票/退款相关接口 |
| member-order | `POST` | `/thvendor/member/ticket/order/unLockSeat.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| member-order | `GET` | `/thvendor/member/ticket/order/updateTicketOrderContactName.xhtml` | True | 更新/变更相关接口 |
| member-order | `GET` | `/thvendor/member/ticket/order/updateTicketOrderExpressFee.xhtml` | True | 更新/变更相关接口 |
| member-order | `GET` | `/thvendor/member/ticket/order/updateTicketOrderTransport.xhtml` | True | 更新/变更相关接口 |
| payment | `POST` | `/pay/cybersource/payment/create.xhtml` | False | 创建 CyberSource 支付请求/支付参数 |
| sms | `POST` | `/sms/common/commonUpload.xhtml` | False | 通用文件上传 |
| thvendor | `GET` | `/thvendor/adinfo/getAdContentByIds.xhtml` | False | 详情查询接口 |
| thvendor | `POST` | `/thvendor/adinfo/getAdInfoById.xhtml` | False | 详情查询接口 |
| thvendor | `GET` | `/thvendor/campaignLabel/listCampaignLabel.xhtml` | False | [crawler] Campaign labels / categories. |
| thvendor | `GET` | `/thvendor/common/getCityList.xhtml` | False | 列表/分页查询接口 |
| thvendor | `POST` | `/thvendor/common/getCountryAllList.xhtml` | False | 列表/分页查询接口 |
| thvendor | `GET` | `/thvendor/common/getCountyList.xhtml` | False | 列表/分页查询接口 |
| thvendor | `POST` | `/thvendor/common/getProvinceAllList.xhtml` | False | 列表/分页查询接口 |
| thvendor | `POST` | `/thvendor/common/getProvinceList.xhtml` | False | 列表/分页查询接口 |
| thvendor | `GET` | `/thvendor/common/getServerTime.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| thvendor | `GET` | `/thvendor/common/prepareUpload.xhtml` | False | 准备上传并获取 uploadToken |
| thvendor | `GET` | `/thvendor/companyBaseInfo/getDisplayConfig.xhtml` | False | [crawler] Per-site display config loaded on every page entry. |
| thvendor | `GET` | `/thvendor/dynamicvalue/getDynamicValueListByField.xhtml` | False | 列表/分页查询接口 |
| thvendor | `POST` | `/thvendor/favorites/getFavoritesTotal.xhtml` | False | [deep-crawler] Aggregate favourite count for a program. |
| thvendor | `GET` | `/thvendor/favorites/memberFavoritesCategory.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| thvendor | `GET` | `/thvendor/getCaptchaId.xhtml` | False | 获取验证码会话 ID |
| thvendor | `GET` | `/thvendor/getStadiums.xhtml` | False | [crawler] Venue / stadium list. |
| thvendor | `POST` | `/thvendor/mall/getCulturalProductDetail.xhtml` | False | 详情查询接口 |
| thvendor | `POST` | `/thvendor/membership/bindPerson/getBind.xhtml` | False | 会员卡/会员权益相关接口 |
| thvendor | `POST` | `/thvendor/membership/getDetail.xhtml` | False | 详情查询接口 |
| thvendor | `GET` | `/thvendor/membership/getList.xhtml` | False | [crawler] Public membership plans list (anonymous browse). |
| thvendor | `GET` | `/thvendor/membership/transfer/getTransfer.xhtml` | False | 会员卡/会员权益相关接口 |
| thvendor | `GET` | `/thvendor/programcalendar/querySchedulesByDate.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| thvendor | `GET` | `/thvendor/tools/qrcode.xhtml` | False | 生成二维码图片 |
| thvendor | `POST` | `/thvendor/wxMsg/schedule/v2/remind.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/member/cart/cancel.xhtml` | True | 取消/撤销相关接口 |
| ticketing | `GET` | `/thvendor/member/cart/cancelCartItem.xhtml` | True | 取消/撤销相关接口 |
| ticketing | `GET` | `/thvendor/member/cart/cancelCartItemsBySession.xhtml` | True | 取消/撤销相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/cancelPackOrder.xhtml` | True | 取消/撤销相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/clearShippingInfo.xhtml` | True | 删除/移除相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/confirmCart.xhtml` | True | 购物车相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/discount/addPromoCode.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/cart/discount/cancel.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/cart/discount/confirm.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/cart/discount/getRepo.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/cart/discount/removePromoCode.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/cart/discount/use.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/cart/discount/usePoint.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/cart/discount/validatePromoCode.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/cart/getCartDetail.xhtml` | True | [crawler] Current cart contents. |
| ticketing | `POST` | `/thvendor/member/cart/getPackOrder.xhtml` | True | 购物车相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/initTicketCart.xhtml` | True | [crawler] Initialise a ticket cart session. |
| ticketing | `POST` | `/thvendor/member/cart/setContactInfo.xhtml` | True | 详情查询接口 |
| ticketing | `POST` | `/thvendor/member/cart/setDonation.xhtml` | True | 购物车相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/setShippingInfo.xhtml` | True | 详情查询接口 |
| ticketing | `POST` | `/thvendor/member/cart/setShippingInfoBySubOrders.xhtml` | True | 详情查询接口 |
| ticketing | `POST` | `/thvendor/member/cart/setSingleOrderCert.xhtml` | True | 购物车相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/show/addShowItems.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/ticket/addSeatItems.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/ticket/autoAddSeatItems.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/ticket/changeSeatPack.xhtml` | True | 更新/变更相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/ticket/cleanSeatPack.xhtml` | True | 购物车相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/updateItemCert.xhtml` | True | 更新/变更相关接口 |
| ticketing | `POST` | `/thvendor/member/cart/upsertCartCert.xhtml` | True | 购物车相关接口 |
| ticketing | `POST` | `/thvendor/member/show/addon/addonSplicing.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/show/addon/createAddonCulturalOrder.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/show/addon/getAddonDiscount.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/show/addon/getAvaiableAddonProductList.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/show/change/create.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/show/change/getChangeDetailInfo.xhtml` | True | 更新/变更相关接口 |
| ticketing | `POST` | `/thvendor/member/show/change/getContainer.xhtml` | True | 更新/变更相关接口 |
| ticketing | `POST` | `/thvendor/member/show/change/getOrder.xhtml` | True | 更新/变更相关接口 |
| ticketing | `POST` | `/thvendor/member/show/change/preCreate.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/show/change/selectSeats.xhtml` | True | 更新/变更相关接口 |
| ticketing | `GET` | `/thvendor/member/show/combo/options.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/show/date.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/show/dateListWithSellOut.xhtml` | True | 列表/分页查询接口 |
| ticketing | `POST` | `/thvendor/member/show/discount/addItemToRepoByCode.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `GET` | `/thvendor/member/show/discount/cancelDiscount.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `GET` | `/thvendor/member/show/discount/confirmDiscount.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `GET` | `/thvendor/member/show/discount/getDiscountRepo.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/show/discount/removeItemFromRepoByCode.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `GET` | `/thvendor/member/show/discount/useDiscount.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/show/discount/usePoint.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `GET` | `/thvendor/member/show/eticketTemplate/findByProgram.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/show/listBydate.xhtml` | True | 获取非座位类场次列表 |
| ticketing | `GET` | `/thvendor/member/show/tickettype/list.xhtml` | True | 获取非座位类票种列表 |
| ticketing | `POST` | `/thvendor/member/show/transfer/acceptTransfer.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/member/show/transfer/startTransfer.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/member/ticket/addon/addonSplicing.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/addon/createAddonCulturalOrder.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/addon/getAddonDiscount.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/addon/getAvaiableAddonProductList.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/change/create.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/change/getContainer.xhtml` | True | 更新/变更相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/change/getOrder.xhtml` | True | 更新/变更相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/change/getSeatInfo.xhtml` | True | 更新/变更相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/change/preCreate.xhtml` | True | 创建/保存相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/change/selectSeats.xhtml` | True | 更新/变更相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/discount/addItemToRepoByCode.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/ticket/discount/cancelDiscount.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `GET` | `/thvendor/member/ticket/discount/confirmDiscount.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `GET` | `/thvendor/member/ticket/discount/getDiscountRepo.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/ticket/discount/removeItemFromRepoByCode.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/ticket/discount/useDiscount.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/ticket/discount/usePoint.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `GET` | `/thvendor/member/ticket/getAvailableSeats2.xhtml` | True | Get seat-map availability for a given schedule. |
| ticketing | `POST` | `/thvendor/member/ticket/getAvailableSeats2.xhtml` | True | 获取座位图可售座位和 orderKey |
| ticketing | `GET` | `/thvendor/member/ticket/getGeneralAreaStats.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/ticket/getScheduleInfo.xhtml` | True | Get show schedule info for a given product. |
| ticketing | `POST` | `/thvendor/member/ticket/getScheduleInfo.xhtml` | True | 获取座位类场次信息 |
| ticketing | `GET` | `/thvendor/member/ticket/getSchedulePrices.xhtml` | True | Get ticket price tiers for a given schedule. |
| ticketing | `POST` | `/thvendor/member/ticket/getSchedulePrices.xhtml` | True | 获取座位类票价 |
| ticketing | `POST` | `/thvendor/member/ticket/getSeatImages.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/member/ticket/getSpecialSeatEnableConfig.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/ticket/getSpecialSeatOverlay.xhtml` | True | 获取特殊座位覆盖层 |
| ticketing | `POST` | `/thvendor/member/ticket/listScheduleByDate.xhtml` | True | 按日期获取座位类场次 |
| ticketing | `GET` | `/thvendor/member/ticket/packorder/activeOrder.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/ticket/packorder/payOrder.xhtml` | True | 支付/重新支付相关接口 |
| ticketing | `POST` | `/thvendor/member/ticket/scheduleDateList.xhtml` | True | 列表/分页查询接口 |
| ticketing | `GET` | `/thvendor/member/ticket/scheduleDateListWithSellOut.xhtml` | True | 获取有售罄标记的场次日期 |
| ticketing | `GET` | `/thvendor/member/ticket/seasonpack/addPackDetail.xhtml` | True | 创建/保存相关接口 |
| ticketing | `GET` | `/thvendor/member/ticket/seasonpack/cancelPackDetail.xhtml` | True | 取消/撤销相关接口 |
| ticketing | `GET` | `/thvendor/member/ticket/seasonpack/cancelPackOrder.xhtml` | True | 取消/撤销相关接口 |
| ticketing | `GET` | `/thvendor/member/ticket/seasonpack/computeDiscount.xhtml` | True | 优惠/折扣相关接口 |
| ticketing | `GET` | `/thvendor/member/ticket/seasonpack/confirmOrder.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/ticket/seasonpack/createOrder.xhtml` | True | 创建/保存相关接口 |
| ticketing | `GET` | `/thvendor/member/ticket/seasonpack/getOrder.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/ticket/seasonpack/getSelected.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/member/ticket/seasonpack/processLastOrder.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/ticket/seasonpack/updateContact.xhtml` | True | 更新/变更相关接口 |
| ticketing | `GET` | `/thvendor/member/ticket/seat/discount/query2.xhtml` | True | 查询座位/票价优惠 |
| ticketing | `POST` | `/thvendor/member/ticket/transfer/acceptTransfer.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/member/ticket/transfer/startTransfer.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/wxMsg/cancle/subscribe/show/remind.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/member/wxMsg/subscribe/show/remind.xhtml` | True | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/program/content/getProgramContentInfo.xhtml` | False | [deep-crawler] Static program detail content (description, images). |
| ticketing | `POST` | `/thvendor/program/getCategoryList.xhtml` | False | [crawler] Program / show categories. |
| ticketing | `GET` | `/thvendor/program/getProgramNumByStadium.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/program/promotion/activity/list.xhtml` | False | 列表/分页查询接口 |
| ticketing | `POST` | `/thvendor/program/promotion/coupon/list.xhtml` | False | 列表/分页查询接口 |
| ticketing | `POST` | `/thvendor/program/promotion/member/list.xhtml` | False | [deep-crawler] Membership-tier discount info shown on program page. |
| ticketing | `POST` | `/thvendor/program/promotion/package/ticket/list.xhtml` | False | [deep-crawler] Combo / package ticket options for a program. |
| ticketing | `GET` | `/thvendor/seat/program/countdown.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/seat/program/schedule/countdown.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/show/combo/entry/list.xhtml` | False | 列表/分页查询接口 |
| ticketing | `GET` | `/thvendor/show/combo/getShowTicketTypes.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/show/combo/listBydate.xhtml` | False | 获取非座位类场次列表 |
| ticketing | `POST` | `/thvendor/show/supportReserveProgramShowList.xhtml` | False | 列表/分页查询接口 |
| ticketing | `POST` | `/thvendor/show/transfer/getTransfer.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/stand/program/countdown.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/stand/program/show/countdown.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `POST` | `/thvendor/ticket/program/getHotProgramList.xhtml` | False | [crawler] Hot programs (PC recList) — homepage carousel data. |
| ticketing | `GET` | `/thvendor/ticket/program/getProgramById.xhtml` | False | 获取项目详情主数据 |
| ticketing | `GET` | `/thvendor/ticket/program/getVenueProgramCount.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/ticket/program/v2/getHomeCountdownProgramList.xhtml` | False | 列表/分页查询接口 |
| ticketing | `POST` | `/thvendor/ticket/seasonpack/detail.xhtml` | False | 详情查询接口 |
| ticketing | `POST` | `/thvendor/ticket/seasonpack/getSchedules.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/ticket/supportReserveProgramScheduleList.xhtml` | False | 列表/分页查询接口 |
| ticketing | `POST` | `/thvendor/ticket/transfer/getTransfer.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |
| ticketing | `GET` | `/thvendor/trans/program/getListByIds.xhtml` | False | 列表/分页查询接口 |
| ticketing | `GET` | `/thvendor/wxMsg/show/v2/remind.xhtml` | False | 静态包发现，未在本次抓包中拿到业务说明 |

## auth

### `GET /ucenter/captcha.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
}
```
- Query 入参:
```json
{
  "captchaId": "***REDACTED***",
  "r": "1782122352227"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - current crawl reached logged-in state

### `GET /ucenter/getCaptchaId.xhtml`

- 用途: Issues a captcha session id used by login / register flows.
- 是否需要登录态: `False`
- 证据来源: `local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - Issues a captcha session id used by login / register flows.

### `POST /ucenter/getCaptchaId.xhtml`

- 用途: 获取验证码会话 ID
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": "uWp6gifrXtDwgupw94c8e4bb",
  "success": true
}
```
- 备注:
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/guest/createAndLogin.xhtml`

- 用途: 游客账号创建并登录
- 是否需要登录态: `False`
- 证据来源: `current_spa_static`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "_front_end_data_object": "静态推断；需按实际游客登录/绑定流程补字段"
}
```
- 出参样例:
`无样例 / 未抓到`

### `POST /ucenter/member/bindEmail.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/member/bindMobile.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/member/bindWxUserInfo.xhtml`

- 用途: 绑定微信用户信息
- 是否需要登录态: `False`
- 证据来源: `current_spa_static`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "_front_end_data_object": "静态推断；需按微信绑定流程补字段"
}
```
- 出参样例:
`无样例 / 未抓到`

### `GET /ucenter/member/getUpHeadToken.xhtml`

- 用途: 获取头像/图片上传 token
- 是否需要登录态: `False`
- 证据来源: `current_spa_static`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`

### `GET /ucenter/member/globalConfig/telephoneCountryCodes.xhtml`

- 用途: Returns the list of supported country codes shown in the phone dropdown.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "regionCode": "CN",
      "regionName": "中国大陆",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "Z",
      "popular": "Y"
    },
    {
      "regionCode": "HK",
      "regionName": "中国香港",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "X",
      "popular": "Y"
    },
    {
      "regionCode": "MO",
      "regionName": "中国澳门",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "A",
      "popular": "Y"
    },
    {
      "regionCode": "TW",
      "regionName": "中国台湾",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "T",
      "popular": "Y"
    },
    {
      "regionCode": "US",
      "regionName": "美国",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "M",
      "popular": "Y"
    },
    {
      "regionCode": "IN",
      "regionName": "印度",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "Y"
    },
    {
      "regionCode": "GB",
      "regionName": "英国",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "Y"
    },
    {
      "regionCode": "DE",
      "regionName": "德国",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "D"
    },
    {
      "regionCode": "FR",
      "regionName": "法国",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "F"
    },
    {
      "regionCode": "JP",
      "regionName": "日本",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "R"
    },
    {
      "regionCode": "RU",
      "regionName": "俄罗斯",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "E"
    },
    {
      "regionCode": "CA",
      "regionName": "加拿大",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "J"
    },
    {
      "regionCode": "AU",
      "regionName": "澳大利亚",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "A"
    },
    {
      "regionCode": "BR",
      "regionName": "巴西",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "B"
    },
    {
      "regionCode": "ZA",
      "regionName": "南非",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "N"
    },
    {
      "regionCode": "KR",
      "regionName": "韩国",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "H"
    },
    {
      "regionCode": "AR",
      "regionName": "阿根廷",
      "telephoneCountryCode": "***REDACTED***",
      "initial": "A"
    },
    {
      "regionCode": "IT",
      "regionName": "意大利",
     
...<truncated>
```
- 备注:
  - Returns the list of supported country codes shown in the phone dropdown.
  - current crawl reached logged-in state

### `GET /ucenter/openapi/openlogin/getAuthUrl.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/openapi/openlogin/pollResult.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/rest/createAndLoginWithBindEmail.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/rest/createAndLoginWithBindMobile.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/rest/getLogonInfo.xhtml`

- 用途: 获取当前登录会员信息
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "id": 56577659601,
    "nickname": "***REDACTED***",
    "headpic": null,
    "bindMobile": "***REDACTED***",
    "bindEmail": "***REDACTED***",
    "gender": null,
    "mobile": null,
    "appkey": null,
    "email": "***REDACTED***",
    "memberEncode": "Ko_dVa-rQDrapG2Ymz7pu9eMzlVrFqmi291flsU8oIjeGgX4Fu0CD_Uay04WXJPl@0a152d0a"
  },
  "success": true
}
```
- 备注:
  - current crawl reached logged-in state

### `GET /ucenter/rest/logout.xhtml`

- 用途: Logout endpoint.
- 是否需要登录态: `False`
- 证据来源: `local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - Logout endpoint.

### `POST /ucenter/rest/logout.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/rest/pcLoginByPass.xhtml`

- 用途: 账号密码登录，带图片验证码
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "mobileOrEmail": "***REDACTED***",
  "password": "***REDACTED***",
  "captchaId": "***REDACTED***",
  "captcha": "***REDACTED***"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "id": 56577659601,
    "nickname": "***REDACTED***",
    "headpic": null,
    "bindMobile": "***REDACTED***",
    "bindEmail": "***REDACTED***",
    "gender": null,
    "mobile": null,
    "appkey": null,
    "email": "***REDACTED***",
    "memberEncode": "Ko_dVa-rQDrapG2Ymz7pu9eMzlVrFqmi291flsU8oIjeGgX4Fu0CD_Uay04WXJPl@0a152d0a"
  },
  "success": true
}
```
- 备注:
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/rest/sendBindMsg.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /ucenter/rest/sendEmailDynamic.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

## cms

### `POST /thvendor/ad/getNewAdList.xhtml`

- 用途: [crawler] Banner / ad list shown on home + landing pages.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "adflag": "cardlist",
  "originType": "PC"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": 23314,
      "code": "AY6FEMRxz2jp",
      "title": "官网LOGO",
      "subtitle": null,
      "logoUrl": "https://imgtest.antank.cn/pic/thvendor/27378d7c253e49c1.png",
      "type": "link",
      "targetId": null,
      "targetUrl": null,
      "cityCode": null,
      "cityName": null,
      "ranks": 1,
      "remark": null,
      "adflag": "PClogo",
      "starttime": "2026-05-13 18:16:41",
      "endtime": "2099-01-01 00:00:00",
      "status": "Y",
      "category": "F",
      "otherinfo": null,
      "recommandFlag": "N",
      "publishtime": null,
      "originTypes": "PC",
      "operatorid": 63660,
      "operatorName": "M+卡里司马",
      "description": null,
      "labelLocation": null,
      "labelContent": null,
      "productSource": null,
      "productCode": null,
      "stadiumIds": "",
      "productDetail": null,
      "relatedImgs": null,
      "relatedVideo": null,
      "data": null,
      "localCache": false
    }
  ],
  "success": true
}
```
- 备注:
  - [crawler] Banner / ad list shown on home + landing pages.
  - current crawl reached logged-in state

### `POST /thvendor/campaign/getCachedCampaign.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/campaign/getChargeType.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/campaign/listCachedCampaign.xhtml`

- 用途: [crawler] Cached campaign list (homepage).
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": 61,
      "name": "Points (No Review Required)",
      "addressType": "stadium",
      "stadiumId": 69674,
      "stadiumName": "M+ Museum",
      "venueId": 1459,
      "venueName": "Grand Stair",
      "chargeType": "point",
      "chargeAmount": 1.0,
      "agencyId": null,
      "agencyName": null,
      "agencyAddress": null,
      "verified": "N",
      "noShow": "N",
      "noShowCycle": null,
      "noShowTime": null,
      "orderReserveMax": 20,
      "memberReserveMax": 20,
      "dynamicFieldId": null,
      "auditStatus": "pass",
      "status": "Y",
      "displayType": "Y",
      "coverPoster": "https://imgtest.antank.cn/pic/thvendor/f2c57b85f6051cf9.jpg",
      "horizontalPoster": "https://imgtest.antank.cn/pic/thvendor/f2c57b85f6051cf9.jpg",
      "verticalPoster": "https://imgtest.antank.cn/pic/thvendor/f2c57b85f6051cf9.jpg",
      "otherPoster": "https://imgtest.antank.cn/pic/thvendor/f2c57b85f6051cf9.jpg",
      "formStatus": "N",
      "dynamicForm": null,
      "invitationLimit": null,
      "displayOrder": 999,
      "activityIntroduction": "<p>VVVVVVVV</p>\n<p><img src=\"https://imgtest.antank.cn/pic/thvendor/f2c57b85f6051cf9.jpg\" /></p>",
      "activityNotice": "<p>一句话特别GV发</p>",
      "participationNotice": "<p>横幅的</p>",
      "addUserId": 63660,
      "addUserName": "M+卡里司马",
      "updateUserId": 63660,
      "updateUserName": "M+卡里司马",
      "addUserGroupId": 56768,
      "updateUserGroupId": 56768,
      "periodList": null,
      "starttime": "2026-06-01 00:00:00",
      "endtime": "2026-07-31 00:00:00",
      "addtime": "2026-05-11 16:04:24",
      "updatetime": "2026-06-01 10:59:09",
      "labelIds": [
        35
      ],
      "stockSum": 20,
      "useSum": 7,
      "favoritesTotal": 1
    },
    {
      "id": 72,
      "name": "UDUDH",
      "addressType": "stadium",
      "stadiumId": 69632,
      "stadiumName": "M+ Concert",
      "venueId": 1362,
      "venueName": "M+ Concert Hall",
      "chargeType": "free",
      "chargeAmount": null,
      "agencyId": null,
      "agencyName": null,
      "agencyAddress": null,
      "verified": "N",
      "noShow": "Y",
      "noShowCycle": "1",
      "noShowTime": 1,
      "orderReserveMax": 60,
      "memberReserveMax": 60,
      "dynamicFieldId": null,
      "auditStatus": "pass",
      "status": "Y",
      "displayType": "Y",
      "coverPoster": "https://imgtest.antank.cn/pic/theatre/c3dff7d59a314ab2.png",
      "horizon
...<truncated>
```
- 备注:
  - [crawler] Cached campaign list (homepage).
  - current crawl reached logged-in state

### `GET /thvendor/campaign/order/getCampaignOrderConstant.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

## member

### `POST /thvendor/member/address/getMemberAddressById.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/address/getMemberAddressList.xhtml`

- 用途: [crawler] Member shipping address list.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": 20718,
      "memberId": 56577659601,
      "memberName": "***REDACTED***",
      "countryName": "China",
      "countryCode": "10000",
      "postalCode": null,
      "provinceName": "Beijing",
      "provinceCode": "110000",
      "cityName": "Beijing",
      "cityCode": "110000",
      "countyName": "Dongcheng District",
      "countyCode": "110101",
      "address": "sssss",
      "mobile": "***REDACTED***",
      "defaultAddr": "N",
      "contactName": "wangyifan",
      "contactEmail": "***REDACTED***"
    },
    {
      "id": 20719,
      "memberId": 56577659601,
      "memberName": "***REDACTED***",
      "countryName": "China",
      "countryCode": "10000",
      "postalCode": null,
      "provinceName": "Tianjin",
      "provinceCode": "120000",
      "cityName": "Tianjin",
      "cityCode": "120000",
      "countyName": "Heping District",
      "countyCode": "120101",
      "address": "dsfsdfsdfdsf",
      "mobile": "***REDACTED***",
      "defaultAddr": "N",
      "contactName": "wangyifan",
      "contactEmail": "***REDACTED***"
    },
    {
      "id": 20720,
      "memberId": 56577659601,
      "memberName": "***REDACTED***",
      "countryName": "China",
      "countryCode": "10000",
      "postalCode": null,
      "provinceName": "Beijing",
      "provinceCode": "110000",
      "cityName": "Beijing",
      "cityCode": "110000",
      "countyName": "Dongcheng District",
      "countyCode": "110101",
      "address": "ddddd",
      "mobile": "***REDACTED***",
      "defaultAddr": "N",
      "contactName": "wangyifan",
      "contactEmail": "***REDACTED***"
    }
  ],
  "success": true
}
```
- 备注:
  - [crawler] Member shipping address list.
  - current crawl reached logged-in state

### `POST /thvendor/member/address/remove.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/address/save.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/campaign/approval/approvalDetail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/campaign/approval/cancel.xhtml`

- 用途: 取消/撤销相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/campaign/approval/create.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/certification/getVerifyType.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/clearMember/checkCode.xhtml`

- 用途: Step 3 of account-deletion — verify the entered code.
- 是否需要登录态: `True`
- 证据来源: `local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - Step 3 of account-deletion — verify the entered code.

### `POST /thvendor/member/clearMember/checkCode.xhtml`

- 用途: 删除/移除相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`

### `GET /thvendor/member/clearMember/confirm.xhtml`

- 用途: Final step of account-deletion — submit deletion request.
- 是否需要登录态: `True`
- 证据来源: `current_spa_static, local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - Final step of account-deletion — submit deletion request.

### `GET /thvendor/member/clearMember/reasonList.xhtml`

- 用途: List of selectable reasons for leaving (account deletion).
- 是否需要登录态: `True`
- 证据来源: `current_spa_static, local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - List of selectable reasons for leaving (account deletion).

### `GET /thvendor/member/clearMember/sendCode.xhtml`

- 用途: Step 2 of account-deletion — send the verification code.
- 是否需要登录态: `True`
- 证据来源: `local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - Step 2 of account-deletion — send the verification code.

### `POST /thvendor/member/clearMember/sendCode.xhtml`

- 用途: 删除/移除相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`

### `GET /thvendor/member/clearMember/validateWay.xhtml`

- 用途: Step 1 of account-deletion — which channel (email/SMS) to verify on.
- 是否需要登录态: `True`
- 证据来源: `local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - Step 1 of account-deletion — which channel (email/SMS) to verify on.

### `POST /thvendor/member/clearMember/validateWay.xhtml`

- 用途: 删除/移除相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`

### `GET /thvendor/member/common/getDynamicCode.xhtml`

- 用途: 获取电子票动态码
- 是否需要登录态: `True`
- 证据来源: `current_spa_static, current_spa_static_template`
- Query 入参:
```json
{
  "uuid": "${uuid}",
  "needServiceTime": "true"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/common/getFreightByArea.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/coupon/getByStatus.xhtml`

- 用途: 优惠/折扣相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/coupon/getMemberCouponsByStatus.xhtml`

- 用途: [crawler] My coupons, filtered by status (notStart / inUse / expired).
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, current_spa_static_template, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
```json
{
  "status": "notStart"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [],
  "success": true
}
```
- 备注:
  - [crawler] My coupons, filtered by status (notStart / inUse / expired).
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/coupon/orderDetail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/donation/addDonation.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/donation/cancelDonation.xhtml`

- 用途: 取消/撤销相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/donation/getDonationConfig.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/favorites/deleteFavoriteById.xhtml`

- 用途: 删除/移除相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/favorites/isFavorites.xhtml`

- 用途: [deep-crawler] Did the logged-in member favourite this program.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "relatedId": "225529",
  "tag": "program",
  "showToast": "noMsg"
}
```
- 出参样例:
```json
{
  "msg": "Not added to favourites",
  "errcode": "1122",
  "data": null,
  "success": false
}
```
- 备注:
  - [deep-crawler] Did the logged-in member favourite this program.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/favorites/listFavorites.xhtml`

- 用途: [crawler] My wishlist / favorites.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "categoryMaps": {
      "mallcultural": "文创",
      "mallpoint": "积分兑换",
      "agency": "商户",
      "guidepoint": "点位",
      "program": "项目",
      "projectdata": "项目资料",
      "guidemap": "导览地图",
      "campaign": "Event",
      "show": "Performance",
      "activity": "Event"
    },
    "page": {
      "rowTotal": 0,
      "pageSize": 20,
      "pageNo": 1,
      "order": null,
      "sortName": null,
      "queryTotal": true,
      "startRow": 0,
      "total": 0,
      "pageCount": 1
    },
    "stadiumMaps": {},
    "venueMaps": {},
    "resultList": []
  },
  "success": true
}
```
- 备注:
  - [crawler] My wishlist / favorites.
  - current crawl reached logged-in state

### `GET /thvendor/member/favorites/saveFavorites.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/general/getShowTicketInfo.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/getCertificationList.xhtml`

- 用途: [crawler] ID certification status (real-name).
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "resultList": [
      {
        "id": 176790,
        "certificateType": "***REDACTED***",
        "certificateNo": "***REDACTED***",
        "specialFlag": "",
        "verified": "N",
        "selfFlag": "Y",
        "identityChannel": null,
        "identity": "***REDACTED***",
        "realname": "***REDACTED***",
        "age": 36
      },
      {
        "id": 176788,
        "certificateType": "***REDACTED***",
        "certificateNo": "***REDACTED***",
        "specialFlag": "",
        "verified": "N",
        "selfFlag": "N",
        "identityChannel": null,
        "identity": "***REDACTED***",
        "realname": "***REDACTED***",
        "age": 36
      },
      {
        "id": 176795,
        "certificateType": "***REDACTED***",
        "certificateNo": "***REDACTED***",
        "specialFlag": "",
        "verified": "N",
        "selfFlag": "N",
        "identityChannel": null,
        "identity": "***REDACTED***",
        "realname": "***REDACTED***",
        "age": 36
      },
      {
        "id": 176796,
        "certificateType": "***REDACTED***",
        "certificateNo": "***REDACTED***",
        "specialFlag": "",
        "verified": "N",
        "selfFlag": "N",
        "identityChannel": null,
        "identity": "***REDACTED***",
        "realname": "***REDACTED***",
        "age": 36
      },
      {
        "id": 176797,
        "certificateType": "***REDACTED***",
        "certificateNo": "***REDACTED***",
        "specialFlag": "",
        "verified": "N",
        "selfFlag": "N",
        "identityChannel": null,
        "identity": "***REDACTED***",
        "realname": "***REDACTED***",
        "age": 36
      },
      {
        "id": 176798,
        "certificateType": "***REDACTED***",
        "certificateNo": "***REDACTED***",
        "specialFlag": "",
        "verified": "N",
        "selfFlag": "N",
        "identityChannel": null,
        "identity": "***REDACTED***",
        "realname": "***REDACTED***",
        "age": 36
      }
    ],
    "allowVerify": false,
    "supportSpecialFlag": [
      "student",
      "elder"
    ]
  },
  "success": true
}
```
- 备注:
  - [crawler] ID certification status (real-name).
  - current crawl reached logged-in state

### `GET /thvendor/member/getPaymentGatewayList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/getPaymentGatewayList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/info/getMemberInfo.xhtml`

- 用途: [crawler] Logged-in member's core info bundle.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "name": "***REDACTED***",
    "id": 1001895585,
    "description": null,
    "addtime": "2026-05-28 17:26:36",
    "origin": "AUTO",
    "status": "Y",
    "realname": null,
    "email": "***REDACTED***",
    "memberId": 56577659601,
    "otherinfo": null,
    "memberLevelId": 252,
    "mobile": null,
    "cardNo": null,
    "discount": null,
    "endTime": "4764-04-30 11:53:59",
    "point": 0,
    "useRight": "N",
    "beginTime": "2026-06-04 11:53:59",
    "effectiveGrowthValue": 1992150,
    "gender": null,
    "marketingEnabled": "Y",
    "totalExpenditure": null,
    "thirdMemberId": null,
    "memberLevelName": "高级会员",
    "activeTime": "2026-05-28 17:26:36",
    "thirdLevelCode": null,
    "thirdMemberType": null,
    "rightTimefrom": null,
    "rightTimeto": null,
    "memberLeveId": 252,
    "memberLeveCode": "B",
    "membershipBalanceList": null,
    "birthdayAlterConfig": true
  },
  "success": true
}
```
- 备注:
  - [crawler] Logged-in member's core info bundle.
  - current crawl reached logged-in state

### `GET /thvendor/member/info/getPersonalInfo.xhtml`

- 用途: [crawler] Profile page data.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "ecd": null,
    "realname": null,
    "certificateType": null,
    "certificateNo": null,
    "gender": null,
    "birthday": null,
    "email": "***REDACTED***",
    "industry": null,
    "fieldId": null,
    "dynamicJsonValue": null,
    "upgrade": null,
    "alterable": "Y",
    "modifyTimes": 0,
    "totalAlterCount": 0,
    "birthdayMonth": null,
    "thirdBinds": [
      "weixin"
    ],
    "finishAllInfo": false
  },
  "success": true
}
```
- 备注:
  - [crawler] Profile page data.
  - current crawl reached logged-in state

### `GET /thvendor/member/info/getPersonalInfoDynamicField.xhtml`

- 用途: [crawler] Dynamic / custom profile fields.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "id": 205,
    "tag": "personalInfo",
    "category": "personalForm",
    "relatedId": 53440,
    "fields": [
      {
        "name": "region",
        "label": "地区",
        "enLabel": null,
        "subName": "",
        "subLabel": "",
        "description": "",
        "sortNum": 1,
        "dataType": "string",
        "inputType": "input",
        "maxSize": 50,
        "required": "N",
        "checkRule": "",
        "selectValue": "",
        "defaultValue": "",
        "memberView": "Y",
        "memberEdite": "Y",
        "bizScenario": null,
        "componentCategory": null,
        "placeholder": null,
        "selectValueList": null,
        "selectValueMap": null
      },
      {
        "name": "field_lkrwy0",
        "label": "名字",
        "enLabel": null,
        "subName": "",
        "subLabel": "",
        "description": "",
        "sortNum": 1,
        "dataType": "string",
        "inputType": "select",
        "maxSize": 0,
        "required": "N",
        "checkRule": "",
        "selectValue": "name:John",
        "defaultValue": "",
        "memberView": "Y",
        "memberEdite": "Y",
        "bizScenario": null,
        "componentCategory": null,
        "placeholder": null,
        "selectValueList": [
          {
            "value": "name",
            "label": "John"
          }
        ],
        "selectValueMap": {
          "name": "John"
        }
      }
    ],
    "remark": null,
    "defaultLangType": "zh-CN",
    "transFields": {
      "en": [
        {
          "name": "field_lkrwy0",
          "label": null,
          "enLabel": null,
          "subName": null,
          "subLabel": null,
          "description": null,
          "sortNum": null,
          "dataType": null,
          "inputType": null,
          "maxSize": null,
          "required": null,
          "checkRule": null,
          "selectValue": null,
          "defaultValue": null,
          "memberView": null,
          "memberEdite": null,
          "bizScenario": null,
          "componentCategory": null,
          "placeholder": null,
          "selectValueList": null,
          "selectValueMap": null
        }
      ],
      "zh-HK": [
        {
          "name": "field_lkrwy0",
          "label": null,
          "enLabel": null,
          "subName": null,
          "subLabel": null,
          "description": null,
          "sortNum": null,
          "dataType": null,
          "inputType": null,
      
...<truncated>
```
- 备注:
  - [crawler] Dynamic / custom profile fields.
  - current crawl reached logged-in state

### `POST /thvendor/member/mall/getFreightByArea.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/memberRemindEvent/list.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/memberRemindEvent/save.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/activeMembership.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/activeMembershipWithPersionInfo.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/bindPerson/acceptBind.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/bindPerson/startBind.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/cancelOrder.xhtml`

- 用途: 取消未支付订单
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/getMembershipDetail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/getMembershipEncode.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/getMembershipPersonEncode.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/getMemberships.xhtml`

- 用途: [crawler] My membership cards list.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
```json
{
  "pageNo": "1",
  "pageSize": "60",
  "status": "new"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "page": {
      "pageNo": 1,
      "rowTotal": -1,
      "pageSize": 60
    },
    "resultList": [
      {
        "id": 33463,
        "membershipTypeId": "hguzfbt2x83vcgh6",
        "membershipTypeName": "DAN REN RU CHANG",
        "titleImgUrl": "https://imgtest.antank.cn/pic/theatre/ebbc3520da98979f.png",
        "tradeNo": "742606091456006825",
        "cardno": "msc2026060915032905856",
        "cardType": "times",
        "contactName": null,
        "contactHead": null,
        "contactMobile": "***REDACTED***",
        "contactCertType": null,
        "contactCertNo": null,
        "totalnum": 5,
        "usednum": 0,
        "timefrom": null,
        "timeto": null,
        "status": "new",
        "statusText": null,
        "remark": "这是备注内容弄",
        "price": 50.0,
        "totalFee": null,
        "activetime": null,
        "tag": "M+会员",
        "certTag": "normal",
        "memberLevelId": null,
        "memberLevelName": "",
        "checkEndtime": null,
        "continueCheck": null,
        "carNumber": null,
        "dynamicField": null,
        "suportRenew": "Y",
        "suportExpiredRenew": "N",
        "renewDiscountAmount": 25.0,
        "buyType": null,
        "membershipTypePrice": 50.0,
        "stadiumIds": null,
        "stadiumNames": null,
        "activeWithInfo": "Y",
        "persons": null,
        "claimStatus": null,
        "claimStatusText": null,
        "describe": null,
        "defaultActiveStatus": null,
        "platform": "PC",
        "discount": 0.0,
        "paidAmount": 50.0,
        "multiCouponBatchId": null,
        "multiCouponBatchName": null,
        "multiCouponTotalnum": 0,
        "multiCouponUsednum": 0,
        "checkNeedReserve": "N",
        "reserveProgramIds": "",
        "reserveMaxnum": 0,
        "reserveDay": "",
        "balance": 0.0,
        "validTransfer": "N",
        "loginUserid": 56577659601,
        "mobile": null,
        "cardMode": "entrance",
        "originalPrice": 55.0,
        "transfers": "Y",
        "charge": "Y",
        "cardTypeStatus": null,
        "expiredShow": "N",
        "applyRefund": "N",
        "refundStatus": "apply",
        "buyPriorityId": null,
        "memberLevelIcon": null,
        "promotionIcon": null,
        "promotionIds": null,
        "buyPriorityIcon": null,
        "owner": null,
        "exchangeNo": null,
        "multipleCode": "N",
        "showRenewButton": "Y",
        "singlePerson": "Y"
...<truncated>
```
- 备注:
  - [crawler] My membership cards list.
  - current crawl reached logged-in state

### `POST /thvendor/member/membership/getOrderDetail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/getOrderList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/gotoPay.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/sendActiveEmail.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/sendActiveMobile.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/transfer/acceptTransfer.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/transfer/listTransferRecords.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/transfer/startTransfer.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membershiporder/refund/applay.xhtml`

- 用途: 退票/退款相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/partnerMember/available/list.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/partnerMember/identity/bind.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/partnerMember/identity/list.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/partnerMember/identity/unbind.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/record/getMemberRemainPointBeforeTime.xhtml`

- 用途: [crawler] Remaining points expiring soon.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, current_spa_static_template, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "msg": "Points expiry time configuration does not exist.",
  "errcode": "1122",
  "data": null,
  "success": false
}
```
- 备注:
  - [crawler] Remaining points expiring soon.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/record/listMemberPointReceiveRecord.xhtml`

- 用途: [crawler] Point-earning history.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, current_spa_static_template, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "fluctuationType": "increase",
  "pageSize": "10",
  "pageNo": "1"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "actionMaps": {
      "receive": "获赠",
      "receive_refund": "获赠返还",
      "spend": "花积分",
      "spend_refund": "花积分返还"
    },
    "page": {
      "rowTotal": 0,
      "pageSize": 10,
      "pageNo": 1,
      "order": null,
      "sortName": null,
      "queryTotal": true,
      "startRow": 0,
      "total": 0,
      "pageCount": 1
    },
    "resultList": []
  },
  "success": true
}
```
- 备注:
  - [crawler] Point-earning history.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/removeCertification.xhtml`

- 用途: 删除/移除相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/saveCertification.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "realname": "***REDACTED***",
  "certificateType": "***REDACTED***",
  "certificateNo": "***REDACTED***",
  "selfFlag": "N"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "id": 176827,
    "certificateType": "***REDACTED***",
    "certificateNo": "***REDACTED***",
    "specialFlag": "",
    "verified": "N",
    "selfFlag": "N",
    "identityChannel": null,
    "identity": "***REDACTED***",
    "realname": "***REDACTED***",
    "age": 31
  },
  "success": true
}
```
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/subscription/record/eventMsg/getLastSubscriptionRecord.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "programId": "225518"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": null,
  "success": true
}
```
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/subscription/record/eventMsg/mine.xhtml`

- 用途: My event subscriptions / message inbox.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [],
  "success": true
}
```
- 备注:
  - My event subscriptions / message inbox.
  - current crawl reached logged-in state

### `HEAD /thvendor/member/subscription/record/eventMsg/mine.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, current_spa_static`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "*/*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - current crawl reached logged-in state

### `GET /thvendor/member/subscription/record/v2/save.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/toggleSelf.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/transfer/pageList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/transfer/rule/times.xhtml`

- 用途: [crawler] Ticket-transfer rule: allowed times per ticket.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "id": 6,
    "periodType": "week",
    "memberLevelRuleStatus": "Y",
    "times": 2,
    "leftTimes": 2
  },
  "success": true
}
```
- 备注:
  - [crawler] Ticket-transfer rule: allowed times per ticket.
  - current crawl reached logged-in state

### `GET /thvendor/member/wxMsg/cancle/subscribe/schedule/remind.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/wxMsg/subscribe/schedule/remind.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

## member-order

### `POST /thvendor/member/campaign/order/cancelOrder.xhtml`

- 用途: 取消未支付订单
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/campaign/order/create.xhtml`

- 用途: 创建非座位类订单
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/campaign/order/orderDetail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/campaign/order/pageList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/campaign/order/pay.xhtml`

- 用途: 支付/重新支付相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/order/create.xhtml`

- 用途: 创建非座位类订单
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/order/discount/cancelDiscount.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/order/discount/confirmDiscount.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/order/discount/getDiscountRepo.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/order/discount/useDiscount.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/membership/order/discount/usePoint.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/membership/order/renewPayOrder.xhtml`

- 用途: 支付/重新支付相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/order/budgetTicketsRefundPlan.xhtml`

- 用途: 退票/退款相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/order/getAllValidTicketList.xhtml`

- 用途: [crawler] My valid tickets (entry-ready).
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, current_spa_static_template, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
```json
{
  "showToast": "noMsg"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "ticketList": [
      {
        "type": "seat",
        "showId": 19614,
        "playEndTime": "2026-06-25 14:00:00",
        "ticketPriceId": 62852,
        "scheduleId": 19614,
        "colNo": "2",
        "rowNo": "1",
        "venueAreaId": 6339,
        "venueAreaName": "fisrt",
        "seatRemark": null,
        "additionInfoMap": {},
        "checkRecords": null,
        "priceRemark": "",
        "seatLabel": "一楼  1排2座",
        "transport": "express",
        "status": "Y",
        "realname": null,
        "platform": "PC",
        "programId": 225199,
        "tradeNo": "312606042020240946",
        "payStatus": "paid_success",
        "playTime": "2026-06-25 12:00:00",
        "uuid": "TH3F7RXWmDr7Pe0a",
        "certificateType": null,
        "ticketPrice": 10.0,
        "paidtime": "2026-06-04 20:24:16",
        "certificateNo": null,
        "checkType": "paper",
        "printMethod": "ticket",
        "specialFlag": null,
        "barcode": "23416714",
        "printNum": 0,
        "transfer": "N",
        "ticketPriceStr": "HK$10.0",
        "orderQrcode": null,
        "displayPrice": "10.0",
        "allowTransfer": "N",
        "expired": "N",
        "qrcode": null,
        "checkNum": 0,
        "sellType": "1",
        "extraInfo": {}
      },
      {
        "type": "seat",
        "showId": 19614,
        "playEndTime": "2026-06-25 14:00:00",
        "ticketPriceId": 62853,
        "scheduleId": 19614,
        "colNo": "7",
        "rowNo": "6",
        "venueAreaId": 6339,
        "venueAreaName": "fisrt",
        "seatRemark": null,
        "additionInfoMap": {},
        "checkRecords": null,
        "priceRemark": "",
        "seatLabel": "一楼  6排7座",
        "transport": "express",
        "status": "Y",
        "realname": null,
        "platform": "PC",
        "programId": 225199,
        "tradeNo": "312606041950240929",
        "payStatus": "paid_success",
        "playTime": "2026-06-25 12:00:00",
        "uuid": "THVMVageFpAci7ed",
        "certificateType": null,
        "ticketPrice": 20.0,
        "paidtime": "2026-06-04 19:56:35",
        "certificateNo": null,
        "checkType": "paper",
        "printMethod": "ticket",
        "specialFlag": null,
        "barcode": "70647783",
        "printNum": 0,
        "transfer": "N",
        "ticketPriceStr": "HK$20.0",
        "orderQrcode": null,
        "displayPrice": "20.0",
        "allowTransfer": "N",
        "expired": "
...<truncated>
```
- 备注:
  - [crawler] My valid tickets (entry-ready).
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/order/getMemberOrderList.xhtml`

- 用途: [crawler] My orders, paginated + filterable by status.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "pageNo": "1",
  "pageSize": "10",
  "status": "paid",
  "expireFlag": "N"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "souvenirTicketStatusMap": [
      {
        "312606051924241272": {
          "status": -1,
          "templateId": null,
          "claimRecordId": null
        }
      },
      {
        "312606051514241102": {
          "status": -1,
          "templateId": null,
          "claimRecordId": null
        }
      },
      {
        "312606051044240995": {
          "status": -1,
          "templateId": null,
          "claimRecordId": null
        }
      },
      {
        "312606051028240991": {
          "status": -1,
          "templateId": null,
          "claimRecordId": null
        }
      },
      {
        "312606042020240946": {
          "status": -1,
          "templateId": null,
          "claimRecordId": null
        }
      },
      {
        "312606041950240929": {
          "status": -1,
          "templateId": null,
          "claimRecordId": null
        }
      },
      {
        "312606041937240925": {
          "status": -1,
          "templateId": null,
          "claimRecordId": null
        }
      },
      {
        "312606041514240723": {
          "status": -1,
          "templateId": null,
          "claimRecordId": null
        }
      },
      {
        "312606041144240576": {
          "status": -1,
          "templateId": null,
          "claimRecordId": null
        }
      }
    ],
    "showMap": {},
    "scheduleMap": {
      "23913": {
        "channel": "SELF",
        "specialFlag": null,
        "msg": null,
        "playDate": "2026-06-30",
        "supportRefundPlan": "N",
        "visitorBuy": "Y",
        "seatPlanId": 23922,
        "usedStatusMsg": null,
        "usedStatusCode": null,
        "showCalendar": "Y",
        "allowBuy": "Y",
        "refundDeadline": "2026-07-01 08:00:00",
        "supportCart": "N",
        "planType": "normal",
        "availabeNum": 100,
        "showStatus": "Y",
        "fullView": "Y",
        "supportAutoSelect": null,
        "id": 23913,
        "transport": "all",
        "availableNum": 100,
        "status": "Y",
        "enName": null,
        "updatetime": "2026-06-05 11:51:30",
        "addtime": "2026-05-17 00:03:41",
        "programId": 225472,
        "otherinfo": null,
        "cnName": "2026-06-30 19:00",
        "stadiumName": "WestK Performing Arts Centre",
        "playTime": "2026-06-30 19:00:00",
        "advanceSendMin": 0,
        "playEndTime": "2026-06-30 22:00:00",
        "stadiumId": 69643,
        "venueId"
...<truncated>
```
- 备注:
  - [crawler] My orders, paginated + filterable by status.
  - current crawl reached logged-in state

### `GET /thvendor/member/order/getTicketInfo.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/order/refundOrderDetails.xhtml`

- 用途: 退票/退款相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/combo/order/cancelOrder.xhtml`

- 用途: 取消未支付订单
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/combo/order/create.xhtml`

- 用途: 创建非座位类订单
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/combo/order/orderDetail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/combo/order/pay.xhtml`

- 用途: 支付/重新支付相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/combo/order/repeatedPayOrder.xhtml`

- 用途: 支付/重新支付相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/combo/order/updateContact.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/combo/order/updateDelivery.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/combo/order/updateTransport.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/order/budgetTicketsRefundPlan.xhtml`

- 用途: 退票/退款相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/order/cancelOrder.xhtml`

- 用途: 取消未支付订单
- 是否需要登录态: `True`
- 证据来源: `legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "tradeNo": "412606061541241407",
  "showToast": "noMsg"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "msg": "success",
  "errcode": "0000",
  "data": null,
  "success": true
}
```

### `GET /thvendor/member/show/order/changeOrderCerts.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/order/create.xhtml`

- 用途: 创建非座位类订单
- 是否需要登录态: `True`
- 证据来源: `legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en",
  "orderkey": "2606061541jcmzfpcdfe0b69332e5690"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "command": {
    "platform": "PC",
    "requestType": "encryption",
    "showId": "90051589",
    "items": [
      {
        "ticketTypeId": "54604",
        "ticketType": "normal",
        "quantity": 1
      }
    ]
  },
  "showToast": "noMsg"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "tradeNo": "412606061541241407",
    "thirdPartOrderInfo": null
  },
  "success": true
}
```

### `GET /thvendor/member/show/order/orderDetail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/order/pay.xhtml`

- 用途: 支付/重新支付相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/order/refundOrder.xhtml`

- 用途: 退票/退款相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/order/refundOrderDetails.xhtml`

- 用途: 退票/退款相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/order/saveOutOfStockRegistration.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/order/updateShowOrderContactName.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/order/updateShowOrderExpressFee.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/order/updateShowOrderTransport.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/order/autoLock.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/order/cancelOrder.xhtml`

- 用途: 取消未支付订单
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/order/changeOrderCerts.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/order/create.xhtml`

- 用途: 创建非座位类订单
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/order/create2.xhtml`

- 用途: 创建座位类订单
- 是否需要登录态: `True`
- 证据来源: `legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en",
  "orderkey": "2606061539ssmxphe20dfd4812d8c37a"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "requestType": "encryption",
  "createOrderReq": {
    "platform": "PC",
    "scheduleId": "19614",
    "seats": [
      {
        "ticketPriceId": 62852,
        "ticketPrice": 10,
        "venueAreaId": 6339,
        "packCode": null,
        "rowNo": "1",
        "colNo": "12"
      }
    ]
  },
  "showToast": "noMsg"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": "312606061539241406",
  "success": true
}
```

### `POST /thvendor/member/ticket/order/createOrder.xhtml`

- 用途: 创建非座位类订单
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/order/detail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/order/payOrder.xhtml`

- 用途: 支付/重新支付相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/order/refundOrder.xhtml`

- 用途: 退票/退款相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/order/unLockSeat.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/order/updateTicketOrderContactName.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/order/updateTicketOrderExpressFee.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/order/updateTicketOrderTransport.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

## payment

### `POST /pay/cybersource/payment/create.xhtml`

- 用途: 创建 CyberSource 支付请求/支付参数
- 是否需要登录态: `False`
- 证据来源: `current_spa_static`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "_payment_payload": "静态推断；本次未走支付页，需支付流程抓包补完整字段"
}
```
- 出参样例:
`无样例 / 未抓到`

## sms

### `POST /sms/common/commonUpload.xhtml`

- 用途: 通用文件上传
- 是否需要登录态: `False`
- 证据来源: `current_spa_static`
- Header / 相关请求头样例:
```json
{
  "content-type": "multipart/form-data"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "file": "<binary>",
  "uploadToken": "***REDACTED***"
}
```
- 出参样例:
`无样例 / 未抓到`

## thvendor

### `GET /thvendor/adinfo/getAdContentByIds.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/adinfo/getAdInfoById.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "id": "23343"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "id": 23343,
    "code": "3epQncFJfBig",
    "title": "Privacy Policy",
    "subtitle": null,
    "logoUrl": null,
    "type": "content",
    "targetId": null,
    "targetUrl": null,
    "cityCode": null,
    "cityName": null,
    "ranks": 1,
    "remark": null,
    "adflag": "privacy_policy",
    "starttime": "2026-05-21 11:53:17",
    "endtime": "2099-01-01 00:00:00",
    "status": "Y",
    "category": "F",
    "otherinfo": null,
    "recommandFlag": "N",
    "publishtime": null,
    "originTypes": "APP,PC",
    "operatorid": 63660,
    "operatorName": "M+卡里司马",
    "description": "<p style=\"text-align: center;\"><span style=\"font-size: 12px;\"><strong>西九文化票务网站隐私政策</strong></span></p>\n<p>&nbsp;</p>\n<p style=\"line-height: 2;\"><span style=\"font-size: 12px;\">版本生效日...<truncated>",
    "labelLocation": null,
    "labelContent": null,
    "productSource": null,
    "productCode": null,
    "stadiumIds": "",
    "productDetail": null,
    "relatedImgs": null,
    "relatedVideo": null,
    "data": null,
    "localCache": false
  },
  "success": true
}
```
- 备注:
  - current crawl reached logged-in state

### `GET /thvendor/campaignLabel/listCampaignLabel.xhtml`

- 用途: [crawler] Campaign labels / categories.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "companyId": 53440,
      "addtime": "2026-04-27 10:09:04",
      "updatetime": "2026-04-27 10:09:04",
      "id": 28,
      "name": "Free Activity",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-04-27 10:09:14",
      "updatetime": "2026-04-27 10:09:14",
      "id": 29,
      "name": "Outdoor Entertainment",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-04-27 10:26:53",
      "updatetime": "2026-04-27 10:26:53",
      "id": 30,
      "name": "Points",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-05-11 13:40:20",
      "updatetime": "2026-05-11 13:40:20",
      "id": 33,
      "name": "Kung Fu Master",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-05-11 13:40:24",
      "updatetime": "2026-05-11 13:40:24",
      "id": 34,
      "name": "",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-05-11 13:40:29",
      "updatetime": "2026-05-11 13:40:29",
      "id": 35,
      "name": "en",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-05-11 13:40:33",
      "updatetime": "2026-05-11 13:40:33",
      "id": 36,
      "name": "National Defense University",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-05-11 13:40:47",
      "updatetime": "2026-05-11 13:40:47",
      "id": 37,
      "name": "",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-05-11 13:40:52",
      "updatetime": "2026-05-11 13:40:52",
      "id": 38,
      "name": "",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-05-11 13:40:59",
      "updatetime": "2026-05-11 13:40:59",
      "id": 39,
      "name": "",
      "sortNum": 0
    },
    {
      "companyId": 53440,
      "addtime": "2026-05-11 13:41:13",
      "updatetime": "2026-05-11 13:41:13",
      "id": 40,
      "name": "",
      "sortNum": 0
    }
  ],
  "success": true
}
```
- 备注:
  - [crawler] Campaign labels / categories.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/common/getCityList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/common/getCountryAllList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/common/getCountyList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/common/getProvinceAllList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/common/getProvinceList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/common/getServerTime.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/common/prepareUpload.xhtml`

- 用途: 准备上传并获取 uploadToken
- 是否需要登录态: `False`
- 证据来源: `current_spa_static`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`

### `GET /thvendor/companyBaseInfo/getDisplayConfig.xhtml`

- 用途: [crawler] Per-site display config loaded on every page entry.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "decimalPlaces": 1,
    "displayUnit": "HK$"
  },
  "success": true
}
```
- 备注:
  - [crawler] Per-site display config loaded on every page entry.
  - current crawl reached logged-in state

### `GET /thvendor/dynamicvalue/getDynamicValueListByField.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/favorites/getFavoritesTotal.xhtml`

- 用途: [deep-crawler] Aggregate favourite count for a program.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "tag": "program",
  "relatedId": "225529"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": 7,
  "success": true
}
```
- 备注:
  - [deep-crawler] Aggregate favourite count for a program.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/favorites/memberFavoritesCategory.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/getCaptchaId.xhtml`

- 用途: 获取验证码会话 ID
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/getStadiums.xhtml`

- 用途: [crawler] Venue / stadium list.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": 69934,
      "cnName": "多BU冒烟场馆20260517001620",
      "enName": null,
      "cnAddress": "Smoke Test",
      "telephone": null,
      "provinceCode": "810000",
      "cityCode": "810000",
      "countyCode": "810000",
      "provinceName": "香港特别行政区",
      "cityName": "香港",
      "countyName": "市辖区",
      "sortNum": 19000,
      "briefName": "多BU场馆",
      "logo": null,
      "addtime": "2026-05-17 00:16:22",
      "updatetime": "2026-05-17 00:16:22",
      "status": "Y",
      "longitude": null,
      "latitude": null,
      "businessHours": null,
      "stadiumExtendVo": null,
      "venueVos": null,
      "categoryVos": null
    },
    {
      "id": 69933,
      "cnName": "多BU冒烟场馆20260516235245",
      "enName": null,
      "cnAddress": "Smoke Test",
      "telephone": null,
      "provinceCode": "810000",
      "cityCode": "810000",
      "countyCode": "810000",
      "provinceName": "香港特别行政区",
      "cityName": "香港",
      "countyName": "市辖区",
      "sortNum": 18000,
      "briefName": "多BU场馆",
      "logo": null,
      "addtime": "2026-05-16 23:52:47",
      "updatetime": "2026-05-16 23:52:47",
      "status": "Y",
      "longitude": null,
      "latitude": null,
      "businessHours": null,
      "stadiumExtendVo": null,
      "venueVos": null,
      "categoryVos": null
    },
    {
      "id": 69932,
      "cnName": "多BU冒烟场馆20260516232928",
      "enName": null,
      "cnAddress": "Smoke Test",
      "telephone": null,
      "provinceCode": "810000",
      "cityCode": "810000",
      "countyCode": "810000",
      "provinceName": "香港特别行政区",
      "cityName": "香港",
      "countyName": "市辖区",
      "sortNum": 17000,
      "briefName": "多BU场馆",
      "logo": null,
      "addtime": "2026-05-16 23:29:30",
      "updatetime": "2026-05-16 23:29:30",
      "status": "Y",
      "longitude": null,
      "latitude": null,
      "businessHours": null,
      "stadiumExtendVo": null,
      "venueVos": null,
      "categoryVos": null
    },
    {
      "id": 69931,
      "cnName": "多BU冒烟场馆20260516230923",
      "enName": null,
      "cnAddress": "Smoke Test",
      "telephone": null,
      "provinceCode": "810000",
      "cityCode": "810000",
      "countyCode": "810000",
      "provinceName": "香港特别行政区",
      "cityName": "香港",
      "countyName": "市辖区",
      "sortNum": 16000,
      "briefName": "多BU场馆",
      "logo": null,
      "addtime": "2026-05-16 23:09:25",
      "updatetime": "2026-05-16 23:09:25",
    
...<truncated>
```
- 备注:
  - [crawler] Venue / stadium list.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/mall/getCulturalProductDetail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/membership/bindPerson/getBind.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/membership/getDetail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/membership/getList.xhtml`

- 用途: [crawler] Public membership plans list (anonymous browse).
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
```json
{
  "tag": "PA会员"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": "hguzfbt2x83vcgh6",
      "name": "DAN REN RU CHANG",
      "stadiumIds": null,
      "stadiumNames": null,
      "price": 50.0,
      "cardType": "times",
      "cardTypeName": "次卡",
      "titleImgUrl": "https://imgtest.antank.cn/pic/theatre/ebbc3520da98979f.png",
      "transferImgUrl": "https://imgtest.antank.cn/pic/theatre/ebbc3520da98979f.png",
      "suitRemark": null,
      "remark": "vnfsdhgdjbvhxb",
      "tag": "M+会员",
      "certTag": "normal",
      "buId": 25,
      "dayNum": 30,
      "validStartDate": null,
      "validEndDate": null,
      "suportRenew": "Y",
      "renewDiscountAmount": 25.0,
      "multiCouponTotalnum": null,
      "dynamicValue": "{\"fieldId\": 207}",
      "checkFace": "Y",
      "longId": 1000457,
      "originalPrice": 55.0,
      "promotionId": null,
      "allowGrowth": "N",
      "allowPoint": "N",
      "supportQuickBuy": "Y",
      "supportAutoRenew": null,
      "dynamicValueMap": {
        "fieldId": 207
      }
    },
    {
      "id": "4yy4p4pak2rkvzdx",
      "name": "DUO REN CI KA",
      "stadiumIds": "69632,69920,69674,69927,69928,69719,69643",
      "stadiumNames": "M+ Concert中,M+ Recital Hall,M+博物馆,Westk1,Westk21,香港故宫文化博物馆,西九演艺",
      "price": 35.0,
      "cardType": "times",
      "cardTypeName": "次卡",
      "titleImgUrl": "https://imgtest.antank.cn/pic/theatre/119fc4a2fb56a769.png",
      "transferImgUrl": "https://imgtest.antank.cn/pic/theatre/119fc4a2fb56a769.png",
      "suitRemark": null,
      "remark": "DUORENCIKABEIHZUNEIRONG",
      "tag": "M+会员",
      "certTag": "normal",
      "buId": 25,
      "dayNum": 30,
      "validStartDate": null,
      "validEndDate": null,
      "suportRenew": "Y",
      "renewDiscountAmount": 10.0,
      "multiCouponTotalnum": null,
      "dynamicValue": "{\"fieldId\": 207}",
      "checkFace": "Y",
      "longId": 1000455,
      "originalPrice": 30.0,
      "promotionId": null,
      "allowGrowth": "N",
      "allowPoint": "N",
      "supportQuickBuy": "Y",
      "supportAutoRenew": "N",
      "dynamicValueMap": {
        "fieldId": 207
      }
    },
    {
      "id": "t4ub36gazfz8cj22",
      "name": "M+ Family Membership (Preview)",
      "stadiumIds": "69632,69674,69719,69643",
      "stadiumNames": "M+ Concert中,M+博物馆,香港故宫文化博物馆,西九演艺",
      "price": 12.0,
      "cardType": "times",
      "cardTypeName": "次卡",
      "titleImgUrl": "https://imgtest.antank.cn/pic/theatre/b3ee04ef3b04b42c.png",
      "transfe
...<truncated>
```
- 备注:
  - [crawler] Public membership plans list (anonymous browse).
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/membership/transfer/getTransfer.xhtml`

- 用途: 会员卡/会员权益相关接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/programcalendar/querySchedulesByDate.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
```json
{
  "dateFrom": "2026-06-01",
  "dateTo": "2026-06-30"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "programId": 225562,
      "programName": "项目名称 en",
      "fullCnName": "项目名称 en",
      "playDate": "2026-06-01",
      "playTime": "08:00",
      "supportSeat": "N",
      "showSite": null
    },
    {
      "programId": 225518,
      "programName": "Full Access Ticket (Gallery 1-9) (Flex) Preview",
      "fullCnName": "Full Access Ticket (Gallery 1-9) (Flex) Preview",
      "playDate": "2026-06-01",
      "playTime": "10:00",
      "supportSeat": "N",
      "showSite": "Weblist,home,list,xhshome,xhslist,douyinHome,douyinList,calendar,homeHotSale,PCrecList2,PCrecList1,WebSite"
    },
    {
      "programId": 225201,
      "programName": "2026 Lo Ta-yu Spring Dragon Symphony Night Concert - Shanghai Station",
      "fullCnName": "2026 Lo Ta-yu Spring Dragon Symphony Night Concert - Shanghai Station",
      "playDate": "2026-06-01",
      "playTime": "11:00",
      "supportSeat": "N",
      "showSite": "WebSite,Weblist,kHome,home,list,homeHotSale,homeHotSalePC"
    },
    {
      "programId": 225562,
      "programName": "项目名称 en",
      "fullCnName": "项目名称 en",
      "playDate": "2026-06-02",
      "playTime": "08:00",
      "supportSeat": "N",
      "showSite": null
    },
    {
      "programId": 225201,
      "programName": "2026 Lo Ta-yu Spring Dragon Symphony Night Concert - Shanghai Station",
      "fullCnName": "2026 Lo Ta-yu Spring Dragon Symphony Night Concert - Shanghai Station",
      "playDate": "2026-06-02",
      "playTime": "11:00",
      "supportSeat": "N",
      "showSite": "WebSite,Weblist,kHome,home,list,homeHotSale,homeHotSalePC"
    },
    {
      "programId": 225539,
      "programName": "Service Fee Test Project",
      "fullCnName": "Service Fee Test Project",
      "playDate": "2026-06-06",
      "playTime": "08:00",
      "supportSeat": "N",
      "showSite": "WebSite,Weblist,home,list"
    },
    {
      "programId": 225528,
      "programName": "Full Access Ticket (Gallery 1-9) Preview",
      "fullCnName": "Full Access Ticket (Gallery 1-9) Preview",
      "playDate": "2026-06-16",
      "playTime": "00:00",
      "supportSeat": "N",
      "showSite": "Weblist,home,list,xhshome,xhslist,douyinHome,douyinList,calendar,homeHotSale,PCrecList2,PCrecList1,WebSite"
    },
    {
      "programId": 225528,
      "programName": "Full Access Ticket (Gallery 1-9) Preview",
      "fullCnName": "Full Access Ticket (Gallery 1-9) Preview",
      "playDate": "2026-06-17",
      "playTime": "00:00"
...<truncated>
```
- 备注:
  - current crawl reached logged-in state

### `GET /thvendor/tools/qrcode.xhtml`

- 用途: 生成二维码图片
- 是否需要登录态: `False`
- 证据来源: `current_spa_static`
- Query 入参:
```json
{
  "text": "${text}",
  "backColor": "ffffff",
  "frontColor": "000000"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`

### `POST /thvendor/wxMsg/schedule/v2/remind.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

## ticketing

### `POST /thvendor/member/cart/cancel.xhtml`

- 用途: 取消/撤销相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/cart/cancelCartItem.xhtml`

- 用途: 取消/撤销相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/cart/cancelCartItemsBySession.xhtml`

- 用途: 取消/撤销相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/cancelPackOrder.xhtml`

- 用途: 取消/撤销相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/clearShippingInfo.xhtml`

- 用途: 删除/移除相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/confirmCart.xhtml`

- 用途: 购物车相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/discount/addPromoCode.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/discount/cancel.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/discount/confirm.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/discount/getRepo.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/discount/removePromoCode.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/discount/use.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/discount/usePoint.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/discount/validatePromoCode.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/getCartDetail.xhtml`

- 用途: [crawler] Current cart contents.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "tradeNo": "CT2606221555266452"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "cart": {
      "tradeNo": "CT2606221555266452",
      "orderType": "cart",
      "mobile": null,
      "memberName": "***REDACTED***",
      "validtime": "2026-06-22 23:55:57",
      "status": "init",
      "contactMobile": null,
      "createdType": null,
      "createdTradeNo": null,
      "addtime": "2026-06-22 15:55:57",
      "timeout": false,
      "remainSeconds": 21392
    },
    "cartList": [],
    "validtime": "2026-06-22 23:55:57",
    "totalCount": 0,
    "totalAmount": 0.0,
    "totalDiscount": 0.0,
    "deliveryOptions": [],
    "programMap": {},
    "packPriceMap": {},
    "ticketTypeMap": {},
    "ticketPriceMap": {},
    "specialPackPrices": {},
    "availablePackPrices": {},
    "seatInfoMap": {}
  },
  "success": true
}
```
- 备注:
  - [crawler] Current cart contents.
  - current crawl reached logged-in state

### `POST /thvendor/member/cart/getPackOrder.xhtml`

- 用途: 购物车相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/initTicketCart.xhtml`

- 用途: [crawler] Initialise a ticket cart session.
- 是否需要登录态: `True`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "platform": "PC"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "companyId": 53440,
    "addtime": "2026-06-06 15:32:46",
    "updatetime": "2026-06-06 15:32:46",
    "id": 652,
    "version": 0,
    "tradeNo": "CT2606061532241403",
    "orderType": "cart",
    "mobile": null,
    "memberId": 56577659601,
    "memberName": "***REDACTED***",
    "origin": null,
    "validtime": "2026-06-06 23:32:46",
    "platform": "PC",
    "clientIp": "133.18.114.45",
    "tbsUserId": null,
    "status": "init",
    "contactMobile": null,
    "appkey": "ShanghaiCS",
    "appid": "wxf90d95915c0d3bd5",
    "openid": "app210-56577659601",
    "createdType": null,
    "createdTradeNo": null,
    "cartItems": null,
    "timeout": false
  },
  "success": true
}
```
- 备注:
  - [crawler] Initialise a ticket cart session.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/setContactInfo.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/setDonation.xhtml`

- 用途: 购物车相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/setShippingInfo.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/setShippingInfoBySubOrders.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/setSingleOrderCert.xhtml`

- 用途: 购物车相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/show/addShowItems.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/ticket/addSeatItems.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/ticket/autoAddSeatItems.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/ticket/changeSeatPack.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/ticket/cleanSeatPack.xhtml`

- 用途: 购物车相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/updateItemCert.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/cart/upsertCartCert.xhtml`

- 用途: 购物车相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/addon/addonSplicing.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/addon/createAddonCulturalOrder.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/addon/getAddonDiscount.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/addon/getAvaiableAddonProductList.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/change/create.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/change/getChangeDetailInfo.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/change/getContainer.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/change/getOrder.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/change/preCreate.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/change/selectSeats.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/combo/options.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/date.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/dateListWithSellOut.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/discount/addItemToRepoByCode.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/discount/cancelDiscount.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/discount/confirmDiscount.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/discount/getDiscountRepo.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/discount/removeItemFromRepoByCode.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/discount/useDiscount.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/discount/usePoint.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/eticketTemplate/findByProgram.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/listBydate.xhtml`

- 用途: 获取非座位类场次列表
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "programKey": "2606061541vgbsbb71999a0099d8ee95",
  "programId": "225518"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "channel": "SELF",
      "ticketTypes": null,
      "msg": null,
      "playDate": null,
      "codeMedium": null,
      "reserveType": "order",
      "reserveProgramId": null,
      "queueShow": null,
      "supportRefundPlan": "N",
      "visitorBuy": "Y",
      "supportReserve": "N",
      "usedStatusMsg": "正常",
      "usedStatusCode": "comfort",
      "reserveWeek": null,
      "showCalendar": "Y",
      "allowBuy": "Y",
      "throughFlag": "Y",
      "maxnum": 100,
      "showAvaliableEntrynum": 94,
      "prices": [
        135.0,
        270.0
      ],
      "refundDeadline": null,
      "clientTicketConfigId": null,
      "supportCart": "N",
      "toProgramId": null,
      "shareReserveTag": null,
      "pairingSeat": "N",
      "id": 90051589,
      "transport": "eTicket",
      "availableNum": 594,
      "status": "Y",
      "enName": null,
      "updatetime": "2026-06-01 13:26:35",
      "addtime": "2026-06-01 13:26:33",
      "programId": 225518,
      "otherinfo": null,
      "cnName": "六月（June 2026）",
      "stadiumName": "香港故宫文化博物馆",
      "playTime": "2026-06-01 10:00:00",
      "advanceSendMin": 0,
      "playEndTime": "2026-06-30 20:00:00",
      "stadiumId": 69719,
      "venueId": 1834,
      "remark": null,
      "maxBuyPerMember": 10,
      "givePoint": 0,
      "fixed": "N",
      "opentime": "2026-05-01 00:00:00",
      "closetime": "2026-08-31 00:00:00",
      "advanceMin": 0,
      "checkcard": "N",
      "paymentLimit": null,
      "transfer": "Y",
      "scheduleShowPrice": null,
      "unionFlag": "promotion",
      "advanceTime": "2026-05-01 00:00:00",
      "maxBuyLimit": 9999,
      "venueName": "展厅1-9",
      "externalTime": "2026-05-01 00:00:00",
      "externalEndTime": "2026-08-31 00:00:00",
      "outOfStockPriceIds": [],
      "printMethod": "ticket",
      "checkType": "eTicket",
      "display": "Y",
      "takeType": "eTicket",
      "showStatus": "Y",
      "sessionKey": "***REDACTED***"
    },
    {
      "channel": "SELF",
      "ticketTypes": null,
      "msg": null,
      "playDate": null,
      "codeMedium": null,
      "reserveType": "order",
      "reserveProgramId": null,
      "queueShow": null,
      "supportRefundPlan": "N",
      "visitorBuy": "Y",
      "supportReserve": "N",
      "usedStatusMsg": "正常",
      "usedStatusCode": "comfort",
      "reserveWeek": null,
      "showCalendar": "Y",
      "allowBuy": "Y",
      "throughFlag": "Y",
      "maxnum"
...<truncated>
```
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/show/tickettype/list.xhtml`

- 用途: 获取非座位类票种列表
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "sessionKey": "***REDACTED***",
  "programKey": "2606061541vgbsbb71999a0099d8ee95",
  "showId": "90051589"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": 54606,
      "ticketType": "normal",
      "code": "STAN",
      "cnName": "Standard ticket",
      "briefName": null,
      "status": "Y",
      "price": 270.0,
      "priceStr": "HK$270.0",
      "originalPrice": null,
      "programId": 225518,
      "description": null,
      "remark": null,
      "availableNum": 98,
      "combType": null,
      "subItems": null,
      "labels": null,
      "priceLimitId": null,
      "priceLimit": null,
      "minBuyNum": 0,
      "sortNum": 6,
      "otherinfo": null
    },
    {
      "id": 54604,
      "ticketType": "normal",
      "code": "FTSC",
      "cnName": "Concession - Fulltime Student",
      "briefName": null,
      "status": "Y",
      "price": 135.0,
      "priceStr": "HK$135.0",
      "originalPrice": null,
      "programId": 225518,
      "description": null,
      "remark": null,
      "availableNum": 98,
      "combType": null,
      "subItems": null,
      "labels": null,
      "priceLimitId": null,
      "priceLimit": null,
      "minBuyNum": 0,
      "sortNum": 5,
      "otherinfo": null
    },
    {
      "id": 54603,
      "ticketType": "normal",
      "code": "CSEN",
      "cnName": "Concession - Senior (Aged 60 and above)",
      "briefName": null,
      "status": "Y",
      "price": 135.0,
      "priceStr": "HK$135.0",
      "originalPrice": null,
      "programId": 225518,
      "description": null,
      "remark": null,
      "availableNum": 99,
      "combType": null,
      "subItems": null,
      "labels": null,
      "priceLimitId": null,
      "priceLimit": null,
      "minBuyNum": 0,
      "sortNum": 4,
      "otherinfo": null
    },
    {
      "id": 54602,
      "ticketType": "normal",
      "code": "DISU",
      "cnName": "Concession - People with Disabilities",
      "briefName": null,
      "status": "Y",
      "price": 135.0,
      "priceStr": "HK$135.0",
      "originalPrice": null,
      "programId": 225518,
      "description": null,
      "remark": null,
      "availableNum": 100,
      "combType": null,
      "subItems": null,
      "labels": null,
      "priceLimitId": null,
      "priceLimit": null,
      "minBuyNum": 0,
      "sortNum": 3,
      "otherinfo": null
    },
    {
      "id": 54600,
      "ticketType": "normal",
      "code": "DISM",
      "cnName": "Concession - Companion for People with Disabilities",
      "briefName": null,
      "status": "Y",
      "price": 135.0,
      "priceStr": "HK$135.0",
      
...<truncated>
```
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/transfer/acceptTransfer.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/show/transfer/startTransfer.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/addon/addonSplicing.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/addon/createAddonCulturalOrder.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/addon/getAddonDiscount.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/addon/getAvaiableAddonProductList.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/change/create.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/change/getContainer.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/change/getOrder.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/change/getSeatInfo.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/change/preCreate.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/change/selectSeats.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/discount/addItemToRepoByCode.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/discount/cancelDiscount.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/discount/confirmDiscount.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/discount/getDiscountRepo.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/discount/removeItemFromRepoByCode.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/discount/useDiscount.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/discount/usePoint.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/getAvailableSeats2.xhtml`

- 用途: Get seat-map availability for a given schedule.
- 是否需要登录态: `True`
- 证据来源: `current_spa_static, local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - Get seat-map availability for a given schedule.

### `POST /thvendor/member/ticket/getAvailableSeats2.xhtml`

- 用途: 获取座位图可售座位和 orderKey
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "scheduleId": "19614",
  "promotionCode": "",
  "watchServer": "true",
  "showToast": "noMsg"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "orderKey": "2606061537pdmvqz66c7ecb80980cb11",
    "seats": [
      {
        "ticketPriceId": 62907,
        "venueAreaId": 52161,
        "seats": "C:31,C:32,C:33,C:34,C:35,C:36,C:37,D:27,D:28,D:29,D:30,D:31,D:32,D:33,D:35,D:36,D:37,D:38,D:39,D:40,E:27,E:28,E:29,E:30,E:31,E:32,E:33,E:34,E:35,E:37,E:38,E:39,E:40,F:27,F:28,F:29,...<truncated>",
        "venueAreaName": "Stalls 堂座"
      },
      {
        "ticketPriceId": 63216,
        "venueAreaId": 52162,
        "seats": "AA:24,AA:25,AA:26,AA:27,AA:28,AA:29,AA:30,AA:31,AA:32,AA:33,AA:35,AA:37,AA:39,AA:44,AA:40",
        "venueAreaName": "Balcony 楼座"
      }
    ]
  },
  "success": true
}
```
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/getGeneralAreaStats.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/getScheduleInfo.xhtml`

- 用途: Get show schedule info for a given product.
- 是否需要登录态: `True`
- 证据来源: `current_spa_static, local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - Get show schedule info for a given product.

### `POST /thvendor/member/ticket/getScheduleInfo.xhtml`

- 用途: 获取座位类场次信息
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "watchServer": "true",
  "scheduleId": "19614",
  "showToast": "noMsg"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "schedule": {
      "id": 23913,
      "programId": 225472,
      "stadiumId": 69643,
      "venueId": 1826,
      "cnName": "2026-06-30 19:00",
      "enName": null,
      "status": "Y",
      "playTime": "2026-06-30 19:00:00",
      "playEndTime": "2026-06-30 22:00:00",
      "opentime": "2026-05-17 00:00:00",
      "closetime": "2026-06-30 23:59:59",
      "display": "auto",
      "advanceMin": 120,
      "checkcard": "F",
      "givePoint": 0,
      "addtime": "2026-05-17 00:03:41",
      "updatetime": "2026-06-05 11:51:30",
      "unionFlag": "coupon,promotion",
      "transport": "all",
      "checkType": "eTicket,paper",
      "takeType": "express,selfservice",
      "printMethod": "ticket",
      "remark": null,
      "fixed": "N",
      "otherinfo": null,
      "transfer": "Y",
      "paymentLimit": null,
      "scheduleShowPrice": null,
      "maxBuyLimit": 100,
      "maxBuyPerMember": 200,
      "advanceSendMin": 0,
      "externalTime": "2026-05-17 00:00:00",
      "externalEndTime": "2026-06-30 23:59:59",
      "venueName": "Xiqu Centre Tea House Theatre",
      "stadiumName": "WestK Performing Arts Centre",
      "availableNum": null,
      "advanceTime": "2026-05-17 00:00:00",
      "outOfStockPriceIds": null,
      "seatPlanId": 23922,
      "fullView": "Y",
      "playDate": "2026-06-30",
      "showCalendar": "Y",
      "allowBuy": "Y",
      "msg": null,
      "planType": "normal",
      "specialFlag": null,
      "usedStatusMsg": null,
      "usedStatusCode": null,
      "supportRefundPlan": "N",
      "supportAutoSelect": null,
      "channel": "SELF",
      "refundDeadline": "2026-07-01 08:00:00",
      "visitorBuy": "Y",
      "supportCart": "N",
      "availabeNum": null,
      "showStatus": "Y"
    },
    "seatPlan": {
      "name": "戏曲中心茶馆剧场（Preview）",
      "id": 23922,
      "channel": "SELF",
      "companyId": 53440,
      "addtime": "2026-05-08 16:51:57",
      "stadiumId": 69643,
      "venueId": 1826,
      "updatetime": "2026-05-09 16:11:57",
      "planNo": "PL53440AT26050816515725",
      "fullView": "Y",
      "seatCount": 148,
      "publishUrl": "https://imgtest.antank.cn/pic/seatplan/publish/53440/v1/PL53440AT26050816515725.json",
      "seatMapRequired": "Y",
      "planType": "normal",
      "background": null,
      "svgBackground": "https://imgtest.antank.cn/pic/theatre/5856c64806db6992.svg",
      "excelUrl": null,
      "areaViewUrl": null,
      "onlineStatus": "N",
    
...<truncated>
```
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/getSchedulePrices.xhtml`

- 用途: Get ticket price tiers for a given schedule.
- 是否需要登录态: `True`
- 证据来源: `current_spa_static, local_wk_endpoints_registry`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - Get ticket price tiers for a given schedule.

### `POST /thvendor/member/ticket/getSchedulePrices.xhtml`

- 用途: 获取座位类票价
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "scheduleId": "19614",
  "promotionCode": "",
  "watchServer": "true",
  "showToast": "noMsg",
  "sessionKey": "***REDACTED***",
  "programKey": "2606061539tgmbzse51f95398fbb4541"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "ticketPriceId": 62907,
      "price": 300.0,
      "color": 0,
      "colorStr": "#FBCC60",
      "description": "",
      "venueAreaId": null,
      "type": "O",
      "display": "Y",
      "remark": "",
      "availableNum": 84,
      "availablePackPrices": [
        {
          "packCode": "20260511AK9hUY",
          "packName": "双人套票",
          "description": null,
          "priceId": 62907,
          "unitNum": 2,
          "ticketPrice": 250.0,
          "updatetime": "2026-05-17 01:00:56",
          "specialFlag": null,
          "realNameVerify": "***REDACTED***",
          "labels": null,
          "availableNum": 42,
          "packPriceId": null
        }
      ],
      "specialPackPrices": [
        {
          "packCode": "202605213Dn9fi",
          "packName": "特惠儿童",
          "description": null,
          "priceId": 62907,
          "unitNum": 1,
          "ticketPrice": 150.0,
          "updatetime": "2026-05-21 14:53:19",
          "specialFlag": "child",
          "realNameVerify": "***REDACTED***",
          "labels": null,
          "availableNum": 84,
          "packPriceId": null
        },
        {
          "packCode": "20260521APgbxR",
          "packName": "特惠学生",
          "description": null,
          "priceId": 62907,
          "unitNum": 1,
          "ticketPrice": 150.0,
          "updatetime": "2026-05-21 14:54:08",
          "specialFlag": "student",
          "realNameVerify": "***REDACTED***",
          "labels": "学生",
          "availableNum": 84,
          "packPriceId": null
        },
        {
          "packCode": "20260521HML74C",
          "packName": "特惠长者",
          "description": null,
          "priceId": 62907,
          "unitNum": 1,
          "ticketPrice": 150.0,
          "updatetime": "2026-05-21 14:54:32",
          "specialFlag": "elder",
          "realNameVerify": "***REDACTED***",
          "labels": "长者",
          "availableNum": 84,
          "packPriceId": null
        }
      ],
      "schedulePriceGroup": null,
      "originalPrice": null,
      "cnName": null
    },
    {
      "ticketPriceId": 62908,
      "price": 350.0,
      "color": 7,
      "colorStr": "#6EABBD",
      "description": "",
      "venueAreaId": null,
      "type": "O",
      "display": "Y",
      "remark": "",
      "availableNum": 0,
      "availablePackPrices": null,
      "specialPackPrices": null,
      "schedulePriceGroup": null,
      "originalPrice": null,
     
...<truncated>
```
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/getSeatImages.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/getSpecialSeatEnableConfig.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/getSpecialSeatOverlay.xhtml`

- 用途: 获取特殊座位覆盖层
- 是否需要登录态: `True`
- 证据来源: `legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "scheduleId": "19614"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "enableConfig": {
      "wheelchair": "Y",
      "table": "Y"
    },
    "runtimeState": {
      "wheelchair": "N",
      "table": "N"
    },
    "seatOverlayList": [
      {
        "seatFullKey": "52162:AA:30",
        "infoType": "obstructed",
        "label": "obstructed",
        "enterpriseEnabled": "Y",
        "specialSaleActive": "N",
        "nosaleApplied": "N",
        "queryState": "OBSTRUCTED_STATIC",
        "tipMessage": "视野受阻座位",
        "relatedSeatKeys": [],
        "tableGroupId": null,
        "tableGroupName": null
      },
      {
        "seatFullKey": "52162:AA:31",
        "infoType": "obstructed",
        "label": "obstructed",
        "enterpriseEnabled": "Y",
        "specialSaleActive": "N",
        "nosaleApplied": "N",
        "queryState": "OBSTRUCTED_STATIC",
        "tipMessage": "视野受阻座位",
        "relatedSeatKeys": [],
        "tableGroupId": null,
        "tableGroupName": null
      },
      {
        "seatFullKey": "52162:AA:32",
        "infoType": "obstructed",
        "label": "obstructed",
        "enterpriseEnabled": "Y",
        "specialSaleActive": "N",
        "nosaleApplied": "N",
        "queryState": "OBSTRUCTED_STATIC",
        "tipMessage": "视野受阻座位",
        "relatedSeatKeys": [],
        "tableGroupId": null,
        "tableGroupName": null
      },
      {
        "seatFullKey": "52162:AA:37",
        "infoType": "obstructed",
        "label": "obstructed",
        "enterpriseEnabled": "Y",
        "specialSaleActive": "N",
        "nosaleApplied": "N",
        "queryState": "OBSTRUCTED_STATIC",
        "tipMessage": "视野受阻座位",
        "relatedSeatKeys": [],
        "tableGroupId": null,
        "tableGroupName": null
      },
      {
        "seatFullKey": "52162:AA:38",
        "infoType": "obstructed",
        "label": "obstructed",
        "enterpriseEnabled": "Y",
        "specialSaleActive": "N",
        "nosaleApplied": "N",
        "queryState": "OBSTRUCTED_STATIC",
        "tipMessage": "视野受阻座位",
        "relatedSeatKeys": [],
        "tableGroupId": null,
        "tableGroupName": null
      },
      {
        "seatFullKey": "52162:AA:28",
        "infoType": "obstructed",
        "label": "obstructed",
        "enterpriseEnabled": "Y",
        "specialSaleActive": "N",
        "nosaleApplied": "N",
        "queryState": "OBSTRUCTED_STATIC",
        "tipMessage": "视野受阻座位",
        "relatedSeatKeys": [],
        "tableGroupId": null,
        "tableGroupName"
...<truncated>
```

### `POST /thvendor/member/ticket/listScheduleByDate.xhtml`

- 用途: 按日期获取座位类场次
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "programKey": "2606061539tgmbzse51f95398fbb4541",
  "programId": "225199",
  "date": "2026-06-30"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "channel": "SELF",
      "specialFlag": "child,student,elder",
      "msg": null,
      "playDate": "2026-06-30",
      "supportRefundPlan": "N",
      "visitorBuy": "Y",
      "seatPlanId": 23922,
      "usedStatusMsg": "正常",
      "usedStatusCode": "comfort",
      "showCalendar": "Y",
      "allowBuy": "Y",
      "refundDeadline": null,
      "supportCart": "N",
      "planType": "normal",
      "availabeNum": 100,
      "showStatus": "Y",
      "fullView": "Y",
      "supportAutoSelect": null,
      "id": 23913,
      "transport": "all",
      "availableNum": 100,
      "status": "Y",
      "enName": null,
      "updatetime": "2026-06-05 11:51:30",
      "addtime": "2026-05-17 00:03:41",
      "programId": 225472,
      "otherinfo": null,
      "cnName": "2026-06-30 19:00",
      "stadiumName": "WestK Performing Arts Centre",
      "playTime": "2026-06-30 19:00:00",
      "advanceSendMin": 0,
      "playEndTime": "2026-06-30 22:00:00",
      "stadiumId": 69643,
      "venueId": 1826,
      "remark": null,
      "maxBuyPerMember": 200,
      "givePoint": 0,
      "fixed": "N",
      "opentime": "2026-05-17 00:00:00",
      "closetime": "2026-06-30 23:59:59",
      "advanceMin": 120,
      "checkcard": "F",
      "paymentLimit": null,
      "transfer": "Y",
      "scheduleShowPrice": null,
      "unionFlag": "coupon,promotion",
      "advanceTime": "2026-05-17 00:00:00",
      "maxBuyLimit": 100,
      "venueName": "Xiqu Centre Tea House Theatre",
      "externalTime": "2026-05-17 00:00:00",
      "externalEndTime": "2026-06-30 23:59:59",
      "outOfStockPriceIds": [
        "62908:350.0"
      ],
      "printMethod": "ticket",
      "checkType": "eTicket,paper",
      "display": "auto",
      "takeType": "express,selfservice",
      "sessionKey": "***REDACTED***"
    },
    {
      "channel": "SELF",
      "specialFlag": "child,student,elder",
      "msg": null,
      "playDate": "2026-06-30",
      "supportRefundPlan": "N",
      "visitorBuy": "Y",
      "seatPlanId": 23958,
      "usedStatusMsg": "正常",
      "usedStatusCode": "comfort",
      "showCalendar": "Y",
      "allowBuy": "Y",
      "refundDeadline": null,
      "supportCart": "N",
      "planType": "complex",
      "availabeNum": 1695,
      "showStatus": "Y",
      "fullView": "Y",
      "supportAutoSelect": null,
      "id": 23914,
      "transport": "all",
      "availableNum": 1695,
      "status": "Y",
      "enName": null,
      "updateti
...<truncated>
```
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/packorder/activeOrder.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/packorder/payOrder.xhtml`

- 用途: 支付/重新支付相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/scheduleDateList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/scheduleDateListWithSellOut.xhtml`

- 用途: 获取有售罄标记的场次日期
- 是否需要登录态: `True`
- 证据来源: `legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "programId": "225472"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "date": "2026-06-30",
      "sellOut": "N"
    },
    {
      "date": "2026-07-31",
      "sellOut": "N"
    },
    {
      "date": "2026-09-04",
      "sellOut": "N"
    },
    {
      "date": "2026-09-05",
      "sellOut": "N"
    }
  ],
  "success": true
}
```

### `GET /thvendor/member/ticket/seasonpack/addPackDetail.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/seasonpack/cancelPackDetail.xhtml`

- 用途: 取消/撤销相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/seasonpack/cancelPackOrder.xhtml`

- 用途: 取消/撤销相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/seasonpack/computeDiscount.xhtml`

- 用途: 优惠/折扣相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/seasonpack/confirmOrder.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/seasonpack/createOrder.xhtml`

- 用途: 创建/保存相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/seasonpack/getOrder.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/seasonpack/getSelected.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/seasonpack/processLastOrder.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/seasonpack/updateContact.xhtml`

- 用途: 更新/变更相关接口
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/ticket/seat/discount/query2.xhtml`

- 用途: 查询座位/票价优惠
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "command": "{\"scheduleId\":\"19614\",\"seats\":[{\"rowNo\":\"1\",\"colNo\":\"12\",\"venueAreaId\":6339,\"packCode\":null}]}"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "scheduleId": 23913,
    "seatCandidates": [
      {
        "seat": {
          "venueAreaId": 52161,
          "rowNo": "C",
          "colNo": "37",
          "seatkey": null,
          "packCode": null,
          "packName": null,
          "packTicketPrice": null
        },
        "priceMode": "ORIGINAL",
        "packPriceType": null,
        "packCode": null,
        "specialFlag": null,
        "realNameVerify": null,
        "originalAmount": 300.0,
        "discountAmount": 0.0,
        "totalAmount": 300.0,
        "items": []
      }
    ],
    "summary": {
      "originalAmount": 300.0,
      "discountAmount": 0.0,
      "totalAmount": 300.0,
      "normalSummary": null,
      "specialSummary": null
    }
  },
  "success": true
}
```
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/transfer/acceptTransfer.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/member/ticket/transfer/startTransfer.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/wxMsg/cancle/subscribe/show/remind.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/member/wxMsg/subscribe/show/remind.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `True`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/program/content/getProgramContentInfo.xhtml`

- 用途: [deep-crawler] Static program detail content (description, images).
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "programId": "225529"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "ticketSnatchingTips": {
      "id": 15,
      "updateUserId": 63660,
      "status": "Y",
      "updatetime": "2025-12-19 13:48:21",
      "addtime": "2025-12-19 13:20:43",
      "companyId": 53440,
      "addUserId": 63660,
      "displayTitle": "抢票攻略",
      "contentType": "ticketSnatchingTips",
      "programContents": [
        {
          "id": 143,
          "contentType": "ticketSnatchingTips",
          "code": "qiangpiao",
          "title": "Ticket Snatching Guide",
          "titleColor": "",
          "sortNum": 0,
          "icon": "",
          "content": "Preparations for Smooth Booking\nPlease update the APP to the latest version and enable notification permissions to receive sale alerts and order notifications timely.\nComplete acco...<truncated>",
          "image": "",
          "status": "Y",
          "systemPreset": "N",
          "addUserId": 63660,
          "updateUserId": 63660,
          "companyId": 53440,
          "addtime": "2026-05-14 14:09:16",
          "updatetime": "2026-05-14 14:44:22"
        },
        {
          "id": 83,
          "contentType": "ticketSnatchingTips",
          "code": "delivery",
          "title": "Pre-fill shipping address",
          "titleColor": "",
          "sortNum": 1,
          "icon": "",
          "content": "This program offers physical tickets, and you can fill in your delivery address in advance.",
          "image": "",
          "status": "Y",
          "systemPreset": "Y",
          "addUserId": 63660,
          "updateUserId": 63660,
          "companyId": 53440,
          "addtime": "2025-12-19 13:20:43",
          "updatetime": "2026-05-17 14:31:21"
        },
        {
          "id": 82,
          "contentType": "ticketSnatchingTips",
          "code": "realName",
          "title": "Pre-fill real-name information",
          "titleColor": "",
          "sortNum": 1,
          "icon": "",
          "content": "This event requires real-name ticket purchasing, and you can fill in the audience information in advance.",
          "image": "",
          "status": "Y",
          "systemPreset": "Y",
          "addUserId": 63660,
          "updateUserId": 63660,
          "companyId": 53440,
          "addtime": "2025-12-19 13:20:43",
          "updatetime": "2026-05-17 14:32:05"
        },
        {
          "id": 85,
          "contentType": "ticketSnatchingTips",
          "code": "notice",
          "title": "测试notice",
          "titleC
...<truncated>
```
- 备注:
  - [deep-crawler] Static program detail content (description, images).
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/program/getCategoryList.xhtml`

- 用途: [crawler] Program / show categories.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "categoryList": [
      "JamesP",
      "测试分类999",
      "演出",
      "Traditional opera",
      "Event",
      "Combo",
      "Public Guided Tour",
      "Exhibition",
      "Screening programs",
      "Performance",
      "vocal concert",
      "Seat selection",
      "Good act",
      "Fashion line",
      "Culture Pass & Special Packages",
      "Curated Routes",
      "2",
      "测试",
      "Permanent Exhibition",
      "Special Exhibition"
    ]
  },
  "success": true
}
```
- 备注:
  - [crawler] Program / show categories.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/program/getProgramNumByStadium.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "stadiumId": "69719"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": 6,
  "success": true
}
```
- 备注:
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/program/promotion/activity/list.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "programId": "225529"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "promotionName": "票务95折促销优惠",
      "scheduleCount": 5,
      "scheduleInfo": [
        "2026-06-30 (Tue) 19:00",
        "2026-06-30 (Tue) 21:00",
        "2026-07-31 (Fri) 19:00",
        "2026-09-04 (Fri) 19:30",
        "2026-09-05 (Sat) 14:30"
      ],
      "allShowAvailable": true
    },
    {
      "promotionName": "促销码测试9折",
      "scheduleCount": 5,
      "scheduleInfo": [
        "2026-06-30 (Tue) 19:00",
        "2026-06-30 (Tue) 21:00",
        "2026-07-31 (Fri) 19:00",
        "2026-09-04 (Fri) 19:30",
        "2026-09-05 (Sat) 14:30"
      ],
      "allShowAvailable": true
    },
    {
      "promotionName": "en1",
      "scheduleCount": 5,
      "scheduleInfo": [
        "2026-06-30 (Tue) 19:00",
        "2026-06-30 (Tue) 21:00",
        "2026-07-31 (Fri) 19:00",
        "2026-09-04 (Fri) 19:30",
        "2026-09-05 (Sat) 14:30"
      ],
      "allShowAvailable": true
    }
  ],
  "success": true
}
```
- 备注:
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/program/promotion/coupon/list.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "programId": "225529",
  "showToast": "noMsg"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": 3165,
      "pid": null,
      "companyId": null,
      "buId": null,
      "prefix": null,
      "tag": null,
      "cardtype": "A",
      "amount": 99999.0,
      "title": "西九-特别展8号厅兑换券-站+座",
      "expression": null,
      "rule": null,
      "remark": null,
      "description": null,
      "category": null,
      "visibletype": null,
      "weektype": null,
      "minfee": null,
      "venueids": null,
      "programids": null,
      "itemids": null,
      "validprice": null,
      "timefrom": "2025-01-01 00:00:00",
      "timeto": "2034-12-31 00:00:00",
      "playtime1": null,
      "playtime2": null,
      "stime1": null,
      "stime2": null,
      "notifymsg": null,
      "daynum": null,
      "delayDays": null,
      "delayFee": null,
      "limitcycle": null,
      "limittime": null,
      "limitnum": null,
      "limitlevel": null,
      "ordertype": null,
      "limitdesc": null,
      "unionFlag": null,
      "updatetime": null,
      "wxCardId": null,
      "channel": null,
      "usageScenario": null,
      "soldcount": null,
      "bindcount": null,
      "avaiableCount": null,
      "totalnum": null,
      "batchType": null,
      "stock": null,
      "hasStock": null,
      "priceRange": null,
      "quantityLimit": null,
      "relateMap": null,
      "platformSubsidy": null,
      "maxfee": null,
      "validTimeType": null,
      "validTimeValue": null,
      "overdueTimePonit": null,
      "selfCheck": null,
      "syschannelids": null,
      "orderTypeRange": null,
      "availableType": null,
      "availableProjectType": null,
      "outChannel": null,
      "outBatchNo": null,
      "receiveUrl": null,
      "transfer": null,
      "claimStatus": "N",
      "discountDesc": "兑换"
    },
    {
      "id": 3195,
      "pid": null,
      "companyId": null,
      "buId": null,
      "prefix": null,
      "tag": null,
      "cardtype": "C",
      "amount": 5.0,
      "title": "西九官网测试券（勿动）—减5元优惠券",
      "expression": null,
      "rule": null,
      "remark": null,
      "description": null,
      "category": null,
      "visibletype": null,
      "weektype": null,
      "minfee": null,
      "venueids": null,
      "programids": null,
      "itemids": null,
      "validprice": null,
      "timefrom": "2025-11-02 00:00:00",
      "timeto": "2030-12-06 23:59:59",
      "playtime1": null,
      "playtime2": null,
      "stime1": null,
      "stime2": null,
      "notifymsg": null,
      
...<truncated>
```
- 备注:
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/program/promotion/member/list.xhtml`

- 用途: [deep-crawler] Membership-tier discount info shown on program page.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "programId": "225529"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [],
  "success": true
}
```
- 备注:
  - [deep-crawler] Membership-tier discount info shown on program page.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/program/promotion/package/ticket/list.xhtml`

- 用途: [deep-crawler] Combo / package ticket options for a program.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "programId": "225529"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": 2853,
      "packCode": null,
      "packName": "双人套票-en",
      "description": "双人套票-en",
      "programId": null,
      "priceId": null,
      "scheduleIds": null,
      "unitNum": null,
      "ticketPrice": null,
      "status": null,
      "unionFlag": null,
      "timefrom": null,
      "timeto": null,
      "packType": null,
      "availableNum": null,
      "combType": null,
      "packPriceItems": null,
      "updatetime": null,
      "specialFlag": null,
      "realNameVerify": null
    }
  ],
  "success": true
}
```
- 备注:
  - [deep-crawler] Combo / package ticket options for a program.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/seat/program/countdown.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "programId": "225528"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "countdown": {
      "programId": 225472,
      "displayCountdown": "Y",
      "displayCountdownPosition": "programDetail,sessionDetail",
      "supportReserve": "Y",
      "salesStartReminder": "Y",
      "session": null,
      "sessions": [
        {
          "sessionId": "***REDACTED***",
          "opentime": "2026-05-08 00:00:00",
          "advanceTime": "2026-05-08 00:00:00",
          "scheduleAdvanceMin": 120
        },
        {
          "sessionId": "***REDACTED***",
          "opentime": "2026-05-08 00:00:00",
          "advanceTime": "2026-05-08 00:00:00",
          "scheduleAdvanceMin": 120
        },
        {
          "sessionId": "***REDACTED***",
          "opentime": "2026-05-14 00:00:00",
          "advanceTime": "2026-05-14 00:00:00",
          "scheduleAdvanceMin": 120
        },
        {
          "sessionId": "***REDACTED***",
          "opentime": "2026-05-17 00:00:00",
          "advanceTime": "2026-05-17 00:00:00",
          "scheduleAdvanceMin": 120
        },
        {
          "sessionId": "***REDACTED***",
          "opentime": "2026-05-17 00:00:00",
          "advanceTime": "2026-05-17 00:00:00",
          "scheduleAdvanceMin": 120
        }
      ],
      "countdownSessions": []
    },
    "serverTime": "2026-06-06 15:36:52"
  },
  "success": true
}
```
- 备注:
  - current crawl reached logged-in state

### `GET /thvendor/seat/program/schedule/countdown.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "programId": "225199",
  "scheduleId": "19614"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "countdown": {
      "programId": 225472,
      "displayCountdown": "Y",
      "displayCountdownPosition": "programDetail,sessionDetail",
      "supportReserve": "Y",
      "salesStartReminder": "Y",
      "session": null,
      "sessions": [
        {
          "sessionId": "***REDACTED***",
          "opentime": "2026-05-17 00:00:00",
          "advanceTime": "2026-05-17 00:00:00",
          "scheduleAdvanceMin": 120
        }
      ],
      "countdownSessions": []
    },
    "serverTime": "2026-06-06 15:37:05"
  },
  "success": true
}
```

### `POST /thvendor/show/combo/entry/list.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
  "lang": "en"
}
```
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
```json
{
  "programId": "225529",
  "advanceMin": "0",
  "showToast": "noMsg"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [],
  "success": true
}
```
- 备注:
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/show/combo/getShowTicketTypes.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/show/combo/listBydate.xhtml`

- 用途: 获取非座位类场次列表
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/show/supportReserveProgramShowList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/show/transfer/getTransfer.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/stand/program/countdown.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
```json
{
  "programId": "225528"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "countdown": {
      "programId": 225472,
      "displayCountdown": "Y",
      "displayCountdownPosition": "programDetail,sessionDetail",
      "supportReserve": "Y",
      "salesStartReminder": "Y",
      "session": null,
      "sessions": null,
      "countdownSessions": null
    },
    "serverTime": "2026-06-22 17:59:44"
  },
  "success": true
}
```
- 备注:
  - current crawl reached logged-in state

### `POST /thvendor/stand/program/show/countdown.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/ticket/program/getHotProgramList.xhtml`

- 用途: [crawler] Hot programs (PC recList) — homepage carousel data.
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, current_spa_static_template, legacy_anticket_har, local_wk_endpoints_registry`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "content-type": "application/json"
}
```
- Query 入参:
```json
{
  "showSite": "Weblist",
  "dynamicValueList": "[]",
  "stadiumId": "",
  "categoryIds": "1030"
}
```
- Body 入参:
```json
{
  "showSite": "PCrecList1"
}
```
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": 225513,
      "cnName": "The AAPPAC 2026 Hong Kong Conference (Preview)",
      "fullCnName": "The AAPPAC 2026 Hong Kong Conference Preview",
      "fullEnName": null,
      "briefName": "亚太表演艺术中心协会香港年会2026",
      "enName": null,
      "stadiumId": 69643,
      "showMode": "calendar",
      "horizontalPoster": "https://imgtest.antank.cn/pic/theatre/d751bf0ddaa8ae5b.jpg",
      "verticalPoster": "https://imgtest.antank.cn/pic/theatre/96714b711af6bf2a.jpg",
      "extraPoster": "https://imgtest.antank.cn/pic/theatre/d751bf0ddaa8ae5b.jpg",
      "otherPoster": "https://imgtest.antank.cn/pic/theatre/d751bf0ddaa8ae5b.jpg",
      "tag": "In progress",
      "venueId": 1838,
      "startTime": "2026-04-06 00:00:00",
      "endTime": "2026-10-09 23:59:59",
      "minPrice": 1400.0,
      "maxPrice": 1400.0,
      "otherinfo": null,
      "supportSeat": "N",
      "addtime": "2026-05-16 12:39:09",
      "updatetime": "2026-06-01 15:10:02",
      "status": "Y",
      "sortNum": 999,
      "saleType": "sale",
      "stadiumName": "WestK Performing Arts Centre",
      "stadiumMobile": "***REDACTED***",
      "venueName": "Freespace",
      "stadiumAddress": "88 Austin Road West, Tsim Sha Tsui, Kowloon (near China Hong Kong City)",
      "dynamicValue": {
        "frontProgramType": "show",
        "autoPopupTicketType": "Y",
        "frontProgramType_label": "演出",
        "autoPopupTicketType_label": "是"
      },
      "showSite": "WebSite,Weblist,PCrecList1,PCrecList2,home,list,homeHotSale,xhshome,xhslist,douyinHome,douyinList,calendar",
      "category": "Event",
      "smallCategory": null,
      "programCode": "POM01013809",
      "agencyId": 0,
      "releaseStartTime": "2026-05-14 12:00:00",
      "releaseEndTime": "2026-10-06 23:59:59",
      "releaseFlag": "Y",
      "dynamicStatus": "N",
      "dynamicFieldResult": null,
      "releaseStartTime2": "2026-05-14 12:00:00",
      "releaseEndTime2": "2026-10-06 23:59:59",
      "stadiumCityCode": "810000",
      "stadiumCityName": null,
      "allowInvoice": "N",
      "pushInvoice": "N",
      "multiGroupCheck": "N",
      "durationType": "through",
      "consumerInvoiceTime": "paid",
      "ticketingNotice": null,
      "serviceTerm": null,
      "faq": null,
      "preFillInfo": null,
      "realNameMaxNum": null,
      "channel": null
    },
    {
      "id": 225472,
      "cnName": "Tea House Theatre Experience",
      "fullCnName": "Tea House Theatre Exp
...<truncated>
```
- 备注:
  - [crawler] Hot programs (PC recList) — homepage carousel data.
  - current crawl reached logged-in state
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/ticket/program/getProgramById.xhtml`

- 用途: 获取项目详情主数据
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl, legacy_anticket_har`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "accept": "application/json, text/plain, */*",
  "cmpappkey": "ShanghaiCS",
  "lang": "en"
}
```
- Query 入参:
```json
{
  "programId": "225529"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": {
    "horizontalPoster": "https://imgtest.antank.cn/pic/theatre/ed26db4c521e65d0.jpg",
    "stadiumName": "WestK Performing Arts Centre",
    "allowInvoice": "N",
    "agencyId": 0,
    "showMode": "calendar",
    "stadiumAddress": "88 Austin Road West, Tsim Sha Tsui, Kowloon (near China Hong Kong City)",
    "otherPoster": null,
    "realNameMaxNum": null,
    "programHighlightImage": null,
    "smallCategoryIds": null,
    "faq": "testaa,SDFADS",
    "displayPromotions": "Y",
    "id": 225472,
    "tag": "Dance",
    "stadiumMobile": "***REDACTED***",
    "releaseFlag": "Y",
    "images": null,
    "salesStartReminder": "Y",
    "programCode": "PXQ01014344",
    "stadiumCityCode": "810000",
    "briefName": "粤・乐・茶韵",
    "countdown": null,
    "showSite": "home,list,xhshome,xhslist,douyinHome,douyinList,calendar,WebSite,Weblist,homeHotSale,PCrecList1,PCrecList2",
    "supportReserve": "Y",
    "venueName": "Xiqu Centre Tea House Theatre",
    "blackLimit": "Y",
    "displayCountdownPosition": "programDetail,sessionDetail",
    "cnName": "Tea House Theatre Experience",
    "fullCnName": "Tea House Theatre Experience Preview",
    "releaseEndTime": "2026-09-27 23:59:59",
    "minPrice": 300.0,
    "preFillInfo": "qiangpiao,delivery",
    "maxPrice": 350.0,
    "status": "Y",
    "displayCountdown": "Y",
    "saleType": "sale",
    "tagIds": "1126",
    "seatPoster": null,
    "programKey": "2606061536jwyhyvc06c6cef03858f5e",
    "video": null,
    "serviceTerm": "DFSDFSD,otherdeal,programrul,tuihuanpia,xczasd",
    "dynamicValue": {
      "frontProgramType": "show",
      "autoPopupTicketType": "Y",
      "frontProgramType_label": "演出",
      "autoPopupTicketType_label": "是"
    },
    "supportSeat": "Y",
    "visitingNotice": null,
    "pushInvoice": "N",
    "venueId": 1826,
    "outOfStock": "Y",
    "startTime": "2026-05-01 00:00:00",
    "sortNum": 999,
    "releaseStartTime": "2026-05-08 17:03:33",
    "stadiumId": 69643,
    "releaseEndTime2": "2026-09-27 23:59:59",
    "ticketsNotice": "<p><strong>Tea House Theatre Experience</strong></p>\n<p><strong>&nbsp;</strong></p>\n<p><strong><u>Organiser</u></strong></p>\n<p><strong>&nbsp;</strong></p>\n<p>WestK Performing Arts...<truncated>",
    "programInfo": "<p><strong>Terms and Conditions</strong></p>\n<ol>\n<li>Each QR code can only be scanned once. Please keep your e-ticket safe.<br />2. Children under 6 are not admitted.<br />3. One ...<truncated>",
    "showContent
...<truncated>
```
- 备注:
  - current crawl reached logged-in state

### `GET /thvendor/ticket/program/getVenueProgramCount.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/ticket/program/v2/getHomeCountdownProgramList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/ticket/seasonpack/detail.xhtml`

- 用途: 详情查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/ticket/seasonpack/getSchedules.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/ticket/supportReserveProgramScheduleList.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `POST /thvendor/ticket/transfer/getTransfer.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发

### `GET /thvendor/trans/program/getListByIds.xhtml`

- 用途: 列表/分页查询接口
- 是否需要登录态: `False`
- 证据来源: `current_playwright_crawl`
- 抓到的 HTTP 状态: `200`
- Header / 相关请求头样例:
```json
{
  "cmpappkey": "ShanghaiCS",
  "lang": "en",
  "accept": "application/json, text/plain, */*"
}
```
- Query 入参:
```json
{
  "programIds": "225562,225518,225201,225539,225528,225678,225530,225693,225531,225517,225655,225198,225197,225199,225472,225585,225454,225622",
  "TRANS": "en",
  "notCover": "Y"
}
```
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
```json
{
  "errcode": "0000",
  "data": [
    {
      "id": 225562,
      "cnName": "项目名称 en",
      "fullCnName": "项目名称 en",
      "fullEnName": null,
      "briefName": "《大唐雅韵•钟鸣鼓乐》音乐会",
      "enName": null,
      "stadiumId": 69632,
      "showMode": "calendar",
      "horizontalPoster": null,
      "verticalPoster": null,
      "extraPoster": null,
      "otherPoster": null,
      "tag": null,
      "venueId": 1362,
      "startTime": "2026-05-04 10:00:00",
      "endTime": "2032-04-30 23:59:59",
      "minPrice": 20.0,
      "maxPrice": 10000.0,
      "otherinfo": null,
      "supportSeat": "N",
      "addtime": "2026-05-21 15:48:56",
      "updatetime": "2026-06-01 10:30:36",
      "status": "Y",
      "sortNum": 99,
      "saleType": "sale",
      "stadiumName": "M+ Concert",
      "stadiumMobile": "***REDACTED***",
      "venueName": "M+ Concert Hall",
      "stadiumAddress": "Art Park West Kowloon Cultural District",
      "dynamicValue": {
        "frontProgramType": "activity",
        "turnstileProgram": "闸机项目",
        "turnstileProgram_trans_en": "闸机项目",
        "turnstileProgram_trans_zh-HK": "闸机项目",
        "autoPopupTicketType": "Y",
        "frontProgramType_label": "活动",
        "autoPopupTicketType_label": "是"
      },
      "showSite": null,
      "category": null,
      "smallCategory": null,
      "programCode": "PS2605211548017087",
      "agencyId": 0,
      "releaseStartTime": "2026-04-27 00:00:00",
      "releaseEndTime": "2029-05-03 23:59:59",
      "releaseFlag": "Y",
      "dynamicStatus": "N",
      "dynamicFieldResult": null,
      "releaseStartTime2": "2026-04-27 00:00:00",
      "releaseEndTime2": "2029-05-11 23:59:59",
      "stadiumCityCode": "810000",
      "stadiumCityName": "香港",
      "allowInvoice": "N",
      "pushInvoice": "N",
      "multiGroupCheck": "N",
      "durationType": "period",
      "consumerInvoiceTime": "paid",
      "ticketingNotice": null,
      "serviceTerm": null,
      "faq": null,
      "preFillInfo": null,
      "realNameMaxNum": null,
      "channel": null
    },
    {
      "id": 225518,
      "cnName": "Full Access Ticket (Gallery 1-9) (Flex) Preview",
      "fullCnName": "Full Access Ticket (Gallery 1-9) (Flex) Preview",
      "fullEnName": null,
      "briefName": "Full Access Ticket",
      "enName": null,
      "stadiumId": 69719,
      "showMode": "row",
      "horizontalPoster": null,
      "verticalPoster": null,
      "extraPoster": null,
      "otherPoster": null,
      "tag": "常设展,特展",

...<truncated>
```
- 备注:
  - current crawl reached logged-in state

### `GET /thvendor/wxMsg/show/v2/remind.xhtml`

- 用途: 静态包发现，未在本次抓包中拿到业务说明
- 是否需要登录态: `False`
- 证据来源: `current_spa_static_template`
- Query 入参:
`无样例 / 未抓到`
- Body 入参:
`无样例 / 未抓到`
- 出参样例:
`无样例 / 未抓到`
- 备注:
  - 静态模板路径展开；本次未必现场触发
