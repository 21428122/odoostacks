import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

DB  = 'data/odoo.duckdb'
RUN = '20260508T180021Z-19e350'
conn = duckdb.connect(DB, read_only=True)

MANDATORY_KWS  = ['e-slog','eslog','peppol','zatca','irn','eway bill','ewaybill','gst 2.0','e-invoice mandate','ksef','mydata']
MIGRATION_KWS  = ['quickbooks','qbo','tally','sage','myob','dynamics gp','dynamics nav','netsuite','wave accounting','datev','busy accounting']
MIGRATOR_KWS   = ['quickbooks','qbo','tally','sage','myob','xero','dynamics','netsuite','wave accounting','zoho books','busy accounting','datev']
MIGRATOR_PROXY = {'quickbooks':90,'qbo':90,'tally':80,'datev':85,'dynamics':75,'sage':65,'myob':65,'xero':70,'netsuite':75,'zoho books':60,'busy accounting':70,'wave':55}

def score(kw, ns):
    n=int(ns['n']); tp=int(ns['tp']); vel=int(ns['vel'])
    dead=int(ns['dead']); active=max(int(ns['active']),1)
    paid_c=int(ns['paid_c']); low_c=int(ns['low_c']); stale=int(ns['stale'])
    top_sh=float(ns['top_sh'] or 50); avg_r=float(ns['avg_r'] or 0)
    dead_pct=dead/n if n>0 else 0
    avg_pur=tp/active; vel_per=vel/active

    if   n==0:  sat=50
    elif n<=3:  sat=90
    elif n<=8:  sat=75
    elif n<=20: sat=55
    elif n<=50: sat=35
    else:       sat=15
    if dead_pct>=0.80 and n>3: sat=min(sat,35)

    is_mig=any(k in kw for k in MIGRATOR_KWS)
    if is_mig:
        demand=max((MIGRATOR_PROXY.get(k,50) for k in MIGRATOR_KWS if k in kw), default=60)
    else:
        if avg_pur>500: demand=90
        elif avg_pur>200: demand=75
        elif avg_pur>80: demand=60
        elif avg_pur>20: demand=40
        elif avg_pur>5: demand=25
        else: demand=10

    if paid_c==0: gap=50
    elif low_c==0: gap=80
    elif low_c<=3: gap=60
    elif low_c<=8: gap=40
    else: gap=20

    if   top_sh>60: moat=20
    elif top_sh>40: moat=45
    elif top_sh>20: moat=65
    else:           moat=85
    if stale>=2 and paid_c>0 and stale/max(paid_c,1)>=0.5: moat=min(95,moat+15)

    recency=vel/max(tp,1); rb=min(20,int(recency*200))
    if is_mig: momentum=min(90,70+rb)
    else:
        if vel_per>10: momentum=90
        elif vel_per>5: momentum=80
        elif vel_per>2: momentum=65
        elif vel_per>0.5: momentum=45
        elif vel_per>0.1: momentum=25
        else: momentum=10
        momentum=min(90,momentum+rb)

    if n<=3: dh=50
    elif dead_pct<=0.40: dh=85
    elif dead_pct<=0.55: dh=65
    elif dead_pct<=0.70: dh=45
    elif dead_pct<=0.85: dh=25
    else: dh=10

    fb=10
    if any(k in kw for k in MANDATORY_KWS): fb=90
    elif any(k in kw for k in MIGRATION_KWS): fb=70

    rs=int(avg_r/5.0*100) if avg_r>0 else 50
    viab=int(sat*0.10+demand*0.20+dh*0.12+momentum*0.28+fb*0.13+rs*0.17)
    return dict(sat=sat,demand=demand,dead_health=dh,
                momentum=momentum,forced_buyer=fb,rating_score=rs,viability=viab,
                is_migrator=is_mig,dead_pct=round(dead_pct*100,1),niche_n=n,niche_tp=tp)

def get_tier(where, limit, label):
    return conn.execute(f"""
        SELECT display_name,author,summary,price_cents,
               COALESCE(rating_stars,0) as rating_stars,
               COALESCE(review_count,0) as review_count,
               COALESCE(total_purchases,0) as total_purchases,
               COALESCE(last_month_purchases,0) as last_month_purchases
        FROM app_snapshots WHERE run_id='{RUN}' AND {where}
        ORDER BY total_purchases DESC LIMIT {limit}
    """).df().assign(tier=label)

winners = get_tier('price_cents>0 AND total_purchases>=100', 200, 'WINNER')
mid     = get_tier('price_cents>0 AND total_purchases BETWEEN 5 AND 99', 150, 'MID')
losers  = get_tier('price_cents>0 AND COALESCE(total_purchases,0)=0', 200, 'LOSER')
df = pd.concat([winners,mid,losers], ignore_index=True)

rows=[]
for _,row in df.iterrows():
    name=str(row['display_name'] or '')
    kw=(name+' '+str(row['summary'] or '')).lower()
    fw=name.split()[0].replace("'","''") if name.split() else 'x'
    ns=conn.execute(f"""
        SELECT COUNT(*) as n,
               COALESCE(SUM(total_purchases),0) as tp,
               COALESCE(SUM(last_month_purchases),0) as vel,
               SUM(CASE WHEN COALESCE(total_purchases,0)=0 THEN 1 ELSE 0 END) as dead,
               SUM(CASE WHEN COALESCE(last_month_purchases,0)>0 THEN 1 ELSE 0 END) as active,
               SUM(CASE WHEN price_cents>0 THEN 1 ELSE 0 END) as paid_c,
               SUM(CASE WHEN price_cents>0 AND price_cents<=3000 THEN 1 ELSE 0 END) as low_c,
               SUM(CASE WHEN price_cents>0 AND total_purchases>50 AND last_month_purchases=0 THEN 1 ELSE 0 END) as stale,
               COALESCE(MAX(CASE WHEN total_purchases>0 THEN total_purchases ELSE 0 END)*100.0/NULLIF(SUM(total_purchases),0),50) as top_sh,
               COALESCE(AVG(CASE WHEN rating_stars>0 THEN rating_stars END),0) as avg_r
        FROM app_snapshots WHERE run_id='{RUN}' AND display_name ILIKE '%{fw}%'
    """).df().iloc[0]
    s=score(kw,ns)
    s.update(dict(display_name=name,tier=row['tier'],
        total_purchases=int(row['total_purchases']),
        last_month=int(row['last_month_purchases']),
        price_cents=int(row['price_cents']) if pd.notna(row['price_cents']) else 0,
        rating=float(row['rating_stars']),reviews=int(row['review_count']),author=str(row['author'])))
    rows.append(s)

out=pd.DataFrame(rows)
out.to_csv('data/backtest_v2.csv',index=False)
print("Saved",len(out),"rows to data/backtest_v2.csv")
print(out.groupby('tier')[['viability','total_purchases','rating_score','momentum']].mean().round(2))
