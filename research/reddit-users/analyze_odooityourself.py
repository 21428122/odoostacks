"""Analyze crawled /u/ODOOITYOURSELF data — surface expertise signals."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent / "odooityourself"


def load_jsonl(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    posts = load_jsonl(ROOT / "submitted.jsonl")
    comments = load_jsonl(ROOT / "comments.jsonl")

    print("=" * 70)
    print(f"POSTS: {len(posts)}   COMMENTS: {len(comments)}")
    print("=" * 70)

    # Date range
    all_times = [c.get("created_utc") for c in posts + comments if c.get("created_utc")]
    if all_times:
        oldest = datetime.fromtimestamp(min(all_times), tz=timezone.utc)
        newest = datetime.fromtimestamp(max(all_times), tz=timezone.utc)
        print(f"Activity window: {oldest.date()}  ->  {newest.date()}")
        days = (newest - oldest).days or 1
        print(f"  span: {days} days, ~{len(comments)/max(days,1)*30:.1f} comments/month")
    print()

    # Subreddits
    print("--- TOP SUBREDDITS (posts) ---")
    sub_posts = Counter(p["subreddit"] for p in posts if p.get("subreddit"))
    for sub, n in sub_posts.most_common(15):
        print(f"  {n:4d}  r/{sub}")
    print()
    print("--- TOP SUBREDDITS (comments) ---")
    sub_comments = Counter(c["subreddit"] for c in comments if c.get("subreddit"))
    for sub, n in sub_comments.most_common(15):
        print(f"  {n:4d}  r/{sub}")
    print()

    # Top posts by score
    print("--- TOP POSTS BY SCORE ---")
    posts_sorted = sorted(posts, key=lambda x: x.get("score") or 0, reverse=True)
    for p in posts_sorted[:15]:
        ts = datetime.fromtimestamp(p["created_utc"], tz=timezone.utc).date() if p.get("created_utc") else "?"
        print(f"  [{p.get('score'):>3} | {p.get('num_comments'):>3}c | {ts}] r/{p.get('subreddit')}")
        print(f"      {p.get('title','')[:120]}")
    print()

    # Post titles - all
    print("--- ALL POST TITLES (chronological) ---")
    posts_chrono = sorted(posts, key=lambda x: x.get("created_utc") or 0)
    for p in posts_chrono:
        ts = datetime.fromtimestamp(p["created_utc"], tz=timezone.utc).date() if p.get("created_utc") else "?"
        print(f"  {ts}  r/{p.get('subreddit'):<20} {p.get('title','')[:100]}")
    print()

    # Top comments by score
    print("--- TOP COMMENTS BY SCORE ---")
    cmts_sorted = sorted(comments, key=lambda x: x.get("score") or 0, reverse=True)
    for c in cmts_sorted[:25]:
        ts = datetime.fromtimestamp(c["created_utc"], tz=timezone.utc).date() if c.get("created_utc") else "?"
        body = (c.get("body") or "").replace("\n", " ")[:300]
        print(f"  [{c.get('score'):>3} | {ts} | r/{c.get('subreddit')}]")
        print(f"      on: {(c.get('link_title') or '')[:120]}")
        print(f"      >>> {body}")
        print()

    # Keyword frequency for topical signals
    print("--- TOPIC KEYWORDS (across comment bodies) ---")
    text_blob = " ".join((c.get("body") or "").lower() for c in comments)
    keywords = [
        "studio", "owl", "qweb", "xml", "python", "javascript",
        "accounting", "inventory", "mrp", "manufacturing", "pos",
        "crm", "sales", "purchase", "stock", "warehouse",
        "odoo.sh", "saas", "community", "enterprise",
        "module", "app", "customization", "developer", "developer",
        "report", "pivot", "kanban", "form view", "tree view",
        "automation", "server action", "scheduled action",
        "api", "rpc", "xmlrpc", "rest",
        "migration", "upgrade", "v15", "v16", "v17", "v18",
        "fiscal", "tax", "vat", "gst", "invoice", "einvoic",
        "shipping", "delivery", "ecommerce", "website",
        "partner", "vendor", "customer",
        "consult", "implement", "training", "coaching",
        "small business", "smb", "freelance",
        "germany", "europe", "us", "uk", "india", "australia",
    ]
    counts = []
    for kw in keywords:
        c = text_blob.count(kw)
        if c >= 3:
            counts.append((c, kw))
    counts.sort(reverse=True)
    for n, kw in counts[:40]:
        print(f"  {n:5d}  {kw}")
    print()

    # Long, detailed comments (proxy for depth)
    print("--- LONGEST COMMENTS (top 15 by length) ---")
    cmts_len = sorted(comments, key=lambda x: len(x.get("body") or ""), reverse=True)
    for c in cmts_len[:15]:
        ts = datetime.fromtimestamp(c["created_utc"], tz=timezone.utc).date() if c.get("created_utc") else "?"
        body = (c.get("body") or "").replace("\n", " ")
        print(f"  [{len(body):>4}ch | score {c.get('score')} | {ts} | r/{c.get('subreddit')}]")
        print(f"      on: {(c.get('link_title') or '')[:120]}")
        print(f"      >>> {body[:500]}")
        print()


if __name__ == "__main__":
    main()
