# West Kowloon Codex Instructions

Use the project-owned AI skills in this repository. Do not rely on
`C:\Users\klsm\.codex\skills` as the source of truth.

## Start Here

Read:

`D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills\README.md`

Then select the matching project skill:

- Test case generation / QA2 review:
  `01-requirements\00-project-overview\project-ai-skills\westk-testcase-workflow\SKILL.md`
- Human review comments / sign-off:
  `01-requirements\00-project-overview\project-ai-skills\westk-review-signoff\SKILL.md`
- Chinese-to-English translation:
  `01-requirements\00-project-overview\project-ai-skills\westk-zh-en-translation\SKILL.md`

## Codex Local Skills

Codex user-local skills under `C:\Users\klsm\.codex\skills` are launchers only.
If one of those skills triggers, read the project-owned skill listed above
before changing any West Kowloon artifact.

## Harness Skills

When a project skill references a harness skill, read the harness source file
under:

`D:\Workspace\qa-harness\01-system\01-skills`

Do not replace these with ad hoc prompts or generic translation, spreadsheet,
or document behavior.

## Project Context

Read project context and indexes before producing or reviewing artifacts:

- `01-requirements\00-project-overview\project-context.md`
- `01-requirements\00-project-overview\translation-glossary.md`
- `01-requirements\00-project-overview\domain-glossary.md`
- `01-requirements\01-source-documents\source-index.md`
