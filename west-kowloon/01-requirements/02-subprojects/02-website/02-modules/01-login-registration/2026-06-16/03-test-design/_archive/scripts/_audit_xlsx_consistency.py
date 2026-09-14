"""Comprehensive xlsx audit: fonts, formatting consistency, and content issues.

Reports per category. Does NOT modify the xlsx — read-only audit.
"""
import openpyxl, io, sys, re
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

XLSX = 'test-cases-registration-login_2026-06-12.xlsx'
wb = openpyxl.load_workbook(XLSX)
ws = wb['Test Cases']
hdr = {str(ws.cell(1, c).value).split('\n')[0].strip(): c
       for c in range(1, ws.max_column+1) if ws.cell(1,c).value}
id_col = hdr['Test Case ID']

print(f'=== Workbook audit: {XLSX} ===')
print(f'Sheet: Test Cases | rows: {ws.max_row} | cols: {ws.max_column}')

# ---------------------------------------------------------------------------
# 1. Fonts (family + size) used in data rows
# ---------------------------------------------------------------------------
fonts = Counter()
sizes = Counter()
for rn in range(2, ws.max_row + 1):
    for c in range(1, ws.max_column + 1):
        cell = ws.cell(rn, c)
        if cell.font:
            fonts[cell.font.name] += 1
            sizes[cell.font.size] += 1
print('\n[1] Font families used in data cells:')
for f, n in fonts.most_common():
    print(f'    {f!r}: {n} cells')
print('[1] Font sizes used:')
for s, n in sizes.most_common():
    print(f'    {s}: {n} cells')

# ---------------------------------------------------------------------------
# 2. Header row font consistency
# ---------------------------------------------------------------------------
hdr_fonts = set()
for c in range(1, ws.max_column + 1):
    cell = ws.cell(1, c)
    if cell.font and cell.value:
        hdr_fonts.add((cell.font.name, cell.font.size, cell.font.bold))
print(f'\n[2] Header font signatures (name, size, bold): {hdr_fonts}')

# ---------------------------------------------------------------------------
# 3. Alignment & wrap_text
# ---------------------------------------------------------------------------
wrap_counts = Counter()
halign = Counter()
valign = Counter()
for rn in range(2, ws.max_row + 1):
    for c in range(1, ws.max_column + 1):
        cell = ws.cell(rn, c)
        if cell.alignment:
            wrap_counts[bool(cell.alignment.wrap_text)] += 1
            halign[cell.alignment.horizontal or '-'] += 1
            valign[cell.alignment.vertical or '-'] += 1
print('\n[3] wrap_text distribution:', dict(wrap_counts))
print('    horizontal:', dict(halign))
print('    vertical:', dict(valign))

# ---------------------------------------------------------------------------
# 4. Empty mandatory cells
# ---------------------------------------------------------------------------
MANDATORY = ['Test Case ID','Module/Feature','Priority','Severity','Test Scenario',
             'Test Case Description','Test Steps','Expected Result','Status']
empty_mand = []
for rn in range(2, ws.max_row + 1):
    tcid = ws.cell(rn, id_col).value
    if not tcid: continue
    for col_name in MANDATORY:
        if col_name in hdr:
            v = ws.cell(rn, hdr[col_name]).value
            if v is None or (isinstance(v, str) and not v.strip()):
                empty_mand.append((tcid, col_name))
print(f'\n[4] Empty mandatory cells: {len(empty_mand)}')
for tcid, col in empty_mand[:20]:
    print(f'    {tcid}.{col}')

# ---------------------------------------------------------------------------
# 5. Duplicate TC IDs
# ---------------------------------------------------------------------------
tcid_counter = Counter()
for rn in range(2, ws.max_row + 1):
    t = ws.cell(rn, id_col).value
    if t:
        tcid_counter[t] += 1
dups = [(k, v) for k, v in tcid_counter.items() if v > 1]
print(f'\n[5] Duplicate Test Case IDs: {len(dups)}')
for k, v in dups[:10]:
    print(f'    {k}: {v} occurrences')

# ---------------------------------------------------------------------------
# 6. Trailing whitespace / odd content
# ---------------------------------------------------------------------------
weird = []
for rn in range(2, ws.max_row + 1):
    tcid = ws.cell(rn, id_col).value
    for c in range(1, ws.max_column + 1):
        v = ws.cell(rn, c).value
        if isinstance(v, str):
            if v != v.rstrip() or v != v.strip():
                weird.append((tcid, list(hdr.keys())[c-1] if c-1 < len(hdr) else f'col{c}', 'whitespace'))
            if '  ' in v.replace('\n', ' '):
                pass  # tolerate double spaces
            if v.count('\r\n') or v.count('\r'):
                weird.append((tcid, list(hdr.keys())[c-1] if c-1 < len(hdr) else f'col{c}', 'CRLF/CR found'))
print(f'\n[6] Cells with trailing/leading whitespace or CR: {len(weird)}')
for tcid, col, kind in weird[:20]:
    print(f'    {tcid}.{col}: {kind}')

# ---------------------------------------------------------------------------
# 7. Step numbering format consistency
# ---------------------------------------------------------------------------
step_formats = Counter()
for rn in range(2, ws.max_row + 1):
    tcid = ws.cell(rn, id_col).value
    if not tcid: continue
    steps = ws.cell(rn, hdr['Test Steps']).value
    expected = ws.cell(rn, hdr['Expected Result']).value
    for blob in (steps, expected):
        if not blob or not isinstance(blob, str):
            continue
        for line in blob.split('\n'):
            line = line.strip()
            m = re.match(r'^(\d+)([\.\)、])', line)
            if m:
                step_formats[m.group(2)] += 1
print(f'\n[7] Step numbering separators: {dict(step_formats)}')

# ---------------------------------------------------------------------------
# 8. Status values
# ---------------------------------------------------------------------------
st = Counter()
for rn in range(2, ws.max_row + 1):
    v = ws.cell(rn, hdr['Status']).value
    if v: st[str(v).strip()] += 1
print(f'\n[8] Status values (should only be Pass/Fail/NA):')
for k, v in st.most_common():
    print(f'    {k!r}: {v}')

# ---------------------------------------------------------------------------
# 9. Row height summary
# ---------------------------------------------------------------------------
rh = []
for rn in range(2, ws.max_row + 1):
    h = ws.row_dimensions[rn].height
    rh.append(h or 0)
print(f'\n[9] Row heights: min={min(rh):.1f}, max={max(rh):.1f}, mean={sum(rh)/len(rh):.1f}')

# ---------------------------------------------------------------------------
# 10. Border consistency on data rows
# ---------------------------------------------------------------------------
border_styles = Counter()
for rn in range(2, ws.max_row + 1):
    for c in range(1, ws.max_column + 1):
        cell = ws.cell(rn, c)
        b = cell.border
        if b:
            sig = (
                b.left.style if b.left else None,
                b.right.style if b.right else None,
                b.top.style if b.top else None,
                b.bottom.style if b.bottom else None,
            )
            border_styles[sig] += 1
print(f'\n[10] Border style signatures: {len(border_styles)} distinct')
for sig, n in border_styles.most_common(5):
    print(f'    {sig}: {n} cells')

# ---------------------------------------------------------------------------
# 11. Cells with raw URLs or Python syntax leakage
# ---------------------------------------------------------------------------
leak_pat = re.compile(r'\*\*\{|NEW_TCS|dict\(|<class ')
leaks = []
for rn in range(2, ws.max_row + 1):
    tcid = ws.cell(rn, id_col).value
    for c in range(1, ws.max_column + 1):
        v = ws.cell(rn, c).value
        if isinstance(v, str) and leak_pat.search(v):
            leaks.append((tcid, list(hdr.keys())[c-1], v[:60]))
print(f'\n[11] Python syntax leak: {len(leaks)}')
for x in leaks: print('   ', x)

# ---------------------------------------------------------------------------
# 12. New TCs (088+): font / fill / alignment vs existing
# ---------------------------------------------------------------------------
print('\n[12] New TCs (088+) vs existing-row format spot-check:')
def fmt(cell):
    a = cell.alignment
    f = cell.font
    return (
        f.name if f else '-',
        f.size if f else '-',
        a.wrap_text if a else '-',
        a.horizontal if a else '-',
        a.vertical if a else '-',
    )
existing_fmt = fmt(ws.cell(2, hdr['Test Steps']))  # AUTH-001 Test Steps as the reference
new_diff = []
for rn in range(2, ws.max_row + 1):
    tcid = ws.cell(rn, id_col).value
    if not tcid or not tcid.startswith('SIT-TC-WEB-AUTH-'): continue
    num = int(tcid.split('-')[-1])
    if num < 88: continue
    sig = fmt(ws.cell(rn, hdr['Test Steps']))
    if sig != existing_fmt:
        new_diff.append((tcid, sig))
print(f'    Reference (AUTH-001 Test Steps): {existing_fmt}')
print(f'    New TC rows with different signature: {len(new_diff)}')
for tcid, sig in new_diff[:10]:
    print(f'      {tcid}: {sig}')
