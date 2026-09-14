# Behave Step Definitions

Step definitions in this folder must follow the project automation strategy:

- API steps use Python `requests` and call real endpoints.
- UI steps use Playwright against the real application.
- Mixed scenarios use API steps first and Playwright only for final UI checks.

Do not add local deterministic services or static HTML fixtures as passable
automation tests.
