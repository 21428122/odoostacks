import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

conn = duckdb.connect('data/odoo.duckdb', read_only=True)
RUN = '20260508T180021Z-19e350'

print("=== TOP 20 VELOCITY HOTSPOTS (paid, min 3 apps) ===")
hot = conn.execute(f"""
    WITH niche AS (
        SELECT LOWER(SPLIT_PART(display_name,' ',1)) as kw,
               COUNT(*) as n, SUM(total_purchases) as total,
               SUM(last_month_purchases) as velocity,
               AVG(CASE WHEN price_cents>0 THEN price_cents/100.0 END) as avg_price,
               AVG(CASE WHEN rating_stars>0 THEN rating_stars END) as avg_rating,
               SUM(CASE WHEN COALESCE(total_purchases,0)=0 THEN 1 ELSE 0 END)*100.0/COUNT(*) as dead_pct
        FROM app_snapshots WHERE run_id='{RUN}' AND price_cents>0
        GROUP BY 1 HAVING COUNT(*)>=3 AND SUM(last_month_purchases)>0
    )
    SELECT kw,n,total,velocity,ROUND(velocity*1.0/n,2) as vel_per_app,
           ROUND(avg_price,0) as avg_price,ROUND(avg_rating,2) as avg_rating,ROUND(dead_pct,0) as dead_pct
    FROM niche ORDER BY velocity DESC LIMIT 20
""").df()
print(hot.to_string(index=False))

print("\n=== HIDDEN GEMS: 2-5 apps, high sales/app ===")
gems = conn.execute(f"""
    WITH niche AS (
        SELECT LOWER(SPLIT_PART(display_name,' ',1)) as kw,
               COUNT(*) as n, COALESCE(SUM(total_purchases),0) as total,
               COALESCE(SUM(last_month_purchases),0) as velocity,
               AVG(CASE WHEN price_cents>0 THEN price_cents/100.0 END) as avg_price,
               SUM(CASE WHEN COALESCE(total_purchases,0)=0 THEN 1 ELSE 0 END) as dead
        FROM app_snapshots WHERE run_id='{RUN}' AND price_cents>0
        GROUP BY 1 HAVING COUNT(*) BETWEEN 2 AND 5
    )
    SELECT kw,n,total,ROUND(total*1.0/n,0) as sales_per_app,velocity,ROUND(avg_price,0) as price,dead
    FROM niche WHERE total>100
    ORDER BY sales_per_app DESC LIMIT 25
""").df()
print(gems.to_string(index=False))

print("\n=== MONOPOLY NICHES: one author >70% of sales ===")
mono = conn.execute(f"""
    WITH auth AS (
        SELECT LOWER(SPLIT_PART(display_name,' ',1)) as kw, author,
               SUM(total_purchases) as auth_sales, COUNT(*) as auth_apps
        FROM app_snapshots WHERE run_id='{RUN}' AND price_cents>0 GROUP BY 1,2
    ),
    nt AS (SELECT kw, SUM(auth_sales) as niche_sales FROM auth GROUP BY kw HAVING SUM(auth_sales)>50)
    SELECT a.kw,a.author,a.auth_sales,nt.niche_sales,
           ROUND(a.auth_sales*100.0/nt.niche_sales,0) as share_pct,a.auth_apps
    FROM auth a JOIN nt ON a.kw=nt.kw
    WHERE a.auth_sales*100.0/nt.niche_sales>70
    ORDER BY nt.niche_sales DESC LIMIT 20
""").df()
print(mono.to_string(index=False))

print("\n=== STALE INCUMBENTS: >100 buyers, ZERO sales this month ===")
stale = conn.execute(f"""
    SELECT display_name,author,ROUND(price_cents/100.0,0) as price,
           total_purchases,last_month_purchases,rating_stars,review_count
    FROM app_snapshots WHERE run_id='{RUN}' AND price_cents>0
      AND total_purchases>100 AND COALESCE(last_month_purchases,0)=0
    ORDER BY total_purchases DESC LIMIT 20
""").df()
print(stale.to_string(index=False))

print("\n=== PRICE GAP: min paid price >$50 (entry tier open) ===")
pgap = conn.execute(f"""
    SELECT LOWER(SPLIT_PART(display_name,' ',1)) as kw,COUNT(*) as n,
           ROUND(MIN(price_cents/100.0),0) as min_price, ROUND(MAX(price_cents/100.0),0) as max_price,
           SUM(total_purchases) as total_sales
    FROM app_snapshots WHERE run_id='{RUN}' AND price_cents>5000
    GROUP BY 1 HAVING COUNT(*)>=3 AND SUM(total_purchases)>50
    ORDER BY total_sales DESC LIMIT 20
""").df()
print(pgap.to_string(index=False))

print("\n=== AI/LLM KEYWORDS in marketplace ===")
for kw in ['llm','gpt','openai','ai-powered','chatgpt','gemini','agentic','vector','embedding','machine learning']:
    r = conn.execute(f"""
        SELECT COUNT(*) as n, COALESCE(SUM(total_purchases),0) as sales,
               COALESCE(AVG(CASE WHEN price_cents>0 THEN price_cents/100.0 END),0) as avg_price
        FROM app_snapshots WHERE run_id='{RUN}'
          AND (display_name ILIKE '%{kw}%' OR summary ILIKE '%{kw}%')
    """).fetchone() or (0,0,0)
    if r[0]>0: print(f"  {kw:25s}: n={r[0]}  sales={int(r[1])}  avg_price=${int(r[2] or 0)}")

print("\n=== GEO GAPS: country-specific with <10 apps but >0 sales ===")
for c in ['australia','canada','brazil','mexico','south africa','uae','saudi','japan','korea','indonesia','vietnam','nigeria','kenya','new zealand','chile','colombia']:
    r = conn.execute(f"""
        SELECT COUNT(*) as n, COALESCE(SUM(total_purchases),0) as sales,
               COALESCE(AVG(CASE WHEN price_cents>0 THEN price_cents/100.0 END),0) as price
        FROM app_snapshots WHERE run_id='{RUN}' AND price_cents>0
          AND (display_name ILIKE '%{c}%' OR summary ILIKE '%{c}%')
    """).fetchone() or (0,0,0)
    n,s,p=int(r[0]),int(r[1]),int(r[2] or 0)
    if 0<n<10 and s>0: print(f"  {c:20s}: n={n}  sales={s}  avg_price=${p}")
