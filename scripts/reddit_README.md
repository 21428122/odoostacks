# Reddit Odoo Crawler — Setup

Daily, no-LLM, no-paid-API monitoring of Odoo discussion across Reddit.
Tags every post with regex signals (client, hiring, switching, complaint,
pricing, india, help, module, version) and stores in a SQLite db at
`data/reddit/reddit.sqlite`.

## One-time setup (~3 min)

### 1. Get a free Reddit `client_id`

Reddit closed their public JSON endpoints in 2023. You need a free OAuth
client_id — no Reddit account password is shared, no approval needed,
no billing. Read-only "installed app" grant is enough.

1. Sign in at https://www.reddit.com/prefs/apps
2. Scroll to bottom, click **create another app...**
3. Fill in:
   - **name:** `odoostack-research`
   - **type:** select **installed app** (NOT "script" or "web app")
   - **redirect uri:** `http://localhost`
   - description: leave blank
4. Click **create app**
5. The string directly under the app name (right under "installed app")
   is your `client_id`. It looks like `aBc1d2EfGhIjKlMn`.

### 2. Set the env var (PowerShell, persistent)

```powershell
setx REDDIT_CLIENT_ID "aBc1d2EfGhIjKlMn"
```

Close + reopen the shell so the var is available.

### 3. Smoke test

```powershell
cd c:\Users\InBody\Projects\odoostacks
python scripts\scrape_reddit.py --subs r/Odoo --no-sitewide --limit 25
```

Expect ~25 posts, signal-tag counts, "wrote N new" line.

## Daily run

```powershell
python scripts\scrape_reddit.py
```

That's the full pull — 15 seed subs + sitewide search, ~30 sec, idempotent.

## Weekly report

```powershell
python scripts\reddit_report.py --days 7
```

Writes a markdown rollup to `data\reddit\reports\YYYY-MM-DD.md` with:
hiring/client signals, complaints, switching/migration, pricing pain,
India-specific posts, top subs, repeat authors, keyword trends.

## Schedule it (Windows Task Scheduler)

One-liner to register a daily 7 AM job:

```powershell
$action = New-ScheduledTaskAction `
  -Execute "python.exe" `
  -Argument "scripts\scrape_reddit.py" `
  -WorkingDirectory "c:\Users\InBody\Projects\odoostacks"

$trigger = New-ScheduledTaskTrigger -Daily -At 7am

Register-ScheduledTask -TaskName "OdoostackRedditCrawl" `
  -Action $action -Trigger $trigger `
  -Description "Daily Odoo Reddit signal crawl"
```

To remove: `Unregister-ScheduledTask -TaskName "OdoostackRedditCrawl" -Confirm:$false`

For weekly reports, register a second task that runs `reddit_report.py` on Mondays.

## Cost

- **Reddit API:** $0 (installed_client grant, free tier, ~100 reqs/min ceiling)
- **Compute:** local Python, ~30s/day
- **LLM tokens:** $0 (regex tagging only)

## Optional LLM upgrade

If you later want sharper labels on the flagged-signal subset, the schema
already supports it — add a `llm_label` column and run Claude Haiku over
just the rows where `signals != '[]'`. ~50 posts/day at Haiku rates is
under $0.01/day.
