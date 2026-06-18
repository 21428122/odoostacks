"""
Back-test the validator scoring formula against ground-truth marketplace outcomes.
Uses DuckDB directly — no LLM spend.

Output: accuracy metrics + bias report
"""

import sys
import duckdb
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

DB   = "data/odoo.duckdb"
RUN  = "20260508T180021Z-19e350"

MANDATORY_DEADLINE_KWS = ['e-slog','eslog','peppol','zatca','irn','eway bill',
                          'ewaybill','gst 2.0','e-invoice mandate','ksef','mydata']
MIGRATION_TRIGGER_KWS  = ['quickbooks','qbo','tally','sage','myob','dynamics gp',
                          'dynamics nav','netsuite','wave accounting','datev','busy accounting']
MIGRATOR_KEYWORDS      = ['quickbooks','qbo','tally','sage','myob','xero','dynamics',
                          'netsuite','wave accounting','zoho books','busy accounting','datev']
MIGRATOR_DEMAND_PROXY  = {
    'quickbooks':90,'qbo':90,'tally':80,'datev':85,
    'dynamics':75,'sage':65,'myob':65,'xero':70,
    'netsuite':75,'zoho books':60,'busy accounting':70,'wave':55,
}
ODOO_OWNED = ['subscription','recurring','esign','expense','elearning',
              'field service','helpdesk','repair','timesheet','appraisal']

conn = duckdb.connect(DB, read_only=True)

# ── Pull a stratified sample ──────────────────────────────────────────────────
# Winners: top 100 by total_purchases (paid only)
winners = conn.execute(f"""
    SELECT display_name, author, summary, price_cents,
           rating_stars, review_count, total_purchases, last_month_purchases
    FROM app_snapshots
    WHERE run_id='{RUN}' AND price_cents > 0 AND total_purchases > 0
    ORDER BY total_purchases DESC
    LIMIT 100
""").df()
winners["tier"] = "WINNER"

# Mid-tier: paid, 5–50 purchases
mid = conn.execute(f"""
    SELECT display_name, author, summary, price_cents,
           rating_stars, review_count, total_purchases, last_month_purchases
    FROM app_snapshots
    WHERE run_id='{RUN}' AND price_cents > 0
      AND total_purchases BETWEEN 5 AND 50
    ORDER BY total_purchases DESC
    LIMIT 100
""").df()
mid["tier"] = "MID"

# Losers: paid apps, zero purchases
losers = conn.execute(f"""
    SELECT display_name, author, summary, price_cents,
           rating_stars, review_count, total_purchases, last_month_purchases
    FROM app_snapshots
    WHERE run_id='{RUN}' AND price_cents > 0
      AND COALESCE(total_purchases,0) = 0
    ORDER BY RANDOM()
    LIMIT 100
""").df()
losers["tier"] = "LOSER"

df = pd.concat([winners, mid, losers], ignore_index=True)
print(f"Sample: {len(df)} apps  ({len(winners)} winners / {len(mid)} mid / {len(losers)} losers)")


# ── Scoring formula (mirrors dashboard logic) ─────────────────────────────────
def score_app(row, niche_df):
    """Score a single app row. niche_df = same-niche stats from DB."""
    name    = str(row["display_name"] or "").lower()
    summary = str(row["summary"] or "").lower()
    kw      = name + " " + summary

    # Niche stats
    n         = int(niche_df["n"])
    total_p   = int(niche_df["total_p"])
    velocity  = int(niche_df["velocity"])
    avg_price = float(niche_df["avg_price"] or 0)
    dead_apps = int(niche_df["dead_apps"])
    active_apps = max(int(niche_df["active_apps"]), 1)

    dead_pct  = dead_apps / n if n > 0 else 0
    avg_pur   = total_p / active_apps
    vel_per   = velocity / active_apps

    # Saturation — fewer competitors = more opportunity (data-backed, June 2026)
    if   n == 0:   sat = 50
    elif n <= 3:   sat = 90
    elif n <= 8:   sat = 75
    elif n <= 20:  sat = 55
    elif n <= 50:  sat = 35
    else:          sat = 15
    if dead_pct >= 0.80 and n > 3:
        sat = min(sat, 35)

    # Demand
    is_migrator = any(k in kw for k in MIGRATOR_KEYWORDS)
    if is_migrator:
        demand = max((MIGRATOR_DEMAND_PROXY.get(k, 50) for k in MIGRATOR_KEYWORDS if k in kw), default=60)
    else:
        if   avg_pur > 500: demand = 90
        elif avg_pur > 200: demand = 75
        elif avg_pur > 80:  demand = 60
        elif avg_pur > 20:  demand = 40
        elif avg_pur > 5:   demand = 25
        else:                demand = 10

    # Gap — anti-predictive at high weight (AUC=0.42), keep minimal
    free_count = int(niche_df["free_count"])
    paid_count = int(niche_df["paid_count"])
    low_count  = int(niche_df.get("low_count", 0))
    if   paid_count == 0: gap = 50
    elif low_count == 0:  gap = 80
    elif low_count <= 3:  gap = 60
    elif low_count <= 8:  gap = 40
    else:                  gap = 20

    # Moat
    stale = int(niche_df["stale"])
    top_share = float(niche_df.get("top_share", 50))
    if   top_share > 60: moat = 20
    elif top_share > 40: moat = 45
    elif top_share > 20: moat = 65
    else:                 moat = 85
    if stale >= 2 and paid_count > 0 and stale / max(paid_count, 1) >= 0.5:
        moat = min(95, moat + 15)

    # Momentum — highest AUC component (0.71)
    recency = velocity / max(total_p, 1)
    recency_bonus = min(20, int(recency * 200))
    if is_migrator:
        momentum = min(90, 70 + recency_bonus)
    else:
        if   vel_per > 10:  momentum = 90
        elif vel_per > 5:   momentum = 80
        elif vel_per > 2:   momentum = 65
        elif vel_per > 0.5: momentum = 45
        elif vel_per > 0.1: momentum = 25
        else:                momentum = 10
        momentum = min(90, momentum + recency_bonus)

    # Dead health
    if   n <= 3:             dead_health = 50
    elif dead_pct <= 0.40:   dead_health = 85
    elif dead_pct <= 0.55:   dead_health = 65
    elif dead_pct <= 0.70:   dead_health = 45
    elif dead_pct <= 0.85:   dead_health = 25
    else:                     dead_health = 10

    # Forced buyer
    forced_buyer = 10
    if any(k in kw for k in MANDATORY_DEADLINE_KWS):  forced_buyer = 90
    elif any(k in kw for k in MIGRATION_TRIGGER_KWS): forced_buyer = 70

    # Rating — r=0.50 with actual purchases, strongest single predictor
    avg_rating = float(niche_df.get("avg_rating", 0) or 0)
    rating_score = int(avg_rating / 5.0 * 100) if avg_rating > 0 else 50

    # 8-component formula — AUC-optimised weights (June 2026 back-test)
    viability = int(
        sat          * 0.10 +
        demand       * 0.14 +
        gap          * 0.04 +
        dead_health  * 0.10 +
        moat         * 0.12 +
        momentum     * 0.22 +
        forced_buyer * 0.13 +
        rating_score * 0.15
    )

    return {
        "sat": sat, "demand": demand, "gap": gap,
        "dead_health": dead_health, "moat": moat,
        "momentum": momentum, "forced_buyer": forced_buyer,
        "rating_score": rating_score, "viability": viability,
        "is_migrator": is_migrator,
        "dead_pct": round(dead_pct * 100, 1),
    }


# ── Get niche stats for each app (use its own name as keyword) ────────────────
print("Scoring apps...")
scores = []
for _, row in df.iterrows():
    name = str(row["display_name"] or "")
    kw   = name.split()[0] if name else "x"   # use first word as niche proxy

    niche_stats = conn.execute(f"""
        SELECT COUNT(*) as n,
               COALESCE(SUM(total_purchases),0) as total_p,
               COALESCE(SUM(last_month_purchases),0) as velocity,
               COALESCE(AVG(CASE WHEN price_cents>0 THEN price_cents/100.0 END),0) as avg_price,
               SUM(CASE WHEN COALESCE(total_purchases,0)=0 THEN 1 ELSE 0 END) as dead_apps,
               SUM(CASE WHEN COALESCE(last_month_purchases,0)>0 THEN 1 ELSE 0 END) as active_apps,
               SUM(CASE WHEN price_cents=0 THEN 1 ELSE 0 END) as free_count,
               SUM(CASE WHEN price_cents>0 THEN 1 ELSE 0 END) as paid_count,
               SUM(CASE WHEN price_cents>0 AND price_cents<=3000 THEN 1 ELSE 0 END) as low_count,
               SUM(CASE WHEN price_cents>0 AND total_purchases>50 AND last_month_purchases=0 THEN 1 ELSE 0 END) as stale,
               COALESCE(MAX(CASE WHEN total_purchases>0 THEN total_purchases ELSE 0 END)*100.0
                        / NULLIF(SUM(total_purchases),0), 50) as top_share,
               COALESCE(AVG(CASE WHEN rating_stars>0 THEN rating_stars END), 0) as avg_rating
        FROM app_snapshots
        WHERE run_id='{RUN}'
          AND display_name ILIKE '%{kw.replace("'","''")}%'
    """).df().iloc[0]

    s = score_app(row, niche_stats)
    s["display_name"]      = name
    s["tier"]              = row["tier"]
    s["total_purchases"]   = int(row["total_purchases"]) if pd.notna(row["total_purchases"]) else 0
    s["last_month"]        = int(row["last_month_purchases"]) if pd.notna(row["last_month_purchases"]) else 0
    s["price_cents"]       = int(row["price_cents"]) if pd.notna(row["price_cents"]) else 0
    s["rating_stars"]      = float(row["rating_stars"]) if pd.notna(row["rating_stars"]) else 0
    scores.append(s)

results = pd.DataFrame(scores)


# ── Accuracy metrics ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("ACCURACY: Average viability score by ground-truth tier")
print("="*60)
acc = results.groupby("tier")["viability"].agg(["mean","median","std","count"])
print(acc.to_string())

print("\n" + "="*60)
print("SCORE DISTRIBUTION: What % of each tier scores LAUNCH READY (≥70)?")
print("="*60)
for tier in ["WINNER","MID","LOSER"]:
    t = results[results["tier"]==tier]
    launch_ready = (t["viability"] >= 70).sum()
    print(f"  {tier:8s}: {launch_ready}/{len(t)} ({launch_ready/len(t)*100:.0f}%) score ≥70")

print("\n" + "="*60)
print("FALSE POSITIVES: LOSER apps that score ≥60 (inflated by formula)")
print("="*60)
fp = results[(results["tier"]=="LOSER") & (results["viability"]>=60)].sort_values("viability",ascending=False)
print(fp[["display_name","viability","sat","demand","dead_health","forced_buyer","dead_pct"]].head(15).to_string())

print("\n" + "="*60)
print("FALSE NEGATIVES: WINNER apps that score <50 (underscored by formula)")
print("="*60)
fn = results[(results["tier"]=="WINNER") & (results["viability"]<50)].sort_values("viability")
print(fn[["display_name","viability","total_purchases","sat","demand","momentum"]].head(15).to_string())

print("\n" + "="*60)
print("BIAS: Average sub-score by tier (where does formula inflate/deflate?)")
print("="*60)
components = ["sat","demand","gap","dead_health","moat","momentum","forced_buyer"]
bias = results.groupby("tier")[components].mean()
print(bias.round(1).to_string())

print("\n" + "="*60)
print("CALIBRATION: Correlation — viability score vs log(total_purchases)")
print("="*60)
import numpy as np
active = results[results["total_purchases"] > 0].copy()
active["log_sales"] = np.log1p(active["total_purchases"])
corr = active[["viability","log_sales"] + components].corr()["log_sales"].drop("log_sales")
print(corr.sort_values(ascending=False).to_string())

print("\n" + "="*60)
print("MIGRATOR bias check: do migrator keywords inflate scores?")
print("="*60)
mg = results[results["is_migrator"]]
non = results[~results["is_migrator"]]
print(f"  Migrator apps (n={len(mg)}):     avg viability = {mg['viability'].mean():.1f}")
print(f"  Non-migrator apps (n={len(non)}): avg viability = {non['viability'].mean():.1f}")
if len(mg) > 0:
    print(f"  Migrator winners/losers: {mg[mg['tier']=='WINNER']['viability'].mean():.1f} / {mg[mg['tier']=='LOSER']['viability'].mean():.1f}")
