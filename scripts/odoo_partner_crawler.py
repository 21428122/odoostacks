#!/usr/bin/env python3
"""
Odoo Partner Crawler
Crawls apps.odoo.com/partners to extract:
- Partner name, location, contact info
- Client references from case studies
- Industries served
- Join date / certification level
- Website and email
Saves to CSV for manual analysis.

Usage:
    python odoo_partner_crawler.py --top-partners 50
    python odoo_partner_crawler.py --search-keyword "QuickBooks"
"""

import requests
import csv
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

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

ODOO_PARTNERS_BASE_URL = "https://apps.odoo.com/partners"
ODOO_PARTNER_PROFILE_URL = "https://apps.odoo.com/apps/modules/{partner_slug}"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "partners_crawled"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ============================================================================
# MAIN CRAWLER
# ============================================================================

class OdooPartnerCrawler:
    """Crawl Odoo partner profiles and extract key information."""

    def __init__(self, timeout=10, delay_between_requests=1):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout
        self.delay = delay_between_requests
        self.partners = []

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_partner_info(self, partner_page: BeautifulSoup) -> Dict:
        """Extract information from a single partner page."""
        info = {
            'partner_name': None,
            'location': None,
            'website': None,
            'email': None,
            'phone': None,
            'certification': None,
            'employees': None,
            'industries': [],
            'clients': [],
            'join_date': None,
            'description': None,
        }

        # Partner name
        name_elem = partner_page.find('h1')
        if name_elem:
            info['partner_name'] = name_elem.get_text(strip=True)

        # Contact info from header section
        header = partner_page.find('div', class_='o_portal_header')
        if header:
            # Look for email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', header.get_text())
            if email_match:
                info['email'] = email_match.group()

            # Look for phone
            phone_match = re.search(r'\+?[\d\s\-\(\)]{7,}', header.get_text())
            if phone_match:
                info['phone'] = phone_match.group()

            # Website
            link = header.find('a', href=re.compile(r'http'))
            if link:
                info['website'] = link.get('href', '').strip()

        # Certification level
        cert_elem = partner_page.find(string=re.compile(r'(Gold|Silver|Bronze)\s+(Partner|Certification)'))
        if cert_elem:
            info['certification'] = cert_elem.get_text(strip=True)

        # Location
        location_match = re.search(r'(Location|Based in):\s*([^<\n]+)', partner_page.get_text())
        if location_match:
            info['location'] = location_match.group(2).strip()

        # Employee count
        employees_match = re.search(r'(\d+)\s*-\s*(\d+)\s*(employees|staff)', partner_page.get_text(), re.IGNORECASE)
        if employees_match:
            info['employees'] = f"{employees_match.group(1)}-{employees_match.group(2)}"

        # Industries served
        industries_section = partner_page.find(string=re.compile(r'Industries?', re.IGNORECASE))
        if industries_section:
            industries_container = industries_section.find_parent()
            if industries_container:
                industries_text = industries_container.get_text(strip=True)
                # Simple extraction
                info['industries'] = [ind.strip() for ind in re.split(r'[,;•]', industries_text) if ind.strip()][:5]

        # Case studies / Client references
        case_studies = partner_page.find_all(['article', 'div'], class_=re.compile(r'case|study|client|project', re.IGNORECASE))
        for case in case_studies[:3]:  # Max 3 case studies
            case_text = case.get_text(strip=True)[:100]
            if case_text:
                info['clients'].append(case_text)

        # Description / About
        about = partner_page.find(string=re.compile(r'About|Overview', re.IGNORECASE))
        if about:
            about_container = about.find_parent()
            if about_container:
                info['description'] = about_container.get_text(strip=True)[:200]

        return info

    def get_top_partners(self, limit: int = 50) -> List[Dict]:
        """Get top Odoo partners from the directory."""
        # Use known high-value partners directly
        print(f"Loading top Odoo partners (limit: {limit})...")
        partners_to_crawl = self._get_known_partners()
        partners_to_crawl = partners_to_crawl[:limit]
        print(f"Found {len(partners_to_crawl)} partners to crawl")
        return partners_to_crawl

    def _get_known_partners(self) -> List[Dict]:
        """Known high-value Odoo partners as fallback."""
        return [
            {'slug': 'emipro-technologies-pvt-ltd', 'name': 'Emipro Technologies'},
            {'slug': 'ksolves-india-ltd', 'name': 'Ksolves India'},
            {'slug': 'webkul-software-pvt-ltd', 'name': 'Webkul Software'},
            {'slug': 'browseinfo', 'name': 'BROWSEINFO'},
            {'slug': 'softhealer-technologies', 'name': 'Softhealer Technologies'},
            {'slug': 'almighty-consulting-solutions-pvt-ltd', 'name': 'Almighty Consulting'},
            {'slug': 'faOtools', 'name': 'faOtools'},
            {'slug': 'probuse-consulting-service-pvt-ltd', 'name': 'Probuse Consulting'},
            {'slug': 'pragmatic-solutions-pvt-ltd', 'name': 'Pragmatic Solutions'},
            {'slug': 'ventortech-solutions-pvt-ltd', 'name': 'VentorTech'},
            {'slug': 'techspawn-solutions-pvt-ltd', 'name': 'TechSpawn Solutions'},
            {'slug': 'dynamic-technologies-india', 'name': 'Dynamic Technologies'},
            {'slug': 'codepace-software', 'name': 'Codepace Software'},
            {'slug': 'openerp-experts', 'name': 'OpenERP Experts'},
            {'slug': 'ats-systems-pvt-ltd', 'name': 'ATS Systems'},
            {'slug': 'biztech-consultancy', 'name': 'BizTech Consultancy'},
            {'slug': 'erp-solutions-india', 'name': 'ERP Solutions India'},
            {'slug': 'accenture', 'name': 'Accenture'},
            {'slug': 'infosys', 'name': 'Infosys'},
            {'slug': 'tcs-india', 'name': 'TCS'},
        ]

    def crawl_partners(self, limit: int = 50) -> List[Dict]:
        """Main crawl routine."""
        partners_to_crawl = self.get_top_partners(limit)

        print(f"\nCrawling {len(partners_to_crawl)} partner profiles...")
        print("=" * 80)

        for idx, partner in enumerate(partners_to_crawl, 1):
            print(f"[{idx}/{len(partners_to_crawl)}] Crawling: {partner['name']}")

            # Construct partner profile URL
            partner_url = f"{ODOO_PARTNERS_BASE_URL}/{partner['slug']}"

            # Fetch and parse
            soup = self.fetch_page(partner_url)
            if soup:
                info = self.extract_partner_info(soup)
                info['url'] = partner_url
                info['slug'] = partner['slug']
                self.partners.append(info)
                print(f"  [+] Extracted: {info['partner_name'] or 'Unknown'}")
                print(f"    Location: {info['location'] or 'N/A'}")
                print(f"    Email: {info['email'] or 'N/A'}")
                if info['industries']:
                    print(f"    Industries: {', '.join(info['industries'][:3])}")
            else:
                print(f"  [-] Failed to fetch")

            # Respect rate limiting
            if idx < len(partners_to_crawl):
                time.sleep(self.delay)

        print("=" * 80)
        print(f"\nCrawl complete. Extracted {len(self.partners)} partners.\n")
        return self.partners

    def save_to_csv(self, filename: str = "odoo_partners.csv") -> Path:
        """Save extracted data to CSV."""
        output_path = OUTPUT_DIR / filename

        if not self.partners:
            print("No partner data to save")
            return output_path

        # Flatten data for CSV
        rows = []
        for partner in self.partners:
            rows.append({
                'Partner Name': partner['partner_name'] or 'Unknown',
                'URL': partner['url'],
                'Location': partner['location'] or 'N/A',
                'Website': partner['website'] or 'N/A',
                'Email': partner['email'] or 'N/A',
                'Phone': partner['phone'] or 'N/A',
                'Certification': partner['certification'] or 'N/A',
                'Employees': partner['employees'] or 'N/A',
                'Industries': '; '.join(partner['industries']) if partner['industries'] else 'N/A',
                'Client References': '; '.join(partner['clients']) if partner['clients'] else 'N/A',
                'Description': partner['description'] or 'N/A',
                'Crawled At': datetime.now().isoformat(),
            })

        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            writer.writeheader()
            writer.writerows(rows)

        print(f"[+] Saved {len(rows)} partners to: {output_path}")
        return output_path

    def save_to_json(self, filename: str = "odoo_partners.json") -> Path:
        """Save extracted data to JSON."""
        import json
        output_path = OUTPUT_DIR / filename

        # Convert lists and serialize
        json_data = []
        for partner in self.partners:
            partner_copy = partner.copy()
            partner_copy['crawled_at'] = datetime.now().isoformat()
            json_data.append(partner_copy)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"[+] Saved {len(json_data)} partners to: {output_path}")
        return output_path


# ============================================================================
# MANUAL FILTERS (For QB migration targeting)
# ============================================================================

def filter_partners_by_keyword(partners: List[Dict], keyword: str) -> List[Dict]:
    """Filter partners by keyword in name, description, or industries."""
    keyword_lower = keyword.lower()
    filtered = []

    for partner in partners:
        text_to_search = (
            f"{partner.get('partner_name', '')} "
            f"{partner.get('description', '')} "
            f"{' '.join(partner.get('industries', []))} "
            f"{' '.join(partner.get('clients', []))}"
        ).lower()

        if keyword_lower in text_to_search:
            filtered.append(partner)

    return filtered


def filter_qb_migration_partners(partners: List[Dict]) -> List[Dict]:
    """Filter for partners likely doing QB migrations."""
    qb_keywords = ['quickbooks', 'qb', 'migration', 'accounting', 'erp']
    relevant_partners = []

    for partner in partners:
        text_to_search = (
            f"{partner.get('partner_name', '')} "
            f"{partner.get('description', '')} "
            f"{' '.join(partner.get('industries', []))} "
            f"{' '.join(partner.get('clients', []))}"
        ).lower()

        if any(kw in text_to_search for kw in qb_keywords):
            relevant_partners.append(partner)

    return relevant_partners


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Crawl Odoo partner profiles and extract contact/client information'
    )
    parser.add_argument(
        '--top-partners',
        type=int,
        default=50,
        help='Number of top partners to crawl (default: 50)'
    )
    parser.add_argument(
        '--search-keyword',
        type=str,
        help='Filter partners by keyword (e.g., "QuickBooks")'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=1,
        help='Delay between requests in seconds (default: 1)'
    )
    parser.add_argument(
        '--output-format',
        choices=['csv', 'json', 'both'],
        default='both',
        help='Output format (default: both)'
    )

    args = parser.parse_args()

    # Initialize crawler
    crawler = OdooPartnerCrawler(delay_between_requests=args.delay)

    # Crawl partners
    partners = crawler.crawl_partners(limit=args.top_partners)

    # Filter if keyword provided
    if args.search_keyword:
        partners = filter_partners_by_keyword(partners, args.search_keyword)
        print(f"\nFiltered to {len(partners)} partners matching '{args.search_keyword}'")

    # Save results
    if args.output_format in ['csv', 'both']:
        csv_path = crawler.save_to_csv()
        print(f"CSV path: {csv_path}")

    if args.output_format in ['json', 'both']:
        json_path = crawler.save_to_json()
        print(f"JSON path: {json_path}")

    # Print summary
    print("\n" + "=" * 80)
    print("PARTNER CRAWL SUMMARY")
    print("=" * 80)
    print(f"Total partners crawled: {len(crawler.partners)}")
    if args.search_keyword:
        print(f"Partners matching '{args.search_keyword}': {len(partners)}")

    # Show QB migration partners if relevant
    qb_partners = filter_qb_migration_partners(crawler.partners)
    if qb_partners:
        print(f"\nPartners likely doing QB migrations: {len(qb_partners)}")
        for p in qb_partners[:5]:
            print(f"  • {p['partner_name']} ({p['location'] or 'N/A'})")


if __name__ == '__main__':
    main()
