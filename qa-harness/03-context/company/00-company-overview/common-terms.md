# Common Terms

---

## [SECTION] Summary

This glossary is based on the AnTank terminology workbook and the current West Kowloon project context.

It is intended to help AI and QA use consistent business language when reading requirements, writing test cases, and reviewing results. The list below is selective, not exhaustive.

---

## [SECTION] Core Terms

| Chinese Term | Working English | Short Form | Testing Notes |
|---|---|---|---|
| 票务系统 | Ticketing and Access Control System | TAS | Often central to order, payment, issuance, and admission flows. |
| 选座票务系统 | Reserved Seating Ticketing System | Seated TAS | Seat map, seat locking, availability, and pricing rules are key risks. |
| 门票票务系统 | General Admission Ticketing System | Admission TAS | Quantity rules, inventory, and admission validation are key risks. |
| 无座票务系统 | Standing / General Admission Ticketing System |  | Clarify whether the flow is standing only or general admission in the requirement. |
| 预约 | Booking Management |  | Verify booking status, confirmation, change, and cancellation flows. |
| 活动管理 | Event and Programme Management |  | Test event lifecycle, publish state, schedule, and visibility rules. |
| 验票 | Admission Validation / Access Control |  | Admission validation, reuse prevention, device behavior, and audit trails matter. |
| 核销 | Ticket Redemption / Ticket Collection |  | Confirm whether the term means redemption, collection, or both in context. |
| 售取票机 | Ticketing Kiosk | Kiosk | Kiosk-specific UX, device behavior, payment, and printing should be covered. |
| 票房 | Box Office |  | Usually implies staff-assisted operational workflows and stronger permissions. |

---

## [SECTION] Usage Notes

- Use the project preferred English names consistently across requirements, test cases, and reports.
- Clarify whether a term refers to a user-facing feature, backend capability, physical device, or business process.
- Terms related to ticketing mode, admission, seat handling, inventory, payment, and permissions should be treated as business-critical.

---

## [SECTION] QA Guidance

When a requirement uses a domain term:

1. confirm the exact business meaning in that scenario
2. map it to the correct system or user flow
3. check whether the term implies role, inventory, payment, or admission risk
4. make the term explicit in test cases and expected results

---

## [SECTION] Source Notes

- The source workbook includes more rows and version history.
- When a future requirement depends heavily on terminology, expand this glossary from the original workbook rather than guessing from memory.
