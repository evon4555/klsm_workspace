# Standard Product Performance Tests

This folder stores Standard Product Locust entry files discovered by QA
Dashboard Performance Test.

## Linked Ticketing

`linked_ticket.py` runs the real cart API flow:

1. get cart number
2. cancel existing admission and seat cart items
3. add linked admission ticket
4. add linked seat ticket
5. cancel the linked admission and seat tickets

Runtime data must stay outside committed artifacts because it contains member
cookies and live ticketing identifiers. Preferred input:

```powershell
$env:STD_LINKED_TICKET_CSV = "D:\path\to\linked_ticket_params.local.csv"
$env:PERF_STORAGE_STATE = "D:\path\to\storage_state.json"
```

If not set, the script looks for
`D:\Workspace\standard product\02-automation\06-envs\linked_ticket_params.local.csv`,
then falls back to the local `workspace_tools` carts ticket checkout CSV.

The linked-ticket flow uses one live member session and live ticketing rows.
Default pacing is intentionally conservative:

```powershell
$env:PERF_LINKED_TICKET_WAIT_SECONDS = "10"
```

For multi-user or longer performance runs, prepare multiple valid rows in the
CSV to avoid same-account and same-ticket data contention.
