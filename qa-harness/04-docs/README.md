# Docs

This folder stores cross-cutting design notes and migration plans for the QA
harness repository.

Use this folder for documents that explain structure, architecture, or migration
decisions, but are not themselves QA standards.

Current documents:

- `workspace-deployment-guide.md` - 新人部署、Team Lead 验收和日常更新手册。

- `workspace-structure.md` - workspace-level refactor plan and migration map.
- `path-reference-audit.md` - hard-coded old-path audit for physical migration.
- `historical-path-policy.md` - what to rewrite now vs preserve as evidence.
- `migration-gates.md` - gates before any physical directory move.
- `platform-project-split.md` - boundary between reusable platform automation
  and West Kowloon project automation.
- `project-workspace-contract.md` - standard `requirements`, `automation`, and
  `evidence` structure for concrete projects.

Durable decisions that should survive chat context loss go under
`05-memory\YYYY-MM-DD-short-topic.md`.

Imported Claude memory is archived under `05-memory\claude-import\`; it is source
material, not automatically current policy.
