import duckdb

con = duckdb.connect('data/odoo.duckdb', read_only=True)
RUN = '20260508T180021Z-19e350'

print('=== 1. PRICE TIER: which tiers actually convert ===')
rows = con.execute(f"""
SELECT
  CASE
    WHEN price_cents = 0 THEN 'Free'
    WHEN price_cents <= 999 THEN '$1-9'
    WHEN price_cents <= 1999 THEN '$10-19'
    WHEN price_cents <= 4999 THEN '$20-49'
    WHEN price_cents <= 9999 THEN '$50-99'
    WHEN price_cents <= 19999 THEN '$100-199'
    WHEN price_cents <= 49999 THEN '$200-499'
    ELSE '$500+'
  END as tier,
  COUNT(*) as apps,
  COALESCE(SUM(total_purchases),0) as total_sales,
  ROUND(COALESCE(SUM(total_purchases),0)*1.0/COUNT(*),1) as sales_per_app,
  COALESCE(SUM(last_month_purchases),0) as last_month
FROM app_snapshots WHERE run_id='{RUN}'
GROUP BY 1 ORDER BY MIN(COALESCE(price_cents,0))
""").fetchall()
print(f"{'Tier':<12} {'Apps':>6} {'TotSales':>10} {'Sales/App':>10} {'LastMo':>8}")
for r in rows:
    print(f"{r[0]:<12} {r[1]:>6} {r[2]:>10,} {r[3]:>10} {r[4]:>8,}")

print()
print('=== 2. NICHE VELOCITY (last-month purchases = real current demand) ===')
NICHES = [
    ('Manufacturing',    'manufacturing,mrp,bom,work order,production,routing'),
    ('eCommerce Sync',   'shopify,woocommerce,amazon,magento,ebay,flipkart,meesho'),
    ('Accounting',       'invoice,accounting,ledger,tax,payment,journal,fiscal'),
    ('HR/Payroll',       'payroll,hr,employee,attendance,leave,biometric'),
    ('Inventory/WMS',    'inventory,warehouse,stock,wms,barcode,lot,serial'),
    ('Connector/API',    'connector,api,integration,sync,webhook,edi'),
    ('CRM/Sales',        'crm,lead,opportunity,pipeline,prospect,quotation'),
    ('Dashboard/BI',     'dashboard,report,analytics,kpi,chart,pivot,bi'),
    ('Migration/Import', 'migration,import,quickbooks,tally,zoho,sage,datev'),
    ('WhatsApp/Chat',    'whatsapp,telegram,sms,chat,messaging'),
    ('GST/Compliance',   'gst,einvoice,compliance,vat,mandate'),
    ('POS/Retail',       'pos,point of sale,retail,cashier,kiosk'),
    ('Field Service',    'field service,technician,maintenance,repair'),
    ('Subscription',     'subscription,recurring,saas,renewal,membership'),
    ('Document/DMS',     'document,dms,attachment,folder,cloud storage'),
    ('Helpdesk',         'helpdesk,ticket,support,sla'),
    ('Project',          'timesheet,project,task,gantt,resource'),
    ('Fleet/GPS',        'fleet,vehicle,car,driver,gps,tracking'),
    ('Quality/QC',       'quality,qc,inspection,defect,iso'),
    ('Healthcare',       'hospital,clinic,patient,medical,pharmacy,doctor'),
    ('Restaurant/Hotel', 'restaurant,hotel,hospitality,pms,food delivery'),
    ('Real Estate',      'real estate,property,rent,lease,tenant,realty'),
    ('Education',        'school,college,university,student,lms,course,exam'),
    ('Construction',     'construction,contractor,site,civil,project cost'),
    ('Logistics/3PL',    'logistics,3pl,freight,courier,shipment,carrier'),
]
results = []
for label, kws in NICHES:
    terms = kws.split(',')
    cond_parts = []
    for t in terms:
        t = t.strip()
        cond_parts.append(f"display_name ILIKE '%{t}%'")
        cond_parts.append(f"summary ILIKE '%{t}%'")
    cond = ' OR '.join(cond_parts)
    r = con.execute(f"""
    SELECT COUNT(*) as cnt,
           COALESCE(SUM(total_purchases),0) as sales,
           COALESCE(SUM(last_month_purchases),0) as velocity,
           COUNT(DISTINCT author) as authors
    FROM app_snapshots
    WHERE run_id='{RUN}' AND ({cond})
    """).fetchone()
    vel_per_app = round(r[2]/r[0], 2) if r[0] > 0 else 0
    results.append((label, r[0], r[1], r[2], r[3], vel_per_app))

results.sort(key=lambda x: x[3], reverse=True)
print(f"{'Niche':<22} {'Apps':>5} {'TotSales':>9} {'LastMo':>7} {'Authors':>8} {'Vel/App':>8}")
for r in results:
    print(f"{r[0]:<22} {r[1]:>5} {r[2]:>9,} {r[3]:>7,} {r[4]:>8} {r[5]:>8}")

print()
print('=== 3. ZERO/THIN-APP GAPS (keywords with <5 apps = unclaimed territory) ===')
ZERO_CHECK = [
    'unicommerce', 'flipkart', 'meesho', 'myntra', 'zepto', 'blinkit',
    'shiprocket', 'delhivery', 'bluedart', 'dtdc', 'eway bill', 'ewaybill',
    'tally prime', 'busy accounting', 'khatabook', 'vyapar',
    'indiamart', 'tradeindia', 'jiomart', 'udaan', 'snapdeal',
    'docusign', 'esign', 'digital signature', 'aadhaar', 'e-sign',
    'cpq', 'dunning', 'revenue recognition', 'deferred revenue',
    'hl7', 'fhir', 'dicom', 'lims', 'laboratory information',
    'cold chain', 'iot sensor', 'scada', 'plc',
    'freight forwarder', 'customs', 'import duty',
    'franchise', 'multi-outlet', 'multi-store',
    'property management', 'tenant', 'rent collection',
    'lms', 'e-learning', 'course management',
    'cpg', 'fmcg', 'consumer goods',
    'nutraceutical', 'pharma', 'drug', 'batch recall',
    'carbon', 'esg', 'sustainability', 'scope 3',
    'salary advance', 'loan management', 'nbfc',
    'toll', 'fastag', 'vehicle tracking', 'gps tracker',
    'geofence', 'route optimization',
    'voice call', 'ivr', 'call center', 'telephony',
    'ai invoice', 'ocr invoice', 'receipt scan',
    'crypto', 'blockchain', 'nft',
    'social commerce', 'instagram shop', 'live commerce',
]
print(f"{'Keyword':<28} {'Apps':>5} {'Sales':>8}")
for kw in ZERO_CHECK:
    r = con.execute(f"""
    SELECT COUNT(*), COALESCE(SUM(total_purchases),0)
    FROM app_snapshots
    WHERE run_id='{RUN}'
      AND (display_name ILIKE '%{kw}%' OR summary ILIKE '%{kw}%')
    """).fetchone()
    if r[0] < 6:
        print(f"{kw:<28} {r[0]:>5} {r[1]:>8,}")

print()
print('=== 4. INDIA-SPECIFIC SIGNALS ===')
INDIA_KWS = ['india','indian','gst','tds','tcs','pan','tan','msme','udyam',
             'rupee','inr','neft','rtgs','upi','imps','cheque','challan',
             'e-way','eway','hsn','sac code','gstr','itr','traces']
cond_parts = []
for kw in INDIA_KWS:
    cond_parts.append(f"display_name ILIKE '%{kw}%'")
    cond_parts.append(f"summary ILIKE '%{kw}%'")
cond = ' OR '.join(cond_parts)
r = con.execute(f"""
SELECT COUNT(*), COALESCE(SUM(total_purchases),0), COALESCE(SUM(last_month_purchases),0),
       COUNT(DISTINCT author)
FROM app_snapshots WHERE run_id='{RUN}' AND ({cond})
""").fetchone()
print(f"India-signal apps: {r[0]}, total sales: {r[1]:,}, last month: {r[2]:,}, authors: {r[3]}")

top_india = con.execute(f"""
SELECT display_name, author, ROUND(price_cents/100.0,2) as price,
       total_purchases, last_month_purchases
FROM app_snapshots
WHERE run_id='{RUN}' AND ({cond}) AND total_purchases > 0
ORDER BY total_purchases DESC LIMIT 10
""").fetchall()
print("Top India apps:")
for r in top_india:
    print(f"  {r[0][:50]:<50} ${r[2]:>7} | {r[3]:>5} sales | {r[4]:>3} last mo")

con.close()
