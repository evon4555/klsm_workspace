# Desensitization Module Index

Module purpose:

- 统一管理 West Kowloon 各渠道和业务模块中的 PII 脱敏展示、权限、审计、
  集中存储及 KMS 保护要求。
- 当前输入涉及 Website、PDA、后台和 BI，属于跨模块安全与隐私能力。

Package convention:

- 使用本模块下的直接日期包，例如 `2026-07-30`。
- 每个日期包以 `package.md` 作为追踪入口。
- 跨模块需求在用例的 `Module/Feature` 字段中明确实际模块和页面，不把所有
  场景笼统写成一个“脱敏模块”。

Timeline:

| Package | Type | Status | Source | Change summary | Next workflow step |
|---|---|---|---|---|---|
| `2026-07-30` | new-requirement | Signed Off; ready for execution | ZenTao story `4319` + masking checking rules | v1.3 中文跨模块用例共 47 条；覆盖 Website、PDA、后台和 BI 定制报表，门票/座票分开。 | 进入 `05-execution` 执行准备。 |

Maintenance rule:

- 日期包状态变化时同步更新本时间线和日期包内的 `package.md`。
- 正式测试用例必须在需求整合签字后生成。
