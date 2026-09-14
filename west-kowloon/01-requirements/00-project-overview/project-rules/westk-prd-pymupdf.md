---
rule_id: westk-prd-pymupdf
title: 用 PyMuPDF 不用 pdftotext 抽 CJK PRD 文本
scope: project-permanent
created: 2026-05-15
origin: pdftotext 抽 西九 PRD 中文全乱码 (2026-05-15)
applies_to: [西九]
candidate_for_promotion: no
promoted_to: null
promoted_at: null
---

## Rule

When extracting text from 西九 PRD PDFs (`国际版标准官网 *.pdf` under
`D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\01-source-documents\02-prd\2026-05-14\`),
**use Python PyMuPDF (`fitz`)**, not the standard `pdftotext` (Poppler)
command-line tool.

```python
import fitz
doc = fitz.open(path)
text = "\n".join(p.get_text() for p in doc)
```

## Why

`pdftotext` (Poppler) fails on these PRDs — the embedded fonts have
custom CJK glyph maps that Poppler can't decode to Unicode, so the
output is garbage / empty. PyMuPDF handles them correctly because it
implements the CFF font tables directly.

Installed once on 2026-05-15:
```
pip install pymupdf
```

## How to verify

Quick smoke:
```python
import fitz
doc = fitz.open(r"D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\01-source-documents\02-prd\2026-05-14\国际版标准官网 - 在线购票.pdf")
print(doc[0].get_text()[:200])
```

Should print readable Chinese (`第一章 …` / `## 业务概述` etc), not
boxes / question marks / empty string.

## Promotion candidate?

**No** — `scope: project-permanent`. The trick is real and generally
applies to ANY CJK PDF from CJK SaaS exporters, BUT:
- It's a one-line workaround, not a methodology
- Other projects' PDFs might come from different exporters with
  different font issues
- It belongs in a "tools notes" cheat-sheet rather than a system standard

If a second project independently hits the same issue, copy this rule
into their project-rules/ rather than promote (per `01-system/11-rule-promotion.md`).
