# OdooStack

A gstack-style toolkit for finding, scoring, and shipping Odoo apps. Slash commands for Claude Code, backed by Python scripts and a local DuckDB. No hosting, no auth, no SaaS — runs on your laptop.

## What it does

You type slash commands in Claude Code. Claude becomes your full-time research analyst for the Odoo Apps marketplace.

| Command | What it does |
| --- | --- |
| `/odoo-refresh` | Scrape apps.odoo.com and update the local DB |
| `/odoo-trends` | Top trending niches this week (4-week velocity) |
| `/odoo-score [niche]` | Deep score on one niche — Trend, Opportunity, Gap |
| `/odoo-gaps` | Top unmet demand from reviews + forums (Phase 2) |
| `/odoo-research [niche]` | Full markdown brief for a niche (Phase 2) |
| `/odoo-scaffold [name]` | Generate an Odoo 18 module skeleton (Phase 3) |
| `/odoo-publish-checklist` | Pre-flight for apps.odoo.com submission (Phase 3) |
| `/odoo-help` | List commands |

## Quickstart

```bash
# 1. Install Python deps (Python 3.11+)
cd odoostack
pip install -e .

# 2. Pull a fresh snapshot (~20 minutes for full marketplace)
python scripts/scrape_odoo.py --max-pages 5    # smoke test, 100 apps
python scripts/scrape_odoo.py                  # full crawl

# 3. Load into DuckDB
python scripts/load.py

# 4. Compute scores
python scripts/score.py

# 5. See what's hot
python scripts/score.py trends --top 20
```

## Inside Claude Code

Once installed as a plugin, the same workflow becomes:

```
/odoo-refresh
/odoo-trends
/odoo-score expense-management
```

Claude will explain what's happening at each step.

## Project layout

```
odoostack/
├── skills/                     # Slash command definitions (SKILL.md)
├── scripts/                    # Python: scrape, score, scaffold
├── prompts/                    # LLM prompt templates
├── data/
│   ├── snapshots/              # Daily JSON snapshots (git-tracked)
│   ├── briefs/                 # Research outputs (git-tracked)
│   ├── modules/                # Scaffolded modules
│   └── odoo.duckdb             # gitignored
├── pyproject.toml
└── README.md
```

## Phases

- **Phase 1 (now):** scrape + Trend/Opportunity scoring + `/odoo-trends` and `/odoo-score`
- **Phase 2:** review classification + gap clustering + `/odoo-gaps` and `/odoo-research`
- **Phase 3:** module scaffolder + `/odoo-publish-checklist`

## Status

Phase 1 in progress. Scraper hits apps.odoo.com directly (no Playwright needed — pages are server-rendered Odoo views).
