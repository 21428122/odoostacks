# Platform Brief Template — The Decoder Method

A Platform Brief is a single document that captures *everything a migrator app builder, salesperson, and support engineer need to know* about a source platform we want to migrate customers off of. Each brief is the foundation for:

1. The migrator app code (schema mapping, edge cases)
2. The marketing site (pain points to rank for)
3. The agency sales deck (objection handling)
4. The customer support runbook (failure modes)

Every brief follows this exact structure so they are comparable and grep-able.

---

## Section 1 — Identity

- **Vendor & ownership** (company, parent, country of HQ)
- **Product lines** (separate SKUs / variants — e.g. QBO vs QBD, Tally Prime vs ERP9)
- **Versions in the wild** (still-supported releases, EOL dates)
- **Pricing tiers** (what each tier unlocks, current $/€/₹ per tier)
- **Total addressable installed base** (estimate by region)
- **Market segments** (solopreneur, SMB, mid-market, enterprise — who actually buys it)
- **Geographic footprint** (countries where it's dominant, where it's blocked)

## Section 2 — User Psychology

- **Why people choose it** (the original buying triggers)
- **Why people stay** (lock-in mechanisms — data, habit, accountant relationship)
- **Why people leave** (the top 10 reasons, ranked)
- **What they fear about migrating** (data loss, downtime, retraining)
- **Who makes the migration decision** (founder, controller, external accountant)

## Section 3 — Data Model

For every business object the platform contains:

- Object name (source) → Odoo equivalent
- Required fields, optional fields, computed fields
- Relationships (parent-child, many-to-many)
- Lifecycle (draft → posted → reconciled etc.)
- Special handling (deleted vs voided vs archived)

Cover at minimum:
- Chart of Accounts / GL
- Customers / Vendors / Contacts
- Products / Items / Services
- Sales documents (Quote, Order, Invoice, Credit Note, Receipt)
- Purchase documents (PO, Bill, Bill Payment, Vendor Credit)
- Payments (in/out, methods, undeposited holding patterns)
- Banking (accounts, transactions, reconciliation state, statements)
- Journal entries / general journal postings
- Inventory (warehouses, locations, valuation method, adjustments)
- Taxes (codes, groups, jurisdictions, agencies)
- Multi-currency (rate sources, revaluation behavior)
- Dimensional tracking (classes, locations, departments, projects)
- Attachments / documents
- Custom fields
- Users / permissions / audit log
- Memorized / recurring transactions
- Reports & saved customizations

## Section 4 — Hidden Complexity (the gotcha catalogue)

The non-obvious design decisions that break naive migrators. Each entry:

- **What the platform does** (the surprising behavior)
- **Why it does that** (accounting / historical reason)
- **What goes wrong if ignored** (the symptom the customer will see)
- **How to handle it in the migrator** (the mapping strategy)

Examples: undeposited funds buffers, item-as-three-accounts patterns, virtual entries, batch numbering, voucher chains, currency revaluation snapshots, opening balance equity, retained earnings closing entries.

## Section 5 — Export Surface

- **APIs** (auth model, rate limits, completeness, pagination, versioning)
- **File exports** (formats, what's included vs locked, can it be done from the UI)
- **Backup formats** (proprietary or readable, what's needed to parse)
- **Third-party export tools** (what consultants currently use)
- **What you can NEVER get out** (the data customers think they have but don't)

## Section 6 — Odoo Mapping

For each object listed in Section 3, the destination:

- Odoo model (e.g. `account.move`, `product.template`)
- Field-by-field mapping with transforms
- Lossy mappings (what gets compressed / dropped)
- Required pre-conditions in Odoo (modules, chart of accounts, journals)
- Post-migration reconciliation queries (SQL/ORM to verify match)

## Section 7 — Migration Risk Register

A ranked list of failure modes:

| Rank | Failure | Probability | Customer impact | Mitigation |
|---|---|---|---|---|

Each row covers a real way a migration breaks (trial balance mismatch, AR aging delta, inventory valuation drift, tax filing divergence, attachment loss, audit log loss).

## Section 8 — Marketing Hooks

The keywords, pain phrases, and competitive angles to use in:

- SEO landing page H1s
- Google Ad copy
- LinkedIn posts
- Comparison tables vs Odoo
- Agency sales decks

Include: 5 long-tail search queries with intent, 3 pain quotes from forums (real, attributed), 1 "killer wedge" sentence — the one line that closes the sale.

## Section 9 — Pricing & Packaging Insight

- Their pricing structure → our anchor for "migrate and save"
- The tier at which customers feel the squeeze (the migration trigger)
- ROI math: how much they save in year 1 by switching

## Section 10 — Sources & Open Questions

- Citations (docs URLs, forum threads, accountant blogs)
- Things we don't know yet and should research
- Version-dependent claims that need re-verification
