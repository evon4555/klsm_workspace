"""Round 3 split: 7 remaining combined cases get explicit email + mobile twins.
  AUTH-001 -> AUTH-118 (mobile reg)
  AUTH-004 -> AUTH-119 (mobile duplicate)
  AUTH-083 -> AUTH-120 (third-party Bind page mobile)
  AUTH-096 -> AUTH-121 (Bind uniqueness check 1 mobile)
  AUTH-097 -> AUTH-122 (Bind uniqueness check 2 mobile)
  AUTH-101 -> AUTH-123 (Order page picker mobile-mode)
  AUTH-108 -> AUTH-124 (Submit + payment WITHOUT opt-in mobile)
"""
import openpyxl, io, sys
from copy import copy
from openpyxl.styles import PatternFill
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

XLSX = 'test-cases-registration-login_2026-06-12.xlsx'
YELLOW = PatternFill(start_color='FFFFFF00', end_color='FFFFFF00', fill_type='solid')
MOBILE_NOTE = 'NA - QA手动测 (mainland team cannot auto-test HK SMS infra; manual verification by QA owner).'

# ---------- MODIFY existing: email-explicit -------------------------------
MODIFY = {
    'SIT-TC-WEB-AUTH-001': {
        'Test Scenario': 'Successful native registration (Email mode)',
        'Test Steps': '1. Open registration page; select Email mode.\n'
                      '2. Enter email + solve image CAPTCHA (动态码); confirm CAPTCHA passes before next step is unlocked.\n'
                      '3. Click "Get Code"; receive OTP and enter it; confirm OTP passes before password step is unlocked.\n'
                      '4. Enter password; verify focus-out triggers inline password-rule validation.\n'
                      '5. Enter password again (repeat).\n'
                      '6. Click Submit.',
    },
    'SIT-TC-WEB-AUTH-004': {
        'Test Scenario': 'Duplicate email registration is blocked with the specified 3-language error',
        'Test Case Description': 'Verify duplicate email registration is blocked with the exact 3-language error specified by PRD.',
        'Expected Result': '1. Registration is blocked.\n'
                           '2. The email field shows the 3-language error (red):\n'
                           '   - zh-CN: 该邮箱已注册，请登录或找回密码。\n'
                           '   - zh-HK: 此電子郵件已註冊，請直接登入或重設密碼。\n'
                           '   - en: This email address is already registered. Please sign in or reset your password.',
    },
    'SIT-TC-WEB-AUTH-083': {
        'Test Scenario': 'Bind page (third-party auth, Email mode) - OTP send, 30s cooldown, wrong-code retry',
        'Test Case Description': 'Verify the third-party-auth Bind page in Email mode: OTP send to email succeeds; resend within 30s cooldown is rejected; entering a wrong OTP shows the inline error and allows retry.',
    },
    'SIT-TC-WEB-AUTH-096': {
        'Test Scenario': 'Bind Email - uniqueness check 1 catches conflict (email already bound to another account)',
        'Test Case Description': 'Verify Bind-Email uniqueness check 1 (pre-OTP-send): when the entered EMAIL is already bound to another account, OTP is NOT sent and the 3-language error is shown.',
        'Expected Result': '1. Uniqueness check 1 fails: "该邮箱已绑定其他账号" (zh-CN), "此電子郵件已綁定其他帳號" (zh-HK), "This email is already bound to another account" (en).\n'
                           '2. OTP is NOT sent.\n'
                           '3. Account A remains unchanged.',
    },
    'SIT-TC-WEB-AUTH-097': {
        'Test Scenario': 'Bind Email - uniqueness check 2 catches race during OTP entry',
        'Test Case Description': 'Verify Bind-Email uniqueness check 2 (post-OTP-verify): when another account takes the same email during the OTP wait, the second check catches the race and bind fails.',
        'Expected Result': '1. Uniqueness check 2 fails: "该邮箱已绑定其他账号" (3 languages, same as AUTH-096).\n'
                           '2. Account A is NOT bound to that email.',
    },
    'SIT-TC-WEB-AUTH-101': {
        'Test Scenario': 'Order page - contact method picker: Email mode required-marker behavior',
        'Test Case Description': 'Verify that when the picker is set to Email, the Email input becomes required (red *) and the Mobile input is optional; submit is blocked when Email is empty.',
        'Test Steps': '1. On the order page, switch the contact picker to Email.\n'
                      '2. Verify Email becomes required (red *) and Mobile becomes optional.\n'
                      '3. Try submitting with Email empty — submit must be blocked.\n'
                      '4. Fill a valid email — submit becomes available.',
        'Expected Result': '1. Email is required when the picker = Email.\n'
                          '2. Mobile has no validation error if left empty.\n'
                          '3. Submit is blocked when Email is empty.',
    },
    'SIT-TC-WEB-AUTH-108': {
        'Test Scenario': 'Submit + payment success WITHOUT opt-in (email branch) → no upgrade; normal guest purchase',
        'Test Case Description': 'Verify the no-upgrade branch when the chosen contact is EMAIL: opt-in unchecked + payment success leaves the guest temp account as a guest; no registered account is created; the order is recorded under the guest temp account per the existing flow.',
        'Preconditions': 'Guest user on order page; contact method = Email; unregistered email; checkbox UNchecked.',
    },
}

# ---------- ADD mobile variants ------------------------------------------
ADD = [
    dict(
        tcid='SIT-TC-WEB-AUTH-118',
        Label='SIT/UAT',
        **{'Module/Feature': 'High'},
        Priority='High', Severity='High',
        **{'Collected from': '2026-06-10 PRD §用户邮箱/手机+密码注册 — mobile variant of AUTH-001'},
        **{'Test Scenario': 'Successful native registration (Mobile mode)'},
        **{'Test Case Description': 'Verify a visitor can complete native registration in Mobile mode through the gated 5-step flow: select Mobile -> image CAPTCHA -> mobile OTP (SMS) -> password (focus-out rule check) -> Submit.'},
        Preconditions='SIT website available; test HK mobile unused.',
        **{'Test Steps': '1. Open registration page; select Mobile mode.\n'
                        '2. Enter mobile + solve image CAPTCHA.\n'
                        '3. Click "Get Code"; receive OTP via SMS and enter it.\n'
                        '4. Enter password; verify focus-out rule check.\n'
                        '5. Enter password again (repeat).\n'
                        '6. Click Submit.'},
        **{'Test Data': 'Fresh HK mobile number; HK SMS provider.'},
        **{'Expected Result': '1. CAPTCHA gates the OTP step; OTP gates the password step.\n'
                             '2. Mobile OTP delivered via SMS.\n'
                             '3. On Submit, account is created and the user is logged in.\n'
                             '4. No duplicate account is created.'},
        **{'Test Case Owner': 'QA-manual'}, Environment='SIT', Status='NA',
        **{'Comments/Remarks': MOBILE_NOTE},
    ),
    dict(
        tcid='SIT-TC-WEB-AUTH-119',
        Label='SIT/UAT',
        **{'Module/Feature': 'High'},
        Priority='High', Severity='High',
        **{'Collected from': '2026-06-10 PRD §用户邮箱/手机+密码注册 step 5.a — mobile variant of AUTH-004'},
        **{'Test Scenario': 'Duplicate mobile registration is blocked with the specified 3-language error'},
        **{'Test Case Description': 'Verify duplicate mobile registration is blocked with the exact 3-language error specified by PRD.'},
        Preconditions='An account already exists with the test HK mobile.',
        **{'Test Steps': '1. Open registration page; select Mobile mode.\n'
                        '2. Enter the EXISTING HK mobile + valid CAPTCHA + valid OTP + valid password.\n'
                        '3. Submit.'},
        **{'Test Data': 'Existing HK mobile (already bound to an account).'},
        **{'Expected Result': '1. Registration is blocked.\n'
                             '2. The mobile field shows the 3-language error (red):\n'
                             '   - zh-CN: 该手机号已注册，请直接登录。\n'
                             '   - zh-HK: 此手機號碼已註冊，請直接登入。\n'
                             '   - en: This mobile number is already registered. Please sign in or reset your password.'},
        **{'Test Case Owner': 'QA-manual'}, Environment='SIT', Status='NA',
        **{'Comments/Remarks': MOBILE_NOTE},
    ),
    dict(
        tcid='SIT-TC-WEB-AUTH-120',
        Label='SIT',
        **{'Module/Feature': 'Third-party Bind'},
        Priority='Medium', Severity='Medium',
        **{'Collected from': 'Mobile variant of AUTH-083 (third-party Bind page)'},
        **{'Test Scenario': 'Bind page (third-party auth, Mobile mode) - OTP send, 30s cooldown, wrong-code retry'},
        **{'Test Case Description': 'Verify the third-party-auth Bind page in Mobile mode: OTP send via SMS succeeds; resend within 30s cooldown is rejected; wrong OTP shows inline error and allows retry.'},
        Preconditions='Third-party OAuth completed; landed on Bind page with Mobile mode selected.',
        **{'Test Steps': '1. On Bind page, switch to Mobile mode.\n'
                        '2. Enter a test HK mobile + solve CAPTCHA.\n'
                        '3. Click Get Code; receive OTP via SMS.\n'
                        '4. Try to resend within 30s — expect cooldown rejection.\n'
                        '5. Enter wrong OTP — expect retry-allowed error.\n'
                        '6. Enter correct OTP — submit.'},
        **{'Test Data': 'Fresh HK mobile.'},
        **{'Expected Result': '1. OTP delivered via SMS.\n'
                             '2. Resend within 30s rejected.\n'
                             '3. Wrong OTP: inline error + retry.\n'
                             '4. Correct OTP: bind succeeds.'},
        **{'Test Case Owner': 'QA-manual'}, Environment='SIT', Status='NA',
        **{'Comments/Remarks': MOBILE_NOTE},
    ),
    dict(
        tcid='SIT-TC-WEB-AUTH-121',
        Label='SIT',
        **{'Module/Feature': 'Bind Contact'},
        Priority='High', Severity='High',
        **{'Collected from': '2026-06-10 PRD §绑定手机/邮箱 — mobile variant of AUTH-096'},
        **{'Test Scenario': 'Bind Mobile - uniqueness check 1 catches conflict (mobile already bound to another account)'},
        **{'Test Case Description': 'Verify Bind-Mobile uniqueness check 1 (pre-OTP-send): when the entered MOBILE is already bound to another account, OTP is NOT sent and the 3-language error is shown.'},
        Preconditions='Account A: email-only. Account B: holds mobile X.',
        **{'Test Steps': '1. Log in as Account A; open Bind Mobile.\n'
                        '2. Enter mobile X (already on Account B).\n'
                        '3. Observe error before OTP send.'},
        **{'Test Data': 'HK mobile X already bound to Account B.'},
        **{'Expected Result': '1. Uniqueness check 1 fails: "该手机号已绑定其他账号" / "此手機號碼已綁定其他帳號" / "This mobile number is already bound to another account".\n'
                             '2. OTP is NOT sent.\n'
                             '3. Account A remains unchanged.'},
        **{'Test Case Owner': 'QA-manual'}, Environment='SIT', Status='NA',
        **{'Comments/Remarks': MOBILE_NOTE},
    ),
    dict(
        tcid='SIT-TC-WEB-AUTH-122',
        Label='SIT',
        **{'Module/Feature': 'Bind Contact'},
        Priority='Medium', Severity='Medium',
        **{'Collected from': '2026-06-10 PRD §绑定手机/邮箱 — mobile variant of AUTH-097'},
        **{'Test Scenario': 'Bind Mobile - uniqueness check 2 catches race during OTP entry'},
        **{'Test Case Description': 'Verify Bind-Mobile uniqueness check 2 (post-OTP-verify): when another account takes the same mobile during the OTP wait, the second check catches the race and bind fails.'},
        Preconditions='Account A: email-only. Race-simulation: another path binds mobile Y during the OTP window.',
        **{'Test Steps': '1. Start Bind Mobile with mobile Y.\n'
                        '2. After OTP send, before submitting, have mobile Y get bound to another account.\n'
                        '3. Submit OTP.'},
        **{'Test Data': 'Fresh HK mobile Y; back-office or two browser sessions for race.'},
        **{'Expected Result': '1. Uniqueness check 2 fails; same 3-language error as AUTH-121.\n'
                             '2. Account A is NOT bound to Y.'},
        **{'Test Case Owner': 'QA-manual'}, Environment='SIT', Status='NA',
        **{'Comments/Remarks': MOBILE_NOTE},
    ),
    dict(
        tcid='SIT-TC-WEB-AUTH-123',
        Label='SIT/UAT',
        **{'Module/Feature': 'Guest-to-Member'},
        Priority='High', Severity='High',
        **{'Collected from': '2026-06-10 PRD §订单确认页 — mobile variant of AUTH-101'},
        **{'Test Scenario': 'Order page - contact method picker: Mobile mode required-marker behavior'},
        **{'Test Case Description': 'Verify that when the picker is set to Mobile, the Mobile input becomes required (red *) and the Email input is optional; submit is blocked when Mobile is empty.'},
        Preconditions='Guest user reaches the order-confirmation page.',
        **{'Test Steps': '1. On the order page, switch the contact picker to Mobile.\n'
                        '2. Verify Mobile becomes required (red *) and Email becomes optional.\n'
                        '3. Try submitting with Mobile empty — submit must be blocked.\n'
                        '4. Fill a valid HK mobile — submit becomes available.'},
        **{'Test Data': 'Guest; HK mobile.'},
        **{'Expected Result': '1. Mobile is required when the picker = Mobile.\n'
                             '2. Email has no validation error if left empty.\n'
                             '3. Submit blocked when Mobile is empty.'},
        **{'Test Case Owner': 'QA-manual'}, Environment='SIT', Status='NA',
        **{'Comments/Remarks': MOBILE_NOTE},
    ),
    dict(
        tcid='SIT-TC-WEB-AUTH-124',
        Label='SIT/UAT',
        **{'Module/Feature': 'Guest-to-Member'},
        Priority='High', Severity='Medium',
        **{'Collected from': '2026-06-10 PRD §提交订单 (non-upgrade branch) — mobile variant of AUTH-108'},
        **{'Test Scenario': 'Submit + payment success WITHOUT opt-in (mobile branch) → no upgrade'},
        **{'Test Case Description': 'Verify the no-upgrade branch when the chosen contact is MOBILE: opt-in unchecked + payment success leaves the guest as a guest; no registered account is created; order is recorded under the guest temp account.'},
        Preconditions='Guest user on order page; contact method = Mobile; unregistered HK mobile; checkbox UNchecked.',
        **{'Test Steps': '1. Leave the opt-in UNCHECKED.\n'
                        '2. Submit the order; complete payment.\n'
                        '3. Inspect the user state in admin / DB.'},
        **{'Test Data': 'Guest; unregistered HK mobile.'},
        **{'Expected Result': '1. No account upgrade.\n'
                             '2. No registered account created.\n'
                             '3. Order recorded under guest temp account.'},
        **{'Test Case Owner': 'QA-manual'}, Environment='SIT', Status='NA',
        **{'Comments/Remarks': MOBILE_NOTE},
    ),
]

wb = openpyxl.load_workbook(XLSX)
ws = wb['Test Cases']
hdr = {str(ws.cell(1, c).value).split('\n')[0].strip(): c for c in range(1, ws.max_column+1) if ws.cell(1,c).value}
id_col = hdr['Test Case ID']
row_by_id = {ws.cell(rn, id_col).value: rn for rn in range(2, ws.max_row+1) if ws.cell(rn, id_col).value}
REF_ROW = row_by_id.get('SIT-TC-WEB-AUTH-088', 2)

# Modify
modified = 0
for tcid, fields in MODIFY.items():
    rn = row_by_id.get(tcid)
    if not rn:
        print(f'WARN: {tcid} not found'); continue
    for col_name, val in fields.items():
        c = hdr[col_name]
        ws.cell(rn, c).value = val
        ws.cell(rn, c).fill = YELLOW
        modified += 1

# Add
from openpyxl.styles import Font, Alignment
added = 0
for tc in ADD:
    rn = ws.max_row + 1
    # copy formatting from REF_ROW + force normalized format (Calibri 11, wrap, top, left)
    for c in range(1, ws.max_column + 1):
        ref = ws.cell(REF_ROW, c)
        new = ws.cell(rn, c)
        new.font = Font(name='Calibri', size=11)
        new.alignment = Alignment(wrap_text=True, vertical='top', horizontal='left')
        if ref.has_style:
            new.border = copy(ref.border)
            new.number_format = ref.number_format
    tcid = tc.pop('tcid')
    c = hdr['Test Case ID']
    ws.cell(rn, c).value = tcid
    ws.cell(rn, c).fill = YELLOW
    for col_name, val in tc.items():
        if val:
            c = hdr.get(col_name)
            if c:
                ws.cell(rn, c).value = val
                ws.cell(rn, c).fill = YELLOW
    # row height: use longest field for estimate
    longest_lines = max(
        (str(tc.get('Test Steps','')).count('\n') + sum(max(1, len(l)//50) for l in str(tc.get('Test Steps','')).split('\n'))),
        (str(tc.get('Expected Result','')).count('\n') + sum(max(1, len(l)//50) for l in str(tc.get('Expected Result','')).split('\n'))),
    )
    ws.row_dimensions[rn].height = max(150.0, longest_lines * 13.5 + 8)
    added += 1

wb.save(XLSX)
print(f'Modified {modified} cells across 7 existing TCs; added {added} new TCs (AUTH-118 ~ 124).')

# re-scan
import re
wb2 = openpyxl.load_workbook(XLSX, data_only=True)
ws2 = wb2['Test Cases']
pats = [re.compile(r'email\s*[/、／]\s*mobile', re.I), re.compile(r'email\s*[/、／]\s*phone', re.I),
        re.compile(r'邮箱\s*[/、／]\s*手机', re.I), re.compile(r'mobile\s*[/、／]\s*email', re.I),
        re.compile(r'\(or mobile\)', re.I), re.compile(r'Email\s*/\s*Mobile', re.I)]
print('\nRemaining combined cases:')
n_left = 0
for rn in range(2, ws2.max_row+1):
    tcid = ws2.cell(rn, id_col).value
    if not tcid: continue
    blob = ''
    for col in ['Test Scenario','Test Case Description','Preconditions','Test Steps','Test Data','Expected Result']:
        v = ws2.cell(rn, hdr[col]).value
        if v: blob += str(v) + ' || '
    hits = set()
    for p in pats:
        for m in p.finditer(blob): hits.add(m.group())
    if hits:
        n_left += 1
        print(f'  {tcid}: {hits}')
print(f'Total combined remaining: {n_left}')
