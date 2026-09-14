"""
Regenerate a test-cases-*.xlsx from its md source by cloning the project template.

Procedure (per project-context.md § Test Case Template):
  1. byte-clone template -> target
  2. capture row-2 sample styles per column
  3. clear sample row values, keep styles
  4. write each parsed data row with captured styles
  5. apply FFFFF2CC yellow fill to deferred-pending-product rows / cells
  6. apply FFFF0000 red font color to red-marked cells (e.g., Cybersource "needs confirm" items)

CLI usage:
  python regenerate_xlsx.py \
    --md   "<path>/test-cases-XXX.md" \
    --xlsx "<path>/test-cases-XXX.xlsx" \
    --prefix-regex "AUTH-(\\d{3})" \
    --row-pattern "^\\| SIT-TC-WEB-AUTH-" \
    --yellow-rows "046,047,064,065" \
    --yellow-cells '{"015":[11],"030":[11]}' \
    --red-cells '{"006":[11]}'
"""

import argparse
import shutil
import copy
import json
import re
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font

from _paths import westk_root
NUM_COLS = 20  # Was 19 before 2026-06-01; bumped to 20 when project added Label column (col 1) — see TestCase_Template_pre-label.xlsx for the historical 19-col version.
SAMPLE_ROW = 2

YELLOW = PatternFill(start_color='FFFFF2CC', end_color='FFFFF2CC', fill_type='solid')


def resolve_template(md_path: Path, explicit_template: str | None) -> Path:
    if explicit_template:
        template = Path(explicit_template)
        if template.exists():
            return template
        raise FileNotFoundError(f"template not found: {template}")

    for parent in [md_path.resolve().parent, *md_path.resolve().parents]:
        if parent.name == '01-requirements':
            template = parent / '01-source-documents' / '02-templates' / 'TestCase_Template.xlsx'
            if template.exists():
                return template
            break

    template = westk_root() / '01-requirements' / '01-source-documents' / '02-templates' / 'TestCase_Template.xlsx'
    if template.exists():
        return template
    raise FileNotFoundError(f"project test case template not found for {md_path}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--md', required=True)
    p.add_argument('--xlsx', required=True)
    p.add_argument('--template', default=None,
                   help='Optional explicit TestCase_Template.xlsx path. Defaults to the owning project 01-requirements/01-source-documents/02-templates template.')
    p.add_argument('--row-pattern', default=r'^\| (\*\*)?(SIT|UAT|NA|此功能|SIT/UAT|SIT-TC-)',
                   help="Regex line prefix that identifies a case row in the md table. Default allows either the new Label-first layout (SIT/SIT|UAT/NA/etc.) or the legacy Test Case ID-first layout (SIT-TC-).")
    p.add_argument('--prefix-regex', default=r'SIT-TC-[A-Z-]+-(\d{3}[a-z]?)',
                   help="Regex with one capture group that extracts the 3-digit (optionally trailing letter) case num from the case ID column.")
    p.add_argument('--yellow-rows', default='',
                   help="Comma-separated 3-digit case nums whose entire row is yellow.")
    p.add_argument('--yellow-cells', default='{}',
                   help='JSON {"NNN": [col, ...]} for cell-level yellow fills.')
    p.add_argument('--red-cells', default='{}',
                   help='JSON {"NNN": [col, ...]} for cell-level red font (e.g., Cybersource items).')
    return p.parse_args()


def main():
    args = parse_args()
    md_path = Path(args.md)
    xlsx_path = Path(args.xlsx)
    template_path = resolve_template(md_path, args.template)
    row_pat = re.compile(args.row_pattern)
    num_pat = re.compile(args.prefix_regex)
    yellow_rows = set(s.strip() for s in args.yellow_rows.split(',') if s.strip())
    yellow_cells = {k: list(v) for k, v in json.loads(args.yellow_cells).items()}
    red_cells = {k: list(v) for k, v in json.loads(args.red_cells).items()}

    # 1. Parse md table
    md_text = md_path.read_text(encoding='utf-8')
    data_rows = []
    for line in md_text.split('\n'):
        if row_pat.match(line):
            parts = [p.strip() for p in line.split('|')]
            parts = parts[1:-1]
            parts = [p.replace('<br>', '\n') for p in parts]
            while len(parts) < NUM_COLS:
                parts.append('')
            data_rows.append(parts[:NUM_COLS])

    print(f"Parsed {len(data_rows)} case rows from {md_path.name}")

    # 2. Clone template
    shutil.copy(template_path, xlsx_path)
    print(f"Cloned template {template_path} -> {xlsx_path.name}")

    # 3. Open + capture sample-row styles
    wb = load_workbook(xlsx_path)
    ws = wb.active
    col_styles = []
    for col in range(1, NUM_COLS + 1):
        c = ws.cell(row=SAMPLE_ROW, column=col)
        col_styles.append({
            'font': copy.copy(c.font),
            'fill': copy.copy(c.fill),
            'border': copy.copy(c.border),
            'alignment': copy.copy(c.alignment),
            'number_format': c.number_format,
            'protection': copy.copy(c.protection),
        })

    # 4. Clear existing data rows
    max_row = ws.max_row
    for r in range(SAMPLE_ROW, max_row + 1):
        for col in range(1, NUM_COLS + 1):
            ws.cell(row=r, column=col).value = None

    # 5. Write data rows
    for idx, row_data in enumerate(data_rows, start=SAMPLE_ROW):
        # Strip revise-marker bold (**...**) from every cell before writing.
        row_data = [re.sub(r'^\*\*(.*)\*\*$', r'\1', cell) for cell in row_data]
        # Test Case ID is at index 1 (Label is at 0 since 2026-06-01); fall back to index 0 for legacy 19-col md.
        case_id = row_data[1] if NUM_COLS >= 20 else row_data[0]
        m = num_pat.search(str(case_id))
        case_num = m.group(1) if m else None
        is_yellow_row = case_num in yellow_rows
        y_cells = set(yellow_cells.get(case_num, []))
        r_cells = set(red_cells.get(case_num, []))

        for col in range(1, NUM_COLS + 1):
            c = ws.cell(row=idx, column=col)
            c.value = row_data[col - 1] if row_data[col - 1] != '' else None
            style = col_styles[col - 1]
            c.font = copy.copy(style['font'])
            c.fill = copy.copy(style['fill'])
            c.border = copy.copy(style['border'])
            c.alignment = copy.copy(style['alignment'])
            c.number_format = style['number_format']
            c.protection = copy.copy(style['protection'])
            if is_yellow_row or col in y_cells:
                c.fill = copy.copy(YELLOW)
            if col in r_cells:
                # Preserve other font attributes, only change color
                base = c.font
                c.font = Font(name=base.name, size=base.size, bold=base.bold,
                              italic=base.italic, color='FFFF0000')

    wb.save(xlsx_path)
    print(f"Saved {xlsx_path.name} ({len(data_rows)} rows)")


if __name__ == '__main__':
    main()
