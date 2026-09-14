# Test Case Change Audit Trail

Scope: QA harness workflow and all projects under `D:\Workspace`.

Trigger: A post-sign-off case removal exposed that MD-only audit notes are not
enough because reviewers open the current `.xlsx` and `.docx` artifacts.

Decision: Any test-case add, modify, remove, or post-sign-off scope adjustment
must be visible in workbook `Audit Trail` sheet(s) and in the paired review
DOCX `Review Trail and Version Record`. If automation assessment already
exists, update its workbook and review document too.

Implementation: `01-system/03-tools/record_testcase_change.py` writes the
audit rows and regenerates review DOCX files. `01-system/03-tools/check_testcase_audit_trail.py`
is wired into `gate.py` as the default case-audit validator.
