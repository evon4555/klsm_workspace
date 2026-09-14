# West Kowloon Subprojects

This folder separates West Kowloon work by subproject.

```text
02-subprojects\
  01-box-office\
  02-website\
```

Each subproject should use a consistent internal shape:

```text
<subproject>\
  01-source-documents\
  02-modules\
```

Use module folders for module-specific work. Requirement change packages should
live under:

```text
<subproject>\02-modules\<module>\<yyyy-mm-dd>
```

Do not create a top-level subproject change area for new work. If a source PRD
change spans multiple modules, update the affected module date packages and link
them back to the same dated source document.
