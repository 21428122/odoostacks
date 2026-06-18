#!/usr/bin/env python3
"""
Filter client references for European companies.
Detects European companies by:
- Company name patterns (GmbH, S.A., Ltd., B.V., etc.)
- Industry mentions of European countries
- Text content matching European patterns
"""

import csv
import json
from pathlib import Path
from typing import List, Dict

EUROPEAN_COUNTRIES = [
    'Germany', 'France', 'Italy', 'Spain', 'UK', 'United Kingdom', 'Belgium',
    'Netherlands', 'Austria', 'Switzerland', 'Poland', 'Portugal', 'Greece',
    'Sweden', 'Norway', 'Denmark', 'Finland', 'Ireland', 'Hungary', 'Czech',
    'Romania', 'Bulgaria', 'Croatia', 'Slovenia', 'Slovakia', 'Lithuania',
    'Latvia', 'Estonia', 'Cyprus', 'Luxembourg', 'Malta', 'Iceland'
]

EUROPEAN_SUFFIXES = [
    'gmbh', 'sarl', 's.a.', 's.a.r.l.', 'ltd', 'b.v.', 'a.s.', 'sp.z.o.o',
    'srl', 'société', 'gesellschaft', 'company', 'ag', 'oy', 'ab', 'nv'
]

EU_COUNTRIES_SHORT = [
    'DE', 'FR', 'IT', 'ES', 'UK', 'GB', 'BE', 'NL', 'AT', 'CH', 'PL',
    'PT', 'GR', 'SE', 'NO', 'DK', 'FI', 'IE', 'HU', 'CZ', 'RO', 'BG',
    'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'CY', 'LU', 'MT', 'IS'
]


def is_likely_european(company_name: str, industry: str, description: str) -> bool:
    """Check if a company is likely European based on name/industry/description."""

    text_to_search = f"{company_name} {industry} {description}".lower()

    # Check for European country names
    for country in EUROPEAN_COUNTRIES:
        if country.lower() in text_to_search:
            return True

    # Check for country codes (DE, FR, etc. in parentheses or as code)
    for code in EU_COUNTRIES_SHORT:
        if f' {code}' in text_to_search or f'({code})' in text_to_search or f'-{code}' in text_to_search:
            return True

    # Check for European business suffixes
    company_lower = company_name.lower()
    for suffix in EUROPEAN_SUFFIXES:
        if company_lower.endswith(suffix):
            return True
        if f' {suffix} ' in f' {company_lower} ':
            return True

    # Check for European cities/regions mentioned
    european_cities = [
        'london', 'paris', 'berlin', 'amsterdam', 'brussels', 'zurich',
        'warsaw', 'prague', 'budapest', 'athens', 'madrid', 'barcelona',
        'lisbon', 'stockholm', 'copenhagen', 'dublin', 'rome', 'vienna',
        'dublin', 'geneva', 'bern', 'hamburg', 'munich', 'cologne',
        'lyon', 'marseille', 'milan', 'italy'
    ]

    for city in european_cities:
        if city in text_to_search:
            return True

    return False


def filter_european_clients(input_csv: str, output_csv: str = None) -> None:
    """Filter client database for European companies."""

    input_path = Path(input_csv)
    if not input_path.exists():
        print(f"Error: {input_csv} not found")
        return

    if output_csv is None:
        output_csv = input_path.parent / "european_clients_db.csv"

    print(f"Reading: {input_csv}")

    # Read input
    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Total clients: {len(rows)}")

    # Filter for European
    european_clients = []
    for row in rows:
        company_name = row.get('Client Company', '')
        industry = row.get('Industry', '')
        description = row.get('Description', '')

        if is_likely_european(company_name, industry, description):
            european_clients.append(row)

    print(f"European clients found: {len(european_clients)}")

    # Write output
    if european_clients:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=european_clients[0].keys())
            writer.writeheader()
            writer.writerows(european_clients)

        print(f"[+] Saved to: {output_csv}\n")

        # Show sample
        print("Sample European clients:")
        for i, client in enumerate(european_clients[:10], 1):
            print(f"{i}. {client.get('Client Company')} ({client.get('Industry')})")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Filter client database for European companies')
    parser.add_argument('--input', type=str, default='data/partner_references/all_clients_db.csv',
                       help='Input CSV file')
    parser.add_argument('--output', type=str, help='Output CSV file')

    args = parser.parse_args()

    filter_european_clients(args.input, args.output)


if __name__ == '__main__':
    main()
