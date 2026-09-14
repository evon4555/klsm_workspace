---
rule_id: westk-zh-en-translation-style
title: West Kowloon Chinese-to-English QA translation style
scope: project-permanent
created: 2026-07-08
origin: User approved the English translation style of the 2026-07-07 discount test-case workbook
applies_to: [West Kowloon Chinese-to-English translation, QA artifacts, requirements, test cases, review documents]
candidate_for_promotion: yes
promoted_to: null
promoted_at: null
---

# Chinese-to-English Translation Style Rule

For West Kowloon project materials under `D:\Workspace`, Chinese-to-English
translation should follow the English QA style used in:

`D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\08-discount\2026-07-07\03-test-design\test-cases-promo-code-bank-card-offer.xlsx`

Rules:

- Use short, direct, professional QA English.
- Preserve identifiers, codes, filenames, test data, dates, URLs, case IDs,
  F/Q/U references, MID, BPP, BCO, and CyberSource terms exactly.
- Keep scope and business qualifiers. Do not drop partner, module, ticket
  type, card, MID, payment gateway, or flow qualifiers.
- Do not add explanation that is not in the source.
- Use stable project terminology from
  `D:\Workspace\west-kowloon\01-requirements\00-project-overview\domain-glossary.md`.
- Use
  `D:\Workspace\west-kowloon\01-requirements\00-project-overview\translation-glossary.md`
  as the first terminology reference before
  translating.
- Use `Admission ticket` for 门票 and `seat-selection ticket` for 座票.
- For test cases, keep `Test Steps` as user actions and `Expected Result` as
  observable outcomes.
- After translating an artifact, run the translation quality review workflow:
  `D:\Workspace\qa-harness\01-system\01-skills\review-translation-quality\SKILL.md`.

Project-owned AI skill:

`D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills\westk-zh-en-translation\SKILL.md`

Codex user-local skill folders are launchers only; do not treat them as the
canonical source for this rule.
