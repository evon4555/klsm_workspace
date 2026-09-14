# Input Index

## Requirement Package

- Project: West Kowloon Website
- Primary module: Ticketing
- Related modules: Homepage, Seat Selection
- Package: `2026-05-17`
- Previous package name: `2026-05-17-project-detail-ticketing`
- Canonical location:
  `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\03-ticketing\2026-05-17`

This package was originally named `2026-05-17-椤圭洰璇︽儏椤礰. It covers the event
detail page and ticket-purchase end-to-end flow.

## Source Files

### Figma

- `01-figma\figma-link.txt`

### Mindmap

Mindmap PNGs are authoritative for this package. Keep the original images
unchanged.

- `02-mindmap\001-椤圭洰璇︽儏椤电殑涓€浜岀骇鐩綍锛堣喘绁ㄦ湭灞曞紑锛?png`
- `02-mindmap\002-椤圭洰璇︽儏-璐エ灞曞紑椤?png`
- `02-mindmap\003-璐エ涓殑搴хエ灞曞紑椤?閫夋嫨鏃ユ湡.png`
- `02-mindmap\004-璐エ涓殑搴хエ灞曞紑椤?閫夋嫨搴т綅.png`
- `02-mindmap\005-璐エ涓殑搴хエ灞曞紑椤?璁㈠崟纭椤?png`
- `02-mindmap\006-璐エ涓殑搴хエ灞曞紑椤?浠樻.png`
- `02-mindmap\007-璐エ涓殑搴хエ灞曞紑椤?璁㈠崟璇︽儏椤?png`
- `02-mindmap\008-璐エ涓殑搴хエ灞曞紑椤?鍏朵粬.png`
- `02-mindmap\009-璐エ涓殑闂ㄧエ灞曞紑椤?閫夋嫨鏃ユ湡.png`
- `02-mindmap\010-璐エ涓殑闂ㄧエ灞曞紑椤?閫夋嫨闂ㄧエ.png`
- `02-mindmap\011-璐エ涓殑闂ㄧエ灞曞紑椤?璁㈠崟纭椤?png`
- `02-mindmap\012-璐エ涓殑闂ㄧエ灞曞紑椤?浠樻.png`
- `02-mindmap\013-璐エ涓殑闂ㄧエ灞曞紑椤?璁㈠崟璇︽儏椤?png`
- `02-mindmap\014-璐エ涓殑闂ㄧエ灞曞紑椤?鍏朵粬.png`

## Test Design Outputs

Use these numbered subfolders only:

- `..\03-test-design\01-homepage`
- `..\03-test-design\02-ticketing`
- `..\03-test-design\03-seat-selection`

Legacy aliases `homepage`, `闂ㄧエ`, and `搴хエ` were removed during the
2026-06-16 module migration.

## Scope Notes

- Homepage/event detail page cases live in `..\03-test-design\01-homepage`.
- Admission-ticket cases live in `..\03-test-design\02-ticketing`.
- Seat-selection-ticket cases live in `..\03-test-design\03-seat-selection`.
- Refund and reschedule logic can affect multiple ticket types; keep the
  concrete cases in the relevant numbered test-design folder.

## Website-Level Background

Rolling full-website PRD source documents live under:

```text
..\..\..\..\..\01-source-documents\02-prd
```

Use those files as background/reference. This package's working inputs are the
Figma and mindmap files listed above.

