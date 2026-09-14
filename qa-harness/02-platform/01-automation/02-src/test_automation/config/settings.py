from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic import HttpUrl
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

# Resolve which .env file to load based on ENV= environment variable.
# e.g. ENV=sit  →  envs/.env.sit
# Falls back to envs/.env.local if ENV is not set.
def _project_automation_root() -> Path:
    override = os.getenv("QA_PROJECT_AUTOMATION_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    westk = os.getenv("QA_WESTK_ROOT")
    if westk:
        return (Path(westk).expanduser() / "02-automation").resolve()
    workspace = Path(os.getenv("QA_WORKSPACE_ROOT", "D:/Workspace")).expanduser()
    return (workspace / "west-kowloon" / "02-automation").resolve()


_PROJECT_ROOT = _project_automation_root()
_env_name = os.getenv("ENV", "local")
_env_file = _PROJECT_ROOT / "06-envs" / f".env.{_env_name}"

# Push the .env file into os.environ so callers (e.g. users.py's ${VAR}
# placeholder expansion) can read it via os.environ. pydantic-settings only
# loads .env into its own Settings model, not into the process environment.
load_dotenv(_env_file, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TA_",
        env_file=str(_env_file),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="local")
    base_url: HttpUrl = Field(default="https://httpbin.org")
    # Historical West Kowloon adapter field. Keep the name until page objects
    # and project tools are migrated to a generic project_url/target_url alias.
    antank_url: str = Field(default="https://anticket.lengliwh.com")
    artifacts_dir: str = Field(default=str(_PROJECT_ROOT / "07-artifacts"))


class SettingsError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        raise SettingsError(str(e)) from e
