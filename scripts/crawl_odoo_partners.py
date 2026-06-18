"""Crawl all Odoo partners for a country (e.g. India) using curl_cffi.

www.odoo.com blocks plain httpx via TLS fingerprinting. curl_cffi impersonates
real Chrome so we get through cleanly.

Usage:
    python -m scripts.crawl_odoo_partners --country india-101
    python -m scripts.crawl_odoo_partners --country india-101 --output briefs/india-market/all-partners.md
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import click
from curl_cffi import requests
from selectolax.parser import HTMLParser

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "competitors"


def fetch_page(url: str) -> str:
    """Fetch with Chrome TLS fingerprint impersonation."""
    r = requests.get(url, impersonate="chrome", timeout=30)
    r.raise_for_status()
    return r.text


def extract_partners(html: str) -> list[dict]:
    """Pull every partner card from one page."""
    tree = HTMLParser(html)
    partners = []
    for a in tree.css('a[aria-label="Go to reseller"]'):
        href = a.attributes.get("href", "")
        m = re.search(r"/partners/([a-z0-9][a-z0-9-]+)-(\d+)", href)
        if not m:
            continue
        slug, pid = m.group(1), m.group(2)

        # Inside the card: name (h5), location (div.o_wprofile_pname), grade (img alt or icon class)
        name_node = a.css_first("h5") or a.css_first(".o_wprofile_pname") or a.css_first("strong")
        name = name_node.text(strip=True) if name_node else slug.replace("-", " ").title()
        # Strip trailing grade suffix that bleeds in from sibling badge ("FooGold" -> "Foo")
        name = re.sub(r"(Gold|Silver|Ready)$", "", name).strip()

        # All text inside the card
        text_blob = " ".join(t.strip() for t in a.text(separator=" ").split() if t.strip())

        # Grade hint: look for "Gold", "Silver", "Ready" in img alt or text
        grade = None
        for img in a.css("img[alt]"):
            alt = img.attributes.get("alt", "")
            if alt in ("Gold", "Silver", "Ready"):
                grade = alt
                break
        if not grade:
            for level in ("Gold", "Silver", "Ready"):
                if re.search(rf"\b{level}\b", text_blob):
                    grade = level
                    break

        partners.append({
            "id": pid,
            "slug": slug,
            "name": name,
            "grade": grade,
            "text": text_blob[:300],
            "url": "https://www.odoo.com" + href.split("country_id=")[0].rstrip("?&"),
        })
    return partners


def crawl_all(country: str, save_dir: Path) -> list[dict]:
    save_dir.mkdir(parents=True, exist_ok=True)
    base = f"https://www.odoo.com/partners/country/{country}"
    all_partners: list[dict] = []
    seen_ids: set[str] = set()

    for page_num in range(1, 30):  # safety cap
        url = base if page_num == 1 else f"{base}/page/{page_num}"
        try:
            html = fetch_page(url)
        except Exception as e:
            print(f"page {page_num}: ERROR {e}")
            break
        (save_dir / f"page{page_num}.html").write_text(html, encoding="utf-8")
        partners = extract_partners(html)
        new = [p for p in partners if p["id"] not in seen_ids]
        for p in new:
            seen_ids.add(p["id"])
        all_partners.extend(new)
        print(f"page {page_num}: {len(partners)} cards, {len(new)} new (total: {len(all_partners)})")
        if len(partners) == 0 or len(new) == 0:
            break
        time.sleep(0.5)

    (save_dir / "partners.json").write_text(
        json.dumps(all_partners, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return all_partners


def render_markdown(partners: list[dict], country: str) -> str:
    by_grade: dict[str, list[dict]] = {"Gold": [], "Silver": [], "Ready": [], "—": []}
    for p in partners:
        by_grade.setdefault(p["grade"] or "—", []).append(p)

    lines = [f"# All Odoo partners — {country}", ""]
    lines.append(f"**Total partners scraped:** {len(partners)}")
    lines.append("")
    lines.append(f"**By grade:** Gold {len(by_grade.get('Gold', []))} · "
                 f"Silver {len(by_grade.get('Silver', []))} · "
                 f"Ready {len(by_grade.get('Ready', []))} · "
                 f"Unknown {len(by_grade.get('—', []))}")
    lines.append("")

    for grade in ("Gold", "Silver", "Ready", "—"):
        plist = by_grade.get(grade, [])
        if not plist:
            continue
        lines.append(f"\n## {grade} ({len(plist)})\n")
        lines.append("| # | Name | Profile |")
        lines.append("|---|---|---|")
        for i, p in enumerate(plist, 1):
            lines.append(f"| {i} | {p['name']} | [link]({p['url']}) |")
    return "\n".join(lines) + "\n"


@click.command()
@click.option("--country", default="india-101", show_default=True)
@click.option("--output", default=None, help="Save markdown summary here")
def main(country: str, output: str | None):
    save_dir = DATA_DIR / f"odoo-partners-{country}"
    partners = crawl_all(country, save_dir)
    print(f"\nDONE. {len(partners)} unique partners.")
    print(f"Raw HTML + JSON saved to {save_dir}/")
    md = render_markdown(partners, country)
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(md, encoding="utf-8")
        print(f"Markdown summary: {output}")


if __name__ == "__main__":
    main()
