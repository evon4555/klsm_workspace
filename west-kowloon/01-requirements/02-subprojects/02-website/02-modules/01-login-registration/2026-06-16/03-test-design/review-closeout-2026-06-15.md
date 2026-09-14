# Registration/Login Test Case Review Closeout - 2026-06-15

## Scope

- Historical input workbook: `_archive/workbooks/test-cases-registration-login_2026-06-12.xlsx`
- Corrected workbook retained in this folder:
  `test-cases-registration-login_2026-06-12.fixed-2026-06-16.xlsx`
- Requirement source: `2026-06-12/prd/游客购票引导注册功能 (1).md`
- Harness repo: `D:\Workspace\qa-harness`
- Validation scope: Website registration/login `AUTH` test cases and matching `antank_*.feature` files.

## Incident

The first review iterations were not acceptable because the review relied on manual inspection and a custom deterministic gate before running the existing `qa-system/tools/gate.py` contract required by `D:\Workspace\qa-harness\CLAUDE.md`.

That created a false sense of completion. The formal harness gate later exposed schema, evidence, and traceability failures.

## Decisions Applied

- Remove test cases that depend on discussion-only, deprecated, or unconfirmed requirement branches.
- Keep only deterministic requirement coverage.
- Do not fake execution evidence to satisfy validators.
- Use `Not Run` for deterministic but unexecuted design rows.
- Keep `NA` only where there is an explicit non-executable reason and execution metadata.
- For Pass/Fail rows, `Comments/Remarks` must include a `features/...` automation reference.
- For this workbook, run the formal gate with an `AUTH` feature scope. Running one AUTH workbook against all feature files is an invalid scope because Cookies/HOME/SEAT/TKT features require their own workbooks.

## Workbook Changes

- Deleted discussion/deprecated IDs from the workbook:
  - `SIT-TC-WEB-AUTH-036`
  - `SIT-TC-WEB-AUTH-037`
  - `SIT-TC-WEB-AUTH-046`
  - `SIT-TC-WEB-AUTH-047`
  - `SIT-TC-WEB-AUTH-064`
  - `SIT-TC-WEB-AUTH-065`
  - `SIT-TC-WEB-AUTH-068`
  - `SIT-TC-WEB-AUTH-069`
  - `SIT-TC-WEB-AUTH-070`
  - `SIT-TC-WEB-AUTH-071`
  - `SIT-TC-WEB-AUTH-072`
  - `SIT-TC-WEB-AUTH-074`
- Added deterministic coverage:
  - `SIT-TC-WEB-AUTH-125`
- Added automation references to judged rows.
- Converted 38 execution-empty `NA` rows to `Not Run`.

## Feature Changes

- Removed feature references for deleted AUTH IDs.
- Added traceability for `SIT-TC-WEB-AUTH-125`.
- Replaced AUTH-scope `@todo`, `pending`, `TBD`, `Deferred`, and `placeholder` wording with deterministic `@na` / documented-only wording where automation is not repeatable.

## Validation Results

2026-06-16 follow-up review:

- The original workbook `_archive/workbooks/test-cases-registration-login_2026-06-12.xlsx` was open in WPS and could not be overwritten safely.
- A corrected, self-tested sibling workbook was written instead:
  `test-cases-registration-login_2026-06-12.fixed-2026-06-16.xlsx`.
- The corrected workbook removes duplicate `AUTH-017` / `AUTH-018` provider-expanded rows while retaining the provider-specific coverage in `AUTH-059` .. `AUTH-063`.
- `AUTH-017` and `AUTH-018` are marked `NA` because they require an OAuth provider mock.
- `AUTH-045` is marked `Not Run` because screenshot evidence was missing after row cleanup; it should not be counted as executed until rerun.

Reproducible local runner:

```powershell
python ".\_archive\scripts\_run_registration_login_auth_gate.py" ".\test-cases-registration-login_2026-06-12.fixed-2026-06-16.xlsx"
```

This rebuilds the temporary AUTH feature scope from the real
`D:\Workspace\west-kowloon\02-automation\01-features` source files before running the
custom deterministic gate and the formal `01-system\03-tools\gate.py` contract.

Custom deterministic review gate:

```powershell
python ".\_archive\scripts\_validate_2026_06_15_review_gates.py" ".\test-cases-registration-login_2026-06-12.fixed-2026-06-16.xlsx"
```

Result:

```text
PASS: deterministic review gates
rows=107 unique_ids=107 status_counts={'Pass': 31, 'Fail': 1, 'NA': 37, 'Not Run': 38}
```

Formal harness gate, scoped to AUTH feature files:

```powershell
python ".\_archive\scripts\_run_registration_login_auth_gate.py" ".\test-cases-registration-login_2026-06-12.fixed-2026-06-16.xlsx"
```

Result:

```text
schema        PASS
traceability  PASS  (X=107, F=107, X-F=0, F-X=0)
evidence      PASS
coverage      PASS
overall       PASS
```

Supplementary audit:

- Workbook duplicate IDs: none.
- Workbook forbidden discussion markers: none.
- Workbook deleted ID references: none.
- AUTH feature deleted ID references: none.
- AUTH feature `@todo` / `pending` / `TBD` / `Deferred` / `placeholder` residue: none.

## Operating Rule For Next Review

For West Kowloon QA workbook review, do not say "reviewed", "tested", or "safe to use" until:

1. The existing `CLAUDE.md` and `qa-system` workflow have been checked.
2. The formal `qa-system/tools/gate.py` has been run with the correct workbook and feature scope.
3. Any custom review script has passed.
4. Remaining failures are either fixed or explicitly classified as out-of-scope with evidence.
