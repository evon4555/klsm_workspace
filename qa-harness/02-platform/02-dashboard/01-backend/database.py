"""
SQLite database models for the Test Automation Dashboard.

Tables:
  test_runs      — one row per test execution (stores summary: total/passed/failed/skipped)
  test_scenarios — one row per scenario in a run (stores name, status, duration, error)

SQLAlchemy ORM is used so we work with Python objects instead of raw SQL.
The DB file (dashboard.db) is created automatically on first startup.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Store the DB file next to this script by default. Tests and isolated smoke
# runs can override it without touching the real dashboard history.
DB_PATH = Path(
    os.environ.get("QA_DASHBOARD_DB_PATH", Path(__file__).parent / "dashboard.db")
).resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"timeout": 30},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()

DASHBOARD_SCHEMA_VERSION = 3


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@event.listens_for(engine, "connect")
def _configure_sqlite(dbapi_connection, _connection_record):
    """Use safe local-dashboard defaults on every SQLite connection."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
    finally:
        cursor.close()


class TestRun(Base):
    """A single test execution. Created when the user clicks 'Run Tests'."""

    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running | passed | failed | error | interrupted
    env = Column(String(20), default="local")                       # local | sit | uat
    project_key = Column(String(100), nullable=False, default="west-kowloon", index=True)
    tags = Column(String(200), nullable=True)                       # e.g., "@hybrid,@antank"
    # full = normal suite/scope execution used by package status and quality
    # gates. Reruns are execution attempts for selected cases only and must
    # not replace the latest full-run summary.
    run_kind = Column(String(30), nullable=False, default="full", index=True)
    parent_run_id = Column(Integer, nullable=True, index=True)
    rerun_scope = Column(String(30), nullable=True)                  # failed | single
    source_scenario_id = Column(Integer, nullable=True)
    total = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    # "errored" counts scenarios that crashed before assertion (Playwright
    # timeout, undefined step, fixture exception) — kept separate from
    # `failed` (= assertion mismatch) so the dashboard distinguishes
    # "product bug" (failed) from "test/infra problem" (errored).
    errored = Column(Integer, default=0)
    skipped = Column(Integer, default=0)

    scenarios = relationship("TestScenario", back_populates="run", cascade="all, delete-orphan")


class TestScenario(Base):
    """One scenario result inside a test run."""

    __tablename__ = "test_scenarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    feature = Column(String(200), nullable=False)    # e.g., "Antank 项目管理"
    name = Column(String(200), nullable=False)        # e.g., "Admin creates a no-seat project..."
    status = Column(String(20), nullable=False)       # passed | failed | skipped | undefined
    duration_s = Column(Float, default=0.0)
    error_msg = Column(Text, nullable=True)
    tags = Column(String(200), nullable=True)          # e.g., "@hybrid,@antank"

    # Legacy single-bug fields (added 2026-05-23). Still present so the
    # initial multi-bug migration can copy from here; new writes go to
    # ScenarioBug instead. Safe to read NULL — code path no longer uses
    # these to make decisions.
    zentao_bug_id = Column(Integer, nullable=True)
    zentao_bug_url = Column(String(300), nullable=True)

    run = relationship("TestRun", back_populates="scenarios")
    bugs = relationship("ScenarioBug", back_populates="scenario",
                        cascade="all, delete-orphan")


class PerformanceRunConfig(Base):
    """Configuration and aggregate metrics for a Locust performance run."""

    __tablename__ = "performance_run_configs"

    run_id = Column(Integer, ForeignKey("test_runs.id"), primary_key=True)
    host = Column(String(500), nullable=False, default="")
    locustfile = Column(String(500), nullable=False, default="")
    mode = Column(String(100), nullable=False, default="")
    users = Column(Integer, default=0)
    spawn_rate = Column(Float, default=0.0)
    duration = Column(String(40), nullable=False, default="")
    artifact_prefix = Column(String(1000), nullable=True)
    total_requests = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    avg_response_time = Column(Float, default=0.0)
    rps = Column(Float, default=0.0)

    run = relationship("TestRun")


class ScenarioBug(Base):
    """A ZenTao bug opened from the dashboard for one scenario. A scenario
    can have multiple bugs (different defects in the same scenario, or
    follow-up bugs filed later) — they are deduped by exact title within
    the scenario so re-clicking 'Open Bug' with the default title returns
    the existing bug, but editing the title creates a new one."""

    __tablename__ = "scenario_bugs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("test_scenarios.id"), nullable=False)
    zentao_bug_id = Column(Integer, nullable=False)
    zentao_bug_url = Column(String(300), nullable=False)
    title = Column(String(300), nullable=False)            # used for dedup
    opened_at = Column(DateTime, default=lambda: __import__("datetime").datetime.utcnow())

    scenario = relationship("TestScenario", back_populates="bugs")


class ApiMonitorRun(Base):
    """One pytest api-smoke session. Appended each time latest.json changes."""

    __tablename__ = "api_monitor_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ran_at = Column(DateTime, nullable=False, index=True)
    project = Column(String(200), default="")
    website_url = Column(String(500), default="")
    total = Column(Integer, default=0)
    up = Column(Integer, default=0)
    degraded = Column(Integer, default=0)
    down = Column(Integer, default=0)
    skipped = Column(Integer, default=0)

    endpoints = relationship(
        "ApiMonitorEndpointResult",
        back_populates="run",
        cascade="all, delete-orphan",
    )


class ApiMonitorEndpointResult(Base):
    """Per-endpoint result inside one ApiMonitorRun."""

    __tablename__ = "api_monitor_endpoint_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("api_monitor_runs.id"), nullable=False, index=True)
    name = Column(String(300), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False)            # up | degraded | down | skipped
    actual_status_code = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    group = Column(String(100), nullable=True)
    auth_required = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    body_warning = Column(Text, nullable=True)

    run = relationship("ApiMonitorRun", back_populates="endpoints")


def init_db():
    """Create all tables if they don't exist yet (safe to call multiple times)."""
    Base.metadata.create_all(engine)
    # SQLite "migration" for the bug columns added 2026-05-23. CREATE TABLE
    # IF NOT EXISTS will not add new columns to an existing table, so we run
    # explicit ALTERs and swallow the "duplicate column" error.
    with engine.begin() as conn:
        for ddl in (
            "ALTER TABLE test_scenarios ADD COLUMN zentao_bug_id INTEGER",
            "ALTER TABLE test_scenarios ADD COLUMN zentao_bug_url VARCHAR(300)",
            # 2026-06-03: split 'errored' out of 'failed' in test_runs.
            "ALTER TABLE test_runs ADD COLUMN errored INTEGER DEFAULT 0",
            "ALTER TABLE test_runs ADD COLUMN project_key VARCHAR(100) DEFAULT 'west-kowloon'",
            "ALTER TABLE test_runs ADD COLUMN run_kind VARCHAR(30) DEFAULT 'full'",
            "ALTER TABLE test_runs ADD COLUMN parent_run_id INTEGER",
            "ALTER TABLE test_runs ADD COLUMN rerun_scope VARCHAR(30)",
            "ALTER TABLE test_runs ADD COLUMN source_scenario_id INTEGER",
        ):
            try:
                conn.execute(text(ddl))
            except Exception as exc:  # noqa: BLE001
                # SQLite raises OperationalError("duplicate column name") on re-run
                if "duplicate column" not in str(exc).lower():
                    raise
        conn.execute(text("""
            UPDATE test_runs
            SET project_key = 'west-kowloon'
            WHERE project_key IS NULL OR TRIM(project_key) = ''
        """))
        conn.execute(text("""
            UPDATE test_runs
            SET run_kind = 'full'
            WHERE run_kind IS NULL OR TRIM(run_kind) = ''
        """))
        # Conservative backfill for reruns created before run_kind existed:
        # a one-scenario run whose scenario had already appeared in an earlier
        # same-project run is almost certainly a dashboard single-case rerun.
        conn.execute(text("""
            UPDATE test_runs
            SET run_kind = 'rerun_single',
                rerun_scope = COALESCE(rerun_scope, 'single'),
                parent_run_id = COALESCE(parent_run_id, (
                    SELECT MAX(prior.id)
                    FROM test_runs AS prior
                    JOIN test_scenarios AS prior_s ON prior_s.run_id = prior.id
                    JOIN test_scenarios AS this_s ON this_s.run_id = test_runs.id
                    WHERE prior.id < test_runs.id
                      AND prior.project_key = test_runs.project_key
                      AND prior_s.name = this_s.name
                )),
                source_scenario_id = COALESCE(source_scenario_id, (
                    SELECT this_s.id
                    FROM test_scenarios AS this_s
                    WHERE this_s.run_id = test_runs.id
                    LIMIT 1
                ))
            WHERE run_kind = 'full'
              AND total = 1
              AND (
                SELECT COUNT(1)
                FROM test_scenarios AS only_s
                WHERE only_s.run_id = test_runs.id
              ) = 1
              AND EXISTS (
                SELECT 1
                FROM test_runs AS prior
                JOIN test_scenarios AS prior_s ON prior_s.run_id = prior.id
                JOIN test_scenarios AS this_s ON this_s.run_id = test_runs.id
                WHERE prior.id < test_runs.id
                  AND prior.project_key = test_runs.project_key
                  AND prior_s.name = this_s.name
              )
        """))
        # One-time backfill: copy existing single-bug rows from test_scenarios
        # into scenario_bugs so the multi-bug UI starts populated. Idempotent:
        # only copies if no row for that (scenario_id, zentao_bug_id) pair
        # exists yet.
        conn.execute(text("""
            INSERT INTO scenario_bugs (scenario_id, zentao_bug_id,
                                       zentao_bug_url, title, opened_at)
            SELECT ts.id, ts.zentao_bug_id, ts.zentao_bug_url,
                   '[Auto] ' || ts.name || ' (run #' || ts.run_id || ')',
                   CURRENT_TIMESTAMP
            FROM test_scenarios AS ts
            WHERE ts.zentao_bug_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM scenario_bugs AS sb
                WHERE sb.scenario_id = ts.id
                  AND sb.zentao_bug_id = ts.zentao_bug_id
              )
        """))
        # Explicit index creation is required for databases that predate the
        # indexed ORM columns. create_all() skips indexes when the table already
        # exists, which left older dashboard.db files without query indexes.
        for ddl in (
            "CREATE INDEX IF NOT EXISTS ix_test_runs_project_key ON test_runs (project_key)",
            "CREATE INDEX IF NOT EXISTS ix_test_runs_run_kind ON test_runs (run_kind)",
            "CREATE INDEX IF NOT EXISTS ix_test_runs_parent_run_id ON test_runs (parent_run_id)",
            "CREATE INDEX IF NOT EXISTS ix_test_runs_status ON test_runs (status)",
            "CREATE INDEX IF NOT EXISTS ix_test_runs_project_kind_started ON test_runs (project_key, run_kind, started_at)",
            "CREATE INDEX IF NOT EXISTS ix_test_scenarios_run_id ON test_scenarios (run_id)",
            "CREATE INDEX IF NOT EXISTS ix_scenario_bugs_scenario_id ON scenario_bugs (scenario_id)",
            "CREATE INDEX IF NOT EXISTS ix_performance_run_configs_run_id ON performance_run_configs (run_id)",
        ):
            conn.execute(text(ddl))
        conn.execute(text(f"PRAGMA user_version = {DASHBOARD_SCHEMA_VERSION}"))


def reconcile_interrupted_runs() -> int:
    """Close stale in-progress rows left behind by a stopped backend process."""
    db = SessionLocal()
    try:
        stale = db.query(TestRun).filter(TestRun.status == "running").all()
        if not stale:
            return 0
        finished_at = _utcnow_naive()
        for run in stale:
            run.status = "interrupted"
            run.finished_at = run.finished_at or finished_at
        db.commit()
        return len(stale)
    finally:
        db.close()


def get_db():
    """Return a new database session. Caller must call .close() when done."""
    return SessionLocal()
