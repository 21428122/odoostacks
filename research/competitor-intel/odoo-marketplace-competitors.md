# Odoo apps.odoo.com — competitor intelligence (2026-05-17)

**Source:** local DuckDB snapshot at `data/odoo.duckdb` (captured 2026-05-08, 67,370 listings, 6,775 publishers).
**Reproduce:** `python scripts/competitor_leaderboard.py` → writes `data/competitors/leaderboard.json`.

All dollar figures are **estimated gross revenue** = `price × purchases`. Marketplace takes 30%; Odoo Enterprise prerequisites cost extra. Treat as upper-bound proxies, not net income.

---

## 1. Profitable publishers — top 15 by lifetime estimated gross

These are the operators making money. Treat their public catalog as the canvas. Treat their GitHub as the blueprint.

| # | Publisher | Lifetime gross | Apps | Last-mo gross | GitHub | Model |
|---|---|---:|---:|---:|---|---|
| 1 | **Ksolves India Ltd.** | $3,843,640 | 75 | $31,367 | [ksolves-store](https://github.com/ksolves-store) — 5 repos (mostly LGPL trial apps; paid catalog at [store.ksolves.com](https://store.ksolves.com/)) | Focused, premium apps + own storefront |
| 2 | **Emipro Technologies** | $3,370,289 | **10** | **$50,012** | [emiprogithub](https://github.com/emiprogithub) — 3 repos; [bamtech/odoo-addons](https://github.com/bamtech/odoo-addons) | **Best per-app revenue in market** — 10 apps, $337K each. Amazon / eBay / Shipstation connectors. |
| 3 | **Webkul Software** | $2,717,500 | 1,039 | $21,060 | [webkul](https://github.com/webkul), [webkul-odoo-team](https://github.com/webkul-odoo-team) | Massive shotgun + own marketplace [store.webkul.com](https://store.webkul.com) |
| 4 | **BROWSEINFO** | $2,603,618 | 1,516 | $18,080 | [browseinfo](https://github.com/browseinfo) — 54 repos | Highest-volume shotgun in the catalog |
| 5 | **Probuse Consulting** | $2,373,171 | **1,722** | $13,485 | Bitbucket private (no public GitHub); has 2 DMCA takedowns of pirated mirrors | Most apps in the catalog, all proprietary |
| 6 | **Softhealer Technologies** | $1,761,132 | 1,528 | $16,680 | Unofficial mirror [automatuanis/softhealer](https://github.com/automatuanis/softhealer); 1 DMCA takedown filed by them | Shotgun, Silver Partner |
| 7 | **Almighty Consulting** | $1,442,592 | 253 | $28,762 | [AlmightyCS](https://github.com/AlmightyCS) | Hospital + recurring procedure niche (sole leader in SOP-adjacent) |
| 8 | **faOtools** | $1,326,937 | 95 | $15,741 | **No GitHub — proprietary** (faotools.com/tools-licensing forbids redistribution) | Focused premium, ~100 apps, ZERO public source |
| 9 | **Serpent Consulting** | $1,028,229 | 578 | $1,512 | [SerpentCS](https://github.com/SerpentCS) — 54 repos, [JayVora-SerpentCS](https://github.com/JayVora-SerpentCS) — 59 repos | Gold partner, EduERP + HotelMS open source |
| 10 | **VentorTech** | $924,699 | **25** | **$32,125** | [ventor-tech](https://github.com/ventor-tech) — 17 repos (QB connector itself is proprietary) | **Closest model for you** — small, focused, premium, $32K/mo |
| 11 | **Center of R&D** | $729,139 | 185 | $246 | n/a | Russian, mostly v17/below |
| 12 | **Terabits Technolab** | $684,597 | 46 | $18,166 | n/a public | Focused mid-tier |
| 13 | **Pragmatic TechSoft** | $621,507 | 209 | $6,385 | [pragtech](https://github.com/pragtech) — light public footprint | Owns 3 QuickBooks SKUs (USA/Canada/Desktop) |
| 14 | **Openinside** | $492,512 | 159 | $890 | n/a public | |
| 15 | **AcruxLab** | (#1 in WhatsApp) | ~14 | high | [AcruxLab](https://github.com/AcruxLab) — 11 repos; full mirror at [vanthaiunghoa/acruxlab](https://github.com/vanthaiunghoa/acruxlab) | **WhatsApp wedge monopolist** — confirms your pivot away was correct |

### Other useful GitHub orgs
- **[CybroOdoo](https://github.com/CybroOdoo)** (Cybrosys Technologies) — 25 repos, [CybroAddons](https://github.com/CybroOdoo/CybroAddons), [OpenHRMS](https://github.com/CybroOdoo/OpenHRMS). India-based.
- **[OCA](https://github.com/OCA)** — Odoo Community Association, hundreds of free LGPL modules. Goldmines:
  - `OCA/account-financial-tools`, `OCA/account-financial-reporting` — accounting patterns
  - `OCA/openupgrade` — version-to-version migrations (direct competitor to a "Migration Pickaxe v17→v20" upgrader)
  - `OCA/server-tools`, `OCA/web` — import wizards & UI patterns
- **[odoo-code-search.com](https://odoo-code-search.com/)** — **1.9 BILLION lines of Odoo code indexed**, searchable by author/keyword. Killer tool for reverse-engineering competitor patterns. E.g. `author:"Softhealer Technologies"`.

---

## 2. Per-wedge competitive landscape (your targets)

The wedges you've memo'd: Migration Pickaxe, EU e-invoicing, India GST. Numbers are dedupe'd to latest version per (author × tech_name).

### 2.1 Migration: QuickBooks → Odoo (Migration Pickaxe core wedge)

**Total market:** 50 apps, 32 publishers, $296K lifetime gross, $3.5K last-month gross, **median paid $208**.

| Competitor | App | Price | Lifetime sales | Last-mo | Lifetime gross |
|---|---|---:|---:|---:|---:|
| Techspawn Solutions | QuickBooks Odoo Connector | **$387** | 167 | 0 | $64,699 |
| Kodershop | Quickbooks Desktop Connector | **$5,637** | 11 | 0 | $62,012 |
| Pragmatic TechSoft | QB Online Connector [USA] | $199 | 239 | 4 | $47,563 |
| VentorTech | QB Online Connector PRO | $350 | 127 | 2 | $44,428 |
| Pragmatic TechSoft | QB Desktop (QBD) Connector | $300 | 107 | 1 | $32,100 |
| Webkul | Quickbooks Online Connector | $169 | 64 | 1 | $10,815 |
| Webkul | Quickbooks Desktop Connector | $299 | 24 | 0 | $7,176 |
| Pragmatic TechSoft | QB Online Connector [Canada] | $250 | 14 | 2 | $3,500 |

**Reads as:**
- **Pricing band:** $169–$387 is the sweet spot. Kodershop's $5,637 outlier is a "white-glove + done-for-you" play; you'd need direct sales for that.
- **VentorTech and Pragmatic are the two operators still making sales this month.** VentorTech only has the one QB SKU; Pragmatic stacks 3 country variants — that's a real strategy (split US/CA/UK SKUs to capture geo-anchored search).
- **Wedge for your `migrate_quickbooks_lite`:** charge $79–$129 below the median ($208). Pitch as "CSV-based lightweight migrator" — the gap between free OCA `base_import` and the $300+ Connector PRO is exactly where a paid Lite sits.
- **No one owns the Desktop niche cheaply.** Kodershop charges $5,637 because Desktop-to-Odoo is hard. A $199 "Migration Pickaxe — QuickBooks Desktop CSV mode" is a clear wedge.

### 2.2 Migration: DATEV → Odoo (Migration Pickaxe 2027 supercycle)

**Total market:** 20 apps, 13 publishers, $42K lifetime gross, **median paid $585** (highest of any wedge studied).

| Competitor | App | Price | Lifetime | Last-mo | Lifetime gross |
|---|---|---:|---:|---:|---:|
| **ecoservice** | DATEV Export | **$760** | 32 | 1 | $24,336 |
| manaTec GmbH | manaTec DATEV Export | **$2,106** | 5 | 0 | $10,530 |
| Lexcode | DATEV CSV Export + XML | $526 | 5 | 0 | $2,632 |
| ecoservice | DATEV Import | $1,521 | 1 | 0 | $1,521 |
| ecoservice GbR | DATEV Lodas | $760 | 0 | 0 | $0 (just listed) |

**Reads as:**
- **ecoservice has 4 DATEV SKUs and owns the wedge.** German tax-advisor compliance, deep integration.
- **No public GitHub for ecoservice DATEV modules** — they protect this aggressively.
- **manaTec's $2,106 single sale × 5 = $10K** validates premium pricing for German accountancy.
- **Your DATEV companion play:** at $149-$199 you're undercutting the entire market while still 2x your QB lite price. The 2027 DATEV supercycle (per project_migration_pickaxe.md) is real; market median is $585, you have headroom.

### 2.3 Migration: Tally → Odoo (Indian SMB)

**Total market:** 11 apps, 9 publishers, $3,795 lifetime gross — **massively under-served**.

| Competitor | App | Price | Lifetime | Last-mo | Lifetime gross |
|---|---|---:|---:|---:|---:|
| Webkul | Odoo Tally Connector | $149 | 11 | 1 | $1,639 |
| NEXERP | Tally Connector (Direct XML) | $149 | 5 | 0 | $745 |
| Technaureus | Tally Balance Sheet & PL | $58 | 10 | 0 | $585 |
| Technaureus | Tally Trial Balance | $58 | 9 | 0 | $526 |

**Reads as:**
- **Webkul is the de-facto Tally leader with $1.6K lifetime.** That's not a real moat — that's an unclaimed crown.
- A Tally migrator at $79–$129 fits the India GST/e-invoice India market thesis perfectly. Tally has 1M+ India SMB seats; even 0.1% conversion = $100K+/yr.
- **WARNING:** last-month sales = 1. The market is dormant. The wedge is "Tally users migrating to Odoo because of GST 2.0 / Odoo 20 Agentic AI" — narrative-driven, not search-driven yet.

### 2.4 Migration: Zoho → Odoo

**Total market:** 31 apps, 15 publishers, $13,843 lifetime gross, **$0 last-month gross**.

| Competitor | App | Price | Lifetime gross |
|---|---|---:|---:|
| Pragmatic TechSoft | Odoo ZOHO CRM Connector | $292 | $2,632 |
| Webkul | Zoho Books Odoo Connector | $249 | $1,743 |
| BROWSEINFO | All in One Zoho Odoo Connector | $152 | $608 |

**Reads as:** **DEAD market.** Zero sales last month across 31 apps. Zoho users don't migrate; they're a different ICP. **Don't build.** The user's prior memo already concluded this; numbers confirm.

### 2.5 EU e-invoicing — broad category

**Total market:** 516 apps, 270 publishers, $141K lifetime gross, $1.8K last-month gross, **median paid $34** (low — most are localization extras, not full e-invoicing).

Notable specifics:
- **KSA Zatca Phase 2** (Altapete Solutions) — $349, 21 sales = $7,330 lifetime. Saudi e-invoicing is paid demand.
- **Guatemala FE** (Xmarts) — $596, 10 sales = $5,959. Tiny niche, premium pricing.
- The market is dominated by **Odoo Enterprise localization extensions** that are nominally "e-invoicing" but actually invoice formatting/branding.

### 2.6 Slovenia e-SLOG (your $149 published pick)

**Total market:** 3 listings, $0 lifetime gross — **NONE OF THEM ARE ACTUAL e-SLOG e-invoicing**.

| Listing | Note |
|---|---|
| Editor d.o.o. — "Travel Order Daily Reimbursement Slovenian1" | Travel/HR, v12 (abandoned) |
| Synodica — "Delivery Slovenia Post Shipping" | Shipping connector |
| Synodica — "DPD Slovenia Shipping" | Shipping connector |

**Reads as:** **You have zero direct competition in Slovenia e-invoicing today.** The 2026-06 mandate is the forcing function; you're 6–8 weeks ahead of the obvious next entrant. Ship the v18/v19/v20 builds and seed the apps.odoo.com search before someone else notices.

### 2.7 India: GST + e-invoice IRN + e-way bill

| Sub-wedge | Apps | Publishers | Lifetime gross | Notes |
|---|---:|---:|---:|---|
| `india_gst` (broad GST) | 54 | 35 | $26,437 | Webkul leads with two SKUs ($6.9K + $4.2K) |
| `india_einvoice` (IRN) | **4** | 4 | **$181** | **ZestyBeanz is the only one with any sales** ($30 × 6 = $181); E-INVOICE INDIA by Enzapps has zero. Wide open. |
| `india_tds` | 38 | 20 | $8,951 | Saturated cheap; median $53 |
| `india_eway` (E-way bill) | 432 | 179 | $163K | Noisy keyword match (many false positives like "SagepaY"); narrow before relying on this |

**India IRN-specific leaders:**

| Competitor | App | Price | Lifetime | Lifetime gross |
|---|---|---:|---:|---:|
| Webkul | GST - Returns and Invoices | $99 | 70 | $6,931 |
| Webkul | Odoo GSTR3B Returns | $198 | 21 | $4,158 |
| TeXByte | TeXByte GSTR reports | $205 | 18 | $3,686 |
| Geo Technosoft | GST E-Invoicing And E-way Bill w/5 hr support | $99 | 35 | $3,480 |
| Webkul | GST E-Way Bill | $99 | 22 | $2,176 |
| **ZestyBeanz** | GST E-Invoice and E-Way Bill (IRN) | **$30** | 6 | $181 |

**Reads as:**
- **No paid India GST app has cleared $7K lifetime.** This is your stated 2026 thesis market but **purchase volume hasn't materialized yet** — buyers either use the free Odoo Enterprise India localization or pay BrowseInfo/Webkul $99 for the cheap reports add-on.
- **The IRN-specific wedge is real but tiny.** ZestyBeanz is leading at $30. That's a pricing mistake — a properly-built IRN connector + e-way bill at $149 is defensible if you also include MasterGST/IRIS aggregator integration.
- **Geo Technosoft's $99 + 5-hour support** is the only credible bundled compete. Out-positions on support.

### 2.8 WhatsApp (confirmation of your earlier pivot)

**AcruxLab owns this wedge.** Top 8 listings = $400K+ combined lifetime gross. Their pricing tiers $99–$277.

| AcruxLab SKU | Price | Lifetime | Last-mo | Gross |
|---|---:|---:|---:|---:|
| ChatRoom BASE | $99 | 842 | 10 | $83,173 |
| ChatRoom AI ChatBot | $247 | 218 | 3 | $53,881 |
| ChatRoom CRM extra | $158 | 324 | 5 | $51,043 |
| ChatRoom Chatter | $148 | 319 | 5 | $47,078 |
| ChatRoom Marketing & Group | $277 | 151 | 3 | $41,832 |
| ChatRoom PACK | $99 | 411 | 9 | $40,599 |

Their source is public at [vanthaiunghoa/acruxlab](https://github.com/vanthaiunghoa/acruxlab) — that's a fork/leak, but it's there. **Pivoting away from WhatsApp CRM (per project_post_sop_next_app.md) was the correct call** — AcruxLab's moat is real, multi-SKU, and they actively maintain.

### 2.9 SOP / Procedure builder (your sop_builder context)

**Total market:** 25 listings, 9 publishers — **mostly false positives** (hospital/clinical procedure mgmt).

- Almighty Consulting dominates with "Recurring Procedure (Hospital Management System)" — $146 × 26 = $3,796.
- **No real "team SOP / documented standard operating procedure builder" leader exists.** Your sop_builder is the first credible entry into the actual SOP knowledge-management niche.

---

## 3. Five strategic reads

1. **Focused beats shotgun on revenue-per-app.** Emipro (10 apps, $337K each) and VentorTech (25 apps, $36K each) outearn BrowseInfo/Softhealer per-app by 100×. **Your "Migration Pickaxe + companion" focused playbook is the right model — copy Emipro/VentorTech, not BrowseInfo.**

2. **Your QuickBooks Lite has a clean $79–$129 price slot.** Pragmatic owns $199–$300, VentorTech owns $350, Kodershop white-gloves $5,637. The gap below $169 is empty. **Migration Pickaxe Lite at $99 wins the "I just need CSV import, not a live connector" buyer.**

3. **DATEV is your 2027 highest-ROI play.** Median $585, only ecoservice + manaTec are real competition, both German. **A $199 DATEV companion under ecoservice and manaTec is unclaimed.** That's the highest-priced wedge per memo confirmed by numbers.

4. **Slovenia e-SLOG is empty water.** Zero real competition. Ship v18/v19/v20 builds before the mandate triggers and you own a category overnight.

5. **India is a thesis market, not a revenue market — yet.** Total India GST+IRN+TDS lifetime gross < $50K. Webkul is the cheap-incumbent. **If 2026-07 e-invoice mandate expansion lands as expected, the wedge opens; price ABOVE $99 (where everyone clusters) with bundled MasterGST/IRIS integration.**

---

## 4. Source code intelligence (free reconnaissance)

### Public GitHub orgs you can study/lift LGPL patterns from
- [CybroOdoo/CybroAddons](https://github.com/CybroOdoo/CybroAddons) — 100s of patterns
- [SerpentCS/SerpentCS_Contributions](https://github.com/JayVora-SerpentCS/SerpentCS_Contributions) — Gold partner code from v7→v19
- [browseinfo/website](https://github.com/browseinfo/website), [browseinfo/Custom-odoo](https://github.com/browseinfo/Custom-odoo) — what they publish openly
- [OCA/openupgrade](https://github.com/OCA/openupgrade) — version migration patterns, directly applicable to Migration Pickaxe
- [OCA/account-financial-tools](https://github.com/OCA/account-financial-tools) — accounting wizards
- [ventor-tech](https://github.com/ventor-tech) — 17 repos, study their non-QB OSS for code style
- [emiprogithub](https://github.com/emiprogithub), [bamtech/odoo-addons](https://github.com/bamtech/odoo-addons) — Amazon/eBay connector patterns

### GitHub code search queries that work
- `https://github.com/search?q=%22migrate_quickbooks%22+language%3APython&type=code` — find every public copy of a competitor's manifest
- `https://github.com/search?q=quickbooks+odoo+__manifest__&type=code`
- `https://github.com/search?q=%22account.move%22+quickbooks+import&type=code`

### The unfair advantage: odoo-code-search.com
[odoo-code-search.com](https://odoo-code-search.com/) indexes **1.9 billion lines** of Odoo code, searchable by author. Examples:
- `author:"Softhealer Technologies"` → every Softhealer module ever published, including paid ones leaked into public mirrors
- `author:"Probuse Consulting Service Pvt. Ltd."` → Probuse's full corpus (they DMCA aggressively, so use carefully)
- Search for technical module names from `data/competitors/leaderboard.json` to find real implementations

### DMCA tells you who guards what
The [github/dmca](https://github.com/github/dmca) repo logs takedowns. We saw:
- Probuse (2019 — 2 separate takedowns)
- BrowseInfo (2019)
- Softhealer (2023)
- Ksolves (2023)

**Read:** these publishers actively monitor + sue. Don't republish their code. **Do** study public mirrors before they get torn down (use `odoo-code-search.com` cache).

---

## 5. Recommended next actions

| Priority | Action | Why |
|---|---|---|
| 🔴 NOW | Ship `migrate_quickbooks_lite` at $99–$129 | Empty price slot below Pragmatic/VentorTech; 4–8 sales/mo realistic at $99 |
| 🔴 NOW | Push the Slovenia e-SLOG v18/v19/v20 builds | Zero competition; 2026-06 mandate forcing function; first-mover SEO |
| 🟡 4–8 wk | Build Tally CSV migrator at $79–$129 | Webkul's $1.6K crown is unclaimed; India narrative-aligned |
| 🟡 8–12 wk | Build India IRN connector at $149 (above ZestyBeanz $30) | Wedge below Webkul's $198 GSTR3B but above ZestyBeanz floor |
| 🟢 Q4 2026 | DATEV companion at $199 | 2027 supercycle, $585 market median, only 2 real competitors |
| 🟢 Q4 2026 | Study Emipro + VentorTech architecture | Both achieve $300K+/app lifetime — same blueprint applies to your stack |

---

## 6. Reproduce / extend

```powershell
# Regenerate leaderboard from current DB
cd c:\Users\InBody\Projects\odoostacks
$env:PYTHONIOENCODING="utf-8"; python scripts/competitor_leaderboard.py
# Outputs:
#   data/competitors/leaderboard.json    (top 40 publishers + top 60 apps + 15 wedges)
```

To rescrape the marketplace for fresh numbers: `python scripts/scrape_odoo.py` (run before each monthly competitor review).

Add a wedge: edit `WEDGES` in `scripts/competitor_leaderboard.py` and re-run.
