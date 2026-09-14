# 02-platform/03-infra/

Windows-native observability stack. Three services launched by .bat files
in this directory. **No WSL, no Docker** (since 2026-05-27).

## Services

| Service | Port | Launcher | Binary location | Data |
|---|---|---|---|---|
| **Prometheus** | `9090` | `start-prometheus.bat` | `D:\prometheus\prometheus-2.51.0.windows-amd64\` | `D:\prometheus\data\` (TSDB, 7-day retention) |
| **Loki** | `3100` | `start-loki.bat` | `D:\loki\loki-windows-amd64.exe` | `D:\loki\data\` (BoltDB-shipper + chunks) |
| **Grafana** | `3000` | `start-grafana.bat` | `D:\grafana\grafana-v10.4.1\` | `D:\grafana\grafana-v10.4.1\data\` |

Binary install dirs are **outside** the repo — see `bootstrap.ps1` for
downloads and `INSTALL.md` for the exact URLs.

## Config in this dir

```
02-platform/03-infra/
├── start-prometheus.bat     launcher (calls prometheus.exe with --config.file=...)
├── start-loki.bat
├── start-grafana.bat
├── prometheus/
│   └── prometheus.yml       scrape configs (Locust on 127.0.0.1:9646)
├── loki/
│   └── loki-config.yaml     single-binary Loki config
└── grafana/
    ├── grafana.windows.ini  paths/admin/anonymous-Viewer config
    ├── provisioning/
    │   ├── datasources/datasources.yml    Prometheus + Loki UIDs
    │   └── dashboards/dashboards.yml      auto-load locust-performance.json
    └── dashboards/
        └── locust-performance.json        the 6-panel perf dashboard
```

## Quirks worth knowing

1. **Prometheus targets must use IPv4 (`127.0.0.1:9646`), not `localhost:9646`.**
   On Windows, `localhost` resolves IPv6 `[::1]` first; Locust's
   `start_http_server(addr="0.0.0.0")` only binds IPv4, so a `localhost`
   target silently fails forever. See memory
   `project_perf_test_two_bugs_2026_05_27` for the full debug.

2. **Grafana iframe URLs need `refresh=5s`.** Without it the embedded
   panel loads once and freezes. Backend's `metrics_client.get_grafana_panel_url()`
   adds this by default since 2026-05-27.

3. **Locust port `9646` is transient** — only listens when a perf test is
   actively running. Prometheus targets show DOWN between runs; that's
   normal.

## See also

- [../../README.md](../../README.md) — top-level
- [../01-automation/CLAUDE.md](../01-automation/CLAUDE.md) — startup runbook + service matrix
- [../01-automation/TROUBLESHOOTING.md](../01-automation/TROUBLESHOOTING.md) — failure recipes
- [../01-automation/SESSION_NOTES.md](../01-automation/SESSION_NOTES.md) — why we went Windows-native (vs WSL Docker)
