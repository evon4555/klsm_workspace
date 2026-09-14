---
name: create-security-checklist
description: Use this skill to create a baseline security testing checklist for a feature, API, user flow, admin function, data export, authentication flow, permission change, or release. It covers authentication, authorization, input validation, sensitive data, data integrity, abuse cases, and audit concerns.
---

# Create Security Checklist

## Purpose

Create a practical security testing checklist for QA-level validation.

This skill does not replace specialist security review. It helps QA identify common security risks early and document what was checked.

## Inputs

Use any available input:

- Requirement
- User roles and permissions
- API documentation
- UI flow
- Data model
- Authentication behavior
- Export or download behavior
- Sensitive data rules
- Audit requirements

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../05-evidence-standard.md`
- `../../templates/security-test-checklist.md`

## Workflow

1. Identify protected resources and user roles.
2. Identify sensitive data and operations.
3. Define authentication checks.
4. Define authorization checks.
5. Define input validation checks.
6. Define data integrity and abuse checks.
7. Define required evidence and remaining risks.

## Output Format

```markdown
# Security Test Checklist

---

## [SECTION] Scope Summary

- Feature:
- Protected resources:
- User roles:
- Sensitive data:

---

## [SECTION] Authentication Checks

- [ ]

---

## [SECTION] Authorization Checks

- [ ]

---

## [SECTION] Input Validation Checks

- [ ]

---

## [SECTION] Sensitive Data Checks

- [ ]

---

## [SECTION] Data Integrity And Abuse Checks

- [ ]

---

## [SECTION] Evidence And Risks

- Required evidence:
- Remaining risks:
- Need specialist security review: Yes / No
```

## Quality Rules

- Always check server-side permission risk, not only UI visibility.
- Include direct URL or direct API access where relevant.
- Include sensitive data exposure in logs, exports, and API responses.
- If the feature handles money, personal data, admin permissions, or external access, mark specialist review as recommended.
- If security requirements are unclear, list questions rather than assuming safety.
