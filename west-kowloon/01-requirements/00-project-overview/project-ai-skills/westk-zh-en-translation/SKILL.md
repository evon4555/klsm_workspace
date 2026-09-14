---
name: westk-zh-en-translation
description: Project-owned workflow for West Kowloon Chinese-to-English translation of QA artifacts under D:\Workspace, including requirements, test cases, review documents, CHANGE notes, DOCX/MD/XLSX handoffs, terminology cleanup, and the approved West Kowloon QA English style.
---

# WestK ZH-EN Translation

## Source Of Truth

This file is the portable project-owned skill. User-local agent skills should
delegate to this file instead of becoming the only copy of the translation
rules.

## Purpose

Translate West Kowloon QA/project artifacts from Chinese to English using the
approved QA English style shown in:

`D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\08-discount\2026-07-07\03-test-design\test-cases-promo-code-bank-card-offer.xlsx`

This skill is for translation. It does not change requirement scope or test
coverage unless the user explicitly asks for a test-design update.

## Required Reading

Before translating West Kowloon artifacts, read as applicable:

- `D:\Workspace\west-kowloon\01-requirements\00-project-overview\translation-glossary.md`
- `D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-context.md`
- `D:\Workspace\west-kowloon\01-requirements\00-project-overview\domain-glossary.md`
- `D:\Workspace\west-kowloon\01-requirements\01-source-documents\source-index.md`
- approved style anchor:
  `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\08-discount\2026-07-07\03-test-design\test-cases-promo-code-bank-card-offer.xlsx`
- mandatory post-translation review:
  `D:\Workspace\qa-harness\01-system\01-skills\review-translation-quality\SKILL.md`

If translation is part of test-case generation or review, also read:

`D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills\westk-testcase-workflow\SKILL.md`

If translation affects human sign-off artifacts, also read:

`D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills\westk-review-signoff\SKILL.md`

## Style Rules

- Use short, direct, professional QA English.
- Preserve stable identifiers verbatim: case IDs, F/Q/U IDs, filenames, promo
  codes, MID, CyberSource, BPP, BCO, URLs, card/test data, and dates.
- Keep product/system names stable. Do not translate them creatively.
- Use `translation-glossary.md` as the first terminology authority.
- Do not add explanatory content that is not in the source.
- Do not omit qualifiers that affect meaning, such as partner, module, flow,
  ticket type, card, MID, or payment gateway.
- Keep `Admission ticket` for 门票 and `seat-selection ticket` for 座票.
- Use `promo code`, `bank-card offer`, `CyberSource Checkout`, `order
  confirmation page`, `payable amount`, `discount detail area`, and `payment
  flow` consistently when those concepts appear.

## Test Case Translation Rules

- Keep workbook/markdown column structure unchanged.
- Translate only human-readable content; preserve blank design-time fields.
- Keep `Module/Feature` as slash-separated English paths.
- Write `Test Scenario` as a concise noun phrase.
- Write `Test Case Description` as one grammatical sentence beginning with
  `Verify that...` when possible.
- Write `Test Steps` as numbered user actions only.
- Write `Expected Result` as numbered observable outcomes.
- Keep test data exact. Do not translate mock codes or card labels.
- Preserve ambiguity and flag it; do not silently decide product behavior.

## Review Requirement

After producing or modifying a translated artifact, run:

`D:\Workspace\qa-harness\01-system\01-skills\review-translation-quality\SKILL.md`

Do not report the translation as ready until Medium+ translation findings are
fixed or explicitly accepted by the user.

## Output Expectations

- Preserve the original file format.
- For `.xlsx`, use `openpyxl` and preserve formatting.
- For formal review/sign-off `.docx`, regenerate through the approved renderer
  only when the source `.md` changed.
- Update version/change records only when translation changes are part of an
  artifact lifecycle, not for a one-off text answer.
