---
rule_id: westk-review-docx-format
title: West Kowloon review DOCX format rule
scope: project-permanent
created: 2026-07-07
origin: User reported poor formatting in the 2026-06-25 discount test-case review DOCX
applies_to: [西九]
candidate_for_promotion: yes
promoted_to: null
promoted_at: null
---

# West Kowloon Review DOCX Format Rule

Date: 2026-07-07

## Trigger

The `2026-06-25/04-test-case-review/test-case-review-bank-card-priority-purchase.docx`
handoff format was reported as poor. Its markdown source used raw HTML
tables for the decision list, which is fragile for `md_docx.py` / pandoc
conversion and produces poor human-review output.

## Rule

For West Kowloon human-facing review/sign-off artifacts:

- Use the v2.1 project review templates for all future human-facing review
  handoffs:
  - `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Requirement Review Template.docx`
    for requirement review / scope sign-off.
  - `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Test Case Review Template.docx`
    for Test Manager test-case review / sign-off.
- Use a clean prior accepted sign-off document as the structural reference.
- Prefer the current markdown-table sign-off structure used by
  `08-discount/2026-07-07/04-test-case-review/test-case-review-promo-code-bank-card-offer.md`.
- Current source of truth is the v2.1 template pair in
  `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates`.
  Use the `.md` template as the content source and the paired `.docx` as the
  Word layout reference. Do not use older generated review files as the
  template unless the user explicitly asks to revise the source template.
- For formal human-facing review/sign-off DOCX output, use
  `D:\Workspace\qa-harness\01-system\03-tools\render_review_docx.py`. Do not
  regenerate these final review files with the generic `md_docx.py` converter,
  because that loses the approved professional layout.
- Generated human-facing review documents must capture the reviewer
  name/signature in `Signature / Confirmation | <type name or sign here>`.
  Do not add a separate `Signed Off By` row because it duplicates the signature
  field.
- Do not include a `Final Decision` row in the top sign-off table; it
  duplicates the review summary / final decision section and makes the sign-off
  block noisy.
- Do not add a separate `Final Decision` section to new human-facing review
  forms. Use the bottom `Conditions and Next Step` table, including
  `Open Review Comments`, `Next Folder / Phase`, and `Handoff Decision`.
- In `Review Trail and Version Record`, historical `Needs Revision` rows should
  not stay red after a later row fixes/closes the issue. Use warning color only
  for currently open blocker states.
- The template files may keep `Template` in their filenames, but generated
  review documents must not show `Template` wording in the document body.
- Do not copy legacy raw-HTML table blocks from older review forms.
- Avoid forced line breaks such as `<br>` inside decision-list table cells;
  use concise semicolon-separated options so docx -> md round-trips stay as
  markdown tables where possible.
- `md_docx.py to-docx` must fail fast on raw HTML table blocks by default;
  `--allow-raw-html-tables` is only for legacy recovery, not normal handoff.
- Keep the active signature/status table near the top and the decision list at
  the bottom.
- Generate paired `.md` + `.docx`, then verify the `.docx` opens and contains
  the expected number of tables before handoff.

## Anti-reference

Do not use the `2026-06-25` 04 review form as a formatting template unless it
has first been cleaned to markdown-table format.
