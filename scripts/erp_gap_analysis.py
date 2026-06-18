"""
ERP Ecosystem Gap Analysis
==========================
Compares known capabilities in Zoho, SAP, Salesforce, QuickBooks, NetSuite,
Tally, and other ecosystems against what exists in Odoo marketplace.

No LLM. Pure keyword mining against DuckDB (67k apps).

Output: prints a ranked opportunity table — high presence in other ecosystems,
low/no apps in Odoo = white space for a new module.
"""

import duckdb

con = duckdb.connect("data/odoo.duckdb", read_only=True)
RUN = "20260508T180021Z-19e350"


def odoo_coverage(keywords: list[str]) -> dict:
    """Returns {apps, sales, last_month} for a keyword list."""
    cond = " OR ".join(
        f"display_name ILIKE '%{k}%' OR summary ILIKE '%{k}%'"
        for k in keywords
    )
    row = con.execute(f"""
        SELECT COUNT(*),
               COALESCE(SUM(total_purchases), 0),
               COALESCE(SUM(last_month_purchases), 0)
        FROM app_snapshots
        WHERE run_id = '{RUN}' AND ({cond})
    """).fetchone()
    return {"apps": row[0], "sales": row[1], "last_month": row[2]}


# ─── Known capabilities in other ecosystems that might be absent in Odoo ─────
# Format: (category, description, search_keywords, erp_sources)
GAPS = [
    # ── Zoho One / Zoho ecosystem ──────────────────────────────────────────────
    ("Zoho CRM deep-sync",       "Two-way live sync with Zoho CRM (contacts, deals, activities)",
     ["zoho crm", "zoho sync", "zoho integration"], "Zoho"),
    ("Zoho Books migrator",      "Full migration: chart of accounts, invoices, vendors from Zoho Books",
     ["zoho books", "zoho migration", "zoho import"], "Zoho"),
    ("Zoho Recruit sync",        "Sync job positions and candidates from Zoho Recruit",
     ["zoho recruit", "zoho hr", "zoho talent"], "Zoho"),
    ("Zoho Desk connector",      "Pull support tickets from Zoho Desk into Odoo Helpdesk",
     ["zoho desk", "zoho ticket", "zoho support"], "Zoho"),
    ("Zoho Inventory bridge",    "Bi-directional stock/order sync with Zoho Inventory",
     ["zoho inventory", "zoho stock", "zoho order"], "Zoho"),

    # ── SAP / SAP Business One ────────────────────────────────────────────────
    ("SAP migrator",             "Migrate master data + financials from SAP B1 / SAP ECC",
     ["sap migration", "sap import", "sap b1"], "SAP"),
    ("SAP HANA connector",       "Real-time data read from SAP HANA via RFC/BAPI",
     ["sap hana", "sap connector", "sap rfc"], "SAP"),
    ("SAP BOM sync",             "Push/pull bill-of-materials between SAP PP and Odoo MRP",
     ["sap bom", "sap mrp", "sap production"], "SAP"),
    ("SAP IDoc / EDI",           "Parse SAP IDocs (ORDERS, INVOIC, DESADV) into Odoo docs",
     ["idoc", "sap edi", "sap orders05"], "SAP/EDI"),

    # ── QuickBooks / Xero / Sage ──────────────────────────────────────────────
    ("QuickBooks Online migrator","Migrate QB Online company: COA, invoices, customers, vendors, history",
     ["quickbooks", "quickbooks online", "qbo migration"], "Intuit"),
    ("QuickBooks Desktop migrator","Migrate QB Desktop / Enterprise via IIF/QBW export",
     ["quickbooks desktop", "quickbooks enterprise", "qb desktop"], "Intuit"),
    ("Xero migrator",            "Full Xero → Odoo migration (accounts, bank feeds, invoices)",
     ["xero migration", "xero import", "xero connector"], "Xero"),
    ("Sage 50 migrator",         "Migrate Sage 50 / Sage 100 / Sage 300 data",
     ["sage 50", "sage migration", "sage import"], "Sage"),
    ("Wave Accounting migrator", "Migrate Wave (free accounting app popular in Canada/US SMBs)",
     ["wave accounting", "wave migration", "wave import"], "Wave"),
    ("FreshBooks migrator",      "Migrate FreshBooks invoices and clients",
     ["freshbooks", "freshbooks migration", "freshbooks import"], "FreshBooks"),
    ("MYOB migrator",            "Migrate MYOB AccountRight / Essentials (dominant in AU/NZ)",
     ["myob", "myob migration", "myob import"], "MYOB"),

    # ── Salesforce ────────────────────────────────────────────────────────────
    ("Salesforce CRM sync",      "Live bi-directional sync of Leads/Contacts/Opportunities",
     ["salesforce", "salesforce sync", "salesforce connector"], "Salesforce"),
    ("Salesforce CPQ bridge",    "Pull Salesforce CPQ quotes into Odoo Sales",
     ["salesforce cpq", "sf cpq"], "Salesforce"),

    # ── NetSuite / Microsoft ──────────────────────────────────────────────────
    ("NetSuite migrator",        "Migrate financial data from Oracle NetSuite",
     ["netsuite", "netsuite migration", "oracle netsuite"], "Oracle"),
    ("Dynamics 365 migrator",    "Migrate from Microsoft Dynamics 365 / Business Central / NAV",
     ["dynamics 365", "dynamics nav", "business central", "ms dynamics"], "Microsoft"),
    ("Dynamics GP migrator",     "Migrate from Microsoft Great Plains (GP) — still huge in midmarket",
     ["dynamics gp", "great plains", "microsoft gp"], "Microsoft"),

    # ── India-specific platforms ───────────────────────────────────────────────
    ("Tally Prime migrator",     "Full Tally Prime / Tally ERP 9 data export → Odoo import",
     ["tally prime", "tally erp", "tally migration", "tally import"], "Tally"),
    ("Busy Accounting migrator", "Migrate BUSY Accounting Software (strong in Indian SMBs)",
     ["busy accounting", "busy software", "busy migration"], "Busy"),
    ("Marg ERP migrator",        "Migrate Marg ERP data (pharma/FMCG, popular in India)",
     ["marg erp", "marg migration", "marg software"], "Marg"),
    ("Miracle Accounting",       "Migrate Miracle Accounting (Rajasthan/UP region)",
     ["miracle accounting", "miracle erp"], "Miracle"),
    ("IndiaMART lead sync",      "Pull verified buyer inquiries from IndiaMART into CRM",
     ["indiamart", "india mart", "indiamart lead"], "IndiaMART"),
    ("TradeIndia connector",     "Sync trade leads from TradeIndia.com",
     ["tradeindia", "trade india"], "TradeIndia"),
    ("Delhivery shipping",       "Auto-book & track Delhivery courier shipments from Odoo",
     ["delhivery", "delhivery shipping", "delhivery integration"], "Delhivery"),
    ("BlueDart / DTDC courier",  "Book shipments via BlueDart or DTDC courier API",
     ["bluedart", "dtdc", "courier booking"], "Bluedart/DTDC"),
    ("Shiprocket integration",   "Multi-carrier shipping via Shiprocket (India's #1 aggregator)",
     ["shiprocket", "shiprocket integration", "shiprocket shipping"], "Shiprocket"),
    ("Unicommerce sync",         "Sync orders/inventory with Unicommerce OMS (D2C brands)",
     ["unicommerce", "unicommerce sync"], "Unicommerce"),
    ("Meesho seller sync",       "Manage Meesho seller account orders in Odoo",
     ["meesho", "meesho seller", "meesho order"], "Meesho"),
    ("Flipkart seller",          "Manage Flipkart seller central orders in Odoo",
     ["flipkart", "flipkart seller", "flipkart order"], "Flipkart"),
    ("JioMart connector",        "Sync orders from JioMart seller portal",
     ["jiomart", "jio mart"], "Reliance"),
    ("Myntra seller",            "Sync Myntra seller orders and returns",
     ["myntra", "myntra seller"], "Myntra"),
    ("eWay Bill integration",    "Auto-generate and cancel eWay Bills via GST API",
     ["eway bill", "ewaybill", "e-way bill"], "GST Portal"),
    ("UPI payment reconciliation","Match UPI payment references (NPCI) to Odoo invoices",
     ["upi", "upi reconciliation", "upi payment"], "NPCI"),
    ("GSTIN validation",         "Validate GSTIN numbers via govt API at invoice time",
     ["gstin", "gstin validation", "gstin verify"], "GST Portal"),

    # ── eCommerce connectors ───────────────────────────────────────────────────
    ("TikTok Shop connector",    "Sync TikTok Shop orders and inventory in real-time",
     ["tiktok shop", "tiktok seller", "tiktok commerce"], "TikTok"),
    ("Etsy seller sync",         "Pull Etsy listings and orders into Odoo",
     ["etsy", "etsy seller", "etsy shop"], "Etsy"),
    ("Noon marketplace",         "Sync orders from Noon.com (UAE/Saudi dominant marketplace)",
     ["noon", "noon marketplace", "noon seller"], "Noon"),
    ("Lazada / Tokopedia",       "SEA marketplace (Indonesia/SE Asia) order sync",
     ["lazada", "tokopedia", "shopee seller"], "SEA"),
    ("Walmart Marketplace",      "Sync Walmart Marketplace seller orders",
     ["walmart marketplace", "walmart seller"], "Walmart"),
    ("Target Plus",              "Sync Target.com marketplace orders",
     ["target plus", "target marketplace"], "Target"),

    # ── HR / Payroll platforms ─────────────────────────────────────────────────
    ("BambooHR sync",            "Sync employee records between BambooHR and Odoo HR",
     ["bamboohr", "bamboo hr", "bamboo sync"], "BambooHR"),
    ("Workday migrator",         "Migrate employee/org data from Workday HCM",
     ["workday", "workday migration", "workday hcm"], "Workday"),
    ("ADP Payroll connector",    "Export Odoo payroll runs to ADP payroll system",
     ["adp payroll", "adp connector", "adp hr"], "ADP"),
    ("Darwinbox connector",      "Sync employee leave/attendance with Darwinbox (India/SEA HCM)",
     ["darwinbox", "darwin box"], "Darwinbox"),
    ("Keka HR sync",             "Sync HR data with Keka (popular India SMB HRMS)",
     ["keka hr", "keka hrms", "keka payroll"], "Keka"),
    ("greytHR connector",        "Sync payroll/attendance with greytHR (India)",
     ["greythr", "greyt hr"], "Greytip"),

    # ── Field service / IoT ────────────────────────────────────────────────────
    ("ServiceTitan connector",   "Sync jobs/customers from ServiceTitan (HVAC/plumbing/electrical)",
     ["servicetitan", "service titan"], "ServiceTitan"),
    ("Jobber integration",       "Sync field jobs from Jobber to Odoo CRM/Projects",
     ["jobber", "jobber integration"], "Jobber"),
    ("IoT sensor → inventory",   "Auto-adjust stock from IoT sensor readings (weight/count)",
     ["iot sensor", "iot inventory", "sensor reading", "scada"], "IoT"),

    # ── Compliance / Legal ─────────────────────────────────────────────────────
    ("DocuSign e-signature",     "Send Odoo docs for e-signature via DocuSign",
     ["docusign", "docu sign", "esign"], "DocuSign"),
    ("Aadhaar KYC",              "Aadhaar-based KYC verification API for Indian customers",
     ["aadhaar", "aadhar", "aadhaar kyc", "aadhar verify"], "UIDAI"),
    ("Video KYC",                "Video-based KYC workflow for banks/NBFCs in Odoo",
     ["video kyc", "vkyc", "video verification"], "RBI"),
    ("Carbon footprint tracker", "Calculate Scope 1/2/3 emissions from Odoo purchase/inventory data",
     ["carbon", "esg", "scope 3", "emission", "sustainability reporting"], "ESG"),
    ("FHIR / HL7 health bridge", "Exchange patient data between EHR and Odoo (medical suppliers)",
     ["fhir", "hl7", "healthcare interop", "ehr connector"], "HL7/FHIR"),
    ("LIMS integration",         "Lab Information Management System connector for pharma/food quality",
     ["lims", "laboratory information", "lab management system"], "LIMS"),

    # ── Finance / Fintech ──────────────────────────────────────────────────────
    ("Revenue recognition",      "ASC 606 / IFRS 15 deferred revenue and recognition schedules",
     ["revenue recognition", "asc 606", "ifrs 15", "deferred revenue schedule"], "NetSuite/SAP"),
    ("Dunning management",       "Automated overdue invoice dunning with escalation workflows",
     ["dunning", "dunning letter", "dunning management"], "SAP/ERP"),
    ("CPQ (Configure-Price-Quote)","Complex product configurator with pricing rules and quoting",
     ["cpq", "configure price quote", "product configurator quote"], "Salesforce"),
    ("NBFC loan management",     "Full loan lifecycle: application → disbursement → EMI for NBFCs",
     ["nbfc", "loan management", "emi schedule", "loan disbursement"], "Fintech"),
    ("Salary advance / loan",    "Employee salary advance and loan repayment via payroll deduction",
     ["salary advance", "employee loan", "advance salary", "loan deduction"], "HR"),

    # ── Logistics / 3PL ───────────────────────────────────────────────────────
    ("FedEx One Rate shipping",  "Book FedEx shipments directly from Odoo with rate comparison",
     ["fedex", "fedex shipping", "fedex label"], "FedEx"),
    ("Flexport freight",         "Book ocean/air freight via Flexport API from Odoo",
     ["flexport", "flexport freight", "flexport booking"], "Flexport"),
    ("Route optimization",       "Optimize delivery routes for last-mile fleet using HERE/Google",
     ["route optimization", "last mile", "route planning", "delivery route"], "Logistics"),
    ("Customs / import duty",    "Auto-calculate import duties from HS codes and country of origin",
     ["customs duty", "import duty", "hs code duty", "tariff calculator"], "Trade"),
]

# ─── Run analysis ─────────────────────────────────────────────────────────────
print(f"\n{'='*95}")
print(f"{'CATEGORY':<35} {'SOURCE':<15} {'Odoo Apps':>9} {'Sales':>8} {'LastMo':>7} {'SIGNAL'}")
print(f"{'='*95}")

results = []
for cat, desc, keywords, source in GAPS:
    cov = odoo_coverage(keywords)
    signal = "🔴 ZERO"   if cov["apps"] == 0 else \
             "🟡 THIN"   if cov["apps"] <= 3 else \
             "🟢 OK"     if cov["apps"] <= 15 else \
             "⚪ CROWDED"
    results.append((cat, desc, source, cov["apps"], cov["sales"], cov["last_month"], signal))

# Sort: zeros first, then thin, then by sales
order = {"🔴 ZERO": 0, "🟡 THIN": 1, "🟢 OK": 2, "⚪ CROWDED": 3}
results.sort(key=lambda r: (order[r[6]], -r[4]))

for cat, desc, source, apps, sales, last_mo, signal in results:
    print(f"{cat:<35} {source:<15} {apps:>9,} {sales:>8,} {last_mo:>7,}  {signal}")

print(f"\n{'='*95}")
print("\n🔴 ZERO = no Odoo app exists | 🟡 THIN = 1-3 apps (exploitable) | 🟢 OK = some coverage | ⚪ CROWDED")

# ── Summarise ──────────────────────────────────────────────────────────────────
zeros = [r for r in results if r[6] == "🔴 ZERO"]
thin  = [r for r in results if r[6] == "🟡 THIN"]
print(f"\n{len(zeros)} ZERO-competition gaps  |  {len(thin)} THIN gaps")
print(f"\nTop ZERO picks by ecosystem:\n")
by_source = {}
for r in zeros:
    by_source.setdefault(r[2], []).append(r[0])
for src, cats in sorted(by_source.items()):
    print(f"  {src:<18} {', '.join(cats[:3])}")

con.close()
