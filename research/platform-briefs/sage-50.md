# Platform Brief — Sage 50 (UK / Ireland)

> The UK SMB accounting incumbent — 400k+ installs. Sage Group plc (FTSE 100). Perpetual licenses being killed; subscription forced. The April-2026 MTD for Income Tax mandate is creating a fresh exodus from Sage's add-on-laden pricing model. The UK accountant is the gatekeeper; sales must respect that.

**Naming note (critical):** "Sage 50" means different products in different countries:
- **Sage 50 Accounts** (UK/IE) = the focus of this brief
- **Sage 50** (US) = formerly Peachtree, completely different product
- **Sage 50** (Canada) = formerly Simply Accounting, different again

This brief is UK/IE only. The US Peachtree-lineage and Canadian variants need separate briefs.

---

## Section 1 — Identity

**Vendor:** The Sage Group plc, Newcastle upon Tyne, UK. FTSE 100 component. Founded 1981 by David Goldman. Public since 1989. Revenue ~£2.3B (2024). Strategy: pushing all customers from perpetual-license desktop to cloud-subscription.

**Product lines (the confusion matrix):**

| Product | Status | Migration target? |
|---|---|---|
| Sage 50 Accounts (UK/IE) — formerly Sage Line 50 | Installed Windows desktop, current | **YES — focus of this brief** |
| Sage 50cloud Accounts | Same desktop product, sync to cloud | YES — same migration |
| Sage Business Cloud Accounting (formerly Sage One) | Pure SaaS, different product | Separate brief (similar to QBO/Zoho) |
| Sage Accounting (current naming of Business Cloud) | Same as above | Separate brief |
| Sage 200 | Mid-market, UK | Separate brief — out of scope |
| Sage Intacct | Cloud mid-market (acquired 2017) | Separate, out of scope |
| Sage X3 | Enterprise ERP | Out of scope |
| Sage 50 (US — formerly Peachtree) | Different product entirely | Separate brief — US migration target |
| Sage 50 (Canada — formerly Simply Accounting) | Different product | Separate brief |

**Pricing (UK, 2026, monthly):**

| Tier | Price | Companies | Users | Key features |
|---|---|---|---|---|
| Sage 50 Accounts Essentials | £14.50 | 1 | 1 | Invoicing, banking, MTD VAT |
| Sage 50 Accounts Standard | £40 | 2 | 1 | Inventory, projects |
| Sage 50 Accounts Professional | £79 | Unlimited | 1 base + £15/mo per extra | Multi-currency, advanced inventory, departments |
| Sage 50 Manufacturing (add-on) | +£30 | — | — | Light MRP, BOM |
| Sage Payroll (add-on) | from £10 | — | — | RTI submissions |

Perpetual licenses (older customers, "Sage 50 Accounts Plus 2024" etc.) are being phased out — version 30+ is subscription-only. This is the migration trigger.

**Installed base:**
- ~400k Sage 50 (UK) active subscribers
- ~200k Sage Business Cloud subscribers
- ~750k total Sage SMB customers worldwide
- Long tail of unsupported perpetual installs (v22 and older) — these are the easiest migration targets

**Market segments:**
- UK & Ireland SMB (1-50 employees typical)
- Many UK accountants run Sage Practice or Sage Accountants Cloud as their backbone
- Sage 50 has a 30-year installed base — bookkeepers trained in 1995 are still using it

**Geographic footprint:**
- Tier 1: UK (dominant), Ireland
- Tier 2 (different products): South Africa (Sage Pastel Partner — separate codebase), Canada, US
- Outside English-speaking world: minimal Sage 50 presence

## Section 2 — User Psychology

**Why people choose Sage 50:**
1. Their accountant uses it / requested it (#1 reason — UK accountants are conservative)
2. HMRC MTD VAT compliance built-in since 2019
3. Decades of familiarity ("we've used it since 1998")
4. Sage Payroll integration (RTI to HMRC, P60s, P45s)
5. Local presence — Newcastle-based, UK call center

**Why people stay:**
1. **Accountant lock-in** — switching means convincing the practice
2. **HMRC integration** — MTD VAT submission record
3. **CIS module** — Construction Industry Scheme handling
4. **Payroll** continuity (separate Sage Payroll product)
5. **Familiarity** — 30 years of muscle memory

**Why people leave (ranked, from r/UKBusiness, AccountingWeb forums):**
1. **Subscription forced** — perpetual licenses being killed (v30+)
2. **Annual price hikes** — Sage raises prices 5-15% per year
3. **Windows-only desktop** — Sage 50 doesn't run native on Mac/Linux
4. **Cloud sync flaky** (Sage 50cloud) — customers report data conflicts
5. **Manufacturing weak** — add-on still primitive
6. **MTD ITSA (April 2026)** — Sage charging extra for self-employed compliance
7. **Multi-currency clunky** — designed for £-only originally
8. **No CRM** — separate Sage CRM product or third-party
9. **Reporting limited** — Crystal Reports add-on for anything serious
10. **Mobile app weak**
11. **Younger employees refuse to learn the legacy UI**
12. **Brexit-related complications** — Northern Ireland Protocol VAT handling messy

**What they fear about migrating:**
1. MTD VAT submission record loss → HMRC headache
2. Accountant won't accept the new system
3. CIS deduction history broken
4. Payroll continuity disrupted (Sage Payroll = separate concern)
5. Historical journals lost — UK audit retention 7 years

**Who decides the migration:**
- Founder + bookkeeper + external accountant (the accountant has near-veto power)
- For >10 employees: financial controller often drives
- For construction (CIS) customers: the accountant's CIS-handling preference dictates

**Sales implication:** must include accountant reassurance — "Odoo with `l10n_uk` + our companion handles MTD VAT submissions just like Sage does, your accountant continues to receive the same management reports."

## Section 3 — Data Model

Sage 50 uses traditional UK double-entry accounting with the SAGE Default Chart of Accounts (4-digit nominal codes).

### Nominal Code Structure (the UK SAGE chart)

```
0001-0999  Fixed Assets       (Plant, Vehicles, Property)
1000-1099  Current Assets     (Stock, WIP)
1100-1199  Debtors            (Trade Debtors = 1100)
1200-1299  Bank Accounts      (Bank Current = 1200)
1300-1399  Cash & Loans
2000-2199  Long-Term Liab
2200-2399  Current Liab       (Trade Creditors = 2100, VAT Liability = 2200, PAYE = 2210)
3000-3999  Capital & Reserves (Share Capital, P&L Account)
4000-4999  Sales / Income     (Product Sales = 4000)
5000-5999  Purchases / COGS
6000-6999  Direct Expenses    (Wages, Subcontractors)
7000-7999  Overheads          (Rent, Light, Insurance, etc.)
8000-8999  Depreciation, Bad Debts
9000-9999  Suspense, Mispostings, Year-End
```

### Lists

| Sage 50 Object | Odoo Target | Notes |
|---|---|---|
| Nominal Code | `account.account` | Map via `l10n_uk` chart |
| Customer Record | `res.partner` customer_rank=1 | Account refs like "ABCDE001" |
| Supplier Record | `res.partner` supplier_rank=1 | |
| Stock Record (Product/Service) | `product.template` | Type per product |
| Department | `account.analytic.account` (Plan 1) | 0-999 numbered |
| Project / Cost Codes | `project.project` + analytic | Sage 50 Professional+ |
| VAT Code (T0-T26) | `account.tax` via `l10n_uk` | Direct mapping |
| Bank Account | `account.journal` + linked nominal | |
| Currency | `res.currency` | Multi-currency in Professional+ |

### VAT Code mapping (the UK essential)

| Sage T-Code | Rate | Description | Odoo tax (l10n_uk) |
|---|---|---|---|
| T0 | 0% | Zero-rated supplies | Zero-Rated Sales/Purchases |
| T1 | 20% | Standard rate | Standard Sales/Purchases 20% |
| T2 | 0% | Exempt from VAT | Exempt |
| T3 | (custom) | Customer-defined | Map per customer |
| T4 | (legacy 0%) | EC sales (pre-Brexit) | Now T22 |
| T5 | 5% | Reduced rate | Reduced 5% |
| T7 | 0% | Zero-rated purchases EC | Now post-Brexit imports |
| T8 | (legacy) | Standard EC purchases | Now T17/T18 |
| T9 | n/a | Outside scope (wages, drawings) | No tax |
| T17 | 20% | Import goods (post-Brexit) | Postponed VAT 20% |
| T18 | 0% | Import goods reverse charge | Postponed VAT 0% |
| T20 | 20% | Construction reverse charge | Domestic reverse charge |
| T21 | 5% | Construction reverse charge (5%) | Domestic reverse charge 5% |
| T22 | 0% | EC sales (services, post-Brexit) | EU services |
| T23 | (custom) | Reverse charge zero | Custom |
| T24 | 20% | Construction reverse charge (Mar 2021+) | CIS reverse charge |
| T25 | 0% | Northern Ireland Protocol | NI-specific |
| T26 | 20% | NI standard | NI standard |

### Transactions (Sage 50 audit trail entry types)

Sage 50's audit trail is sequential — every transaction gets a number that can't be reused. Entry types:

| Sage Code | Description | Odoo Target |
|---|---|---|
| SI | Sales Invoice | `account.move` out_invoice |
| SC | Sales Credit Note | `account.move` out_refund |
| SR | Sales Receipt | `account.payment` |
| SA | Sales Receipt on Account | `account.payment` (unapplied) |
| SD | Sales Discount | `account.move` (discount line or refund) |
| PI | Purchase Invoice | `account.move` in_invoice |
| PC | Purchase Credit Note | `account.move` in_refund |
| PP | Purchase Payment | `account.payment` |
| PA | Purchase Payment on Account | `account.payment` (unapplied) |
| PD | Purchase Discount | discount line |
| BR | Bank Receipt | `account.move` + `account.payment` |
| BP | Bank Payment | `account.move` + `account.payment` |
| BT | Bank Transfer | `account.move` (bank ↔ bank) |
| CR | Cash Receipt | `account.payment` (cash journal) |
| CP | Cash Payment | `account.payment` (cash journal) |
| CT | Cash Transfer | `account.move` |
| VR | Visa Receipt | `account.payment` |
| VP | Visa Payment | `account.payment` |
| JC | Journal Credit | `account.move.line` (credit side) |
| JD | Journal Debit | `account.move.line` (debit side) |
| JR | Journal Reverse | `account.move` (reversal) |

## Section 4 — Hidden Complexity (the gotcha catalogue)

### 4.1 Audit Trail Integrity ("Reverse, not Delete")

- **What Sage does:** Sage refuses to permanently delete posted transactions. Reversal creates a contra entry with the next sequential audit number. Even "deleted" via Maintenance still leaves a trail.
- **What breaks:** Customer expects reversed transactions to migrate. Naive importer skips zero-net pairs.
- **Mitigation:** Import both original and reversal as posted `account.move` records, link reversal via `reversed_entry_id`.

### 4.2 VAT Scheme Variants

- **What Sage does:** Customer may be on Standard VAT, Cash Accounting VAT, Flat Rate Scheme, Annual Accounting, or Margin Scheme. Each calculates VAT differently.
- **What breaks:** If migrator assumes Standard VAT, customers on Cash Accounting will see incorrect VAT liability post-cutover.
- **Mitigation:** Detect scheme from Settings → Company → VAT. Configure Odoo's VAT module accordingly (`l10n_uk` supports Standard and Cash Accounting; FRS requires custom handling).

### 4.3 MTD VAT Submission History

- **What Sage does:** Stores MTD VAT submission obligations, periods, submitted return data, HMRC acknowledgments. Each return has a `correlationId` from HMRC.
- **What breaks:** Submission history is audit-critical for HMRC compliance. Lost = inability to prove returns were filed.
- **Mitigation:** Pull VAT return list with all submitted periods. Store in a custom `l10n_uk_mtd_history` model in Odoo as historical record. Configure Odoo MTD for go-forward submissions.

### 4.4 Year-End Procedure

- **What Sage does:** Year-End Wizard explicitly closes the fiscal year, locks prior-year data, and transfers P&L net to nominal 3200 (P&L Account). After year-end, transactions before that date can't be edited.
- **What breaks:** If migrator runs mid-year (e.g., October migration for April-March year), opening balances must reflect last year-end + YTD activity.
- **Mitigation:** Identify last year-end date. Import full prior-year activity OR opening balances + YTD activity (depends on data depth requested).

### 4.5 Departments vs Projects

- **What Sage does:** Department (0-999) is a tag on transactions for management reporting. Project (Sage 50 Professional+) has cost tracking, budgets, P&L.
- **What breaks:** Map both — Department to analytic, Project to `project.project`. If customer uses BOTH, two-axis required.
- **Mitigation:** Map Department to one analytic plan; Project to `project.project` + second analytic plan (Odoo 17+).

### 4.6 Bank Reconciliation Status

- **What Sage does:** Each bank-account transaction has a flag: Bank Reconciled (Yes/No) + reconciliation date. Statement reconciliations are stored.
- **What breaks:** Customer must not re-reconcile years of statements.
- **Mitigation:** Pull `reconciled_date` per line. Build `account.bank.statement` records in Odoo grouped by reconcile date. Mark migrated lines reconciled.

### 4.7 CIS (Construction Industry Scheme)

- **What Sage does:** Construction subcontractor payments require CIS deduction (20% verified / 30% unverified / 0% gross status). Each subcontractor has UTR (Unique Tax Reference). Monthly CIS300 return filed to HMRC.
- **What breaks:** Without CIS module in Odoo, deductions lost; HMRC filing breaks.
- **Mitigation:** Use community module `l10n_uk_construction` if available, or build minimal CIS handling: deduction tax + subcontractor UTR on partner + CIS300 report template.

### 4.8 Foreign Currency Revaluation

- **What Sage does:** Multi-currency in Professional+ requires manual revaluation entries at period-end via "Foreign Currency Revaluation Wizard."
- **What breaks:** If you import historical transactions with original rates but Odoo's auto-revaluation kicks in with current rates, AR/AP in foreign currency diverges.
- **Mitigation:** Import full rate history. Disable Odoo auto-revaluation until customer briefed.

### 4.9 Stock Take Adjustments

- **What Sage does:** Stock Take feature creates "ST" adjustments via the Stock Take wizard. These post to nominal 1000 (Stock) and 5200 (Stock Adjustments) typically.
- **What breaks:** If migrated as journals, valuation method calculations don't replay correctly.
- **Mitigation:** Re-create as `stock.move` (internal) with valuation entry. Test against Sage Stock Valuation report.

### 4.10 Customer/Supplier Multi-Address

- **What Sage does:** Each customer/supplier can have multiple delivery addresses (Sage 50 Professional) + main invoice address + registered address.
- **What breaks:** Odoo `res.partner` supports child contacts for addresses but it's not 1:1 with Sage's "delivery address" concept.
- **Mitigation:** Main address → res.partner. Delivery addresses → child res.partner records with `type='delivery'`.

### 4.11 Sage Drive Sync Mid-Export

- **What Sage does:** Sage 50cloud (or "Connected Services") syncs the desktop file to a cloud copy via Sage Drive. State can be "syncing" / "out of date" / "in conflict."
- **What breaks:** If migrator extracts mid-sync, partial data.
- **Mitigation:** Pre-flight: ensure Sage Drive is fully synced AND customer pauses sync during export.

### 4.12 Sage 50 v25+ Backend = MS SQL

- **What Sage does:** From v25 (2019) onwards, Sage 50 stores data in a local MS SQL Server Express instance, not the older Pervasive/Btrieve format.
- **What breaks:** Direct DB queries possible (undocumented schema) but only if migrator knows the version.
- **Mitigation:** Direct SQL queries against MS SQL = fastest extraction path. Schema must be reverse-engineered per version (changes between v25-v30). High maintenance burden.

### 4.13 Layouts and Reports (Customer Customizations)

- **What Sage does:** Customers customize invoice/statement layouts (.layout files), reports (.report files), and have saved letter templates.
- **What breaks:** Visual/formatting customizations are NOT migrated.
- **Mitigation:** Document customer's customizations; rebuild in Odoo as QWeb templates.

### 4.14 Recurring Entries

- **What Sage does:** Recurring SI/PI/JR entries with frequency (weekly, monthly, etc.) and next-due-date.
- **What breaks:** Without explicit pass, future entries stop appearing.
- **Mitigation:** Pull recurring entries list; create Odoo recurring invoices or use cron-driven account.move generation.

### 4.15 Brexit and Northern Ireland VAT

- **What Sage does:** Post-Brexit (2021+) added T17/T18 (postponed VAT for imports), T22 (EU services), T25/T26 (Northern Ireland Protocol). The NI Protocol means NI businesses follow EU VAT rules for goods, UK VAT for services — split treatment.
- **What breaks:** If migrator doesn't preserve T-code, NI-specific VAT treatment is wrong.
- **Mitigation:** Preserve T-code on every line as `account.tax` mapping. Use `l10n_uk` NI-aware taxes if customer is NI-based.

### 4.16 Sage Payroll Separate Product

- **What Sage does:** Sage Payroll is a separate product/database. Payroll posts journals to Sage 50 via integration but holds employee details, RTI submissions, P60/P45 separately.
- **What breaks:** Payroll journals migrate; employee data and RTI submission history don't.
- **Mitigation:** Document explicitly: payroll migration is OUT OF SCOPE; customer continues running Sage Payroll standalone OR migrates separately to Odoo Payroll (`hr_payroll` Enterprise).

## Section 5 — Export Surface

### The Hard Truth: No Public REST API for Sage 50 Desktop

Sage 50 (UK desktop) does NOT have a public REST API. This is a fundamental constraint.

### Sage SDK (paid)

- **What it is:** C#/.NET SDK for ISVs to read/write Sage 50 data files
- **Cost:** ~£500-£3,000/year per ISV depending on tier
- **Access:** must be a Sage Developer Partner; application required
- **Capability:** complete read/write access to .SDB files (Pervasive) or MS SQL backends (v25+)
- **Quality:** the only "real" path; what professional migration tools use
- **Strategic implication:** for serious migration tooling, the SDK is mandatory and is itself a competitive moat (the licensing cost keeps amateurs out)

### Audit Trail Report → Excel/CSV

- Customer exports the full Audit Trail report (transaction-level) to CSV
- Limited to displayed columns; line-level detail of invoices is in a separate report
- **Most common low-end migration data source**
- **Limitation:** invoice line items require a separate Day Books → Sales/Purchase Day Book export

### List View CSV Exports

- Customers list, Supplier list, Nominal list, Stock list each export to CSV
- Lossy: only displayed columns; custom fields if visible
- Used in combination with Audit Trail

### Sage Business Cloud Accounting API (different product!)

- Sage Accounting (the SaaS, formerly Sage One) has a REST API at `developer.sage.com`
- OAuth 2.0, modern
- **NOT applicable to Sage 50 desktop migration** — only for SaaS customers

### Third-Party Tools (the competitive landscape)

- **Movemybooks** — Sage's official migration partner (move FROM Sage TO QBO/Xero; not Odoo)
- **AutoEntry / Dext** — receipt capture + Sage integration (not migration)
- **Saasant Transactions** — Sage import/export tool
- **Zed Axis** — multi-platform import/export
- Most third-party tools target Sage → Xero or Sage → QBO migrations. **Sage → Odoo is uncovered.**

### What You Can NEVER Get Out

1. Custom layout files (.layout) — proprietary format
2. Custom report definitions
3. User permission grant history
4. Sage Drive sync conflict logs
5. Email send history (Sage 50 sends emails via Outlook; logs are in Outlook, not Sage)
6. Custom Sage Add-Ons (third-party plugins) data
7. Sage Practice / Sage Accountants Cloud integration state

### Practical Migration Paths (ranked by effort/quality)

**Option A — Sage SDK (premium path):**
- Acquire Sage Developer Partnership and SDK license
- Direct read of customer's data file
- Complete data extraction including line items, recurring entries, bank rec status
- **Cost:** £500-£3,000/yr for us
- **Sales pitch:** "Professional migration, certified Sage partner"

**Option B — MS SQL direct (v25+ only, semi-supported):**
- Connect to local MS SQL instance
- Query tables directly (schema reverse-engineered)
- Free but unstable across versions
- **Risk:** Sage may change schema between versions; ongoing maintenance

**Option C — CSV exports (low-end fallback):**
- Customer exports Audit Trail + each list view to CSV
- Migrator parses CSVs
- Lossy but accessible without partnership
- **Limitation:** line items, bank rec status, recurring entries often lost

**Recommendation:** start with Option C for solo customers ($99 SKU), graduate to Option A for agency-partner SKU ($499+) once volume justifies SDK cost.

## Section 6 — Odoo Mapping (key tables)

### Nominal code mapping (SAGE Default Chart → l10n_uk)

The `l10n_uk` Odoo module installs a UK chart that's similar but not identical to the SAGE Default. Migration involves either:
- (a) Installing `l10n_uk` and remapping customer's SAGE codes to its chart
- (b) Recreating customer's SAGE codes in Odoo as-is (preserves continuity)

Recommendation: (b) for the migrator default — customer keeps their nominal codes; UK reports work as long as account types are right.

| SAGE Nominal | Description | Odoo `account.account` setup |
|---|---|---|
| 0030 | Premises | Type=Fixed Asset, code=0030 |
| 1100 | Debtors Control | Type=Receivable, code=1100 |
| 1200 | Bank Current | Type=Bank, code=1200, linked Bank Journal |
| 2100 | Creditors Control | Type=Payable, code=2100 |
| 2200 | Sales Tax Control (VAT Liability) | Type=Current Liability, linked to tax engine |
| 2210 | PAYE | Type=Current Liability |
| 3200 | Profit & Loss Account | Type=Equity |
| 4000 | Sales — Products | Type=Income |
| 4905 | Distribution & Carriage | Type=Income (or Expense) |
| 5000 | Materials Purchased | Type=Cost of Revenue |
| 6201 | Subcontractor Charges | Type=Direct Expense |
| 7100 | Rent | Type=Overhead Expense |
| 7200 | Electricity | Type=Overhead Expense |
| 7906 | Foreign Exchange Gain/Loss | Type=Other Income/Expense |
| 8200 | Sundry Expenses | Type=Expense |
| 9999 | Mispostings Account | Type=Current Asset (Suspense) |

### Invoice mapping

| Sage field | Odoo `account.move` field | Transform |
|---|---|---|
| Audit Trail No. | `name` or `ref` (Sage's sequence) | Direct |
| Invoice Number | `name` | Direct (override Odoo sequence) |
| Account Reference | `partner_id` (customer) | Lookup |
| Date | `invoice_date` | DD/MM/YYYY → ISO |
| Due Date | `invoice_date_due` | DD/MM/YYYY → ISO |
| Reference | `ref` (PO number from customer) | Direct |
| Line: Stock Code | line `product_id` | Lookup |
| Line: Description | line `name` | Direct |
| Line: Quantity | line `quantity` | Direct |
| Line: Net Amount | line `price_subtotal` | Computed from price_unit × qty |
| Line: VAT Code (T-code) | line `tax_ids` | Mapping table |
| Line: Nominal Code | line `account_id` (override) | Direct |
| Line: Department | line `analytic_distribution` | Plan-aware |
| Line: Project Ref | line `analytic_distribution` (project) | |
| Currency | `currency_id` | Direct |
| Foreign Rate | `currency_rate` | Direct |

### Post-migration reconciliation queries

```sql
-- Trial Balance match Sage as of cutover
SELECT a.code, a.name,
       SUM(l.debit) AS dr, SUM(l.credit) AS cr,
       (SUM(l.debit) - SUM(l.credit)) AS balance
FROM account_move_line l
JOIN account_account a ON a.id = l.account_id
WHERE l.parent_state = 'posted' AND l.date <= '{cutover}'
GROUP BY a.code, a.name
ORDER BY a.code;

-- VAT Return check (compare to Sage's last submitted MTD VAT)
SELECT t.name AS vat_code,
       SUM(CASE WHEN m.move_type IN ('out_invoice','out_refund') THEN line.balance ELSE 0 END) AS box6,
       SUM(CASE WHEN m.move_type IN ('in_invoice','in_refund') THEN line.balance ELSE 0 END) AS box7
FROM account_move_line line
JOIN account_tax_repartition_line rep ON rep.id = line.tax_repartition_line_id
JOIN account_tax t ON t.id = rep.tax_id
JOIN account_move m ON m.id = line.move_id
WHERE m.invoice_date BETWEEN '{period_start}' AND '{period_end}'
GROUP BY t.name;

-- AR Aging compare with Sage's Aged Debtors
SELECT p.name AS customer,
       CASE
         WHEN CURRENT_DATE - m.invoice_date_due <= 30 THEN '0-30'
         WHEN CURRENT_DATE - m.invoice_date_due <= 60 THEN '31-60'
         WHEN CURRENT_DATE - m.invoice_date_due <= 90 THEN '61-90'
         ELSE '90+'
       END AS bucket,
       SUM(m.amount_residual) AS amount
FROM account_move m
JOIN res_partner p ON p.id = m.partner_id
WHERE m.move_type = 'out_invoice' AND m.amount_residual > 0
GROUP BY p.name, bucket;
```

## Section 7 — Migration Risk Register

| Rank | Failure | Probability | Customer impact | Mitigation |
|---|---|---|---|---|
| 1 | MTD VAT continuity broken | High | HMRC penalty risk | Pull MTD submission history; configure Odoo MTD module |
| 2 | VAT scheme misidentified (Standard vs Cash) | Medium | Wrong VAT liability | Detect at company level pre-flight |
| 3 | CIS deductions silently dropped | Medium | HMRC CIS300 broken | Detect CIS usage; install l10n_uk_construction or custom |
| 4 | Audit trail integrity (reverse-pairs) lost | Medium | Audit compliance issue | Import both original + reversal |
| 5 | Bank rec status lost | High | Customer re-reconciles years | Pull reconcile dates; build statements |
| 6 | Department/Project dimensional collapsed | Medium | Management reports wrong | Require Odoo 17+; multi-plan analytic |
| 7 | Customer ref number scheme broken | Medium | Cross-reference confusion | Preserve account_ref as `ref` |
| 8 | Stock valuation method mismatch | Medium | COGS drift | Set product.category cost method |
| 9 | NI Protocol VAT (T25/T26) wrong | Medium (NI only) | NI VAT filing wrong | NI-aware tax mapping |
| 10 | Foreign currency revaluation reposts | Low | Small FX divergence | Import rate history first |
| 11 | Multi-address customer collapsed | Low | Shipping address lost | Child partner records |
| 12 | Recurring entries silently dropped | Medium | Future invoices stop | Pull recurring list separately |
| 13 | Year-end timing breaks opening balance | Medium | Trial balance off | Compute YE balance correctly |
| 14 | Sage Drive sync conflict mid-export | Low | Partial data | Pause sync pre-export |
| 15 | Custom nominal codes outside SAGE chart | Medium | Mapping unclear | Surface unknown codes pre-flight |
| 16 | Sage Payroll integration breaks | High (if used) | Payroll journals stop posting | Document out-of-scope; recommend Sage Payroll standalone OR full Odoo Payroll migration |
| 17 | Accountant rejects Odoo | High | Migration aborted | Demo MTD + management reports to accountant pre-sale |

## Section 8 — Marketing Hooks

**SEO long-tails (UK-specific):**
1. "migrate sage 50 to odoo"
2. "sage 50 alternative UK"
3. "leaving sage 50"
4. "sage 50 to odoo migration"
5. "sage subscription too expensive"
6. "MTD ITSA sage alternative" (April 2026 trigger)
7. "sage 50 manufacturing alternative"
8. "sage business cloud to odoo"
9. "sage 50 cloud cancel migration"

**Pain points from forums (re-verify from AccountingWeb, r/UKBusiness, UKBF):**
- "Sage raised our subscription AGAIN this year"
- "We've used Sage since 1998 but the cloud sync keeps breaking"
- "MTD ITSA is forcing us to evaluate alternatives"
- "Sage Manufacturing add-on is £30/month for what should be free"
- "Younger staff refuse to use Sage 50"

**Killer wedge sentence:**
> *"Sage just put your subscription up again — and the MTD ITSA add-on is coming in April 2026. Migrate to Odoo in a weekend, keep every VAT return, every CIS deduction, every department code. Your accountant gets the same management reports. You pay £0/month for the software, forever."*

**Comparison angles:**
- Sage 50 Professional: £79/mo × 12 = £948/yr forever, plus £30/mo Manufacturing add-on = £1,308/yr
- Plus Sage Payroll add-on (3+ employees): £25/mo = £300/yr more
- **5-year Sage cost: £8,040+**
- Odoo Community (free) + our migrator (£75 one-time) + hosting (£20/mo) = £315/yr
- **5-year Odoo cost: ~£1,650** (£6,400 saved, more features)

**The accountant reassurance angle:**
- "Your accountant continues to receive monthly management reports in the format they're used to. Odoo's MTD VAT module is HMRC-recognised. We provide the migrator AND the ongoing companion that exports Sage-format CSVs for accountants who still want them."

**The April-2026 MTD ITSA hook:**
- HMRC mandate: from April 2026, self-employed individuals and landlords with income >£50k must submit quarterly via MTD-compliant software. >£30k follows in 2027. Sage charges add-on £/mo for compliance.
- Position our migrator as "MTD ITSA ready Day 1" — Odoo's UK localization can submit quarterly returns natively.

## Section 9 — Pricing & Packaging Insight

**Our pricing relative to Sage 50 pain:**

| Customer profile | Sage monthly | Migration value-prop | Our SKU |
|---|---|---|---|
| Sage 50 Essentials (sole trader) | £14.50 | Not worth migrating — too small | Lead magnet only |
| Sage 50 Standard | £40 | "Save £480/yr, get CRM/projects" | `migrate_sage50_lite` free, `pro` £79 |
| Sage 50 Professional | £79 | "Save £948/yr, get manufacturing native" | `migrate_sage50_pro` £79-£149 |
| Sage 50 Pro + Manufacturing + Payroll | £140+ | "Save £1,680/yr, replace whole stack" | `migrate_sage50_partner` £399/yr |
| MTD ITSA self-employed | £varies | "Compliance ready Day 1" | Bundle with property accounting |

**Migration triggers:**
- Sage raises subscription (annual September raise) → renewal-time evaluation
- Perpetual license customer forced to subscription (v30+) → fresh evaluation
- MTD ITSA mandate (April 2026) → self-employed exodus
- Manufacturing growth → Sage Manufacturing add-on cost
- Multi-user scale → Sage 50 per-user pricing escalation
- Brexit-related complexity → NI Protocol headaches

**Agency program for UK accountants:**
- "Sage Practice Replacement Toolkit": migrator + ongoing-export companion + l10n_uk module pack
- £499/yr for agencies → unlimited client migrations
- Differentiator: most UK accountants already know Odoo exists but think migrating Sage is a nightmare. Our toolkit makes it a weekend.

## Section 10 — Sources & Open Questions

**Primary sources to verify against:**
- Sage 50 product documentation: `gb.sage.com/help/sage-50-accounts/`
- Sage Developer Network: `developer.sage.com` (for SDK + Business Cloud API)
- AccountingWeb forums (UK accountant community) — best pain point source
- HMRC MTD VAT guidance: `gov.uk/guidance/making-tax-digital-for-vat`
- HMRC MTD ITSA: `gov.uk/guidance/check-if-youll-need-to-sign-up-for-making-tax-digital-for-income-tax`
- r/UKBusiness, r/UKPersonalFinance, UKBF (UK Business Forums)

**Open questions for the first build:**
1. SDK acquisition: is the £500-3,000/yr Sage Partner cost worth it? (Recommendation: NO for v1 — start with CSV/Audit Trail approach; revisit at $5k/mo recurring revenue.)
2. MTD VAT submission: Odoo `l10n_uk` has MTD module — verify it supports the customer's VAT scheme.
3. CIS module: does the Odoo community offer a working `l10n_uk_construction`? (Verify; if not, build minimal CIS handling as part of our localization pack.)
4. Sage Payroll: scope decision — explicitly out-of-scope OR companion product?
5. NI Protocol VAT: does our migrator detect NI-based customers and apply right tax mapping?

**Things that change yearly (re-verify in August before September price rises):**
- Sage 50 subscription pricing (rises annually September-October)
- HMRC MTD thresholds (VAT, ITSA expansion to lower income thresholds)
- VAT rate changes (rare but possible in budgets)
- CIS rates (Construction Industry Scheme parameters)
- Brexit-related VAT rules (postponed accounting, NI Protocol amendments)
- New Sage 50 releases (annual, usually April or September)
