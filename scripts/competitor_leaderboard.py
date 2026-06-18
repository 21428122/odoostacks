"""Competitor leaderboard — extract profitable Odoo publishers from local DuckDB.

Dedupes per-version snapshots to one row per (author, tech_name) using the latest
version's price * lifetime purchases as the per-app gross. Surfaces:
  1. Top 40 publishers by lifetime gross revenue (proxy: price * total_purchases)
  2. Top 40 publishers by last-month gross (still active)
  3. Top 60 individual apps by lifetime gross
  4. Per-publisher portfolio in user's target wedges
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

DB = Path(__file__).resolve().parent.parent / "data" / "odoo.duckdb"

# User's target wedges from memory: migration pickaxe + EU e-invoicing + India GST.
WEDGES = {
    "migration_quickbooks":  "lower(tech_name) LIKE '%quickbook%' OR lower(display_name) LIKE '%quickbook%'",
    "migration_tally":       "lower(tech_name) LIKE '%tally%' OR lower(display_name) LIKE '%tally%'",
    "migration_zoho":        "lower(tech_name) LIKE '%zoho%' OR lower(display_name) LIKE '%zoho%'",
    "migration_sage":        "lower(tech_name) LIKE '%sage%' OR lower(display_name) LIKE '%sage%'",
    "migration_datev":       "lower(tech_name) LIKE '%datev%' OR lower(display_name) LIKE '%datev%'",
    "migration_generic":     "(lower(tech_name) LIKE '%import%' OR lower(tech_name) LIKE '%migrat%' OR lower(display_name) LIKE '%migration%') AND price_cents > 0",
    "einvoice_eu":           "(lower(tech_name) LIKE '%einvoic%' OR lower(tech_name) LIKE '%e_invoic%' OR lower(tech_name) LIKE '%peppol%' OR lower(display_name) LIKE '%e-invoic%' OR lower(display_name) LIKE '%peppol%')",
    "einvoice_slovenia":     "lower(tech_name) LIKE '%slovenia%' OR lower(tech_name) LIKE '%eslog%' OR lower(display_name) LIKE '%slovenia%'",
    "einvoice_greece_mydata":"lower(tech_name) LIKE '%mydata%' OR lower(display_name) LIKE '%mydata%'",
    "india_gst":             "lower(tech_name) LIKE '%gst%' OR lower(display_name) LIKE '%gst%'",
    "india_einvoice":        "(lower(tech_name) LIKE '%irn%' OR lower(tech_name) LIKE '%e_invoice_india%' OR lower(display_name) LIKE '%e-invoice india%' OR lower(display_name) LIKE '%india e-invoice%')",
    "india_tds":             "lower(tech_name) LIKE '%tds%' OR lower(display_name) LIKE '%tds%'",
    "india_eway":            "lower(tech_name) LIKE '%eway%' OR lower(tech_name) LIKE '%e_way%' OR lower(display_name) LIKE '%e-way%' OR lower(display_name) LIKE '%eway%'",
    "whatsapp":              "lower(tech_name) LIKE '%whatsapp%' OR lower(display_name) LIKE '%whatsapp%'",
    "sop_documentation":     "lower(tech_name) LIKE '%sop%' OR lower(display_name) LIKE '%sop%' OR lower(tech_name) LIKE '%procedure%' OR lower(display_name) LIKE '%standard operating%'",
}


def latest_snapshot_per_app(con):
    """One row per app_key — the most recent snapshot."""
    con.execute("""
        CREATE OR REPLACE TEMP VIEW latest AS
        SELECT s.*, a.tech_name, a.version
        FROM app_snapshots s
        JOIN apps a ON a.app_key = s.app_key
        QUALIFY ROW_NUMBER() OVER (PARTITION BY s.app_key ORDER BY captured_at DESC) = 1
    """)


def latest_per_tech_name_per_author(con):
    """Dedupe across versions: keep highest-version row per (author, tech_name)."""
    con.execute("""
        CREATE OR REPLACE TEMP VIEW best_per_app AS
        SELECT *
        FROM latest
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY author, tech_name
            ORDER BY total_purchases DESC NULLS LAST, version DESC
        ) = 1
    """)


def top_publishers_by_lifetime_gross(con, n=40):
    return con.execute(f"""
        SELECT
            author,
            count(*) AS apps,
            sum(COALESCE(total_purchases, 0)) AS lifetime_sales,
            sum(COALESCE(last_month_purchases, 0)) AS lastmo_sales,
            sum(COALESCE(price_cents, 0) * COALESCE(total_purchases, 0)) / 100.0 AS lifetime_gross,
            sum(COALESCE(price_cents, 0) * COALESCE(last_month_purchases, 0)) / 100.0 AS lastmo_gross,
            avg(NULLIF(price_cents, 0)) / 100.0 AS avg_paid_price
        FROM best_per_app
        WHERE author IS NOT NULL AND author != ''
        GROUP BY author
        HAVING lifetime_gross > 0
        ORDER BY lifetime_gross DESC
        LIMIT {n}
    """).fetchall()


def top_publishers_by_lastmo_gross(con, n=40):
    return con.execute(f"""
        SELECT
            author,
            count(*) AS apps,
            sum(COALESCE(total_purchases, 0)) AS lifetime_sales,
            sum(COALESCE(last_month_purchases, 0)) AS lastmo_sales,
            sum(COALESCE(price_cents, 0) * COALESCE(last_month_purchases, 0)) / 100.0 AS lastmo_gross,
            sum(COALESCE(price_cents, 0) * COALESCE(total_purchases, 0)) / 100.0 AS lifetime_gross
        FROM best_per_app
        WHERE author IS NOT NULL AND author != ''
        GROUP BY author
        HAVING lastmo_gross > 0
        ORDER BY lastmo_gross DESC
        LIMIT {n}
    """).fetchall()


def top_apps_lifetime(con, n=60):
    return con.execute(f"""
        SELECT
            display_name, author, tech_name, version,
            COALESCE(price_cents, 0) / 100.0 AS price,
            COALESCE(total_purchases, 0) AS total,
            COALESCE(last_month_purchases, 0) AS lastmo,
            (COALESCE(price_cents, 0) * COALESCE(total_purchases, 0)) / 100.0 AS lifetime_gross,
            detail_url
        FROM best_per_app
        WHERE price_cents > 0 AND total_purchases > 0
        ORDER BY lifetime_gross DESC
        LIMIT {n}
    """).fetchall()


def wedge_breakdown(con):
    out = {}
    for name, where in WEDGES.items():
        rows = con.execute(f"""
            SELECT
                count(*) AS apps,
                count(DISTINCT author) AS publishers,
                sum(COALESCE(total_purchases, 0)) AS lifetime,
                sum(COALESCE(last_month_purchases, 0)) AS lastmo,
                sum(COALESCE(price_cents, 0) * COALESCE(total_purchases, 0)) / 100.0 AS lifetime_gross,
                sum(COALESCE(price_cents, 0) * COALESCE(last_month_purchases, 0)) / 100.0 AS lastmo_gross,
                quantile_cont(NULLIF(price_cents, 0), 0.5) / 100.0 AS median_paid_price
            FROM best_per_app
            WHERE {where}
        """).fetchone()
        leaders = con.execute(f"""
            SELECT
                display_name, author, tech_name, version,
                COALESCE(price_cents, 0) / 100.0 AS price,
                COALESCE(total_purchases, 0) AS total,
                COALESCE(last_month_purchases, 0) AS lastmo,
                (COALESCE(price_cents, 0) * COALESCE(total_purchases, 0)) / 100.0 AS lifetime_gross,
                detail_url
            FROM best_per_app
            WHERE ({where}) AND price_cents > 0
            ORDER BY lifetime_gross DESC NULLS LAST, total_purchases DESC NULLS LAST
            LIMIT 10
        """).fetchall()
        out[name] = {"summary": rows, "leaders": leaders}
    return out


def publisher_portfolio(con, author):
    return con.execute("""
        SELECT
            display_name, tech_name, version,
            COALESCE(price_cents, 0) / 100.0 AS price,
            COALESCE(total_purchases, 0) AS total,
            COALESCE(last_month_purchases, 0) AS lastmo,
            (COALESCE(price_cents, 0) * COALESCE(total_purchases, 0)) / 100.0 AS lifetime_gross
        FROM best_per_app
        WHERE author = ?
        ORDER BY lifetime_gross DESC NULLS LAST
        LIMIT 15
    """, [author]).fetchall()


def main():
    con = duckdb.connect(str(DB), read_only=True)
    latest_snapshot_per_app(con)
    latest_per_tech_name_per_author(con)

    result = {
        "top_by_lifetime_gross": top_publishers_by_lifetime_gross(con, n=40),
        "top_by_lastmo_gross":   top_publishers_by_lastmo_gross(con, n=40),
        "top_apps":              top_apps_lifetime(con, n=60),
        "wedges":                wedge_breakdown(con),
    }

    # Top 25 publishers — pull each portfolio so we can see what they actually sell.
    top_authors = [r[0] for r in result["top_by_lifetime_gross"][:25]]
    result["portfolios"] = {a: publisher_portfolio(con, a) for a in top_authors}

    Path("data/competitors").mkdir(parents=True, exist_ok=True)
    out_path = Path("data/competitors/leaderboard.json")
    out_path.write_text(json.dumps(result, default=str, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"\nTOP 15 BY LIFETIME GROSS:")
    for r in result["top_by_lifetime_gross"][:15]:
        print(f"  ${r[4]:>13,.0f}  apps={r[1]:>3}  lifetime_sales={r[2]:>6,}  lastmo=${r[5]:>10,.0f}  {r[0]}")
    print(f"\nTOP 15 BY LAST-MONTH GROSS:")
    for r in result["top_by_lastmo_gross"][:15]:
        print(f"  ${r[4]:>10,.0f}/mo  apps={r[1]:>3}  lastmo_sales={r[3]:>5,}  {r[0]}")
    print(f"\nWEDGE SUMMARY:")
    for name, w in result["wedges"].items():
        s = w["summary"]
        if s[0]:
            print(f"  {name:<24}  apps={s[0]:>4}  pubs={s[1]:>3}  lifetime=${s[4]:>11,.0f}  lastmo=${s[5]:>8,.0f}  med=${s[6] or 0:>5,.0f}")

    con.close()


if __name__ == "__main__":
    main()
