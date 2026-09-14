# Security Test Checklist

---

## [SECTION] Basic Information

- Project:
- Feature / Release:
- Owner:
- Reviewers:
- Date:
- Requirement Link:
- Environment:
- Version / Build:

---

## [SECTION] Authentication

- [ ] Login requirement is clear.
- [ ] Unauthenticated users cannot access protected resources.
- [ ] Session expiration behavior is verified.
- [ ] Logout invalidates access where required.
- [ ] Failed login behavior is controlled.

---

## [SECTION] Authorization

- [ ] Role and permission matrix is clear.
- [ ] Users cannot access data outside their permission.
- [ ] Horizontal privilege escalation is checked.
- [ ] Vertical privilege escalation is checked.
- [ ] API authorization is checked, not only UI visibility.

---

## [SECTION] Input Validation

- [ ] Required fields are enforced.
- [ ] Length limits are enforced.
- [ ] Invalid formats are rejected.
- [ ] Special characters are handled safely.
- [ ] File upload type and size limits are checked where relevant.
- [ ] Error messages do not leak sensitive information.

---

## [SECTION] Sensitive Data

- [ ] Sensitive data is masked in UI where required.
- [ ] Sensitive data is not exposed in logs.
- [ ] Sensitive data is not exposed in API responses unnecessarily.
- [ ] Download or export behavior is permission controlled.
- [ ] Personal or business-sensitive data follows retention rules.

---

## [SECTION] Data Integrity

- [ ] Unauthorized data modification is blocked.
- [ ] Duplicate submission is handled.
- [ ] Concurrent update risk is considered.
- [ ] Important operations have audit trail where required.

---

## [SECTION] Abuse And Boundary Cases

- [ ] Rate limit or abuse risk is considered.
- [ ] Repeated submission behavior is checked.
- [ ] Expired links or tokens are checked where relevant.
- [ ] Direct URL access is checked.
- [ ] Client-side restrictions are backed by server-side validation.

---

## [SECTION] Findings

| Finding | Severity | Impact | Evidence | Owner | Status |
|---|---|---|---|---|---|
|  | Critical / High / Medium / Low |  |  |  |  |

---

## [SECTION] Security Conclusion

- Result: Pass / Pass With Risk / Fail / Blocked
- Remaining risks:
- Required follow-up:
