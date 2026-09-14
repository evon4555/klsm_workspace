# Domain Glossary

---

## [SECTION] Summary

This glossary combines West Kowloon project wording with the company terminology baseline. It is a working glossary for QA use and should be expanded when requirement-specific vocabulary appears.

---

## [SECTION] Project Terms

| Term | Working Meaning | Testing Notes |
|---|---|---|
| Ticketing and Admission System | Core ticketing, issuance, and admission platform | Usually touches inventory, payment, issuance, and access control risks. |
| B2C applications | Customer-facing applications and journeys | Focus on registration, login, browsing, purchase, wallet, and account behavior. |
| Box Office | Staff-assisted onsite sales and service channel | Strong role and permission checks are needed. |
| Reserved Seating | Seated ticketing with seat map selection | Locking, concurrency, seat eligibility, and pricing are key risks. |
| General Admission | Unseated or quantity-based admission flow | Inventory, quantity limits, and admission validation are key risks. |
| Admission ticket | Project test-case term for 门票 / unseated quantity-based tickets | Treat as a separate Charisma flow from `seat-selection ticket`; do not use one flow as implicit coverage for the other. |
| seat-selection ticket | Project test-case term for 座票 / selected-seat tickets | Treat as a separate Charisma flow from `Admission ticket`; verify seat-map selection, seat lock, seat identity, and downstream handling when in scope. |
| Shopping Cart | Order-building stage before payment | Promotion, pricing, inventory, and edit-lock behavior matter. |
| E-Ticket Wallet | Customer ticket storage and retrieval area | Verify visibility, status, redemption, and cross-device access. |
| Admission Terminal | Staff-side admission operation terminal | Verify login, scope, switching, validation, and auditability. |
| OTA Integration | Third-party channel integration | Verify order sync, ticket purchase, validation, return, and status consistency. |

---

## [SECTION] Language Notes

- The specification references multilingual support and language switching.
- Language-sensitive flows should not only test translation quality but also business correctness after switching language.
- Terms such as `admission`, `redemption`, `collection`, and `wallet` should be interpreted consistently in each scenario.
