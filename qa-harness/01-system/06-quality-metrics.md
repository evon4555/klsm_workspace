# Quality Metrics

---

## [SECTION] Purpose

Quality metrics help the team understand whether the QA system is protecting business quality and improving over time.

Metrics should drive improvement, not blame. A metric is useful only when it leads to a better process, better test design, better automation, better training, or clearer release decisions.

---

## [SECTION] Metric Principles

- Measure business risk reduction, not only testing activity.
- Combine outcome metrics and process metrics.
- Use trends instead of isolated numbers.
- Review metrics with context such as project risk, team size, release frequency, and requirement quality.
- Avoid rewarding behavior that increases numbers but reduces real quality.

---

## [SECTION] Project Quality Metrics

| Metric | Purpose | Suggested Review |
|---|---|---|
| Production defect count | Understand escaped quality problems | Per release / Monthly |
| Escaped defect rate | Measure defects missed before release | Per release / Monthly |
| Critical production incident count | Track severe business impact | Immediate / Monthly |
| Defect reopen rate | Measure fix quality and verification quality | Per sprint / Monthly |
| Release rollback count | Track severe release quality failure | Per release |
| Known risk acceptance count | Track release risk exposure | Per release |

---

## [SECTION] Test Process Metrics

| Metric | Purpose | Suggested Review |
|---|---|---|
| Requirement risk review completion | Check testing left shift | Per feature |
| Test strategy completion | Check planning quality | Per feature / Release |
| Requirement-to-case coverage | Check traceability | Per feature |
| Test case review completion | Check review discipline | Per feature |
| Execution completion rate | Check delivery completeness | Per release |
| Evidence completeness | Check traceability and auditability | Per release |
| Regression completion rate | Check existing flow protection | Per release |

---

## [SECTION] Automation Metrics

| Metric | Purpose | Suggested Review |
|---|---|---|
| Critical flow automation coverage | Measure business protection | Monthly / Release |
| Automation pass stability | Measure trust in automation signal | Daily / Weekly |
| Flaky test rate | Track automation reliability risk | Weekly |
| Automation execution frequency | Check feedback speed | Weekly |
| Automation failure signal quality | Check whether failures are actionable | Weekly |
| Manual regression effort reduced | Measure automation value | Monthly |

---

## [SECTION] Non-Functional Metrics

| Metric | Purpose | Suggested Review |
|---|---|---|
| Performance baseline pass rate | Check performance readiness | Per release |
| P95 / P99 response time trend | Track user-facing performance | Per release / Monthly |
| Error rate under load | Track reliability under pressure | Per release |
| Security checklist completion | Check baseline security discipline | Per release |
| Security finding count by severity | Track security risk | Monthly / Release |
| Compatibility issue count | Track device/browser/system risk | Per release |

---

## [SECTION] Worker And Team Metrics

Worker metrics should be used for coaching and improvement, not public blame.

| Metric | Purpose | Suggested Review |
|---|---|---|
| Test case review finding rate | Identify test design gaps | Monthly |
| Missed scenario pattern | Identify training needs | Monthly |
| Evidence completeness by worker | Improve execution discipline | Monthly |
| Defect report quality | Improve reproducibility and communication | Monthly |
| Production bug contribution pattern | Identify process or skill gaps | Per incident |
| Improvement action completion | Check coaching effectiveness | Monthly |

---

## [SECTION] Improvement Loop

1. Collect metrics.
2. Identify weak signal or trend.
3. Analyze root cause.
4. Decide process, template, skill, automation, or training improvement.
5. Apply improvement to real project work.
6. Re-measure the result.

---

## [SECTION] Anti-Patterns

- Counting test cases as quality without checking business coverage.
- Counting automation cases without checking stability or critical flow value.
- Using metrics only to blame individuals.
- Ignoring requirement quality when evaluating QA performance.
- Treating missing evidence as completed testing.
- Closing production bugs without improving the system.
