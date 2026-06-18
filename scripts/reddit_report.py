"""Markdown rollup of the Reddit crawl SQLite db.

Reads data/reddit/reddit.sqlite and emits a markdown report with:
  - top issues (signal-tagged posts, ranked by score+comments)
  - hiring/client signals (potential paying users)
  - trending subs by volume
  - new posts in the window

No LLM — pure SQL aggregation. Cheap to run daily/weekly.

Usage:
    python scripts/reddit_report.py                # last 7 days
    python scripts/reddit_report.py --days 1       # daily
    python scripts/reddit_report.py --days 30 --out report.md
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import click

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "reddit"
DB_PATH = DATA_DIR / "reddit.sqlite"
REPORTS_DIR = DATA_DIR / "reports"


def _engagement(score: int, num_comments: int) -> int:
    # Comments weight 2x score — comments mean active discussion / problems / clients.
    return score + 2 * num_comments


def _row_to_md_link(title: str, permalink: str) -> str:
    safe_title = title.replace("[", "(").replace("]", ")").replace("\n", " ").strip()
    return f"[{safe_title[:120]}](https://reddit.com{permalink})"


def _section_top_signals(conn: sqlite3.Connection, since: int, signal: str, limit: int) -> str:
    rows = conn.execute("""
        SELECT subreddit, title, permalink, score, num_comments, signals, created_utc
          FROM posts
         WHERE first_seen_utc >= ?
           AND signals LIKE ?
         ORDER BY (score + 2*num_comments) DESC
         LIMIT ?
    """, (since, f'%"{signal}"%', limit)).fetchall()
    if not rows:
        return f"_No `{signal}` signals in window._\n"
    out = []
    for sub, title, perma, score, ncomm, signals_json, created in rows:
        sig_list = json.loads(signals_json or "[]")
        sig_chips = " ".join(f"`{s}`" for s in sig_list if s != signal)
        date = datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%d")
        out.append(
            f"- **r/{sub}** ({date}, {score}↑ / {ncomm}💬) — "
            f"{_row_to_md_link(title, perma)} {sig_chips}"
        )
    return "\n".join(out) + "\n"


def _section_top_subs(conn: sqlite3.Connection, since: int) -> str:
    rows = conn.execute("""
        SELECT subreddit, COUNT(*) as n, SUM(score) as s, SUM(num_comments) as c
          FROM posts
         WHERE first_seen_utc >= ?
         GROUP BY subreddit
         ORDER BY n DESC
         LIMIT 20
    """, (since,)).fetchall()
    if not rows:
        return "_No posts in window._\n"
    lines = ["| sub | posts | total ↑ | total 💬 |", "|---|---:|---:|---:|"]
    for sub, n, s, c in rows:
        lines.append(f"| r/{sub} | {n} | {s or 0} | {c or 0} |")
    return "\n".join(lines) + "\n"


def _section_top_authors(conn: sqlite3.Connection, since: int) -> str:
    """Power posters — recurring voices often mean active practitioners or clients."""
    rows = conn.execute("""
        SELECT author, COUNT(*) as n, GROUP_CONCAT(DISTINCT subreddit) as subs
          FROM posts
         WHERE first_seen_utc >= ?
           AND author != '[deleted]'
           AND author != ''
         GROUP BY author
        HAVING n > 1
         ORDER BY n DESC
         LIMIT 15
    """, (since,)).fetchall()
    if not rows:
        return "_No repeat authors._\n"
    lines = ["| author | posts | subs |", "|---|---:|---|"]
    for author, n, subs in rows:
        lines.append(f"| u/{author} | {n} | {subs} |")
    return "\n".join(lines) + "\n"


def _section_keyword_trends(conn: sqlite3.Connection, since: int) -> str:
    """Naive keyword frequency — captures topics not in our regex tags."""
    import re
    rows = conn.execute("""
        SELECT title, selftext FROM posts
         WHERE first_seen_utc >= ?
    """, (since,)).fetchall()
    if not rows:
        return "_No posts._\n"
    # noise filter — common words to drop
    stop = set("""
        the and for with this that have are was were from your you our their they
        will can but not all any odoo about how what when where which who why
        has had been being into onto over under just like into more most some
        such only own same very off out get got also too one two three need
        want using used use users user new old apps app module modules code
        thanks thank please help anyone someone something nothing things able
        com www https http href rel nofollow link comment comments post posts
        reddit.com r self automod amp x200b nbsp ive im dont didnt cant wont
        its hes shes thats whats theres heres whos whose whom shall should would
        could might must may make made making takes taking took give giving gave
        try tried trying gets getting see seen looking look first last next prev
    """.split())
    counter: Counter[str] = Counter()
    word_re = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{3,}")
    for title, selftext in rows:
        text = f"{title} {selftext or ''}".lower()
        for w in word_re.findall(text):
            if w in stop or len(w) < 4:
                continue
            counter[w] += 1
    top = counter.most_common(40)
    if not top:
        return "_No keywords._\n"
    lines = ["| keyword | count |", "|---|---:|"]
    for w, n in top:
        lines.append(f"| `{w}` | {n} |")
    return "\n".join(lines) + "\n"


def build_report(db_path: Path, days: int, top_n: int) -> str:
    conn = sqlite3.connect(db_path)
    now = int(time.time())
    since = now - days * 86400
    total = conn.execute(
        "SELECT COUNT(*) FROM posts WHERE first_seen_utc >= ?", (since,),
    ).fetchone()[0]
    grand_total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sections = [
        f"# Reddit Odoo signal — {today} ({days}-day window)",
        f"_Window covers posts first seen in the last {days} day(s). "
        f"DB total: {grand_total} posts. New in window: {total}._\n",

        "## Hiring & client signals (potential customers)\n",
        _section_top_signals(conn, since, "hiring", top_n),
        _section_top_signals(conn, since, "client", top_n),

        "\n## Migration / switching signals (active buying intent)\n",
        _section_top_signals(conn, since, "switching", top_n),

        "\n## Complaints & frustration (problem topics)\n",
        _section_top_signals(conn, since, "complaint", top_n),

        "\n## Pricing pain (margin / undercut opportunity)\n",
        _section_top_signals(conn, since, "pricing", top_n),

        "\n## India-specific (per market thesis)\n",
        _section_top_signals(conn, since, "india", top_n),

        "\n## Help-seeking / how-to (app idea fodder)\n",
        _section_top_signals(conn, since, "help", top_n),

        "\n## Module / custom-build mentions\n",
        _section_top_signals(conn, since, "module", top_n),

        "\n## Subreddit volume\n",
        _section_top_subs(conn, since),

        "\n## Repeat authors (active voices)\n",
        _section_top_authors(conn, since),

        "\n## Keyword frequency (uncategorized topics)\n",
        _section_keyword_trends(conn, since),
    ]
    conn.close()
    return "\n".join(sections)


@click.command()
@click.option("--days", default=7, show_default=True, help="Window in days.")
@click.option("--top", "top_n", default=15, show_default=True, help="Rows per section.")
@click.option("--out", "out_path", default=None, help="Write to file instead of stdout.")
@click.option("--db", "db_path_arg", default=None, help="Override DB path.")
def main(days: int, top_n: int, out_path: str | None, db_path_arg: str | None) -> None:
    db_path = Path(db_path_arg) if db_path_arg else DB_PATH
    if not db_path.exists():
        click.echo(f"DB not found: {db_path}. Run scripts/scrape_reddit.py first.", err=True)
        sys.exit(1)
    md = build_report(db_path, days, top_n)
    if out_path:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        click.echo(f"wrote {out}")
    else:
        # Default: write to data/reddit/reports/YYYY-MM-DD.md AND echo
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORTS_DIR / f"{today}.md"
        report_path.write_text(md, encoding="utf-8")
        click.echo(md)
        click.echo(f"\n[saved to {report_path}]", err=True)


if __name__ == "__main__":
    main()
