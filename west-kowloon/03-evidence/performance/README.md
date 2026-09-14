# Performance Evidence

This folder stores West Kowloon performance-test evidence that should be kept
outside transient automation artifacts.

## Layout

- `latest/` - dashboard-managed latest Locust CSV output
- `runs/` - named or timestamped run packages worth preserving
- `analysis/` - written analysis, conclusions, and follow-up notes
- `grafana-exports/` - exported Grafana panels, screenshots, or JSON

The dashboard writes new Locust CSV output to:

`03-evidence/performance/latest/perf_latest*.csv`

## Evidence Rule

Keep raw UI, API, and MIX automation output in
`02-automation/07-artifacts` while a run is active.

Copy only selected durable evidence into `03-evidence` when it needs to support
review, audit, delivery, a defect, or later project memory. Do not mirror every
temporary automation run here by default.
