# Test Design

Status: v1.3 signed off by Test Manager; ready for execution.

## Current Test Case Set

- `test-cases-desensitization.md`
- `test-cases-desensitization.xlsx`
- Version: v1.3
- Test cases: 47
- Language: Chinese
- Sheet: one `Test Cases` Sheet with module-specific `Module/Feature` and descriptions

## Scope

- Fields: 手机号、邮箱、姓名、身份证/实名制 ID、地址、生日、性别。
- Modules: Website、PDA、后台、BI 定制报表。
- Ticket types: Admission ticket 与 seat-selection ticket 分开覆盖。
- Reports: 页面、预览、下载、导出分开覆盖。
- Excluded by signed scope: BI Dashboard、权限/审计、KMS/集中存储、多语言、复杂格式边界和旧用例回写。

## QA2 Review

- `.iterations/test-case-review-desensitization-r1.md`
- Result: v1 passed; v1.3 signed off by Test Manager after removing `SIT-TC-WK-PII-048`
- Open findings: None

## Human Review

- `../04-test-case-review/test-case-review-desensitization.md`
- `../04-test-case-review/test-case-review-desensitization.docx`
- Status: Signed Off; ready for execution
