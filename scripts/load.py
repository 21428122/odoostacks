"""Load JSON snapshots produced by scrape_odoo.py into DuckDB.

Usage:
    python scripts/load.py                       # load latest run
    python scripts/load.py --run-dir data/snapshots/2026-05-08/<run_id>
    python scripts/load.py --all                 # re-load every run on disk
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console

from . import db as dbmod

console = Console()

SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "data" / "snapshots"


def _latest_run_dir() -> Path | None:
    if not SNAPSHOTS_DIR.exists():
        return None
    candidates: list[Path] = []
    for day_dir in sorted(SNAPSHOTS_DIR.iterdir()):
        if not day_dir.is_dir():
            continue
        for run_dir in sorted(day_dir.iterdir()):
            if (run_dir / "run.json").exists():
                candidates.append(run_dir)
    return candidates[-1] if candidates else None


def _all_run_dirs() -> list[Path]:
    if not SNAPSHOTS_DIR.exists():
        return []
    runs = []
    for day_dir in sorted(SNAPSHOTS_DIR.iterdir()):
        if not day_dir.is_dir():
            continue
        for run_dir in sorted(day_dir.iterdir()):
            if (run_dir / "run.json").exists():
                runs.append(run_dir)
    return runs


def load_run(run_dir: Path) -> tuple[int, int]:
    """Insert one run + its app snapshots into DuckDB. Idempotent on run_id."""
    run_meta = json.loads((run_dir / "run.json").read_text("utf-8"))

    run_id = run_meta["run_id"]
    started_at = datetime.fromisoformat(run_meta["started_at"])
    finished_at = (
        datetime.fromisoformat(run_meta["finished_at"])
        if run_meta.get("finished_at")
        else None
    )
    apps_path = (run_dir / "apps.json").as_posix()

    con = dbmod.connect()
    try:
        dbmod.init_schema(con)
        con.execute("BEGIN")

        # Idempotent reload: drop previous rows for this run before re-inserting.
        con.execute("DELETE FROM app_snapshots WHERE run_id = ?", [run_id])
        con.execute("DELETE FROM scrape_runs   WHERE run_id = ?", [run_id])

        con.execute(
            """
            INSERT INTO scrape_runs
                (run_id, started_at, finished_at, page_count, app_count, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                run_id,
                started_at,
                finished_at,
                run_meta.get("pages_scraped"),
                run_meta.get("total_cards"),
                None,
            ],
        )

        # Stage apps.json into a CTE-style temp view, then INSERT … SELECT into both
        # tables. This pushes the 67k-row scan into DuckDB's C++ JSON reader instead
        # of round-tripping every row through Python parameter binding.
        # DuckDB's `read_json_auto` can't accept a parameter-bound path, so the path
        # is embedded as a SQL string literal. Single quotes are escaped to prevent
        # injection via filesystem path.
        safe_path = apps_path.replace("'", "''")
        con.execute(
            f"CREATE OR REPLACE TEMP VIEW _stage AS "
            f"SELECT * FROM read_json_auto('{safe_path}', format='array')"
        )
        # In-JSON dedup: keep only the first card per (version, tech_name) inside this run.
        con.execute(
            """
            CREATE OR REPLACE TEMP VIEW _stage_unique AS
            SELECT *
            FROM (
                SELECT *,
                    row_number() OVER (PARTITION BY version, tech_name ORDER BY tech_name) AS _rn
                FROM _stage
                WHERE tech_name IS NOT NULL AND version IS NOT NULL
            )
            WHERE _rn = 1
            """
        )

        con.execute(
            """
            INSERT INTO apps (app_key, tech_name, version, first_seen, last_seen)
            SELECT
                version || '/' || tech_name,
                tech_name,
                version,
                CAST(? AS TIMESTAMP),
                CAST(? AS TIMESTAMP)
            FROM _stage_unique
            ON CONFLICT (app_key) DO UPDATE SET last_seen = excluded.last_seen
            """,
            [started_at, started_at],
        )

        next_snapshot_id = (
            con.execute("SELECT coalesce(max(snapshot_id), 0) FROM app_snapshots").fetchone()[0]
            or 0
        )

        con.execute(
            """
            INSERT INTO app_snapshots (
                snapshot_id, run_id, app_key, captured_at,
                display_name, summary, author, price_cents, currency,
                rating_stars, review_count,
                total_purchases, last_month_purchases,
                image_url, detail_url
            )
            SELECT
                CAST(? AS BIGINT) + row_number() OVER ()       AS snapshot_id,
                CAST(? AS VARCHAR)                              AS run_id,
                version || '/' || tech_name                     AS app_key,
                CAST(? AS TIMESTAMP)                            AS captured_at,
                display_name, summary, author, price_cents, currency,
                rating_stars, review_count,
                total_purchases, last_month_purchases,
                image_url, detail_url
            FROM _stage_unique
            """,
            [next_snapshot_id, run_id, started_at],
        )

        apps_count = con.execute(
            "SELECT count(*) FROM _stage_unique"
        ).fetchone()[0]
        con.execute("COMMIT")
        return apps_count, apps_count
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()


@click.command()
@click.option(
    "--run-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Specific run directory to load. Defaults to the latest one on disk.",
)
@click.option("--all", "load_all", is_flag=True, help="Reload every run on disk.")
def main(run_dir: Path | None, load_all: bool) -> None:
    """Load scraped JSON into DuckDB."""
    if load_all:
        runs = _all_run_dirs()
        if not runs:
            console.print("[red]No runs found on disk.[/red]")
            return
        for r in runs:
            apps_n, snaps_n = load_run(r)
            console.print(f"  loaded {r.name}: {apps_n} apps, {snaps_n} snapshots")
        console.print(f"[green]done — {len(runs)} runs loaded[/green]")
        return

    target = run_dir or _latest_run_dir()
    if target is None:
        console.print("[red]No runs found on disk. Run scrape_odoo.py first.[/red]")
        return

    apps_n, snaps_n = load_run(target)
    console.print(f"[green]loaded[/green] {target}")
    console.print(f"  {apps_n} apps, {snaps_n} snapshots")
    console.print(dbmod.db_info())


if __name__ == "__main__":
    main()
