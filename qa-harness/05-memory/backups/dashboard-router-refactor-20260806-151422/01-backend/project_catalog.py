"""Visible, validated project profiles for the QA Dashboard platform."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


class ProjectCatalogError(ValueError):
    """Raised when the project profile file or a requested project is invalid."""


class ProjectCatalog:
    def __init__(self, workspace_root: Path, harness_root: Path, config_path: Path):
        self.workspace_root = workspace_root.resolve()
        self.harness_root = harness_root.resolve()
        self.config_path = config_path.resolve()
        payload = self._load_payload()
        self.version = int(payload.get("version") or 1)
        self.default_project = str(payload.get("defaultProject") or "").strip()
        self._projects = self._validate_projects(payload.get("projects"))
        self._by_alias = self._build_alias_index(self._projects)
        if self.default_project not in {item["key"] for item in self._projects}:
            raise ProjectCatalogError(
                f"defaultProject {self.default_project!r} is not present in {self.config_path}"
            )

    @property
    def projects(self) -> list[dict]:
        return deepcopy(self._projects)

    def _load_payload(self) -> dict:
        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ProjectCatalogError(f"project config not found: {self.config_path}") from exc
        except json.JSONDecodeError as exc:
            raise ProjectCatalogError(f"invalid project config JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ProjectCatalogError("project config root must be an object")
        return payload

    @staticmethod
    def _relative_workspace_path(value: object, field: str) -> str:
        text = str(value or "").strip().replace("\\", "/")
        path = Path(text)
        if not text or path.is_absolute() or ".." in path.parts:
            raise ProjectCatalogError(f"{field} must be a safe workspace-relative path: {text!r}")
        return text

    def _validate_projects(self, raw_projects: object) -> list[dict]:
        if not isinstance(raw_projects, list) or not raw_projects:
            raise ProjectCatalogError("projects must be a non-empty list")

        projects: list[dict] = []
        seen_keys: set[str] = set()
        seen_workspaces: set[str] = set()
        for raw in raw_projects:
            if not isinstance(raw, dict):
                raise ProjectCatalogError("each project profile must be an object")
            item = dict(raw)
            key = str(item.get("key") or "").strip()
            name = str(item.get("name") or "").strip()
            workspace = self._relative_workspace_path(item.get("workspace"), "workspace")
            if not key or not name:
                raise ProjectCatalogError("each project requires non-empty key and name")
            if key in seen_keys:
                raise ProjectCatalogError(f"duplicate project key: {key}")
            if workspace.lower() in seen_workspaces:
                raise ProjectCatalogError(f"duplicate project workspace: {workspace}")
            seen_keys.add(key)
            seen_workspaces.add(workspace.lower())

            aliases = item.get("aliases") or []
            if not isinstance(aliases, list):
                raise ProjectCatalogError(f"aliases for {key} must be a list")
            item.update({
                "key": key,
                "name": name,
                "kind": str(item.get("kind") or "project").strip(),
                "workspace": workspace,
                "aliases": [str(alias).strip() for alias in aliases if str(alias).strip()],
            })
            if item.get("automationFallback"):
                item["automationFallback"] = self._relative_workspace_path(
                    item["automationFallback"], "automationFallback"
                )
            projects.append(item)
        return projects

    @staticmethod
    def _build_alias_index(projects: list[dict]) -> dict[str, dict]:
        index: dict[str, dict] = {}
        for item in projects:
            values = {
                item["key"],
                item["name"],
                item["workspace"],
                *item.get("aliases", []),
            }
            for value in values:
                normalized = str(value).strip().casefold()
                if normalized:
                    index[normalized] = item
        return index

    def config(self, project: str | None) -> dict:
        requested = str(project or self.default_project).strip().casefold()
        item = self._by_alias.get(requested)
        if item is None:
            raise ProjectCatalogError(f"unknown project: {project or self.default_project}")
        return deepcopy(item)

    def key(self, project: str | None) -> str:
        return self.config(project)["key"]

    def match_values(self, project: str | None) -> set[str]:
        item = self.config(project)
        return {
            value
            for value in {
                item["key"], item["workspace"], item["name"], *item.get("aliases", [])
            }
            if value
        }

    def project_root(self, project: str | None) -> Path:
        return (self.workspace_root / self.config(project)["workspace"]).resolve()

    def automation_root(self, project: str | None) -> Path:
        item = self.config(project)
        project_automation = self.project_root(item["key"]) / "02-automation"
        if project_automation.exists():
            return project_automation
        fallback = item.get("automationFallback")
        if fallback:
            return (self.workspace_root / fallback).resolve()
        return project_automation

    def paths(self, project: str | None) -> dict[str, Path | str]:
        item = self.config(project)
        project_root = self.project_root(item["key"])
        automation_root = self.automation_root(item["key"])
        return {
            "project_key": item["key"],
            "workspace_root": project_root,
            "automation_root": automation_root,
            "features_root": automation_root / "01-features",
            "tests_root": automation_root / "02-tests",
            "tools_root": automation_root / "04-tools",
            "artifacts_root": automation_root / "07-artifacts",
            "evidence_root": project_root / "03-evidence",
        }
