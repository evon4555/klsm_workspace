# Website Modules

Website work is organized by business module.

```text
02-modules\
  01-login-registration\
  02-homepage\
  03-ticketing\
  04-seat-selection\
  05-membership-card\
  06-events\
  07-merchandise\
  08-discount\
  09-accessibility-map\
  10-SSO\
  11-Desensitization\
```

Use module folders as derived working views from `..\01-source-documents`.
The source PRD can remain full-website and rolling; module folders should keep
the extracted analysis, test design, review, and execution outputs that apply to
that module.

Put all future requirement-change outputs directly under the affected module by
source/change date:

```text
<module>\<yyyy-mm-dd>
```

If multiple independent changes land on the same date for the same module,
start with one date package only when they are part of the same delivery thread.
Use a story suffix only when the changes are independent enough that sharing one
package would hide ownership or status:

```text
<module>\<yyyy-mm-dd>-story-<id>-<short-topic>
```

Do not create nested change-wrapper folders such as `01-changes`.

Each date package should contain:

```text
01-input\
02-analysis\
03-test-design\
04-test-case-review\
05-execution\
06-execution-review\
07-release-feedback\
package.md
```

Every date package must use `package.md` as the traceability entry point. The
package file should state source, change summary, affected modules, workflow
status, key outputs, and open questions.

When `01-input` already contains source material, do not stop after creating
empty workflow folders. Index the inputs and continue to the next required
workflow output. For requirement-change packages, the default next output is
`02-analysis/requirement-consolidation-<scope>.md` plus the generated `.docx`
review copy; `03-test-design` stays blocked until this consolidation is signed
off.

Human-facing review `.docx` files must use the project templates under
`D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates`:
`Requirement Review Template.docx` for requirement/scope review and
`Test Case Review Template.docx` for `04-test-case-review` sign-off.
QA2 AI review artifacts stay under `03-test-design/.iterations/`.

Each module should also keep `module-index.md` as the module timeline. Update it
whenever a date package is added or its status changes.

When a source PRD change spans multiple modules, create or update the affected
module date packages separately and link back to the same dated source document.
