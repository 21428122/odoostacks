#!/usr/bin/env python3
"""
European Odoo Partners Crawler
Automatically crawls https://www.odoo.com/partners and extracts
all partner URLs for European countries.

Usage:
    python crawl_european_partners.py
    python crawl_european_partners.py --countries "Germany,France,Belgium"
    python crawl_european_partners.py --output my_partners.txt
"""

import requests
import re
import time
from pathlib import Path
from typing import List, Dict, Set
from urllib.parse import urljoin

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(["pip", "install", "requests", "beautifulsoup4"])
    from bs4 import BeautifulSoup

# ============================================================================
# CONFIGURATION
# ============================================================================

ODOO_PARTNERS_BASE_URL = "https://www.odoo.com/partners"

EUROPEAN_COUNTRIES = {
    'Germany': 'germany-71',
    'France': 'france-64',
    'Belgium': 'belgium-60',
    'Netherlands': 'netherlands-77',
    'United Kingdom': 'united-kingdom-106',
    'UK': 'united-kingdom-106',
    'Austria': 'austria-57',
    'Poland': 'poland-80',
    'Spain': 'spain-91',
    'Italy': 'italy-72',
    'Portugal': 'portugal-83',
    'Greece': 'greece-68',
    'Sweden': 'sweden-93',
    'Norway': 'norway-78',
    'Denmark': 'denmark-63',
    'Finland': 'finland-66',
    'Ireland': 'ireland-70',
    'Hungary': 'hungary-69',
    'Czech Republic': 'czech-republic-62',
    'Romania': 'romania-84',
    'Bulgaria': 'bulgaria-61',
    'Croatia': 'croatia-208',
    'Slovenia': 'slovenia-90',
    'Slovakia': 'slovakia-89',
    'Lithuania': 'lithuania-73',
    'Latvia': 'latvia-74',
    'Estonia': 'estonia-65',
    'Cyprus': 'cyprus-209',
    'Luxembourg': 'luxembourg-75',
    'Malta': 'malta-76',
}

OUTPUT_DIR = Path(__file__).parent.parent / "scripts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ============================================================================
# CRAWLER
# ============================================================================

class EuropeanPartnersCrawler:
    """Crawl Odoo partners directory and extract European partner URLs."""

    def __init__(self, timeout=15, delay_between_requests=1):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout
        self.delay = delay_between_requests
        self.partner_urls = set()
        self.country_partners = {}  # Track partners per country

    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch a page and return BeautifulSoup object."""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"  Error: {e}")
            return None

    def get_country_links_from_main_page(self) -> Dict[str, str]:
        """Extract country links and partner counts from main partners page."""
        print("\nFetching main partners page to detect countries...")

        url = f"{ODOO_PARTNERS_BASE_URL}?country_all=1"
        soup = self.fetch_page(url)

        if not soup:
            print("Failed to fetch main page")
            return {}

        country_links = {}

        # Strategy 1: Look for all anchor tags with country-like text
        all_links = soup.find_all('a')

        for link in all_links:
            href = link.get('href', '').strip()
            text = link.get_text(strip=True)

            # Look for links that might be country filters
            # Pattern: text like "France 133" or just link text with country name
            if '/partners' in href and text and len(text) > 2:
                # Try to extract country name and number
                match = re.search(r'^([A-Za-z\s\-]+?)\s*(\d+)?\s*$', text)

                if match:
                    country_name = match.group(1).strip()
                    count = match.group(2) if match.group(2) else "?"

                    # Filter: must be a reasonable country name
                    if (len(country_name) > 2 and
                        country_name not in ['All', 'Menu', 'Apps', 'Help', 'Sign'] and
                        not country_name[0].isupper() or country_name.count(' ') <= 2):

                        full_url = urljoin(ODOO_PARTNERS_BASE_URL, href)

                        # Avoid duplicates
                        if country_name not in country_links:
                            country_links[country_name] = {
                                'url': full_url,
                                'count': count
                            }
                            print(f"  Found: {country_name} ({count} partners)")

        # Strategy 2: If still no countries, look in buttons or divs with country data attributes
        if not country_links:
            print("  No countries found via links. Trying alternative parsing...")

            # Look for any div/button with country-related content
            country_patterns = [
                'Germany', 'France', 'Belgium', 'Netherlands', 'UK', 'Austria',
                'Poland', 'Spain', 'Italy', 'Portugal', 'Greece', 'Sweden',
                'Norway', 'Denmark', 'Finland', 'Ireland', 'Hungary', 'Czech',
                'Romania', 'Bulgaria', 'Croatia', 'Slovenia', 'Slovakia'
            ]

            for elem in soup.find_all(['a', 'button', 'div']):
                text = elem.get_text(strip=True)
                for country in country_patterns:
                    if country in text:
                        href = elem.get('href', '') or ''
                        if '/partners' in href:
                            full_url = urljoin(ODOO_PARTNERS_BASE_URL, href)
                            match = re.search(r'(\d+)', text)
                            count = match.group(1) if match else "?"

                            if country not in country_links:
                                country_links[country] = {
                                    'url': full_url,
                                    'count': count
                                }
                                print(f"  Found: {country} ({count} partners)")

        return country_links

    def extract_partner_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract partner profile URLs from a partner listing page."""
        urls = []

        if not soup:
            return urls

        # Look for partner profile links
        # Patterns:
        # 1. Links to partner profiles (/partners/[name]-[id])
        # 2. Usually in article or div containers

        # Strategy: Find all links that match partner URL pattern
        all_links = soup.find_all('a', href=re.compile(r'/partners/[a-z0-9\-]+-\d+'))

        for link in all_links:
            href = link.get('href', '').strip()
            if href and '/partners/' in href:
                # Convert to absolute URL if needed
                if href.startswith('/'):
                    full_url = urljoin(ODOO_PARTNERS_BASE_URL, href)
                else:
                    full_url = href

                if full_url not in urls:
                    urls.append(full_url)

        return urls

    def crawl_country(self, country_name: str, country_slug: str) -> List[str]:
        """Crawl all partners for a specific country."""
        print(f"\n{'='*80}")
        print(f"Crawling: {country_name}")
        print(f"{'='*80}")

        country_urls = []
        page = 1
        max_pages = 10  # Safety limit

        while page <= max_pages:
            url = f"{ODOO_PARTNERS_BASE_URL}/country/{country_slug}?page={page}"
            print(f"Page {page}...")

            soup = self.fetch_page(url)
            if not soup:
                break

            # Extract partners from this page
            partners = self.extract_partner_urls(soup)

            if not partners:
                print(f"No partners found. Done with {country_name}.")
                break

            print(f"  Found {len(partners)} partners on page {page}")
            country_urls.extend(partners)

            # Check if there's a next page link
            next_link = soup.find('a', string=re.compile(r'Next|next|>'))
            if not next_link:
                print(f"No next page. Done with {country_name}.")
                break

            page += 1
            time.sleep(self.delay)

        print(f"Total partners in {country_name}: {len(country_urls)}")
        return country_urls

    def crawl_all_european_countries(self, countries: List[str] = None) -> Set[str]:
        """Crawl all specified European countries."""

        # First, get country links from the main page
        country_links = self.get_country_links_from_main_page()

        if not country_links:
            print("No countries found. Falling back to hardcoded list...")
            if countries is None:
                countries = list(EUROPEAN_COUNTRIES.keys())
        else:
            # Filter to European countries if specified
            if countries:
                country_links = {k: v for k, v in country_links.items()
                               if k in countries}
            else:
                # Filter to only European countries
                european_names = set(EUROPEAN_COUNTRIES.keys()) | {
                    'Czech', 'Slovak', 'Lithuanian', 'Latvian', 'Estonian',
                    'Croatian', 'Slovenian', 'Cyprus', 'Malta', 'Iceland',
                    'Greece', 'Portugal', 'Estonia', 'Latvia', 'Lithuania'
                }
                country_links = {k: v for k, v in country_links.items()
                               if any(eu in k for eu in european_names)}

        print(f"\nCrawling {len(country_links)} European countries for Odoo partners...")

        all_partners = set()

        for country_name, country_data in country_links.items():
            print(f"\n{'='*80}")
            print(f"Crawling: {country_name} ({country_data['count']} partners expected)")
            print(f"{'='*80}")

            url = country_data['url']
            partners = self._crawl_country_by_url(country_name, url)
            all_partners.update(partners)

        return all_partners

    def _crawl_country_by_url(self, country_name: str, base_url: str) -> List[str]:
        """Crawl partners for a country given its URL."""
        country_urls = []
        page = 1
        max_pages = 20  # Safety limit

        while page <= max_pages:
            # Add pagination if needed
            url = base_url if page == 1 else f"{base_url}&page={page}"
            print(f"Page {page}...")

            soup = self.fetch_page(url)
            if not soup:
                break

            # Extract partners from this page
            partners = self.extract_partner_urls(soup)

            if not partners:
                print(f"No partners found. Done with {country_name}.")
                break

            print(f"  Found {len(partners)} partners on page {page}")
            country_urls.extend(partners)

            # Check if there's a next page link
            next_link = soup.find('a', string=re.compile(r'Next|next|>'))
            if not next_link:
                print(f"No next page. Done with {country_name}.")
                break

            page += 1
            time.sleep(self.delay)

        print(f"Total partners in {country_name}: {len(country_urls)}")
        self.country_partners[country_name] = len(country_urls)
        return country_urls

    def save_partner_urls(self, urls: Set[str], filename: str = "european_partners_real.txt") -> Path:
        """Save partner URLs to a text file."""
        output_path = OUTPUT_DIR / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            for url in sorted(urls):
                f.write(f"{url}\n")

        print(f"\n[+] Saved {len(urls)} partner URLs to: {output_path}")
        return output_path


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Crawl European Odoo partners and save URLs'
    )
    parser.add_argument('--countries', type=str,
                       help='Comma-separated list of countries (default: all European)')
    parser.add_argument('--output', type=str, default='european_partners_real.txt',
                       help='Output filename (default: european_partners_real.txt)')
    parser.add_argument('--delay', type=int, default=1,
                       help='Delay between requests in seconds (default: 1)')
    parser.add_argument('--debug', action='store_true',
                       help='Save page HTML for inspection')

    args = parser.parse_args()

    # Parse countries if provided
    countries = None
    if args.countries:
        countries = [c.strip() for c in args.countries.split(',')]
        print(f"Crawling specified countries: {countries}")
    else:
        print(f"Crawling all {len(EUROPEAN_COUNTRIES)} European countries")

    # Initialize crawler
    crawler = EuropeanPartnersCrawler(delay_between_requests=args.delay)

    # Crawl
    print("\n" + "="*80)
    print("EUROPEAN ODOO PARTNERS CRAWLER")
    print("="*80)

    # Try main page method first
    partner_urls = crawler.crawl_all_european_countries(countries)

    # If no partners found, use fallback: crawl directly by country slug
    if not partner_urls:
        print("\n[!] Main page parsing failed. Using direct country URLs...")
        print("Crawling European countries directly...\n")

        if countries is None:
            countries = list(EUROPEAN_COUNTRIES.keys())

        for country_name in countries:
            if country_name not in EUROPEAN_COUNTRIES:
                continue

            country_slug = EUROPEAN_COUNTRIES[country_name]
            url = f"{ODOO_PARTNERS_BASE_URL}/country/{country_slug}"
            partners = crawler._crawl_country_by_url(country_name, url)
            partner_urls.update(partners)

    # Debug: save HTML if requested
    if args.debug and not partner_urls:
        print("\n[*] Debug mode: Saving page HTML for inspection...")
        soup = crawler.fetch_page(f"{ODOO_PARTNERS_BASE_URL}?country_all=1")
        if soup:
            debug_file = OUTPUT_DIR / "debug_partners_page.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print(f"    Saved to: {debug_file}")

    if not partner_urls:
        print("No partners found.")
        return

    # Save
    output_path = crawler.save_partner_urls(partner_urls, args.output)

    # Summary
    print("\n" + "="*80)
    print("CRAWL COMPLETE")
    print("="*80)
    print(f"Total unique partner URLs: {len(partner_urls)}")
    print(f"Output file: {output_path}")

    # Per-country stats
    if crawler.country_partners:
        print("\nPartners per country:")
        for country, count in sorted(crawler.country_partners.items(), key=lambda x: -x[1]):
            print(f"  {country:25} {count:4} partners")

    print(f"\nNext step:")
    print(f"  python odoo_partner_references_crawler.py --partner-list {args.output}")
    print("="*80)


if __name__ == '__main__':
    main()
