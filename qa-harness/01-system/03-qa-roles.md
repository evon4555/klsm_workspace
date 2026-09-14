# QA Roles


---

## [SECTION] Purpose

This document defines QA roles by responsibility. A role does not always mean a different person. One person may own multiple roles depending on project size, budget, schedule, and team capability.

The purpose is to make quality responsibilities explicit.

---

## [SECTION] Role Model

#### [POINT] QA1: Functional QA

Primary responsibility:

- Understand business requirements.
- Design and execute functional test cases.
- Verify main user flows, alternative flows, negative scenarios, boundaries, permissions, and data changes.
- Report and verify defects.
- Collect test evidence.

Expected output:

- Requirement questions
- Functional test cases
- Test execution records
- Defect reports
- Evidence package

#### [POINT] QA2: Requirement And Test Review QA

Primary responsibility:

- Review requirement clarity and risk.
- Review test strategy and test cases.
- Challenge missing scenarios and weak expected results.
- Verify that test coverage matches business risk.

Expected output:

- Requirement risk review
- Test case review findings
- Coverage gap list
- Review approval or revision request

#### [POINT] QA3: Regression QA

Primary responsibility:

- Define regression scope based on changes, dependencies, historical defects, and critical business flows.
- Execute manual or automated regression tests.
- Confirm that existing functions are not broken by new changes.

Expected output:

- Regression plan
- Regression execution records
- Regression risk notes

#### [POINT] QA4: Performance QA

Primary responsibility:

- Identify performance-sensitive flows.
- Define workload, volume, response time, throughput, and stability expectations.
- Execute or coordinate performance testing.
- Analyze performance risk before release.

Expected output:

- Performance test plan
- Performance test result
- Bottleneck or risk analysis
- Performance readiness recommendation

#### [POINT] QA5: Security QA

Primary responsibility:

- Review authentication, authorization, input validation, sensitive data, session behavior, audit logs, and abuse cases.
- Execute baseline security checks.
- Coordinate deeper security testing when project risk requires it.

Expected output:

- Security checklist
- Security finding list
- Security risk notes

#### [POINT] QA6: Automation QA

Primary responsibility:

- Identify automation candidates.
- Build or maintain automated tests for stable and important flows.
- Evaluate automation coverage and reliability.
- Integrate automation into CI/CD when possible.

Expected output:

- Automation plan
- Automated test cases
- Automation execution results
- Flaky test analysis
- Coverage review

#### [POINT] Quality Owner

Primary responsibility:

- Own the release quality conclusion.
- Review whether quality gates are satisfied.
- Accept or reject known release risks.
- Ensure production issues feed back into the QA system.

Expected output:

- QA readiness decision
- Accepted risk list
- Post-release improvement actions

---

## [SECTION] AI Worker Roles

AI can assist each role:

- Requirement risk reviewer
- Test strategy writer
- Test case writer
- Test case reviewer
- Regression planner
- Automation planner
- Performance test planner
- Security checklist generator
- Test report generator
- Production bug analyst
- Retrospective coach

AI output must be reviewed by the responsible human role before it becomes project evidence or a release decision.

---

## [SECTION] Assignment Rules

- For low-risk changes, one QA may cover functional testing, regression, evidence, and reporting.
- For medium-risk changes, separate test design review should be added.
- For high-risk changes, assign explicit owners for regression, automation, performance, security, and quality review as needed.
- If resources are limited, document which roles are not covered and what risk remains.
- If AI is used to cover a role, record who reviewed and accepted the AI output.
