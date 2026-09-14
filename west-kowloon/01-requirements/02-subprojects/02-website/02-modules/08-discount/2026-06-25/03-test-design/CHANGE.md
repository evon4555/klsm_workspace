# Test Cases CHANGE Log

> 顶层文件夹永远存放**最新版**用例。历史版本在 `.iterations/v1/`、`.iterations/v2/` ... 留底。本 CHANGE.md 跟随最新版滚动 — 每新出一版 AI 在最上方新增一段，旧段保留作为变更日志。

## v2 — 2026-06-29 (current)

**来源依赖**：
- v1 用例集（已快照到 `.iterations/v1/`，共 45 条）
- 04 form 评审签字：`../04-test-case-review/test-case-review-bank-card-priority-purchase.md` 修订历史末行 `2026-06-29 王一凡 已签字`
- 决策清单 Q-1..Q-10 答复：Q-1=b (Pass with revisions) / Q-2=a / Q-3=a (后口头改为 c) / Q-4=a (后口头改为跳过) / Q-5=a / Q-6..Q-9=b / Q-10=空

**修改触发**：
- 04 评审 Q-1 = b → 进 Pass with revisions 分支，按 Q-2..Q-5 补用例
- v1 r1 评审标记的 4 个 Medium gap（BPP-046..049）实际仅补 3 个（用户口头调整：Q-4 关于「等值最优 tiebreak」与测试无关、PRD 未规定 → 跳过）

**修改清单**（仅新增，不改 v1 原 45 条）：
- 新增 **BPP-046**（Q-2(a) / F4+F6 / High-High）— 凭证过期边界：剩 0 天 + 凌晨 00:00 跨日 + 失效瞬间
- 新增 **BPP-047**（Q-3(c) / F6 / High-Medium）— 30 分窗口模糊边界（不验证秒级精度；按 Q-3=c 决策走默认假设）
- 新增 **BPP-048**（Q-5(a) / F9 / Medium-Medium）— 优先购次数耗尽 (=0) 降级为普通价
- **跳过**原计划 BPP-049 等值最优 tiebreak（用户口头决定：与测试无关，PRD 未规定。04 form Q-4 已签 a，但本次产 v2 时改为 不补 — audit trail 见此处）

**黄色标注**（user-facing diff）：
- BPP-046 / 047 / 048 三条 xlsx 整行 FFFF00 亮黄填充（"本轮新增"信号）
- md 表对应行用 🟡 前缀标识
- FFFFF2CC 浅黄 Deferred：本版 0 条

**口头改 04 决策的 audit 摘要**（重要）：

| 04 已签答复 | v2 实际操作 | 理由（用户口头 2026-06-29） |
|---|---|---|
| Q-3 = a (补精确边界) | **改为 c**（默认假设，模糊边界） | "假设默认就行，不用这么精细" |
| Q-4 = a (补等值最优) | **改为 跳过** | "最优不最优和 test case 好像没啥关系，PRD 没明确规定先不测" |

文档化此处是因为：04 签字版是历史快照不动；后续 traceability 看 Q-3/Q-4 答复 vs 实际用例时会出现"答了 a 却没补对应内容"的疑问，此 audit 表解释原因。

**上一版快照**：`.iterations/v1/` — 含 test-cases-*.{md,xlsx} + CHANGE.md + en/ + r1 review + translation-review r1

**评审记录**：
- AI 评审 r2：`.iterations/test-case-review-bank-card-priority-purchase-r2.{md,docx}`（仅评 3 条新增 + 残余风险）
- 人评审签字表单 (v2)：`../04-test-case-review/test-case-review-bank-card-priority-purchase.{md,docx}` ← 等你再签
- 翻译 r2：`.iterations/translation-review-bank-card-priority-purchase-r2.{md,docx}`（仅评 3 条新增的 EN 译文）
- EN v2：`en/test-cases-bank-card-priority-purchase.xlsx`

---

## v1 — 2026-06-27

**来源依赖**：
- Consolidation 签字版 v2：`../02-analysis/requirement-consolidation-bank-card-priority-purchase.md`（Q-1..Q-8 + U-1..U-6 全部已签，2026-06-27 王一凡）

**本版包含**：
- 45 条用例，covering F1-F12 (C 端) + 2 条 E2E
- 0 条黄色 deferred（v2 签字后 Q-7/Q-8 决策已消化；BPP-037 重分类为联调验证）
- xlsx + md 两种载体（xlsx 是执行用，md 是人读 + Python 解析用）
- EN 译本在 `en/`，已过 `review-translation-quality` skill v3 自检

**变更点 vs 上一版**：
- 无 — v1 是首版

**评审记录**：
- AI 评审 r1：`.iterations/test-case-review-bank-card-priority-purchase-r1.{md,docx}`（Pass with optional improvements，0 阻塞 / 4 Medium / 4 Minor）
- 人评审签字表单：`../04-test-case-review/test-case-review-bank-card-priority-purchase.{md,docx}` → 2026-06-29 已签 Pass with revisions → 触发 v2
- 翻译评审 r1：`.iterations/translation-review-bank-card-priority-purchase-r1.{md,docx}`（Pass with revisions，3 Medium 已修到 EN v3）

---

## 接下来（流程模板）

如果你在 04 签 Pass with revisions / Needs Revision，AI 出 **v2** 时会按下面格式在本文档**顶部**新增一段：

```
## v2 — yyyy-mm-dd

**来源依赖**：v1 + 04 评审签字（链接到具体的签字行）
**修改触发**：v1 的 r1 评审 Q-N（链接到具体 Q 编号）
**修改清单**：
- 新增 BPP-XXX（编号 / 类型 / 触发哪条评审项）
- 修改 BPP-YYY 的 <某列>（旧值 → 新值 / 触发哪条评审项）
- ...
**黄色标注**（user-facing diff）：
- 新增/修改的 cell 在 xlsx 中以 **FFFF00 亮黄** 填充（区别于 FFFFF2CC 浅黄 = Deferred / 待确认）
- 用户打开 v2.xlsx 一眼即知"哪些是本轮改动"
**上一版快照**：`.iterations/v1/` （test-cases-*.{md,xlsx} + CHANGE.md + review-r1.* + en/）
**评审记录**：r2 在 `.iterations/test-case-review-*-r2.{md,docx}`
```

---

## 文件夹约定

```
03-test-design/
├── test-cases-bank-card-priority-purchase.md       ← 最新版（人 + 工具读这个）
├── test-cases-bank-card-priority-purchase.xlsx     ← 最新版（执行 / 闸门读这个；黄 cell = 本轮 diff）
├── CHANGE.md                                       ← 本文件，滚动日志（人只看最新一段，旧段是 audit）
├── en/
│   └── test-cases-bank-card-priority-purchase.xlsx ← 最新版 EN
└── .iterations/                                     ← audit 留底（人通常不动，工具不计入闸门统计 — 详见 package_scanner）
    ├── v1/                                          ← v2 出现时，v1 整体快照到这里
    │   ├── test-cases-*.{md,xlsx}
    │   ├── CHANGE.md
    │   ├── en/
    │   └── review-r1.{md,docx}
    ├── v2/                                          ← v3 出现时，v2 快照到这里
    │   └── ...
    ├── test-case-review-*-r1.{md,docx}             ← AI 评审（不进 04）
    ├── test-case-review-*-r2.{md,docx}             ← v2 出现后的评审
    ├── translation-review-*-r1.{md,docx}
    └── iteration-log.md                             ← (可选) 跨版本索引
```

**人只看顶层** — 顶层永远是最新的可信版本 + CHANGE.md 解释这次改了什么。
