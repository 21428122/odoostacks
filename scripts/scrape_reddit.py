"""Daily Reddit crawler for Odoo signal.

Uses Reddit's OAuth2 'installed_client' grant — no Reddit account password
needed, just a free client_id from https://www.reddit.com/prefs/apps
(create an "installed app", redirect URI http://localhost). Set the
client_id as the REDDIT_CLIENT_ID env var. Tokens are cached for 1 hour
in data/reddit/.token.json.

For each seed subreddit we pull /new and /search?q=odoo, plus a sitewide
search for "odoo" mentions in long-tail subs. Posts are deduped in
data/reddit/reddit.sqlite by post id; today's new-or-updated posts
are also written to a daily JSONL snapshot.

Each post is tagged with regex signal categories (client, hiring,
switching, complaint, pricing, india, help) — no LLM, no API spend.

Usage:
    set REDDIT_CLIENT_ID=abc123xyz                 # one-time
    python scripts/scrape_reddit.py                # full daily run
    python scripts/scrape_reddit.py --dry-run      # fetch but don't write
    python scripts/scrape_reddit.py --subs r/Odoo  # one sub only
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import click
import httpx
from rich.console import Console
from rich.table import Table
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

console = Console()

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "reddit"
DB_PATH = DATA_DIR / "reddit.sqlite"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
TOKEN_PATH = DATA_DIR / ".token.json"
DEVICE_ID_PATH = DATA_DIR / ".device_id"

# Reddit requires a unique, descriptive User-Agent per their API rules.
UA = "windows:odoostack-research:0.1 (by /u/odoostack)"

OAUTH_BASE = "https://oauth.reddit.com"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

# Seed subreddits — Odoo-direct + adjacent + India angle (per market thesis).
SEED_SUBS = [
    ("Odoo",          "new"),
    ("Odoo",          "search"),
    ("ERP",           "search"),
    ("smallbusiness", "search"),
    ("Accounting",    "search"),
    ("Entrepreneur",  "search"),
    ("sysadmin",      "search"),
    ("selfhosted",    "search"),
    ("Python",        "search"),
    ("india",         "search"),
    ("IndianStartups","search"),
    ("startups",      "search"),
    ("webdev",        "search"),
    ("freelance",     "search"),
    ("consulting",    "search"),
]
# Sitewide catch-all for mentions in subs we haven't seeded.
SITEWIDE_QUERY = True

SEARCH_QUERY = "odoo"

# Signal regex tagging — case-insensitive, word-boundary aware.
SIGNAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "client":     re.compile(r"\b(my|our) client\b|\bclient (is|wants|needs|asked|requires)\b", re.I),
    "hiring":     re.compile(r"\b(hiring|looking for (a |an )?(odoo )?(developer|dev|consultant|partner|expert)|need (a |an )?(odoo )?(developer|dev|consultant))\b", re.I),
    "switching":  re.compile(r"\b(switching (from|to)|migrating (from|to)|moving (from|to)|replace (sap|netsuite|quickbooks|zoho|tally))\b", re.I),
    "complaint":  re.compile(r"\b(hate|frustrated|frustrating|broken|nightmare|terrible|awful|garbage|worst|sucks?|disaster|painful)\b", re.I),
    "pricing":    re.compile(r"\b(too expensive|overpriced|cant afford|can't afford|pricing model|enterprise (license|cost)|community (vs|or) enterprise|price hike)\b", re.I),
    "india":      re.compile(r"\b(india|indian|gst|e-invoic|einvoic|tally|zoho india|hsn|tds|tcs|gstr)\b", re.I),
    "help":       re.compile(r"\b(need help|how do (i|we|you)|anyone (know|have|tried)|any one|stuck|cant figure|can't figure|how to)\b", re.I),
    "version":    re.compile(r"\b(odoo (1[0-9]|20|21)|migrate to odoo|upgrade to odoo|version (1[0-9]|20))\b", re.I),
    "module":     re.compile(r"\b(custom module|build a module|develop a module|odoo app store|apps\.odoo|opl-1)\b", re.I),
}


# ---------------------------------------------------------------------------
# data model
# ---------------------------------------------------------------------------
@dataclass
class Post:
    id: str               # reddit base36 id (e.g. "1abc234")
    fullname: str         # t3_<id>
    subreddit: str
    title: str
    selftext: str
    author: str
    score: int
    num_comments: int
    created_utc: int      # epoch seconds
    permalink: str        # /r/Odoo/comments/.../title/
    url: str              # external link (or self-post permalink)
    flair: str | None
    is_self: bool
    over_18: bool
    signals: list[str]    # tagged categories
    fetched_via: str      # "r/<sub>/new" | "r/<sub>/search" | "sitewide"
    first_seen_utc: int   # epoch when WE first saw it
    last_seen_utc: int    # epoch of latest re-fetch


def tag_signals(title: str, selftext: str) -> list[str]:
    haystack = f"{title}\n{selftext}"
    return [name for name, pat in SIGNAL_PATTERNS.items() if pat.search(haystack)]


# ---------------------------------------------------------------------------
# OAuth — installed_client grant (read-only, no password)
# ---------------------------------------------------------------------------
def _get_device_id() -> str:
    """Stable per-machine device id (Reddit requires 20-30 chars, alphanumeric)."""
    DEVICE_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DEVICE_ID_PATH.exists():
        return DEVICE_ID_PATH.read_text(encoding="utf-8").strip()
    # 22 alphanumeric chars
    did = uuid.uuid4().hex[:22]
    DEVICE_ID_PATH.write_text(did, encoding="utf-8")
    return did


def _load_cached_token() -> str | None:
    if not TOKEN_PATH.exists():
        return None
    try:
        cached = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
        if cached.get("expires_at", 0) > time.time() + 60:
            return cached["access_token"]
    except Exception:
        return None
    return None


def _save_token(access_token: str, expires_in: int) -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps({
        "access_token": access_token,
        "expires_at": int(time.time()) + int(expires_in),
    }), encoding="utf-8")


def get_access_token(client_id: str) -> str:
    cached = _load_cached_token()
    if cached:
        return cached
    device_id = _get_device_id()
    r = httpx.post(
        TOKEN_URL,
        auth=(client_id, ""),  # installed apps have no client_secret
        data={
            "grant_type": "https://oauth.reddit.com/grants/installed_client",
            "device_id": device_id,
        },
        headers={"User-Agent": UA},
        timeout=15.0,
    )
    if r.status_code != 200:
        raise RuntimeError(
            f"Reddit token request failed: HTTP {r.status_code} {r.text[:200]}\n"
            f"Verify REDDIT_CLIENT_ID is correct and the app is type 'installed'."
        )
    body = r.json()
    token = body["access_token"]
    _save_token(token, body.get("expires_in", 3600))
    return token


# ---------------------------------------------------------------------------
# fetching
# ---------------------------------------------------------------------------
@retry(
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    reraise=True,
)
def _fetch(client: httpx.Client, url: str, params: dict | None = None) -> dict:
    r = client.get(url, params=params, timeout=20.0)
    if r.status_code == 429:
        time.sleep(5)
        r.raise_for_status()
    if r.status_code == 401:
        # Token expired mid-run — clear cache so caller can refresh.
        TOKEN_PATH.unlink(missing_ok=True)
        r.raise_for_status()
    r.raise_for_status()
    return r.json()


def _parse_children(data: dict, fetched_via: str) -> list[Post]:
    posts: list[Post] = []
    now = int(time.time())
    children = data.get("data", {}).get("children", [])
    for c in children:
        if c.get("kind") != "t3":
            continue
        d = c.get("data", {})
        title = d.get("title") or ""
        selftext = d.get("selftext") or ""
        signals = tag_signals(title, selftext)
        posts.append(Post(
            id=d.get("id") or "",
            fullname=d.get("name") or "",
            subreddit=d.get("subreddit") or "",
            title=title,
            selftext=selftext,
            author=d.get("author") or "",
            score=int(d.get("score") or 0),
            num_comments=int(d.get("num_comments") or 0),
            created_utc=int(d.get("created_utc") or 0),
            permalink=d.get("permalink") or "",
            url=d.get("url") or "",
            flair=d.get("link_flair_text"),
            is_self=bool(d.get("is_self")),
            over_18=bool(d.get("over_18")),
            signals=signals,
            fetched_via=fetched_via,
            first_seen_utc=now,
            last_seen_utc=now,
        ))
    return posts


def fetch_subreddit_new(client: httpx.Client, sub: str, limit: int = 100) -> list[Post]:
    url = f"{OAUTH_BASE}/r/{sub}/new"
    data = _fetch(client, url, params={"limit": limit, "raw_json": 1})
    return _parse_children(data, fetched_via=f"r/{sub}/new")


def fetch_subreddit_search(client: httpx.Client, sub: str, query: str, limit: int = 100) -> list[Post]:
    url = f"{OAUTH_BASE}/r/{sub}/search"
    data = _fetch(client, url, params={
        "q": query, "restrict_sr": "on", "sort": "new", "limit": limit, "raw_json": 1,
    })
    return _parse_children(data, fetched_via=f"r/{sub}/search")


def fetch_sitewide_search(client: httpx.Client, query: str, limit: int = 100) -> list[Post]:
    url = f"{OAUTH_BASE}/search"
    data = _fetch(client, url, params={
        "q": query, "sort": "new", "limit": limit, "raw_json": 1,
    })
    return _parse_children(data, fetched_via="sitewide")


# ---------------------------------------------------------------------------
# storage
# ---------------------------------------------------------------------------
def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            fullname TEXT,
            subreddit TEXT,
            title TEXT,
            selftext TEXT,
            author TEXT,
            score INTEGER,
            num_comments INTEGER,
            created_utc INTEGER,
            permalink TEXT,
            url TEXT,
            flair TEXT,
            is_self INTEGER,
            over_18 INTEGER,
            signals TEXT,           -- JSON array
            fetched_via TEXT,
            first_seen_utc INTEGER,
            last_seen_utc INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_created  ON posts(created_utc)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_first_seen ON posts(first_seen_utc)")
    conn.commit()
    return conn


def upsert_posts(conn: sqlite3.Connection, posts: list[Post]) -> tuple[int, int]:
    """Insert new posts; update score/comments/last_seen on existing.

    Returns (new_count, updated_count).
    """
    new_count = 0
    updated_count = 0
    cur = conn.cursor()
    for p in posts:
        row = cur.execute("SELECT first_seen_utc FROM posts WHERE id = ?", (p.id,)).fetchone()
        if row is None:
            cur.execute("""
                INSERT INTO posts VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p.id, p.fullname, p.subreddit, p.title, p.selftext, p.author,
                p.score, p.num_comments, p.created_utc, p.permalink, p.url,
                p.flair, int(p.is_self), int(p.over_18),
                json.dumps(p.signals), p.fetched_via, p.first_seen_utc, p.last_seen_utc,
            ))
            new_count += 1
        else:
            cur.execute("""
                UPDATE posts
                   SET score = ?, num_comments = ?, last_seen_utc = ?, signals = ?
                 WHERE id = ?
            """, (p.score, p.num_comments, p.last_seen_utc, json.dumps(p.signals), p.id))
            updated_count += 1
    conn.commit()
    return new_count, updated_count


def write_snapshot(posts: list[Post], snapshot_dir: Path) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    out = snapshot_dir / "posts.jsonl"
    with out.open("a", encoding="utf-8") as f:
        for p in posts:
            f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _filter_subs_arg(arg: str | None) -> list[tuple[str, str]] | None:
    if not arg:
        return None
    wanted = {s.strip().removeprefix("r/").lower() for s in arg.split(",") if s.strip()}
    return [(sub, mode) for (sub, mode) in SEED_SUBS if sub.lower() in wanted]


@click.command()
@click.option("--subs", default=None, help="Comma list to filter seed subs, e.g. 'r/Odoo,r/ERP'.")
@click.option("--limit", default=100, show_default=True, help="Posts per endpoint (max 100).")
@click.option("--dry-run", is_flag=True, help="Fetch + tag, but don't write to disk.")
@click.option("--no-sitewide", is_flag=True, help="Skip the sitewide /search.json call.")
@click.option("--sleep", default=1.5, show_default=True, help="Seconds between requests (rate limit).")
def main(subs: str | None, limit: int, dry_run: bool, no_sitewide: bool, sleep: float) -> None:
    """Daily Reddit Odoo crawl. Idempotent — safe to re-run."""
    client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    if not client_id:
        console.print(
            "[red]REDDIT_CLIENT_ID env var not set.[/red]\n"
            "  1. Visit https://www.reddit.com/prefs/apps\n"
            "  2. Click 'create another app...', choose type [bold]installed app[/bold]\n"
            "  3. Set redirect URI to http://localhost\n"
            "  4. Copy the client_id (string under the app name, NOT the secret)\n"
            "  5. Set it: [bold]setx REDDIT_CLIENT_ID <id>[/bold] (then re-open shell)\n"
        )
        raise click.Abort()

    seeds = _filter_subs_arg(subs) or SEED_SUBS
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshot_dir = SNAPSHOTS_DIR / today

    token = get_access_token(client_id)
    headers = {
        "User-Agent": UA,
        "Authorization": f"bearer {token}",
        "Accept": "application/json",
    }
    all_posts: list[Post] = []

    with httpx.Client(headers=headers, follow_redirects=True) as client:
        for sub, mode in seeds:
            try:
                if mode == "new":
                    posts = fetch_subreddit_new(client, sub, limit=limit)
                else:
                    posts = fetch_subreddit_search(client, sub, SEARCH_QUERY, limit=limit)
            except httpx.HTTPStatusError as e:
                console.print(f"[yellow]r/{sub} {mode}: HTTP {e.response.status_code}[/yellow]")
                continue
            except Exception as e:
                console.print(f"[red]r/{sub} {mode}: {e!r}[/red]")
                continue
            console.print(f"  r/{sub:<18} {mode:<7} -> {len(posts):3d} posts")
            all_posts.extend(posts)
            time.sleep(sleep)

        if SITEWIDE_QUERY and not no_sitewide:
            try:
                posts = fetch_sitewide_search(client, SEARCH_QUERY, limit=limit)
                console.print(f"  sitewide search          -> {len(posts):3d} posts")
                all_posts.extend(posts)
            except Exception as e:
                console.print(f"[red]sitewide: {e!r}[/red]")

    # Dedupe across endpoints (same post can appear in r/Odoo/new + sitewide).
    by_id: dict[str, Post] = {}
    for p in all_posts:
        if p.id not in by_id:
            by_id[p.id] = p
        else:
            # merge signals, prefer earlier fetched_via
            existing = by_id[p.id]
            existing.signals = sorted(set(existing.signals) | set(p.signals))
    deduped = list(by_id.values())

    # Filter to actual Odoo-relevant posts. r/Odoo/new returns everything in
    # the sub, so if a post is from a non-Odoo sub it must mention "odoo"
    # somewhere. (Title alone is enough — search.json already filtered for it.)
    relevant = [
        p for p in deduped
        if p.subreddit.lower() == "odoo"
        or "odoo" in (p.title + " " + p.selftext).lower()
    ]

    console.print(f"\n[bold]{len(deduped)} unique posts, {len(relevant)} Odoo-relevant[/bold]")

    # Tagging summary
    sig_counts: dict[str, int] = {}
    for p in relevant:
        for s in p.signals:
            sig_counts[s] = sig_counts.get(s, 0) + 1
    if sig_counts:
        table = Table(title="Signal tag counts (today's pull)")
        table.add_column("signal")
        table.add_column("count", justify="right")
        for sig, cnt in sorted(sig_counts.items(), key=lambda kv: -kv[1]):
            table.add_row(sig, str(cnt))
        console.print(table)

    if dry_run:
        console.print("[dim]--dry-run: no writes[/dim]")
        return

    conn = init_db(DB_PATH)
    try:
        new_count, updated_count = upsert_posts(conn, relevant)
        snap_path = write_snapshot(relevant, snapshot_dir)
        console.print(
            f"[green]wrote {new_count} new, updated {updated_count}[/green] "
            f"-> {DB_PATH.relative_to(DATA_DIR.parent)}"
        )
        console.print(f"[green]snapshot[/green] -> {snap_path.relative_to(DATA_DIR.parent)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
