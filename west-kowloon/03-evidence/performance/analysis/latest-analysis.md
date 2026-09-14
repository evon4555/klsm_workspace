# Latest Performance Analysis

Date: 2026-06-22

Source CSV:

- `03-evidence/performance/latest/perf_latest_stats.csv`
- `03-evidence/performance/latest/perf_latest_stats_history.csv`
- `03-evidence/performance/latest/perf_latest_failures.csv`

## Run Summary

This latest imported run is a mixed/login-heavy run, not the new standalone
order-create business run. The CSV does not contain
`POST /thvendor/member/show/order/create`, so it should not be used as the
final capacity result for create order.

- Total requests: 127,411
- Total failures: 1
- Error rate: about 0.00%
- Average response time: 470.74 ms
- P50: 180 ms
- P95: 650 ms
- P99: 9,300 ms
- Reported aggregate RPS: 408.02
- Max active users: 1,000
- Peak history RPS: 596.60
- Final history RPS: 36.20

## Main Findings

Error rate did not increase materially. There was one
`ConnectionResetError(10054)` on `GET /mainframe/index.html (home)`.

The bigger signal is latency tail and throughput decay. During the stable
1,000-user period, RPS reached about 596.6, but near the end dropped to about
36.2 while active users stayed at 1,000. At the same time P99 stayed high and
ended around 9,100 ms. That pattern is more consistent with saturation,
server-side throttling, connection pool pressure, or long waits than with a
simple application error-rate problem.

The slowest P95 rows in the stats file were:

| Method | Endpoint | Requests | Failures | P95 ms | P99 ms | RPS |
|---|---|---:|---:|---:|---:|---:|
| GET | SSO: getCaptchaId | 1,542 | 0 | 2,900 | 10,000 | 4.94 |
| POST | POST /theatre/program/save (create program) | 5,666 | 0 | 720 | 11,000 | 18.14 |
| GET | GET /sso/getCaptchaId (API) | 17,509 | 0 | 710 | 11,000 | 56.07 |
| GET | SSO flow: getCaptchaId | 11,615 | 0 | 700 | 9,300 | 37.20 |
| GET | GET /menpiao/index.html (ticket SPA) | 23,242 | 0 | 700 | 11,000 | 74.43 |
| GET | GET /mainframe/index.html (home) | 28,925 | 1 | 700 | 11,000 | 92.63 |

## Interpretation

Because this run includes SSO/captcha and general page endpoints, the results
are useful for broad mixed-flow pressure, but they can hide the real capacity
of a business endpoint.

For create-order capacity, run:

- Locust File: `tests/performance/business_create_order.py`
- Mode: `Business: order create`

Then focus on:

`POST /thvendor/member/show/order/create (target)`

Do not use SSO/captcha setup rows as the business capacity indicator.

## Business Create Order Smoke

Run folder:

`03-evidence/performance/runs/business_create_order_smoke_20260622_171544`

This was a 1-user smoke only, not a capacity test.

- Auth setup: guest UI page returned HTTP 401, so the script used website API
  login fallback.
- Locust stats contained only the target business request, not setup login or
  captcha rows.
- Target: `POST /thvendor/member/show/order/create (target)`
- Requests: 8
- Failures: 0
- Average response time: 74.18 ms
- P50: 49 ms
- P95: 170 ms
- P99: 170 ms

This confirms the standalone script can bootstrap a session and isolate the
business endpoint in Locust stats. It is not evidence of production capacity.
