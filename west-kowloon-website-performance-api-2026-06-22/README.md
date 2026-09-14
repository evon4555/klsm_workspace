# 西九官网性能测试 API 资料包

生成日期: 2026-06-23

主要文件:

- `api_browser.html`: 可本地打开的 Swagger-like API 浏览器，默认隐藏高风险/静态副作用接口。
- `openapi_like.json`: 接近 OpenAPI 3.0 的结构化接口定义。
- `openapi_quality_report.json`: OpenAPI-like 的证据状态、schema 状态和缺口报告。
- `api_dependency_map.json`: 业务链路依赖关系、提取字段、使用字段和断言点。
- `api_documentation.md`: 面向 JMeter 的接口文档，含入参、出参、认证、断言建议。
- `api_inventory.csv`: 全量接口清单，适合筛选/导入。
- `api_inventory_jmeter.csv`: 带压测推荐等级、风险等级、验证状态的接口总表。
- `scenario_flows.md`: 单接口与串联压测场景建议。
- `jmeter/jmeter_generation_notes.md`: JMeter 生成和断言配置说明。
- `jmeter/jmeter_single_api_candidates.csv`: 单接口压测候选清单。
- `jmeter/jmeter_scenario_candidates.csv`: 串联压测场景步骤清单。
- `jmeter/jmeter_excluded_risky_apis.csv`: 高风险/不建议直接压测清单。
- `jmeter/jmeter_recommendation_summary.json`: 推荐等级统计。
- `raw/api_samples.redacted.json`: 脱敏后的结构化样例。
- `scripts/collect_api_inventory.py`: 采集脚本。
- `scripts/generate_api_browser.py`: 生成 HTML 和 OpenAPI-like JSON。
- `scripts/generate_jmeter_recommendations.py`: 生成 JMeter 推荐清单。

压测推荐等级:

- `Ready`: 有真实样例且看起来是查询类接口，适合优先做单接口压测。
- `Scenario Ready`: 有真实样例但需要串联上下文或有副作用，只适合受控场景压测。
- `Smoke First`: 缺少真实响应样例，先 1 线程验证入参、响应和断言。
- `Do Not Load Test`: 验证码、登录、支付、退款、上传、实名认证、注销、账号绑定等接口，不建议直接压测。

OpenAPI 质量标记:

- `x-evidence-status`: `observed`、`staticOnly`、`registeredOnly` 或 `unknown`。
- `x-schema-status`: `observedResponseSample`、`requestShapeOnly` 或 `schemaUnknown`。
- `x-load-test-level`: 和 JMeter 推荐等级保持一致。

注意:

- 本目录不保存真实站内密码、验证码、Cookie、Session 或 Token。
- 验证码登录不适合直接高并发压测；JMeter 应使用预置 session、免验证码测试登录或压测白名单。
- 写接口压测前需要和业务确认数据隔离、库存准备和清理规则。
