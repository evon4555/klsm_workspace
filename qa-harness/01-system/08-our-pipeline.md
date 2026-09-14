# Our Pipeline (West Kowloon / Antank)

This document pins down **the specific end-to-end QA pipeline this team uses
today**. `02-qa-workflow.md` is the generic 12-step model; this file is the
concrete instance — who does what, with which tool, in which order.

If something in this file contradicts `02-qa-workflow.md`, this file wins
for our project. If you are starting a NEW project under this harness and
have different tooling / roles, write your own `08-...-pipeline.md` for
that project instead of mutating this one.

---

## [SECTION] Pipeline Overview

```
[1]   Input package         figma + mindmap + PRD          (human PM/BA)
        ↓
[1.5] Requirement           AI consolidates → TM signs off skill: consolidate-requirement
      consolidation         02-analysis/requirement-           GATE: blocks [2]
      (TM scope gate)       consolidation-<scope>.md
        ↓
[2]   AI drafts cases       QA1 (AI) writes v1             skill: write-test-case
        ↓
[3]   Iterative review      QA1(AI) ↔ QA2(AI) loop         skill: iterate-test-case-quality
        ↓                    (up to 3 revise rounds)
[4]   Human sign-off        Test Manager final review      04-test-case-review/
        ↓
[5]   Automation            API for flow + Playwright UI   Behave outer wrapper
        ↓                    (see § Layered automation)
[6]   Execution → dashboard runs land in dashboard.db     /api/runs, ApiMonitorPage
        ↓
[7]   Defect feedback       failed scenarios → ZenTao bug  open-bug button
        ↓
[8]   (future) ZenTao loop  pull requirement → close req   not built yet
```

---

## [SECTION] 1. Input Package

QA does not start until ALL THREE of these are on disk under
`<project>/01-requirements/02-subprojects/<subproject>/02-modules/<module>/<yyyy-mm-dd>/01-input/`:

| Source | Required? | Location |
|---|---|---|
| Figma screenshots | If the feature has UI | `01-input/figma/<change-date>/` (ISO date dir — see `10-change-management.md`) |
| Mindmap | Strongly preferred for non-trivial features | `01-input/mindmap/<change-date>/` |
| PRD (or equivalent spec) | **Always** | `01-input/` or referenced from `01-source-documents/` |

Plus an `input-index.md` that lists what's there and links to source authority
(`07-source-authority.md`).

If one source is missing, log it in the input-index instead of guessing.

---

## [SECTION] 1.5. Requirement Consolidation + Test Manager Scope Sign-Off

Owner: **QA1 (AI)** produces the doc; **Test Manager** signs it off.

Skill: [`skills/consolidate-requirement`](./01-skills/consolidate-requirement/SKILL.md)
Template: [`templates/requirement-consolidation-template.md`](./02-templates/requirement-consolidation-template.md)
Guard: [`tools/check_requirement_review_interface.py`](./03-tools/check_requirement_review_interface.py)

Output:

- `<package>/02-analysis/requirement-consolidation-<scope>.md`
- `<package>/02-analysis/requirement-consolidation-<scope>.docx` generated
  from the `.md` for Test Manager review

The human-facing working copy must use the fixed decision-only Chinese
template in `02-templates/requirement-consolidation-template.md`. Formal
project review/sign-off layouts may be generated for external packages only
when explicitly requested, and must not replace the decision-only Q/U working
document.

What this step is for: between raw inputs and AI-drafted test cases,
QA produces one human-readable consolidation document containing:

- Conclusion first: `有没有问题？`
- Issue classification
- Test scope / capability list (capabilities re-organized by business
  function, not by source-doc structure)
- **Differences (差异项)** — vs previous version / vs standard product /
  vs adjacent module
- Source inventory (with authority order applied)
- **Decision table** — `Q-1..Q-n` with proposed options and an empty
  `答复` column
- **Assumption table** — `U-1..U-n` with working assumptions and an empty
  `确认 / 修正` column
- **Next step / sign-off gate** — what the Test Manager fills and when
  `03-test-design` can start

**Gate rule (hard):**

- Step 2 (AI drafts test cases) MUST NOT start until the consolidation
  doc reaches **Signed Off** status in its Revision History.
- Sign-off is recorded by the Test Manager editing the pre-filled human
  reviewer row in place. AI must not self-sign-off.
- When the Test Manager updates the doc with answers to open
  questions, treat the updated document — not the raw sources — as
  the authoritative scope statement for step 2.
- If sources change after sign-off (e.g., PRD revision lands), produce
  a new revision of the consolidation doc with a delta-only section
  and re-request sign-off before updating the corresponding test
  cases.

**Why this step exists:**

- Bypassing it sends test cases to step 3 review with unconfirmed scope
  and unanswered questions baked in — those churn into revise loops.
- The Test Manager needs one place to (a) see what the AI understood,
  (b) confirm scope, (c) answer open questions in one pass.
- For SaaS contexts where a project is overriding a standard product,
  the `差异项` table forces explicit decisions about what syncs back
  to standard product and what stays project-only.

### Optional skills that branch off here (conditional)

Step 1.5 is the **default per-package entry point**. The generic
`02-qa-workflow.md` lists separate Steps 2 (risk review) and 3 (test
strategy) — in this pipeline they are **conditional adjuncts**, not
mandatory per package:

| Skill | Invoke when |
|---|---|
| `review-requirement-risk` | The consolidation flags risk_level=High AND a stakeholder writeup beyond QA is needed; or production-bug retrospective requires a backwards-looking risk review. |
| `create-test-strategy` | Project kickoff, new subproject onboarding, or cross-package release strategy. **Not per requirement package.** |
| `create-automation-plan` / `create-performance-test-plan` / `create-security-checklist` | Per project or per release scope, when the consolidation flags non-functional concerns warranting a dedicated workbook. |

For routine requirement packages, the consolidation doc absorbs the
risk + scope + strategy content; producing parallel artifacts is
discouraged because the parallel files drift out of sync.

---

## [SECTION] 2. AI Drafts Test Cases (QA1)

Owner: **QA1** role (currently the AI). See `03-qa-roles.md`.

Skill: [`skills/write-test-case`](./01-skills/write-test-case/SKILL.md)

Output: `03-test-design/test-cases-<scope>.md` + auto-generated `.xlsx`

Constraints:
- Must follow the project xlsx template exactly when one exists; otherwise
  use `templates/test-case-template.md`
- Must consult project's `07-source-authority.md` order
- Must NOT pad with categories the user didn't ask for (see feedback memory `dont_invent_extra_categories`)

---

## [SECTION] 3. Iterative QA1 ↔ QA2 Review

Owner: **QA1 + QA2** in an **automated closed loop** (no human in between rounds).

Skill: [`skills/iterate-test-case-quality`](./01-skills/iterate-test-case-quality/SKILL.md)

Mechanics — verbatim from that skill:

```
WRITE (v1) → REVIEW (r1) → if Pass: DONE
                          ↓ if Needs Revision
                          REVISE (v2) → REVIEW (r2) → ...
                          ↓ hard cap: 3 revise rounds
                          DONE (status: pass | cap_reached | reject_persisted)
```

| Output | Where |
|---|---|
| Live final case file | `03-test-design/test-cases-<scope>.md` (always overwritten to latest) |
| Round-by-round audit trail | `03-test-design/.iterations/test-cases-<scope>-vN.md` + `test-case-review-<scope>-rN.md` |
| Iteration log | `03-test-design/.iterations/iteration-log-<scope>.md` |

**Important — what this is NOT:**
- It is NOT a 3-role chain (no third "QA3 review"); it is a 2-role iterative loop
- The human Test Manager review happens AFTER this loop in step 4, not during

---

## [SECTION] 4. Human Test Manager Sign-Off

Owner: **Test Manager** (the human, not AI).

Reviews the FINAL artifact from step 3. Catches things AI can't catch:
- Business judgment (is this important to test?)
- Org context (does sales / customer support agree?)
- Compliance / regulatory specifics

Output:

- `04-test-case-review/test-case-review-<scope>.md`
- `04-test-case-review/test-case-review-<scope>.docx` generated from the
  `.md` for Test Manager sign-off

For West Kowloon packages, the human-facing test-case review/sign-off copy
must use the project template:
`D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Test Case Review Template.docx`.
QA2 working reviews still use the harness `test-case-review-template.md`
and stay under `03-test-design/.iterations/`.
Human review comments must be captured in `Review Trail and Version Record`,
then closed by updating the affected test-case artifacts, regenerating the
workbook, and recording closure evidence before human sign-off. Use the
conditions/next-step section's `Open Review Comments` field as the simple gate
signal: any actionable comment blocks sign-off; `None` means the reviewer has
no open comments.

If cases are added, modified, removed, or scope-adjusted after review starts,
the change must also be written to the workbook `Audit Trail` sheet and the
review DOCX must be regenerated. When automation assessment already exists,
apply the same audit row to
`05-execution/02-automation-assessment/automation-assessment-<scope>.xlsx` and
its paired review DOCX. Use `record_testcase_change.py`; then run
`check_testcase_audit_trail.py` or the full gate. MD-only audit notes are not
accepted for this path.

**Hard rule**: AI review verdicts NEVER go in `04/`. `04/` is reserved for
the named human reviewer's signed verdict. AI round-by-round reviews live
in `03/.iterations/`.

---

## [SECTION] 5. Automation — Layered

Owner: **QA1** (AI writes automation) with **QA6/Automation QA** oversight.

We split into two layers below Behave:

```
┌─────────────────────────────────────────────────────────┐
│  Behave (.feature files)  ←  business-readable wrapper  │
│       │                                                  │
│       ├──► API layer (requests)                          │
│       │    runs the "data plumbing" steps fast & cheap   │
│       │    e.g. login, set up cart, query orders         │
│       │                                                  │
│       └──► UI layer (Playwright)                         │
│            verifies "what the user sees" on the          │
│            last meaningful screen, not every screen      │
└─────────────────────────────────────────────────────────┘
```

**Rule of thumb**:
- Anything that's "I need this state to exist" → API
- Anything that's "the user should see X / click Y / get Z visual feedback" → Playwright
- The outer Behave scenario reads like prose; the steps inside choose which layer

**Where things live**:
| Layer | Code | Tests |
|---|---|---|
| Behave API+UI mixed scenarios | `west-kowloon/02-automation/01-features/api_ui_mixed/*.feature` | API chain/setup first, final UI assertion |
| Behave UI E2E scenarios | `west-kowloon/02-automation/01-features/ui_e2e/*.feature` | pure browser long-chain scenarios |
| API smoke | `west-kowloon/02-automation/02-tests/api/api_smoke/` | pure single-API monitoring |
| API contract / functional / mixed pytest | `west-kowloon/02-automation/02-tests/api/api_contract/`, `api_functional/`, `api_ui_mixed/` | schema checks, API journeys, shared-session API+UI references |
| Page objects and adapters | `west-kowloon/02-automation/03-src/test_automation/` | project page objects and adapters |
| UI page objects | `west-kowloon/02-automation/03-src/test_automation/web/*_page.py` | Playwright, headless OK |

**Website test layers**: see `west-kowloon/02-automation/02-tests/api/README.md`
and `west-kowloon/02-automation/01-features/README.md` for the current split:
API smoke, API contract, API functional, API+UI mixed, and UI E2E.

---

## [SECTION] 6. Execution → Dashboard

Owner: **dashboard backend** (auto).

### What gets recorded

Behave runs auto-record into `dashboard/backend/dashboard.db`. Every
run shows up in:

- `/api/runs` (list) → Dashboard "Test Run" page
- `/api/api-monitor/endpoints` → API Monitor page (smoke results)
- `/api/api-monitor/layers` → 2-card layer summary
- `/api/stats/trends` → trend charts

### How the sync works (promoted from memory `behave_auto_dashboard_sync` on 2026-06-03)

`west-kowloon/02-automation/01-features/environment.py` has three Behave hooks that write
each session into `dashboard.db` via stdlib `sqlite3` (no SQLAlchemy
needed, so behave doesn't require the `[dashboard]` extra):

| Hook | Action |
|---|---|
| `before_all` | INSERT a new `test_runs` row in `'running'` state; capture id on `context._dashboard_run_id`. |
| `after_scenario` | INSERT a `test_scenarios` row linked to the run id. Status = behave's verdict (passed/failed/skipped/untested/error). duration = sum of step durations. error_msg = first failed step's message. |
| `after_all` | Re-aggregate scenarios into the `test_runs` row: set finished_at + total + passed + failed + errored + skipped + final status (`passed` iff zero failed AND zero errored, else `failed`). |

Visible in stdout while running:
```
[dashboard-sync] created test_runs id=N env=E
[dashboard-sync] finalized run #N: total=T passed=P failed=F errored=E skipped=S -> S
```

### Double-recording prevention

`dashboard/backend/runner.py` (the dashboard's own BehaveRunner) sets
`BEHAVE_DASHBOARD_RUN_ID=<run_id>` in the subprocess env when it
launches behave. `environment.py::_dashboard_should_record()` checks
that var and **skips its own recording** in that case — the runner
already created the row and will populate scenarios by parsing the
JSON results file.

| Invocation | Who records |
|---|---|
| CLI `behave ...` from terminal | `environment.py` creates + populates the row |
| Dashboard "Run Tests" button | `runner.py` creates the row; environment.py stays out of the way |

No duplicates either way.

### Failure tolerance

`environment.py` checks `_DASHBOARD_DB.exists()` and silently no-ops if
the db file isn't there (e.g. behave invoked on a machine without the
dashboard installed). Any recording-time exception is caught + logged
as `[dashboard-sync] ... failed (continuing)` — never crashes a test
run.

### Implementation gotcha

Path resolution uses `Path(__file__).parents[2]` because the layout is
`west-kowloon/02-automation/01-features/environment.py`. **Don't write `[3]`**
— that resolves to `D:\` and the existence check silently no-ops, so
nothing records, with no error.

### Relation to xlsx writeback

dashboard.db captures **every** run, no policy.
xlsx is only updated when explicitly asked (via `writeback_results.py`
or via manual flip for new NA → Pass cases) — see
`feedback_dont_refresh_pass_scenarios` under
`D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-rules`.

---

## [SECTION] 7. Defect Feedback

Owner: **Test Manager** (decides which failures are real bugs).

For each scenario that genuinely fails (not flake, not env), use the
**"Open Bug"** button on the dashboard → fires a ZenTao bug pre-filled
from the failed scenario. Idempotent — won't double-file.

---

## [SECTION] 8. (Future) Full ZenTao Closed Loop

Not built. Planned shape:

```
ZenTao requirement created
        ↓
QA pulls it via /api/requirements/pull         (todo)
        ↓
the 8-step pipeline above runs end-to-end
        ↓
final state: tests pass + cases signed off
        ↓
QA pushes "Done" back to ZenTao              (todo)
```

When this is built, this section gets a real spec. Until then it stays
as an intent statement so anyone reading the doc knows where we're headed.

---

## [SECTION] Mapping back to 02-qa-workflow.md

For audit / convention check:

| Step here | 02-qa-workflow step |
|---|---|
| 1 Input | step 1 Requirement intake |
| 1.5 Requirement consolidation | step 3.5 Requirement consolidation and scope sign-off |
| 2 AI drafts | step 4 Test case design (executed by AI QA1) |
| 3 Iterate | step 5 Test case review (closed AI loop) |
| 4 Human sign-off | step 5 (continued — human verdict) |
| 5 Automation | adjunct of step 3 (automation strategy) + step 6 (execution) |
| 6 Execution | step 6 Test execution |
| 7 Defect feedback | step 7 Defect management |
| 8 (future) ZenTao loop | spans 1+7 in 02-qa-workflow |

If you change this pipeline, also update the mapping above.
