"""
Odoo Global Partner & Reference Crawler
========================================
Crawls every partner in every country from www.odoo.com/partners.
Extracts partner info, industries they serve, and their client references.

No LLM tokens. Pure HTTP scraping with TLS bypass (curl_cffi).

Output files (in data/partners/global/):
  countries.json          - list of all country slugs + IDs
  partners_raw.csv        - one row per partner (name, country, grade, industries, URL)
  references_raw.csv      - one row per client reference (partner -> client, client industry)
  state.json              - crawl checkpoint for resuming

Usage:
  python scripts/crawl_global_partners.py                   # full crawl (resumes if state exists)
  python scripts/crawl_global_partners.py --phase countries # only fetch country list
  python scripts/crawl_global_partners.py --phase partners  # only crawl partner lists
  python scripts/crawl_global_partners.py --phase refs      # only fetch partner detail pages
  python scripts/crawl_global_partners.py --reset           # wipe state and start fresh
  python scripts/crawl_global_partners.py --delay 2         # slower (more polite)

Requirements:
  pip install curl_cffi selectolax
"""

import argparse
import csv
import json
import re
import time
import random
from pathlib import Path
from datetime import datetime

try:
    from curl_cffi import requests as cffi_requests
    from selectolax.parser import HTMLParser
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(["pip", "install", "curl_cffi", "selectolax"])
    from curl_cffi import requests as cffi_requests
    from selectolax.parser import HTMLParser

# ─── PATHS ───────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent
OUT_DIR     = ROOT / "data" / "partners" / "global"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COUNTRIES_FILE  = OUT_DIR / "countries.json"
PARTNERS_FILE   = OUT_DIR / "partners_raw.csv"
REFS_FILE       = OUT_DIR / "references_raw.csv"
STATE_FILE      = OUT_DIR / "state.json"
HTML_CACHE_DIR  = OUT_DIR / "html_cache"
HTML_CACHE_DIR.mkdir(exist_ok=True)

# ─── CONSTANTS ───────────────────────────────────────────────────────────────
BASE            = "https://www.odoo.com"
PARTNERS_URL    = "https://www.odoo.com/partners"
NAV_WORDS       = {
    'skip', 'menu', 'sign', 'search', 'try it', 'download', 'follow',
    'login', 'contact', 'home', 'blog', 'pricing', 'documentation',
}
HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─── HTTP ─────────────────────────────────────────────────────────────────────
def fetch(url: str, delay: float = 1.0, retries: int = 3) -> str | None:
    """Fetch with Chrome TLS fingerprint. Retries on failure."""
    for attempt in range(retries):
        try:
            r = cffi_requests.get(
                url, impersonate="chrome120", timeout=20,
                headers=HEADERS, allow_redirects=True
            )
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                return None
            print(f"    HTTP {r.status_code} → retrying ({attempt+1}/{retries})")
        except Exception as e:
            print(f"    Error: {e} → retrying ({attempt+1}/{retries})")
        time.sleep(delay * (attempt + 1) + random.uniform(0.2, 0.8))
    return None


def get_cached_or_fetch(cache_key: str, url: str, delay: float) -> str | None:
    """Return cached HTML or fetch and cache it."""
    cache_file = HTML_CACHE_DIR / f"{cache_key}.html"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")
    html = fetch(url, delay)
    if html:
        cache_file.write_text(html, encoding="utf-8", errors="replace")
    time.sleep(delay + random.uniform(0, 0.5))
    return html


# ─── STATE ────────────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {
        "countries_done": False,
        "partners_done": False,
        "crawled_country_slugs": [],
        "crawled_partner_ids": [],
        "started_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }


def save_state(state: dict):
    state["last_updated"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ─── CSV HELPERS ─────────────────────────────────────────────────────────────
PARTNER_FIELDS = ["partner_id", "name", "grade", "country", "country_slug",
                  "industries", "employees", "url", "crawled_at"]
REF_FIELDS     = ["partner_id", "partner_name", "partner_country",
                  "client_name", "client_industry", "description", "crawled_at"]


def append_rows(filepath: Path, rows: list[dict], fieldnames: list[str]):
    exists = filepath.exists()
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


# ─── PHASE 1: COUNTRY LIST ────────────────────────────────────────────────────
def fetch_countries(delay: float) -> list[dict]:
    """Extract all country slugs from the partners directory."""
    print("\n[Phase 1] Fetching country list from /partners ...")
    html = fetch(PARTNERS_URL, delay)
    if not html:
        print("ERROR: could not fetch partners index page")
        return []

    tree = HTMLParser(html)
    countries = []
    seen = set()

    # Country links appear as /partners/country/NAME-ID
    for a in tree.css("a[href*='/partners/country/']"):
        href = a.attributes.get("href", "")
        m = re.search(r"/partners/country/([a-z0-9][a-z0-9-]+-(\d+))", href)
        if not m:
            continue
        slug = m.group(1)
        cid  = m.group(2)
        if slug in seen:
            continue
        seen.add(slug)

        # Derive name from slug (remove trailing numeric ID) — more reliable than DOM text
        raw_name = slug.rsplit("-", 1)[0].replace("-", " ").title()
        name = raw_name if raw_name else slug

        countries.append({"slug": slug, "id": cid, "name": name})

    # Fallback: also parse any JSON embedded in the page
    m_json = re.search(r'"res\.country".*?"records"\s*:\s*(\[.*?\])', html, re.DOTALL)
    if m_json and not countries:
        try:
            records = json.loads(m_json.group(1))
            for rec in records:
                slug = f"{rec.get('display_name','').lower().replace(' ','-')}-{rec.get('id','')}"
                countries.append({"slug": slug, "id": str(rec.get("id","")), "name": rec.get("display_name","")})
        except Exception:
            pass

    print(f"  Found {len(countries)} countries")
    COUNTRIES_FILE.write_text(json.dumps(countries, indent=2, ensure_ascii=False), encoding="utf-8")
    return countries


# ─── PHASE 2: PARTNERS PER COUNTRY ───────────────────────────────────────────
def parse_partner_list_page(html: str, country_slug: str, country_name: str) -> list[dict]:
    """Extract partner cards from one listing page."""
    tree = HTMLParser(html)
    partners = []

    for a in tree.css('a[aria-label="Go to reseller"]'):
        href = a.attributes.get("href", "")
        m = re.search(r"/partners/([a-z0-9][a-z0-9-]+-(\d+))", href)
        if not m:
            continue
        slug, pid = m.group(1), m.group(2)

        # Name
        name_node = a.css_first("h5") or a.css_first("strong") or a.css_first(".o_wprofile_pname")
        name = name_node.text(strip=True) if name_node else slug.replace("-", " ").title()
        name = re.sub(r"\s*(Gold|Silver|Ready)$", "", name).strip()

        # Grade — stored in <span class="badge bg_gold|bg_silver|bg_ready">Gold</span>
        grade = None
        for span in a.css("span.badge"):
            txt = span.text(strip=True)
            if txt in ("Gold", "Silver", "Ready"):
                grade = txt
                break
        if not grade:
            # fallback: check class names on any element
            for el in a.css("[class*='bg_gold'],[class*='bg_silver'],[class*='bg_ready']"):
                cls = el.attributes.get("class", "")
                if "bg_gold" in cls:   grade = "Gold"
                elif "bg_silver" in cls: grade = "Silver"
                elif "bg_ready" in cls:  grade = "Ready"
                if grade: break

        url = BASE + href.split("?")[0].rstrip("/")

        partners.append({
            "partner_id":   pid,
            "name":         name,
            "grade":        grade or "Unknown",
            "country":      country_name,
            "country_slug": country_slug,
            "industries":   "",       # filled in Phase 3
            "employees":    "",       # filled in Phase 3
            "url":          url,
            "crawled_at":   datetime.now().isoformat(),
        })

    return partners


def crawl_country_partners(country: dict, delay: float, seen_ids: set) -> list[dict]:
    """Crawl all paginated partner listing pages for one country."""
    slug  = country["slug"]
    name  = country["name"]
    base  = f"{BASE}/partners/country/{slug}"
    all_partners = []

    for page_num in range(1, 60):
        url       = base if page_num == 1 else f"{base}/page/{page_num}"
        cache_key = f"list_{slug}_p{page_num}"
        html      = get_cached_or_fetch(cache_key, url, delay)
        if not html:
            break

        partners = parse_partner_list_page(html, slug, name)
        new      = [p for p in partners if p["partner_id"] not in seen_ids]
        for p in new:
            seen_ids.add(p["partner_id"])
        all_partners.extend(new)

        print(f"    {name} p{page_num}: {len(partners)} cards, {len(new)} new")

        if len(partners) == 0 or len(new) == 0:
            break

    return all_partners


# ─── PHASE 3: PARTNER DETAIL + REFERENCES ────────────────────────────────────
def parse_partner_detail(html: str, partner: dict) -> tuple[dict, list[dict]]:
    """
    Extract from a partner's profile page:
    - Industries they specialise in
    - Employee count hint
    - Client references (company name, industry, description)
    """
    tree = HTMLParser(html)

    # ── Industries ───────────────────────────────────────────────────────────
    industries = []

    # Method A: look for industry tag pills / spans
    for span in tree.css("span.badge, span.o_tag, .o_field_many2many_tags span, .o_tags span"):
        txt = span.text(strip=True)
        if txt and 2 < len(txt) < 40 and not any(c.isdigit() for c in txt):
            industries.append(txt)

    # Method B: look for a labelled "Industries" section
    for node in tree.css("div, section"):
        label = node.css_first("label, h4, h5, strong, .o_field_label")
        if label and "industr" in label.text(strip=True).lower():
            for child in node.css("span, li, a"):
                txt = child.text(strip=True)
                if txt and len(txt) > 2:
                    industries.append(txt)

    # Method C: generic "Word / Word" inside structured divs (already seen in refs crawler)
    # (don't confuse with reference industry lines — skip here)

    industries = list(dict.fromkeys(i for i in industries if i))

    # ── Employee count ────────────────────────────────────────────────────────
    employees = ""
    text_blob = tree.css_first("body").text(separator="\n") if tree.css_first("body") else ""
    m = re.search(r"(\d[\d,]*)\s+employee", text_blob, re.IGNORECASE)
    if m:
        employees = m.group(1).replace(",", "")

    updated_partner = dict(partner)
    updated_partner["industries"] = "; ".join(industries)
    updated_partner["employees"]  = employees

    # ── References ────────────────────────────────────────────────────────────
    refs = []
    lines = [ln.strip() for ln in text_blob.split("\n") if ln.strip()]

    # Pattern: line N = company name, line N+1 = "Sector / Sector"
    i = 0
    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines):
            nxt = lines[i + 1]
            if " / " in nxt and nxt.count("/") <= 4 and len(nxt) < 120:
                company = line
                # Basic quality gate
                if (5 < len(company) < 150
                        and company[0].isupper()
                        and not any(w in company.lower() for w in NAV_WORDS)):
                    desc = ""
                    if i + 2 < len(lines) and len(lines[i + 2]) > 20:
                        desc = lines[i + 2][:300]
                    refs.append({
                        "partner_id":       partner["partner_id"],
                        "partner_name":     partner["name"],
                        "partner_country":  partner["country"],
                        "client_name":      company,
                        "client_industry":  nxt,
                        "description":      desc,
                        "crawled_at":       datetime.now().isoformat(),
                    })
                    i += 2
                    continue
        i += 1

    # Deduplicate references by client_name within this partner
    seen_clients = set()
    unique_refs  = []
    for r in refs:
        key = r["client_name"].lower()
        if key not in seen_clients:
            seen_clients.add(key)
            unique_refs.append(r)

    return updated_partner, unique_refs


def crawl_partner_detail(partner: dict, delay: float) -> tuple[dict, list[dict]]:
    pid      = partner["partner_id"]
    url      = partner["url"]
    cache_key = f"detail_{pid}"
    html     = get_cached_or_fetch(cache_key, url, delay)
    if not html:
        return partner, []
    return parse_partner_detail(html, partner)


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Crawl all Odoo global partners + references")
    parser.add_argument("--phase", choices=["countries", "partners", "refs", "all"],
                        default="all", help="Which phase to run")
    parser.add_argument("--delay", type=float, default=1.2,
                        help="Seconds between requests (default 1.2)")
    parser.add_argument("--reset", action="store_true",
                        help="Wipe state and restart from scratch")
    args = parser.parse_args()

    if args.reset and STATE_FILE.exists():
        STATE_FILE.unlink()
        print("State reset.")

    state = load_state()
    delay = args.delay

    # ── Phase 1: Countries ────────────────────────────────────────────────────
    if args.phase in ("countries", "all"):
        if state.get("countries_done") and COUNTRIES_FILE.exists():
            print("[Phase 1] Countries already fetched — skipping (use --reset to redo)")
        else:
            countries = fetch_countries(delay)
            if countries:
                state["countries_done"] = True
                save_state(state)
    else:
        if COUNTRIES_FILE.exists():
            countries = json.loads(COUNTRIES_FILE.read_text(encoding="utf-8"))
        else:
            print("ERROR: countries.json not found. Run --phase countries first.")
            return

    countries = json.loads(COUNTRIES_FILE.read_text(encoding="utf-8")) if COUNTRIES_FILE.exists() else []
    if not countries:
        print("No countries found. Exiting.")
        return

    # ── Phase 2: Partner lists ────────────────────────────────────────────────
    if args.phase in ("partners", "all"):
        done_slugs = set(state.get("crawled_country_slugs", []))
        seen_ids   = set()

        # Load already-written partner IDs to avoid duplicates across resume
        if PARTNERS_FILE.exists():
            with open(PARTNERS_FILE, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    seen_ids.add(row["partner_id"])
        print(f"\n[Phase 2] Partners — {len(done_slugs)}/{len(countries)} countries done, "
              f"{len(seen_ids)} partners already saved")

        for country in countries:
            slug = country["slug"]
            if slug in done_slugs:
                continue
            print(f"\n  Crawling: {country['name']} ({slug})")
            new_partners = crawl_country_partners(country, delay, seen_ids)
            if new_partners:
                append_rows(PARTNERS_FILE, new_partners, PARTNER_FIELDS)
                print(f"    => {len(new_partners)} new partners saved")

            done_slugs.add(slug)
            state["crawled_country_slugs"] = list(done_slugs)
            save_state(state)

        state["partners_done"] = True
        save_state(state)
        print(f"\n[Phase 2] Done. Total partners in {PARTNERS_FILE.name}")

    # ── Phase 3: Detail pages + references ───────────────────────────────────
    if args.phase in ("refs", "all"):
        if not PARTNERS_FILE.exists():
            print("ERROR: partners_raw.csv not found. Run --phase partners first.")
            return

        done_ids = set(state.get("crawled_partner_ids", []))
        print(f"\n[Phase 3] Detail pages — {len(done_ids)} already crawled")

        # Read all partners
        with open(PARTNERS_FILE, encoding="utf-8") as f:
            all_partners = list(csv.DictReader(f))

        remaining = [p for p in all_partners if p["partner_id"] not in done_ids]
        total     = len(all_partners)
        print(f"  Total partners: {total}, remaining: {len(remaining)}")

        for idx, partner in enumerate(remaining, 1):
            pid  = partner["partner_id"]
            name = partner["name"]
            print(f"  [{idx}/{len(remaining)}] {name} ({pid})")

            updated_partner, refs = crawl_partner_detail(partner, delay)

            # Update partner row (industries + employees) — append to a separate enriched file
            enriched_file = OUT_DIR / "partners_enriched.csv"
            append_rows(enriched_file, [updated_partner], PARTNER_FIELDS)

            if refs:
                append_rows(REFS_FILE, refs, REF_FIELDS)
                print(f"    => {len(refs)} client refs")
            else:
                print(f"    => no refs found")

            done_ids.add(pid)
            # Save state every 10 partners
            if idx % 10 == 0:
                state["crawled_partner_ids"] = list(done_ids)
                save_state(state)

        state["crawled_partner_ids"] = list(done_ids)
        save_state(state)
        print(f"\n[Phase 3] Done. References in {REFS_FILE.name}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("CRAWL SUMMARY")
    print("=" * 60)
    if PARTNERS_FILE.exists():
        with open(PARTNERS_FILE, encoding="utf-8") as f:
            n_partners = sum(1 for _ in csv.DictReader(f))
        print(f"  Partners:   {n_partners:,} rows in {PARTNERS_FILE.name}")
    if REFS_FILE.exists():
        with open(REFS_FILE, encoding="utf-8") as f:
            n_refs = sum(1 for _ in csv.DictReader(f))
        print(f"  References: {n_refs:,} rows in {REFS_FILE.name}")
    print(f"  Output dir: {OUT_DIR}")
    print(f"  State file: {STATE_FILE}")
    print(f"\nTo resume:  python scripts/crawl_global_partners.py")
    print(f"To restart: python scripts/crawl_global_partners.py --reset")


if __name__ == "__main__":
    main()
