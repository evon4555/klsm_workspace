# Performance Test Layout

`locustfile.py` is still the active Locust entry point used by the QA dashboard.
The subfolders below are the target structure for gradual cleanup.

```text
performance/
  locustfile.py          Active entry point. Keep exporting Locust User classes.
  business_create_order.py
                         Standalone minimal order-create Locust entry.
  linked_ticket.py       Linked admission + seat ticket cart flow migrated from
                         JMeter TG - Linked Ticket.
  users/                 Locust HttpUser classes and workload models.
  flows/                 Reusable request flows and business helpers.
  data/                  Test profiles, defaults, and data-shape notes.
```

## Current Rule

Do not move working code from `locustfile.py` into these folders in one large
change. Migrate one flow at a time, then verify with:

```powershell
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe -m locust -f D:\Workspace\west-kowloon\02-automation\02-tests\performance\locustfile.py --list
```

## Planned Split

- `users/login_users.py` exposes login-only user models.
- `users/business_users.py` exposes business-mix user models.
- `users/order_users.py` exposes order-create and order-cancel user models.
- `flows/auth_flow.py` owns website and SSO login helpers.
- `flows/ticketing_flow.py` owns programme, show, and ticket-type setup.
- `flows/order_flow.py` owns create-order and cancel-order request helpers.
- `data/performance_profiles.py` owns workload profile constants.

## Standalone Entry Files

`business_create_order.py` is a focused order-create scaffold. It does not log in
or look up real ticketing context; it only calls the order-create endpoint with a
minimal payload. Use it to verify dashboard file selection and script
separation. Add authentication and valid show/ticket data before treating it as
a final capacity test.

`linked_ticket.py` is the executable Locust version of the JMeter
`TG - Linked Ticket` flow from
`D:\workspace_tools\Load Test\jmeter\westk load test scripts\westk_website_load_test.jmx`.
It reads `westk_params.csv` cyclically, applies the website cookies from the
current row, then repeats the linked-ticket cart flow:

1. get cart number
2. cancel existing show and seat cart items
3. add the linked admission ticket
4. wait 2 seconds
5. add the linked seat ticket
6. cancel the linked admission and seat tickets

Dashboard usage:

```text
Project:      west-kowloon
Locust File:  tests/performance/linked_ticket.py
Mode:         Linked Ticket cart
Users:        100
Spawn Rate:   0.83 per second
Duration:     300s
Host:         https://anticket.lengliwh.com
```

Set `WESTK_LINKED_TICKET_CSV` if the parameter CSV is not at the default local
JMeter path.
