"""Writeback ONLY the 4 PRD-changed Pass scenarios to xlsx (don't touch others).

Per user rule "没有变更的测试用例不用覆盖", we only update the 4 rows whose
test-case content was changed per 2026-06-10 PRD AND whose automation was
re-run on 2026-06-12.
"""
import openpyxl, io, sys, datetime
from openpyxl.drawing.image import Image as XLImage
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

XLSX = 'test-cases-registration-login_2026-06-12.xlsx'
TODAY = datetime.date.today().isoformat()
EXECUTOR = 'Auto+Evan'  # Auto run + manual verify per AUTH-001
SHOT_ROOT = Path(r'D:\Workspace\west-kowloon\02-automation\07-artifacts\screenshots')

UPDATES = {
    'SIT-TC-WEB-AUTH-001': {
        'env': 'SIT',
        'date': TODAY,
        'by': EXECUTOR,
        'actual': 'Page-open + form-fill OK; submit step rejected by SIT email-OTP backdoor (fixed 111111 removed 2026-05-23). Per-step gating (CAPTCHA->OTP->password focus-out) assertion pending page-object refactor.',
        'status': 'Pass',  # manually verified by QA owner per existing policy
        'comments': 'Pass via manual verification (kept per QA-owner decision). Script updated 2026-06-12 with PRD-2026-06-10 gated-flow annotation; gate-level assertion pending page-object refactor.',
        'screenshot_glob': 'registration_*/02_registration_form_filled.png',
    },
    'SIT-TC-WEB-AUTH-004': {
        'env': 'SIT',
        'date': TODAY,
        'by': 'Auto',
        'actual': 'DEFECT: SIT returns no error wording for duplicate email registration (empty error message). 2026-06-10 PRD requires the 3-language duplicate-email error string; product currently does not produce it.',
        'status': 'Fail',
        'comments': 'Updated 2026-06-12 per PRD-2026-06-10: now asserts 3-language wording. Product gap surfaced — needs dev follow-up.',
        'screenshot_glob': 'registration_*/02_duplicate_email_form_filled.png',
    },
    'SIT-TC-WEB-AUTH-010': {
        'env': 'SIT',
        'date': TODAY,
        'by': 'Auto',
        'actual': 'As expected. SIT returns "Incorrect username or password!" (PRD-compliant generic wording). No enumeration leak.',
        'status': 'Pass',
        'comments': 'Updated 2026-06-12 per PRD-2026-06-10: now asserts the generic wording AND screens for enumeration leaks (e.g., "not registered", "go register"). Both pass.',
        'screenshot_glob': None,  # behave run didn't save shot for login
    },
    'SIT-TC-WEB-AUTH-012': {
        'env': 'SIT',
        'date': TODAY,
        'by': 'Auto',
        'actual': 'As expected. SIT returns the SAME generic wording as AUTH-010 ("Incorrect username or password!") — no "go register" guidance.',
        'status': 'Pass',
        'comments': 'Updated 2026-06-12 per PRD-2026-06-10: shares assertion with AUTH-010; verifies unknown-account does NOT leak account state.',
        'screenshot_glob': None,
    },
}

wb = openpyxl.load_workbook(XLSX)
ws = wb['Test Cases']
hdr = {str(ws.cell(1, c).value).split('\n')[0].strip(): c for c in range(1, ws.max_column+1) if ws.cell(1,c).value}
id_col = hdr['Test Case ID']
COL_MAP = {
    'env':        hdr['Environment'],
    'date':       hdr['Execution Date'],
    'by':         hdr['Executed By'],
    'actual':     hdr['Actual Result'],
    'status':     hdr['Status'],
    'comments':   hdr['Comments/Remarks'],
}
SHOT_COL = hdr.get('Screenshots')

# Find rows
row_by_id = {ws.cell(rn, id_col).value: rn for rn in range(2, ws.max_row+1) if ws.cell(rn, id_col).value}

touched = []
for tcid, upd in UPDATES.items():
    rn = row_by_id.get(tcid)
    if not rn:
        print(f'WARN: {tcid} not found in xlsx')
        continue
    for field, c in COL_MAP.items():
        ws.cell(rn, c).value = upd[field]
    # Screenshot: embed if path resolvable
    if upd.get('screenshot_glob') and SHOT_COL:
        matches = sorted(SHOT_ROOT.glob(upd['screenshot_glob']))
        if matches:
            shot_path = matches[-1]  # latest
            try:
                img = XLImage(str(shot_path))
                # Fit to a reasonable cell width
                img.width = 360
                img.height = int(img.height * 360 / max(1, img.width))
                ws.cell(rn, SHOT_COL).value = ''
                ws.add_image(img, ws.cell(rn, SHOT_COL).coordinate)
                ws.row_dimensions[rn].height = max(ws.row_dimensions[rn].height or 0, 200)
                print(f'  {tcid}: embedded {shot_path.name}')
            except Exception as exc:
                print(f'  {tcid}: shot embed failed ({exc}); leaving cell as path')
                ws.cell(rn, SHOT_COL).value = f'See: {shot_path}'
        else:
            print(f'  {tcid}: no shot matched {upd["screenshot_glob"]}')
    touched.append(tcid)

wb.save(XLSX)
print(f'\nWriteback touched: {touched}')
print(f'Saved: {XLSX}')
