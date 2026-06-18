"""Planning stats: every number that matters when picking a niche to build.

Pulls market sizing, pricing, sales velocity, publisher concentration,
India-specific position, and per-niche signals from the local DuckDB.
No LLM. Reproducible — re-run after each scrape to track changes.

Usage:
    python -m scripts.planning_stats
    python -m scripts.planning_stats --output briefs/india-market/planning-stats.md
"""
from __future__ import annotations

from pathlib import Path

import click

from . import db as dbmod


# Indian Odoo partners cross-reference (from briefs/india-market/all-partners.md)
INDIA_PARTNER_KEYWORDS = [
    "browseinfo", "ksolves", "webkul", "softhealer", "cybrosys",
    "almighty", "closyss", "serpent", "emipro", "oodu", "techultra",
    "teckzilla", "caret it", "navabrind", "mindphin", "candidroot",
    "tatvamasi", "globalteckz", "kanak infosys", "edge technologies",
    "geminate", "probuse", "geo technosoft", "technaureus", "laxicon",
    "pragmatic techsoft", "synodica", "evozard", "primacy infotech",
    "highshine", "steigend", "apagen", "kavi software", "ahex",
    "links4engg", "namah softech", "broadtech", "nioses", "agbe",
    "finable consulting", "linescripts", "pinnacle seven", "guruebs",
    "beyondata", "cloudscience", "qwy software", "techmatic", "insoft",
    "warlock technologies", "prixgen", "technogeo",
]


def section(title: str) -> str:
    return f"\n\n## {title}\n"


def fmt_money(cents) -> str:
    if cents is None or cents == 0:
        return "Free"
    return f"${cents / 100:,.0f}"


def main_stats(con) -> dict:
    """Top-level market sizing."""
    out = {}
    out["total_apps"] = con.execute("SELECT count(*) FROM app_snapshots").fetchone()[0]
    out["paid_apps"] = con.execute(
        "SELECT count(*) FROM app_snapshots WHERE price_cents > 0"
    ).fetchone()[0]
    out["free_apps"] = out["total_apps"] - out["paid_apps"]
    out["distinct_publishers"] = con.execute(
        "SELECT count(DISTINCT author) FROM app_snapshots WHERE author IS NOT NULL"
    ).fetchone()[0]
    out["paid_publishers"] = con.execute(
        "SELECT count(DISTINCT author) FROM app_snapshots WHERE price_cents > 0"
    ).fetchone()[0]
    out["v19_apps"] = con.execute(
        "SELECT count(*) FROM app_snapshots s JOIN apps a ON a.app_key = s.app_key "
        "WHERE a.version = '19.0'"
    ).fetchone()[0]
    out["apps_with_sales_last_mo"] = con.execute(
        "SELECT count(*) FROM app_snapshots WHERE last_month_purchases > 0"
    ).fetchone()[0]
    out["apps_zero_lifetime_sales"] = con.execute(
        "SELECT count(*) FROM app_snapshots WHERE total_purchases = 0 OR total_purchases IS NULL"
    ).fetchone()[0]
    return out


def price_distribution(con) -> list[tuple[str, str]]:
    """Percentile price for paid apps."""
    rows = con.execute("""
        SELECT
            quantile_cont(price_cents, 0.10),
            quantile_cont(price_cents, 0.25),
            quantile_cont(price_cents, 0.50),
            quantile_cont(price_cents, 0.75),
            quantile_cont(price_cents, 0.90),
            quantile_cont(price_cents, 0.95),
            quantile_cont(price_cents, 0.99),
            avg(price_cents)
        FROM app_snapshots WHERE price_cents > 0
    """).fetchone()
    labels = ["p10", "p25", "median", "p75", "p90", "p95", "p99", "mean"]
    return [(labels[i], fmt_money(rows[i])) for i in range(8)]


def sales_velocity_buckets(con) -> list[tuple[str, int, str]]:
    """How many apps move 0 / 1 / 2-5 / 6-20 / 21+ sales last month?"""
    buckets = [
        ("0/mo (dead)", "last_month_purchases = 0 OR last_month_purchases IS NULL"),
        ("1/mo", "last_month_purchases = 1"),
        ("2-5/mo", "last_month_purchases BETWEEN 2 AND 5"),
        ("6-20/mo (busy)", "last_month_purchases BETWEEN 6 AND 20"),
        ("21+/mo (hot)", "last_month_purchases > 20"),
    ]
    out = []
    total = con.execute("SELECT count(*) FROM app_snapshots").fetchone()[0]
    for label, where in buckets:
        n = con.execute(f"SELECT count(*) FROM app_snapshots WHERE {where}").fetchone()[0]
        out.append((label, n, f"{n/total*100:.1f}%"))
    return out


def lifetime_buckets(con) -> list[tuple[str, int, str]]:
    """Lifetime sales distribution."""
    buckets = [
        ("0 lifetime", "total_purchases = 0 OR total_purchases IS NULL"),
        ("1-9 lifetime", "total_purchases BETWEEN 1 AND 9"),
        ("10-49 lifetime", "total_purchases BETWEEN 10 AND 49"),
        ("50-199 lifetime", "total_purchases BETWEEN 50 AND 199"),
        ("200-999 lifetime", "total_purchases BETWEEN 200 AND 999"),
        ("1000+ lifetime (hits)", "total_purchases >= 1000"),
    ]
    out = []
    total = con.execute("SELECT count(*) FROM app_snapshots").fetchone()[0]
    for label, where in buckets:
        n = con.execute(f"SELECT count(*) FROM app_snapshots WHERE {where}").fetchone()[0]
        out.append((label, n, f"{n/total*100:.1f}%"))
    return out


def top_publishers_by_apps(con, n: int = 20) -> list:
    """Largest portfolios."""
    return con.execute(f"""
        SELECT
            author,
            count(*) AS app_count,
            sum(COALESCE(last_month_purchases, 0)) AS sales_last_mo,
            sum(COALESCE(total_purchases, 0)) AS sales_total,
            sum(COALESCE(price_cents, 0) * COALESCE(last_month_purchases, 0)) / 100.0 AS gross_last_mo
        FROM app_snapshots
        WHERE author IS NOT NULL
        GROUP BY author
        ORDER BY app_count DESC
        LIMIT {n}
    """).fetchall()


def top_apps_by_lifetime_gross(con, n: int = 20) -> list:
    """Top apps by lifetime gross revenue (price × total_purchases)."""
    return con.execute(f"""
        SELECT
            s.display_name, s.author, a.version,
            COALESCE(s.price_cents, 0) AS p,
            COALESCE(s.total_purchases, 0) AS t,
            COALESCE(s.last_month_purchases, 0) AS lm,
            (COALESCE(s.price_cents, 0) * COALESCE(s.total_purchases, 0)) / 100.0 AS gross
        FROM app_snapshots s
        JOIN apps a ON a.app_key = s.app_key
        WHERE s.price_cents > 0 AND s.total_purchases > 0
        ORDER BY gross DESC
        LIMIT {n}
    """).fetchall()


def india_market_position(con) -> dict:
    """How much of the marketplace is Indian publishers?"""
    likes = " OR ".join(["lower(author) LIKE ?"] * len(INDIA_PARTNER_KEYWORDS))
    params = [f"%{k}%" for k in INDIA_PARTNER_KEYWORDS]

    out = {}
    out["india_apps"] = con.execute(
        f"SELECT count(*) FROM app_snapshots WHERE {likes}", params
    ).fetchone()[0]
    out["india_publishers"] = con.execute(
        f"SELECT count(DISTINCT author) FROM app_snapshots WHERE {likes}", params
    ).fetchone()[0]
    out["india_sales_last_mo"] = con.execute(
        f"SELECT sum(COALESCE(last_month_purchases, 0)) FROM app_snapshots WHERE {likes}",
        params,
    ).fetchone()[0]
    out["india_gross_last_mo"] = con.execute(
        f"SELECT sum(COALESCE(price_cents, 0) * COALESCE(last_month_purchases, 0)) / 100.0 "
        f"FROM app_snapshots WHERE {likes}",
        params,
    ).fetchone()[0]
    out["india_median_price_paid"] = con.execute(
        f"SELECT quantile_cont(price_cents, 0.50) FROM app_snapshots "
        f"WHERE price_cents > 0 AND ({likes})",
        params,
    ).fetchone()[0]
    out["non_india_median_price_paid"] = con.execute(
        f"SELECT quantile_cont(price_cents, 0.50) FROM app_snapshots "
        f"WHERE price_cents > 0 AND NOT ({likes})",
        params,
    ).fetchone()[0]
    return out


def top_india_publishers(con, n: int = 20) -> list:
    likes = " OR ".join(["lower(author) LIKE ?"] * len(INDIA_PARTNER_KEYWORDS))
    params = [f"%{k}%" for k in INDIA_PARTNER_KEYWORDS]
    return con.execute(f"""
        SELECT
            author,
            count(*) AS app_count,
            sum(COALESCE(last_month_purchases, 0)) AS sales_last_mo,
            sum(COALESCE(total_purchases, 0)) AS sales_total,
            (sum(COALESCE(price_cents, 0) * COALESCE(last_month_purchases, 0)) / 100.0) AS gross_last_mo
        FROM app_snapshots
        WHERE {likes}
        GROUP BY author
        ORDER BY gross_last_mo DESC, app_count DESC
        LIMIT {n}
    """, params).fetchall()


def render(stats, prices, velocity, lifetime, top_pubs, top_apps, india, top_india_pubs) -> str:
    out = ["# OdooStack planning stats — market reality check\n"]
    out.append(f"_Generated from local DuckDB. Re-run with `python -m scripts.planning_stats` to refresh._\n")

    out.append(section("1. Market sizing"))
    out.append(f"- **Total app listings:** {stats['total_apps']:,}")
    out.append(f"- **Paid apps:** {stats['paid_apps']:,} ({stats['paid_apps']/stats['total_apps']*100:.0f}%)")
    out.append(f"- **Free apps:** {stats['free_apps']:,} ({stats['free_apps']/stats['total_apps']*100:.0f}%)")
    out.append(f"- **v19-current apps:** {stats['v19_apps']:,} ({stats['v19_apps']/stats['total_apps']*100:.0f}% of catalog)")
    out.append(f"- **Distinct publishers (any apps):** {stats['distinct_publishers']:,}")
    out.append(f"- **Distinct publishers (paid apps):** {stats['paid_publishers']:,}")
    out.append(f"- **Apps with ANY sale last month:** {stats['apps_with_sales_last_mo']:,} "
               f"({stats['apps_with_sales_last_mo']/stats['total_apps']*100:.1f}%) "
               f"→ **{(1-stats['apps_with_sales_last_mo']/stats['total_apps'])*100:.0f}% of apps moved zero last month**")
    out.append(f"- **Apps with ZERO lifetime sales:** {stats['apps_zero_lifetime_sales']:,} "
               f"({stats['apps_zero_lifetime_sales']/stats['total_apps']*100:.0f}% — never sold once)")

    out.append(section("2. Price distribution (paid apps only)"))
    out.append("| Percentile | Price |\n|---|---|")
    for label, val in prices:
        out.append(f"| {label} | {val} |")
    out.append("\n**Reads as:** half of paid apps cost ≤ median price; only 1 in 100 charge p99 or higher. "
               "Don't price your first app above p75 unless you have a strong reason — Odoo buyers anchor to median.")

    out.append(section("3. Sales velocity — last month (the truth filter)"))
    out.append("| Bucket | App count | % of catalog |\n|---|---|---|")
    for label, n, pct in velocity:
        out.append(f"| {label} | {n:,} | {pct} |")
    out.append("\n**Reads as:** the dead/free-passenger tail is enormous. Anything above 2/mo is already top-quartile. "
               "Don't compare yourself to the 'busy' or 'hot' rows for year-1 expectations.")

    out.append(section("4. Lifetime sales distribution"))
    out.append("| Bucket | App count | % of catalog |\n|---|---|---|")
    for label, n, pct in lifetime:
        out.append(f"| {label} | {n:,} | {pct} |")

    out.append(section("5. Top 20 publishers by portfolio size"))
    out.append("| Publisher | Apps | Sales last mo | Sales lifetime | Gross last mo |\n|---|---|---|---|---|")
    for r in top_pubs:
        out.append(f"| {r[0]} | {r[1]:,} | {r[2]:,} | {r[3]:,} | ${r[4]:,.0f} |")

    out.append(section("6. Top 20 apps by lifetime gross revenue"))
    out.append("| App | Author | Ver | Price | Last mo | Lifetime | Gross lifetime |\n|---|---|---|---|---|---|---|")
    for r in top_apps:
        out.append(f"| {r[0]} | {r[1]} | {r[2]} | {fmt_money(r[3])} | {r[5]:,} | {r[4]:,} | ${r[6]:,.0f} |")

    out.append(section("7. India-specific market position"))
    out.append(f"- **Indian publishers (DB-detected):** {india['india_publishers']:,}")
    out.append(f"- **Apps published by Indian authors (DB-detected):** {india['india_apps']:,} "
               f"({india['india_apps']/stats['total_apps']*100:.0f}% of total catalog)")
    out.append(f"- **Indian last-month sales (units):** {india['india_sales_last_mo']:,}")
    out.append(f"- **Indian last-month gross:** ${india['india_gross_last_mo']:,.0f}")
    out.append(f"- **Indian median paid price:** {fmt_money(india['india_median_price_paid'])}  "
               f"vs non-Indian median: {fmt_money(india['non_india_median_price_paid'])}")
    out.append("- _Note: detection uses keyword match on top 50 known India publishers. Real Indian share is HIGHER._")

    out.append(section("8. Top 20 Indian publishers by last-month gross revenue"))
    out.append("| Publisher | Apps | Sales last mo | Sales lifetime | Gross last mo |\n|---|---|---|---|---|")
    for r in top_india_pubs:
        out.append(f"| {r[0]} | {r[1]:,} | {r[2]:,} | {r[3]:,} | ${r[4]:,.0f} |")

    out.append(section("9. KPIs to track for YOUR app (year-1)"))
    out.append("""
**Pre-launch (validate before building):**
- Niche size (apps): 20-200 is the sweet spot. <10 = dead. >500 = saturated.
- Niche last-month sales: ≥10/mo niche-wide = real buyer pool.
- Top-3 author concentration: if top-1 has >40% of niche sales, the moat is steep.
- Top app price: between $40 (median) and $200 (your wedge ceiling).

**Launch month:**
- Days from submission to approval: target ≤14 (median). Slow review = your listing has issues.
- Reviews-per-install ratio: marketplace bias is 5★ but written reviews are gold for SEO.
- Time to first sale: if not within 30 days post-publish, the listing copy is the bottleneck.

**Months 1-3:**
- Sales/mo trajectory: you should see month 1 < month 2 < month 3 if the niche is real and you're iterating on listing copy.
- Refund rate: marketplace gives 30-day refund window — keep refund rate under 5%.
- Support inquiries per install: <0.3 = scalable. >1 = product is broken or docs are bad.

**Months 3-12:**
- Version-upgrade lag: new Odoo version drops, ship your app's new-version build within 6 weeks. Late = lost buyers.
- Reviews-text complaint patterns (scrape your own reviews monthly).
- Competitor watch: re-run `planning_stats.py` monthly, see if anyone enters your niche.

**12-month success ranges (year-1 solo, no prior brand):**
- 1-3 sales/mo by month 6 = on track for $200-800/mo by year 2
- 3-8 sales/mo by month 12 at $50-150 ASP = $150-1,200/mo personal income
- The 4,398 paid publishers in our DB include thousands at this exact level. Be one of them before chasing the top-tier numbers in section 6.
""")

    return "\n".join(out) + "\n"


@click.command()
@click.option("--output", default=None, help="Save markdown to path")
def main(output):
    con = dbmod.connect(read_only=True)
    try:
        stats = main_stats(con)
        prices = price_distribution(con)
        velocity = sales_velocity_buckets(con)
        lifetime = lifetime_buckets(con)
        top_pubs = top_publishers_by_apps(con, n=20)
        top_apps = top_apps_by_lifetime_gross(con, n=20)
        india = india_market_position(con)
        top_india_pubs = top_india_publishers(con, n=20)
    finally:
        con.close()

    md = render(stats, prices, velocity, lifetime, top_pubs, top_apps, india, top_india_pubs)
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(md, encoding="utf-8")
        click.echo(f"Wrote {output}")
    else:
        click.echo(md)


if __name__ == "__main__":
    main()
