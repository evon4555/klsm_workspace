"""
Root pytest conftest — shared fixtures for API and app tests.

NOTE: BDD web tests (Behave) do NOT use this file.
      Behave uses features/environment.py for its lifecycle hooks instead.

Fixture scopes:
  session  → created once for the whole test run (expensive objects like settings)
  function → created fresh for every test (default, safest for stateful objects)
"""

from __future__ import annotations

import pytest

from test_automation.logging import configure_logging
from test_automation.config import get_settings, get_user, User


# Load the pytest_plugin which writes artifacts/summary.json at the end of a run.
pytest_plugins = ["test_automation.pytest_plugin"]


@pytest.fixture(scope="session", autouse=True)
def _configure_logging() -> None:
    """Set up loguru logging once per session. autouse=True means it runs automatically."""
    configure_logging()


@pytest.fixture(scope="session")
def env() -> str:
    """Current environment name: local | sit | uat.
    Controlled by the ENV environment variable (defaults to 'local').
    Example: ENV=sit pytest tests/"""
    return get_settings().env


@pytest.fixture
def user1(env: str) -> User:
    """Admin user credentials for the current environment (from config/users.yml)."""
    return get_user("user1", env)


@pytest.fixture
def user2(env: str) -> User:
    """Editor user credentials for the current environment."""
    return get_user("user2", env)


@pytest.fixture
def user3(env: str) -> User:
    """Viewer user credentials for the current environment."""
    return get_user("user3", env)


@pytest.fixture(params=["user1", "user2", "user3"])
def any_user(request, env: str) -> User:
    """Parametrized fixture — runs the test once per user role (admin, editor, viewer).
    Use this when you want to verify a test passes for ALL users at once."""
    return get_user(request.param, env)
