---
rule_id: westk-ticket-type-flow-split
title: Admission ticket and seat-selection ticket flows must be considered separately
scope: project-permanent
created: 2026-07-08
origin: User clarified that Admission ticket and seat-selection ticket are separate Charisma flows
applies_to: [West Kowloon Website test case design and test case review]
candidate_for_promotion: yes
promoted_to: null
promoted_at: null
---

# Ticket Type Flow Split Rule

For West Kowloon Website test case design and test case review, ticketing,
cart, checkout, payment, discount, refund, wallet, order detail, and related
regression scopes must consider these two ticket types separately:

- `Admission ticket` - the unseated / quantity-based ticket flow.
- `seat-selection ticket` - the seated ticket flow with seat-map selection.

Rule:

- If a requirement touches behavior after ticket selection, do not assume one
  ticket type covers the other.
- Generate separate cases for `Admission ticket` and `seat-selection ticket`
  whenever the functional path, data, inventory/seat locking, pricing,
  payment, discount eligibility, order detail, wallet, refund, or downstream
  Charisma handling can differ.
- If both ticket types share identical behavior and one case is intentionally
  used as representative coverage, record the explicit `NA` / rationale in
  Coverage Notes or the review evidence. Do not leave the second flow implicit.
- During test-case review, treat missing `Admission ticket` or
  `seat-selection ticket` coverage as a gap unless the case set documents why
  the requirement is not applicable to that ticket type.

Preferred terminology:

- Use `Admission ticket`, not only `General Admission`, in test case titles,
  descriptions, module/feature paths, and review comments.
- Use `seat-selection ticket` for 座票 / selected-seat flows.
