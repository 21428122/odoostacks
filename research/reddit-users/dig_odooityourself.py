"""Drill into specific themes: DIY vs partner, YouTube, apps marketplace, migrations, recency."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent / "odooityourself"


def load_jsonl(p):
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def show(c, max_chars=700):
    ts = datetime.fromtimestamp(c["created_utc"], tz=timezone.utc).date() if c.get("created_utc") else "?"
    body = (c.get("body") or "").replace("\r", "")
    print(f"  [{c.get('score'):>3} | {ts} | r/{c.get('subreddit')}]")
    print(f"      on: {(c.get('link_title') or '')[:120]}")
    print(f"      >>> {body[:max_chars]}")
    print()


def main():
    comments = load_jsonl(ROOT / "comments.jsonl")
    posts = load_jsonl(ROOT / "submitted.jsonl")

    themes = {
        "RECENT (2026)": lambda c: (c.get("created_utc") or 0) > datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp(),
        "PARTNER CRITIQUE": lambda c: any(k in (c.get("body") or "").lower() for k in ["partner", "implementation partner", "reseller"]),
        "DIY / COACHING": lambda c: any(k in (c.get("body") or "").lower() for k in ["coach", "diy", "do it yourself", "yourself", "self host"]),
        "YOUTUBE CHANNEL": lambda c: any(k in (c.get("body") or "").lower() for k in ["youtu.be", "youtube.com", "my channel", "my video"]),
        "APPS / OPL / STORE": lambda c: any(k in (c.get("body") or "").lower() for k in ["apps.odoo", "app store", "opl-1", "third party app", "app from the store", "marketplace"]),
        "MIGRATION / UPGRADE": lambda c: any(k in (c.get("body") or "").lower() for k in ["migrat", "upgrade", "v17", "v18", "v19", "version 17", "version 18", "version 19"]),
        "QUICKBOOKS / RIVAL": lambda c: any(k in (c.get("body") or "").lower() for k in ["quickbooks", "qbo", "xero", "netsuite", "sage", "sap"]),
        "STUDIO": lambda c: "studio" in (c.get("body") or "").lower(),
        "PRICING / SUCCESS PACK": lambda c: any(k in (c.get("body") or "").lower() for k in ["success pack", "line of code", "$/user", "per user", "pricing"]),
        "GEOGRAPHY/MARKET": lambda c: any(k in (c.get("body") or "").lower() for k in ["us based", "germany", "india", "europe", "australia", "canada"]),
        "AI / ODOO 19": lambda c: any(k in (c.get("body") or "").lower() for k in [" ai ", "openai", "llm", "odoo 19", "odoo19", " 19 ", "chatgpt", "claude"]),
    }

    for label, pred in themes.items():
        matches = [c for c in comments if pred(c)]
        matches.sort(key=lambda x: x.get("score") or 0, reverse=True)
        print(f"\n========= {label}  ({len(matches)} matches) =========")
        for c in matches[:8]:
            show(c)


if __name__ == "__main__":
    main()
