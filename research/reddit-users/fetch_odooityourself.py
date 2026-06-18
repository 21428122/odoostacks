"""Crawl /u/ODOOITYOURSELF profile via Reddit JSON API.

Pulls submitted posts and comments with pagination, writes raw JSON +
a flattened CSV/JSONL for analysis.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

USER = "ODOOITYOURSELF"
OUT_DIR = Path(__file__).parent / USER.lower()
OUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    # Reddit rejects generic UA strings. Be honest, identify the client.
    "User-Agent": "odoostacks-research/0.1 (research; contact: entrophy)",
    "Accept": "application/json",
}

BASE = f"https://www.reddit.com/user/{USER}"


def fetch_listing(kind: str) -> list[dict]:
    """kind in {'submitted','comments','overview'}"""
    items: list[dict] = []
    after: str | None = None
    page = 0
    while True:
        params = {"limit": 100, "raw_json": 1}
        if after:
            params["after"] = after
        url = f"{BASE}/{kind}.json"
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 429:
            print(f"  429 rate limited, sleeping 30s", flush=True)
            time.sleep(30)
            continue
        if r.status_code != 200:
            print(f"  {kind} HTTP {r.status_code}: {r.text[:200]}", flush=True)
            break
        data = r.json()
        children = data.get("data", {}).get("children", [])
        items.extend(children)
        after = data.get("data", {}).get("after")
        page += 1
        print(f"  {kind} page {page}: +{len(children)} (total {len(items)}) after={after}", flush=True)
        if not after:
            break
        if page > 20:  # safety cap
            print(f"  {kind} page cap reached", flush=True)
            break
        time.sleep(2)
    return items


def main():
    print(f"Fetching profile data for /u/{USER}", flush=True)

    about_r = requests.get(f"{BASE}/about.json", headers=HEADERS, timeout=30)
    print(f"about HTTP {about_r.status_code}", flush=True)
    if about_r.status_code == 200:
        (OUT_DIR / "about.json").write_text(
            json.dumps(about_r.json(), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    for kind in ("submitted", "comments"):
        print(f"--- {kind} ---", flush=True)
        items = fetch_listing(kind)
        (OUT_DIR / f"{kind}.json").write_text(
            json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        flat_path = OUT_DIR / f"{kind}.jsonl"
        with flat_path.open("w", encoding="utf-8") as f:
            for c in items:
                d = c.get("data", {})
                row = {
                    "id": d.get("id"),
                    "kind": c.get("kind"),
                    "created_utc": d.get("created_utc"),
                    "subreddit": d.get("subreddit"),
                    "title": d.get("title"),
                    "link_title": d.get("link_title"),
                    "url": d.get("url"),
                    "permalink": d.get("permalink"),
                    "score": d.get("score"),
                    "num_comments": d.get("num_comments"),
                    "selftext": d.get("selftext"),
                    "body": d.get("body"),
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"  wrote {len(items)} -> {flat_path.name}", flush=True)


if __name__ == "__main__":
    main()
