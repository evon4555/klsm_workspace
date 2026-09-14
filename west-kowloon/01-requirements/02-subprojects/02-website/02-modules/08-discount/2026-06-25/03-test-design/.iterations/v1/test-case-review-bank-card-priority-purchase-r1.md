# Test Case Review — 银行卡优先购 r1 (AI / QA2)

> **AI 评审结论，非签字版本。** 按 `08-our-pipeline.md` §4 硬规则，AI 评审从不放进 `04-test-case-review/`。此文档存档在 `.iterations/` 作为审计轨迹；人评审 + 签字请见 `../04-test-case-review/test-case-review-bank-card-priority-purchase.md`。

## [SECTION] Basic Information

- Review ID: BPP-R1-2026-06-27
- Project: West Kowloon Website
- Feature: 银行卡优先购 (F1-F12)
- Test Case Set: `03-test-design/test-cases-bank-card-priority-purchase.md` (+ .xlsx)（共 45 条）
- Author: QA1 (AI) — generated 2026-06-26, revised 2026-06-27 per Q-7/Q-8 v2 signoff
- Reviewer: QA2 (AI)
- Review Date: 2026-06-27
- Review Result: **Pass with optional improvements** (建议补 6-8 条 gap，但不阻塞执行)

---

## [SECTION] Review Summary

### [FIELD] Overall Assessment

45 条用例覆盖了 12 个能力 (F1-F12) + 2 条 E2E。主流程 / 负流程 / 大部分边界都到位。所有 Q-1..Q-8 决策都落到了对应用例；3 条原黄色行已按 v2 签字结果消化（BPP-033 部分退款不反转 / BPP-037 联调验证 / BPP-043 fallback zh-CN）。可执行性良好（步骤、前置、期望都具体到能跑的程度）。

**建议补充**的 gap 都是非阻塞类（网络异常、并发、边界精度），属于「可加但不影响这批执行」。如果时间紧，按当前 45 条上 SIT 执行可行；如果要更扎实，建议补 6-8 条（详见 § Findings）。

### [FIELD] Main Concern

- **没有真正的关键缺陷**。可执行性 + 决策追溯 + 命名规范都过关
- 弱点都在**非功能性 / 边界精度**：网络异常、超时、并发、时间边界精确到秒
- Q-5(b) 联调验证（BPP-037）依赖后端实现，执行时如果发现实现位置与决策不符，需要二次决策（已在 Comments 注明，不算 gap）

### [FIELD] Required Action

- **执行前必做**：无
- **建议补**：6-8 条非阻塞 gap（见下方 § Findings，全部 Medium / Minor）
- **执行后回看**：BPP-037 联调验证如果发现实现与 Q-5(b) 不符，回 consolidation 补 Q-9

---

## [SECTION] Coverage Review

| Coverage Area | Status | Finding | Required Action |
|---|---|---|---|
| Main business flow | **Covered** | F1-F12 主流程全覆盖；E2E BPP-044 完整链路 | — |
| Alternative flow | **Covered** | F2/F3 失败 + 重试、F5 取消、F6 未命中、F7 全不命中等都有 | — |
| Negative scenario | **Covered** | BIN 不命中 / API 失败 / 必填漏填 / 凭证过期 / 支付失败均覆盖 | — |
| Boundary value | **Partial** | 凭证「剩 X 天」覆盖了 7/5/2 天但漏 0 天和凌晨过期；时间窗口「在/不在」覆盖但漏窗口开放瞬间；F7「等值最优」未覆盖 | 补 3 条边界 (建议 Medium) |
| Permission | **Covered** | 已登录/未登录路径区分清楚（F1 默认登录、F5 解绑要登录） | — |
| Data state | **Covered** | 已绑定/未绑定/已过期/已用/已退款各状态都有 | — |
| Integration | **Partial** | F10/F11 mid 冲突覆盖；但**与 03-ticketing 模块的回归**没有专门用例（只在 D-adj-1 列出影响） | 建议 ticketing 模块在下次 regression 时加 1-2 条 "with active partner benefit" 维度（**Owner: ticketing 模块负责人，不在本包**） |
| Compatibility | **Missing** | 浏览器兼容 / 移动端响应式 / 不同分辨率均未覆盖 | 非本包范围（属于横切回归集），可不补 |
| Regression | **Partial** | 影响相邻模块 D-adj-1..5 已识别但未生成 regression 用例 | 同上 — 横切回归集决策 |
| Non-functional risk | **Missing** | 网络异常 / 后端超时 / 并发同时购票同一权益 / 计数原子性均未覆盖 | 补 2-3 条非功能性边界 (建议 Medium) |

---

## [SECTION] Quality Checklist

- [x] Each case maps to a requirement, risk, or business flow (Collected from 列追溯到 F-编号 / Q-编号 / U-编号 / PRD §)
- [x] Preconditions are clear and executable (user1..user5、mock 数据、时间窗口都明示)
- [x] Test data is defined (mock 卡号、合作方编号、事件配置都有具体值)
- [x] Steps are specific enough to execute (步骤都是「点 X / 输入 Y / 观察 Z」形式)
- [x] Expected results are observable (期望都是可断言的 UI 状态 / 数据值 / 计数)
- [x] Priority matches business risk (营收相邻全是 High；i18n 多语言 Medium；细节边界 Low)
- [x] Duplicate cases are removed or justified (无重复)
- [x] Blocked or not-testable areas are documented (Q-3=c 决策下，真实卡场景不在范围内，已在 Scope Summary 注明)
- [x] Regression impact is considered (D-adj-1..5 在 consolidation 列出，但 regression 用例归属其他模块)
- [N/A] Evidence requirements are clear (执行前不适用)
- [N/A] For v2+ case sets... (这是 v1 测试用例)

---

## [SECTION] Findings

按严重度排序。所有 finding 都是 Medium 或 Minor — **无 Critical / High**。

| Severity | Issue | Impact | Suggestion | Owner |
|---|---|---|---|---|
| Medium | F4 凭证「0 天 / 即将凌晨过期」边界未覆盖。当前覆盖 7/5/2 天 | 时区 / 系统时钟微差可能导致前端显示「0 天」时后端已视为过期，造成 UX 不一致 | 补 BPP-046：凭证「0 天剩余 + 当天午夜过期」边界，验证前端文案和后端命中判断一致 | QA1 (AI) revise |
| Medium | F6 时间窗口边界 = 公售前 30 分整 (Partner A Diamond) 时的精确行为未覆盖 | 时间窗口开关瞬间可能出现「过几秒能用过几秒不能用」的抖动 | 补 BPP-047：公售前 30:00 / 29:59 / 30:01 三个时刻的命中状态 | QA1 (AI) revise |
| Medium | F7 等值最优未覆盖。Q-6=a「总价最低」，但两个绑定都给出相同折后价时取哪个？ | 多绑定且折扣等值时若实现非确定性，会导致用户「同样状态、不同结果」 | 补 BPP-048：两个等价折扣同时命中，验证选取确定性（建议取 alphabetical / 后台优先级 / FIFO 之一，需开发联调确认） | QA1 (AI) revise + 联调确认 |
| Medium | F9 优先购次数耗尽（计数 = 0）时尝试优先购 → 应不进入优先购模式。当前未覆盖 | 次数耗尽是必然到达的状态，且与 F6「未命中」语义不同（是「条件满足但配额用完」），用户需要不同的弱提示 | 补 BPP-049：user1 甲钻石次数耗尽，购票时验证不进优先购、显示「次数已用完」类弱提示 | QA1 (AI) revise |
| Medium | F8 弱提示出现频次 / 用户关闭后行为未覆盖 | 弱提示每次都出 vs 24 小时出一次 vs 关闭后再不出 — UX 影响大 | 补 BPP-050：弱提示关闭/重新打开/重新出现的行为；如 PRD 未明确则联调时确认 | QA1 (AI) revise (若 PRD 未明确，回 consolidation 加 Q) |
| Minor | F2 BIN 输入容错：用户粘贴带空格 / dash 的卡号（如 `4111 1111 1111 1111`）未覆盖 | 常见用户操作；缺失会被实际用户首次试错抓到 | 补 BPP-051：粘贴 `4111 1111 1111 1111` 和 `4111-1111-1111-1111`，验证前端自动去除分隔符 | QA1 (AI) revise |
| Minor | F2 重复绑定同一已绑定 BIN 未覆盖 | 用户重复操作；应该幂等或友好提示 | 补 BPP-052：user1 已绑甲钻石，再次绑同 BIN 卡，验证或幂等或「已绑定」提示 | QA1 (AI) revise |
| Minor | E2E 失败路径未覆盖（绑定失败 → 重试 → 成功 → 优先购） | 真实用户路径常涉及失败重试 | 补 BPP-053：BIN 第一次不命中 → 改卡号 → 命中 → 完成优先购下单 | QA1 (AI) revise |

**8 条建议补充，全 Medium / Minor**。如果都补，规模从 45 → 53 条。

---

## [SECTION] Final Decision

- **Decision: Pass with optional improvements**
  - 当前 45 条满足执行最低门槛
  - 8 条 gap 都是 Medium / Minor，可补但不阻塞
- **Reason**：覆盖 / 可执行性 / 决策追溯 / 模板符合度都过关；缺失项都在非功能性 + 边界精度领域，不影响主功能验证
- **Follow-up Owner**：测试经理决定是否接受 8 条补充建议；若接受，QA1 (AI) 修订到 r2
- **Due Date**：取决于测试经理决策（接受补充 = +1-2 小时；不补 = 立即转 04 签字）

---

## [SECTION] 评审决策树（给测试经理参考）

```
你的选择：
├─ 接受 8 条补充 → 我修订 → r2 评审 → 04 签字
│   优势：扎实、网络异常类边界提前抓到
│   代价：+1-2 小时
│
├─ 部分接受（如只接受 Medium 4 条，Minor 4 条跳过）→ 我修订 → r2 → 04
│   优势：抓主要 gap，跳次要
│
└─ 全部跳过，立即 04 签字
    优势：最快进执行
    代价：8 条 gap 转为执行中现场补 / 后续维护
```

我建议**部分接受 Medium 4 条**（BPP-046/047/048/049），跳过 Minor 4 条（BPP-050/051/052/053）— Medium 是有意义的边界 gap，Minor 是「锦上添花」类。

但说了算的是你。
