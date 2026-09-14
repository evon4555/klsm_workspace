# 01-system/01-skills/

AI prompt templates used by the QA team to generate QA artifacts with AI
assistance. Each skill is a directory containing one `SKILL.md` that
describes the input contract, the work the AI does, and the expected
output structure. Skills are designed to be agent-invokable but can also
be read directly as prompt templates.

## Skills index

| Skill | What it does | Input |
|---|---|---|
| [`review-requirement-risk/`](./review-requirement-risk/SKILL.md) | Risk review of a requirement package | requirement spec / mindmap / PRD |
| [`create-test-strategy/`](./create-test-strategy/SKILL.md) | Project-level strategy | requirements + risks + timeline |
| [`consolidate-requirement/`](./consolidate-requirement/SKILL.md) | **Gate before test case design.** Integrated breakdown + differences + scope + open questions → Test Manager sign-off | risk review + strategy + 01-input + (optional) prior-version cases / standard-product ref |
| [`write-test-case/`](./write-test-case/SKILL.md) | Generate structured test cases (xlsx-compatible) | requirement + risk review |
| [`review-test-case/`](./review-test-case/SKILL.md) | Coverage / executability / clarity review | xlsx test cases |
| [`revise-test-case/`](./revise-test-case/SKILL.md) | Apply review findings → v2 (bolded diff, xlsx re-emit) | v1 cases + review file |
| [`iterate-test-case-quality/`](./iterate-test-case-quality/SKILL.md) | Auto-loop write→review→revise→re-review until Pass or 3-round cap | requirement (same as write) |
| [`manage-review-signoff/`](./manage-review-signoff/SKILL.md) | Human review comments, version closure, DOCX re-render, and final sign-off sync | reviewer-edited DOCX + affected requirement/test-case artifacts |
| [`maintain-requirement-change/`](./maintain-requirement-change/SKILL.md) | Absorb requirement changes into test cases and automation without losing history | changed requirement package + current test cases |
| [`create-automation-plan/`](./create-automation-plan/SKILL.md) | Identify + prioritize automation candidates | xlsx + run history |
| [`review-automation-coverage/`](./review-automation-coverage/SKILL.md) | Coverage adequacy review | xlsx ↔ .feature mapping |
| [`create-performance-test-plan/`](./create-performance-test-plan/SKILL.md) | Perf scope / workload / metrics / acceptance | requirement + NFRs |
| [`create-security-checklist/`](./create-security-checklist/SKILL.md) | Security test plan | requirement + threat model |
| [`create-regression-plan/`](./create-regression-plan/SKILL.md) | Regression scope | change list + impacted modules |
| [`generate-test-report/`](./generate-test-report/SKILL.md) | Release-ready report | xlsx execution + defects |
| [`analyze-production-bug/`](./analyze-production-bug/SKILL.md) | Escape-defect analysis | production incident |
| [`qa-retrospective-coach/`](./qa-retrospective-coach/SKILL.md) | Retrospective + improvement plan | run history + metrics |
| [`worker-training-plan/`](./worker-training-plan/SKILL.md) | Per-worker improvement plan | review findings + metrics |
| [`review-translation-quality/`](./review-translation-quality/SKILL.md) | **Mandatory after any translation.** Side-by-side source vs target check: alignment / terminology / style / identifiers / precision / idiom / format / mock-data | source artifact + translated artifact + project glossary |

## How to use

Open the `SKILL.md` inside the skill dir. It tells the AI what context to
load, what shape the output should take, and which template (under
[`../02-templates/`](../02-templates/)) to fill.
