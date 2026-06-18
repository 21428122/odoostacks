"""DuckDB helpers for OdooStack.

Single source of truth for the local DB schema. Other scripts import `connect()`
and `init_schema()` from here.
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb

# Override with `export ODOOSTACK_DB_PATH=/some/where/odoo.duckdb` if your default
# data/ directory lives on a filesystem that can't unlink the DuckDB WAL
# (e.g. some network mounts).
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "odoo.duckdb"
DB_PATH = Path(os.environ.get("ODOOSTACK_DB_PATH") or DEFAULT_DB_PATH)


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open the DuckDB file. Creates the parent directory if missing."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH), read_only=read_only)


SCHEMA_SQL = """
-- Every scrape run gets a row here so we can correlate snapshots and reproduce.
CREATE TABLE IF NOT EXISTS scrape_runs (
    run_id      VARCHAR PRIMARY KEY,
    started_at  TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    page_count  INTEGER,
    app_count   INTEGER,
    note        VARCHAR
);

-- Master list of unique apps (technical name + version is the natural key).
CREATE TABLE IF NOT EXISTS apps (
    app_key     VARCHAR PRIMARY KEY,
    tech_name   VARCHAR NOT NULL,
    version     VARCHAR NOT NULL,
    first_seen  TIMESTAMP NOT NULL,
    last_seen   TIMESTAMP NOT NULL
);

-- Per-run snapshot of scraped fields. This is where velocity is measured.
CREATE TABLE IF NOT EXISTS app_snapshots (
    snapshot_id          BIGINT PRIMARY KEY,
    run_id               VARCHAR NOT NULL,
    app_key              VARCHAR NOT NULL,
    captured_at          TIMESTAMP NOT NULL,
    display_name         VARCHAR,
    summary              VARCHAR,
    author               VARCHAR,
    price_cents          BIGINT,
    currency             VARCHAR,
    rating_stars         DOUBLE,
    review_count         BIGINT,
    total_purchases      BIGINT,
    last_month_purchases BIGINT,
    image_url            VARCHAR,
    detail_url           VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_snapshots_app
    ON app_snapshots(app_key, captured_at);

CREATE INDEX IF NOT EXISTS idx_snapshots_run
    ON app_snapshots(run_id);
"""


_INT32_TO_BIGINT = (
    "price_cents",
    "review_count",
    "total_purchases",
    "last_month_purchases",
)


def init_schema(con: duckdb.DuckDBPyConnection | None = None) -> None:
    """Create tables if they don't exist; migrate INT32 → BIGINT. Idempotent."""
    own = con is None
    if own:
        con = connect()
    try:
        # Detect a stale schema with INT32 columns that overflow on real Odoo data
        # (some apps have price_cents > 2^31). Drop and recreate — the snapshot
        # JSONs on disk are the source of truth, so any prior load can be redone
        # by re-running odoostack-load.
        cols = con.execute(
            "SELECT column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_name = 'app_snapshots'"
        ).fetchall()
        col_types = {name: dtype for name, dtype in cols}
        if any(col_types.get(col) == "INTEGER" for col in _INT32_TO_BIGINT):
            con.execute("DROP INDEX IF EXISTS idx_snapshots_app")
            con.execute("DROP INDEX IF EXISTS idx_snapshots_run")
            con.execute("DROP TABLE IF EXISTS app_snapshots")
        con.execute(SCHEMA_SQL)
    finally:
        if own:
            con.close()


def db_info() -> str:
    """Lightweight summary used by /odoo-help and ad-hoc checks."""
    con = connect(read_only=True)
    try:
        runs = con.execute("SELECT count(*) FROM scrape_runs").fetchone()[0]
        apps = con.execute("SELECT count(*) FROM apps").fetchone()[0]
        snaps = con.execute("SELECT count(*) FROM app_snapshots").fetchone()[0]
        latest = con.execute(
            "SELECT max(captured_at) FROM app_snapshots"
        ).fetchone()[0]
    finally:
        con.close()
    return f"runs={runs}  apps={apps}  snapshots={snaps}  latest={latest}"


if __name__ == "__main__":
    init_schema()
    print(f"DB initialized at {DB_PATH}")
    print(db_info())
