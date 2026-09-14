# Input Index

## Requirement Package

- Project: West Kowloon
- Primary capability: PII 脱敏与隐私保护
- Affected systems: Website、PDA、后台、BI、共享安全/数据平台
- Package: `2026-07-30`
- ZenTao story: `4319`
- Canonical location:
  `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\11-Desensitization\2026-07-30`

## Source Files

### ZenTao Requirement

- `00-zentao requirement\requirement id.txt`
  - Story URL: `https://lengliwh.chandao.net/story-view-4319.html`。
  - 提到的 PII：手机号、邮箱、姓名、地址、实名制 ID。
  - 影响场景：Website 前台、PDA、后台、BI。
  - 技术方向：集中存储、阿里云 KMS。
  - 阶段结论：先从手机号、邮箱开始；前端展示方式按当前方式；订单类需权限控制和审计，产品需介入。
- `00-zentao requirement\checking rules.txt`
  - 给出手机号、邮箱、姓名、身份证、地址、生日、性别共 7 类脱敏示例。

### Figma

- `01-figma\` 为空；截至 2026-07-30 没有 Figma URL、截图或设计节点。

### Mindmap

- `02-mindmap\` 为空。
- 项目规则通常以脑图为权威来源；本包需要测试经理确认是否以 ZenTao 文本作为当前工作权威。

### PRD

- `03-prd\` 为空；没有独立 PRD 或技术设计文档。

## Source Authority Notes

- 当前唯一有内容的需求来源是 ZenTao 文本及检查规则。
- 由于权威脑图为空，正式用例设计前必须确认 ZenTao 是否可作为本日期包的工作权威。
- “先从手机号、邮箱开始”与检查规则中的 7 类字段存在范围差异，已在需求整合的 Q-2 中提出。
- 手机号示例中的可见前缀长度并不一致，已在 Q-4 中提出，不能由 QA 自行推导算法。

## Analysis Outputs

- `..\02-analysis\rag-retrieval.md` - 相似历史用例检索及复用判断。
- `..\02-analysis\requirement-consolidation-desensitization.md` - 中文需求整合与范围确认门禁。
- `..\02-analysis\requirement-consolidation-desensitization.docx` - 测试经理填写的 Word 评审副本。
