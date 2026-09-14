from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

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
_ENV_NAME = os.getenv("ENV", "local")
load_dotenv(_PROJECT_ROOT / "06-envs" / f".env.{_ENV_NAME}", override=False)
_USERS_FILE = _PROJECT_ROOT / "05-config" / "users.yml"
_ENV_VAR_RE = re.compile(r"^\$\{([A-Z_][A-Z0-9_]*)\}$")


@dataclass(frozen=True)
class User:
    username: str
    password: str
    role: str
    name: str  # e.g. "user1"
    env: str   # e.g. "sit"


@lru_cache(maxsize=1)
def _load_users_file() -> dict:
    with open(_USERS_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _expand(value: str, field: str, user_name: str, env: str) -> str:
    """If value is a ${ENV_VAR} placeholder, substitute from os.environ.

    Plain strings (no placeholder) pass through unchanged. This lets users.yml
    stay in git with no plaintext secrets, while real values live in
    envs/.env.<env> (loaded by python-dotenv via Settings).
    """
    if not isinstance(value, str):
        return value
    m = _ENV_VAR_RE.match(value.strip())
    if not m:
        return value
    var = m.group(1)
    real = os.environ.get(var)
    if real is None or real == "":
        raise KeyError(
            f"users.yml references {value!r} for {env}.{user_name}.{field}, "
            f"but environment variable {var} is not set. "
            f"Add it to envs/.env.{env} (see envs/.env.example)."
        )
    return real


def get_user(name: str, env: str) -> User:
    """Return a User for the given name and environment.

    Example:
        get_user("user1", "sit")  →  User(username="sit_alice@...", role="admin")
    """
    data = _load_users_file()
    if env not in data:
        raise KeyError(f"Environment '{env}' not found in users.yml")
    if name not in data[env]:
        raise KeyError(f"User '{name}' not found under env '{env}' in users.yml")
    entry = data[env][name]
    return User(
        username=_expand(entry["username"], "username", name, env),
        password=_expand(entry["password"], "password", name, env),
        role=entry["role"],
        name=name,
        env=env,
    )
