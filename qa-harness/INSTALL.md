# Install

Use this on a fresh Windows machine from the physical qa-harness root:

```powershell
cd D:\Workspace\qa-harness
.\bootstrap.ps1
```

`bootstrap.ps1` prepares:

- Python venv: `02-platform\01-automation\.venv`
- dashboard frontend dependencies: `02-platform\02-dashboard\02-frontend\node_modules`
- Prometheus, Loki, and Grafana binaries under `D:\prometheus`, `D:\loki`, and `D:\grafana`

Project environment files are kept outside the harness platform:

```text
D:\Workspace\west-kowloon\02-automation\06-envs
```

After install:

```powershell
.\smoke-docs.ps1
.\start-all.bat
```

Open the dashboard at:

```text
http://127.0.0.1:5174
```

Stop services with:

```powershell
.\stop-all.bat
```

Do not use retired paths such as `D:\qa-harness`, `automation`, `dashboard`,
`infra`, or `qa-system`. The numbered folders are the physical layout.
