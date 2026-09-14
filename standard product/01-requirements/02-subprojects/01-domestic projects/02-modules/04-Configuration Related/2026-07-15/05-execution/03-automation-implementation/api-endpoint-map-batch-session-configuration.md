# API Endpoint Map - Batch Session Configuration

Source package: `../01-automation-demo/short demo.docx`

Additional verification source: deployed frontend chunks on
`https://anticket.lengliwh.com`:

- `mshow/static/showApi-B6ZqxnWM.js`
- `seatadmin/static/screening-C_m8H29K.js`
- `mshow/static/OpenShowDisplayBatchDrawer-XJYnBXMQ.js`
- `seatadmin/static/index-BoWtJIiP.js`

Sensitive-data rule: this map intentionally excludes raw cookies,
authorization values, passwords, and private browser payloads.

## Environment And Session

| Item | Value |
|---|---|
| Standard Product admin entry | `https://anticket.lengliwh.com/mainframe/index.html#/home` |
| Operational access reference | `D:\Workspace\standard product\01-requirements\02-subprojects\01-domestic projects\01-source-documents\网站地址以及权限.txt` |
| Automation session rule | Use a real authenticated session; do not paste captured browser cookies into scripts. |
| Valid execution evidence | QA dashboard run `200`, project `standard product`, result `13 passed / 0 failed / 0 errored / 0 skipped` |

## Common Request Headers

| Header | Usage |
|---|---|
| `accept: application/json, text/plain, */*` | All observed API requests. |
| `lang: zh-CN` | All observed API requests. |
| `referer` | `https://anticket.lengliwh.com/mshow/index.html` for mshow; `https://anticket.lengliwh.com/seatadmin/index.html` for seatadmin. |
| `routerpath` | Route-specific; see endpoint rows. |
| `parentpath` | Present for seatadmin and no-seat mshow flows. |
| `origin` | Required on observed POST requests. |

## Test Data Used By Current Automation

| Session family | Program ID | Target IDs | Route headers |
|---|---:|---|---|
| Seat-selection / seatadmin | `225198` | `scheduleIds=19839,19837` | `parentpath=seatadmin:/seat/programs`, `routerpath=seatadmin:/seat/detail/schedule` |
| Admission-ticket / mshow | `225562` | `showIds=90051349,90051350` | `routerpath=mshow:/menpiao/newDetail/newSchedule` |
| No-seat / mshow | `223334` | `showIds=90042939,90037094` | `parentpath=mshow:/menpiao/programs`, `routerpath=mshow:/menpiao/detail/schedule` |

| Target | Value |
|---|---|
| Saleable ticket group | `groups=57689` |
| Calendar display for seat-selection and admission-ticket | `showCalendar=Y` |
| Calendar display for no-seat | `showCalendar=N` |
| Session-list display | `display=Y` |

## Endpoint Families

### Seat-selection / seatadmin / schedule

| Purpose | Method | Path | Query/body parameters | Evidence |
|---|---|---|---|---|
| Read program | GET | `/theatre/home/ticket/program/get.xhtml` | `id=225198` | Demo curl + run `200` |
| Read schedules | GET | `/theatre/home/schedule/list.xhtml` | `programId=225198`, `pageNo=1`, `pageSize=10`, blank filters for time/status/keyword | Demo curl + run `200` |
| Read saleable ticket group | GET | `/theatre/home/schedule/setting/getUserGroup.xhtml` | `scheduleId=<scheduleId>` | Frontend chunk + run `200` |
| Save saleable ticket group | POST | `/theatre/home/schedule/setting/batchSaveUserGroup.xhtml` | `scheduleIds=19839,19837`, `groups=57689` | Frontend chunk + run `200` |
| Save calendar display | POST | `/theatre/home/schedule/op/batchUpdateShowCalendar.xhtml` | `scheduleIds=19839,19837`, `showCalendar=Y` | Frontend chunk + run `200` |
| Save session-list display | POST | `/theatre/home/schedule/op/batchUpdateDisplay.xhtml` | `scheduleIds=19839,19837`, `display=Y` | Demo curl + run `200` |

### Admission-ticket and no-seat / mshow / openShow

| Purpose | Method | Path | Query/body parameters | Evidence |
|---|---|---|---|---|
| Read sessions by time range | GET | `/theatre/home/openShow/listShowByTimeRange.xhtml` | Admission: `programId=225562`, `isExpired=N`; no-seat: `programId=223334`, `ticketTypeIds=`; common blank filters for date/status/keyword | Demo curl + run `200` |
| Read show detail | GET | `/theatre/home/openShow/get.xhtml` | `id=<showId>` | Demo curl + run `200` |
| Save saleable ticket group | POST | `/theatre/home/openShow/op/batchSaveUserGroup.xhtml` | `showIds=<showIds>`, `groups=57689` | Demo curl + frontend chunk + run `200` |
| Save calendar display | POST | `/theatre/home/openShow/op/batchUpdateShowCalendar.xhtml` | `showIds=<showIds>`, `showCalendar=Y` or `N` | Demo curl + frontend chunk + run `200` |
| Save session-list display | POST | `/theatre/home/openShow/op/batchUpdateDisplay.xhtml` | `showIds=<showIds>`, `display=Y` | Frontend chunk + run `200` |

## Case Mapping

| Case ID | Automation layer | Verification | Write endpoint | Status |
|---|---|---|---|---|
| `SIT-TC-STD-CONFIG-001` | UI | Batch operation menu exposes the three signed actions. | No write endpoint should be called. | Passed in run `200` |
| `SIT-TC-STD-CONFIG-003` | API | `schedule/setting/getUserGroup.xhtml?scheduleId=...` proves `checkIdList` changed from setup value to `57689`. | `POST /theatre/home/schedule/setting/batchSaveUserGroup.xhtml?scheduleIds=19839,19837&groups=57689` | Passed in run `200` |
| `SIT-TC-STD-CONFIG-004` | API | `openShow/listShowByTimeRange.xhtml` proves `groupIdList` changed from setup value to `57689`. | `POST /theatre/home/openShow/op/batchSaveUserGroup.xhtml?showIds=90051349,90051350&groups=57689` | Passed in run `200` |
| `SIT-TC-STD-CONFIG-005` | API | `openShow/listShowByTimeRange.xhtml` proves `groupIdList` changed from setup value to `57689`. | `POST /theatre/home/openShow/op/batchSaveUserGroup.xhtml?showIds=90042939,90037094&groups=57689` | Passed in run `200` |
| `SIT-TC-STD-CONFIG-006` | API | `schedule/list.xhtml` proves `showCalendar` changed from setup value to `Y` for both schedules. | `POST /theatre/home/schedule/op/batchUpdateShowCalendar.xhtml?scheduleIds=19839,19837&showCalendar=Y` | Passed in run `200` |
| `SIT-TC-STD-CONFIG-007` | API | `openShow/get.xhtml?id=...` proves `openShow.showCalendar` changed from setup value to `Y`. | `POST /theatre/home/openShow/op/batchUpdateShowCalendar.xhtml?showIds=90051349,90051350&showCalendar=Y` | Passed in run `200` |
| `SIT-TC-STD-CONFIG-008` | API | `openShow/get.xhtml?id=...` proves `openShow.showCalendar` changed from setup value to `N`. | `POST /theatre/home/openShow/op/batchUpdateShowCalendar.xhtml?showIds=90042939,90037094&showCalendar=N` | Passed in run `200` |
| `SIT-TC-STD-CONFIG-009` | API | `schedule/list.xhtml` proves `display` changed from setup value to `Y` for both schedules. | `POST /theatre/home/schedule/op/batchUpdateDisplay.xhtml?scheduleIds=19839,19837&display=Y` | Passed in run `200` |
| `SIT-TC-STD-CONFIG-010` | API | `openShow/get.xhtml?id=...` proves `openShow.display` changed from setup value to `Y`. | `POST /theatre/home/openShow/op/batchUpdateDisplay.xhtml?showIds=90051349,90051350&display=Y` | Passed in run `200` |
| `SIT-TC-STD-CONFIG-011` | API | `openShow/get.xhtml?id=...` proves `openShow.display` changed from setup value to `Y`. | `POST /theatre/home/openShow/op/batchUpdateDisplay.xhtml?showIds=90042939,90037094&display=Y` | Passed in run `200` |
| `SIT-TC-STD-CONFIG-012` | UI | Mandatory target ticket group blocks pre-generation before any write API is submitted. | No write endpoint should be called. | Passed in run `200` |
| `SIT-TC-STD-CONFIG-013` | Mixed | API setup/action/readback proves only the remaining row changes; final Playwright UI evidence verifies the user-facing result. | `POST /theatre/home/openShow/op/batchUpdateDisplay.xhtml?showIds=90042939&display=<target>` then restore. | Passed in run `200` |
| `SIT-TC-STD-CONFIG-014` | UI | Returning or closing preview does not emit a batch write API. | No write endpoint should be called. | Passed in run `200` |
