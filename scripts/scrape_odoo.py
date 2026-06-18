"""Scrape apps.odoo.com listing pages.

The /apps/modules/browse listing is server-rendered HTML — no JS needed.
We hit each page, parse the app cards, write a per-page JSON snapshot to
data/snapshots/YYYY-MM-DD/, and accumulate one apps.json for the whole run.

Usage:
    python scripts/scrape_odoo.py --max-pages 5    # ~100 apps, smoke test
    python scripts/scrape_odoo.py                  # full crawl (~67k apps, ~20-40 min)
    python scripts/scrape_odoo.py --resume         # skip pages already on disk

After scraping, run scripts/load.py to import into DuckDB.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import click
import httpx
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from selectolax.parser import HTMLParser
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

console = Console()

BASE = "https://apps.odoo.com"
LISTING_URL = BASE + "/apps/modules/browse"
LISTING_PAGE_URL = BASE + "/apps/modules/browse/page/{page}"
DEFAULT_UA = "OdooStack/0.1 (research; contact: github.com/yourname/odoostack)"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

DETAIL_URL_RE = re.compile(r"^/apps/modules/(?P<version>[\d.]+)/(?P<tech>[a-zA-Z0-9_]+)/?$")
# `\d+(?:,\d+)*` matches "2252" and "1,234,567" but stops at a trailing comma —
# important here because the surrounding string is "Total Purchases: 2252, Last month: 42"
# and a greedy [\d,]+ would swallow the comma after the number.
PURCHASES_RE = re.compile(
    r"Total Purchases:\s*(\d+(?:,\d+)*)(?:\s*,\s*Last month:\s*(\d+(?:,\d+)*))?"
)
VOTES_RE = re.compile(r"^(\d+(?:,\d+)*)\s+votes?$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# data model
# ---------------------------------------------------------------------------


@dataclass
class AppCard:
    tech_name: str
    version: str
    detail_url: str
    display_name: str | None
    summary: str | None
    author: str | None
    price_cents: int | None
    currency: str | None
    rating_stars: float | None
    review_count: int | None
    total_purchases: int | None
    last_month_purchases: int | None
    image_url: str | None

    @property
    def app_key(self) -> str:
        return f"{self.version}/{self.tech_name}"


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------


def _to_int(s: str | None) -> int | None:
    if not s:
        return None
    s = s.strip().replace(",", "").replace(" ", "")
    if not s.isdigit():
        return None
    return int(s)


def _parse_card(node) -> AppCard | None:
    """Parse one .loempia_app_entry node. Returns None if structure is unexpected."""
    link = node.css_first("a[href^='/apps/modules/']")
    if not link:
        return None
    href = link.attributes.get("href", "")
    m = DETAIL_URL_RE.match(href)
    if not m:
        return None
    tech_name = m.group("tech")
    version = m.group("version")

    summary_node = node.css_first(".loempia_panel_summary")
    summary = summary_node.text(strip=True) if summary_node else None

    name_node = node.css_first(".loempia_app_entry_bottom h5")
    if name_node:
        display_name = name_node.attributes.get("title") or name_node.text(strip=True)
    else:
        display_name = None

    author_node = node.css_first(".loempia_panel_author b")
    author = author_node.text(strip=True) if author_node else None

    price_cents: int | None = None
    currency: str | None = None
    price_node = node.css_first(".loempia_panel_price")
    if price_node:
        amount_node = price_node.css_first(".oe_currency_value")
        if amount_node:
            try:
                amount = float(amount_node.text(strip=True).replace(",", ""))
                price_cents = int(round(amount * 100))
            except ValueError:
                pass
            full_text = price_node.text(strip=True)
            symbol_match = re.match(r"^([^\d\s]+)", full_text)
            if symbol_match:
                currency = symbol_match.group(1).strip()
        else:
            text_lower = price_node.text(strip=True).lower()
            if "free" in text_lower:
                price_cents = 0
                currency = None

    rating_node = node.css_first(".loempia_rating_stars")
    rating_stars: float | None = None
    review_count: int | None = None
    if rating_node:
        active = rating_node.css(".rating_star_active")
        if active:
            rating_stars = float(len(active))
        title = rating_node.attributes.get("title") or ""
        m_votes = VOTES_RE.match(title.strip())
        if m_votes:
            review_count = _to_int(m_votes.group(1))

    total_purchases: int | None = None
    last_month_purchases: int | None = None
    for tag in node.css(".loempia_tags span[title]"):
        title = tag.attributes.get("title") or ""
        m_pur = PURCHASES_RE.search(title)
        if m_pur:
            total_purchases = _to_int(m_pur.group(1))
            last_month_purchases = _to_int(m_pur.group(2))
            break

    image_url: str | None = None
    img_node = node.css_first(".loempia_cover .img")
    if img_node:
        style = img_node.attributes.get("style") or ""
        m_img = re.search(r"url\(([^)]+)\)", style)
        if m_img:
            raw = m_img.group(1).strip().strip("'\"")
            if raw.startswith("//"):
                raw = "https:" + raw
            image_url = raw

    return AppCard(
        tech_name=tech_name,
        version=version,
        detail_url=BASE + href,
        display_name=display_name,
        summary=summary,
        author=author,
        price_cents=price_cents,
        currency=currency,
        rating_stars=rating_stars,
        review_count=review_count,
        total_purchases=total_purchases,
        last_month_purchases=last_month_purchases,
        image_url=image_url,
    )


def parse_listing(html: str) -> list[AppCard]:
    """Return all app cards parsed from one listing page."""
    tree = HTMLParser(html)
    cards: list[AppCard] = []
    for node in tree.css("div.loempia_app_entry.loempia_app_card"):
        card = _parse_card(node)
        if card:
            cards.append(card)
    return cards


def parse_total_pages(html: str) -> int | None:
    """Find the highest page number in the pagination block."""
    tree = HTMLParser(html)
    max_page = 1
    for a in tree.css("ul.pagination a.page-link"):
        href = a.attributes.get("href") or ""
        m = re.search(r"/page/(\d+)", href)
        if m:
            max_page = max(max_page, int(m.group(1)))
        text = (a.text(strip=True) or "").strip()
        if text.isdigit():
            max_page = max(max_page, int(text))
    return max_page if max_page > 1 else None


# ---------------------------------------------------------------------------
# fetching
# ---------------------------------------------------------------------------


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPError)),
    reraise=True,
)
def _fetch(client: httpx.Client, url: str) -> str:
    resp = client.get(url, timeout=30.0)
    resp.raise_for_status()
    return resp.text


def _page_url(page: int) -> str:
    return LISTING_URL if page == 1 else LISTING_PAGE_URL.format(page=page)


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------


def run_scrape(
    max_pages: int,
    delay: float,
    user_agent: str,
    resume: bool,
) -> Path:
    """Crawl listing pages, write per-page + per-run JSON, return run directory."""
    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    day_dir = SNAPSHOTS_DIR / started_at.strftime("%Y-%m-%d")
    pages_dir = day_dir / run_id / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": user_agent, "Accept-Language": "en-US,en;q=0.9"}

    all_cards: list[AppCard] = []
    pages_scraped = 0

    with httpx.Client(headers=headers, follow_redirects=True) as client:
        first_html = _fetch(client, _page_url(1))
        total_pages = parse_total_pages(first_html) or 1
        target_pages = min(max_pages, total_pages)
        console.print(
            f"[bold cyan]apps.odoo.com[/bold cyan] reports {total_pages} pages; "
            f"will scrape {target_pages}"
        )

        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("apps={task.fields[apps]}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        with progress:
            task = progress.add_task("scraping", total=target_pages, apps=0)

            for page in range(1, target_pages + 1):
                page_file = pages_dir / f"page_{page:04d}.json"
                if resume and page_file.exists():
                    cached = json.loads(page_file.read_text("utf-8"))
                    all_cards.extend(AppCard(**c) for c in cached["cards"])
                    pages_scraped += 1
                    progress.update(task, advance=1, apps=len(all_cards))
                    continue

                html = first_html if page == 1 else _fetch(client, _page_url(page))
                cards = parse_listing(html)
                page_file.write_text(
                    json.dumps(
                        {
                            "page": page,
                            "url": _page_url(page),
                            "captured_at": datetime.now(timezone.utc).isoformat(),
                            "cards": [asdict(c) for c in cards],
                        },
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                all_cards.extend(cards)
                pages_scraped += 1
                progress.update(task, advance=1, apps=len(all_cards))

                if page < target_pages:
                    time.sleep(delay)

    finished_at = datetime.now(timezone.utc)
    run_meta = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "pages_scraped": pages_scraped,
        "total_cards": len(all_cards),
        "user_agent": user_agent,
        "delay_seconds": delay,
    }
    run_dir = day_dir / run_id
    (run_dir / "run.json").write_text(
        json.dumps(run_meta, indent=2),
        encoding="utf-8",
    )
    (run_dir / "apps.json").write_text(
        json.dumps([asdict(c) for c in all_cards], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    console.print(
        f"\n[bold green]done[/bold green] — {len(all_cards)} apps across "
        f"{pages_scraped} pages -> {run_dir}"
    )
    return run_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command()
@click.option(
    "--max-pages",
    default=3500,
    show_default=True,
    type=int,
    help="Cap on number of listing pages to fetch.",
)
@click.option(
    "--delay",
    default=1.5,
    show_default=True,
    type=float,
    help="Politeness delay between page requests, in seconds.",
)
@click.option(
    "--user-agent",
    default=DEFAULT_UA,
    show_default=True,
    help="User-Agent string. Be honest, identify yourself.",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Reuse previously written page JSON files for this run dir if present.",
)
def main(max_pages: int, delay: float, user_agent: str, resume: bool) -> None:
    """Scrape apps.odoo.com and write JSON snapshots under data/snapshots/."""
    run_scrape(
        max_pages=max_pages,
        delay=delay,
        user_agent=user_agent,
        resume=resume,
    )


if __name__ == "__main__":
    main()
