#!/usr/bin/env python3
"""
Odoo Partner References Crawler
Extracts client references from Odoo partner pages.
For each partner, fetches their References section and extracts:
- Client company name
- Industry sector
- Description/case study
- Contact info if available

Usage:
    python odoo_partner_references_crawler.py --partner-url "https://www.odoo.com/partners/closyss-technologies-llp-13254479"
    python odoo_partner_references_crawler.py --partner-list partners.txt
    python odoo_partner_references_crawler.py --partner-id "closyss-technologies-llp-13254479"
"""

import requests
import csv
import re
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

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
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "partner_references"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ============================================================================
# MAIN CRAWLER
# ============================================================================

class OdooPartnerReferencesCrawler:
    """Extract client references from Odoo partner pages."""

    def __init__(self, timeout=10, delay_between_requests=1):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout
        self.delay = delay_between_requests
        self.references = []

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_partner_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract partner name and basic info."""
        partner_info = {
            'partner_name': None,
            'partner_url': url,
            'references': []
        }

        # Try to extract partner name from page
        h1 = soup.find('h1')
        if h1:
            partner_info['partner_name'] = h1.get_text(strip=True)

        return partner_info

    def extract_references(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all client references from partner page."""
        references = []

        # Strategy: Find blocks that match the pattern:
        # 1. Company Name
        # 2. Industry (contains " / ")
        # 3. Description (paragraph)

        # Get all text blocks
        all_divs = soup.find_all('div')

        for div in all_divs:
            text = div.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            # Look for reference patterns
            i = 0
            while i < len(lines):
                line = lines[i]

                # Check if next line looks like an industry (contains " / ")
                if i + 1 < len(lines):
                    next_line = lines[i + 1]

                    # Industry pattern: "Word / Word" (e.g., "Finance / Legal / Insurance")
                    if ' / ' in next_line and next_line.count('/') <= 3:
                        # This line is likely a company name
                        company_name = line

                        # Validate company name
                        if (len(company_name) > 5 and len(company_name) < 150 and
                            company_name[0].isupper() and
                            not any(nav_word in company_name.lower() for nav_word in
                                   ['skip', 'menu', 'sign', 'search', 'try it', 'download', 'follow'])):

                            industry = next_line
                            description = 'N/A'

                            # Look ahead for description
                            if i + 2 < len(lines):
                                desc_line = lines[i + 2]
                                if len(desc_line) > 20:
                                    description = desc_line

                            ref = {
                                'company_name': company_name,
                                'industry': industry,
                                'description': description,
                            }
                            references.append(ref)
                            i += 2

                i += 1

        # Deduplicate by company name
        seen = set()
        unique_refs = []
        for ref in references:
            key = ref['company_name'].lower()
            if key not in seen:
                seen.add(key)
                unique_refs.append(ref)

        return unique_refs

    def _parse_reference_section(self, section) -> Optional[Dict]:
        """Parse a single reference/case study section."""
        ref = {
            'company_name': None,
            'industry': None,
            'description': None,
        }

        # Try to find company name (usually first heading in section)
        name_elem = section.find(['h3', 'h4', 'h2', 'strong', 'b'])
        if name_elem:
            ref['company_name'] = name_elem.get_text(strip=True)

        # Try to find industry
        industry_elem = section.find(string=re.compile(r'/'))  # Often formatted as "Retail / Wholesale"
        if industry_elem:
            ref['industry'] = industry_elem.get_text(strip=True)
        else:
            # Try finding by common patterns
            text = section.get_text()
            industry_match = re.search(r'([A-Z][a-z]+\s*/\s*[A-Z][a-z]+(?:\s*/\s*[A-Z][a-z]+)?)', text)
            if industry_match:
                ref['industry'] = industry_match.group(1)

        # Try to find description (paragraph text)
        desc_elem = section.find('p')
        if desc_elem:
            ref['description'] = desc_elem.get_text(strip=True)[:200]
        else:
            # Use all text minus the name
            all_text = section.get_text(strip=True)
            if ref['company_name']:
                all_text = all_text.replace(ref['company_name'], '', 1)
            if all_text:
                ref['description'] = all_text[:200]

        return ref if ref['company_name'] else None

    def crawl_partner(self, partner_url: str) -> Dict:
        """Crawl a single partner page and extract references."""
        print(f"Crawling: {partner_url}")

        soup = self.fetch_page(partner_url)
        if not soup:
            print(f"  [-] Failed to fetch")
            return None

        # Extract partner info
        partner_info = self.extract_partner_info(soup, partner_url)

        # Extract references
        references = self.extract_references(soup)
        partner_info['references'] = references

        print(f"  [+] Extracted: {partner_info['partner_name'] or 'Unknown'}")
        print(f"      Found {len(references)} client references")

        if references:
            for i, ref in enumerate(references[:3], 1):
                print(f"      {i}. {ref['company_name']} ({ref['industry']})")

        return partner_info

    def crawl_partners_from_list(self, partner_urls: List[str]) -> List[Dict]:
        """Crawl multiple partners."""
        results = []

        print(f"Crawling {len(partner_urls)} partners...")
        print("=" * 80)

        for idx, url in enumerate(partner_urls, 1):
            result = self.crawl_partner(url)
            if result:
                results.append(result)

            # Rate limiting
            if idx < len(partner_urls):
                time.sleep(self.delay)

        print("=" * 80)
        print(f"Crawl complete. Extracted {len(results)} partners with references.\n")
        return results

    def save_to_csv(self, results: List[Dict], filename: str = "partner_references.csv") -> Path:
        """Save extracted references to CSV."""
        output_path = OUTPUT_DIR / filename

        rows = []
        for partner in results:
            for ref in partner.get('references', []):
                rows.append({
                    'Partner Name': partner.get('partner_name', 'Unknown'),
                    'Partner URL': partner.get('partner_url', 'N/A'),
                    'Client Company': ref.get('company_name', 'Unknown'),
                    'Industry': ref.get('industry', 'N/A'),
                    'Description': ref.get('description', 'N/A'),
                    'Extracted At': datetime.now().isoformat(),
                })

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            writer.writeheader()
            writer.writerows(rows)

        print(f"[+] Saved {len(rows)} client references to: {output_path}")
        return output_path

    def save_to_json(self, results: List[Dict], filename: str = "partner_references.json") -> Path:
        """Save extracted references to JSON."""
        import json
        output_path = OUTPUT_DIR / filename

        json_data = []
        for partner in results:
            json_data.append({
                'partner_name': partner.get('partner_name'),
                'partner_url': partner.get('partner_url'),
                'references': partner.get('references', []),
                'extracted_at': datetime.now().isoformat()
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"[+] Saved to: {output_path}")
        return output_path

    def generate_client_database(self, results: List[Dict], filename: str = "all_clients_db.csv") -> Path:
        """Generate deduplicated client database for outreach."""
        output_path = OUTPUT_DIR / filename

        # Deduplicate clients by name
        clients = {}
        for partner in results:
            for ref in partner.get('references', []):
                client_name = ref.get('company_name', '').strip()
                if client_name:
                    if client_name not in clients:
                        clients[client_name] = {
                            'company_name': client_name,
                            'industries': set(),
                            'referred_by_partners': [],
                            'description': ref.get('description', ''),
                        }
                    clients[client_name]['industries'].add(ref.get('industry', 'N/A'))
                    if partner.get('partner_name') not in clients[client_name]['referred_by_partners']:
                        clients[client_name]['referred_by_partners'].append(partner.get('partner_name'))

        # Convert sets to strings and create rows
        rows = []
        for client_name, data in sorted(clients.items()):
            rows.append({
                'Client Company': client_name,
                'Industries': '; '.join(sorted(data['industries'])),
                'Referred By Partners': '; '.join(data['referred_by_partners']),
                'Partner Count': len(data['referred_by_partners']),
                'Description': data['description'][:100] if data['description'] else 'N/A',
            })

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            writer.writeheader()
            writer.writerows(rows)

        print(f"[+] Generated client database: {len(rows)} unique clients")
        print(f"    File: {output_path}")
        return output_path


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_partner_urls_from_file(filepath: str) -> List[str]:
    """Load partner URLs from a text file (one URL per line)."""
    if not Path(filepath).exists():
        print(f"Error: {filepath} not found")
        return []

    with open(filepath, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and line.startswith('http')]

    return urls


def format_partner_url(partner_id: str) -> str:
    """Convert partner ID to full URL."""
    if partner_id.startswith('http'):
        return partner_id
    return f"{ODOO_PARTNERS_BASE_URL}/{partner_id}"


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract client references from Odoo partner pages'
    )
    parser.add_argument('--partner-url', type=str,
                       help='Single partner URL to crawl')
    parser.add_argument('--partner-id', type=str,
                       help='Partner ID (e.g., "closyss-technologies-llp-13254479")')
    parser.add_argument('--partner-list', type=str,
                       help='File with list of partner URLs (one per line)')
    parser.add_argument('--delay', type=int, default=1,
                       help='Delay between requests in seconds (default: 1)')

    args = parser.parse_args()

    # Determine which partners to crawl
    urls_to_crawl = []

    if args.partner_url:
        urls_to_crawl = [args.partner_url]
    elif args.partner_id:
        urls_to_crawl = [format_partner_url(args.partner_id)]
    elif args.partner_list:
        urls_to_crawl = load_partner_urls_from_file(args.partner_list)
    else:
        print("Error: Provide --partner-url, --partner-id, or --partner-list")
        parser.print_help()
        return

    if not urls_to_crawl:
        print("No valid URLs to crawl")
        return

    # Initialize crawler
    crawler = OdooPartnerReferencesCrawler(delay_between_requests=args.delay)

    # Crawl
    results = crawler.crawl_partners_from_list(urls_to_crawl)

    if not results:
        print("No data extracted")
        return

    # Export
    print("\nExporting results...")
    crawler.save_to_csv(results)
    crawler.save_to_json(results)
    crawler.generate_client_database(results)

    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Partners crawled: {len(results)}")
    total_refs = sum(len(p.get('references', [])) for p in results)
    print(f"Total client references: {total_refs}")
    print(f"\nOutput directory: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
