from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


CASE_ID_RE = re.compile(r"\b(SIT-TC-[A-Z0-9-]+-\d{3,})\b", re.IGNORECASE)
SUITE = "batch_session_configuration"
SCHEMA = "case-screenshot-manifest/v1"


def case_id_from_text(text: object) -> str | None:
    match = CASE_ID_RE.search(str(text or ""))
    return match.group(1).upper() if match else None


def automation_root() -> Path:
    return Path(os.environ.get("QA_PROJECT_AUTOMATION_ROOT", "D:/Workspace/standard product/02-automation"))


def artifact_root() -> Path:
    return automation_root() / "07-artifacts" / SUITE


def effective_run_id(context: Any) -> str:
    env_run_id = os.environ.get("BEHAVE_DASHBOARD_RUN_ID")
    if env_run_id:
        return env_run_id
    context_run_id = getattr(context, "_dashboard_run_id", None)
    if context_run_id:
        return str(context_run_id)
    return "manual"


def current_case_id(context: Any) -> str | None:
    case_id = getattr(context, "_current_case_id", None)
    if case_id:
        return str(case_id).upper()
    scenario = getattr(context, "scenario", None)
    return case_id_from_text(getattr(scenario, "name", ""))


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _manifest_paths(context: Any) -> tuple[Path, Path]:
    root = artifact_root()
    run_id = effective_run_id(context)
    return (
        root / f"case-screenshot-manifest-run-{run_id}.json",
        root / "case-screenshot-manifest-latest.json",
    )


def _read_manifest(path: Path, run_id: str) -> dict[str, Any]:
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("cases", {})
                return data
        except Exception:
            pass
    return {
        "schema": SCHEMA,
        "project": os.environ.get("QA_PROJECT_KEY", "standard product"),
        "suite": SUITE,
        "run_id": run_id,
        "artifact_root": str(artifact_root()).replace("\\", "/"),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "cases": {},
    }


def _write_manifest(context: Any, manifest: dict[str, Any]) -> None:
    run_path, latest_path = _manifest_paths(context)
    run_path.parent.mkdir(parents=True, exist_ok=True)
    manifest["updated_at"] = _now_iso()
    payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    run_path.write_text(payload, encoding="utf-8")
    latest_path.write_text(payload, encoding="utf-8")


def _case_entry(manifest: dict[str, Any], case_id: str, context: Any) -> dict[str, Any]:
    scenario = getattr(context, "scenario", None)
    feature = getattr(scenario, "feature", None)
    case = manifest.setdefault("cases", {}).setdefault(case_id, {})
    case.setdefault("case_id", case_id)
    case.setdefault("screenshots", [])
    if scenario:
        case["scenario"] = getattr(scenario, "name", "")
        case["feature"] = getattr(feature, "name", "") if feature else ""
        case["tags"] = sorted(str(tag) for tag in getattr(scenario, "effective_tags", []) or [])
    return case


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    return re.sub(r"-{2,}", "-", text).strip("-") or "screenshot"


def record_case_status(context: Any, scenario: Any) -> None:
    case_id = current_case_id(context) or case_id_from_text(getattr(scenario, "name", ""))
    if not case_id:
        return
    run_id = effective_run_id(context)
    run_path, _latest_path = _manifest_paths(context)
    manifest = _read_manifest(run_path, run_id)
    case = _case_entry(manifest, case_id, context)
    status = getattr(getattr(scenario, "status", None), "name", None) or str(getattr(scenario, "status", ""))
    case["status"] = status
    case["finished_at"] = _now_iso()
    _write_manifest(context, manifest)


def save_case_screenshot(context: Any, ui: Any, label: str, legacy_name: str | None = None) -> Path:
    case_id = current_case_id(context)
    if not case_id:
        raise AssertionError("Cannot save case screenshot because no SIT-TC case ID is active.")
    run_id = effective_run_id(context)
    index = int(getattr(context, "_evidence_screenshot_index", 0)) + 1
    context._evidence_screenshot_index = index

    slug = _slug(label)
    root = artifact_root()
    case_dir = root / f"run-{run_id}" / case_id
    path = case_dir / f"{index:02d}-{slug}.png"
    ui.screenshot(path)

    legacy_path = None
    if legacy_name:
        legacy_path = root / legacy_name
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, legacy_path)

    run_path, _latest_path = _manifest_paths(context)
    manifest = _read_manifest(run_path, run_id)
    case = _case_entry(manifest, case_id, context)
    rel = path.relative_to(root).as_posix()
    screenshots = case.setdefault("screenshots", [])
    screenshots.append({
        "label": label,
        "path": str(path).replace("\\", "/"),
        "relative_path": rel,
        "legacy_path": str(legacy_path).replace("\\", "/") if legacy_path else None,
        "captured_at": _now_iso(),
    })
    case["has_screenshot"] = True
    _write_manifest(context, manifest)
    return path


def save_api_evidence_screenshot(
    context: Any,
    evidence: dict[str, Any],
    label: str = "api-readback-evidence",
) -> Path:
    case_id = current_case_id(context)
    if not case_id:
        raise AssertionError("Cannot save API evidence because no SIT-TC case ID is active.")
    run_id = effective_run_id(context)
    index = int(getattr(context, "_evidence_screenshot_index", 0)) + 1
    context._evidence_screenshot_index = index

    slug = _slug(label)
    root = artifact_root()
    case_dir = root / f"run-{run_id}" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    path = case_dir / f"{index:02d}-{slug}.png"
    json_path = case_dir / f"{index:02d}-{slug}.json"

    payload = {
        **evidence,
        "case_id": case_id,
        "run_id": run_id,
        "captured_at": _now_iso(),
        "evidence_kind": "api-readback-assertion",
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _render_api_evidence_png(payload, path)

    run_path, _latest_path = _manifest_paths(context)
    manifest = _read_manifest(run_path, run_id)
    case = _case_entry(manifest, case_id, context)
    rel = path.relative_to(root).as_posix()
    json_rel = json_path.relative_to(root).as_posix()
    screenshots = case.setdefault("screenshots", [])
    record = {
        "label": label,
        "kind": "api-evidence",
        "path": str(path).replace("\\", "/"),
        "relative_path": rel,
        "evidence_json": str(json_path).replace("\\", "/"),
        "evidence_json_relative_path": json_rel,
        "assertion": payload.get("assertion"),
        "captured_at": payload["captured_at"],
    }
    screenshots.append(record)
    case.setdefault("api_evidence", []).append(record)
    case["has_screenshot"] = True
    case["has_api_evidence"] = True
    _write_manifest(context, manifest)
    return path


def _font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = []
    if mono:
        names.extend(["C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf"])
    elif bold:
        names.extend(["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"])
    else:
        names.extend(["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"])
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_api_evidence_png(evidence: dict[str, Any], path: Path) -> None:
    observations = evidence.get("observations") or []
    readback_requests = evidence.get("readback_requests") or []
    setup_requests = evidence.get("setup_requests") or []
    height = max(960, 670 + len(observations) * 74 + len(setup_requests) * 52 + len(readback_requests) * 52)
    width = 1500
    margin = 42
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)

    title_font = _font(32, bold=True)
    h_font = _font(20, bold=True)
    normal = _font(18)
    small = _font(15)
    mono = _font(15, mono=True)

    y = margin
    draw.text((margin, y), "API Readback Evidence", font=title_font, fill="#111827")
    badge = evidence.get("assertion", {}).get("result", "UNKNOWN")
    badge_fill = "#0f766e" if badge == "PASS" else "#b91c1c"
    draw.rounded_rectangle((1220, y, 1428, y + 42), radius=8, fill=badge_fill)
    draw.text((1262, y + 8), badge, font=h_font, fill="#ffffff")
    y += 54

    scenario = str(evidence.get("scenario") or "")
    y = _draw_wrapped(draw, scenario, margin, y, width - margin * 2, normal, "#374151", 26)
    y += 18

    summary = [
        ("Case ID", evidence.get("case_id")),
        ("Run ID", evidence.get("run_id")),
        ("Flow", evidence.get("flow_key")),
        ("Target Field", evidence.get("expected_field")),
        ("Expected Value", evidence.get("expected_value")),
        ("Captured At", evidence.get("captured_at")),
    ]
    y = _draw_kv_block(draw, summary, margin, y, normal, mono)
    y += 20

    if setup_requests:
        y = _draw_section_title(draw, "Precondition API", margin, y, h_font)
        for idx, request in enumerate(setup_requests, start=1):
            response = request.get("response_summary") or {}
            line = (
                f"{idx}. {request.get('method', '')} {request.get('path', '')} "
                f"status={request.get('status_code', 'N/A')} success={response.get('success', 'N/A')} "
                f"params={_short_json(request.get('params') or {}, 220)}"
            )
            y = _draw_wrapped(draw, line, margin, y, width - margin * 2, mono, "#111827", 22)
        y += 18

    y = _draw_section_title(draw, "Write API", margin, y, h_font)
    write = evidence.get("write_request") or {}
    write_response = evidence.get("write_response") or {}
    write_lines = [
        f"{write.get('method', '')} {write.get('path', '')}",
        f"Params: {_short_json(write.get('params') or {}, 240)}",
        f"HTTP status: {write_response.get('status_code', 'N/A')}  success: {write_response.get('success', 'N/A')}",
    ]
    for line in write_lines:
        y = _draw_wrapped(draw, line, margin, y, width - margin * 2, mono, "#111827", 22)
    y += 18

    y = _draw_section_title(draw, "Readback Assertion", margin, y, h_font)
    y = _draw_observation_table(draw, observations, margin, y, width - margin * 2, small, mono)
    y += 18

    if readback_requests:
        y = _draw_section_title(draw, "Readback API", margin, y, h_font)
        for idx, request in enumerate(readback_requests, start=1):
            line = (
                f"{idx}. {request.get('method', '')} {request.get('path', '')} "
                f"status={request.get('status_code', 'N/A')} "
                f"params={_short_json(request.get('params') or {}, 220)}"
            )
            y = _draw_wrapped(draw, line, margin, y, width - margin * 2, mono, "#111827", 22)

    footer = (
        "PASS is written only after the setup readback differs from the target, "
        "the write API is accepted, and the post-write readback changes to the target value."
    )
    y = height - 58
    draw.line((margin, y - 14, width - margin, y - 14), fill="#e5e7eb", width=1)
    _draw_wrapped(draw, footer, margin, y, width - margin * 2, small, "#4b5563", 20)
    img.save(path)


def _draw_section_title(
    draw: ImageDraw.ImageDraw,
    title: str,
    x: int,
    y: int,
    font: ImageFont.ImageFont,
) -> int:
    draw.text((x, y), title, font=font, fill="#111827")
    return y + 30


def _draw_kv_block(
    draw: ImageDraw.ImageDraw,
    rows: list[tuple[str, Any]],
    x: int,
    y: int,
    label_font: ImageFont.ImageFont,
    value_font: ImageFont.ImageFont,
) -> int:
    for label, value in rows:
        draw.text((x, y), f"{label}:", font=label_font, fill="#374151")
        draw.text((x + 190, y), str(value or ""), font=value_font, fill="#111827")
        y += 28
    return y


def _draw_observation_table(
    draw: ImageDraw.ImageDraw,
    observations: list[dict[str, Any]],
    x: int,
    y: int,
    width: int,
    header_font: ImageFont.ImageFont,
    cell_font: ImageFont.ImageFont,
) -> int:
    col_widths = [170, 180, 270, 160, 270, 110, 110]
    headers = ["Selected ID", "Field", "Before", "Expected", "After", "Changed", "Result"]
    row_h = 44
    draw.rectangle((x, y, x + width, y + row_h), fill="#f3f4f6", outline="#d1d5db")
    cx = x
    for header, col_w in zip(headers, col_widths, strict=False):
        draw.text((cx + 10, y + 13), header, font=header_font, fill="#111827")
        cx += col_w
    y += row_h

    for item in observations:
        before = item.get("before_value", "")
        after = item.get("actual_value", "")
        changed = item.get("changed_from_before")
        row_passed = (
            bool(item.get("passed"))
            and item.get("before_matched_target") is False
            and changed is True
        )
        result = "PASS" if row_passed else "FAIL"
        values = [
            item.get("selected_id", ""),
            item.get("field", ""),
            before,
            item.get("expected_value", ""),
            after,
            "Y" if changed is True else "N" if changed is False else "?",
            result,
        ]
        fill = "#ffffff" if result == "PASS" else "#fff1f0"
        draw.rectangle((x, y, x + width, y + row_h), fill=fill, outline="#e5e7eb")
        cx = x
        for value, col_w in zip(values, col_widths, strict=False):
            color = "#166534" if value == "PASS" else "#991b1b" if value == "FAIL" else "#111827"
            draw.text((cx + 10, y + 13), _short_text(value, 34), font=cell_font, fill=color)
            cx += col_w
        y += row_h
    return y


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width: int,
    font: ImageFont.ImageFont,
    fill: str,
    line_height: int,
) -> int:
    for line in _wrap_text(draw, str(text or ""), font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split(" ") or [""]
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        if _text_width(draw, word, font) <= max_width:
            current = word
        else:
            chunk = ""
            for ch in word:
                candidate = chunk + ch
                if _text_width(draw, candidate, font) <= max_width:
                    chunk = candidate
                else:
                    if chunk:
                        lines.append(chunk)
                    chunk = ch
            current = chunk
    if current:
        lines.append(current)
    return lines or [""]


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    left, _top, right, _bottom = draw.textbbox((0, 0), text, font=font)
    return right - left


def _short_json(value: Any, limit: int) -> str:
    return _short_text(json.dumps(value, ensure_ascii=False, sort_keys=True), limit)


def _short_text(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."
