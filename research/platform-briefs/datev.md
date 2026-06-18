# Platform Brief — DATEV

> The single most important platform brief in this set — because of the 2027 supercycle. DATEV is not just German accounting software. It is the *infrastructure* used by ~40,000 German tax advisors (Steuerberater) to keep the books of ~2.5M German businesses. You don't migrate FROM DATEV — you migrate to Odoo while keeping DATEV-format data flowing to the Steuerberater. **The product is import-once + export-forever.**

---

## Section 1 — Identity

**Vendor:** DATEV eG, Nuremberg, Germany. Founded 1966. **Legal form: eingetragene Genossenschaft (eG) — a cooperative owned by its ~40,000 member tax advisors.** This is structurally different from QB/Sage/Zoho. DATEV doesn't optimize for end-user SMB experience; it optimizes for the Steuerberater workflow.

**Revenue ~€1.4B (2024). Headcount ~9,000.** Not VC-backed, not for-profit in the conventional sense — surplus returned to members.

**Why this matters for migration:** end-user customer doesn't choose DATEV — their Steuerberater chose it for them. Migration battles must respect this. The Steuerberater is the gatekeeper.

**Product lines (DATEV's catalogue is sprawling — these are the migration-relevant ones):**

| Product | Audience | Migration relevance |
|---|---|---|
| DATEV Kanzlei-Rechnungswesen | Steuerberater's office bookkeeping tool | Source of records — the Steuerberater holds the data |
| DATEV Mittelstand Faktura mit Rechnungswesen | SME accounting + invoicing | SME-side product, sometimes self-managed |
| DATEV Mittelstand Faktura compact / classic / comfort | SME tiers | Same product line |
| DATEV Unternehmen online | SaaS portal for SME ↔ Steuerberater document exchange | Source of pre-accounted scans |
| DATEV Buchungsdatenservice | Cloud booking data service | Modern exchange path |
| DATEV Lohn und Gehalt | Payroll | Separate scope (typical) |
| DATEV LODAS | Payroll for outsourced clients | Separate |
| DATEV-Konto-Online (Bank API) | Bank feeds | Bank data flow |
| DATEV Auftragswesen next | Order management add-on | Sometimes used |

**The KEY format: "DATEV Buchungsstapel" (booking batch)**
- A CSV file with a strict 13-row header + transactional data rows
- Every German bookkeeper knows this format
- Universal exchange standard between SME software and Steuerberater software
- **Producing valid Buchungsstapel CSVs from Odoo is the #1 deliverable of our migration tool**

**Pricing (DATEV doesn't publish public pricing — partner-quoted only, estimates):**
- DATEV Mittelstand Faktura compact: ~€30-50/mo
- DATEV Mittelstand Faktura classic/comfort: ~€60-150/mo
- DATEV Unternehmen online (per company): ~€10-30/mo
- Plus Steuerberater fees (the dominant cost) — €200-2,000/mo depending on company size

**Installed base:**
- ~40,000 Steuerberater firms (the channel)
- ~2.5M businesses indirectly (their clients)
- ~250,000 businesses with their own DATEV software products
- Total DATEV ecosystem touches ~⅔ of all German SMEs

**Market segments:**
- Almost exclusively Germany
- Small presence in Austria (similar tax system)
- Effectively nowhere else

**Geographic footprint:**
- Tier 1: Germany (95%+ of presence)
- Tier 2: Austria
- Outside DACH: negligible

## Section 2 — User Psychology

**Why people use DATEV (end-user perspective):**
1. **Their Steuerberater requires it.** This is the dominant reason. End-user often has no say.
2. Compliance certainty — DATEV format is what HMRC-equivalent (Finanzamt) audits use
3. Tax filings (UStVA, ZM, Anlage EÜR, Bilanz) flow seamlessly
4. Bank data flows in via DATEV-Konto-Online
5. GoBD compliance (German bookkeeping principles) built-in

**Why people use DATEV (Steuerberater perspective):**
1. It's the cooperative they're a member of
2. Every other Steuerberater uses it — universal exchange
3. Practice management features
4. Tax software (DATEV ESt, DATEV USt, etc.) integrates natively
5. Audit-trail and Festschreibung (period locking) compliant with GoBD

**Why people leave (the end-user revolt):**
1. **UI is brutal** — DATEV's interfaces are notoriously 1990s
2. **Slow** — month-end batch culture, not real-time
3. **Mobile / modern access** — basically absent
4. **Multi-entity / international consolidation** — DATEV is monolingual-monolocational
5. **E-commerce / Shopify / Amazon integration** — third-party only
6. **Manufacturing / MRP** — nonexistent
7. **CRM** — nonexistent
8. **Project profitability** — primitive
9. **Real-time financial dashboards** — month-end-only culture
10. **International expansion** — DATEV doesn't follow you abroad
11. **The 2027 e-invoicing mandate** — DATEV adapting but bolt-on; modern systems are native
12. **Generational change** — Founders aged 30-50 don't want their CRM in Salesforce, ERP in Odoo, accounting frozen in 1980s DATEV

**The 2027 trigger (THE big one):**

**Germany B2B mandatory e-invoicing timeline:**
- **Jan 1, 2025:** All German businesses must be ABLE TO RECEIVE structured e-invoices (XRechnung XML or ZUGFeRD PDF/A-3 with embedded XML)
- **Jan 1, 2027:** All German businesses with >€800k annual revenue must ISSUE structured e-invoices for B2B
- **Jan 1, 2028:** All German businesses must issue (no revenue threshold)

**Why this matters:** DATEV is rolling out e-invoicing support but as bolt-on additions to their existing batch culture. Odoo with `l10n_de` + `l10n_de_xrechnung` / ZUGFeRD modules is e-invoicing-native — issue invoices that auto-generate XRechnung XML in real-time. This is the moment German SMEs leak from DATEV.

**What they fear about migrating:**
1. Steuerberater rejects new system (THE #1 fear)
2. UStVA monthly VAT filing won't tie
3. SKR03/SKR04 chart of accounts not preserved
4. GoBD compliance broken (audit risk)
5. Buchungsstapel exchange with Steuerberater stops working

**Who decides:**
- Founder + Steuerberater (joint decision)
- The Steuerberater has near-veto power
- For >50 employee companies, CFO drives but still must satisfy Steuerberater

**Sales implication: this is the platform where the migrator's ongoing export companion is mandatory.** Without DATEV Buchungsstapel export from Odoo, no Steuerberater will agree.

## Section 3 — Data Model

DATEV's data model is built around the **SKR (Standardkontenrahmen)** chart of accounts and the **Buchungsstapel** (booking batch) exchange format.

### SKR Chart Variants

DATEV maintains multiple standard charts; customer is on one:

| Chart | Audience | Account number length |
|---|---|---|
| **SKR03** | Industry/traditional (most common) | 4 digits (extendable to 6/7/8) |
| **SKR04** | International/modern | 4 digits (extendable) |
| SKR07 | Personal services | rare |
| SKR11 | Non-profit | niche |
| SKR14 | Agriculture | niche |
| SKR45 | Hospital/healthcare | niche |
| SKR49 | Banking | niche |
| SKR70-99 | Various specialized | rare |

**SKR03 vs SKR04 — the structural difference:**

SKR03 follows German tradition (Income > Expense > Assets > Liabilities organization):
```
0001-0999  Anlagevermögen (Fixed Assets)
1000-1999  Finanz- und Privat-Konten (Cash, Bank, Personal)
2000-2999  Abgrenzung (Accruals/Deferrals)
3000-3999  Wareneingang (Goods Received) + Material
4000-4999  Betriebliche Erträge (Revenues)
5000-5999  Betriebliche Aufwendungen (Materials/Costs)
6000-6999  Betriebliche Aufwendungen (Operating Expenses)
7000-7999  Weitere Aufwendungen (Other Expenses)
8000-8999  Erlöse (Sales Revenue)
9000-9999  Eröffnungs- und Schlussbilanz, statistical (Opening/Closing, statistical)
```

SKR04 follows international (IFRS-ish) order (Assets > Liabilities > Equity > Revenue > Expense):
```
0001-1499  Anlagevermögen (Fixed Assets)
1500-1999  Umlaufvermögen (Current Assets)
2000-2999  Eigenkapital (Equity)
3000-3999  Verbindlichkeiten (Liabilities)
4000-4999  Erträge (Revenue)
5000-7999  Aufwendungen (Expenses)
9000+      Closing / statistical
```

**Both have ~700-1500 standard accounts.** DATEV publishes annual SKR updates.

### Personenkonten Ranges (subsidiary ledgers)

Customer and vendor accounts use specific number ranges:

| Range | Type | Notes |
|---|---|---|
| **10000-69999** | Debitoren (Customers) | Auto-numbered |
| **70000-99999** | Kreditoren (Vendors) | Auto-numbered |

These ranges are sacred — embedded in every Buchungsstapel transaction. Cannot renumber without breaking integrations.

### The Buchungsstapel (Booking Batch) Format

The standard CSV exchange format. Strict structure:

**Header row 1 (metadata, 32 fields):**
```
"EXTF";700;21;"Buchungsstapel";11;...;"Beraternummer";"Mandantennummer";...
```

**Header row 2 (column names, 116 fields):**
```
Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Kurs;...;Konto;Gegenkonto;BU-Schlüssel;...
```

**Data rows: 1 row per transaction line.**

The 116 columns include:
| Column | Description |
|---|---|
| 1: Umsatz | Amount (German format: `1234,56`) |
| 2: Soll/Haben-Kz | "S" or "H" (Debit/Credit indicator) |
| 3: WKZ Umsatz | Currency code (e.g., "EUR") |
| 4: Kurs | Exchange rate |
| 5: Basis-Umsatz | Base currency amount |
| 6: WKZ Basis | Base currency code |
| 7: Konto | Account number (the booking account) |
| 8: Gegenkonto | Contra account (the other side) |
| 9: BU-Schlüssel | VAT/posting key (e.g., "8" for 19% VAT) |
| 10: Belegdatum | Document date (DDMM format!) |
| 11: Belegfeld 1 | Document number / reference (usually invoice number) |
| 12: Belegfeld 2 | Secondary reference (often customer-internal ref) |
| 13: Skonto | Cash discount |
| 14: Buchungstext | Booking text (description) |
| ... | (102 more fields) |
| 37: Kost1-Kostenstelle | Cost centre 1 |
| 38: Kost2-Kostenstelle | Cost centre 2 |
| 39: Kost-Menge | Cost quantity |
| ... | EU VAT ID, fixed-asset fields, document GUID, etc. |

**Encoding:** Windows-1252 (cp1252), NOT UTF-8. CRLF line endings. Semicolon delimiter. German number format (1.234,56).

**This format is what every Steuerberater expects monthly.** Our Odoo companion must produce valid Buchungsstapel CSVs.

### Other DATEV Entities

| DATEV Object | Odoo Target | Notes |
|---|---|---|
| Mandant (client company) | `res.company` | Mandantennummer is the key |
| Berater (advisor) | external — not migrated | The Steuerberater's identity |
| Sachkonto (GL account) | `account.account` | Map via l10n_de chart |
| Personenkonto (subsidiary) | `res.partner` | Range determines customer/vendor |
| BU-Schlüssel (posting/VAT key) | `account.tax` | Lookup table (see 4.4) |
| Steuerschlüssel (tax key) | embedded in BU-Schlüssel | Same |
| Kostenstelle (Kost1) | `account.analytic.account` (Plan A) | |
| Kostenträger (Kost2) | `account.analytic.account` (Plan B) | |
| Belegnummer | `account.move.name` or `ref` | Direct |
| EU-Steuer-USt-ID | partner `vat` | Direct |
| Anlagegüter (Fixed Assets) | `account.asset` | Needs `account_asset` |
| Lohnkonten (Payroll accounts) | `account.account` | But payroll DATA out of scope |
| OPOS (Offene Posten) | `account.partial.reconcile` | Open item tracking |

## Section 4 — Hidden Complexity (the gotcha catalogue)

### 4.1 The Steuerberater Is the Real Customer (Strategic, Not Technical)

- **What's happening:** The end-user wants to migrate to Odoo. The Steuerberater needs to keep filing taxes, which means receiving Buchungsstapel-format data monthly.
- **What breaks:** Without an ongoing DATEV-format export from Odoo, the Steuerberater refuses → migration aborted.
- **Mitigation:** The migrator is TWO products bundled — `import_from_datev` (one-shot) + `export_to_datev` (ongoing monthly export companion). The second is more valuable than the first.

### 4.2 SKR03 vs SKR04 Detection

- **What DATEV does:** Customer is on ONE SKR. Headers in Buchungsstapel files indicate which.
- **What breaks:** If you map to the wrong Odoo l10n_de chart, every account is off-by-thousands.
- **Mitigation:** Pre-flight: detect SKR03 vs SKR04 from header metadata or by asking. Install `l10n_de_skr03` or `l10n_de_skr04` accordingly.

### 4.3 Account Number Length Variability

- **What DATEV does:** Default is 4-digit accounts, but customer can extend to 5, 6, 7, or 8 digits per company. Personenkonten use 5-digit by default.
- **What breaks:** Migrator assumes 4-digit and breaks on 6-digit customers.
- **Mitigation:** Detect from Buchungsstapel header (`Sachkontenlänge` field, position 17). Configure Odoo accordingly.

### 4.4 BU-Schlüssel (Posting/VAT Keys)

- **What DATEV does:** A single 1-2-digit BU-Schlüssel encodes BOTH the VAT rate AND the posting characteristic. Examples:
  - `0` = No VAT
  - `1` = Tax-exempt, intra-EU goods
  - `2` = Tax-exempt, intra-EU services
  - `3` = Tax-exempt, reverse charge
  - `8` = 19% VAT input on revenue
  - `9` = 7% VAT input on revenue
  - `18` = 19% VAT input on cost
  - `19` = 7% VAT input on cost
  - `21` = Intra-EU acquisition 19%
  - `29` = Non-EU import 19%
  - `40` = Special handling (cash discount adjustment)
  - And combinations like `8` + `40` = 19% VAT + cash discount
- **What breaks:** Naive mapping of BU = tax rate misses posting characteristic. UStVA reports break.
- **Mitigation:** Build comprehensive BU-Schlüssel → Odoo `account.tax` lookup table (~50 codes). Use l10n_de tax codes.

### 4.5 GoBD Compliance (Mandatory)

- **What DATEV does:** German law (GoBD — Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern, Aufzeichnungen und Unterlagen in elektronischer Form) requires:
  - Records cannot be altered after Festschreibung (period closing)
  - Sequential numbering (gap-less)
  - All changes audit-logged with user + timestamp
  - 10-year retention
- **What breaks:** Odoo by default allows journal entry edits in draft. GoBD violation if not configured.
- **Mitigation:** Configure Odoo for GoBD: `account.journal` set to `restrict_mode_hash_table=True` (blockchain-style hash chain). Enable mail.thread audit on `account.move`. Document compliance for Steuerberater.

### 4.6 Festschreibung (Period Locking)

- **What DATEV does:** Closing a period (typically monthly after UStVA filing) locks all transactions in that period. Edits forbidden.
- **What breaks:** Migrator must respect this — cannot back-date imports into closed periods.
- **Mitigation:** Pull period locking state per company. In Odoo, set `account.tax.lock.date` and `account.fiscalyear.lock.date` accordingly. Customer's go-forward operations respect these locks.

### 4.7 Buchungsstapel CSV Format Quirks

- **What DATEV does:**
  - **Encoding:** Windows-1252 (cp1252), NOT UTF-8 — Umlauts (Ä Ö Ü ä ö ü ß) encoded in cp1252
  - **Delimiter:** semicolon `;`
  - **Decimal:** comma `,` not period `.` (e.g., `1234,56`)
  - **Thousands:** period `.` (e.g., `1.234,56`)
  - **Date:** German format `TTMM` or `TTMMJJJJ` (e.g., `1503` for March 15)
  - **Line ending:** CRLF (Windows)
  - **Header row 1:** 32 fields, semicolon-separated, quoted strings
  - **Header row 2:** 116 column names
- **What breaks:** Python's default UTF-8 silently corrupts Umlauts. Naive parsers split on commas. Date parsing returns wrong month.
- **Mitigation:** Open files with `encoding='cp1252'`, `newline='\r\n'`. Parse numbers manually (replace `.` then replace `,` with `.`). Date parse with `%d%m` or `%d%m%Y`. **[See memory: cp1252 is a known constraint in this repo.]**

### 4.8 Personenkonten Range Conventions

- **What DATEV does:** Customers in 10000-69999, Vendors in 70000-99999. These numbers are embedded in every transaction's Konto or Gegenkonto field.
- **What breaks:** Renumbering breaks transaction references. Mapping by Konto field requires knowing the range conventions.
- **Mitigation:** Preserve Personenkonto-Nr as `res.partner.ref`. Build lookup: Konto range → res.partner.

### 4.9 Mandantennummer + Beraternummer

- **What DATEV does:** Every Buchungsstapel file has Berater-Nr (advisor identity, 4-7 digits) and Mandant-Nr (client identity, 1-5 digits within the Berater's portfolio).
- **What breaks:** Identifying which company's data is in a Buchungsstapel CSV requires reading these numbers from the header.
- **Mitigation:** Migrator pre-flight reads header, confirms with user "this file is for Berater 12345, Mandant 100 — is that correct?"

### 4.10 OPOS (Offene Posten — Open Items)

- **What DATEV does:** Outstanding customer/vendor balances tracked at invoice-level (not just net balance per partner). Each open invoice has its own reference, due date, and partial payment history.
- **What breaks:** Net-balance migration loses invoice-level open-item tracking.
- **Mitigation:** Migrate per-invoice open items. Use `account.move.line` with payment reconciliation state preserved.

### 4.11 Cost Centre Allocation (Kost1, Kost2)

- **What DATEV does:** Each transaction line can have Kost1 (primary cost centre, e.g., department), Kost2 (cost object, e.g., project), and Kost-Menge (cost quantity for unit costing).
- **What breaks:** Two-axis dimensional tracking. Pre-17 Odoo has one analytic axis.
- **Mitigation:** Require Odoo 17+. Create `account.analytic.plan` for "Kostenstelle" and "Kostenträger." Map via `analytic_distribution`.

### 4.12 UStVA, ZM, Anlage EÜR Reporting

- **What DATEV does:**
  - **UStVA (Umsatzsteuer-Voranmeldung):** monthly/quarterly VAT pre-declaration to Finanzamt
  - **ZM (Zusammenfassende Meldung):** EU recapitulative statement for intra-EU B2B sales/services
  - **Anlage EÜR:** cash-basis P&L attachment (for small businesses opting cash-basis)
  - **Bilanz:** annual balance sheet
- **What breaks:** Odoo's German tax reports must produce matching outputs.
- **Mitigation:** Install `l10n_de_reports` (Odoo Enterprise) or community equivalent. Configure tax codes to feed UStVA correctly. ZM for intra-EU sales requires EU VAT IDs on partners.

### 4.13 EÜR vs Bilanz (Cash-Basis vs Accrual)

- **What DATEV does:** Small businesses can opt for EÜR (Einnahmen-Überschuss-Rechnung — cash-basis P&L) instead of accrual Bilanz. Different account usage, different reporting.
- **What breaks:** If migrator assumes accrual but customer is on EÜR, accruals are wrong.
- **Mitigation:** Detect accounting method from company master. Configure Odoo `res.company.fiscal_position_id` accordingly.

### 4.14 The 2027 e-Invoicing Mandate (XRechnung / ZUGFeRD)

- **What DATEV does:** Adapting — adding e-invoicing modules but as bolt-on to batch-culture workflow.
- **What's mandatory:**
  - **Receipt: Jan 1, 2025** — all German businesses must accept structured e-invoices
  - **Issuance: Jan 1, 2027** — businesses with >€800k revenue must issue structured e-invoices for B2B
  - **Issuance: Jan 1, 2028** — all businesses (no threshold)
- **What formats are allowed:**
  - **XRechnung** — pure XML, government-mandated for B2G already
  - **ZUGFeRD** — PDF/A-3 with embedded XML (hybrid format)
  - **Peppol** — for cross-border within EU
- **What breaks:** SMEs on DATEV will receive PDFs from their suppliers post-2025; they need to process XML embedded data. Pre-2027, they're not required to issue structured — but post-2027, they MUST.
- **Mitigation:** Position Odoo migration as "e-invoicing ready Day 1." Install `l10n_de_xrechnung` and ZUGFeRD modules. Build the companion that ensures every Odoo invoice issued auto-generates both PDF and XML.

### 4.15 DATEV ASCII Format (Legacy)

- **What DATEV does:** Pre-2018, used a fixed-width ASCII format alongside Buchungsstapel CSV. Some old installations still use it.
- **What breaks:** Modern migrators don't parse it.
- **Mitigation:** For customers with pre-2018 data, support ASCII format parsing. Document as legacy.

### 4.16 Anlagebuchhaltung (Fixed Asset Accounting)

- **What DATEV does:** Separate fixed asset register with depreciation schedules, AfA tables (German depreciation tax law standard tables), purchase invoices linked.
- **What breaks:** Without explicit asset migration, depreciation schedules lost.
- **Mitigation:** Use `account_asset` module (Odoo Enterprise) or community equivalent. Pull asset records separately; recreate depreciation schedules.

### 4.17 Bank Feeds via DATEV-Konto-Online

- **What DATEV does:** Banks send transaction data daily to DATEV; customer's bookkeeping auto-pulls. The Steuerberater accesses pre-categorized data.
- **What breaks:** After migration, bank feed must move to Odoo (PSD2-based via providers like Finapi, FinTecSystems, or direct bank connections).
- **Mitigation:** Document bank feed transition; recommend `account_online_synchronization` or PSD2 connector.

## Section 5 — Export Surface

### DATEV Buchungsstapel CSV

- **Format:** as detailed in Section 3
- **How to get it:** Steuerberater exports from DATEV Kanzlei-Rechnungswesen for the period. Customer requests this.
- **Coverage:** Complete posting data (header + lines). No attachments, no master data beyond what's posted-to.
- **Encoding:** cp1252, semicolon, CRLF, German number/date format
- **The de facto interchange standard** — Steuerberater knows how to produce it

### DATEV XML Schnittstelle (DATEV-XML)

- **Format:** Modern XML version of Buchungsstapel
- **Used for:** newer DATEV integrations, especially DATEV Buchungsdatenservice
- **Schema:** published by DATEV (Schnittstellen-Entwicklerhandbuch)
- **Easier to parse** than CSV but customer/Steuerberater must opt to use it

### DATEV-Konto-Online API

- **What it is:** Cloud upload API for booking data and document exchange
- **Access:** requires DATEV Schnittstellen-Zertifizierung (certification program for ISVs)
- **Cost:** partnership fee + per-transaction or annual subscription
- **Use case:** ongoing automatic upload from Odoo → DATEV → Steuerberater
- **Strategic value:** if we get certified, our companion product is "Odoo writes directly to Steuerberater's DATEV" — premium positioning

### Stammdaten Export (Master Data)

- Customers, vendors, accounts, cost centres each exportable separately
- Used in combination with Buchungsstapel for full migration

### DATEV Unternehmen online (the SaaS portal)

- Customer scans/uploads documents (invoices, bills) → portal pre-categorizes → Steuerberater accesses
- API exists (`datev.de/online`) but restricted access
- Most useful for ongoing document flow, not historical migration

### What You Can NEVER Get Out

1. The Steuerberater's working papers and notes
2. DATEV Lohn payroll data without separate access path
3. Custom report definitions
4. User permission / role history within DATEV
5. Sync conflict logs
6. DATEV's internal master data (Kostenrahmen variants we don't have license for)

### Practical Migration Paths

**Option A — Buchungsstapel CSV (the realistic path):**
- Customer asks Steuerberater for Buchungsstapel CSV export for migration period (typically last 2-5 fiscal years)
- Migrator parses CSV with proper cp1252 + German format handling
- Builds Odoo account.move records
- **No DATEV partnership required**

**Option B — DATEV-XML (cleaner, similar effort):**
- Steuerberater exports DATEV XML instead of CSV
- Easier to parse but customer/Steuerberater must opt in
- **No partnership required**

**Option C — DATEV-Konto-Online API (premium path):**
- We become a DATEV-zertifizierter Schnittstellen-Partner
- Direct cloud-to-cloud data exchange
- Steuerberater pre-approves
- **Requires DATEV certification — high barrier, high moat**

**Recommendation:** start with Option A. If our migration volume justifies it (>20 migrations/year), pursue Option C for the agency-partner SKU.

## Section 6 — Odoo Mapping (key tables)

### BU-Schlüssel → Odoo Tax mapping

| BU | Description | Odoo l10n_de Tax |
|---|---|---|
| 0 | No VAT | No Tax |
| 1 | Tax-exempt EU intra-community goods | EU-frei Lieferung |
| 2 | Tax-exempt EU intra-community services | EU-frei sonstige Leistung |
| 3 | Tax-exempt reverse charge (§13b) | RC Eingang |
| 5 | 16% VAT (historical, pre-2007) | — historical |
| 8 | 19% VAT output revenue | USt 19% Ausgang |
| 9 | 7% VAT output revenue (reduced) | USt 7% Ausgang |
| 11 | 19% VAT building services reverse charge | RC §13b |
| 13 | 19% VAT scrap/waste reverse charge | RC §13b Schrott |
| 18 | 19% VAT input cost | VSt 19% Eingang |
| 19 | 7% VAT input cost (reduced) | VSt 7% Eingang |
| 21 | EU intra-community acquisition 19% | i.g. Erwerb 19% |
| 22 | EU intra-community acquisition 7% | i.g. Erwerb 7% |
| 29 | Non-EU import 19% | Einfuhr 19% |
| 30 | Non-EU import 7% | Einfuhr 7% |
| 40 | Posting characteristic flag (cash discount adjustment) | Modifier |
| 91 | Tax-exempt revenue | Steuerfreie Erlöse |
| 94 | Tax-exempt EU services received | EU sonst. Leist. |

(Full table has ~50 codes; build comprehensive lookup as part of migrator.)

### SKR03 sample mapping (Sachkonten → account.account)

| SKR03 | Description | Odoo `account.account` type |
|---|---|---|
| 1000 | Kasse (Cash) | Bank and Cash |
| 1200 | Bank | Bank and Cash |
| 1400 | Forderungen aus L.u.L. | Receivable (control) |
| 1576 | Vorsteuer 19% | Current Asset (VAT receivable) |
| 1771 | Umsatzsteuer 19% | Current Liability (VAT payable) |
| 1800 | Privatentnahmen | Equity |
| 1810 | Privatsteuern | Equity |
| 2000 | Außerordentliche Aufwendungen | Other Expense |
| 3300 | Wareneingang 19% Vorsteuer | Cost of Revenue |
| 3400 | Wareneingang 7% Vorsteuer | Cost of Revenue |
| 4400 | Erlöse 19% USt | Income |
| 4300 | Erlöse 7% USt | Income |
| 4900 | Sonstige Erlöse | Income |
| 6300 | Werbekosten | Expense |
| 6310 | Geschenke abzugsfähig | Expense |
| 6800 | Bürobedarf | Expense |
| 6805 | Telefon | Expense |
| 7000 | Anlagenabgänge | Other Expense |
| 8000+ | (in SKR03, more income accounts) | Income |
| 9000 | Eröffnungsbilanz | Equity (opening) |

(Customer's full chart imported via `l10n_de_skr03` then individual accounts mapped.)

### Buchungsstapel line → account.move mapping

| Buchungsstapel column | Odoo target | Transform |
|---|---|---|
| Umsatz | line `debit` or `credit` (depending on Soll/Haben-Kz) | parse `1.234,56` → 1234.56 |
| Soll/Haben-Kennzeichen | determines debit vs credit | "S" = debit, "H" = credit |
| WKZ Umsatz | `currency_id` | ISO 4217 lookup |
| Kurs | `currency_rate` | If non-EUR |
| Konto | one side of `account.move.line` | account.code lookup |
| Gegenkonto | other side of `account.move.line` | account.code lookup |
| BU-Schlüssel | `tax_ids` on the affected line | lookup table |
| Belegdatum | `date` | DDMMYYYY → ISO |
| Belegfeld 1 | `ref` (invoice number / reference) | Direct |
| Belegfeld 2 | `name` (secondary reference) | Direct |
| Buchungstext | `name` on line | Direct |
| Kost1-Kostenstelle | `analytic_distribution` (Kost1 plan) | |
| Kost2-Kostenstelle | `analytic_distribution` (Kost2 plan) | |
| Kost-Menge | `quantity` for unit costing | |
| EU-Mitgliedstaat USt-IdNr | partner `vat` | Direct |
| Stammdaten | various | Linked via lookup |

### Reconciliation queries

```sql
-- Trial Balance reconciliation with DATEV
SELECT a.code, a.name,
       SUM(CASE WHEN l.debit > 0 THEN l.debit ELSE 0 END) AS soll,
       SUM(CASE WHEN l.credit > 0 THEN l.credit ELSE 0 END) AS haben,
       SUM(l.balance) AS saldo
FROM account_move_line l
JOIN account_account a ON a.id = l.account_id
WHERE l.parent_state = 'posted' AND l.date <= '{cutover}'
GROUP BY a.code, a.name
ORDER BY a.code;

-- UStVA reconciliation per VAT code
SELECT t.name AS bu_schluessel,
       SUM(line.balance) AS umsatz
FROM account_move_line line
JOIN account_tax_repartition_line rep ON rep.id = line.tax_repartition_line_id
JOIN account_tax t ON t.id = rep.tax_id
JOIN account_move m ON m.id = line.move_id
WHERE m.date BETWEEN '{period_start}' AND '{period_end}'
GROUP BY t.name
ORDER BY t.name;

-- Offene Posten (open items) per customer/vendor
SELECT p.name AS partner, p.ref AS personenkonto,
       m.name AS belegnummer,
       m.date AS belegdatum,
       m.amount_residual AS saldo
FROM account_move m
JOIN res_partner p ON p.id = m.partner_id
WHERE m.move_type IN ('out_invoice','in_invoice')
  AND m.amount_residual > 0
ORDER BY p.ref, m.date;
```

## Section 7 — Migration Risk Register

| Rank | Failure | Probability | Customer impact | Mitigation |
|---|---|---|---|---|
| 1 | **Steuerberater refuses to accept Odoo output** | High | Migration aborted | Build & demo Buchungsstapel export companion BEFORE signing migration |
| 2 | cp1252 encoding mishandled (Umlauts corrupted) | High | Silent data corruption | Always use `encoding='cp1252'` explicitly |
| 3 | German number format parsed wrong | High | Amounts wrong by 100-1000× | Custom parser: replace `.` then `,`→`.` |
| 4 | SKR03/SKR04 misdetection | Medium | Entire CoA wrong | Pre-flight: detect from header or ask |
| 5 | BU-Schlüssel → tax mismapping | High | UStVA filing wrong | Comprehensive lookup table, ~50 codes |
| 6 | Period locking (Festschreibung) violated | Low | GoBD violation | Set `account.fiscalyear.lock.date` |
| 7 | Personenkonten ranges miscategorised | Medium | Customer vs vendor confusion | Range-based detection |
| 8 | Cost Centre Kost1/Kost2 collapsed | Medium | Mgmt reports wrong | Require Odoo 17+, multi-plan analytic |
| 9 | OPOS invoice-level tracking lost | Medium | Open items reported as net balance | Per-invoice migration |
| 10 | UStVA continuity broken | Medium | Monthly filing risk | Configure l10n_de tax reports |
| 11 | ZM intra-EU recapitulative broken | Medium | EU filing late | EU VAT ID on partners; configure tax flags |
| 12 | E-invoicing format compatibility | Medium | 2027 mandate non-compliance | Install l10n_de_xrechnung; demo XRechnung output |
| 13 | GoBD audit trail compliance | Low | Audit risk | Enable hash-chain on journals |
| 14 | EÜR vs Bilanz reporting mismatch | Low | Small biz reporting wrong | Detect accounting method |
| 15 | DATEV-format export forward compatibility | Medium | Steuerberater rejects monthly | Build ongoing export, test format conformance |
| 16 | DATEV bank feed transition | Medium | Bank data flow stops | Document PSD2 connector setup |
| 17 | Fixed asset depreciation schedules lost | Medium (if assets exist) | Tax depreciation wrong | Use `account_asset`, recreate AfA schedules |

## Section 8 — Marketing Hooks (German + English)

**SEO long-tails (German):**
1. "DATEV zu Odoo migration"
2. "Odoo DATEV Schnittstelle"
3. "DATEV Alternative Mittelstand"
4. "E-Rechnung 2027 Alternative DATEV"
5. "SKR03 SKR04 Odoo"
6. "Buchungsstapel Export Odoo"
7. "Odoo für deutsche Mittelständler"
8. "XRechnung mit Odoo erstellen"

**SEO long-tails (English, for international companies with German subsidiaries):**
1. "DATEV alternative for English speakers"
2. "Odoo Germany localization"
3. "German bookkeeping in Odoo"
4. "DATEV integration Odoo"

**Pain themes (re-verify from forums: Wer-weiss-was, gutefrage, LinkedIn German SMB groups, Mittelstand-Forum):**
- "Unser Steuerberater bleibt bei DATEV, aber wir brauchen modernes ERP"
- "DATEV ist nicht mehr zeitgemäß für E-Commerce"
- "Mehrsprachigkeit in DATEV ist eine Katastrophe"
- "Die 2027-Pflicht zwingt uns zu modernen Systemen"

**Killer wedge sentence (German):**
> *"Bleiben Sie bei DATEV-Schnittstellen — ohne im DATEV-System gefangen zu sein. Odoo exportiert Buchungsstapel im SKR03/SKR04-Format, so wie es Ihr Steuerberater seit 30 Jahren kennt. Sie bekommen E-Rechnung 2027 sofort, CRM, Lager und Produktion — Ihr Steuerberater bekommt seine gewohnten DATEV-Daten jeden Monat."*

**Killer wedge (English):**
> *"Keep the DATEV pipeline to your Steuerberater — without being trapped in DATEV's 1980s UI. Odoo exports Buchungsstapel CSV monthly in SKR03/SKR04 format. You get e-invoicing-2027-ready ERP, CRM, inventory, manufacturing. Your tax advisor keeps filing UStVA exactly the same way."*

**The 2027 e-invoicing hook (THE primary marketing angle):**
> *"From Jan 1, 2027, German B2B businesses with >€800k revenue MUST issue structured e-invoices. DATEV is adding e-invoicing as a bolt-on — Odoo with `l10n_de_xrechnung` is e-invoicing-native. Migrate before the deadline. We import your DATEV history; we export DATEV-format monthly for your Steuerberater. You're 2027-ready."*

## Section 9 — Pricing & Packaging Insight

**Our pricing relative to DATEV pain:**

| Customer profile | DATEV setup | Migration value-prop | Our SKU |
|---|---|---|---|
| Small Mittelstand <20 employees | Steuerberater only, no own DATEV | "Modernize without disrupting Steuerberater" | `migrate_datev_lite` free (lead magnet) |
| Mittelstand 20-100 employees | DATEV Mittelstand Faktura | "Replace DATEV Faktura, keep Buchungsstapel exchange" | `migrate_datev_pro` €299 |
| 100-500 employees, multi-entity | DATEV + custom integrations | "Multi-entity consolidation DATEV can't do" | `migrate_datev_pro` €299 + agency engagement |
| Agency / IT-Dienstleister doing DATEV migrations | varies | "Migrate unlimited clients" | `migrate_datev_partner` €1,999/yr |

**Companion product (the strategic moat):**

- `odoo_datev_export` — **the ongoing Buchungsstapel export module**. €49/mo subscription OR €999 perpetual. **This is the more valuable product than the migrator.** Every German Odoo customer needs this because their Steuerberater needs it.

**Migration triggers:**
- 2027 e-invoicing mandate (the primary 2026-2027 trigger)
- International expansion (DACH + EU customers)
- E-commerce launch (Shopify/Amazon → DATEV is painful)
- Manufacturing growth (DATEV has no MRP)
- Generational change in management
- Mid-market funded growth (PE-backed companies often replace DATEV)

**Agency / Steuerberater channel program:**
- For Steuerberater-friendly Odoo Partners
- "Steuerberater Toolkit": migrator + ongoing companion + l10n_de SKR03/04 charts + UStVA reporting + XRechnung issuance
- €1,999/yr for unlimited client deployments
- Position as: "the only Odoo migration toolkit that respects the German tax advisor workflow"

## Section 10 — Sources & Open Questions

**Primary sources to verify against:**
- DATEV Schnittstellen-Entwicklerhandbuch (Developer Manual for interfaces) — PDF from datev.de
- DATEV Buchungsstapel-Format documentation (versions 510, 700, current — different schemas)
- SKR03 / SKR04 official charts — published annually by DATEV
- German Finanzministerium (BMF) on e-invoicing mandate: bundesfinanzministerium.de
- §14 UStG (German VAT law) on e-invoicing requirements
- GoBD 2019 (current edition) — BMF guidance on electronic bookkeeping
- Mittelstand-Forum, Wer-weiss-was, LinkedIn German Steuerberater groups

**Open questions for the first build:**
1. DATEV-Schnittstellen-Zertifizierung — pursue or skip? (Recommendation: skip for v1. Buchungsstapel CSV path is sufficient. Revisit at >50 migrations/year.)
2. Steuerberater partner network — should we build relationships with progressive Steuerberater firms? (Yes — 5-10 reference Steuerberater willing to vouch for "Odoo + our export companion works" = unlock the rest of the market.)
3. SKR03 vs SKR04 priority — which to support first? (SKR03 is more common in traditional Mittelstand; SKR04 in newer/international. Support both from v1.)
4. e-Rechnung companion — bundled with migrator OR separate product? (Recommendation: separate. `odoo_xrechnung_pack` €199 perpetual. The 2027 mandate forces this; companion sells itself.)
5. Buchungsstapel export companion — separate SKU or part of partner tier? (Recommendation: separate €49/mo OR €999 perpetual; bundle in partner tier.)
6. Multi-currency in SKR — verify Odoo's l10n_de handles non-EUR correctly with Konto/Gegenkonto pairing.
7. AfA (German tax depreciation tables) — does community module exist or do we need to build?

**Things that change yearly (re-verify in October before fiscal-year transitions):**
- BMF guidance updates on e-invoicing (rules clarified annually)
- SKR03/SKR04 chart updates (DATEV publishes annual update; new accounts added)
- VAT rate changes (rare but possible)
- Buchungsstapel format version updates (DATEV releases new versions)
- UStVA filing schedule changes
- AfA table updates (German depreciation tax tables)
- Mittelstand revenue thresholds (>€800k for 2027 e-invoicing, may be revised)
