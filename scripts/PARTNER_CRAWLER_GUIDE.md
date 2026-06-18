# Odoo Partner Crawler Guide
## Channel A: Partner Referral Customer Acquisition

This guide explains how to use the partner crawler to identify and reach out to Odoo partners for QB→Odoo migrator referrals.

---

## Overview

The crawler strategy uses **manual web scraping** (not AI/LLMs) to minimize token usage while gathering high-quality partner intelligence. The workflow:

1. **Crawl** → Extract partner profiles from apps.odoo.com/partners
2. **Analyze** → Score partners by QB migration fit (keywords, industries, certification)
3. **Segment** → Identify high-value partners for outreach
4. **Reach Out** → Use Channel A email templates to request referrals

---

## Installation

### Requirements
- Python 3.8+
- `requests` and `beautifulsoup4` (auto-installed on first run)

### Setup

```bash
# Navigate to scripts directory
cd c:\Users\InBody\Projects\odoostacks\scripts

# First run will auto-install dependencies
python odoo_partner_crawler.py --top-partners 10
```

---

## Step 1: Crawl Partner Profiles

### Basic Crawl (Top 50 partners)

```bash
python odoo_partner_crawler.py --top-partners 50
```

**Output:**
- `data/partners_crawled/odoo_partners.csv` — tabular format for Excel
- `data/partners_crawled/odoo_partners.json` — structured data for analysis

### Advanced Options

```bash
# Crawl 100 partners with custom delay
python odoo_partner_crawler.py --top-partners 100 --delay 2

# Output only CSV (faster)
python odoo_partner_crawler.py --top-partners 50 --output-format csv

# Search for specific partners
python odoo_partner_crawler.py --top-partners 100 --search-keyword "accounting"
```

### What Gets Extracted

For each partner:
- ✓ Name, location, website
- ✓ Email, phone number
- ✓ Certification level (Gold/Silver/Bronze)
- ✓ Industries served (accounting, finance, manufacturing, etc.)
- ✓ Client case study snippets
- ✓ Employee count
- ✓ Partner profile description
- ✓ Join date / certification level

---

## Step 2: Analyze & Score Partners

After crawling, analyze the data to identify best-fit partners:

```bash
python partner_analysis.py --input data/partners_crawled/odoo_partners.json --min-score 60
```

**This generates three outputs:**

1. **qb_migration_outreach_list.csv** 
   - Ranked by QB fit score
   - Contact info + industries
   - Ready for manual email campaign

2. **partner_contacts_db.csv**
   - Full contact database
   - Import into CRM or mail merge tool

3. **partner_analysis_report.txt**
   - Summary statistics
   - Score distribution
   - Certification breakdown
   - Top 10 partners by fit

### Scoring Formula

Each partner gets a QB Fit Score (0-100):

| Factor | Points | How It Works |
|--------|--------|--------------|
| Keywords | 30 | "QuickBooks," "accounting," "migration," "ERP" |
| Industries | 20 | Targets: accounting, finance, manufacturing, consulting |
| Certification | 20 | Gold=20, Silver=10, Bronze=0 (more credible) |
| Employee Count | 15 | Sweet spot: 20-200 employees (mid-market) |
| Contact Quality | 15 | Has email, phone, website |

**Example:**
- Emipro Technologies: 92/100 (Gold cert, accounting keywords, 100+ employees, all contacts)
- BROWSEINFO: 78/100 (Silver cert, "ERP implementation" keywords, partial contacts)
- Random IT Shop: 25/100 (no QB keywords, no contact info)

### Filtering by Score

```bash
# High-confidence partners only
python partner_analysis.py --min-score 75

# Include moderate prospects
python partner_analysis.py --min-score 50

# Get top 50 partners
python partner_analysis.py --min-score 0 --top-n 50
```

---

## Step 3: Prepare Outreach Lists

The `qb_migration_outreach_list.csv` is designed for manual email campaigns:

| Column | Use |
|--------|-----|
| Rank | Priority order for outreach |
| Partner | Company name (for personalization) |
| Email | Direct contact (from profile) |
| Location | Reference in greeting |
| Industries | Why they're relevant (accounting, finance, etc.) |
| QB Score | Optional: mention in follow-up ("You scored 78/100 for QB migration fit") |

### Example Email Template (from SALES_OUTREACH_PLAYBOOK.md)

```
Subject: QB→Odoo Migrator - Partnership Opportunity

Hi [Partner Name],

We've noticed you're a [Certification] Odoo Partner serving [Industry] clients—many of whom use QuickBooks.

We're launching a QB→Odoo Migrator (web-to-prem) that automates multi-year data migrations with 99% accuracy. Early partners are earning ₹500-₹1200 per referral.

Interested in a 15-min call to discuss how your QB-using customers could benefit?

[Channel A email from playbook]
```

---

## Step 4: Track Outreach & Responses

After exporting, use `partner_contacts_db.csv` to:

1. **Send emails** (Gmail, Outlook, or mail merge tool)
2. **Track responses** in a spreadsheet or CRM
3. **Schedule follow-ups** (3 days, 7 days, 14 days)
4. **Record**: Who expressed interest, partnership terms, referrals sent

---

## Troubleshooting

### "Could not fetch partners directory"

The crawler falls back to a hardcoded list of known partners. This is normal if apps.odoo.com structure changes.

**Fix:** Manually add more partners to `_get_known_partners()` in `odoo_partner_crawler.py`

```python
{'slug': 'partner-slug', 'name': 'Partner Name'},
```

### "No emails found"

Some partner profiles don't display contact info on the public page. Check the partner's website directly using the `Website` column.

### "Very slow crawling"

Increase the delay between requests:
```bash
python odoo_partner_crawler.py --top-partners 50 --delay 3
```

Or reduce scope:
```bash
python odoo_partner_crawler.py --top-partners 20  # Faster
```

---

## Integration with Sales Playbook

This crawler directly supports **Channel A: Partner Referral** from SALES_OUTREACH_PLAYBOOK.md:

1. **Discover Phase**: Crawl → Analyze → Export outreach list
2. **Outreach Phase**: Send Channel A email template
3. **Close Phase**: Track responses, negotiate terms, send referral tracker
4. **Onboard Phase**: Share partner dashboard, affiliate payouts

---

## Typical Campaign Timeline

| Week | Activity | Output |
|------|----------|--------|
| W1 | Crawl 200 partners | JSON + CSV files |
| W1 | Analyze & score | Outreach list (top 100 partners) |
| W2-3 | Manual email campaign | 50-100 emails sent |
| W3-4 | Follow-ups | 10-20 interested partners |
| W5-8 | Close partnerships | 3-5 active referral partners |

---

## Next Steps

After partners are onboarded:
- Share referral tracker template (from playbook)
- Set up referral payouts (₹500-₹1200 per referral)
- Provide partner with marketing collateral
- Monitor referral pipeline weekly

---

## Questions?

Refer to:
- **SALES_OUTREACH_PLAYBOOK.md** — Full Channel A strategy & email templates
- **TOP_5_PRODUCTS_CORRECTED.md** — QB→Odoo Migrator details
- **scripts/odoo_partner_crawler.py** — Code comments for customization

---

**Last Updated:** 2026-06-17
**Strategy Alignment:** QB→Odoo Migrator MVP (Weeks 1-16)
**Expected First 20 Customers:** October 4, 2026
