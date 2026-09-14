# JMeter 生成说明

## 输入文件

- `../api_inventory.csv`: 单接口压测的主清单。
- `../api_inventory_jmeter.csv`: 带压测推荐等级、风险等级、验证状态的总表。
- `jmeter_single_api_candidates.csv`: 可优先生成单接口 JMeter sampler 的候选接口。
- `jmeter_scenario_candidates.csv`: 建议串联压测的场景步骤和关联字段。
- `jmeter_excluded_risky_apis.csv`: 不建议直接压测或必须先人工确认的接口。
- `../api_documentation.md`: 每个接口的入参、出参样例和断言建议。
- `../scenario_flows.md`: 可串联的业务场景。
- `../raw/api_samples.redacted.json`: 脱敏结构化样例，适合脚本生成器读取。

## 单接口压测

建议优先筛选 `api_inventory.csv` 中满足以下条件的接口:

- `auth_required=false` 的 GET/POST 查询类接口。
- `purpose` 为列表、详情、配置、分类、场次、票种、库存查询。
- `source` 包含 `current_playwright_crawl` 或 `legacy_anticket_har` 的接口优先，因为有真实请求/响应样例。

不建议直接高并发的单接口:

- 验证码登录接口。
- 创建订单但不取消的接口。
- 支付、退款、账号注销、实名认证、文件上传等有明显副作用的接口。

## Scenario 压测

建议优先生成:

1. 首页浏览链路。
2. 项目详情/场次/票种查询链路。
3. 非座位票创建订单后立即取消链路。
4. 登录态会员中心读取链路。

关键关联字段见 `../scenario_flows.md`。

## JMeter 固定配置

- HTTP Request Defaults: `https`, `anticket.lengliwh.com`
- HTTP Header Manager:
  - `cmpappkey: ShanghaiCS`
  - `lang: en`
  - `Accept: application/json, text/plain, */*`
- HTTP Authorization Manager: 配置外层 Basic Auth，密码不要写入版本库。
- HTTP Cookie Manager: 登录态/预置 session 场景需要开启。

## 断言

- 先断言 HTTP 状态。
- JSON 接口再断言 `errcode=0000` 和 `success=true`。
- 列表接口可补充 `data` / `resultList` 非空断言。
- 创建订单 scenario 必须补充取消订单断言，避免未支付订单堆积。
