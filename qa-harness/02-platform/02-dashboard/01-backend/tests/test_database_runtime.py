import importlib
import sys
from datetime import datetime, timezone


def test_sqlite_runtime_and_interrupted_run_recovery(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard-test.db"
    monkeypatch.setenv("QA_DASHBOARD_DB_PATH", str(db_path))
    sys.modules.pop("database", None)
    database = importlib.import_module("database")

    try:
        database.init_db()
        db = database.SessionLocal()
        run = database.TestRun(
            started_at=datetime.now(timezone.utc).replace(tzinfo=None),
            status="running",
            project_key="west-kowloon",
            run_kind="full",
        )
        db.add(run)
        db.commit()
        run_id = run.id
        db.close()

        assert database.reconcile_interrupted_runs() == 1

        db = database.SessionLocal()
        recovered = db.query(database.TestRun).filter(database.TestRun.id == run_id).one()
        assert recovered.status == "interrupted"
        assert recovered.finished_at is not None
        db.close()

        with database.engine.connect() as conn:
            assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
            assert conn.exec_driver_sql("PRAGMA journal_mode").scalar().lower() == "wal"
            assert conn.exec_driver_sql("PRAGMA user_version").scalar() == database.DASHBOARD_SCHEMA_VERSION
            indexes = {
                row[1]
                for row in conn.exec_driver_sql("PRAGMA index_list('test_runs')").fetchall()
            }
            assert "ix_test_runs_project_kind_started" in indexes
    finally:
        database.engine.dispose()
        sys.modules.pop("database", None)
