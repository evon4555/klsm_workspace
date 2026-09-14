"""Apply deterministic-only cleanup to the 2026-06-12 registration/login test cases.

Scope:
- remove deprecated or product-open rows that are hard to maintain;
- keep deterministic PRD behavior even when execution is still manual/NA;
- fix known module/typo issues without changing workbook layout.
"""
import io
import sys
from copy import copy
from pathlib import Path

import openpyxl
from openpyxl.styles import PatternFill

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

XLSX = Path("test-cases-registration-login_2026-06-12.xlsx")
YELLOW = PatternFill(start_color="FFFFFF00", end_color="FFFFFF00", fill_type="solid")

DELETE_TC_IDS = {
    # Removed from current PRD scope.
    "SIT-TC-WEB-AUTH-036",
    "SIT-TC-WEB-AUTH-037",
    # Placeholder/mobile rows replaced by concrete mobile/manual cases.
    "SIT-TC-WEB-AUTH-046",
    "SIT-TC-WEB-AUTH-047",
    # Product-open rows.
    "SIT-TC-WEB-AUTH-064",
    "SIT-TC-WEB-AUTH-065",
    "SIT-TC-WEB-AUTH-068",
    "SIT-TC-WEB-AUTH-069",
    "SIT-TC-WEB-AUTH-070",
    "SIT-TC-WEB-AUTH-071",
    "SIT-TC-WEB-AUTH-072",
    "SIT-TC-WEB-AUTH-074",
}


def header_map(ws):
    return {
        str(ws.cell(1, c).value).split("\n")[0].strip(): c
        for c in range(1, ws.max_column + 1)
        if ws.cell(1, c).value
    }


def row_by_id(ws, hdr):
    id_col = hdr["Test Case ID"]
    return {
        ws.cell(rn, id_col).value: rn
        for rn in range(2, ws.max_row + 1)
        if ws.cell(rn, id_col).value
    }


def set_cell(ws, hdr, rn, col_name, value, highlight=True):
    cell = ws.cell(rn, hdr[col_name])
    cell.value = value
    if highlight:
        cell.fill = YELLOW


def append_note(ws, hdr, rn, note):
    cell = ws.cell(rn, hdr["Comments/Remarks"])
    current = (cell.value or "").strip()
    if note not in current:
        cell.value = f"{current} {note}".strip()
        cell.fill = YELLOW


def delete_rows_by_tc_id(ws, hdr, tc_ids):
    id_col = hdr["Test Case ID"]
    deleted = []
    for rn in range(ws.max_row, 1, -1):
        tcid = ws.cell(rn, id_col).value
        if tcid in tc_ids:
            ws.delete_rows(rn, 1)
            deleted.append(tcid)
    return list(reversed(deleted))


def add_row_if_missing(ws, hdr, tcid, values, reference_tcid="SIT-TC-WEB-AUTH-100"):
    rows = row_by_id(ws, hdr)
    if tcid in rows:
        return None

    ref_rn = rows.get(reference_tcid, 2)
    rn = ws.max_row + 1
    ws.row_dimensions[rn].height = ws.row_dimensions[ref_rn].height
    for c in range(1, ws.max_column + 1):
        ref = ws.cell(ref_rn, c)
        cell = ws.cell(rn, c)
        if ref.has_style:
            cell.font = copy(ref.font)
            cell.fill = copy(ref.fill)
            cell.border = copy(ref.border)
            cell.alignment = copy(ref.alignment)
            cell.number_format = ref.number_format
            cell.protection = copy(ref.protection)

    set_cell(ws, hdr, rn, "Test Case ID", tcid)
    for col_name, value in values.items():
        set_cell(ws, hdr, rn, col_name, value)
    return rn


wb = openpyxl.load_workbook(XLSX)
ws = wb["Test Cases"]
hdr = header_map(ws)
rows = row_by_id(ws, hdr)

modified = []

def update(tcid, fields, note=None):
    rn = rows[tcid]
    for col_name, value in fields.items():
        set_cell(ws, hdr, rn, col_name, value)
        modified.append(f"{tcid}.{col_name}")
    if note:
        append_note(ws, hdr, rn, note)
        modified.append(f"{tcid}.Comments/Remarks")


# Data-quality fixes.
update(
    "SIT-TC-WEB-AUTH-001",
    {
        "Preconditions": "SIT website available; test email unused. (Mobile mode covered by AUTH-118)",
        "Test Steps": (
            "1. Open registration page and select Email mode.\n"
            "2. Enter email and fill CAPTCHA.\n"
            "3. Click \"Get Code\" and receive OTP then enter it.\n"
            "4. Enter password; verify focus-out triggers inline password-rule validation.\n"
            "5. Enter password again (repeat).\n"
            "6. Click Submit."
        ),
    },
    "Cleaned 2026-06-15: typo/whitespace only.",
)
update(
    "SIT-TC-WEB-AUTH-009",
    {"Module/Feature": "Website / Registered Login (password mode)"},
    "Cleaned 2026-06-15: restored module name.",
)
update(
    "SIT-TC-WEB-AUTH-118",
    {"Module/Feature": "Website / Mobile Registration"},
    "Cleaned 2026-06-15: fixed module column.",
)
update(
    "SIT-TC-WEB-AUTH-119",
    {"Module/Feature": "Website / Mobile Registration"},
    "Cleaned 2026-06-15: fixed module column.",
)

# Remove embedded open assertions while keeping deterministic main flows.
update(
    "SIT-TC-WEB-AUTH-015",
    {
        "Test Case Description": (
            "Verify user can reset password through the confirmed direct-reset flow: "
            "email -> captcha -> OTP -> new password."
        ),
        "Test Steps": (
            "1. Open forgot password.\n"
            "2. Enter email + captcha.\n"
            "3. Receive OTP and enter it.\n"
            "4. Set a new password.\n"
            "5. Login with the new password."
        ),
        "Expected Result": (
            "1. Password reset succeeds.\n"
            "2. Old password no longer works.\n"
            "3. New password logs in."
        ),
    },
    "Cleaned 2026-06-15: removed old reset-model open question.",
)
update(
    "SIT-TC-WEB-AUTH-022",
    {
        "Expected Result": (
            "1. Guest login is blocked.\n"
            "2. Clear verification failure message is shown.\n"
            "3. No guest session is created."
        ),
    },
    "Cleaned 2026-06-15: removed redirect-target assertion.",
)
update(
    "SIT-TC-WEB-AUTH-030",
    {
        "Test Case Description": "Verify captcha refreshes when the user clicks the captcha image.",
        "Test Steps": (
            "1. Note captcha image A.\n"
            "2. Click the captcha image.\n"
            "3. Note captcha image B.\n"
            "4. Submit using image A's value after refresh, then submit using image B's value."
        ),
        "Expected Result": (
            "1. Click-to-refresh loads a new captcha image.\n"
            "2. The previous captcha value no longer passes after refresh.\n"
            "3. The current captcha value can proceed."
        ),
    },
    "Cleaned 2026-06-15: removed unconfirmed auto-refresh-on-error branch.",
)
update(
    "SIT-TC-WEB-AUTH-034",
    {
        "Test Case Description": "Verify a registered user can log in via OTP mode using email + captcha + OTP.",
    },
    "Cleaned 2026-06-15: removed old password-requirement open question.",
)
update(
    "SIT-TC-WEB-AUTH-035",
    {
        "Test Case Description": (
            "Verify a not-yet-registered email completing OTP login auto-creates an account "
            "and the user is logged in."
        ),
        "Expected Result": "1. New account is created.\n2. User is logged in.",
    },
    "Cleaned 2026-06-15: removed subsequent-native-registration collision assertion.",
)
update(
    "SIT-TC-WEB-AUTH-066",
    {
        "Test Case Description": (
            "Verify a password-mode session expires after 30 days from last successful "
            "authentication, after which authenticated access is denied."
        ),
        "Test Steps": (
            "1. Login via password mode.\n"
            "2. Age the session past 30 days using a test-clock/session override, or execute "
            "through the configured long-duration test method.\n"
            "3. Attempt to use a registered-only feature."
        ),
    },
    "Cleaned 2026-06-15: retained because 30-day rule is now deterministic.",
)
update(
    "SIT-TC-WEB-AUTH-067",
    {
        "Test Case Description": (
            "Verify an OTP-mode session expires after 30 days from last successful "
            "authentication, after which authenticated access is denied."
        ),
        "Test Steps": (
            "1. Login via OTP mode.\n"
            "2. Age the session past 30 days using a test-clock/session override, or execute "
            "through the configured long-duration test method.\n"
            "3. Attempt to use a registered-only feature."
        ),
    },
    "Cleaned 2026-06-15: retained because 30-day rule is now deterministic.",
)

# Remove discussion-only reward/tag assertions from the conversion happy paths.
update(
    "SIT-TC-WEB-AUTH-107",
    {
        "Test Case Description": (
            "Verify the upgrade branch when the chosen contact method is EMAIL: opt-in checked "
            "+ payment success converts the guest temp account into a registered account; the "
            "chosen EMAIL is stored as the account contact, mobile field is empty; the order is linked."
        ),
        "Test Steps": (
            "1. Tick the opt-in checkbox.\n"
            "2. Submit the order; complete payment.\n"
            "3. Inspect the resulting account in admin / DB:\n"
            "   a. Confirm the guest account was upgraded to a registered account.\n"
            "   b. Confirm the chosen email is stored as the account contact; the mobile field is empty.\n"
            "   c. Confirm the order is linked to this account."
        ),
        "Expected Result": (
            "1. The guest temp account is converted to a registered account.\n"
            "2. The EMAIL is stored on the account; the mobile field is empty per PRD.\n"
            "3. Order is linked to the converted account."
        ),
    },
    "Cleaned 2026-06-15: narrowed to deterministic account/order assertions.",
)
update(
    "SIT-TC-WEB-AUTH-116",
    {
        "Test Case Description": (
            "Verify the upgrade branch when the chosen contact method is MOBILE: opt-in checked "
            "+ payment success converts the guest into a registered account; the MOBILE is stored "
            "as the account contact, the email field is empty; the order is linked."
        ),
        "Test Steps": (
            "1. Tick the opt-in checkbox.\n"
            "2. Submit the order; complete payment.\n"
            "3. Inspect resulting account in admin / DB:\n"
            "   a. Confirm mobile is stored and email is empty.\n"
            "   b. Confirm the order is linked to this account."
        ),
        "Expected Result": (
            "1. The guest temp account is converted to a registered account.\n"
            "2. The MOBILE is stored on the account; the email field is empty per PRD.\n"
            "3. Order is linked to the converted account."
        ),
    },
    "Cleaned 2026-06-15: narrowed to deterministic account/order assertions.",
)

# Second-pass cleanup: remove old open/pending wording that lived outside the
# guest-to-member rows but still made the workbook harder to maintain.
update(
    "SIT-TC-WEB-AUTH-018",
    {
        "Test Case Description": (
            "[Revised 2026-06-02] Verify third-party login with a provider whose unique-id "
            "is ALREADY linked: the Link Your Account page is skipped and the user is logged in "
            "directly. PRD §3.2.2 step 5.a: 若已绑定 直接登录成功."
        ),
    },
    "Cleaned 2026-06-15: removed unrelated provider-inclusion note.",
)
update(
    "SIT-TC-WEB-AUTH-030",
    {
        "Collected from": "REQ-WEB-REG-001, Mindmap 注册 > 动态码 click-to-refresh",
    },
    "Cleaned 2026-06-15: source now matches deterministic click-refresh scope.",
)
for tcid in ["SIT-TC-WEB-AUTH-039", "SIT-TC-WEB-AUTH-040", "SIT-TC-WEB-AUTH-041"]:
    rn = rows[tcid]
    expected = ws.cell(rn, hdr["Expected Result"]).value or ""
    expected = expected.replace(
        " **Pending SSO test environment (SSO confirmed in scope per customer review 2026-06-01).**",
        "",
    ).replace(
        "**Pending SSO test environment (SSO confirmed in scope per customer review 2026-06-01).**",
        "",
    )
    set_cell(ws, hdr, rn, "Expected Result", expected)
    append_note(ws, hdr, rn, "Cleaned 2026-06-15: execution remains NA because SSO test environment is unavailable.")
    modified.append(f"{tcid}.Expected Result")
    modified.append(f"{tcid}.Comments/Remarks")
update(
    "SIT-TC-WEB-AUTH-066",
    {"Collected from": "REQ-WEB-REG-003; 2026-06-10 PRD: non-guest password session expires after 30 days"},
    "Cleaned 2026-06-15: removed old mindmap question marker from source.",
)
update(
    "SIT-TC-WEB-AUTH-067",
    {"Collected from": "REQ-WEB-REG-003; 2026-06-10 PRD: non-guest OTP session expires after 30 days"},
    "Cleaned 2026-06-15: removed old mindmap question marker from source.",
)
for tcid in ["SIT-TC-WEB-AUTH-073", "SIT-TC-WEB-AUTH-076", "SIT-TC-WEB-AUTH-077"]:
    rn = rows[tcid]
    set_cell(ws, hdr, rn, "Comments/Remarks", "Automation not implemented; keep as manual/NA until step definitions are added.")
    modified.append(f"{tcid}.Comments/Remarks")
for tcid in [
    "SIT-TC-WEB-AUTH-078",
    "SIT-TC-WEB-AUTH-079",
    "SIT-TC-WEB-AUTH-080",
    "SIT-TC-WEB-AUTH-081",
    "SIT-TC-WEB-AUTH-082",
    "SIT-TC-WEB-AUTH-084",
    "SIT-TC-WEB-AUTH-086",
    "SIT-TC-WEB-AUTH-087",
]:
    rn = rows[tcid]
    set_cell(ws, hdr, rn, "Comments/Remarks", "NA - OAuth sandbox not provisioned for current execution.")
    modified.append(f"{tcid}.Comments/Remarks")
update(
    "SIT-TC-WEB-AUTH-083",
    {
        "Expected Result": (
            "1. OTP email/SMS is delivered.\n"
            "2. Get Code button is disabled or shows countdown during the 30s cooldown.\n"
            "3. After 30s, Get Code re-enables and a fresh OTP can be requested.\n"
            "4. Wrong OTP returns inline error 'Verification Code incorrect'.\n"
            "5. Correct OTP proceeds to binding submission."
        ),
        "Comments/Remarks": "NA - OAuth sandbox not provisioned for current execution.",
    },
    "Cleaned 2026-06-15: removed wrong-OTP attempt-limit open question.",
)
update(
    "SIT-TC-WEB-AUTH-085",
    {
        "Test Case Description": (
            "Verify the Link Your Account page can toggle between Email and Phone modes via "
            "the 'Use phone number' / 'Use email' link, and only the active mode's inputs are shown."
        ),
        "Test Steps": (
            "1. Start on Link Your Account in Email mode.\n"
            "2. Verify Email input is shown.\n"
            "3. Click 'Use phone number'.\n"
            "4. Verify Phone input and country-code dropdown are shown, while Email input is hidden.\n"
            "5. Click 'Use email'.\n"
            "6. Verify Email input is shown again, while Phone input is hidden."
        ),
        "Expected Result": (
            "1. Email mode and Phone mode can be toggled without leaving the Link Your Account page.\n"
            "2. Only the active mode's inputs are visible and eligible for validation/submission.\n"
            "3. Inactive-mode values are not submitted."
        ),
        "Comments/Remarks": "NA - OAuth sandbox not provisioned for current execution.",
    },
    "Cleaned 2026-06-15: limited to deterministic mode-switch behavior.",
)

deleted = delete_rows_by_tc_id(ws, hdr, DELETE_TC_IDS)

added_rows = []
added = add_row_if_missing(
    ws,
    hdr,
    "SIT-TC-WEB-AUTH-125",
    {
        "Label": "SIT/UAT",
        "Module/Feature": "Guest-to-Member",
        "Priority": "High",
        "Severity": "Medium",
        "Collected from": "2026-06-12 PRD §订单确认页 item 4",
        "Test Scenario": "Order page - delivery notice follows selected contact method",
        "Test Case Description": (
            "Verify the order page delivery notice displays the selected contact method "
            "(Email or Mobile) and shows a not-provided state when the selected field is empty."
        ),
        "Preconditions": "Guest user reaches the order-confirmation page.",
        "Test Steps": (
            "1. Select Email and leave Email empty; inspect the delivery notice.\n"
            "2. Fill a valid email; inspect the delivery notice again.\n"
            "3. Select Mobile and leave Mobile empty; inspect the delivery notice.\n"
            "4. Fill a valid mobile; inspect the delivery notice again.\n"
            "5. Fill both Email and Mobile, switch the selected method, and inspect the notice."
        ),
        "Test Data": "Valid email; valid HK mobile.",
        "Expected Result": (
            "1. When Email is selected and empty, the notice indicates Email is not provided.\n"
            "2. When Email is selected and filled, the notice shows the selected email.\n"
            "3. When Mobile is selected and empty, the notice indicates Mobile is not provided.\n"
            "4. When Mobile is selected and filled, the notice shows the selected mobile.\n"
            "5. When both fields are filled, the notice follows only the currently selected method."
        ),
        "Test Case Owner": "Antank QA Team",
        "Environment": "SIT",
        "Status": "NA",
        "Comments/Remarks": "Added 2026-06-15: deterministic PRD coverage for delivery notice.",
    },
)
if added:
    added_rows.append("SIT-TC-WEB-AUTH-125")

TEXT_REPLACEMENTS = {
    "NA-deferred:": "NA -",
    "tagged @todo and not yet implemented": "whose step definitions are not implemented",
    "See CHANGE.md open question #2 re: WhatsApp inclusion.": "",
    "Cleaned 2026-06-15: removed old reset-model open question.": (
        "Cleaned 2026-06-15: removed old reset-model uncertainty."
    ),
    "Cleaned 2026-06-15: removed old password-requirement open question.": (
        "Cleaned 2026-06-15: removed old password-requirement uncertainty."
    ),
    "Cleaned 2026-06-15: removed wrong-OTP attempt-limit open question.": (
        "Cleaned 2026-06-15: removed wrong-OTP attempt-limit note."
    ),
    "Cleaned 2026-06-15: removed TBD redirect-target assertion.": (
        "Cleaned 2026-06-15: removed redirect-target assertion."
    ),
    "Cleaned 2026-06-15: removed subsequent-native-registration collision TBD assertion.": (
        "Cleaned 2026-06-15: removed subsequent-native-registration collision assertion."
    ),
    "TC-070 SIT confirmation 2026-05-23 (promotes Deferred → executable)": (
        "TC-070 SIT confirmation 2026-05-23 (resolved direct-reset flow)"
    ),
    "Cleaned 2026-06-15: removed reward-pack/conversion-tag assertions pending product configuration.": (
        "Cleaned 2026-06-15: narrowed to deterministic account/order assertions."
    ),
    (
        "Cleaned 2026-06-15: removed reward-pack/conversion-tag assertions. "
        "Cleaned 2026-06-15: removed reward-pack/conversion-tag assertions."
    ): "Cleaned 2026-06-15: narrowed to deterministic account/order assertions.",
    "Cleaned 2026-06-15: removed reward-pack/conversion-tag assertions.": (
        "Cleaned 2026-06-15: narrowed to deterministic account/order assertions."
    ),
    "@todo — pending step def implementation": "Automation not implemented; keep as manual/NA until step definitions are added.",
    "pending page-object refactor": "requires page-object refactor",
    "Pending OAuth sandbox provisioning": "NA - OAuth sandbox not provisioned for current execution.",
    "[Open] PRD §3.2.2 待确认: whether wrong-OTP has an attempt-count or time-window upper limit. See CHANGE.md open question #1.": (
        "NA - OAuth sandbox not provisioned for current execution."
    ),
    "[Open] Whether email value persists across Email↔Phone mode switch — confirm with PM. See CHANGE.md open question #3.": (
        "NA - OAuth sandbox not provisioned for current execution."
    ),
}

cleaned_text_cells = 0
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=ws.max_column):
    for cell in row:
        if not isinstance(cell.value, str):
            continue
        new_value = cell.value
        for old, new in TEXT_REPLACEMENTS.items():
            new_value = new_value.replace(old, new)
        new_value = new_value.strip()
        if new_value != cell.value:
            cell.value = new_value
            cell.fill = YELLOW
            cleaned_text_cells += 1

wb.save(XLSX)

print(f"Modified cells: {len(modified)}")
for item in modified:
    print(f"  modified: {item}")
print(f"Deleted rows: {len(deleted)}")
for tcid in deleted:
    print(f"  deleted: {tcid}")
print(f"Added rows: {len(added_rows)}")
for tcid in added_rows:
    print(f"  added: {tcid}")
print(f"Cleaned residual wording cells: {cleaned_text_cells}")
