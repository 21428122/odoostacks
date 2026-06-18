"""Compute Trend and Opportunity scores from the latest snapshot.

Phase 1 stub. Single-snapshot version — uses fields already on each card
(`last_month_purchases`, `total_purchases`, `review_count`, `rating_stars`)
to produce sensible numbers without needing historical data.

Once we have ≥2 daily runs, replace the velocity proxy here with a true
week-over-week diff.

Usage:
    python scripts/score.py                # rebuild scores from latest run
    python scripts/score.py trends --top 20
    python scripts/score.py niche "expense management"
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys

import click
import duckdb
from rich.console import Console
from rich.table import Table

from . import db as dbmod

console = Console()

ROW_COLUMNS = ("App", "Ver", "Author", "Last mo", "Total", "Stars", "Trend", "Opp")


def _format_row(r: tuple) -> tuple[str, str, str, str, str, str, str, str]:
    return (
        (r[0] or "")[:50],
        r[1] or "",
        (r[2] or "")[:30],
        f"{r[3]:,}",
        f"{r[4]:,}",
        f"{r[5]:.0f}" if r[5] is not None else "-",
        f"{r[6]:.1f}" if r[6] is not None else "-",
        f"{r[7]:.1f}" if r[7] is not None else "-",
    )


def _emit_csv(rows: list[tuple]) -> None:
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(ROW_COLUMNS)
    for r in rows:
        # Re-fetch raw numbers for CSV — strip the comma formatting and the [:50] truncation
        writer.writerow(
            (
                r[0] or "",
                r[1] or "",
                r[2] or "",
                r[3] or 0,
                r[4] or 0,
                "" if r[5] is None else f"{r[5]:.0f}",
                "" if r[6] is None else f"{r[6]:.2f}",
                "" if r[7] is None else f"{r[7]:.2f}",
            )
        )

# ---------------------------------------------------------------------------
# scoring math
# ---------------------------------------------------------------------------


def _percentile(con: duckdb.DuckDBPyConnection, run_id: str, column: str) -> dict:
    """Cache p50/p90/max for a numeric column inside one run."""
    row = con.execute(
        f"""
        SELECT
            quantile_cont({column}, 0.5)  AS p50,
            quantile_cont({column}, 0.9)  AS p90,
            max({column})                  AS pmax
        FROM app_snapshots
        WHERE run_id = ? AND {column} IS NOT NULL
        """,
        [run_id],
    ).fetchone()
    return {"p50": row[0], "p90": row[1], "max": row[2]}


def _norm(value: float | None, p90: float | None) -> float:
    """Normalize value into 0..1 against the run's p90. Anything ≥ p90 saturates."""
    if value is None or p90 in (None, 0):
        return 0.0
    return max(0.0, min(1.0, value / p90))


def latest_run_id(con: duckdb.DuckDBPyConnection) -> str | None:
    row = con.execute(
        "SELECT run_id FROM scrape_runs ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def compute_app_scores(run_id: str | None = None) -> int:
    """Compute per-app Trend and Opportunity scores for one run.

    Stored back in a `app_scores` table that we (re)build each call.
    Returns number of rows written.
    """
    con = dbmod.connect()
    try:
        dbmod.init_schema(con)
        run_id = run_id or latest_run_id(con)
        if not run_id:
            console.print("[red]No runs in DB. Scrape and load first.[/red]")
            return 0

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS app_scores (
                run_id              VARCHAR NOT NULL,
                app_key             VARCHAR NOT NULL,
                trend_score         DOUBLE,
                opportunity_score   DOUBLE,
                PRIMARY KEY (run_id, app_key)
            );
            """
        )
        con.execute("DELETE FROM app_scores WHERE run_id = ?", [run_id])

        last_month_pct = _percentile(con, run_id, "last_month_purchases")
        total_pct = _percentile(con, run_id, "total_purchases")
        reviews_pct = _percentile(con, run_id, "review_count")

        rows = con.execute(
            """
            SELECT
                app_key,
                last_month_purchases,
                total_purchases,
                review_count,
                rating_stars,
                price_cents
            FROM app_snapshots
            WHERE run_id = ?
            """,
            [run_id],
        ).fetchall()

        out: list[tuple] = []
        for (
            app_key,
            last_month,
            total,
            reviews,
            stars,
            price_cents,
        ) in rows:
            # Trend Score
            #   60% recent monthly velocity, 30% review activity, 10% momentum bonus
            #   for apps where last_month / max(total, 1) > 5% (i.e. accelerating).
            n_month = _norm(last_month, last_month_pct["p90"])
            n_reviews = _norm(reviews, reviews_pct["p90"])
            momentum_bonus = 0.0
            if last_month and total and total > 0:
                share = last_month / total
                if share > 0.05:
                    momentum_bonus = min(1.0, math.log1p(share * 20))
            trend = 100 * (0.6 * n_month + 0.3 * n_reviews + 0.1 * momentum_bonus)

            # Opportunity Score
            #   demand (total purchases) × price potential × rating × low-saturation proxy.
            #   Higher review count relative to purchases means more competition / saturation,
            #   so we lightly penalize that.
            n_total = _norm(total, total_pct["p90"])
            price_factor = 0.0
            if price_cents is not None:
                # cap at $500 to prevent outliers from dominating
                price_factor = min(1.0, (price_cents / 100.0) / 500.0)
            else:
                price_factor = 0.1  # unknown price treated as low potential
            stars_factor = (stars or 0) / 5.0
            saturation_penalty = 0.0
            if reviews and total and total > 0:
                ratio = reviews / total
                saturation_penalty = min(0.4, ratio * 5)  # cap at 40%
            raw = (
                0.4 * n_total
                + 0.3 * price_factor
                + 0.2 * stars_factor
                + 0.1 * (1.0 - saturation_penalty)
            )
            opportunity = 100 * raw

            out.append((run_id, app_key, round(trend, 2), round(opportunity, 2)))

        if out:
            con.executemany(
                "INSERT INTO app_scores VALUES (?, ?, ?, ?)",
                out,
            )
        return len(out)
    finally:
        con.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Compute and inspect scores."""
    if ctx.invoked_subcommand is None:
        n = compute_app_scores()
        console.print(f"[green]scored[/green] {n} apps")


@main.command()
@click.option("--top", default=20, show_default=True, type=int)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "csv"]),
    default="table",
    show_default=True,
    help="Output format: pretty table or raw CSV.",
)
def trends(top: int, fmt: str) -> None:
    """Show top apps by Trend Score."""
    con = dbmod.connect(read_only=True)
    try:
        run_id = latest_run_id(con)
        if not run_id:
            console.print("[red]No runs in DB.[/red]")
            return
        rows = con.execute(
            """
            SELECT
                s.display_name,
                a.version,
                s.author,
                COALESCE(s.last_month_purchases, 0)  AS last_month,
                COALESCE(s.total_purchases, 0)       AS total,
                s.rating_stars,
                sc.trend_score,
                sc.opportunity_score
            FROM app_scores sc
            JOIN apps a              ON a.app_key = sc.app_key
            JOIN app_snapshots s     ON s.run_id = sc.run_id AND s.app_key = sc.app_key
            WHERE sc.run_id = ?
            ORDER BY sc.trend_score DESC
            LIMIT ?
            """,
            [run_id, top],
        ).fetchall()
    finally:
        con.close()

    if fmt == "csv":
        _emit_csv(rows)
        return

    table = Table(title=f"Top {top} apps by Trend Score", show_lines=False)
    table.add_column("App", overflow="fold")
    table.add_column("Ver", justify="right")
    table.add_column("Author", overflow="fold")
    table.add_column("Last mo", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Stars", justify="right")
    table.add_column("Trend", justify="right", style="cyan")
    table.add_column("Opp", justify="right", style="magenta")
    for r in rows:
        table.add_row(*_format_row(r))
    console.print(table)


@main.command()
@click.argument("query")
@click.option("--top", default=10, show_default=True, type=int)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "csv"]),
    default="table",
    show_default=True,
    help="Output format: pretty table or raw CSV.",
)
@click.option(
    "--name-only",
    is_flag=True,
    help="Match keyword in display_name only (skips noisy summary matches).",
)
def niche(query: str, top: int, fmt: str, name_only: bool) -> None:
    """Score a niche by keyword. Use --name-only for clean Day 1 gate input."""
    con = dbmod.connect(read_only=True)
    try:
        run_id = latest_run_id(con)
        if not run_id:
            console.print("[red]No runs in DB.[/red]")
            return
        like = f"%{query.lower()}%"
        where = (
            "lower(s.display_name) LIKE ?"
            if name_only
            else "(lower(s.display_name) LIKE ? OR lower(s.summary) LIKE ?)"
        )
        params_match = [like] if name_only else [like, like]

        rows = con.execute(
            f"""
            SELECT
                s.display_name,
                a.version,
                s.author,
                COALESCE(s.last_month_purchases, 0),
                COALESCE(s.total_purchases, 0),
                s.rating_stars,
                sc.trend_score,
                sc.opportunity_score,
                COALESCE(s.price_cents, 0)
            FROM app_scores sc
            JOIN apps a              ON a.app_key = sc.app_key
            JOIN app_snapshots s     ON s.run_id = sc.run_id AND s.app_key = sc.app_key
            WHERE sc.run_id = ?
              AND {where}
            ORDER BY sc.opportunity_score DESC
            LIMIT ?
            """,
            [run_id, *params_match, top],
        ).fetchall()

        rollup = con.execute(
            f"""
            SELECT
                count(*),
                avg(s.rating_stars),
                sum(s.last_month_purchases),
                sum(s.total_purchases)
            FROM app_snapshots s
            WHERE s.run_id = ?
              AND {where}
            """,
            [run_id, *params_match],
        ).fetchone()
    finally:
        con.close()

    if fmt == "csv":
        _emit_csv([r[:8] for r in rows])
        return

    n_apps, avg_rating, sum_last_month, sum_total = rollup
    match_mode = "name-only" if name_only else "name+summary"
    console.print(
        f"\n[bold]niche:[/bold] {query!r}  ({match_mode})  ->  "
        f"{n_apps or 0} apps · "
        f"avg rating {avg_rating:.2f} · " if avg_rating else
        f"{n_apps or 0} apps · "
    )
    console.print(
        f"  last-month purchases: {sum_last_month or 0:,}    "
        f"total purchases: {sum_total or 0:,}\n"
    )

    table = Table(title=f"Top {top} apps in niche by Opportunity Score")
    table.add_column("App", overflow="fold")
    table.add_column("Ver", justify="right")
    table.add_column("Author", overflow="fold")
    table.add_column("Last mo", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Stars", justify="right")
    table.add_column("Trend", justify="right", style="cyan")
    table.add_column("Opp", justify="right", style="magenta")
    for r in rows:
        price_str = f"${r[8] / 100:.0f}" if r[8] else "Free"
        table.add_row(
            (r[0] or "")[:50],
            r[1] or "",
            (r[2] or "")[:30],
            f"{r[3]:,}",
            f"{r[4]:,}",
            price_str,
            f"{r[5]:.0f}" if r[5] is not None else "-",
            f"{r[6]:.1f}" if r[6] is not None else "-",
            f"{r[7]:.1f}" if r[7] is not None else "-",
        )
    console.print(table)

    # Day 1 marketplace gate (validate playbook)
    if rows:
        net_revenue_per_month = (
            sum(r[3] * r[8] / 100.0 for r in rows) * 0.7
        )
        top3_authors = [r[2] for r in rows[:3]]
        author_unique = len(set(top3_authors)) == len(top3_authors) == 3
        weak_apps = [
            (r[0], r[5], r[3])
            for r in rows[:5]
            if (r[5] is not None and r[5] < 4) or r[3] == 0
        ]
        rev_pass = net_revenue_per_month > 2_500
        author_pass = author_unique
        quality_pass = len(weak_apps) >= 2
        all_pass = rev_pass and author_pass and quality_pass

        console.print("\n[bold]Day 1 marketplace gate:[/bold]")
        console.print(
            f"  Net niche revenue (top 10, x0.7): "
            f"${net_revenue_per_month:,.0f}/mo  "
            f"[{'PASS' if rev_pass else 'FAIL'}: needs > $2.5k]"
        )
        console.print(
            f"  Top-3 authors all different:      "
            f"{author_unique}  [{'PASS' if author_pass else 'FAIL'}]"
        )
        console.print(
            f"  Quality gap (top 5, weak apps):   "
            f"{len(weak_apps)}  [{'PASS' if quality_pass else 'FAIL'}: needs >= 2]"
        )
        if weak_apps:
            for name, stars, last_mo in weak_apps:
                stars_str = f"{stars:.1f}*" if stars is not None else "unrated"
                console.print(f"    - {name[:55]:<55} {stars_str:>8} last_mo={last_mo}")
        verdict = "[bold green]GATE PASS[/bold green]" if all_pass else "[bold red]GATE FAIL[/bold red]"
        console.print(f"  Overall: {verdict}")


# ---------------------------------------------------------------------------
# ideabrowser-style card
# ---------------------------------------------------------------------------


_STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "to", "in", "on", "of", "by", "with",
    "odoo", "module", "app", "apps", "manager", "management", "free", "pro",
    "ai", "advanced", "premium", "smart", "easy", "simple", "best", "all",
    "new", "top", "ultimate", "complete",
}


def _primary_keyword(name: str | None) -> str | None:
    """Pick the most distinctive token from a display name (skips stopwords)."""
    if not name:
        return None
    tokens = [t for t in re.findall(r"[A-Za-z][A-Za-z0-9]+", name)]
    for t in tokens:
        if t.lower() not in _STOPWORDS and len(t) > 2:
            return t
    return tokens[0] if tokens else None


def _build_card(con: duckdb.DuckDBPyConnection, run_id: str, app_key: str) -> dict | None:
    """Compose one ideabrowser-style card from snapshots + scores."""
    row = con.execute(
        """
        SELECT
            s.display_name, a.version, s.author, s.summary, s.detail_url,
            s.price_cents, s.currency, s.rating_stars, s.review_count,
            s.total_purchases, s.last_month_purchases,
            sc.trend_score, sc.opportunity_score
        FROM app_snapshots s
        JOIN apps a       ON a.app_key = s.app_key
        LEFT JOIN app_scores sc ON sc.run_id = s.run_id AND sc.app_key = s.app_key
        WHERE s.run_id = ? AND s.app_key = ?
        """,
        [run_id, app_key],
    ).fetchone()
    if not row:
        return None
    (
        name, version, author, summary, url,
        price_cents, currency, stars, reviews,
        total, last_month,
        trend_100, opp_100,
    ) = row

    total = total or 0
    last_month = last_month or 0
    momentum_pct = (last_month / total * 100) if total > 0 else 0.0

    # Timing score: ideabrowser-style 1-10. Reward apps where last month is a meaningful
    # share of all-time sales (= accelerating). 10% monthly share saturates at 10/10.
    timing = min(10.0, momentum_pct)

    price_dollars = (price_cents or 0) / 100.0
    est_month_revenue = price_dollars * last_month  # crude

    paid = price_cents is not None and price_cents > 0
    badges = [version and f"v{version}", "B2B", "Paid" if paid else "Free"]
    if stars and stars >= 4.5:
        badges.append("Top-rated")
    if momentum_pct >= 5:
        badges.append("Accelerating")

    # Competitors: top 3 other apps sharing the primary keyword, by total purchases.
    keyword = _primary_keyword(name)
    competitors: list[dict] = []
    if keyword:
        like = f"%{keyword.lower()}%"
        comp_rows = con.execute(
            """
            SELECT s.display_name, s.author, s.rating_stars, s.total_purchases
            FROM app_snapshots s
            WHERE s.run_id = ? AND s.app_key != ?
              AND lower(s.display_name) LIKE ?
            ORDER BY s.total_purchases DESC NULLS LAST
            LIMIT 3
            """,
            [run_id, app_key, like],
        ).fetchall()
        competitors = [
            {
                "name": r[0],
                "author": r[1],
                "stars": r[2],
                "total_purchases": r[3] or 0,
            }
            for r in comp_rows
        ]

    return {
        "title": name,
        "author": author,
        "version": version,
        "url": url,
        "summary": summary,
        "badges": [b for b in badges if b],
        "scores": {
            "opportunity": round((opp_100 or 0) / 10, 1),
            "trend": round((trend_100 or 0) / 10, 1),
            "timing": round(timing, 1),
            "_note": "1-10 scale; opportunity/trend rescaled from internal 0-100",
        },
        "demand": {
            "total_purchases": total,
            "last_month_purchases": last_month,
            "momentum_pct": round(momentum_pct, 2),
            "review_count": reviews or 0,
            "rating_stars": stars,
        },
        "pricing": {
            "price_usd": price_dollars if paid else 0.0,
            "currency": currency,
            "estimated_monthly_revenue_usd": round(est_month_revenue, 2),
        },
        "competitors": competitors,
        "llm_fields": {
            "problem_severity": None,
            "feasibility": None,
            "why_now": None,
            "market_gap": None,
        },
    }


def _render_card_text(c: dict) -> str:
    bar = "-" * 78
    lines: list[str] = []
    lines.append(bar)
    lines.append(f"  {c['title']}")
    sub = " | ".join(
        x for x in [c.get("author"), c.get("version") and f"v{c['version']}"] if x
    )
    if sub:
        lines.append(f"  {sub}")
    if c.get("badges"):
        lines.append("  [" + "] [".join(c["badges"]) + "]")
    if c.get("url"):
        lines.append(f"  {c['url']}")
    if c.get("summary"):
        lines.append("")
        lines.append(f"  {c['summary']}")

    s = c["scores"]
    lines.append("")
    lines.append("  SCORES (1-10)")
    lines.append(f"    Opportunity   {s['opportunity']:>4}")
    lines.append(f"    Trend         {s['trend']:>4}")
    lines.append(f"    Timing        {s['timing']:>4}    (last-month share of all-time sales)")

    d = c["demand"]
    lines.append("")
    lines.append("  DEMAND")
    lines.append(f"    Total purchases     {d['total_purchases']:,}")
    lines.append(f"    Last month          {d['last_month_purchases']:,}    ({d['momentum_pct']}% momentum)")
    stars_str = f"* {d['rating_stars']:.1f}" if d.get("rating_stars") else "no rating"
    lines.append(f"    Reviews             {d['review_count']:,}    {stars_str}")

    p = c["pricing"]
    lines.append("")
    lines.append("  PRICING & REVENUE")
    if p["price_usd"]:
        lines.append(f"    Price               ${p['price_usd']:.2f}")
    else:
        lines.append("    Price               Free")
    lines.append(f"    Est. monthly rev.   ~${p['estimated_monthly_revenue_usd']:,.0f}")

    if c["competitors"]:
        lines.append("")
        lines.append("  COMPETITION (matching keyword)")
        for i, comp in enumerate(c["competitors"], 1):
            stars = f"* {comp['stars']:.1f}" if comp.get("stars") else "  -"
            lines.append(
                f"    {i}. {(comp['name'] or '')[:48]:<48}  "
                f"{(comp['author'] or '')[:24]:<24}  {stars}  {comp['total_purchases']:>5,}"
            )

    llm = c["llm_fields"]
    pending = [k for k, v in llm.items() if v is None and not k.startswith("_")]
    if pending:
        lines.append("")
        lines.append("  NOT DERIVABLE FROM LISTING DATA")
        for k in pending:
            lines.append(f"    {k}: -")

    lines.append(bar)
    return "\n".join(lines)


@main.command()
@click.argument("app_key", required=False)
@click.option("--top", default=0, type=int, help="Render top-N cards by opportunity instead of one app.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
def card(app_key: str | None, top: int, fmt: str) -> None:
    """Render ideabrowser-style card(s) for one app or the top N by opportunity."""
    con = dbmod.connect(read_only=True)
    try:
        run_id = latest_run_id(con)
        if not run_id:
            console.print("[red]No runs in DB.[/red]")
            return

        keys: list[str] = []
        if app_key:
            keys = [app_key]
        elif top > 0:
            keys = [
                r[0]
                for r in con.execute(
                    """
                    SELECT app_key
                    FROM app_scores
                    WHERE run_id = ?
                    ORDER BY opportunity_score DESC
                    LIMIT ?
                    """,
                    [run_id, top],
                ).fetchall()
            ]
        else:
            console.print("[red]Pass APP_KEY (e.g. 19.0/dashboard_ninja) or --top N.[/red]")
            return

        cards = [c for c in (_build_card(con, run_id, k) for k in keys) if c]
    finally:
        con.close()

    if fmt == "json":
        sys.stdout.write(json.dumps(cards, indent=2, ensure_ascii=False) + "\n")
        return

    for c in cards:
        sys.stdout.write(_render_card_text(c) + "\n\n")


# ---------------------------------------------------------------------------
# niche opportunity hunt — find buildable niches across the catalog
# ---------------------------------------------------------------------------


_NICHE_STOPWORDS = _STOPWORDS | {
    # generic descriptors and connector-class words that aren't niches by themselves
    "connector", "connectors", "integration", "integrations", "integrator",
    "tool", "tools", "system", "systems", "extension", "extensions",
    "plugin", "plugins", "addon", "addons", "add", "ons",
    "auto", "automatic", "automation", "based",
    "multi", "single", "with", "without",
}


def _niche_keyword(name: str | None) -> str | None:
    """First non-stopword token of length >=4. Niches use a wider stoplist than cards."""
    if not name:
        return None
    for t in re.findall(r"[A-Za-z][A-Za-z0-9]+", name):
        if t.lower() not in _NICHE_STOPWORDS and len(t) >= 4:
            return t
    return None


def _p90(values: list[float]) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    return xs[max(0, int(round(0.9 * (len(xs) - 1))))]


def _bucket_niches(rows: list[tuple]) -> dict[str, list[tuple]]:
    """rows: (app_key, display_name, author, price_cents, currency,
              rating_stars, review_count, total_purchases, last_month_purchases)"""
    buckets: dict[str, list[tuple]] = {}
    for r in rows:
        kw = _niche_keyword(r[1])
        if kw:
            buckets.setdefault(kw.lower(), []).append(r)
    return buckets


def _summarize_niche(keyword: str, apps: list[tuple]) -> dict:
    purchases = [a[7] or 0 for a in apps]
    last_month = [a[8] or 0 for a in apps]
    sum_total = sum(purchases)
    sum_lm = sum(last_month)
    top1 = max(purchases) if purchases else 0
    top1_share = (top1 / sum_total) if sum_total > 0 else 1.0

    reviewed = [a for a in apps if (a[6] or 0) >= 5 and a[5] is not None]
    avg_rating = (sum(a[5] for a in reviewed) / len(reviewed)) if reviewed else None
    low_rated = [a for a in reviewed if a[5] < 4]
    quality_gap = (len(low_rated) / len(reviewed)) if reviewed else 0.5

    paid = [a for a in apps if a[3] and a[3] > 0]
    paid_share = len(paid) / len(apps) if apps else 0.0
    prices = sorted([a[3] / 100.0 for a in paid])
    median_price = prices[len(prices) // 2] if prices else 0.0

    momentum = (sum_lm / sum_total) if sum_total > 0 else 0.0

    # display-cased keyword: pick the most common original casing among the apps
    display_kw = keyword
    for a in apps:
        for tok in re.findall(r"[A-Za-z][A-Za-z0-9]+", a[1] or ""):
            if tok.lower() == keyword:
                display_kw = tok
                break
        if display_kw != keyword:
            break

    return {
        "keyword": display_kw,
        "n_apps": len(apps),
        "sum_total": sum_total,
        "sum_last_month": sum_lm,
        "top1_share": top1_share,
        "avg_rating": avg_rating,
        "quality_gap": quality_gap,
        "paid_share": paid_share,
        "median_price_usd": median_price,
        "momentum": momentum,
    }


def _score_niches(niches_list: list[dict]) -> None:
    """Mutates each dict to add an `opportunity` score in 0-100."""
    if not niches_list:
        return
    log_demands = [math.log10(n["sum_total"] + 1) for n in niches_list]
    p90_log = _p90(log_demands) or 1.0
    p90_price = _p90([n["median_price_usd"] for n in niches_list]) or 1.0

    for n in niches_list:
        # demand: log-rescaled against 90th percentile
        demand = min(1.0, math.log10(n["sum_total"] + 1) / p90_log)
        # fragmentation: linear from top1=0.8 (monopoly) -> 0.2 (open) -> 1.0
        t1 = n["top1_share"]
        if t1 >= 0.8:
            frag = 0.0
        elif t1 <= 0.2:
            frag = 1.0
        else:
            frag = (0.8 - t1) / 0.6
        # quality_gap: share of reviewed apps below 4 stars; unknown -> 0.5
        qgap = n["quality_gap"]
        # price headroom: rescaled median price
        price = (
            min(1.0, n["median_price_usd"] / p90_price) if p90_price > 0 else 0.0
        )
        # momentum: monthly share of all-time, saturating at 10%
        mom = min(1.0, n["momentum"] / 0.1)

        n["opportunity"] = round(
            100
            * (
                0.30 * demand
                + 0.25 * frag
                + 0.20 * qgap
                + 0.15 * price
                + 0.10 * mom
            ),
            1,
        )


@main.command()
@click.option("--top", default=20, show_default=True, type=int)
@click.option(
    "--min-apps",
    default=3,
    show_default=True,
    type=int,
    help="Skip niches with fewer apps than this.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "csv"]),
    default="table",
    show_default=True,
)
def niches(top: int, min_apps: int, fmt: str) -> None:
    """Rank niches (apps grouped by primary keyword) by buildable opportunity."""
    con = dbmod.connect(read_only=True)
    try:
        run_id = latest_run_id(con)
        if not run_id:
            console.print("[red]No runs in DB.[/red]")
            return
        rows = con.execute(
            """
            SELECT
                app_key, display_name, author, price_cents, currency,
                rating_stars, review_count, total_purchases, last_month_purchases
            FROM app_snapshots
            WHERE run_id = ? AND display_name IS NOT NULL
            """,
            [run_id],
        ).fetchall()
    finally:
        con.close()

    buckets = _bucket_niches(rows)
    niches_list = [
        _summarize_niche(kw, apps)
        for kw, apps in buckets.items()
        if len(apps) >= min_apps
    ]
    _score_niches(niches_list)
    niches_list.sort(key=lambda x: x["opportunity"], reverse=True)
    niches_list = niches_list[:top]

    if fmt == "csv":
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(
            [
                "Niche",
                "Apps",
                "Total purchases",
                "Last month",
                "Top1 share %",
                "Avg rating",
                "Quality gap %",
                "Paid %",
                "Median $",
                "Momentum %",
                "Opportunity",
            ]
        )
        for n in niches_list:
            writer.writerow(
                [
                    n["keyword"],
                    n["n_apps"],
                    n["sum_total"],
                    n["sum_last_month"],
                    f"{n['top1_share'] * 100:.1f}",
                    f"{n['avg_rating']:.2f}" if n["avg_rating"] is not None else "",
                    f"{n['quality_gap'] * 100:.0f}",
                    f"{n['paid_share'] * 100:.0f}",
                    f"{n['median_price_usd']:.0f}",
                    f"{n['momentum'] * 100:.2f}",
                    n["opportunity"],
                ]
            )
        return

    table = Table(title=f"Top {top} buildable niches", show_lines=False)
    table.add_column("Niche")
    table.add_column("Apps", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("LastMo", justify="right")
    table.add_column("Top1%", justify="right")
    table.add_column("Rating", justify="right")
    table.add_column("QGap%", justify="right")
    table.add_column("MedPrice", justify="right")
    table.add_column("Mom%", justify="right")
    table.add_column("Opp", justify="right", style="cyan")
    for n in niches_list:
        table.add_row(
            n["keyword"],
            str(n["n_apps"]),
            f"{n['sum_total']:,}",
            f"{n['sum_last_month']:,}",
            f"{n['top1_share'] * 100:.0f}",
            f"{n['avg_rating']:.1f}" if n["avg_rating"] is not None else "-",
            f"{n['quality_gap'] * 100:.0f}",
            f"${n['median_price_usd']:.0f}" if n["median_price_usd"] else "-",
            f"{n['momentum'] * 100:.1f}",
            f"{n['opportunity']:.1f}",
        )
    console.print(table)


if __name__ == "__main__":
    main()
