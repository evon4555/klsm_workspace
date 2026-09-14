# JMeter 场景建议

## 单接口压测优先级

1. 公共读接口: 首页配置、广告、分类、热门项目、项目详情、详情内容、场次/票种查询。
2. 登录态读接口: 会员信息、订单列表、优惠券、收藏、有效票列表。
3. 写接口低并发验证: 收藏、购物车初始化、创建订单、取消订单。
4. 不建议直接高并发: 验证码登录、账号注销、支付参数、支付网关、座位类抢同一座位。

## Scenario 1: 首页浏览

`getDisplayConfig -> getNewAdList -> getCategoryList -> getHotProgramList -> getProgramById -> getProgramContentInfo`

用途: 验证匿名浏览、首页和项目详情吞吐。

JMeter 关联:
- 从 `getHotProgramList` 提取 `programId` / `id`
- 传给 `getProgramById` 和 `getProgramContentInfo`

## Scenario 2: 非座位票下单后取消

`getProgramById -> listBydate -> tickettype/list -> show/order/create -> show/order/cancelOrder -> getMemberOrderList(status=cancel)`

用途: 第一优先级端到端压测链路，历史 HAR 和自动化都证明比座位票更稳定。

JMeter 关联:
- `getProgramById` 提取 `programKey`
- `listBydate` 提取 `showId`、`sessionKey`
- `tickettype/list` 提取 `ticketTypeId`、`ticketType`
- `show/order/create` 请求头生成唯一 `orderkey`
- `show/order/create` 响应提取 `tradeNo`
- `cancelOrder` 使用 `tradeNo`

控制点:
- 每个创建订单线程必须执行取消订单
- 断言 `errcode=0000` 和 `success=true`
- 压测前准备足够库存，避免库存不足被误判为性能问题

## Scenario 3: 座位票查询链路

`scheduleDateListWithSellOut -> listScheduleByDate -> getScheduleInfo -> getSchedulePrices -> getAvailableSeats2 -> getSpecialSeatOverlay -> seatplan JSON`

用途: 座位图查询、价格和库存查询压测。

控制点:
- 查询链路可压；创建座位订单 `order/create2` 不建议高并发抢同一座位
- 若要压创建，必须准备大量可售座位并做座位数据参数化
- `getAvailableSeats2` 返回或参与生成的 `orderKey` 需要传给 `order/create2` 的 `orderkey` Header

## Scenario 4: 会员中心读取

`getLogonInfo -> getMemberInfo -> getPersonalInfo -> getMemberOrderList -> getMemberCouponsByStatus -> listFavorites`

用途: 登录态读接口压测。

控制点:
- 避免每个线程都走验证码登录
- 建议预置 Cookie/session 或测试专用免验证码登录
- 每个线程使用独立账号或独立 session，避免服务端 session 互相覆盖
