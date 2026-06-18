# Platform Brief — Tally

> India's accounting standard. Owned by Tally Solutions Pvt Ltd (Bangalore, family-owned). The CA channel's default. Two product generations in the wild: Tally ERP 9 (legacy, still huge installed base) and Tally Prime (current). Migration tooling must handle both. No public REST API — but a usable XML interface exists.

---

## Section 1 — Identity

**Vendor:** Tally Solutions Pvt Ltd, Bangalore, India. Founded 1986 by Bharat Goenka. Private, family-owned, profitable, no PE money. This independence is part of why they don't innovate fast — and why they don't need to.

**Product lines:**

| Product | Status | Migration approach |
|---|---|---|
| Tally ERP 9 (Release 6.x) | Legacy, sales discontinued 2020 but huge installed base, still patched for GST | XML Server (port 9000) |
| Tally Prime (Release 1.0 → 5.0+, 2020 onwards) | Current product | XML Server (same protocol) |
| Tally Prime Server | Multi-user backend, Enterprise | Same XML interface |
| Tally Prime Edit Log | Compliance edition with full audit log | Same + audit data |
| Tally on Cloud | Third-party hosted (AWS, etc.) | Same protocol, accessed via partner |
| Tally Developer / TDL | Customization platform, not data | Detect customizations only |

**Pricing (2026, INR):**

| SKU | Price | Notes |
|---|---|---|
| Tally Prime Single User | ~₹22,500 (~$270) perpetual | + ₹4,500/yr AMC |
| Tally Prime Multi User | ~₹67,500 (~$810) perpetual | + ₹13,500/yr AMC |
| Tally Prime Edit Log | ~₹83,000 (~$1,000) perpetual | Audit edition |
| Tally on Cloud (via partner) | ~₹500-2,000/mo/user | Third-party hosted |

Note: Tally pricing is largely STABLE — the migration trigger is rarely cost. It is feature ceiling.

**Installed base estimate:**
- Tally claims 7M+ businesses globally, 30+ countries
- Active install base: ~2M+ companies
- India dominance: ~80% SMB market share, 100% in CA practices
- Strong secondary markets: UAE, Saudi Arabia, Bangladesh, Nepal, Sri Lanka, Kenya, Nigeria

**Market segments:**
- Indian SMB across all industries (manufacturing, trading, retail, services)
- Chartered Accountant (CA) firms — every CA office in India runs Tally to manage client books
- The CA channel is the single most important fact about Tally distribution

**Geographic footprint:**
- Tier 1 (dominant): India
- Tier 2 (heavy): UAE, Saudi Arabia, Bangladesh, Nepal, Bhutan, Sri Lanka
- Tier 3 (strong): Kenya, Nigeria, parts of East Africa, Indonesia
- Outside this: minimal presence

## Section 2 — User Psychology

**Why people choose Tally:**
1. The family CA / Auditor uses it (THE #1 reason — CAs are the channel)
2. GST compliance built-in (since GST launch 2017)
3. Cheap perpetual license — no recurring subscription squeeze
4. Offline-first — works without internet (huge in tier-2/3 Indian cities)
5. TDL customization — every Tally install can be customized by local consultants
6. Keyboard-shortcut UI is fast for trained accountants

**Why people stay:**
1. CA lock-in — switching means convincing the CA to learn a new system
2. GST returns flow built around Tally's outputs
3. Power/internet unreliability in many regions favors offline
4. Decades of vouchers — CAs trust the audit trail
5. TDL customizations accumulated over years

**Why people leave (ranked):**
1. **Multi-location inventory** — Tally's godown model breaks at scale
2. **Manufacturing / MRP weak** — BOM exists but no real production planning
3. **CRM zero** — no native customer relationship management
4. **Mobile is bad** — Tally is fundamentally Windows desktop; mobile is a viewing app
5. **E-commerce integration** — only via third-party connectors
6. **Modern reporting limits** — dashboards/BI are absent
7. **Workflow / approval missing** — no PR/PO approval flows
8. **International operations** — outside India localization is thin
9. **Audit log only in Edit Log edition** — most installs don't have it
10. **Generational handover** — young staff refuse to learn the keyboard UI
11. **Subscription on Tally on Cloud** — when forced to cloud for multi-user, costs add up

**What they fear about migrating:**
1. GST returns won't tie at cutover
2. CA won't accept the new system
3. Decades of vouchers lost
4. TDS / TCS deduction history broken
5. Custom TDL features they rely on disappear

**Who decides the migration:**
- Owner-promoter (often modernizing because the next generation joined)
- The CA must approve — if CA refuses, migration is dead
- Mid-market (50-500 employees) decisions often go through external consultant

**Sales implication:** Tally migration sales must include CA reassurance. Build a "DATEV-Steuerberater-style" companion that lets the CA keep their workflow — export Tally-compatible data from Odoo monthly.

## Section 3 — Data Model

Tally splits its world into **Masters** (lists) and **Vouchers** (transactions). The crucial conceptual difference from QuickBooks: **in Tally, everything that holds a balance is a "Ledger"** — customers, vendors, banks, expenses, assets, equity. They're differentiated only by their parent **Group**.

### Masters

| Tally Object | Odoo Target | Notes |
|---|---|---|
| Group | `account.account.type` family + naming hierarchy | Group "Sundry Debtors" → customer partners; "Sales Accounts" → income GL |
| Ledger (under Sundry Debtors) | `res.partner` (customer_rank=1) | The customer master |
| Ledger (under Sundry Creditors) | `res.partner` (supplier_rank=1) | The vendor master |
| Ledger (under Bank Accounts) | `account.account` (Bank type) + `account.journal` | |
| Ledger (under Cash-in-Hand) | `account.account` (Cash type) + journal | |
| Ledger (under any P&L group) | `account.account` (Income/Expense) | |
| Ledger (Duties & Taxes) | `account.account` (Tax Receivable/Payable) | Linked to tax engine |
| Stock Group | `product.category` | Hierarchical |
| Stock Item | `product.template` | Storable products |
| Stock Category | Second analytic dimension on stock | Often unused |
| Unit of Measure | `uom.uom` | Tally compound units (12 PCS = 1 DOZ) need explicit conversion |
| Godown | `stock.warehouse` + `stock.location` | Tally supports nested godowns |
| Voucher Type | `account.journal` + sequence rules | Numbering conventions live here |
| Currency | `res.currency` | Built-in |
| Cost Centre | `account.analytic.account` (Plan A) | |
| Cost Category | Second analytic plan | Requires Odoo 17+ for multi-plan |
| Employee | `hr.employee` | If HR module loaded |

### Vouchers

| Tally Voucher Type | Odoo Target | Notes |
|---|---|---|
| Sales | `account.move` type=`out_invoice` | |
| Purchase | `account.move` type=`in_invoice` | |
| Receipt | `account.payment` (inbound) | |
| Payment | `account.payment` (outbound) | |
| Contra | `account.move` (bank ↔ cash transfer) | |
| Journal | `account.move` (manual GL) | |
| Credit Note | `account.move` type=`out_refund` | |
| Debit Note | `account.move` type=`in_refund` | |
| Stock Journal | `stock.move` (internal) + valuation entry | |
| Manufacturing Journal | `mrp.production` consumption | Needs `mrp` |
| Delivery Note | `stock.picking` (outgoing) | Needs `stock` |
| Receipt Note | `stock.picking` (incoming) | |
| Sales Order | `sale.order` | Needs `sale_management` |
| Purchase Order | `purchase.order` | Needs `purchase` |
| Rejection In / Out | Return pickings | |
| Physical Stock | `stock.inventory` adjustment | |
| Memorandum | NOT migrated — non-posting | Skip |
| Optional Voucher | NOT migrated unless made regular | Skip |
| Reversing Journal | `account.move` (reversed) | Map cancellation state |
| TDS / TCS Vouchers | `account.payment` + l10n_in withholding | Sectional handling |

## Section 4 — Hidden Complexity (the gotcha catalogue)

### 4.1 Ledger-as-Universal-Concept

- **What Tally does:** A "Customer," "Vendor," "Bank Account," and "Electricity Expense" are all Ledger records — distinguished only by their parent Group.
- **What breaks:** Naive migrators pull "all ledgers" and try to put them in one Odoo model. The split must be done by walking the Group hierarchy.
- **Mitigation:** Build a Group → Odoo-Entity mapping table. Walk parents to detect inheritance (a custom Group "Tier-1 Customers" is a child of "Sundry Debtors" → still a customer).

### 4.2 GST Era Switch (Pre/Post July 2017)

- **What Tally does:** Before July 1, 2017, India had VAT, CST, Service Tax, and Excise Duty as separate taxes with separate ledger configurations. After: CGST/SGST/IGST/UTGST/Cess. Customers with >7 years of data have BOTH eras present.
- **What breaks:** Tax mapping must detect the voucher date and apply the right tax engine.
- **Mitigation:** Two tax-mapping tables. Pre-July-2017 vouchers can typically be migrated as already-filed (no live tax linkage required); post-July-2017 vouchers need full GST tax setup.

### 4.3 Voucher Numbering Conventions

- **What Tally does:** Per voucher type, supports manual, automatic, or auto-with-prefix numbering. Customers use complex schemes: "INV/2024-25/0001" (financial-year-aware), "SLR/MUM/0001" (branch + serial), "GST-INV-001" (compliance prefix).
- **What breaks:** If you let Odoo auto-number, customers lose their referential history. Indian audit requires invoice numbers to be preserved EXACTLY.
- **Mitigation:** Import voucher numbers as `account.move.name` directly; configure Odoo journal sequences to NOT auto-number imported records. For go-forward, set Odoo sequence to continue customer's pattern.

### 4.4 Financial Year (April–March)

- **What Tally does:** Default FY is April 1–March 31 (Indian fiscal year). All reports, year-end closure, GST returns align to this.
- **What breaks:** Odoo defaults to calendar year. If you migrate mid-year (say October), opening balances must be computed for April 1 of that year, not January 1.
- **Mitigation:** Configure `res.company` `fiscalyear_last_day` and `fiscalyear_last_month` before import. Compute trial balance as of customer's last closed FY end.

### 4.5 TDL Customizations

- **What Tally does:** Any install can load `.tcp` (Tally Compiled Program) files that add custom fields, change voucher behavior, add reports. These are widespread — most mid-size Tally customers have at least 2-3 active TDL extensions.
- **What breaks:** Custom fields appear in voucher XML exports but their meaning is unknown without seeing the TDL source (often encrypted).
- **Mitigation:** Detect non-standard XML elements and surface them as "needs mapping decision" in the migrator UI. Don't silently drop.

### 4.6 Multi-Godown Stock with Nesting

- **What Tally does:** Stock can be in multiple godowns (warehouses). Godowns can be nested (Mumbai → Andheri → Locker-3). Single stock item × multiple godowns × multiple batches = the smallest record.
- **What breaks:** Odoo supports warehouses and locations but customers often want godown hierarchy preserved.
- **Mitigation:** Map top-level godowns to `stock.warehouse`; nested godowns to `stock.location` with parent_id chains.

### 4.7 Cost Centre Allocation with Splits

- **What Tally does:** A single voucher line can be allocated to multiple Cost Centres by percentage (60% Marketing, 40% Sales). Cost Categories add a second axis.
- **What breaks:** Pre-17 Odoo had one analytic axis. From 17+ multi-plan works.
- **Mitigation:** Require Odoo 17+ for Tally migrations using both Cost Centres and Cost Categories.

### 4.8 Inventory Valuation Method Variety

- **What Tally does:** Supports FIFO, LIFO (yes, still!), Average Cost, Standard, Last Purchase Cost, Monthly Average, Weighted Average, Std Price.
- **What breaks:** Odoo supports only Standard, AVCO (Average), and FIFO at `product.category` level.
- **Mitigation:** Map LIFO and weird Tally methods to AVCO with a one-time valuation adjustment to true up opening balance.

### 4.9 Bill-Wise Tracking (Outstanding Bills)

- **What Tally does:** Every customer/vendor balance is broken into individual "Bill References" with reference number, date, due date, credit period. Payment is matched against these references.
- **What breaks:** Odoo's payment matching via `account.move.line` reconciliation is similar but uses the move's name. Reference numbers must transfer.
- **Mitigation:** Import bill references as `account.move.ref` and seed `account.partial.reconcile` records to mirror Tally's allocation.

### 4.10 RCM (Reverse Charge Mechanism)

- **What Tally does:** Certain GST expenses require the BUYER to remit GST (e.g., legal services, lawyer fees, unregistered vendor purchases). Voucher is tagged RCM.
- **What breaks:** Odoo's `l10n_in` supports RCM via specific tax codes; mapping the Tally tag → right Odoo tax must be explicit.
- **Mitigation:** Detect RCM flag at voucher level; apply correct l10n_in reverse-charge tax code.

### 4.11 TDS and TCS

- **What Tally does:** TDS (Tax Deducted at Source) by buyer on payments to vendors per section (194C contractor, 194J professional, etc.) with rates. TCS (Tax Collected at Source) by seller on certain transactions.
- **What breaks:** Odoo `l10n_in` has TDS module but section coverage varies. Year-end Form 26Q reporting depends on correct section tags.
- **Mitigation:** Preserve section code per vendor + rate. Use `l10n_in_tds` or custom withholding tax mapping.

### 4.12 E-Invoice and E-Way Bill (IRN, QR, EWB)

- **What Tally does:** Tally Prime integrates with NIC's e-invoice portal. Each invoice >₹5 Cr aggregate turnover threshold gets an IRN (Invoice Reference Number), signed QR code, and optionally an E-Way Bill number for goods movement.
- **What breaks:** These compliance artifacts are audit-critical. Lost = audit failure.
- **Mitigation:** Pull IRN + QR + EWB on each invoice; store in Odoo as `l10n_in_einvoice_id` / `l10n_in_ewaybill_number` fields.

### 4.13 Multi-Currency (Tally-Style)

- **What Tally does:** Currency is at voucher level. Rate stored on voucher. No automatic period-end revaluation by default (manual).
- **What breaks:** Odoo's automatic revaluation may post entries the customer didn't expect.
- **Mitigation:** Import currency + rate on each voucher. Disable Odoo auto-revaluation until customer is briefed.

### 4.14 Composition Scheme Dealers

- **What Tally does:** Small dealers under GST Composition Scheme pay flat 1-5% turnover tax and cannot claim ITC. Their invoice format is different (no GSTIN on tax line).
- **What breaks:** Different tax treatment; if migrator assumes regular scheme, GST returns break.
- **Mitigation:** Detect Composition flag in company master; apply scheme-specific tax rules.

### 4.15 Job Work / Subcontracting

- **What Tally does:** "Stock Journal — Manufacturing" and "Job Work" features handle sending materials to subcontractors and receiving back. Subcontractor stock is tracked separately under Section 143 GST.
- **What breaks:** Map to Odoo's MRP subcontracting flow.
- **Mitigation:** Use `mrp_subcontracting` module mapping for these voucher types.

### 4.16 Optional and Memorandum Vouchers

- **What Tally does:** Vouchers can be flagged "Optional" (not posted to books, e.g., quotations) or "Memorandum" (memo entries that don't affect ledgers).
- **What breaks:** Naive importers pull them into GL → phantom transactions.
- **Mitigation:** Filter at extract time. Optional Sales Orders may be worth importing as draft `sale.order` records.

## Section 5 — Export Surface

### The Key Fact: No Public REST API

Tally Solutions does NOT provide a public REST API. This is unlike QBO/Zoho/Sage Cloud. **But there IS an XML interface** that almost no one outside Tally consultants knows how to use well.

### Tally XML Server (Gateway of Tally)

- **Enable:** Tally → F12 Configure → Advanced Configuration → Tally.NET and Remote Access → Enable Tally.Server / Enable ODBC Server. Set port (default 9000).
- **Protocol:** Plain HTTP, accepts XML requests, returns XML responses. Surprisingly simple.
- **Authentication:** none by default (LAN-level access). Tally Prime adds password options.
- **Capabilities:** read all masters and vouchers; export reports; can also write data (for two-way sync, dangerous).
- **Quality:** complete data access for migration purposes.
- **Reference:** TDL Server Reference Manual (Tally official) — covers the protocol.

### Tally ODBC

- **Enable:** Tally has built-in ODBC server (port 9000 by default, configurable).
- **Read-only:** safe.
- **Use case:** simpler than XML for tabular queries; commonly used for Excel/Power BI exports.

### Tally Excel Exports

- Most reports support "Export → Excel/XML/PDF."
- **Lossy:** report-level data only, not transaction-level details unless specifically configured.
- **Common use case:** for small migrations where setup of XML Server is overkill.

### Tally Backup Files (.900, company folder)

- **Proprietary:** binary format, not directly parseable.
- **Migration relevance:** for offline migration where the customer can send a backup and we restore in our lab on a Tally trial license, then run our XML extractor.

### Third-Party Tools

- Saral, Webkul, Cybrosys, Aktiv Software, and others have built basic Tally → Odoo connectors. Most are weak: handle masters + simple vouchers, miss the gotchas in Section 4.
- This is the competitive landscape. **The gap to exploit is in Section 4 — handle the gotchas they don't.**

### What You Can NEVER Get Out

1. TDL customization source code (encrypted .tcp files)
2. Audit log unless customer is on Edit Log edition
3. Bank feed history (Tally has no real bank feeds; manual entries)
4. User permission grant history
5. Edit history before period closing
6. Custom report definitions
7. Voucher-level attachments (Tally Prime has attachments but support is thin)

### Practical Path for Migrators

**Option A (preferred):** Customer enables XML Server on their Tally install. Migrator connects over LAN (or SSH tunnel) and pulls all masters + vouchers in a few hours. Then disconnect.

**Option B:** Customer sends compressed company folder (encrypted). Migrator restores on a Tally trial license in our lab. Extract via XML Server. Return only the resulting data.

**Option C (fallback):** Customer exports each major report to Excel/XML manually. Migrator parses. Lossy but works for small migrations.

## Section 6 — Odoo Mapping (key tables)

### Group → Odoo entity routing

```
Sundry Debtors             → res.partner (customer_rank=1)
Sundry Creditors           → res.partner (supplier_rank=1)
Bank Accounts              → account.account (Bank) + account.journal
Cash-in-Hand               → account.account (Cash) + journal
Loans (Liability) & Loans (Asset) → account.account (Liab/Asset)
Capital Account            → account.account (Equity)
Sales Accounts             → account.account (Income)
Purchase Accounts          → account.account (Cost of Revenue)
Direct/Indirect Expenses   → account.account (Expense)
Direct/Indirect Incomes    → account.account (Income)
Fixed Assets               → account.account (Fixed Asset)
Investments                → account.account (Non-current Asset)
Current Assets             → account.account (Current Asset)
Current Liabilities        → account.account (Current Liability)
Duties & Taxes             → account.account (linked to account.tax)
Provisions                 → account.account (Liability)
Stock-in-Hand              → account.account (auto-managed by stock valuation)
```

### Voucher → account.move field mapping

| Tally field | Odoo `account.move` field | Transform |
|---|---|---|
| Voucher Number | `name` | Direct (preserve exact string) |
| Voucher Date | `invoice_date` / `date` | DD-MM-YYYY → ISO |
| Voucher Type | resolved to `journal_id` | Lookup |
| Party Ledger | `partner_id` | Lookup via external_id |
| Currency + Rate | `currency_id` + `currency_rate` | |
| Narration | `narration` | Direct |
| GSTIN of Party | already on partner | Validate |
| Place of Supply | `l10n_in_state_id` | Lookup IN state |
| IRN / QR Code | `l10n_in_irn` / `l10n_in_irn_qr` | Direct |
| E-Way Bill No. | `l10n_in_ewaybill_number` | Direct |
| Line: Stock Item | line `product_id` | Lookup |
| Line: Quantity | line `quantity` | Direct |
| Line: Rate | line `price_unit` | Direct |
| Line: Discount | line `discount` | Direct |
| Line: GST tax | line `tax_ids` (CGST+SGST or IGST) | Composite |
| Line: Cost Centre allocation | line `analytic_distribution` | Plan-aware |
| Bill Reference | `ref` + reconciliation rec | Per-bill |

### Post-migration reconciliation queries

```sql
-- Trial Balance match Tally as of cutover date
SELECT a.code, a.name,
       SUM(l.debit) AS debit, SUM(l.credit) AS credit,
       SUM(l.balance) AS balance
FROM account_move_line l
JOIN account_account a ON a.id = l.account_id
WHERE l.parent_state = 'posted' AND l.date <= '{cutover_date}'
GROUP BY a.code, a.name
ORDER BY a.code;

-- Outstanding bills per partner (compare with Tally Bills Outstanding report)
SELECT p.name, m.name AS bill_no, m.invoice_date,
       m.invoice_date_due, m.amount_residual
FROM account_move m
JOIN res_partner p ON p.id = m.partner_id
WHERE m.move_type IN ('out_invoice','in_invoice')
  AND m.amount_residual > 0;

-- GST output tax for GSTR-1 month (compare with Tally GSTR-1)
SELECT t.name AS tax, SUM(line.balance) AS amount
FROM account_move_line line
JOIN account_tax_repartition_line rep ON rep.id = line.tax_repartition_line_id
JOIN account_tax t ON t.id = rep.tax_id
JOIN account_move m ON m.id = line.move_id
WHERE m.move_type = 'out_invoice'
  AND DATE_TRUNC('month', m.invoice_date) = '{month}'
GROUP BY t.name;
```

## Section 7 — Migration Risk Register

| Rank | Failure | Probability | Customer impact | Mitigation |
|---|---|---|---|---|
| 1 | GST returns don't reconcile (GSTR-1, GSTR-3B) | High | Audit risk, ITC mismatch | Build GSTR-1 line-level comparison report at cutover |
| 2 | TDS sectional codes mismapped | High | Vendor TDS wrong, Form 26Q broken | Section code table per vendor; user confirms |
| 3 | TDL custom fields silently dropped | High | Customer workflow broken | Surface unknown XML nodes in pre-flight report |
| 4 | Voucher numbering convention not preserved | Medium | Audit confusion | Preserve `name` exactly; lock sequence |
| 5 | Bill-wise references lost | Medium | Open bills tracking broken | Import bill refs + seed reconciles |
| 6 | Multi-godown stock collapsed | Medium | Inventory location reports wrong | Nested godowns → nested locations |
| 7 | Cost Centre allocations dropped | Medium | Management P&L wrong | Multi-plan analytic; require Odoo 17+ |
| 8 | Inventory valuation method mismatch (LIFO/Std) | Medium | COGS drift | Map exotic methods to AVCO + opening adjustment |
| 9 | E-invoice IRN / QR / EWB lost | Medium | Audit risk for current FY | Preserve in dedicated fields |
| 10 | RCM invoices not flagged | Medium | GSTR-3B wrong, RCM liability mis-stated | Detect RCM at voucher level |
| 11 | Pre/post-July-2017 tax era handling | Low | Historical filings already done | Filter or treat archival; usually skip |
| 12 | Composition scheme dealer mishandled | Low | Niche but breaks if missed | Detect scheme at company level |
| 13 | Job work / subcontracting flows lost | Low (niche customers only) | MRP broken | Use `mrp_subcontracting` |
| 14 | Bank reconciliation status lost | Medium | Customer re-reconciles | Pull cleared flag if available |
| 15 | Optional/Memorandum vouchers polluting GL | Medium | Phantom transactions | Filter at extract |
| 16 | CA refuses to accept Odoo | High | Migration aborted | Build ongoing Tally-format export tool |

## Section 8 — Marketing Hooks

**SEO long-tail (real Indian search demand):**
1. "migrate tally to odoo"
2. "tally to odoo migration tool"
3. "tally alternative for manufacturing"
4. "tally erp 9 to odoo"
5. "tally prime to odoo migration India"
6. "odoo with gst returns"
7. "multi location tally"
8. "tally for e-commerce" (negative-keyword angle)

**Pain points to mine from forums (re-verify exact text from r/india, r/CharteredAccountants, CAclubindia.com, LinkedIn Indian SMB groups):**
- "We have 4 branches and Tally just shows one location"
- "Our CA refuses to upgrade because he doesn't want to learn anything new"
- "Tally Prime is faster but still doesn't do manufacturing"
- "Mobile access in Tally is useless"

**Killer wedge sentence:**
> *"Tally was built for one accountant on one PC in 1986. Your business has 4 branches, 30 employees, and customers in 5 countries. Migrate to Odoo in a weekend — keep every voucher, every GST return, every IRN — and your CA still gets Tally-format exports every month."*

**Comparison angle:**
- Tally Multi-User: ₹67,500 perpetual + ₹13,500/yr AMC = ₹1.35 lakh over 5 years
- Plus Tally on Cloud hosting: ₹60,000/yr for 5 users = ₹3 lakh over 5 years
- Plus no CRM, no manufacturing, no e-commerce
- Odoo Community + our migrator (₹8,000 one-time) + Odoo.sh hosting (₹15,000/mo for ~30 users) = comparable cost, dramatically more features

**The CA reassurance angle (this is the differentiator):**
- "Your CA continues to receive Tally-format Buchungsstapel-equivalent files every month. We export from Odoo into Tally XML. They keep filing GSTR-1, GSTR-3B, and Form 26Q exactly the way they always have. You get CRM, manufacturing, and multi-location."

## Section 9 — Pricing & Packaging Insight

**Tally pricing pain isn't the issue — feature ceiling is.**

| Customer profile | Tally setup cost | Migration trigger | Our SKU |
|---|---|---|---|
| 1-10 employee SMB | ₹22,500 single user | Rarely migrates — Tally is fine | Not our customer |
| 10-50 employee growing | ₹67,500 multi-user | Multi-location, CRM gap | `migrate_tally_lite` free (lead magnet) |
| 50-200 employee mid-market | ₹67,500 + ₹60k/yr cloud | Manufacturing, branches, modernization | `migrate_tally_pro` ₹8,000 (~$99) |
| 200+ employee, multi-state | Tally Prime Server | Multi-entity consolidation, audit | `migrate_tally_partner` ₹40,000/yr (~$499) |

**Migration triggers (when the customer starts looking):**
- Second branch opened → "I can't see consolidated stock"
- First manufacturing line started → "BOM in Tally is a joke"
- E-commerce launched → "Connecting Shopify is a nightmare"
- Next-gen joins business → "Why are we still on this 1990s software"
- Multi-state GST → "I need different GSTINs in different locations"

## Section 10 — Sources & Open Questions

**Primary sources to verify against:**
- Tally Solutions help portal: `help.tallysolutions.com`
- TDL Reference Manual (download from tallysolutions.com)
- TDL Server Reference (XML protocol)
- Tally Community forum: `community.tallysolutions.com`
- CAclubindia.com — best resource for CA pain points and migration discussions
- LinkedIn: Indian SMB / Manufacturing groups; CA practice owners

**Open questions for the first build:**
1. Do we target Tally ERP 9 + Tally Prime both, or Prime-only first? (Recommendation: Prime-first; ERP 9 customers are mostly the lower-end and harder to upsell. But include ERP 9 XML compatibility — same protocol mostly.)
2. Build XML extractor in Python (requests-based) or Tally Connector libraries? (Recommendation: pure Python; no external deps.)
3. Sandbox: Tally provides 30-day trial; works locally. Spin up trial with sample company for dev.
4. Should we open-source the XML extractor and monetize only the mapping layer? (Tactical question — open-sourcing the extractor builds trust with the consultant community; mapping is the moat.)
5. CA-companion product: "Tally Export from Odoo" — is this a separate SKU or bundled with migrator? (Recommendation: bundled with `partner` tier; separate ₹2,000/mo SKU for solo-buyer customers.)

**Things that change yearly (re-verify in October before each FY):**
- GST tax rates and slabs (annual GST Council changes)
- E-invoice thresholds (currently ₹5 Cr aggregate turnover; likely dropping)
- TDS section rate changes (Finance Bill annual)
- Tally Prime release new features (annual major release in Oct/Nov)
- AMC pricing structure
