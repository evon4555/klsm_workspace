"""smoke_docs.py - structural integrity check for the qa-harness doc tree.

Runs without network or services. It checks:
  1. Key numbered L1/L2 directories have a README or CLAUDE file.
  2. The repo root has CLAUDE.md.
  3. Markdown links resolve.
  4. Markdown files inside 01-system are discoverable.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

SKIP = {
    ".venv",
    "node_modules",
    "__pycache__",
    ".git",
    "claude-import",
    ".pytest_cache",
    "allure-results",
    "site-packages",
    "dist",
    "data",
    "07-artifacts",
    "06-artifacts",
    # Recovery copies keep links relative to their original directories and
    # are not active documentation surfaces.
    "backups",
}

results: list[tuple[str, bool, str]] = []


def is_skipped(path: Path) -> bool:
    return bool(set(path.parts) & SKIP)


def _looks_like_numbered_root(path: Path) -> bool:
    return (
        (path / "01-system").is_dir()
        and (path / "02-platform" / "01-automation").is_dir()
        and (path / "02-platform" / "02-dashboard").is_dir()
    )


def _candidate_roots() -> list[Path]:
    starts = [
        Path.cwd().absolute(),
        Path.cwd().resolve(),
        Path(__file__).absolute(),
        Path(__file__).resolve(),
    ]
    candidates: list[Path] = []
    for start in starts:
        candidates.append(start)
        candidates.extend(start.parents)
    return candidates


def find_repo_root() -> Path:
    override = os.getenv("QA_HARNESS_ROOT")
    if override:
        return Path(override).expanduser().resolve()

    for candidate in _candidate_roots():
        if _looks_like_numbered_root(candidate):
            return candidate.resolve()

    raise RuntimeError("Cannot locate qa-harness numbered root")


REPO_ROOT = find_repo_root()


def display_path(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def check(name: str, passed: bool, detail: str = "") -> None:
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {name}" + (f"  ({detail})" if detail else ""))
    results.append((name, passed, detail))


def has_entry_doc(path: Path) -> bool:
    return any((path / name).exists() for name in ("README.md", "CLAUDE.md"))


def phase_subdir_readmes() -> None:
    print("\n=== Phase 1: every L1/L2 functional dir has README/CLAUDE ===")
    l1_targets = [
        REPO_ROOT / "01-system",
        REPO_ROOT / "02-platform" / "01-automation",
        REPO_ROOT / "02-platform" / "02-dashboard",
        REPO_ROOT / "02-platform" / "03-infra",
        REPO_ROOT / "03-context",
        REPO_ROOT / "04-docs",
        REPO_ROOT / "05-memory",
    ]
    for path in l1_targets:
        if path.exists():
            check(f"L1: {display_path(path)}/ has README", has_entry_doc(path))

    l2_targets = [
        REPO_ROOT / "01-system" / "03-tools",
        REPO_ROOT / "01-system" / "01-skills",
        REPO_ROOT / "01-system" / "02-templates",
        REPO_ROOT / "02-platform" / "01-automation" / "03-tools",
        REPO_ROOT / "02-platform" / "02-dashboard" / "01-backend",
        REPO_ROOT / "02-platform" / "02-dashboard" / "02-frontend",
    ]
    for path in l2_targets:
        if path.exists():
            check(f"L2: {display_path(path)}/ has README", has_entry_doc(path))


def phase_root_claude() -> None:
    print("\n=== Phase 2: root CLAUDE.md present ===")
    check("CLAUDE.md at repo root", (REPO_ROOT / "CLAUDE.md").exists())


def phase_link_integrity() -> None:
    print("\n=== Phase 3: markdown link integrity ===")
    markdown_files = [path for path in REPO_ROOT.rglob("*.md") if not is_skipped(path)]
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    broken: list[str] = []
    for markdown in markdown_files:
        try:
            text = markdown.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in link_re.finditer(text):
            target = match.group(2).split("#")[0].split("?")[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (markdown.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"{display_path(markdown)} -> {target}")
    detail = f"{len(broken)} broken; first={broken[0] if broken else ''}"
    check("all md links resolve", len(broken) == 0, detail)


def phase_orphan_watch() -> None:
    print("\n=== Phase 4: 01-system content is discoverable ===")
    system_root = REPO_ROOT / "01-system"
    if not system_root.exists():
        check("01-system tree exists", False)
        return

    system_markdown = [path for path in system_root.rglob("*.md") if not is_skipped(path)]
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    referenced: set[Path] = set()
    for markdown in system_markdown:
        try:
            text = markdown.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in link_re.finditer(text):
            target = match.group(2).split("#")[0].split("?")[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            try:
                referenced.add((markdown.parent / target).resolve())
            except Exception:
                pass

    allowed = {"README.md", "TODO.md", "SKILL.md"}
    orphans = [
        display_path(path)
        for path in system_markdown
        if path.name not in allowed and path.resolve() not in referenced
    ]
    detail = f"{len(orphans)} orphans; first={orphans[0] if orphans else ''}"
    check("no orphan 01-system md", len(orphans) == 0, detail)


def main() -> int:
    print(f"qa-harness doc smoke - {REPO_ROOT}")
    phase_subdir_readmes()
    phase_root_claude()
    phase_link_integrity()
    phase_orphan_watch()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    failed = total - passed
    print("\n" + "=" * 60)
    if failed == 0:
        print(f"SUMMARY: PASS - {passed}/{total} checks")
    else:
        print(f"SUMMARY: FAIL - {failed}/{total} checks failed")
        for name, ok, detail in results:
            if not ok:
                print(f"  - {name}  ({detail})")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
