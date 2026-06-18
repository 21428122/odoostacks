# Platform Brief — QuickBooks

> The world's most widely deployed SMB accounting platform. Owned by Intuit (USA). Two product lines that behave like different software: QuickBooks Online (QBO, SaaS) and QuickBooks Desktop (QBD, file-based). Migration tooling must pick at least one consciously.

---

## Section 1 — Identity

**Vendor:** Intuit Inc. (NASDAQ: INTU), Mountain View, CA. Founded 1983. Public since 1993. Accounting is one of three business lines (alongside TurboTax and Credit Karma).

**Product lines (the ones that matter for migration):**

| Product | Model | Data store | Migration approach |
|---|---|---|---|
| QuickBooks Online (QBO) | SaaS | Intuit cloud (multi-tenant) | REST API + OAuth2 |
| QuickBooks Desktop (QBD) Pro/Premier/Enterprise | Installed Windows app | Local .QBW file | QBXML via Web Connector, or convert to QBO first |
| QuickBooks Self-Employed / Solopreneur | SaaS (cut-down) | Intuit cloud | API exists but limited; usually export CSV |
| QuickBooks Online Accountant (QBOA) | Multi-firm portal | Same as QBO | Not a separate target |
| QuickBooks Money / Checking | Banking add-on | Intuit / Green Dot | Out of scope |

**Versions still in the wild (2026):**
- QBO is rolling, no versions — but feature availability varies by subscription tier
- QBD 2021 (US) is the oldest with any vendor support; Intuit aggressively sunsets — QBD 2022 lost online services 2025, QBD 2023 loses them 2026
- QBD outside the US (UK, Canada, Australia) has been **discontinued entirely** — those markets are forced to QBO. Huge migration pressure.

**Pricing (US, 2026 — for sales math):**

| Tier | Monthly | Users | Key limit |
|---|---|---|---|
| QBO Simple Start | ~$35 | 1 | No bill pay, no inventory |
| QBO Essentials | ~$65 | 3 | No inventory, no projects, no classes |
| QBO Plus | ~$99 | 5 | The "real" tier — inventory, projects, classes, locations |
| QBO Advanced | ~$235 | 25 | Custom roles, workflow automation, fixed asset, batch invoicing |
| QBD Enterprise | $1,800+/yr | 1-40 | Industry editions, advanced inventory, FIFO |

**The migration trigger** is almost always **Plus → Advanced** (2.4× price jump for features customers want) OR **the 5-user cap** on Plus.

**Installed base (best public estimate):**
- QBO: ~9M subscribers globally as of 2025
- QBD: ~1.5M active US installs, declining ~15% YoY
- Combined dominance: ~80% of US small business accounting

**Geographic footprint:**
- Tier 1 (native + heavy): US, Canada, UK, Australia, India
- Tier 2 (sold but thin): France, Singapore, South Africa, Mexico
- Tier 3 (no localization, customers struggle): rest of EU, LATAM, MENA — these are the **softest migration targets** because Odoo has better localization

## Section 2 — User Psychology

**Why people choose QuickBooks:**
1. Their accountant uses it / requested it (the #1 reason — accountants are the channel)
2. "Industry standard" perception in US SMB
3. TurboTax/Intuit ecosystem trust
4. The 90s/2000s installed base inertia

**Why people stay:**
1. **Accountant lock-in** — switching means convincing the external accountant to learn a new system
2. **Bank feed integration** — connected to thousands of US banks
3. **App marketplace** — 700+ integrations (Shopify, Salesforce, Gusto)
4. **Familiarity** — bookkeepers trained over years
5. **Tax software handoff** — Intuit's TurboTax/ProConnect imports QB data natively

**Why people leave (ranked, what customers actually say):**
1. **Price hikes** — Intuit raises prices ~10% annually; Advanced went from $180 to $235 between 2023-2025
2. **Subscription squeeze** — perpetual QBD users forced to subscribe
3. **Multi-entity / inter-company consolidation** — QBO has no real multi-entity; Advanced "consolidation" is anemic
4. **International / multi-currency** beyond basics breaks down
5. **Manufacturing / MRP** — none. Customers outgrow inventory features
6. **Project profitability** — Customer:Job is primitive vs Odoo Projects
7. **CRM** — none native (have to integrate Salesforce/HubSpot at extra cost)
8. **Custom workflows / approvals** — only on Advanced and weak
9. **API limits & rate-limiting** for high-volume operations
10. **International expansion** — no QB localization in many countries → customers force-migrate
11. **Audit log** weak below Advanced
12. **QBD discontinuation** outside US (UK/Canada/AU customers being kicked off)

**What they fear about migrating:**
1. Trial balance won't tie at cutover
2. Lost historical data / reports
3. Bank reconciliation will need redoing
4. Their accountant won't accept the new system
5. Custom reports they spent years building
6. Existing integrations (Shopify, Stripe, etc.) won't reconnect

**Who decides the migration:**
- Solo / micro: the founder (5–20 employees)
- SMB: controller + external accountant (must approve)
- Mid-market: CFO + IT lead, often via implementation partner

**Sales implication:** for any deal >5 users, the agency channel is mandatory. Solo prosumers buy direct; everyone else buys through an Odoo Partner.

## Section 3 — Data Model

QuickBooks splits its world into **Lists** (master data, slow-changing) and **Transactions** (events, fast-growing).

### Lists

| QB Object | Odoo Target | Notes |
|---|---|---|
| Account (Chart of Accounts) | `account.account` | Type + Detail Type → Odoo `account.account.type` + `user_type_id` |
| Item — Service | `product.template` type=`service` | Income account only |
| Item — Inventory Part | `product.template` type=`product` (storable) | **Three accounts: Income, COGS, Asset** |
| Item — Non-Inventory Part | `product.template` type=`consu` | Income + Expense |
| Item — Inventory Assembly | `product.template` + `mrp.bom` | Premier/Enterprise only; needs `mrp` module |
| Item — Group | No native — expand at line level | Lossy |
| Item — Discount | `product.template` (service, negative) or move-level discount | Architectural mismatch |
| Item — Subtotal | UI-only in QB | Drop |
| Item — Sales Tax / Tax Group | `account.tax` / `account.tax.group` | Complex; see Section 4 |
| Item — Payment | `account.payment.method` or product | Rare, low priority |
| Item — Other Charge | `product.template` (service) | Maps cleanly |
| Customer | `res.partner` (customer_rank=1) | Customer:Job hierarchy → `parent_id` |
| Job (sub-customer) | `res.partner` child OR `project.project` | **Two valid mappings** depending on use |
| Vendor | `res.partner` (supplier_rank=1) | 1099 vendor flag → `l10n_us_check_printing`? |
| Employee | `hr.employee` | If using HR module |
| Class | `account.analytic.account` | One analytic plan |
| Location (QBO Plus+) | `account.analytic.account` (separate plan) | Multi-axis from Odoo 17+ |
| Terms | `account.payment.term` | Net 30, 2/10 Net 30, etc. — discount terms need conversion |
| Payment Method | `account.payment.method` | Check, ACH, Credit Card |
| Tax Code | `account.tax` | Many-to-one if grouped |
| Tax Agency | `res.partner` (gov entity) | Plus a tax account |
| Memorized Transaction | No standard — custom or `account.move` + cron | Often dropped |
| Currency | `res.currency` (built-in) | Rate history → `res.currency.rate` |

### Transactions

| QB Object | Odoo Target | Notes |
|---|---|---|
| Invoice | `account.move` type=`out_invoice` | Header + lines |
| Sales Receipt | `account.move` type=`out_invoice` + `account.payment` (combined) | One-step pay-and-bill |
| Estimate | `sale.order` (state=draft/sent) | Needs `sale_management` |
| Credit Memo | `account.move` type=`out_refund` | |
| Bill | `account.move` type=`in_invoice` | |
| Bill Payment | `account.payment` | |
| Vendor Credit | `account.move` type=`in_refund` | |
| Check | `account.payment` + `account.move` | Check number → `check_number` |
| Deposit | `account.move` (bank-side) OR ignored if grouping payments | See "Undeposited Funds" |
| Payment (Receive Payment) | `account.payment` | |
| Journal Entry | `account.move` (no invoice type) | Manual GL postings |
| Transfer | `account.move` between cash/bank accounts | |
| Inventory Adjustment | `stock.move` + valuation entry | Needs `stock` |
| Purchase Order | `purchase.order` | Needs `purchase` |
| Statement Charge | `account.move` line | Rare |
| Bill Credit | `account.move` type=`in_refund` | |
| Time Tracking | `account.analytic.line` or `hr_timesheet` | |
| Attached document | `ir.attachment` linked to record | Pull binary + re-attach |

## Section 4 — Hidden Complexity (the gotcha catalogue)

These are the migration killers. Every one of them silently produces wrong numbers if ignored.

### 4.1 Undeposited Funds

- **What QB does:** When a customer payment is received, QB posts it to a special current-asset account called "Undeposited Funds" (UF). The user then creates a Deposit transaction that batches multiple payments and moves them to the bank account.
- **Why:** mirrors physical workflow — receive multiple checks in a drawer, deposit at the bank in one slip.
- **What breaks:** if you naively import payments as Odoo `account.payment` directly hitting the bank, the bank balance will mismatch QB by the UF balance. If you import UF as a regular asset account, payments will sit "unreconciled" forever.
- **Mitigation:** at cutover, force the customer to deposit all UF balances in QB first (clean UF to zero). Then post-migration, payments go directly to bank — no UF needed in Odoo.

### 4.2 Items have three accounts (Inventory Parts)

- **What QB does:** An Inventory Part item stores Income Account, COGS Account, AND Asset (Inventory) Account on the item itself. Every sale posts to all three.
- **What breaks:** if migrator only maps Income, COGS and Inventory accounts get default-posted, breaking inventory valuation and gross margin reports.
- **Mitigation:** map all three explicitly on `product.category` (Odoo's stock valuation account, expense account, and income account live partly on category and partly on product).

### 4.3 Inventory valuation method

- **What QB does:** Uses **Average Cost** by default. QB Enterprise Advanced Inventory allows FIFO.
- **What Odoo does:** Defaults to **Standard** cost; supports Average (AVCO) and FIFO. Costing method is set on `product.category`.
- **What breaks:** if you don't switch the Odoo product category to AVCO before importing, inventory value will diverge from QB on the first sale.
- **Mitigation:** create dedicated product categories with `property_cost_method = 'average'` before product import.

### 4.4 Opening Balance Equity

- **What QB does:** A magic equity account created when QB encounters an unbalanced transaction (e.g., user types an opening balance into a customer record). Used as a plug.
- **What breaks:** customers have $50k–$500k accumulated in OBE they don't even know about. Migrating it as-is moves the problem to Odoo. Migrating without it leaves the trial balance unbalanced.
- **Mitigation:** at cutover, force a clean-up journal in QB to clear OBE to Retained Earnings. Then map OBE in migration to a one-time "Migration Adjustments" equity account.

### 4.5 Sales Tax — three different systems

- **QBD Sales Tax:** uses Tax Items + Tax Groups + Tax Agency vendors. Per-line tax codes (T/E/Tax/Non).
- **QBO Manual Sales Tax (legacy):** similar to QBD.
- **QBO Automated Sales Tax (AST):** Intuit calculates tax from shipping address via their own engine. The customer never sees the rate structure — it's a black box.
- **What breaks:** AST gives you a *result* (tax amount on each invoice) but not the *rule* (which jurisdiction, which agency). You can't recreate the rule structure in Odoo.
- **Mitigation:** for AST customers, treat historical tax as a frozen amount per invoice (preserve it as a tax-line override). Build new tax structure in Odoo for go-forward.

### 4.6 Customer:Job vs Project

- **What QB does:** A Customer can have sub-Customers called Jobs. Used for project tracking — invoicing a job rolls up to the parent customer's AR.
- **What breaks:** Odoo `res.partner` can have parent/child but AR doesn't roll up. If you want project P&L, you need `project.project` linked to invoices via analytic distribution.
- **Mitigation:** decision per customer — if they use Jobs for AR grouping only, map to partner hierarchy. If they use Jobs for P&L, map to `project.project` + analytic.

### 4.7 Class and Location (dimensional tracking)

- **What QB does:** QBO Plus+ supports Class (e.g., department) and Location (e.g., branch) as orthogonal axes on every transaction line.
- **What breaks:** Odoo pre-17 has a single analytic plan. Customers using both Class AND Location lose one axis.
- **Mitigation:** require Odoo 17+ for migration; create two `account.analytic.plan` records and map each.

### 4.8 Reconciliation status loss

- **What QB does:** Each transaction line in a bank account has a Cleared status (C=cleared, R=reconciled, blank=outstanding) plus a reconcile date.
- **What breaks:** This per-line state isn't a first-class entity in QBO API — it's accessible but easily missed. If lost, customer must re-reconcile years of statements.
- **Mitigation:** pull each bank account's transactions with the Cleared/Reconciled flag; create matching `account.bank.statement` records grouped by reconcile date in Odoo.

### 4.9 Attachments are a separate entity

- **What QB does:** Attachments are stored in an `Attachable` object linked to transactions via `AttachableRef`. You can't just GET an invoice and have files come along.
- **What breaks:** customer migrates, all PDFs disappear from invoice records.
- **Mitigation:** separate pass — fetch all Attachable, download binary, re-attach to corresponding Odoo record via `ir.attachment`.

### 4.10 1099 vendor handling

- **What QB does:** Each vendor has a 1099-eligible flag, a tax ID, and tracked 1099 boxes (Box 7, Box 1, etc.). Year-end generates 1099-NEC/1099-MISC reports.
- **What breaks:** US localization in Odoo handles 1099 differently. Without mapping, year-end reporting breaks.
- **Mitigation:** preserve 1099 flag + tax ID + payment classifications. Use `l10n_us` modules.

### 4.11 Memorized / Recurring Transactions

- **What QB does:** A list of templated transactions that fire on schedule (recurring rent, recurring invoices).
- **What breaks:** No standard QBO API surface for these. Easily silently dropped.
- **Mitigation:** flag as "manual review needed" in migration report. Build a UI for customer to recreate in Odoo's Subscription / Recurring Invoice module.

### 4.12 Negative Inventory

- **What QB does:** Allows selling stock you don't have (negative on-hand). Posts a fictional COGS using average cost.
- **What breaks:** Odoo refuses negative stock by default unless you allow it on the location. If you allow it, you must also accept that costing entries get fix-up moves later.
- **Mitigation:** detect negative stock at cutover, force customer to fix in QB or accept lossy import (skip negative-stock items).

### 4.13 The "Items vs Expenses" tab in Bills

- **What QB does:** When entering a vendor bill, the user can put line items on either the Items tab (uses Item costs) or the Expenses tab (uses GL accounts directly). Same bill can have both.
- **What breaks:** API returns each as a separate line type. Migrator must handle both.
- **Mitigation:** Map Items-tab lines to Odoo bill lines with product_id; Expenses-tab lines to bill lines with no product, just an account.

### 4.14 Voided vs Deleted transactions

- **What QB does:** Voiding a transaction keeps the record (audit trail) but zeros amounts. Deleting removes it entirely. Voids show up in transaction lists; deletes only show in Audit Log.
- **What breaks:** Customers expect voided records to migrate. Naive importers skip them because amounts are zero.
- **Mitigation:** preserve voided records as `account.move` in cancelled state with original amounts in description.

### 4.15 Multi-currency revaluation

- **What QB does:** When multi-currency is on, period-end revaluation posts to a "Currency Gain/Loss" account based on current rate. Rate history is stored.
- **What breaks:** if you import historical transactions with their original rate but Odoo has different rates, AR/AP in foreign currency will revalue differently.
- **Mitigation:** import the full `res.currency.rate` history first. Lock historical rates.

## Section 5 — Export Surface

### QBO API

- **Auth:** OAuth 2.0, app must be registered in Intuit developer portal. Tokens expire (refresh required).
- **Endpoint:** `https://quickbooks.api.intuit.com/v3/company/{realmId}/`
- **Rate limit:** 500 req/min per realm; bursts above trigger 429. Throttle aggressively.
- **Pagination:** SQL-like query language (`SELECT * FROM Invoice WHERE TxnDate > '...' STARTPOSITION 1 MAXRESULTS 1000`) — max 1000 per page.
- **Versioning:** SyncToken on every record — required for updates. Migrator is read-only so just ignore.
- **Completeness:** ~95% of UI fields are accessible. Missing: custom report definitions, some preferences, in-app reminders.
- **Webhooks:** available for ongoing sync but not needed for one-shot migration.
- **Sandbox:** free dev sandbox; production access requires app review for some scopes.

### QBD (Desktop) Exports

- **IIF files:** legacy text format; mostly write-only (good for import to QB, lossy for export from QB). Avoid.
- **QBB backup files:** proprietary, encrypted; can only be opened by QuickBooks software. **Not directly parseable.**
- **QBXML via QuickBooks Web Connector (QBWC):** SOAP-like, runs as a Windows service on the customer's machine, queries the live .QBW file. Complete data access but requires customer to install + run on their server. High friction.
- **Direct file access via QODBC** (third-party driver): reads .QBW directly. ~$500/license. Used by serious consultants.
- **Reports → Excel:** lossy, hand-curated, common for small migrations.
- **Third-party export tools:** TransactionPro Export, Saasant Transactions, Zed Axis Importer/Exporter. Most US accountants already own one of these.

### Practical path for QBD customers

The pragmatic migration path: **convert QBD file to QBO first** (Intuit provides a tool: "Move to QuickBooks Online"), then use QBO API. The conversion is free, takes ~30 minutes, and gives you a clean API surface. Customer ends up paying for a month of QBO subscription before flipping to Odoo. This is the path 80% of agencies will take — and our migrator should be optimized for it.

### What you can NEVER get out

1. The Audit Log history (who-changed-what-when) — visible in UI on Plus+, not via API
2. Custom report layouts (column choices, filters, saved configurations)
3. Memorized transaction schedules (in QBD only via QBXML)
4. Bank feed connection state / rules
5. Saved bank rules ("if payee starts with STARBUCKS, categorize as Meals")
6. Auto-applied attachments (Plus+ "Receipt Capture" stored images)
7. Form template customizations (invoice PDF designs)

## Section 6 — Odoo Mapping (key tables)

### Chart of Accounts mapping

| QB Account Type | QB Detail Type (sample) | Odoo `account.account.type` (`user_type_id`) |
|---|---|---|
| Bank | Checking, Savings, Cash on Hand | Bank and Cash |
| Accounts Receivable | Accounts Receivable | Receivable |
| Other Current Asset | Inventory Asset, Prepaid Expense | Current Assets |
| Fixed Asset | Machinery & Equipment, Vehicles | Fixed Assets |
| Other Asset | Goodwill, Long-Term Investments | Non-current Assets |
| Accounts Payable | Accounts Payable | Payable |
| Credit Card | Credit Card | Credit Card |
| Other Current Liability | Sales Tax Payable, Payroll Liabilities | Current Liabilities |
| Long Term Liability | Long-Term Debt | Non-current Liabilities |
| Equity | Owner's Equity, Retained Earnings | Equity |
| Income | Sales of Product Income, Service/Fee Income | Income |
| Cost of Goods Sold | Cost of Labor – COS, Supplies & Materials | Cost of Revenue |
| Expense | Office Supplies, Rent, Utilities | Expenses |
| Other Income | Interest Earned | Other Income |
| Other Expense | Depreciation, Penalties | Other Expense |

### Invoice mapping (the bread and butter)

| QB field | Odoo `account.move` field | Transform |
|---|---|---|
| `Id` | `name` (or external_id) | Prefix with `QB-` |
| `DocNumber` | `name` | Direct |
| `TxnDate` | `invoice_date` | ISO format |
| `DueDate` | `invoice_date_due` | ISO |
| `CustomerRef` | `partner_id` | Lookup via external_id |
| `CurrencyRef` | `currency_id` | Lookup ISO code |
| `ExchangeRate` | `currency_rate` | Direct |
| `Line[].Amount` | line `price_subtotal` | Per line |
| `Line[].SalesItemLineDetail.ItemRef` | line `product_id` | Lookup |
| `Line[].SalesItemLineDetail.Qty` | line `quantity` | Direct |
| `Line[].SalesItemLineDetail.UnitPrice` | line `price_unit` | Direct |
| `Line[].SalesItemLineDetail.TaxCodeRef` | line `tax_ids` | Lookup |
| `Line[].SalesItemLineDetail.ClassRef` | line `analytic_distribution` | Plan-aware |
| `TxnTaxDetail.TotalTax` | sum of tax lines | Verify match |
| `Memo` / `PrivateNote` | `narration` | Direct |
| `EmailStatus` | none | Drop |
| `Balance` | computed from payments | Verify post-migration |
| Attachable refs | `ir.attachment` | Separate pass |

### Reconciliation queries (verify migration was correct)

After migration, run these and compare to QB reports:

```sql
-- Trial Balance check
SELECT account.code, account.name,
       SUM(line.debit) AS debit, SUM(line.credit) AS credit,
       SUM(line.balance) AS balance
FROM account_move_line line
JOIN account_account account ON account.id = line.account_id
WHERE line.parent_state = 'posted' AND line.date <= '{cutover_date}'
GROUP BY account.code, account.name
ORDER BY account.code;

-- AR Aging check
SELECT partner.name, move.invoice_date, move.invoice_date_due,
       move.amount_residual, move.currency_id
FROM account_move move
JOIN res_partner partner ON partner.id = move.partner_id
WHERE move.move_type = 'out_invoice'
  AND move.state = 'posted'
  AND move.amount_residual > 0;

-- Inventory valuation check (storable products)
SELECT product.id, template.name,
       SUM(quant.quantity) AS qty, AVG(quant.cost) AS avg_cost,
       SUM(quant.quantity * quant.cost) AS value
FROM stock_quant quant
JOIN product_product product ON product.id = quant.product_id
JOIN product_template template ON template.id = product.product_tmpl_id
GROUP BY product.id, template.name;
```

## Section 7 — Migration Risk Register

| Rank | Failure | Probability | Customer impact | Mitigation |
|---|---|---|---|---|
| 1 | Trial balance mismatch at cutover | High | Cannot file taxes, audit risk | Force OBE cleanup in QB; reconcile each account post-import |
| 2 | AR aging mismatch | High | Customer disputes, dunning errors | Clean Undeposited Funds before export; reconcile per-customer |
| 3 | Inventory valuation drift | High | Wrong COGS, wrong margins | Set Odoo product.category to AVCO before import; spot-check 10 products |
| 4 | Sales tax reports diverge | High | Filing errors, penalties | If AST, freeze historical tax; rebuild forward-looking rules |
| 5 | Bank rec status lost | Medium | Customer re-reconciles years of statements | Import per-line cleared/reconciled flag; create statement records |
| 6 | Attachments lost | Medium | PDFs gone from invoices | Separate attachment pass; re-link by transaction ref |
| 7 | Class/Location dropped | Medium | Management reports broken | Require Odoo 17+; map to multi-axis analytic plans |
| 8 | Memorized transactions silently dropped | Medium | Recurring invoices stop | Pre-migration audit; manual recreation list |
| 9 | Custom fields lost | Medium | Workflow logic broken | Map to Odoo `x_studio_*` fields or studio.fields |
| 10 | 1099 tracking broken | Low (US-only) | Year-end reporting fails | Preserve 1099 flag + payment classifications |
| 11 | Voided records skipped | Low | Audit trail incomplete | Preserve as cancelled state |
| 12 | Multi-currency revaluation diverges | Low (rare) | Foreign AR/AP off | Import full rate history first |
| 13 | Project profitability differs | Low | Job costing wrong | Decide Customer:Job mapping per customer (partner vs project) |
| 14 | Negative inventory items | Low | Cutover fails | Force fix in QB or skip items |
| 15 | OAuth refresh token expires mid-import | Low (technical) | Restart required | Add token refresh + idempotent resume |

## Section 8 — Marketing Hooks

**Top SEO long-tails (real search demand, comparable apps in marketplace):**
1. "migrate quickbooks to odoo"
2. "import quickbooks data into odoo"
3. "quickbooks alternative for manufacturing"
4. "quickbooks to odoo migration tool"
5. "switching from quickbooks online to odoo"
6. "quickbooks desktop end of life alternative" (the UK/CA/AU forced-migration angle)

**Pain quotes from forums (paraphrased, common patterns — re-verify exact text before quoting publicly):**
- "Intuit raised our price again — we're paying $235/month for what used to be $99."
- "We outgrew QuickBooks for inventory. The reports lie about COGS."
- "QuickBooks Desktop is being discontinued in Canada and our accountant doesn't know what to do."
- "We can't run two companies side-by-side without paying for Advanced."

**Killer wedge sentence (the one line that closes):**
> *"Stop paying Intuit's annual 10% price hike — migrate to Odoo in one weekend, keep all your data, and pay €0/month for the core software ever again."*

**Comparison angle for the landing page:**
- QBO Plus ($99/mo × 5 users) = $5,940/year forever
- Odoo Community + our migrator ($99 one-time) + €15/user/mo for hosted Odoo Online = $900/year for 5 users
- **5-year savings: ~$25,000** — and you own the data

## Section 9 — Pricing & Packaging Insight

**Our pricing relative to QB pain:**

| Customer profile | QB monthly | Migration value-prop | Our SKU |
|---|---|---|---|
| Solo QBO Essentials user | $65 | "Save $780/yr" | `migrate_qb_lite` free (lead magnet) |
| Small biz QBO Plus | $99 | "Save $1,200/yr, get manufacturing/CRM" | `migrate_qb_pro` $99 |
| Multi-entity / 25 users / QBO Advanced | $235 | "Save $2,820/yr, real consolidation" | `migrate_qb_pro` $99 + agency engagement |
| Agency doing QB migrations | varies | "Migrate unlimited clients" | `migrate_qb_partner` $499/yr |

**The migration trigger price points** (when the customer starts looking):
- **$99/mo** (Plus): they look casually but rarely move
- **$140/mo** (Plus + payroll): they start Googling alternatives
- **$235/mo** (Advanced): active replacement search
- **$300+/mo** (Advanced + add-ons): they will pay $500-$2000 for migration to get free of Intuit

## Section 10 — Sources & Open Questions

**Primary sources to verify against:**
- Intuit Developer docs: `developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account`
- QBO API entity reference (Account, Invoice, Bill, Customer, Item, Class, Department, etc.)
- QBD QBXML reference (Intuit QBXML SDK docs)
- Intuit pricing page (verify quarterly — they change it)
- Forums to mine for pain: r/QuickBooks, Intuit Community forums, ProAdvisor groups on LinkedIn

**Open questions for the first build:**
1. Do we ship QBO-only first, or include QBD via QBWC? (Recommendation: QBO-only first; offer "convert QBD→QBO then use ours" as the documented path.)
2. Sandbox testing — set up Intuit dev sandbox with realistic test company
3. App approval — does our migrator need to go through Intuit's app marketplace review, or can it stay as a private API consumer? (Likely private since we're not publishing on Intuit's store.)
4. Rate-limit strategy — async queue with exponential backoff?
5. Resume semantics — if import fails at hour 6 of 10, what's the resume primitive?

**Things that change yearly (re-verify in Nov each year):**
- Intuit pricing tiers (rises every fall)
- QBD discontinuation status per country
- QBO Plus feature parity (Intuit moves features between tiers)
- Sales tax automation defaults
- API field additions/deprecations
