import json
from pathlib import Path

import pytest

from project_catalog import ProjectCatalog, ProjectCatalogError


def _write_config(path: Path, projects: list[dict], default: str = "alpha") -> None:
    path.write_text(
        json.dumps({"version": 1, "defaultProject": default, "projects": projects}),
        encoding="utf-8",
    )


def test_catalog_resolves_aliases_and_project_paths(tmp_path):
    config = tmp_path / "projects.json"
    _write_config(config, [
        {
            "key": "alpha",
            "name": "Alpha Project",
            "kind": "customer",
            "workspace": "alpha-workspace",
            "aliases": ["A"],
            "zentaoProductId": 1,
        }
    ])
    (tmp_path / "alpha-workspace" / "02-automation").mkdir(parents=True)

    catalog = ProjectCatalog(tmp_path, tmp_path / "qa-harness", config)

    assert catalog.key("A") == "alpha"
    assert catalog.project_root("Alpha Project") == (tmp_path / "alpha-workspace").resolve()
    assert catalog.paths("alpha")["automation_root"] == (
        tmp_path / "alpha-workspace" / "02-automation"
    ).resolve()


def test_catalog_rejects_workspace_escape(tmp_path):
    config = tmp_path / "projects.json"
    _write_config(config, [
        {
            "key": "alpha",
            "name": "Alpha Project",
            "workspace": "../outside",
        }
    ])

    with pytest.raises(ProjectCatalogError, match="workspace-relative"):
        ProjectCatalog(tmp_path, tmp_path / "qa-harness", config)
