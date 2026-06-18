# Platform Brief — Zoho Books

> The Indian-built SMB cloud accounting platform with serious global ambition. Part of the Zoho Corp suite. Modern REST API. Strong India/MENA localization. Sticky because customers usually also use Zoho CRM, Inventory, Mail, and One — Books is one tab in a 45-app suite. Migration to Odoo wins by replacing the suite, not just the accounting.

---

## Section 1 — Identity

**Vendor:** Zoho Corporation, Chennai, India. Founded 1996 by Sridhar Vembu. Bootstrapped, private, profitable. ~100M+ users across the Zoho suite globally. Cultivates an anti-VC, rural-India-employment narrative that resonates with founder customers.

**Product lines (separate SKUs, share data partially):**

| Product | Scope | Migration relevance |
|---|---|---|
| Zoho Books | Accounting (the target) | Primary |
| Zoho Invoice | Free invoicing-only (no GL) | Lightweight cousin |
| Zoho Inventory | Inventory management (separate app, integrates with Books) | Must pull if customer uses it |
| Zoho Expense | T&E expense management | Pull if used |
| Zoho Subscriptions / Billing | Recurring billing engine | Separate migration target |
| Zoho Commerce | E-commerce platform | Pull if used |
| Zoho Payroll | Payroll (IN/US/UAE/IN limited) | Country-dependent |
| Zoho CRM | CRM (related but separate) | Separate migration target |
| Zoho One | Bundle of 45+ apps including all above | The reason customers stay |

**Pricing (USD, 2026 — subject to change per region):**

| Tier | Monthly | Users | Key features |
|---|---|---|---|
| Free | $0 | 1 | <$50k revenue, basic invoicing/expenses |
| Standard | $20 | 3 | Recurring invoices, bills, multi-currency |
| Professional | $50 | 5 | Bills payable, purchase orders, sales orders |
| Premium | $70 | 10 | Custom domain, branches (multi-location), workflow automation |
| Elite | $150 | 10 | Advanced inventory, warehouse mgmt |
| Ultimate | $275 | 15 | Advanced analytics, dedicated database cluster |

Pricing in INR for India is roughly ₹1,300 / ₹3,500 / ₹5,500 / ₹12,500 / ₹22,500/mo for the same tiers.

Zoho One bundle (45+ apps including Books at Professional-equivalent): $37/employee/mo or $90/employee/mo for "Flexible" pricing.

**Installed base estimate:**
- Zoho Books: ~1M+ accounts globally
- Of those, ~300k+ active paid subscribers
- Strong concentration in India, Middle East, US, UK, Australia

**Market segments:**
- Solopreneur to mid-market (1-100 employees typical)
- Especially strong in: SaaS startups, service businesses, e-commerce sellers
- Zoho One customers (the suite buyers) are stickiest

**Geographic footprint:**
- Tier 1 (heavy): India, UAE, Saudi Arabia, US, UK, Australia, Canada
- Tier 2: South Africa, Singapore, EU (Germany, Netherlands, France via .eu region)
- Tier 3: rest of world via .com region

**Regional data residency (CRITICAL):**
- `books.zoho.com` — US
- `books.zoho.in` — India
- `books.zoho.eu` — EU (Netherlands)
- `books.zoho.com.au` — Australia
- `books.zoho.com.cn` — China (operated by partner)
- `books.zoho.sa` — Saudi Arabia (newer)

Customer's data is in exactly one region. Migrator must hit the right endpoint or get nothing. Region detection is a pre-flight step.

## Section 2 — User Psychology

**Why people choose Zoho Books:**
1. Modern, web-native UI (vs Tally / QB Desktop)
2. Cheap entry tier (Standard $20 vs QBO Plus $99)
3. Indian roots — GST built in from day 1
4. Multi-currency works out-of-box
5. Mobile apps are actually usable
6. The Zoho suite halo — if you already use Zoho CRM, Books is natural
7. UAE / KSA VAT support (Zoho was early to MENA tax)

**Why people stay:**
1. **Zoho One lock-in** — they bought the suite, ripping out Books means re-architecting CRM, Mail, Projects, Desk, Inventory, Subscriptions, Payroll
2. Custom workflows built with Deluge scripts
3. Tight Zoho CRM ↔ Books integration (auto-create invoices from won deals)
4. Multi-region data residency (EU customers love this vs US-only competitors)
5. Custom fields and reports accumulated

**Why people leave (ranked, from real customer complaints):**
1. **Manufacturing / MRP — zero** (Zoho Inventory is light; serious manufacturers leave)
2. **Tier escalation traps** — every nontrivial feature is one tier up
3. **Inventory across multiple warehouses limited** until Elite tier
4. **Custom reports very limited** — heavy users hit walls
5. **Multi-entity / inter-company consolidation weak**
6. **Workflow approval flows shallow**
7. **Branches feature is Premium+ only** — multi-location SMEs forced up
8. **Indian payroll on a separate app** at separate cost
9. **API rate limits bite at scale** (1000 calls/min on top tier)
10. **Custom fields don't surface everywhere** (e.g., report filtering)
11. **Subscriptions/Recurring lives in a different app** — confusing
12. **Outside India/MENA/US/UK/AU localization is thin**

**What they fear about migrating:**
1. Zoho CRM → Books auto-invoice integration breaks
2. Recurring invoice schedules lost
3. Deluge customizations gone
4. Custom field data dropped
5. Branch-specific tax registrations lost
6. The Steuerberater-equivalent (their accountant) won't use Odoo

**Who decides the migration:**
- Tech-literate founder (most common — Zoho Books customers skew technical)
- Or controller in growing SMB
- The accountant is often consulted but rarely vetoes — Zoho Books customers tend to be founder-driven

**Sales implication:** sell to the founder, not the accountant. The angle is "you've outgrown Zoho, the suite is holding you back, here's freedom."

## Section 3 — Data Model

Zoho Books has a clean, modern REST entity model. Easier to migrate than Tally or QBD — but the multi-app integration (Books ↔ Inventory ↔ Subscriptions ↔ CRM) is where complexity lives.

### Core entities (single-org)

| Zoho Books Object | Odoo Target | Notes |
|---|---|---|
| Chart of Accounts (chartofaccounts) | `account.account` | Account types map directly |
| Customer (contacts, contact_type=customer) | `res.partner` customer_rank=1 | |
| Vendor (contacts, contact_type=vendor) | `res.partner` supplier_rank=1 | |
| Customer/Vendor with both flags | `res.partner` with both ranks | |
| Item (item_type=inventory) | `product.template` type=`product` | Storable |
| Item (item_type=service) | `product.template` type=`service` | |
| Item (item_type=sales_and_purchases / sales / purchases) | `product.template` type=`consu` | |
| Composite Item / Bundle | `product.template` + product set logic | Bundle expansion at sale |
| Tax | `account.tax` | Country-aware via l10n_xx |
| Tax Authority / Tax Agency | `res.partner` (gov entity) | |
| Tax Group | `account.tax` with children | |
| Branch (Premium+) | `res.company` OR analytic plan | **Decision per customer** |
| Currency | `res.currency` | Built-in |
| Project | `project.project` | Native Odoo project |
| Reporting Tag | `account.analytic.account` | One plan |
| Custom Field | `x_studio_*` (Studio) or `ir.model.fields` | Best-effort |
| Workflow Rule | NOT migrated | Manual rebuild list |
| Deluge Function | NOT migrated (source not exposed) | Manual rebuild list |
| Email Template | NOT migrated | Customer recreates |
| Document (in Documents folder) | `ir.attachment` | OAuth scope required |
| Bank Account | `account.journal` + `account.account` (Bank) | |
| Payment Method | `account.payment.method` | |

### Transactions

| Zoho Books Object | Odoo Target | Notes |
|---|---|---|
| Estimate (Quote) | `sale.order` state=draft/sent | Needs `sale_management` |
| Sales Order | `sale.order` state=sale | |
| Invoice | `account.move` type=`out_invoice` | |
| Credit Note | `account.move` type=`out_refund` | |
| Customer Payment | `account.payment` | |
| Recurring Invoice | `sale.subscription` or custom recurring | Separate pass |
| Retainer Invoice | `account.move` (advance) | |
| Sales Receipt (rare in Zoho) | combined invoice + payment | |
| Purchase Order | `purchase.order` | Needs `purchase` |
| Bill | `account.move` type=`in_invoice` | |
| Vendor Credit | `account.move` type=`in_refund` | |
| Payment Made | `account.payment` | |
| Expense | `hr.expense` OR `account.move` directly | Customer policy |
| Recurring Expense | recurring rule | |
| Recurring Bill | recurring rule | |
| Journal Entry (Manual Journal) | `account.move` (manual) | |
| Bank Transaction | `account.bank.statement.line` | |
| Bank Transfer | `account.move` (transfer) | |
| Currency Adjustment | `account.move` (FX gain/loss) | |
| Inventory Adjustment (in Zoho Inventory) | `stock.move` adjustment | Pull from Inventory app |

### Cross-app dependencies (the hard part)

Customer may have BOTH Zoho Books AND Zoho Inventory active. Items live in Inventory but appear in Books invoices. Stock levels live in Inventory. Migrator must pull from both:

- Books API: invoices, bills, payments, CoA, contacts
- Inventory API: stock levels, warehouses, item groups, batch/serial tracking, picking, packing, shipping
- Subscriptions API (if used): recurring plans, customer subscriptions, MRR data

## Section 4 — Hidden Complexity (the gotcha catalogue)

### 4.1 Region Mismatch

- **What Zoho does:** Each organization is hosted in exactly one regional data center. The org's region is set at signup and rarely changeable.
- **What breaks:** If migrator hits `books.zoho.com` but customer is on `books.zoho.in`, you get HTTP 404 on every request.
- **Mitigation:** Pre-flight: ask user their region OR detect via OAuth redirect (Zoho's OAuth handshake returns the user's regional accounts server). Then route all API calls accordingly.

### 4.2 Multi-Org Under One Account

- **What Zoho does:** A single Zoho user account can have multiple Zoho Books organizations (e.g., separate companies, separate countries).
- **What breaks:** Migrator must select the right org (`organization_id` query param on every call). Naive code uses the default org.
- **Mitigation:** List orgs first, ask user which to migrate (or migrate all into multi-company Odoo).

### 4.3 Branches and Tax Per Branch (Premium+)

- **What Zoho does:** Premium tier introduces "Branches" — each branch has its own address, GSTIN/VAT registration, and contact info. Invoices are issued from a specific branch.
- **What breaks:** Two mapping paths:
  - Map branches to `res.company` records (full multi-company in Odoo — clean but heavy)
  - Map branches to analytic accounts on a Branch plan (lightweight but loses tax-registration-per-branch)
- **Mitigation:** Decision per customer. Multi-state Indian customer with multiple GSTINs → multi-company. Single-GSTIN multi-location customer → analytic.

### 4.4 Recurring Profiles (Three Types, Separate Entities)

- **What Zoho does:** Recurring Invoices, Recurring Bills, Recurring Expenses — three distinct entities with their own APIs. Each has a profile (schedule, customer/vendor, items, next_invoice_date) and history of generated transactions.
- **What breaks:** Migrators often pull only generated invoices and miss the recurring profiles. Three months later customer wonders why no new invoices.
- **Mitigation:** Pull each recurring type explicitly. Map to Odoo's `sale.subscription` or recurring `account.move` via cron.

### 4.5 Composite Items / Bundles

- **What Zoho does:** Bundle item that expands into component items at sale. NOT a BOM (no assembly tracking). When sold, stock of components decreases, not the bundle.
- **What breaks:** Odoo has product sets (sale_product_pack) or kits in MRP. Wrong choice → either stock or sales reporting breaks.
- **Mitigation:** Use `sale_product_pack` (community module) for sales-side bundles. Use MRP kit for production-side.

### 4.6 GST Implementation (India)

- **What Zoho does:** Clean GST: CGST/SGST/IGST/UTGST/Cess per line, place of supply, RCM flag, GSTIN validation per contact, GSTR-1/3B/9 reporting.
- **What breaks:** Mapping the per-line GST decomposition (CGST 9% + SGST 9% on intra-state, IGST 18% on inter-state) requires the right `l10n_in` tax setup in advance.
- **Mitigation:** Install `l10n_in` and create CGST/SGST/IGST taxes before importing. Map by rate + place-of-supply logic.

### 4.7 MENA VAT (UAE / KSA / Bahrain / Oman / Egypt)

- **What Zoho does:** Strong MENA support. UAE VAT 5%, KSA VAT 15% (since 2020), Bahrain 10%, Oman 5%, Egypt 14%. KSA also requires e-invoicing (FATOORA / ZATCA) with QR codes and clearance integration.
- **What breaks:** KSA's Phase 2 e-invoicing requires invoices to be cryptographically signed and cleared through ZATCA. Zoho integrates with ZATCA. The signed XML and clearance IDs must preserve.
- **Mitigation:** Use `l10n_sa` / `l10n_ae` modules. For KSA invoices, preserve `zatca_invoice_uuid`, `zatca_hash`, and clearance UUID in custom Odoo fields. Build a ZATCA companion module for ongoing.

### 4.8 Multi-Currency Gain/Loss

- **What Zoho does:** Automatically calculates and posts FX gain/loss per transaction when payment settles in different rate. Stores exchange_rate on each transaction header.
- **What breaks:** Odoo's revaluation can produce different results if rate history differs.
- **Mitigation:** Pull rate history first (`res.currency.rate`), then transactions. Odoo will compute gain/loss matching Zoho's logic.

### 4.9 API Rate Limits

- **What Zoho does:** Rate limits per organization, per tier:
  - Free: 25 req/min
  - Standard: 100 req/min
  - Professional: 500 req/min
  - Premium: 750 req/min
  - Elite/Ultimate: 1000 req/min
- **What breaks:** Migrating a 5-year-old Premium customer with 200k invoices at 750/min = ~5 hours of pure API time.
- **Mitigation:** Throttle + exponential backoff on 429. Run during low-traffic hours. Use pagination with `per_page=200` (max).

### 4.10 OAuth Scope Granularity

- **What Zoho does:** Separate OAuth scopes per app and per data type. Books needs `ZohoBooks.fullaccess.all`. Inventory needs `ZohoInventory.fullaccess.all`. Documents need separate scope.
- **What breaks:** Migrator gets some data, then 401s on attachments because docs scope wasn't requested.
- **Mitigation:** Request all needed scopes upfront in OAuth consent screen. Show user which apps will be accessed.

### 4.11 Custom Fields Don't Survive Cleanly

- **What Zoho does:** Custom fields on contacts, items, invoices — each typed (text, number, date, dropdown). Stored in API response under `custom_fields` array per record.
- **What breaks:** Mapping to Odoo requires either Studio fields (license cost) or `ir.model.fields` direct creation (admin-only, painful) or stashing into a JSON note (lossy but cheap).
- **Mitigation:** Surface custom fields in pre-flight; let user choose per-field: (a) create Studio field, (b) map to existing Odoo field, (c) stash into notes/description, (d) drop.

### 4.12 Deluge Custom Functions

- **What Zoho does:** Premium+ allows Deluge scripts (Zoho's proprietary scripting language) to trigger on events. Source code is not exposed via API (only function metadata).
- **What breaks:** Customer relied on a Deluge function to auto-apply discounts; in Odoo it's silently absent.
- **Mitigation:** Surface presence-of-functions in pre-flight report. Document the manual rebuild as a deliverable.

### 4.13 Reporting Tags vs Branches vs Projects (Three-Axis)

- **What Zoho does:** Three orthogonal dimensions: Branch (where), Project (what for), Reporting Tag (free-form).
- **What breaks:** Pre-17 Odoo has one analytic plan. Loses two axes.
- **Mitigation:** Require Odoo 17+. Create three plans: Branch, Project, Tag.

### 4.14 Bills vs Expenses

- **What Zoho does:** Bills are vendor invoices (have a vendor contact, payable, tracked in AP). Expenses are non-vendor cash outflows (uploaded receipt, paid by employee, reimbursable). Different schema, different workflows.
- **What breaks:** Both must migrate but to different Odoo targets — Bills → `account.move` in_invoice; Expenses → `hr.expense` or `account.move` directly per policy.
- **Mitigation:** Two-pass migration. Ask user: "Expenses → employee expense module or direct GL?"

### 4.15 Document Attachments

- **What Zoho does:** Each invoice/bill/transaction can have attachments stored in Zoho Documents. Linked via `documents` array on the transaction. Binary fetched via separate Document API.
- **What breaks:** Without explicit attachment pass, all uploaded receipts/PDFs disappear.
- **Mitigation:** After main migration, iterate all transactions, download each attachment, re-attach via `ir.attachment` linked to corresponding Odoo record.

### 4.16 Webhook State Loss

- **What Zoho does:** Customer may have configured webhooks to other systems (Shopify, payment gateways, custom apps) on Books events.
- **What breaks:** After migration these still fire from Zoho on stale data, or worse, customers expect Odoo to fire the same webhooks.
- **Mitigation:** Pre-flight: list all configured webhooks; document for rebuild in Odoo (`base.automation` or external service).

## Section 5 — Export Surface

### Zoho Books REST API v3

- **Base URL:** regional, e.g., `https://www.zohoapis.in/books/v3/` for India.
- **Auth:** OAuth 2.0, refresh tokens. Apps registered at Zoho API Console (also regional).
- **Pagination:** `?page=N&per_page=200` (max 200 per page).
- **Headers:** must include `organization_id` either as query param or header.
- **Rate limits:** tier-dependent (see 4.9).
- **Webhooks:** for ongoing sync (not relevant to one-shot migration).
- **Sandbox:** Zoho doesn't really do sandbox — recommend customer creates a test org for migration testing.

### Zoho Books Manual Export

- Admin → Backup → Download backup ZIP
- Contains CSV per entity
- Lossy: not all custom fields surface; attachments not included
- Used by accountants for offline review; not great for migration

### CSV Export Per List View

- Each list view (Customers, Invoices, etc.) has Export → CSV/XLS
- Lossy: visible columns only
- Backup option for partial migrations

### Cross-App APIs (must coordinate)

- Zoho Inventory: separate API, separate OAuth scope (`ZohoInventory.fullaccess.all`)
- Zoho Subscriptions: separate API
- Zoho Expense: separate API
- Zoho CRM: separate (if customer wants CRM data migrated too)

### What You Can NEVER Get Out

1. Deluge custom function source code
2. Custom report definitions (saved filters, columns)
3. Email send history (logs only show send-event, not content)
4. User permission grant history (some audit log available, paywalled)
5. Login session history
6. Workflow rule logs (which records fired which workflow)

## Section 6 — Odoo Mapping (key tables)

### Account type mapping

| Zoho `account_type` | Odoo `account.account.type` |
|---|---|
| `bank` | Bank and Cash |
| `cash` | Bank and Cash |
| `credit_card` | Credit Card |
| `accounts_receivable` | Receivable |
| `other_current_asset` | Current Assets |
| `fixed_asset` | Fixed Assets |
| `other_asset` | Non-current Assets |
| `accounts_payable` | Payable |
| `other_current_liability` | Current Liabilities |
| `long_term_liability` | Non-current Liabilities |
| `equity` | Equity |
| `income` | Income |
| `other_income` | Other Income |
| `cost_of_goods_sold` | Cost of Revenue |
| `expense` | Expenses |
| `other_expense` | Other Expense |

### Invoice mapping

| Zoho field | Odoo `account.move` field | Transform |
|---|---|---|
| `invoice_id` | external_id (`ZB-{invoice_id}`) | Direct |
| `invoice_number` | `name` | Direct |
| `date` | `invoice_date` | ISO |
| `due_date` | `invoice_date_due` | ISO |
| `customer_id` | `partner_id` | Lookup by external_id |
| `branch_id` | `analytic_distribution` (branch plan) OR `company_id` | Per-decision |
| `currency_code` + `exchange_rate` | `currency_id` + `currency_rate` | |
| `line_items[].item_id` | line `product_id` | Lookup |
| `line_items[].quantity` | line `quantity` | Direct |
| `line_items[].rate` | line `price_unit` | Direct |
| `line_items[].discount` (percent or amount) | line `discount` | Convert if amount→percent |
| `line_items[].tax_id` | line `tax_ids` | Lookup |
| `line_items[].project_id` | line `analytic_distribution` (project) | |
| `line_items[].tags[]` | line `analytic_distribution` (tag plan) | |
| `cf_*` (custom fields) | `x_studio_*` or notes | Per-field decision |
| `notes` | `narration` | |
| `terms` | `invoice_payment_term_id` | Lookup by name |
| `e_invoice_details.irn` (India) | `l10n_in_irn` | Direct |
| `zatca_invoice_uuid` (KSA) | `l10n_sa_zatca_uuid` | Direct |
| `attached_documents[]` | `ir.attachment` | Separate pass |

### Reconciliation queries

```sql
-- Trial Balance check
SELECT a.code, a.name,
       SUM(l.debit) AS debit, SUM(l.credit) AS credit
FROM account_move_line l
JOIN account_account a ON a.id = l.account_id
WHERE l.parent_state = 'posted' AND l.date <= '{cutover}'
GROUP BY a.code, a.name;

-- Open invoices per customer (compare to Zoho AR aging)
SELECT p.name AS customer,
       COUNT(*) AS open_count,
       SUM(m.amount_residual_signed) AS open_amount
FROM account_move m
JOIN res_partner p ON p.id = m.partner_id
WHERE m.move_type = 'out_invoice'
  AND m.amount_residual > 0
GROUP BY p.name
ORDER BY open_amount DESC;

-- Recurring profile count (manually compare with Zoho recurring count)
SELECT COUNT(*) FROM sale_subscription WHERE state IN ('open','pending');
```

## Section 7 — Migration Risk Register

| Rank | Failure | Probability | Customer impact | Mitigation |
|---|---|---|---|---|
| 1 | Recurring profiles silently dropped | High | Customer billing stops 30 days later | Separate recurring-pass migration |
| 2 | Cross-app data (Inventory/Subscriptions) not pulled | High | Stock levels wrong, MRR data lost | Multi-app OAuth + pull from each |
| 3 | Region mismatch | Low (with detection) | Total failure | Region detection in OAuth handshake |
| 4 | Multi-branch GSTIN handling | Medium | India multi-state filings wrong | Branch → multi-company decision tree |
| 5 | E-invoice IRN/QR (India) or ZATCA UUID (KSA) lost | Medium | Audit risk | Preserve in dedicated fields |
| 6 | Deluge custom functions lost | High | Customer workflows broken silently | Surface presence in pre-flight |
| 7 | Custom fields mapping ambiguous | Medium | Data lost or stuffed in notes | Per-field user decision |
| 8 | Composite items mishandled | Medium | Stock or sales reporting wrong | Choose between product_pack vs MRP kit |
| 9 | Three-axis (Branch/Project/Tag) collapsed | Medium | Management reports broken | Require Odoo 17+ |
| 10 | Bank reconciliation state lost | Medium | Customer re-reconciles | Pull `bank_transaction.status` |
| 11 | Attachments not downloaded | Medium | Receipts disappear | Separate attachment pass |
| 12 | Webhook state not documented | Low | External system integration broken | Pre-flight webhook list |
| 13 | Multi-currency gain/loss reposts | Low | Small FX divergence | Pull rate history first |
| 14 | API rate limits delay migration | Medium | Cutover window blown | Throttle, schedule overnight |
| 15 | Customer/Vendor as same entity (dual role) | Low | Duplicate partners | Dedup logic on contact_id |
| 16 | Subscriptions app entirely missed | Medium | MRR data lost | Detect via OAuth scope check |

## Section 8 — Marketing Hooks

**SEO long-tails:**
1. "migrate zoho books to odoo"
2. "zoho books alternative open source"
3. "zoho books to odoo migration"
4. "zoho one alternative"
5. "zoho books tier upgrade alternative"
6. "zoho books manufacturing"
7. "zoho books multi-warehouse"
8. "zoho books multi-entity consolidation"
9. "leaving zoho books"

**Pain themes from forums (paraphrased, verify before quoting):**
- "Just hit my user limit AGAIN. Premium is $70/mo for 10 users — I have 12"
- "Zoho One sounds great until you realize you're paying $37 per employee for apps you don't use"
- "Their inventory is OK but my factory needs real MRP"
- "I have 4 branches but Branches feature is Premium-only"

**Killer wedge:**
> *"Zoho One is brilliant — for the first 30 employees. After that you're paying $1,000+/month for 45 apps when you only use 6. Migrate to Odoo: pay once for our migrator, keep every invoice and contact, and run the same workflows for ₹0/month in software costs. Forever."*

**Comparison angles:**
- Zoho One ($37/employee × 30 employees) = $13,320/year recurring
- Odoo Community (free) + our migrator ($99) + Odoo.sh ($25-50/mo for 30 users) = $700-900/year
- Or Odoo Enterprise ($28/user/mo) = $10,080/year — competitive but you OWN the data

**The Zoho One trap angle:**
- Zoho's pricing structure rewards 1-30 employees and punishes growth past that. Build a calculator: "Enter your headcount → see what Zoho One costs vs Odoo over 5 years."

## Section 9 — Pricing & Packaging Insight

**Our pricing relative to Zoho pain:**

| Customer profile | Zoho monthly | Migration value-prop | Our SKU |
|---|---|---|---|
| Free / Standard | $0-20 | Not the target — too small | n/a |
| Professional (5 users) | $50 | "Marginal save, no real wedge" | `migrate_zoho_lite` free (lead magnet) |
| Premium (10 users) | $70 | "Save $840/yr, get manufacturing" | `migrate_zoho_pro` $99 |
| Elite/Ultimate | $150-275 | "Outgrowing the suite" | `migrate_zoho_pro` $99 + agency |
| Zoho One (30+ employees) | $1,000+ | "Replace the whole suite" | `migrate_zoho_one_bundle` $999+ (bundles Books+CRM+Inventory migrators) |

**Migration triggers:**
- Hitting 10-user cap on Premium → look at Elite ($150)
- 30+ employees on Zoho One → costs become significant
- Need real manufacturing → Inventory app insufficient
- Multi-entity consolidation → Books can't do it
- Specific country localization missing (e.g., German bookkeeping standards)

## Section 10 — Sources & Open Questions

**Primary sources to verify against:**
- Zoho Books API docs: `www.zoho.com/books/api/v3/`
- Zoho Developer Portal: `api-console.zoho.com` (regional)
- Zoho Books pricing page (verify quarterly — they tier-juggle)
- Reddit: r/zoho (small but real complaints)
- Zoho Community forum: `help.zoho.com/portal/en/community/zoho-books`
- LinkedIn: Zoho One customer testimonials and complaints

**Open questions for the first build:**
1. Books-only first, or include Inventory in same migrator? (Recommendation: Books-only at $99, Inventory companion at $99, bundle at $149.)
2. Detect Zoho One vs standalone Books — bigger upsell to Zoho One customers (bundle migrator).
3. Recurring profile migration — into `sale.subscription` (needs `sale_subscription` module, only Enterprise) vs custom cron-driven invoicing? (Recommendation: custom cron for Community-friendly path.)
4. Custom fields — Studio license is $24/mo per Odoo user. Should we bypass Studio and create `ir.model.fields` directly? (Yes — that's our advantage. Bypass studio.)
5. ZATCA Phase 2 KSA — does the migrator need to invoke ZATCA APIs for re-clearance of historical invoices? (No — historical clearances are preserved as audit data; new go-forward Odoo invoices use Odoo's ZATCA integration.)

**Things that change yearly (re-verify in November):**
- Zoho pricing tiers (annual juggling, watch for renames)
- API rate limits (sometimes adjusted)
- New product launches (Zoho launches new apps every year — check for Books-adjacent)
- KSA ZATCA phases (new waves of taxpayers enrolled annually)
- India GST changes (council meetings ~quarterly)
