# 05-execution — 银行卡优先购

Owner: **QA1** (automated layers) + **QA1 manual** (HK-specific / 联调 / 非阻断验证)
来源：v2 用例 48 条（`../03-test-design/test-cases-bank-card-priority-purchase.xlsx`），04 评审 v2 已签 Pass (2026-06-29)。

## 待回填的 xlsx 列

执行时按 `feedback_ai_qa_testing_process` 约定回填 v2 xlsx 的右侧列：

| 列 | 内容 |
|---|---|
| Environment | SIT |
| Execution Date | YYYY-MM-DD |
| Executed By | 王一凡 / Antank QA Team / Behave Auto |
| Actual Result | 实际观察 |
| Status | Pass / Fail / NA / Blocked / Deferred |
| Comments/Remarks | 补充说明、缺陷链接、联调结论（尤其 BPP-047 / BPP-048 的 RR-1 / RR-2）|
| Screenshots | evidence/ 下文件名引用 |

## 文件夹约定

```
05-execution/
├── README.md                   ← 本文件
├── evidence/                    ← 截图 / 日志 / 接口响应
│   ├── BPP-NNN-pass-YYYY-MM-DD.png
│   ├── BPP-NNN-fail-YYYY-MM-DD.png
│   └── ...
├── execution-log.md            ← 每天执行进度滚动日志（按日期分段）
└── defects/                     ← (可选) 单独缺陷描述 md，若 ZenTao 不够用
```

## 执行策略 — 待决定

详细策略待与测试经理讨论（automated vs manual / 时间线 / mock 数据准备）。
本目录在策略确定后再开始填充。

## 残余风险提醒（来自 04 v2 评审）

- **RR-1**：BPP-047 时间窗口边界精确开/闭区间 PRD 未定 — 用例 Expected 已写「以实际实现为准」。执行时按观察到的行为填 Actual Result；若与开发联调发现明确规则，更新 v2 用例并回写到 r3 评审。
- **RR-2**：BPP-048 次数耗尽弱提示文案 PRD 未规定 — 同上处理。
- 04 v2 Q-2 = b ⇒ **不回流 consolidation 开 U**，执行期决定即可。

## 跳过项 audit

- 原计划 BPP-049 等值最优 tiebreak — 测试经理 2026-06-29 决定不测（PRD 未规定，且用户无可观测差异）。审计记录见 `../03-test-design/CHANGE.md` v2 段。
