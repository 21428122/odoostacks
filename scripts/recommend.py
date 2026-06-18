"""Recommend Odoo app niches to build, ranked by indie-hacker viability.

Reads the latest DuckDB snapshot, clusters apps into niches by curated keyword
match, scores each niche on the multi-factor model from the playbooks, and prints
the top N candidates with reasoning, competitors, differentiation angle, and
failure-mode warnings.

Usage:
    python -m scripts.recommend                    # top 10 to stdout
    python -m scripts.recommend --top 20           # top 20
    python -m scripts.recommend --output FILE.md   # write markdown report
    python -m scripts.recommend --niche shopify    # show details for one niche
"""
from __future__ import annotations

import math
import re
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click
import duckdb
from rich.console import Console

try:
    from . import db as dbmod
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts import db as dbmod

console = Console()

# Curated niche keywords. A niche = bag of apps whose display_name or summary
# contains the keyword (case-insensitive). Add new keywords as you spot them.

NICHE_KEYWORDS: dict[str, dict] = {
    # ecommerce connectors
    "shopify":           {"complexity": "L", "category": "ecommerce-connector"},
    "woocommerce":       {"complexity": "L", "category": "ecommerce-connector"},
    "magento":           {"complexity": "L", "category": "ecommerce-connector"},
    "prestashop":        {"complexity": "L", "category": "ecommerce-connector"},
    "bigcommerce":       {"complexity": "L", "category": "ecommerce-connector"},
    # marketplace connectors
    "amazon":            {"complexity": "L", "category": "marketplace-connector"},
    "ebay":              {"complexity": "L", "category": "marketplace-connector"},
    "etsy":              {"complexity": "L", "category": "marketplace-connector"},
    "walmart":           {"complexity": "L", "category": "marketplace-connector"},
    # messaging
    "whatsapp":          {"complexity": "M", "category": "messaging"},
    "telegram":          {"complexity": "M", "category": "messaging"},
    "twilio":            {"complexity": "M", "category": "messaging"},
    "sms":               {"complexity": "M", "category": "messaging"},
    "slack":             {"complexity": "M", "category": "messaging"},
    "teams":             {"complexity": "M", "category": "messaging"},
    # accounting connectors
    "quickbooks":        {"complexity": "L", "category": "accounting-connector"},
    "xero":              {"complexity": "L", "category": "accounting-connector"},
    "sage":              {"complexity": "L", "category": "accounting-connector"},
    # shipping
    "shipstation":       {"complexity": "M", "category": "shipping"},
    "fedex":             {"complexity": "M", "category": "shipping"},
    "dhl":               {"complexity": "M", "category": "shipping"},
    # payments
    "stripe":            {"complexity": "M", "category": "payment"},
    "razorpay":          {"complexity": "M", "category": "payment"},
    "paypal":            {"complexity": "M", "category": "payment"},
    # compliance
    "gst":               {"complexity": "M", "category": "compliance"},
    "vat":               {"complexity": "M", "category": "compliance"},
    "e-invoice":          {"complexity": "M", "category": "compliance"},
    "tds":               {"complexity": "S", "category": "compliance"},
    # AI
    "chatgpt":           {"complexity": "M", "category": "ai"},
    "openai":            {"complexity": "M", "category": "ai"},
    "claude":            {"complexity": "M", "category": "ai"},
    "gemini":            {"complexity": "M", "category": "ai"},
    "ai assistant":      {"complexity": "M", "category": "ai"},
    "llm":               {"complexity": "M", "category": "ai"},
    "mcp":               {"complexity": "M", "category": "ai"},
    # analytics
    "dashboard":         {"complexity": "M", "category": "analytics"},
    "kpi":               {"complexity": "S", "category": "analytics"},
    "power bi":          {"complexity": "M", "category": "analytics"},
    # HR
    "expense":           {"complexity": "M", "category": "hr"},
    "payroll":           {"complexity": "L", "category": "hr"},
    "attendance":        {"complexity": "M", "category": "hr"},
    "leave management":  {"complexity": "S", "category": "hr"},
    "recruitment":       {"complexity": "M", "category": "hr"},
    "appraisal":         {"complexity": "S", "category": "hr"},
    # CRM
    "lead scoring":      {"complexity": "S", "category": "crm"},
    "sales pipeline":    {"complexity": "S", "category": "crm"},
    "sales commission":  {"complexity": "M", "category": "crm"},
    "crm dashboard":     {"complexity": "S", "category": "crm"},
    # inventory
    "barcode":           {"complexity": "S", "category": "inventory"},
    "warehouse":         {"complexity": "M", "category": "inventory"},
    "stock alert":       {"complexity": "S", "category": "inventory"},
    # POS
    "pos":               {"complexity": "M", "category": "pos"},
    "restaurant":        {"complexity": "M", "category": "vertical-restaurant"},
    "cafe":              {"complexity": "S", "category": "vertical-restaurant"},
    # billing
    "subscription":      {"complexity": "M", "category": "billing"},
    "recurring":         {"complexity": "M", "category": "billing"},
    "membership":        {"complexity": "M", "category": "billing"},
    # documents
    "pdf":               {"complexity": "S", "category": "document"},
    "ocr":               {"complexity": "M", "category": "document"},
    "e-signature":        {"complexity": "M", "category": "document"},
    "contract":          {"complexity": "M", "category": "document"},
    # email
    "newsletter":        {"complexity": "S", "category": "email"},
    "mass mailing":      {"complexity": "S", "category": "email"},
    # project
    "gantt":             {"complexity": "M", "category": "project"},
    "timesheet":         {"complexity": "S", "category": "project"},
    "project dashboard": {"complexity": "S", "category": "project"},
    # field service
    "field service":     {"complexity": "M", "category": "field-service"},
    "fsm":               {"complexity": "M", "category": "field-service"},
    "maintenance":       {"complexity": "M", "category": "field-service"},
    # verticals
    "real estate":       {"complexity": "L", "category": "vertical-realestate"},
    "property":          {"complexity": "M", "category": "vertical-realestate"},
    "school":            {"complexity": "L", "category": "vertical-education"},
    "education":         {"complexity": "L", "category": "vertical-education"},
    "healthcare":        {"complexity": "L", "category": "vertical-healthcare"},
    "clinic":            {"complexity": "M", "category": "vertical-healthcare"},
    "construction":      {"complexity": "L", "category": "vertical-construction"},
    "manufacturing":     {"complexity": "L", "category": "manufacturing"},
    "automotive":        {"complexity": "M", "category": "vertical-automotive"},
    "hotel":             {"complexity": "M", "category": "vertical-hospitality"},
    # admin / multi
    "access management": {"complexity": "S", "category": "admin"},
    "multi company":     {"complexity": "M", "category": "admin"},
    "multi currency":    {"complexity": "S", "category": "admin"},
    # portals
    "customer portal":   {"complexity": "M", "category": "portal"},
    "vendor portal":     {"complexity": "M", "category": "portal"},
}


@dataclass
class NicheStats:
    keyword: str
    category: str
    complexity: str
    n_apps: int
    total_purchases_lifetime: int
    last_month_purchases: int
    median_price_cents: int | None
    avg_rating: float | None
    pct_low_rating: float       # share of *rated* apps with rating <4
    pct_unrated: float          # share of all apps with no rating
    pct_stale: float            # share where last_month/total <0.5%
    author_count: int
    top_author_share: float
    estimated_monthly_revenue_usd: float
    top_apps: list[dict]
    score: float


def _compile_keyword_pattern(kw: str) -> re.Pattern:
    escaped = re.escape(kw.strip()).replace(r"\ ", r"\s+")
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def _build_niche_stats(con: duckdb.DuckDBPyConnection, run_id: str, kw: str, meta: dict) -> NicheStats | None:
    pattern = _compile_keyword_pattern(kw)

    rows = con.execute(
        """
        SELECT s.app_key, s.display_name, s.summary, s.author,
               s.price_cents, s.rating_stars, s.review_count,
               s.total_purchases, s.last_month_purchases
        FROM app_snapshots s
        WHERE s.run_id = ?
        """,
        [run_id],
    ).fetchall()

    matched: list[dict] = []
    for r in rows:
        (app_key, name, summary, author, price, stars, reviews, total, last_month) = r
        haystack = f"{name or ''} {summary or ''}"
        if pattern.search(haystack):
            matched.append({
                "app_key": app_key,
                "name": name,
                "author": author,
                "price_cents": price,
                "stars": stars,
                "reviews": reviews,
                "total": total or 0,
                "last_month": last_month or 0,
            })

    if len(matched) < 2:
        return None

    n_apps = len(matched)
    total_purchases = sum(a["total"] for a in matched)
    last_month_total = sum(a["last_month"] for a in matched)

    paid_prices = [a["price_cents"] for a in matched if a["price_cents"] and a["price_cents"] > 0]
    median_price_cents = int(statistics.median(paid_prices)) if paid_prices else None

    rated = [a["stars"] for a in matched if a["stars"] is not None]
    avg_rating = sum(rated) / len(rated) if rated else None

    # Quality gap: only count apps that ACTUALLY have a rating below 4.
    # Unrated apps are tracked separately via pct_unrated.
    low_rating = sum(1 for a in matched if a["stars"] is not None and a["stars"] < 4)
    pct_low_rating = (low_rating / len(rated)) if rated else 0.0
    pct_unrated = sum(1 for a in matched if a["stars"] is None) / n_apps

    stale = sum(
        1 for a in matched
        if a["total"] > 0 and (a["last_month"] / a["total"]) < 0.005
    )
    pct_stale = stale / n_apps

    author_purchases: dict[str, int] = {}
    for a in matched:
        author_purchases[a["author"] or "unknown"] = (
            author_purchases.get(a["author"] or "unknown", 0) + a["total"]
        )
    author_count = len(author_purchases)
    if total_purchases > 0:
        shares = [v / total_purchases for v in author_purchases.values()]
        top_author_share = max(shares)
    else:
        top_author_share = 1.0

    est_monthly = 0.0
    for a in matched:
        if a["last_month"] and a["price_cents"]:
            est_monthly += a["last_month"] * (a["price_cents"] / 100.0)
    est_monthly *= 0.7

    s_demand = min(1.0, math.log10(max(est_monthly, 1)) / 5.0)
    s_quality_gap = pct_low_rating
    s_staleness = pct_stale
    s_diversity = 1.0 - top_author_share
    s_size_fit = 1.0 - abs(min(n_apps, 30) - 10) / 30.0
    s_price = min(1.0, (median_price_cents or 0) / 30000.0)

    raw = (0.30 * s_demand + 0.20 * s_quality_gap + 0.20 * s_diversity +
           0.10 * s_staleness + 0.10 * s_size_fit + 0.10 * s_price)

    if n_apps > 50:
        raw *= 0.6
    if n_apps < 4:
        raw *= 0.7
    if est_monthly < 5000:
        raw *= 0.5

    score = round(raw * 100, 1)
    top_apps = sorted(matched, key=lambda a: a["total"], reverse=True)[:5]

    return NicheStats(
        keyword=kw,
        category=meta["category"],
        complexity=meta["complexity"],
        n_apps=n_apps,
        total_purchases_lifetime=total_purchases,
        last_month_purchases=last_month_total,
        median_price_cents=median_price_cents,
        avg_rating=avg_rating,
        pct_low_rating=pct_low_rating,
        pct_unrated=pct_unrated,
        pct_stale=pct_stale,
        author_count=author_count,
        top_author_share=top_author_share,
        estimated_monthly_revenue_usd=est_monthly,
        top_apps=top_apps,
        score=score,
    )


def _failure_modes_for(niche: NicheStats) -> list[str]:
    out = []
    if niche.category in {"crm", "hr", "manufacturing", "analytics", "billing"}:
        out.append('#6 "Killed by Odoo S.A." — Odoo Enterprise has features in this category; check roadmap before committing')
    if niche.complexity == "L":
        out.append('#2 "Scope crept the project to death" — large complexity, easy to overrun 4-week cap')
    if niche.top_author_share > 0.5:
        out.append('#7 "Killed by competitor counter-attack" — one publisher dominates; differentiation must be structural')
    if niche.n_apps > 25:
        out.append('#1 "Built a thing nobody wanted" — saturated category; differentiation needs to be obvious')
    if niche.estimated_monthly_revenue_usd < 15000:
        out.append('#10 "Pricing wrong from launch" — small revenue pool; pricing strategy must be airtight')
    if not out:
        out.append('#11 "Quit too early" — no obvious risks in the data; watch your own patience curve')
    return out[:3]


def _angle_for(niche: NicheStats) -> str:
    if niche.pct_stale > 0.3:
        return f"{int(niche.pct_stale*100)}% of apps show low last-month activity — opportunity to be the actively-maintained choice with weekly updates and modern Odoo support."
    if niche.pct_low_rating > 0.4:
        return f"{int(niche.pct_low_rating*100)}% of *rated* apps below 4★ — opportunity to be the 'just works' choice. Read the low-star reviews to find the top 3 complaints; fix all three in v1."
    if niche.pct_unrated > 0.5:
        return f"{int(niche.pct_unrated*100)}% of apps have no ratings yet — niche is either new or under-marketed. Talk to existing installers; opportunity often hides where reviews don't exist."
    if niche.top_author_share > 0.5 and niche.author_count > 1:
        top = niche.top_apps[0]
        return f"One author dominates ({top['author']}). Find a sub-segment they ignore — country-specific compliance, vertical workflow, smaller-business pricing — and own that."
    if niche.median_price_cents and niche.median_price_cents > 30000:
        return "All competitors priced $300+; opportunity for a mid-market entry at $100-200 with the 80% feature set most users actually use."
    return "Read the top 3 competitors' negative reviews. The pattern of complaints is the differentiation angle."


def _render_console(niches: list[NicheStats], top: int) -> None:
    if not niches:
        console.print("[red]No niches matched any keywords. Did you scrape & load data first?[/red]")
        return

    console.print()
    console.print("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
    console.print(f"[bold cyan]  TOP {top} NICHE RECOMMENDATIONS — apps.odoo.com[/bold cyan]")
    console.print(f"[bold cyan]  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
    console.print()
    console.print("[dim]Reminder: candidate list, not a build recommendation.[/dim]")
    console.print("[dim]Every candidate must still pass the 7-day validate gate.[/dim]")
    console.print()

    for rank, n in enumerate(niches[:top], start=1):
        price_str = f"${n.median_price_cents/100:.0f}" if n.median_price_cents else "free"
        rating_str = f"{n.avg_rating:.1f}★" if n.avg_rating else "n/a"

        console.print(f"[bold]Rank {rank} / {top}[/bold]   [bold magenta]score: {n.score}[/bold magenta]")
        console.print(f"[bold]NICHE:[/bold] [cyan]\"{n.keyword}\"[/cyan]   ({n.complexity} complexity • {n.n_apps} apps • category: {n.category})")
        console.print()
        console.print("[bold]Why this niche scored high:[/bold]")
        console.print(f"  • Estimated monthly revenue across niche: [green]${n.estimated_monthly_revenue_usd:,.0f}/month[/green]")
        console.print(f"  • Last-month purchases (total): {n.last_month_purchases:,}")
        console.print(f"  • Author diversity: {n.author_count} publishers, top one owns {n.top_author_share*100:.0f}% of installs")
        console.print(f"  • Quality: {n.pct_low_rating*100:.0f}% of rated apps below 4★ · {n.pct_unrated*100:.0f}% unrated · {n.pct_stale*100:.0f}% stale")
        console.print(f"  • Median price: {price_str}, average rating across rated apps: {rating_str}")
        console.print()
        console.print("[bold]Top competitors to study:[/bold]")
        for i, a in enumerate(n.top_apps[:3], start=1):
            p = f"${a['price_cents']/100:.0f}" if a['price_cents'] else "free"
            stars = f"{a['stars']:.0f}★" if a['stars'] is not None else "n/a"
            console.print(f"  {i}. {a['name'][:50]:<50} {stars}  total={a['total']:,}  last_mo={a['last_month']:,}  {p}  ({a['author'] or '?'})")
        console.print()
        console.print(f"[bold]Estimated build complexity:[/bold] {n.complexity}  (S = ≤2 weeks, M = 3-4 weeks, L = 5-8 weeks)")
        console.print()
        console.print(f"[bold]Suggested differentiation angle:[/bold]")
        console.print(f"  {_angle_for(n)}")
        console.print()
        console.print("[bold]Watch for these failure modes (from failure-atlas.md):[/bold]")
        for fm in _failure_modes_for(n):
            console.print(f"  - {fm}")
        console.print()
        console.print(f"[bold]Next step:[/bold] /coach validate \"{n.keyword}\"")
        console.print()
        console.print("─" * 60)
        console.print()


def _render_markdown(niches: list[NicheStats], top: int) -> str:
    out = []
    out.append(f"# Top {top} niche recommendations — apps.odoo.com\n")
    out.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    out.append("> Reminder: candidate list, not a build recommendation. Every candidate must still pass the 7-day validate gate.\n")

    for rank, n in enumerate(niches[:top], start=1):
        price_str = f"${n.median_price_cents/100:.0f}" if n.median_price_cents else "free"
        rating_str = f"{n.avg_rating:.1f}★" if n.avg_rating else "n/a"
        out.append(f"## {rank}. \"{n.keyword}\"  (score {n.score})")
        out.append(f"- complexity: **{n.complexity}**  ·  category: `{n.category}`  ·  {n.n_apps} apps")
        out.append(f"- estimated monthly revenue: **${n.estimated_monthly_revenue_usd:,.0f}/month**")
        out.append(f"- author diversity: {n.author_count} publishers, top one = {n.top_author_share*100:.0f}% share")
        out.append(f"- quality: {n.pct_low_rating*100:.0f}% of rated apps below 4★ · {n.pct_unrated*100:.0f}% unrated · {n.pct_stale*100:.0f}% stale, median price {price_str}")
        out.append("")
        out.append("**Top 3 competitors:**")
        for a in n.top_apps[:3]:
            p = f"${a['price_cents']/100:.0f}" if a['price_cents'] else "free"
            stars = f"{a['stars']:.0f}★" if a['stars'] is not None else "n/a"
            out.append(f"- {a['name']} ({a['author']}) — {stars}, {a['total']:,} installs, last month {a['last_month']:,}, {p}")
        out.append("")
        out.append(f"**Differentiation angle:** {_angle_for(n)}")
        out.append("")
        out.append("**Failure modes to watch:**")
        for fm in _failure_modes_for(n):
            out.append(f"- {fm}")
        out.append("")
        out.append(f"**Next:** `/coach validate \"{n.keyword}\"`\n")
        out.append("---\n")

    return "\n".join(out)


@click.command()
@click.option("--top", default=10, type=int, show_default=True)
@click.option("--output", type=click.Path(path_type=Path), help="Write a markdown report to this file.")
@click.option("--niche", help="Show details for a single niche keyword.")
def main(top: int, output: Path | None, niche: str | None) -> None:
    """Recommend Odoo app niches to build, ranked by indie-hacker viability."""
    con = dbmod.connect(read_only=True)
    try:
        run_id_row = con.execute(
            "SELECT run_id FROM scrape_runs ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        if not run_id_row:
            console.print("[red]No scrape runs found. Run odoostack-scrape first.[/red]")
            return
        run_id = run_id_row[0]

        if niche:
            keywords = {niche.lower(): NICHE_KEYWORDS.get(niche.lower(), {"complexity": "M", "category": "custom"})}
        else:
            keywords = NICHE_KEYWORDS

        results: list[NicheStats] = []
        for kw, meta in keywords.items():
            stats = _build_niche_stats(con, run_id, kw, meta)
            if stats:
                results.append(stats)
    finally:
        con.close()

    results.sort(key=lambda x: x.score, reverse=True)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(_render_markdown(results, top), encoding="utf-8")
        console.print(f"[green]Wrote[/green] {output}")
    else:
        _render_console(results, top)


if __name__ == "__main__":
    main()
