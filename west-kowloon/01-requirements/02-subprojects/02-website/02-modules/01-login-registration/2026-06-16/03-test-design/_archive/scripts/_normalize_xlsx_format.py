"""Normalize xlsx formatting issues found by _audit_xlsx_consistency.py:
  1. Normalize all data-cell fonts to Calibri 11 (Windows auto-CJK-fallbacks).
  2. Set row heights for the 31 new TCs (AUTH-088~117) so multi-line content shows.
  3. Strip trailing whitespace from cell values.
  4. Normalize alignment to wrap_text=True + top + left for all data cells.
"""
import openpyxl, io, sys
from copy import copy
from openpyxl.styles import Font, Alignment, PatternFill
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

XLSX = 'test-cases-registration-login_2026-06-12.xlsx'
wb = openpyxl.load_workbook(XLSX)
ws = wb['Test Cases']
hdr = {str(ws.cell(1, c).value).split('\n')[0].strip(): c
       for c in range(1, ws.max_column+1) if ws.cell(1,c).value}
id_col = hdr['Test Case ID']

# ---------------------------------------------------------------------------
# 1. Font normalization: every data cell -> Calibri 11
#    Preserve bold/italic/color/etc. flags.
# ---------------------------------------------------------------------------
font_fixed = 0
for rn in range(2, ws.max_row + 1):
    for c in range(1, ws.max_column + 1):
        cell = ws.cell(rn, c)
        if cell.font and cell.font.name != 'Calibri':
            new_font = Font(
                name='Calibri',
                size=cell.font.size or 11,
                bold=cell.font.bold,
                italic=cell.font.italic,
                color=cell.font.color,
                underline=cell.font.underline,
                strike=cell.font.strike,
            )
            cell.font = new_font
            font_fixed += 1
print(f'1. Font normalization: {font_fixed} cells -> Calibri 11')

# ---------------------------------------------------------------------------
# 2. Row height for new TC rows (AUTH-088~117) — set based on longest cell content
#    Use the Test Steps + Expected Result heuristic: max(150, ~7pt per line).
# ---------------------------------------------------------------------------
height_fixed = 0
for rn in range(2, ws.max_row + 1):
    tcid = ws.cell(rn, id_col).value
    if not tcid or not tcid.startswith('SIT-TC-WEB-AUTH-'):
        continue
    num = int(tcid.split('-')[-1])
    if num < 88:
        continue  # existing rows already have heights set
    cur = ws.row_dimensions[rn].height
    if cur and cur >= 50:
        continue
    # Estimate lines needed for longest text field (assume ~50 chars per visible line)
    longest_lines = 0
    for col in ['Test Steps', 'Expected Result', 'Test Case Description']:
        v = ws.cell(rn, hdr[col]).value
        if not v: continue
        # count actual newlines + estimate wrap
        nl = str(v).count('\n')
        # wrap estimate: divide longest non-newline run by 50
        wrap = sum(max(1, len(line) // 50) for line in str(v).split('\n'))
        longest_lines = max(longest_lines, nl + wrap)
    # 1 line ≈ 13.5 pt with default settings; add 8pt padding
    target = max(150.0, longest_lines * 13.5 + 8)
    ws.row_dimensions[rn].height = target
    height_fixed += 1
print(f'2. Row heights set for new TC rows: {height_fixed}')

# ---------------------------------------------------------------------------
# 3. Strip trailing whitespace
# ---------------------------------------------------------------------------
trim_fixed = 0
for rn in range(2, ws.max_row + 1):
    for c in range(1, ws.max_column + 1):
        v = ws.cell(rn, c).value
        if isinstance(v, str):
            stripped = v.rstrip()
            if stripped != v:
                ws.cell(rn, c).value = stripped
                trim_fixed += 1
print(f'3. Cells trimmed: {trim_fixed}')

# ---------------------------------------------------------------------------
# 4. Alignment normalization: wrap_text=True, vertical=top, horizontal=left
#    Skip cells already set this way; only fix anomalies.
# ---------------------------------------------------------------------------
align_fixed = 0
for rn in range(2, ws.max_row + 1):
    for c in range(1, ws.max_column + 1):
        cell = ws.cell(rn, c)
        a = cell.alignment
        if not a or not a.wrap_text or a.vertical != 'top':
            cell.alignment = Alignment(
                wrap_text=True,
                vertical='top',
                horizontal=a.horizontal if (a and a.horizontal) else 'left',
                text_rotation=a.text_rotation if a else 0,
                indent=a.indent if a else 0,
            )
            align_fixed += 1
print(f'4. Alignment normalized: {align_fixed} cells')

wb.save(XLSX)
print('\nSaved.')

# ---------------------------------------------------------------------------
# Re-audit
# ---------------------------------------------------------------------------
from collections import Counter
wb2 = openpyxl.load_workbook(XLSX)
ws2 = wb2['Test Cases']
fonts = Counter()
none_h = 0
wt = Counter()
for rn in range(2, ws2.max_row + 1):
    if not ws2.row_dimensions[rn].height:
        none_h += 1
    for c in range(1, ws2.max_column + 1):
        cell = ws2.cell(rn, c)
        if cell.font:
            fonts[cell.font.name] += 1
        if cell.alignment:
            wt[bool(cell.alignment.wrap_text)] += 1
print(f'\n--- Re-audit ---')
print(f'Fonts: {dict(fonts)}')
print(f'Row heights = None: {none_h}')
print(f'wrap_text: {dict(wt)}')
