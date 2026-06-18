"""Zoho-refugee gap analysis.

For each Zoho One app a refugee would miss, query the local DuckDB for
Odoo marketplace coverage and emit a decision: BUILD, UNDERCUT, WATCH, SKIP.

Run:
    python -m scripts.zoho_gap_analysis
    python -m scripts.zoho_gap_analysis --output briefs/zoho-refugee/decision-table.md
"""
from __future__ import annotations

from pathlib import Path

import click

from . import db as dbmod


# (zoho_app, search_patterns, edition_gap, notes)
# edition_gap: 'enterprise' | 'none' | 'ux-gap' | 'community'
# search_patterns: list of REGEX patterns matched against lowercased display_name (any-of).
# Use \b for word boundaries on short ambiguous terms ("sign", "form", "ticket").
ZOHO_GAPS: list[tuple[str, list[str], str, str]] = [
    ("Zoho Sign",          [r"\bsign\b", r"\bsignature\b", r"\besign\b", r"digital sign", r"e-sign"], "enterprise", "Odoo Sign = Enterprise-only"),
    ("Zoho Bookings",      [r"\bappointment", r"\bbooking"],                                          "enterprise", "Odoo Appointments = Enterprise-only"),
    ("Zoho Desk",          [r"\bhelpdesk", r"support ticket", r"service desk", r"\bsla\b"],          "enterprise", "Odoo Helpdesk = Enterprise-only"),
    ("Zoho Subscriptions", [r"\bsubscription", r"recurring (invoice|billing|payment)"],              "enterprise", "Odoo Subscriptions = Enterprise-only"),
    ("Zoho Marketing Auto",[r"marketing automation", r"\bdrip\b", r"email automation"],              "enterprise", "Enterprise-only"),
    ("Zoho Social",        [r"social media", r"social marketing", r"facebook post", r"instagram"],   "enterprise", "Enterprise-only"),
    ("Zoho WorkDrive",     [r"document management", r"\bdms\b", r"file manager"],                    "enterprise", "Odoo Documents = Enterprise"),
    ("Zoho Learn (LMS)",   [r"\blms\b", r"\belearning\b", r"e-learning", r"online course", r"\btraining course"], "enterprise", "eLearning = Enterprise"),
    ("Zoho Creator",       [r"\bstudio\b", r"low.code", r"no.code", r"app builder"],                 "enterprise", "Studio = Enterprise"),
    ("Zoho Analytics",     [r"\bdashboard\b", r"\banalytics\b", r"\bbi\b", r"business intelligence"],"enterprise", "Spreadsheet/Dashboards = Enterprise"),
    ("Zoho Payroll",       [r"\bpayroll\b"],                                                         "enterprise", "Payroll localizations = Enterprise"),
    ("Zoho SalesIQ",       [r"live chat", r"livechat", r"visitor track", r"website chat"],          "enterprise", "Live Chat full = Enterprise"),
    ("Zoho PageSense",     [r"heatmap", r"a/b test", r"ab test", r"pagesense"],                      "none",       "No Odoo equivalent"),
    ("Zoho Assist",        [r"remote support", r"remote desktop", r"screen share"],                  "none",       "No Odoo equivalent"),
    ("Zoho TeamInbox",     [r"shared inbox", r"team inbox", r"shared mailbox"],                      "none",       "No Odoo equivalent"),
    ("Zoho Vault",         [r"password (manager|vault)", r"\bvault\b", r"credential"],               "none",       "No Odoo equivalent"),
    ("Zoho Notebook",      [r"\bnotebook\b", r"note taking", r"sticky note"],                        "none",       "No Odoo equivalent (Notes is light)"),
    ("Zoho Flow",          [r"\bzapier\b", r"workflow automation", r"integromat", r"\bmake\.com"],   "none",       "No native Zapier-like"),
    ("Zoho DataPrep",      [r"data clean", r"dataprep", r"\betl\b", r"data transform"],              "none",       "No Odoo equivalent"),
    ("Zoho Bigin",         [r"simple crm", r"lite crm", r"small.business crm", r"easy crm"],         "ux-gap",     "Odoo CRM heavy for SMB"),
    ("Zoho Forms",         [r"form builder", r"online form", r"web form", r"\bdynamic form\b"],      "ux-gap",     "Odoo Survey ≠ form builder"),
    ("Zoho Sprints",       [r"\bagile\b", r"\bscrum\b", r"\bsprint\b", r"\bkanban\b"],               "ux-gap",     "Odoo Project limited agile"),
    ("Zoho Connect",       [r"\bintranet\b", r"social intranet", r"company portal"],                 "ux-gap",     "Discuss ≠ intranet"),
    ("Zoho Contracts",     [r"contract management", r"\bclm\b", r"contract lifecycle"],              "ux-gap",     "Sign + DIY"),
    ("Zoho Lens",          [r"augmented reality", r"\bar\b support", r"\bwebar\b"],                  "none",       "No Odoo equivalent"),
]


def latest_run_id(con) -> str | None:
    row = con.execute(
        "SELECT run_id FROM scrape_runs ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def run_niche_query(con, run_id: str, patterns: list[str], top: int = 5):
    """Match any regex pattern in lower(display_name). Returns (rollup, top_apps)."""
    where_clause = " OR ".join(
        ["regexp_matches(lower(s.display_name), ?)"] * len(patterns)
    )
    params = list(patterns)

    rollup = con.execute(
        f"""
        SELECT count(*), sum(s.last_month_purchases), sum(s.total_purchases)
        FROM app_snapshots s
        WHERE s.run_id = ? AND ({where_clause})
        """,
        [run_id, *params],
    ).fetchone()

    top_apps = con.execute(
        f"""
        SELECT s.display_name, s.author,
               COALESCE(s.last_month_purchases, 0),
               COALESCE(s.total_purchases, 0),
               COALESCE(s.price_cents, 0),
               a.version
        FROM app_snapshots s
        JOIN apps a ON a.app_key = s.app_key
        WHERE s.run_id = ? AND ({where_clause})
        ORDER BY COALESCE(s.last_month_purchases, 0) DESC,
                 COALESCE(s.total_purchases, 0) DESC
        LIMIT ?
        """,
        [run_id, *params, top],
    ).fetchall()

    return rollup, top_apps


def decide(rollup, top_apps) -> tuple[str, str]:
    """Return (decision, reason). Honest heuristic, not magic."""
    n_apps, last_mo, total = rollup
    n_apps = n_apps or 0
    last_mo = last_mo or 0
    total = total or 0

    if n_apps == 0:
        return "BUILD", "No competing apps in this niche"
    if n_apps < 5:
        return "BUILD", f"Only {n_apps} apps — wide open"

    top_price = (top_apps[0][4] / 100.0) if top_apps and top_apps[0][4] else 0
    top_last_mo = top_apps[0][2] if top_apps else 0

    if last_mo == 0:
        return "SKIP", f"{n_apps} apps but 0/mo niche-wide — demand dead"
    if last_mo < 3:
        return "SKIP", f"Only {last_mo}/mo niche-wide — too quiet"

    if top_price >= 300:
        return "UNDERCUT", f"Top app ${top_price:.0f} → undercut at $50-99"
    if last_mo >= 5 and top_price < 100:
        return "UNDERCUT", f"{last_mo}/mo, top ${top_price:.0f} → wedge on UX/features"
    if last_mo >= 5:
        return "UNDERCUT", f"{last_mo}/mo, top ${top_price:.0f} → either price or UX"
    return "WATCH", f"Marginal: {last_mo}/mo, top app ${top_price:.0f} sells {top_last_mo}/mo"


def render_markdown(rows) -> str:
    decision_order = {"BUILD": 0, "UNDERCUT": 1, "WATCH": 2, "SKIP": 3}
    rows = sorted(rows, key=lambda r: (decision_order.get(r["decision"], 4), -r["last_mo"]))

    lines = [
        "# Zoho refugee gap-analysis decision table",
        "",
        "Generated from local DuckDB (latest scrape). All numbers are real, queried fresh.",
        "",
        "**Decision rules:**",
        "- `BUILD`: <5 apps in niche → supply is wide open",
        "- `UNDERCUT`: top app priced ≥ $300, OR busy niche (≥5 sales/mo) — wedge on price/UX",
        "- `WATCH`: marginal demand (3-4/mo), watch growth",
        "- `SKIP`: 0-2 sales/mo niche-wide → demand absent",
        "",
        "**Edition gap legend:** `enterprise` = Odoo equivalent is paid Enterprise-only. "
        "`none` = no Odoo equivalent at all. `ux-gap` = exists in Community but UX is bad. "
        "`community` = Community already covers it well.",
        "",
        "| Zoho app | Edition gap | Odoo apps | Niche /mo | Niche total | Top Odoo app | Top price | Top /mo | Top total | Decision | Reason |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['zoho']} | {r['edition']} | {r['n_apps']} | {r['last_mo']} | "
            f"{r['total']} | {r['top_name']} | {r['top_price']} | {r['top_last_mo']} | "
            f"{r['top_total']} | **{r['decision']}** | {r['reason']} |"
        )
    return "\n".join(lines) + "\n"


@click.command()
@click.option("--output", default=None, help="Save markdown to path")
def main(output):
    con = dbmod.connect(read_only=True)
    try:
        run_id = latest_run_id(con)
        if not run_id:
            click.echo("No scrape runs in DB. Run odoostack-load first.")
            return
        rows = []
        for zoho, terms, edition, _notes in ZOHO_GAPS:
            rollup, top_apps = run_niche_query(con, run_id, terms)
            n_apps, last_mo, total = rollup
            top = top_apps[0] if top_apps else None
            decision, reason = decide(rollup, top_apps)
            rows.append({
                "zoho": zoho,
                "edition": edition,
                "n_apps": n_apps or 0,
                "last_mo": last_mo or 0,
                "total": total or 0,
                "top_name": (top[0] or "")[:40] if top else "—",
                "top_price": (f"${top[4] / 100:.0f}" if top and top[4] else ("Free" if top else "—")),
                "top_last_mo": top[2] if top else 0,
                "top_total": top[3] if top else 0,
                "decision": decision,
                "reason": reason,
            })
    finally:
        con.close()

    md = render_markdown(rows)
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(md, encoding="utf-8")
        click.echo(f"Wrote {output}")
    else:
        click.echo(md)


if __name__ == "__main__":
    main()
