"""Crawl a competitor / partner / agency website to learn their offering.

Server-rendered HTML only — no JS. Saves raw HTML + extracts structured text
into local files. No tokens, no LLM, just requests + selectolax.

Usage:
    python -m scripts.crawl_competitor https://closyss.odoo.com/Consulting%20Services%20%26%20Development
    python -m scripts.crawl_competitor <url> --depth 1   # follow same-domain links 1 hop
    python -m scripts.crawl_competitor <url> --output briefs/competitors/closyss.md
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import click
import httpx
from rich.console import Console
from selectolax.parser import HTMLParser
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

console = Console()

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "competitors"
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "page"


@retry(
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
def fetch(url: str, client: httpx.Client) -> str:
    r = client.get(url, follow_redirects=True, timeout=45)
    r.raise_for_status()
    return r.text


def extract(html: str, base_url: str) -> dict:
    """Pull title, headings, paragraphs, list items, and same-domain links."""
    tree = HTMLParser(html)
    base_host = urlparse(base_url).netloc

    # Strip noise: scripts, styles, nav menus, footers
    for sel in ("script", "style", "nav", "header", "footer"):
        for n in tree.css(sel):
            n.decompose()

    title = tree.css_first("title")
    title_text = title.text(strip=True) if title else ""

    h1 = [n.text(strip=True) for n in tree.css("h1") if n.text(strip=True)]
    h2 = [n.text(strip=True) for n in tree.css("h2") if n.text(strip=True)]
    h3 = [n.text(strip=True) for n in tree.css("h3") if n.text(strip=True)]
    paragraphs = [
        p.text(strip=True)
        for p in tree.css("p")
        if p.text(strip=True) and len(p.text(strip=True)) > 20
    ]
    list_items = [
        li.text(strip=True)
        for li in tree.css("li")
        if li.text(strip=True) and len(li.text(strip=True)) > 5
    ]

    same_domain_links = []
    for a in tree.css("a[href]"):
        href = a.attributes.get("href", "")
        if not href or href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        absolute, _ = urldefrag(absolute)
        if urlparse(absolute).netloc == base_host:
            text = a.text(strip=True)
            same_domain_links.append({"url": absolute, "text": text[:120]})

    # Dedupe links by URL while preserving first-seen text
    seen = set()
    unique_links = []
    for link in same_domain_links:
        if link["url"] in seen:
            continue
        seen.add(link["url"])
        unique_links.append(link)

    return {
        "url": base_url,
        "title": title_text,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "paragraphs": paragraphs,
        "list_items": list_items,
        "links": unique_links,
    }


def crawl(start_url: str, depth: int, max_pages: int, save_dir: Path) -> list[dict]:
    """BFS up to `depth` hops within the same domain."""
    save_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": DEFAULT_UA}
    seen: set[str] = set()
    queue: list[tuple[str, int]] = [(start_url, 0)]
    pages: list[dict] = []

    with httpx.Client(headers=headers) as client:
        while queue and len(pages) < max_pages:
            url, level = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            try:
                html = fetch(url, client)
            except Exception as e:
                console.print(f"[yellow]skip[/yellow] {url}: {e}")
                continue

            slug = slugify(urlparse(url).path or "index")
            (save_dir / f"{slug}.html").write_text(html, encoding="utf-8")
            data = extract(html, url)
            pages.append(data)
            console.print(
                f"[green]got[/green] {url}  "
                f"({len(data['paragraphs'])} paragraphs, "
                f"{len(data['list_items'])} list items)"
            )

            if level < depth:
                for link in data["links"]:
                    if link["url"] not in seen:
                        queue.append((link["url"], level + 1))
            time.sleep(0.5)

    (save_dir / "extract.json").write_text(
        json.dumps(pages, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return pages


def render_markdown(pages: list[dict]) -> str:
    if not pages:
        return "# (no pages crawled)\n"
    lines = [f"# Competitor crawl — {urlparse(pages[0]['url']).netloc}\n"]
    for page in pages:
        lines.append(f"\n---\n\n## {page['title'] or page['url']}")
        lines.append(f"\n**URL:** {page['url']}\n")
        if page["h1"]:
            lines.append("\n**H1:**")
            for h in page["h1"]:
                lines.append(f"- {h}")
        if page["h2"]:
            lines.append("\n**H2 sections:**")
            for h in page["h2"]:
                lines.append(f"- {h}")
        if page["h3"]:
            lines.append("\n**H3 subsections:**")
            for h in page["h3"]:
                lines.append(f"- {h}")
        if page["paragraphs"]:
            lines.append("\n**Body content (first 30 paragraphs):**")
            for p in page["paragraphs"][:30]:
                lines.append(f"\n> {p}\n")
        if page["list_items"]:
            lines.append("\n**Listed items (first 50):**")
            for li in page["list_items"][:50]:
                lines.append(f"- {li}")
        if page["links"]:
            lines.append(f"\n**Same-domain links ({len(page['links'])} total, first 30):**")
            for link in page["links"][:30]:
                lines.append(f"- [{link['text'] or '(no text)'}]({link['url']})")
    return "\n".join(lines) + "\n"


@click.command()
@click.argument("url")
@click.option("--depth", default=0, show_default=True, help="Hops to follow within same domain")
@click.option("--max-pages", default=20, show_default=True, help="Hard cap on crawled pages")
@click.option("--output", default=None, help="Write markdown summary here")
def main(url: str, depth: int, max_pages: int, output: str | None):
    domain = urlparse(url).netloc
    save_dir = DATA_DIR / domain
    pages = crawl(url, depth=depth, max_pages=max_pages, save_dir=save_dir)
    console.print(f"\n[bold]Crawled {len(pages)} pages.[/bold] Raw saved to {save_dir}/")

    md = render_markdown(pages)
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(md, encoding="utf-8")
        console.print(f"Markdown summary written to [bold]{output}[/bold]")
    else:
        console.print(md)


if __name__ == "__main__":
    main()
