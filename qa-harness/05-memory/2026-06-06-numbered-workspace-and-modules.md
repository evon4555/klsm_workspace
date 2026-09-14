# Numbered Workspace And Modules

Date: 2026-06-06

Decision: human-facing workspace folders should use numeric prefixes so the
structure sorts predictably in file explorers.

Scope:

- Apply numbering to human-maintained architecture folders.
- Do not rename or number vendor folders, caches, virtual environments,
  generated artifacts, or tool internals unless they are part of the human
  navigation contract.
- Keep old unnumbered paths as hidden compatibility entries when scripts,
  historical documents, or old links still rely on them.

West Kowloon now exposes:

```text
west-kowloon\
  01-requirements\
  02-automation\
  03-evidence\
```

Website requirements now expose subproject/module structure:

```text
01-requirements\02-subprojects\02-website\
  01-source-documents\
  02-modules\
  03-changes\
```

Existing Website change packages were not deleted or rewritten. They remain in
the historical `changes` location with module-level junctions for the current
login/registration and ticketing work.
