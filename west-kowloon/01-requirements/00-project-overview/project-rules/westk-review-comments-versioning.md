---
rule_id: westk-review-comments-versioning
title: Review comments must become traceable version records before sign-off
scope: project-permanent
created: 2026-07-07
origin: User requested review comments be summarized in Review Trail with traceable version changes before final sign-off
applies_to: [West Kowloon human-facing review documents]
candidate_for_promotion: yes
promoted_to: null
promoted_at: null
---

# Review Comments And Version Record Rule

For West Kowloon human-facing requirement-review and test-case review/sign-off
documents:

- Put reviewer comments into `Review Trail and Version Record` as a concise
  summary, not as raw chat logs.
- For each comment round, record reviewer/source, summary, affected case IDs
  or requirement area, action taken, affected version, closure evidence, and
  status.
- If comments concern test cases, update the canonical test case artifacts
  first: `03-test-design/test-cases-<scope>.md`, the derived `.xlsx`, and
  `03-test-design/CHANGE.md`.
- Do not close a review comment merely by summarizing it in the review
  document. A comment is closed only when the affected artifact is updated, or
  the reviewer explicitly accepts a no-change rationale.
- If comments require requirement changes, update the relevant consolidation
  or requirement artifact first, then regenerate the formal review DOCX with
  `render_review_docx.py`.
- After AI changes a reviewed artifact, the final review document must stay
  `Awaiting Sign-Off` or `Awaiting Re-review` until the human reviewer signs
  again.
- AI must not mark the human final decision as `Signed Off` for its own changes.
- Use `Open Review Comments` in the conditions/next-step section as the simple
  gate signal. `None`, blank, or `-` means no open comments; any actionable
  reviewer comment means the document cannot be signed off yet.
- When the human reviewer removes comments and enters both `Sign-off Date` and
  `Signature / Confirmation`, sync the canonical `.md`, regenerate the formal
  `.docx`, update package/module status, and record a final signed-off row in
  `Review Trail and Version Record`.
