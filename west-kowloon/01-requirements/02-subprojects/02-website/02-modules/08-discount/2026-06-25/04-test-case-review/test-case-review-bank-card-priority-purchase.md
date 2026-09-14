# Test Case Review — 银行卡优先购 (签字版)

| 项目 | 值 |
|----|----|
| 评审对象 | **v2** — `../03-test-design/test-cases-bank-card-priority-purchase.{md,xlsx}`（48 条 = v1 的 45 + 3 新增） |
| AI 评审报告 | r2: `../03-test-design/.iterations/test-case-review-bank-card-priority-purchase-r2.docx` |
| 当前状态 | **已签字 (v2)** |
| v1 已签 | 2026-06-29 — Pass with revisions → 触发 v2 |

## 修订历史

签法：把最后一行的「状态」从 **待签字** 改成 **已签字**；可选在「修改」列写一句话验收意见。

| 日期 | 作者 | 修改 | 状态 |
|----|----|----|----|
| 2026-06-27 | QA1 (AI) | 表单生成（针对用例集 v1） | 已完成 |
| 2026-06-29 | 王一凡（测试经理） | Test case review v1 — Pass with revisions (Q-1=b) | 已签字 |
| 2026-06-29 | QA1 (AI) | v2 表单更新：新增 3 条用例后的 r2 评审；附 RR-1/RR-2 残余风险确认 | 已完成 |
| 2026-06-29 | 王一凡（测试经理） | *Test case review v2 — 请填 Q-1 答复* | **已签字** |

## 1. AI r2 评审结论

**Pass with 2 info-only residual risks** — 0 阻塞 / 0 必修 / 0 Medium / 2 Info（RR-1 + RR-2，仅提醒，不阻塞）。

| 严重度       | 数量 | 编号区间                                              |
|--------------|------|-------------------------------------------------------|
| Critical     | 0    | —                                                     |
| High         | 0    | —                                                     |
| Medium       | 0    | —                                                     |
| Minor (info) | 2    | RR-1 (BPP-047 边界精确度) / RR-2 (BPP-048 弱提示文案) |

**消化情况**：v1 r1 的 4 项 Medium 建议中 3 项已补（BPP-046/047/048），1 项跳过（原 Q-4 等值最优 tiebreak，2026-06-29 你口头改为「PRD 未规定先不测」，audit 记录在 CHANGE.md v2 段）。详细 finding：见 r2 docx。

## 2. v2 决策清单

填法：在「答复」列写 `a` / `b` / `c` / `d`；Q-3 自由文本，点单元格输入。

| ID | 决策点 | 选项 | 默认 | 答复 |
|----|----|----|----|----|
| Q-1 | v2 整体评审结论 | (a) Pass — v2 进 05-execution; (b) Pass with revisions — 用 Q-3 详述要补的，产 r3 后再签; (c) Needs Revision — 用 Q-3 详述要修的，产 r3; (d) Reject — 用 Q-3 详述原因，回 consolidation | (a) | a |
| Q-2 | RR-1 + RR-2 处理方式（BPP-047 边界 / BPP-048 弱提示文案）— 这两项 PRD 未规定，但用例已写「以实际实现为准」 | (a) 现在回流 consolidation 开 U-7/U-8 让产品定义; (b) 不回流，执行时按实际实现填 Actual Result，必要时再开 U | (b) | b |
| Q-3 | 其他评审意见 / 自由文本 | 写入其他意见；无则填 `_` | `_` | `_` |

签完告诉我「签了」，按你的 a/b/c/d 走：

- **a** → v2 进 05-execution；03 不动
- **b** → 按 Q-3 详述产 **v3**（FFFF00 黄标 v2 → v3 改动）+ r3 + 你再签
- **c** → 同 b，但说明是修而不是补
- **d** → 升级回 consolidation 层（罕见）
