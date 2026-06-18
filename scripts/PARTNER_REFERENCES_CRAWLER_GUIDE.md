# Partner References Crawler Guide
## Extract Client Data from Odoo Partner Pages

This crawler extracts client references from Odoo partner profile pages, giving you a database of companies already using Odoo through each partner.

---

## Quick Start

### Single Partner

```bash
python odoo_partner_references_crawler.py --partner-url "https://www.odoo.com/partners/closyss-technologies-llp-13254479"
```

**Output:**
- `data/partner_references/partner_references.csv` — All client references
- `data/partner_references/all_clients_db.csv` — Deduplicated client database

### Multiple Partners

Create a file `partners.txt` with one URL per line:

```txt
https://www.odoo.com/partners/closyss-technologies-llp-13254479
https://www.odoo.com/partners/emipro-technologies-pvt-ltd-3
https://www.odoo.com/partners/ksolves-india-ltd-7
```

Then run:

```bash
python odoo_partner_references_crawler.py --partner-list partners.txt
```

### By Partner ID

If you have just the ID part of the URL:

```bash
python odoo_partner_references_crawler.py --partner-id "closyss-technologies-llp-13254479"
```

---

## What Gets Extracted

For each client reference:

| Field | Example | Use |
|-------|---------|-----|
| Client Company | ACCUSPAN CALGAS INDIA PRIVATE LIMITED | Company name for outreach |
| Industry | Utilities / Energy / Water supply | Find QB-using sectors |
| Description | Multi-line case study snippet | Understand use case |
| Partner Name | Closyss Technologies | Track which partner referred |

---

## Output Files

### 1. partner_references.csv
Raw client references with partner attribution.

```
Partner Name | Client Company | Industry | Description
Closyss Technologies | ACCUSPAN CALGAS | Utilities / Energy | [case study]
Closyss Technologies | Allied Safety | Wholesale / Retail | [case study]
```

**Use:** Track which partner brought in each client

### 2. all_clients_db.csv
Deduplicated list of all unique clients across all partners.

```
Client Company | Industries | Referred By Partners | Partner Count
ACCUSPAN CALGAS | Utilities / Energy | Closyss | 1
InBody India | Health / Pharma | Closyss, Emipro | 2
```

**Use:** Outreach targets + partner multi-referral tracking

---

## Example Workflow

### Step 1: Gather Partner URLs

Browse https://www.odoo.com/partners and find Gold/Silver partners. Save URLs:

```bash
echo "https://www.odoo.com/partners/emipro-technologies-pvt-ltd-3" >> partners.txt
echo "https://www.odoo.com/partners/ksolves-india-ltd-7" >> partners.txt
echo "https://www.odoo.com/partners/closyss-technologies-llp-13254479" >> partners.txt
```

### Step 2: Crawl All Partners

```bash
python odoo_partner_references_crawler.py --partner-list partners.txt --delay 2
```

This extracts all client references and creates:
- `partner_references.csv` (1000+ client references)
- `all_clients_db.csv` (deduped list for outreach)

### Step 3: Use Client Database for Outreach

Open `all_clients_db.csv` in Excel → Filter by industry:
- Manufacturing (QB likely)
- Finance / Legal / Insurance (QB likely)
- Wholesale / Retail (QB likely)

These are hot prospects already using Odoo through a partner.

### Step 4: Personalized Outreach

For each client with 50+ employees:

```
Subject: QB→Odoo Migration Opportunity

Hi [Client Name],

I noticed you're using Odoo through [Partner Name] (per their case studies).
Many companies running QuickBooks in parallel are migrating to Odoo.

We've built an automated QB→Odoo migrator that handles:
- 2-3 year historical data
- Multi-location setups
- Custom GL accounts

If you're considering QB exit, let's chat.

[Your contact]
```

---

## Advanced Options

### Custom Delay (avoid rate limiting)

```bash
python odoo_partner_references_crawler.py --partner-list partners.txt --delay 3
```

### Output Formats

The crawler always produces both CSV and JSON. Use JSON if you want to process further in Python:

```python
import json

with open('data/partner_references/partner_references.json') as f:
    data = json.load(f)

for partner in data:
    print(f"{partner['partner_name']}: {len(partner['references'])} clients")
```

---

## Filtering Clients by Industry

Industries found in the references:

**High QB-Migration Probability:**
- Manufacturing / Maintenance
- Finance / Legal / Insurance
- Wholesale / Retail
- Accounting / Finance

**Medium Probability:**
- E-commerce
- Professional Services
- Construction

**Lower Probability:**
- NGO
- Government
- Education

Filter in Excel using these keywords.

---

## Tips

1. **Start Small:** Crawl 3-5 partners first to test
   ```bash
   python odoo_partner_references_crawler.py --partner-id "closyss-technologies-llp-13254479"
   ```

2. **Use CSV for Excel:** Easy to filter/sort in spreadsheet
   ```bash
   # Open all_clients_db.csv in Excel → AutoFilter
   ```

3. **Combine Multiple Crawls:** Run on different partner sets, then merge CSVs
   ```bash
   # Create partners_batch1.txt, partners_batch2.txt
   # Run separately, merge results later
   ```

4. **Find More Partners:** https://www.odoo.com/partners
   - Filter by Country: India
   - Filter by Expertise: Implementation, Accounting
   - Save URLs

---

## Integration with QB→Odoo Migrator Launch

This crawler feeds your Channel A customer acquisition:

1. **Week 1-2:** Crawl 10-20 key partners → 500-1000 client references
2. **Week 3-4:** Filter by industry (manufacturing, finance, retail)
3. **Week 5-8:** Send personalized cold outreach emails to filtered clients
4. **Target:** 20 customers by Oct 4

---

## Example Partner List

Good starting partners (known high performers):

```txt
https://www.odoo.com/partners/emipro-technologies-pvt-ltd-3
https://www.odoo.com/partners/ksolves-india-ltd-7
https://www.odoo.com/partners/webkul-software-pvt-ltd-12
https://www.odoo.com/partners/browseinfo-20
https://www.odoo.com/partners/pragmatic-solutions-pvt-ltd-9
https://www.odoo.com/partners/closyss-technologies-llp-13254479
```

---

**Last Updated:** 2026-06-17
