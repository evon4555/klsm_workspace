# Company Context Index

---

## [SECTION] Purpose

This folder stores company-level context for QA work under Kasi.

Company context is general background. It should support project and requirement analysis, but it should not override project-specific or requirement-specific facts.

---

## [SECTION] Folder Structure

| Folder | Purpose |
|---|---|
| `00-company-overview` | Stable company context and common domain terminology. |
| `01-source-documents` | Original company-level source files. |

---

## [SECTION] Main Files

- `00-company-overview\company-context.md`
- `00-company-overview\common-terms.md`
- `01-source-documents\source-index.md`

---

## [SECTION] Usage Rule

Use this layer after requirement and project context.

Typical usage:

- understand business domains such as ticketing, admission, venues, O2O, and B2C channels
- align terminology across requirements, test cases, and reports
- identify common QA risk areas such as payment, inventory, admission, permissions, and multilingual behavior
