# /u/ODOOITYOURSELF — Profile & Expertise Synthesis

Source: full crawl of public Reddit profile, 2026-05-16.
Raw data: `about.json`, `submitted.jsonl` (44 posts), `comments.jsonl` (745 comments).
Analysis scripts: `../fetch_odooityourself.py`, `../analyze_odooityourself.py`, `../dig_odooityourself.py`.

## Identity

- Handle: ODOOITYOURSELF (= "Odoo It Yourself")
- Bio: *"ODOO consultant trying to help others while I continue learning. If you'd like to sign up for one of my coaching packages, feel free to reach out."*
- Account: created 2023-10-18, verified email, 374 total karma (32 link / 342 comment)
- Activity: 745 comments + 44 posts over 937 days = ~24 comments/month steady cadence
- Subreddit footprint: 696/745 comments in r/Odoo (94%), then r/startups, r/ChannelMakers (he's growing a YouTube channel), r/Accounting, r/excel, r/QuickBooks, r/ERP, r/Netsuite
- **YouTube channel** is the real asset — 74 of 745 comments (~10%) link to his videos/playlists. The Reddit presence is content-marketing for the channel + 1:1 coaching upsell.

## Self-stated background

> "I in the accounting side among other things and have spent most of my career in accounting and financial analysis."

US-based. Treats Odoo accounting as an "Xero-like, GAAP-compliant" system, not a QuickBooks alternative. This is unusual — most r/Odoo "experts" are developer-first, not accountant-first.

## Wheelhouse — verified strong from comment content

1. **Odoo Accounting (deep)** — bank reconciliation/suspense accounts, journal entries, lock dates (Journal Entries / Tax Return / All Users), multi-company consolidation, GAAP vs Xero-style differences. Most consultants he encounters "have no idea how to do accounting let alone consolidate financials."
2. **Server actions + Python automation** — drops actual working snippets, e.g. `env['ir.actions.report'].browse(1248).report_action(env['mrp.production'].browse(record.x_manufacturing_order.id))`. Has a "Basic Python in ODOO for Beginners" playlist.
3. **PDF / QWEB reports** — dedicated playlist; openly says the post-v16 report builder is "a definite mess."
4. **Studio (pragmatic)** — recommends "prove a concept in studio, then move it into a real module/app." Warns studio is NOT upgrade-proof despite Odoo marketing.
5. **Hosting trade-offs** — odoo.com vs odoo.sh vs self-hosted. Owns a comparison video. Often used as his opening question to a stranger.
6. **QB → Odoo migrations** — repeatedly handles these for US clients. Comfortable with imports + small code; uses XMLRPC for Odoo→Odoo.

## His consistent theses (worth borrowing or testing)

- **AVOID Odoo Success Packs.** Repeated in dozens of threads. *"I would never recommend a success pack. The actual success percent from those is abysmally low."*
- **DIY-with-coaching is real for SMBs.** Brand thesis. Channel videos: "5 Reasons Why You Can Implement ODOO Yourself."
- **Vet your partner via Glassdoor — turnover is the killer.** *"If your project manager leaves, you'll be lucky if you don't have to explain everything all over again and they'll likely charge you for that too."* Names OSI as best US partner "but at a premium."
- **Inventory/manufacturing is Odoo's real strength. Accounting is "good enough."** *"I generally would have a strong preference for Odoo wherever inventory is concerned."* Says he'd never jump to Odoo just for accounting.
- **V16 = best stable, V17 took a step back, V19 accounting changes are bad** — *"the change in inventory accounting. Much less detailed and more of a 'well we can't do this right so we'll just force it to be right with a blanket journal entry'… I'd hate to ever try to break this down for an auditor."* Strong real-user signal for our v18-stayer / version-lag thesis.
- **Odoo's own AI doc digitization has regressed.** *"It used to be better than it is now… most times will just give you a total instead of the line item detail. Something built on Claude Haiku these days is way way more reliable and customizable and actually isn't that hard to put together."* He's actively building AI alternatives.
- **Future of Odoo (2026-05-13):** *"Community base, vibe coded additions."* Aligned with our marketplace thesis.

## Tech stack he uses

- Antigravity + Claude Opus as primary AI coding harness (2026-03-10) — same harness we're on
- Claude Haiku for production doc-digitization replacement
- ChatGPT for debugging server actions
- Comfortable: XMLRPC, REST, webhooks (Zapier), Plaid/Yodlee, Gusto, SMS, WhatsApp, Cloudflare in front of Odoo, scraping

## Notable gaps (where we, not he, have leverage)

- **EU/India compliance, e-invoicing, Peppol, ViDA, GST, myDATA, e-SLOG** — essentially absent from his 745 comments. He's US-only.
- **Not an apps.odoo.com seller.** Only 4 mentions of the app store across all comments, all as a consumer/recommender. He's a services business, not a marketplace publisher. So **he is NOT a competitor to our app pipeline.**
- Light on PEPPOL/e-invoicing/GST/India/Slovenia/Germany — our entire moat.

## Why he is useful to us

1. **His audience IS our buyer.** SMBs who watched a "do it yourself" YouTube tutorial and now need a $19-$149 app instead of a $20k success pack. The DIY-coaching subscriber base maps cleanly onto our marketplace audience.
2. **Accounting-grade validation.** If we ever want a second pair of eyes on the accounting plumbing of a QB→Odoo migrator or e-invoicing GL postings, he is one of the few US-side Reddit voices who'd catch a real GL error.
3. **Distribution lever (later).** Affiliate / sponsored video on his YouTube for a specific app launch (QB→Odoo migrator is the obvious one — it's exactly his beat). Not for the EU/India compliance apps, where his audience is wrong.
4. **Confirmation of three of our theses:**
   - v19 accounting changes are real pain (version-surcharge / v18-stayer app thesis)
   - Odoo's native AI is weak vs Claude (Migration Pickaxe + AI-companion app thesis)
   - Success packs are loathed (our app pricing is way cheaper than the entry bar he attacks)
5. **Anti-pattern to watch.** He earns from coaching/consulting, not from products. Sustained-but-modest karma + 24-comment/month cadence shows the cost of running a Reddit-first content strategy without products to scale. We should design our content with products at the end of the funnel, not coaching.

## Concrete next moves (suggested, not done)

- Watch "A Whirlwind Overview of ODOO" + "5 Reasons Why You Can Implement ODOO Yourself" + "Which Hosting Option for ODOO is Right For You?" to clone his SMB framing.
- Map his top playlists (PDF Reports v17, Accounting for Beginners, Basic Python for Beginners) against our app roadmap — these are the topics his SMB audience already searches for.
- Once a QB→Odoo migrator ships, draft a polite affiliate-pitch DM referencing 2-3 of his specific QB-migration threads.
- Do NOT ask for help on EU/India apps — out of scope for him.
