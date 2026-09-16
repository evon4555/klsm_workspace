# Test Run History Scope

- **Trigger:** The Test Run page selected performance Run #227 and displayed nine transaction metrics with `N/A` Case IDs and automation types.
- **Finding:** `/api/runs` treated `full` and `performance` as the same default history. The page then selected the highest run ID, even when it was not a functional test run. Run-detail loading also requested a ZenTao token when no scenarios had linked bugs, adding an unnecessary startup delay.
- **Decision:** The Test Run page's default history contains `full` functional runs only. Performance history remains available through the dedicated Performance Test API/page. `kind=all` remains the explicit cross-kind diagnostic view. Run detail skips ZenTao token/network work when no linked bugs exist.
- **Verification:** Backend tests pass; the live default history selects West Kowloon full Run #159, excludes performance runs, and renders all 11 functional Case IDs and UI automation types without browser console errors.
