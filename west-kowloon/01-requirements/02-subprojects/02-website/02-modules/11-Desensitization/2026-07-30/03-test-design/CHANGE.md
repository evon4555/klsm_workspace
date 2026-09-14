# Test Case Change Log

| Date | Version | Actor | Change | Affected Cases / Artifact |
|---|---|---|---|---|
| 2026-08-12 | v1.3 | Test Manager / QA1 (AI) | Test Manager 签字版删除最后一条招商小程序个人资料脱敏用例，并确认最终签字范围为 47 条用例 | `SIT-TC-WK-PII-048`；`test-cases-desensitization.md/.xlsx`；`test-case-review-desensitization.md/.docx` |
| 2026-08-12 | v1.2 | QA1 (AI) | 按测试用例标准重写新增行，补充可执行前提、动作步骤、测试数据和可观察预期 | `SIT-TC-WK-PII-043..048`；`test-cases-desensitization.md/.xlsx` |
| 2026-08-12 | v1.1 | QA1 (AI) | 补全人工新增用例的相关字段，新增消息推送、购物车和招商小程序展示面的脱敏用例；新增行标黄并等待重新评审 | `SIT-TC-WK-PII-043..048`；`test-cases-desensitization.md/.xlsx` |
| 2026-07-30 | v1 | QA1 (AI) | 根据已签字的需求整合生成中文跨模块脱敏用例 | `SIT-TC-WK-PII-001..042`；`test-cases-desensitization.md/.xlsx` |
| 2026-07-30 | v1 | QA2 (AI) | 草稿质量检查中拆分后台/BI 下载与导出分支，移除重复且需要跨角色切换的一致性场景；随后 QA2 r1 Pass | `SIT-TC-WK-PII-038..042`；`.iterations/test-case-review-desensitization-r1.md` |

## Version Notes

- v1 是本独立需求的首个正式测试用例版本；v1.1 补全新增用例字段；v1.2 将新增行重写为正式可执行测试用例；v1.3 删除 `SIT-TC-WK-PII-048` 后由 Test Manager 签字确认，没有修改历史 AUTH/Ticketing 工作簿。
- 工作簿由 West Kowloon `TestCase_Template.xlsx` 克隆生成。
- 设计阶段的 Environment、Execution Date、Executed By、Actual Result、Status、Comments/Remarks、Screenshots 保持空白。
