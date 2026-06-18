#!/usr/bin/env python3
"""
Partner Analysis & Filtering
Post-processes crawled Odoo partner data to identify QB migration opportunities.
Generates outreach lists, contact databases, and priority rankings.

Usage:
    python partner_analysis.py --input data/partners_crawled/odoo_partners.json
    python partner_analysis.py --segment qb-ready --output outreach_list.csv
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

QB_MIGRATION_KEYWORDS = [
    'quickbooks', 'qb', 'accounting software', 'erp migration',
    'migration', 'accounting', 'finance', 'bookkeeping',
    'small business', 'smb', 'implementation'
]

READY_INDUSTRIES = [
    'accounting', 'bookkeeping', 'finance', 'professional services',
    'consulting', 'manufacturing', 'distribution', 'wholesale',
    'trading', 'import/export'
]

# Certification levels (in order of value)
CERT_LEVELS = {
    'Gold': 3,
    'Silver': 2,
    'Bronze': 1,
    None: 0
}

DATA_DIR = Path(__file__).parent.parent / "data" / "partners_crawled"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "partner_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# ANALYSIS ENGINE
# ============================================================================

class PartnerAnalyzer:
    """Analyze partner data for QB migration opportunities."""

    def __init__(self, partners_json_path: str):
        """Load partner data from JSON."""
        self.partners = self._load_partners(partners_json_path)
        self.scored_partners = []

    def _load_partners(self, json_path: str) -> List[Dict]:
        """Load partners from JSON file."""
        if not Path(json_path).exists():
            print(f"Error: {json_path} not found")
            return []

        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def score_qb_migration_fit(self, partner: Dict) -> Tuple[int, Dict]:
        """
        Score a partner for QB migration suitability.
        Returns: (score: 0-100, reason_dict)
        """
        score = 0
        reasons = {
            'keyword_match': 0,
            'industry_match': 0,
            'certification': 0,
            'employee_count': 0,
            'contact_quality': 0
        }

        # 1. Keyword matching (30 points)
        text_to_search = (
            f"{partner.get('partner_name', '')} "
            f"{partner.get('description', '')} "
            f"{' '.join(partner.get('industries', []))} "
            f"{' '.join(partner.get('clients', []))}"
        ).lower()

        keyword_matches = sum(1 for kw in QB_MIGRATION_KEYWORDS if kw in text_to_search)
        keyword_score = min(30, keyword_matches * 5)
        reasons['keyword_match'] = keyword_score
        score += keyword_score

        # 2. Industry focus (20 points)
        industry_matches = 0
        for industry in partner.get('industries', []):
            if any(ready_ind in industry.lower() for ready_ind in READY_INDUSTRIES):
                industry_matches += 1

        industry_score = min(20, industry_matches * 5)
        reasons['industry_match'] = industry_score
        score += industry_score

        # 3. Certification level (20 points)
        cert = partner.get('certification')
        cert_score = CERT_LEVELS.get(cert, 0) * 10
        reasons['certification'] = cert_score
        score += cert_score

        # 4. Employee count - mid-market sweet spot (15 points)
        employees = partner.get('employees')
        if employees:
            try:
                range_str = str(employees)
                if '-' in range_str:
                    min_emp, max_emp = map(int, range_str.split('-'))
                    avg_emp = (min_emp + max_emp) / 2
                    # Sweet spot: 20-200 employees
                    if 20 <= avg_emp <= 200:
                        reasons['employee_count'] = 15
                        score += 15
                    elif 10 <= avg_emp <= 500:
                        reasons['employee_count'] = 10
                        score += 10
            except:
                pass

        # 5. Contact quality (15 points)
        has_email = bool(partner.get('email'))
        has_phone = bool(partner.get('phone'))
        has_website = bool(partner.get('website'))

        contact_score = (has_email * 5) + (has_phone * 5) + (has_website * 5)
        reasons['contact_quality'] = contact_score
        score += contact_score

        return min(100, score), reasons

    def analyze_partners(self) -> List[Dict]:
        """Score all partners."""
        self.scored_partners = []

        for partner in self.partners:
            score, reasons = self.score_qb_migration_fit(partner)
            partner_scored = partner.copy()
            partner_scored['qb_score'] = score
            partner_scored['scoring_breakdown'] = reasons
            self.scored_partners.append(partner_scored)

        # Sort by score descending
        self.scored_partners.sort(key=lambda p: p['qb_score'], reverse=True)
        return self.scored_partners

    def get_qb_ready_partners(self, min_score: int = 60) -> List[Dict]:
        """Get partners with sufficient QB migration fit."""
        return [p for p in self.scored_partners if p['qb_score'] >= min_score]

    def get_high_value_partners(self, min_cert_level: int = 2) -> List[Dict]:
        """Get certified Gold/Silver partners."""
        filtered = []
        for partner in self.scored_partners:
            cert = partner.get('certification')
            if cert and CERT_LEVELS.get(cert, 0) >= min_cert_level:
                filtered.append(partner)
        return filtered

    def export_outreach_list(self, partners: List[Dict], filename: str) -> Path:
        """Export simplified outreach list with contact info."""
        output_path = OUTPUT_DIR / filename

        rows = []
        for idx, partner in enumerate(partners, 1):
            rows.append({
                'Rank': idx,
                'Partner': partner.get('partner_name', 'Unknown'),
                'Location': partner.get('location', 'N/A'),
                'Email': partner.get('email', 'N/A'),
                'Phone': partner.get('phone', 'N/A'),
                'Website': partner.get('website', 'N/A'),
                'Industries': '; '.join(partner.get('industries', [])[:3]),
                'Certification': partner.get('certification', 'N/A'),
                'QB Score': f"{partner.get('qb_score', 0):.0f}",
                'Score Breakdown': json.dumps(partner.get('scoring_breakdown', {})),
            })

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            writer.writeheader()
            writer.writerows(rows)

        print(f"✓ Exported {len(rows)} partners to: {output_path}")
        return output_path

    def export_contact_database(self, partners: List[Dict], filename: str) -> Path:
        """Export full contact database for CRM import."""
        output_path = OUTPUT_DIR / filename

        rows = []
        for partner in partners:
            rows.append({
                'partner_name': partner.get('partner_name'),
                'location': partner.get('location'),
                'email': partner.get('email'),
                'phone': partner.get('phone'),
                'website': partner.get('website'),
                'certification': partner.get('certification'),
                'industries': json.dumps(partner.get('industries', [])),
                'clients': json.dumps(partner.get('clients', [])[:3]),
                'qb_score': partner.get('qb_score'),
                'url': partner.get('url'),
            })

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            writer.writeheader()
            writer.writerows(rows)

        print(f"✓ Exported {len(rows)} contacts to: {output_path}")
        return output_path

    def export_summary_report(self, filename: str = "partner_analysis_report.txt") -> Path:
        """Generate summary analysis report."""
        output_path = OUTPUT_DIR / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ODOO PARTNER ANALYSIS REPORT\n")
            f.write("QB→Odoo Migrator Customer Acquisition\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Analysis Date: {datetime.now().isoformat()}\n")
            f.write(f"Total Partners Analyzed: {len(self.partners)}\n\n")

            # Score distribution
            f.write("SCORE DISTRIBUTION\n")
            f.write("-" * 40 + "\n")
            ranges = [
                (90, 100, "Excellent Fit"),
                (70, 89, "Good Fit"),
                (50, 69, "Moderate Fit"),
                (30, 49, "Low Fit"),
                (0, 29, "Poor Fit")
            ]

            for min_score, max_score, label in ranges:
                count = sum(1 for p in self.scored_partners
                           if min_score <= p['qb_score'] <= max_score)
                pct = (count / len(self.scored_partners) * 100) if self.scored_partners else 0
                f.write(f"{label:20} ({min_score}-{max_score}): {count:4} partners ({pct:5.1f}%)\n")

            f.write("\n")

            # Top 10 partners
            f.write("TOP 10 QB-READY PARTNERS\n")
            f.write("-" * 40 + "\n")
            for idx, partner in enumerate(self.scored_partners[:10], 1):
                f.write(f"{idx}. {partner.get('partner_name', 'Unknown')}\n")
                f.write(f"   Location: {partner.get('location', 'N/A')}\n")
                f.write(f"   Score: {partner.get('qb_score', 0):.0f}/100\n")
                f.write(f"   Email: {partner.get('email', 'N/A')}\n")
                f.write(f"   Industries: {', '.join(partner.get('industries', [])[:2])}\n\n")

            f.write("\n")

            # Certification breakdown
            f.write("CERTIFICATION BREAKDOWN\n")
            f.write("-" * 40 + "\n")
            cert_counts = {}
            for partner in self.partners:
                cert = partner.get('certification', 'Uncertified')
                cert_counts[cert] = cert_counts.get(cert, 0) + 1

            for cert, count in sorted(cert_counts.items(), key=lambda x: -x[1]):
                pct = (count / len(self.partners) * 100) if self.partners else 0
                f.write(f"{cert:20}: {count:4} partners ({pct:5.1f}%)\n")

            f.write("\n")

            # Industry distribution
            f.write("TOP INDUSTRIES SERVED\n")
            f.write("-" * 40 + "\n")
            industry_counts = {}
            for partner in self.partners:
                for industry in partner.get('industries', []):
                    industry_counts[industry] = industry_counts.get(industry, 0) + 1

            for industry, count in sorted(industry_counts.items(), key=lambda x: -x[1])[:10]:
                f.write(f"{industry:30}: {count:3}\n")

        print(f"✓ Generated report: {output_path}")
        return output_path


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze partner data for QB migration opportunities')
    parser.add_argument('--input', type=str, default='data/partners_crawled/odoo_partners.json',
                       help='Input JSON file with partner data')
    parser.add_argument('--min-score', type=int, default=60,
                       help='Minimum QB fit score for outreach (default: 60)')
    parser.add_argument('--top-n', type=int, default=100,
                       help='Export top N partners (default: 100)')

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = PartnerAnalyzer(args.input)

    print(f"Loading partners from {args.input}...")
    if not analyzer.partners:
        print("No partners loaded. Did you run the crawler first?")
        return

    print(f"Loaded {len(analyzer.partners)} partners\n")

    # Analyze
    print("Analyzing partners for QB migration fit...")
    scored = analyzer.analyze_partners()
    print(f"✓ Scored all partners\n")

    # Export results
    qb_ready = analyzer.get_qb_ready_partners(min_score=args.min_score)
    top_n = qb_ready[:args.top_n]

    print("Exporting results...")
    analyzer.export_outreach_list(top_n, "qb_migration_outreach_list.csv")
    analyzer.export_contact_database(top_n, "partner_contacts_db.csv")
    analyzer.export_summary_report()

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Total partners analyzed: {len(analyzer.partners)}")
    print(f"Partners with score >= {args.min_score}: {len(qb_ready)}")
    print(f"Top {args.top_n} exported for outreach")
    print(f"\nOutput directory: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
