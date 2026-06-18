# Market Persona Sweep — Final Decision (2026-06-18)

## Method
10 parallel agents: 7 buyer personas + 3 B2B app store scanners.
All agents independently identified their "fastest dollar" app.

## Ranked Top 5

| # | App | Competition | Price | Build | Days to $1 |
|---|-----|-------------|-------|-------|------------|
| 1 | DATEV Buchungsstapel Export Companion | ZERO | €299-799 | 2 wk | 14d |
| 2 | Busy Accounting Migrator (India pharma) | ZERO | $72-96 | 3 wk | 14d |
| 3 | MYOB AccountRight Migrator (AU/NZ) | ZERO | $99-199 partner license | 3 wk | 18d |
| 4 | QB Desktop CSV Migrator (UK/CA) | THIN $79-129 slot empty | $99 | 3 wk | 21d |
| 5 | Zoho Books India GST Migrator | THIN India-GST gap | $79-99 | 3 wk | 14d |

## #1 Pick: DATEV Buchungsstapel Export Companion

**Why:**
- Developer already has EU brand (eu_einvoicing_tracker live at €19)
- ZERO competition on Odoo marketplace
- Hans Mueller alone: 8 clients × €299 = €2,392 from one advisor
- Every German Odoo company needs monthly Buchungsstapel export — permanent recurring need
- Pure CSV (cp1252, semicolon), DATEV format fully documented
- 2 week build vs 3 weeks for India alternatives
- €299 = 4x revenue per sale vs Busy at $75

**v1 Feature Set (2 weeks):**
1. Date range selector (month/quarter/year)
2. Odoo journal entries → DATEV Buchungsstapel column mapping
   - Umsatz (amount), Soll/Haben (debit/credit), Konto, Gegenkonto
   - Buchungstext (narration), Datum (date), Belegdatum, Belegnummer
3. Export to DATEV-compatible CSV
   - Encoding: cp1252 (Windows-1252 — DATEV requirement)
   - Delimiter: semicolon
   - Header row: DATEV format v700
4. SKR03/SKR04 account number prefix dropdown
5. Wizard under Accounting > Reporting > DATEV Export

**Exclude from v1:**
- Import/migration (export only)
- Automatic account mapping
- DATEV Unternehmen Online upload
- Multi-company support

**Pricing:** €299 one-time OPL-1. No free tier.

**Channel:**
- German Odoo forum (odoo.com/de_DE/forum)
- LinkedIn: search "Steuerberater Odoo" + "DATEV Odoo"
- DACH Odoo User Group
- Post in German-language announcement: "Buchungsstapel Export für Odoo 18 Community"

## #2 Pick: Busy Accounting Migrator

**Why second:**
- India home market advantage
- ZERO competition
- 1M+ Busy users (pharma/FMCG India)
- Forced buyer: GST e-invoicing 2.0 mandate
- $72-96 per install
- 3 week build (Busy ODBC documented)

**v1 Feature Set:**
1. Connect to Busy ODBC (Busy exposes localhost ODBC port)
2. Import: Ledgers/Parties → res.partner
3. Import: Stock groups/items → product.template (with batch/lot support)
4. Import: Vouchers/transactions → account.move
5. GST field mapping (GSTIN, HSN codes, tax rates)
6. Batch/lot → stock.lot with expiry dates

**Price:** ₹5,999 ($72) one-time

## Key Insight From All 10 Agents
Every persona independently converged on: **migrator apps are the fastest path to first dollar.**
- Forced buyers (mandate/EOL/price hike) close 3-5x faster than discretionary
- Channel buyers (accountants/advisors) multiply each sale by 8-25x
- CSV-based = no govt API certification overhead
- Zero competition = #1 ranking in marketplace search by default
