# Company Overview

---

## [SECTION] Summary

Current company context is derived from:

- `D:\Workspace\qa-harness\03-context\company\01-source-documents\onboarding\2025Q3新员工培训20250818.pptx`
- `D:\Workspace\qa-harness\03-context\company\01-source-documents\terminology\AnTank系统的行业术语库.xlsx`

This is a first-pass summary for QA and AI context use. It should be refined when more formal company background, product documentation, or QA operating rules are available.

---

## [SECTION] Business Positioning

AnTank appears to position itself as a digital platform and solution provider for ticketing, admission, O2O services, and venue or destination operations.

The company serves complex cultural, entertainment, tourism, and mixed-use venue scenarios. The source material references:

- commercial complexes
- destination and tourism projects
- theatres and performance venues
- museums and cultural institutions
- large-scale events and sports scenarios

---

## [SECTION] Core Domain Focus

Based on the onboarding deck and terminology workbook, the company domain is centered on:

- ticketing and admission systems
- reserved seating and general admission flows
- reservation and booking
- event and programme management
- box office and kiosk operations
- admission control and redemption
- customer-facing B2C channels
- multilingual and multi-channel service
- integrated payment methods

---

## [SECTION] Representative Customers And Scenarios

The training deck indicates the company works with high-profile venues and districts, including:

- Hong Kong West Kowloon Cultural District
- Hong Kong Jockey Club
- major theatres and arts venues in Guangzhou, Shanghai, and other cities
- large destination and mixed-use developments

For QA, this matters because the product domain likely includes:

- high-traffic sales periods
- multilingual user journeys
- payment and ticket issuance reliability
- venue-specific admission rules
- cross-channel consistency between web, box office, kiosk, and admission terminals

---

## [SECTION] Quality Implications

From a testing perspective, the company context suggests that quality risk is strongly tied to:

- revenue flows such as ticket purchase and payment
- inventory accuracy such as seat locking and availability
- admission control accuracy
- multilingual and user-facing correctness
- operational stability during high-concurrency sales
- role-based and permission-based operations
- traceability and auditability for refunds, exchanges, reprints, and restricted actions

These areas should be treated as high-priority risk zones in test strategy and regression planning.

---

## [SECTION] Source Notes

- The onboarding deck gives useful business and customer context, but it is not a formal QA policy source.
- No explicit company-wide QA SOP is maintained in the company context layer.
- QA rules should remain in `D:\Workspace\qa-harness\01-system`, while this folder stays focused on company background and terminology.
