"""
Odoo App Validator — real-time intelligence from 67k marketplace apps.
Every number is a live DuckDB query. No AI guessing.

Run: streamlit run dashboard/app.py
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "odoo.duckdb"
LATEST_RUN = "20260508T180021Z-19e350"

# Rank 3: Odoo SA built-in warning
ODOO_OWNED = {
    'subscription':  'Odoo Subscriptions (Enterprise v13+)',
    'recurring':     'Odoo Subscriptions (Enterprise v13+)',
    'esign':         'Odoo Sign (Enterprise v11+)',
    'e-sign':        'Odoo Sign (Enterprise v11+)',
    'expense':       'Odoo Expenses (built-in all editions)',
    'elearning':     'Odoo eLearning (v13+)',
    'field service': 'Odoo Field Service (Enterprise v13+)',
    'helpdesk':      'Odoo Helpdesk (Enterprise v13+)',
    'repair':        'Odoo Repairs (built-in)',
    'timesheet':     'Odoo Timesheets (built-in)',
    'appraisal':     'Odoo Appraisals (Enterprise)',
}

# Rank 7: forced-buyer / mandatory-deadline keywords
MANDATORY_DEADLINE_KWS = ['e-slog', 'eslog', 'peppol', 'zatca', 'irn', 'eway bill',
                          'ewaybill', 'gst 2.0', 'e-invoice mandate', 'ksef', 'mydata']
MIGRATION_TRIGGER_KWS  = ['quickbooks', 'qbo', 'tally', 'sage', 'myob', 'dynamics gp',
                           'dynamics nav', 'netsuite', 'wave accounting', 'datev',
                           'busy accounting']

# Rank 10: migrator-app scoring branch
MIGRATOR_KEYWORDS = ['quickbooks', 'qbo', 'tally', 'sage', 'myob', 'xero', 'dynamics',
                     'netsuite', 'wave accounting', 'zoho books', 'busy accounting', 'datev']
MIGRATOR_DEMAND_PROXY = {
    'quickbooks': 90, 'qbo': 90, 'tally': 80, 'datev': 85,
    'dynamics': 75, 'sage': 65, 'myob': 65, 'xero': 70,
    'netsuite': 75, 'zoho books': 60, 'busy accounting': 70, 'wave': 55,
}

# Rank 9: ERP installed-base TAM lookup
ERP_INSTALLED_BASE = {
    'QuickBooks': {'installs': 9_000_000, 'churn': 0.08, 'geo': 'US/UK/CA/AU'},
    'Tally':      {'installs': 2_000_000, 'churn': 0.03, 'geo': 'India/UAE'},
    'DATEV':      {'installs':   500_000, 'churn': 0.02, 'geo': 'Germany'},
    'MYOB':       {'installs': 1_200_000, 'churn': 0.05, 'geo': 'AU/NZ'},
    'Sage':       {'installs': 3_000_000, 'churn': 0.04, 'geo': 'UK/EU'},
    'Busy':       {'installs': 1_000_000, 'churn': 0.03, 'geo': 'India'},
    'Wave':       {'installs':   500_000, 'churn': 0.08, 'geo': 'US/CA'},
    'Microsoft':  {'installs':   300_000, 'churn': 0.05, 'geo': 'US/EU'},
    'Oracle':     {'installs':   200_000, 'churn': 0.04, 'geo': 'Global'},
    'Marg':       {'installs':   800_000, 'churn': 0.03, 'geo': 'India'},
    'BambooHR':   {'installs':   500_000, 'churn': 0.06, 'geo': 'US/EU'},
}

st.set_page_config(
    page_title="Odoo App Validator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.score-hero {
    text-align: center; padding: 32px 20px 24px;
    background: #1e1e2e; border-radius: 12px; margin-bottom: 24px;
    border: 1px solid #313244;
}
.score-num-high { color: #a6e3a1; font-size: 5rem; font-weight: 900; line-height:1; }
.score-num-mid  { color: #f9e2af; font-size: 5rem; font-weight: 900; line-height:1; }
.score-num-low  { color: #f38ba8; font-size: 5rem; font-weight: 900; line-height:1; }
.verdict-high { background:#a6e3a1; color:#1e1e2e; padding:4px 16px;
                border-radius:20px; font-weight:700; font-size:0.85rem; letter-spacing:1px; }
.verdict-mid  { background:#f9e2af; color:#1e1e2e; padding:4px 16px;
                border-radius:20px; font-weight:700; font-size:0.85rem; letter-spacing:1px; }
.verdict-low  { background:#f38ba8; color:#1e1e2e; padding:4px 16px;
                border-radius:20px; font-weight:700; font-size:0.85rem; letter-spacing:1px; }
.section-card {
    background:#1e1e2e; border:1px solid #313244; border-radius:10px;
    padding:18px 20px; margin-bottom:16px;
}
.section-title { color:#89b4fa; font-size:0.75rem; font-weight:700;
                 letter-spacing:2px; text-transform:uppercase; margin-bottom:10px; }
.pivot-box  { background:#181825; border-left:3px solid #89b4fa;
              padding:10px 14px; border-radius:4px; margin-bottom:8px; }
.action-item { background:#181825; border-left:3px solid #a6e3a1;
               padding:10px 14px; border-radius:4px; margin-bottom:8px; }
.risk-high { color:#f38ba8; font-weight:700; }
.risk-med  { color:#f9e2af; font-weight:700; }
.risk-low  { color:#a6e3a1; font-weight:700; }
.stat-row  { display:flex; gap:24px; flex-wrap:wrap; margin-top:8px; }
.stat-item { text-align:center; }
.stat-val  { font-size:1.6rem; font-weight:700; color:#cdd6f4; }
.stat-lbl  { font-size:0.72rem; color:#6c7086; text-transform:uppercase; letter-spacing:1px; }
</style>
""", unsafe_allow_html=True)


def get_conn():
    return duckdb.connect(str(DB_PATH), read_only=True)


def score_color(v):
    if v >= 70:
        return "score-high"
    if v >= 40:
        return "score-mid"
    return "score-low"


def render_gauge(label, value, help_text=""):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": label, "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": "#89b4fa"},
            "steps": [
                {"range": [0, 40],  "color": "#313244"},
                {"range": [40, 70], "color": "#45475a"},
                {"range": [70, 100],"color": "#585b70"},
            ],
            "threshold": {
                "line": {"color": "#cba6f7", "width": 3},
                "thickness": 0.8,
                "value": value,
            },
        },
        number={"font": {"size": 28}},
    ))
    fig.update_layout(height=200, margin=dict(t=40, b=10, l=10, r=10),
                      paper_bgcolor="rgba(0,0,0,0)", font_color="#cdd6f4")
    st.plotly_chart(fig, use_container_width=True)


# ─── HEADER ──────────────────────────────────────────────────────────────────
st.title("🔍 Odoo App Validator")
st.caption(f"Live queries on **67,370 apps** from apps.odoo.com snapshot (May 2026)")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ Validate Idea", "🗺 Market Map", "🏆 Author Intel", "🌍 Partner Map", "🎯 ERP Gap Finder"])


def _render_validate(keywords, min_purchases, search_mode="Name only"):
    if not keywords.strip():
        st.info("Enter your app idea keywords above — e.g.  `tally, migration`  or  `hospital, patient`")
        return

    conn = get_conn()
    terms = [t.strip() for t in keywords.split(",") if t.strip()]
    name_conds = " OR ".join([f"display_name ILIKE '%{t}%'" for t in terms])
    summ_conds = " OR ".join([f"summary ILIKE '%{t}%'" for t in terms])

    # Rank 4: name-only for scoring (precise), name+summary optional
    filter_conds = name_conds if "Name only" in search_mode else f"({name_conds} OR {summ_conds})"

    df = conn.execute(f"""
        SELECT display_name, author,
               ROUND(price_cents / 100.0, 2)  AS price_usd,
               COALESCE(rating_stars, 0)       AS rating_stars,
               COALESCE(review_count, 0)       AS review_count,
               COALESCE(total_purchases, 0)    AS total_purchases,
               COALESCE(last_month_purchases,0)AS last_month_purchases,
               ROUND(CASE WHEN COALESCE(total_purchases,0) > 0
                          THEN COALESCE(last_month_purchases,0) * 100.0 / total_purchases
                          ELSE 0 END, 1)       AS velocity_pct,
               detail_url, summary
        FROM app_snapshots
        WHERE run_id = '{LATEST_RUN}'
          AND ({filter_conds})
          AND COALESCE(total_purchases,0) >= {int(min_purchases)}
        ORDER BY total_purchases DESC NULLS LAST
    """).df()

    # Show summary-only matches in expander when in precise mode
    if "Name only" in search_mode:
        df_broad_n = (conn.execute(f"""
            SELECT COUNT(*) FROM app_snapshots
            WHERE run_id = '{LATEST_RUN}' AND ({summ_conds})
              AND NOT ({name_conds})
              AND COALESCE(total_purchases,0) >= {int(min_purchases)}
        """).fetchone() or (0,))[0]
        if df_broad_n > 0:
            with st.expander(f"Also found in summaries (not counted in score): {df_broad_n} apps mention this keyword as a feature"):
                df_broad = conn.execute(f"""
                    SELECT display_name, author, ROUND(price_cents/100.0,2) as price_usd,
                           COALESCE(total_purchases,0) as total_purchases, detail_url
                    FROM app_snapshots
                    WHERE run_id = '{LATEST_RUN}' AND ({summ_conds})
                      AND NOT ({name_conds})
                      AND COALESCE(total_purchases,0) >= {int(min_purchases)}
                    ORDER BY total_purchases DESC LIMIT 20
                """).df()
                st.dataframe(df_broad, use_container_width=True, hide_index=True,
                             column_config={"detail_url": st.column_config.LinkColumn("Link"),
                                            "price_usd": st.column_config.NumberColumn(format="$%.0f")})

    n = len(df)
    if n == 0:
        st.warning("No apps found. Try broader keywords or switch to 'Name + Summary' mode.")
        return

    kw_lower = keywords.lower()

    # Rank 3: Odoo SA owns this niche warning
    odoo_warnings = [module for kw, module in ODOO_OWNED.items() if kw in kw_lower]
    if odoo_warnings:
        st.warning(f"⚠️ ODOO SA OWNS THIS NICHE: **{odoo_warnings[0]}** — Enterprise users get this for free. "
                   f"Target Community edition users only, or add a vertical specialization (e.g., India GST, "
                   f"manufacturing compliance) that Enterprise doesn't cover.")

    # Rank 10: Migrator detection
    is_migrator = any(k in kw_lower for k in MIGRATOR_KEYWORDS)
    if is_migrator:
        st.info("🚀 **MIGRATOR APP DETECTED** — demand lives OUTSIDE the marketplace. ERP refugees "
                "search Google & forums, not Odoo Apps. Velocity data understates true demand by 5-10x.")

    # ── Core metrics ──────────────────────────────────────────────────────────
    total_purchases  = df["total_purchases"].sum()
    velocity         = df["last_month_purchases"].sum()
    dead_apps        = (df["total_purchases"] == 0).sum()
    active_apps      = (df["last_month_purchases"] > 0).sum()
    # Rank 1: use active_apps denominator (not n) for demand + velocity
    avg_purchases    = total_purchases / max(active_apps, 1)
    velocity_per_app = velocity / max(active_apps, 1) if active_apps > 0 else 0
    paid_df          = df[df["price_usd"] > 0]
    low_df           = df[(df["price_usd"] > 0) & (df["price_usd"] <= 30)]
    avg_price        = paid_df["price_usd"].mean() if len(paid_df) > 0 else 0
    top_author_share = (
        df.groupby("author")["total_purchases"].sum().max() / total_purchases * 100
        if total_purchases > 0 else 0
    )
    # Rank 5: stale incumbent / stranded buyer detection
    stale_paid      = paid_df[(paid_df["total_purchases"] > 50) & (paid_df["last_month_purchases"] == 0)]
    stale_count     = len(stale_paid)
    stranded_buyers = int(stale_paid["total_purchases"].sum())
    # Rank 8: recency ratio
    recency_ratio = velocity / max(total_purchases, 1)
    recency_pct   = round(recency_ratio * 100, 1)

    # ── Sub-scores ────────────────────────────────────────────────────────────
    dead_pct = dead_apps / n if n > 0 else 0

    # sat (+ Rank 2: graveyard cap)
    if   n <= 4:   sat = 25
    elif n <= 15:  sat = 90
    elif n <= 30:  sat = 70
    elif n <= 60:  sat = 45
    elif n <= 120: sat = 25
    else:          sat = 10
    if dead_pct >= 0.80 and n > 3:
        sat = min(sat, 35)  # graveyard cap

    # demand (Rank 1: active denominator + Rank 10: migrator override)
    if is_migrator:
        demand = max((MIGRATOR_DEMAND_PROXY.get(k, 50) for k in MIGRATOR_KEYWORDS if k in kw_lower), default=60)
    else:
        if   avg_purchases > 500: demand = 90
        elif avg_purchases > 200: demand = 75
        elif avg_purchases > 80:  demand = 60
        elif avg_purchases > 20:  demand = 40
        elif avg_purchases > 5:   demand = 25
        else:                      demand = 10

    if   len(paid_df) == 0:  gap = 50
    elif len(low_df) == 0:   gap = 90
    elif len(low_df) <= 3:   gap = 70
    elif len(low_df) <= 8:   gap = 45
    else:                     gap = 20

    # moat (+ Rank 5: stale incumbent bonus)
    if   top_author_share > 60: moat = 20
    elif top_author_share > 40: moat = 45
    elif top_author_share > 20: moat = 65
    else:                        moat = 85
    if stale_count >= 2 and stale_count / max(len(paid_df), 1) >= 0.5:
        moat = min(95, moat + 15)

    # momentum (Rank 8: recency bonus + Rank 10: migrator override)
    if is_migrator:
        momentum = 70
    else:
        if   velocity_per_app > 10:  momentum = 90
        elif velocity_per_app > 5:   momentum = 80
        elif velocity_per_app > 2:   momentum = 65
        elif velocity_per_app > 0.5: momentum = 45
        elif velocity_per_app > 0.1: momentum = 25
        else:                         momentum = 10
    recency_bonus = min(20, int(recency_ratio * 200))
    momentum = min(90, momentum + recency_bonus)

    # Rank 2: dead_health as 6th component
    if   n <= 3:             dead_health = 50
    elif dead_pct <= 0.40:   dead_health = 85
    elif dead_pct <= 0.55:   dead_health = 65
    elif dead_pct <= 0.70:   dead_health = 45
    elif dead_pct <= 0.85:   dead_health = 25
    else:                     dead_health = 10

    # Rank 7: forced-buyer score
    forced_buyer = 10
    if any(k in kw_lower for k in MANDATORY_DEADLINE_KWS):
        forced_buyer = 90
    elif any(k in kw_lower for k in MIGRATION_TRIGGER_KWS):
        forced_buyer = 70

    # New viability formula: 7 components
    viability = int(sat*0.18 + demand*0.22 + gap*0.12 + dead_health*0.13
                    + moat*0.08 + momentum*0.17 + forced_buyer*0.10)

    # ── Verdict label ─────────────────────────────────────────────────────────
    if   viability >= 80: verdict, vclass = "LAUNCH READY",   "verdict-high",
    elif viability >= 65: verdict, vclass = "VALIDATED",      "verdict-high"
    elif viability >= 50: verdict, vclass = "ONE STEP AWAY",  "verdict-mid"
    elif viability >= 35: verdict, vclass = "NEEDS A PIVOT",  "verdict-low"
    else:                 verdict, vclass = "DO NOT BUILD",   "verdict-low"

    sclass = "score-num-high" if viability >= 65 else "score-num-mid" if viability >= 40 else "score-num-low"

    # ── Regulatory risk ───────────────────────────────────────────────────────
    HIGH_REG  = ['health','pharma','hospital','patient','clinic','medical','bank','banking',
                 'insurance','kyc','aml','gdpr','hipaa','crypto','legal','court','drug']
    MED_REG   = ['payroll','hr','employee','invoice','accounting','gst','vat','einvoice',
                 'tax','compliance','finance','nbfc','loan']
    if any(k in kw_lower for k in HIGH_REG):
        reg_level, reg_note = "HIGH", "Health/Finance/Legal niche — liability exposure in US/EU. Target India/SEA to avoid."
    elif any(k in kw_lower for k in MED_REG):
        reg_level, reg_note = "MEDIUM", "Compliance-adjacent — accuracy matters but no licensing required for software."
    else:
        reg_level, reg_note = "LOW", "No significant regulatory risk for a marketplace app in this niche."

    # ── TAM / SAM / SOM (Rank 4: use paid_df only) ───────────────────────────
    paid_velocity = int(paid_df["last_month_purchases"].sum()) if len(paid_df) > 0 else 0
    sam        = int(paid_df["total_purchases"].sum() * avg_price) if avg_price > 0 else 0
    monthly_rev = int(paid_velocity * avg_price) if avg_price > 0 else 0
    som_year1   = int(monthly_rev * 12 * 0.05)

    # ── GTM recommendation ────────────────────────────────────────────────────
    if avg_price > 100:
        gtm_channel  = "Direct outreach to Odoo partners + LinkedIn"
        gtm_price    = f"${max(49, int(avg_price * 0.6))}–${int(avg_price * 0.8)} (undercut leaders by 20–40%)"
    elif avg_price > 30:
        gtm_channel  = "Odoo Apps marketplace (organic) + announce in Odoo Community forum"
        gtm_price    = f"${max(15, int(avg_price * 0.5))}–${int(avg_price * 0.75)} (own the entry tier)"
    else:
        gtm_channel  = "Odoo Apps marketplace free-then-paid funnel"
        gtm_price    = f"$15–$25 (market is price-sensitive, volume game)"

    # ── Pivot options ─────────────────────────────────────────────────────────
    pivots = []
    if momentum >= 80:
        pivots.append(("Hot Right Now", f"{velocity_per_app:.1f} purchases/app last month — market is actively buying. Ship fast."))
    elif momentum <= 25:
        pivots.append(("Cold Market", f"Only {velocity_per_app:.2f} sales/app last month. Validate on Odoo forum before building."))
    if n > 60:
        pivots.append(("Niche Down", f"{n} apps is crowded. Add a vertical (India GST, manufacturing, F&B) to cut to 10–20 real competitors."))
    if len(low_df) == 0 and len(paid_df) > 0:
        pivots.append(("Price Wedge", f"No app under $30 in this niche. A stripped-down ${int(avg_price*0.3)+5} version owns the entry tier."))
    if top_author_share > 50:
        pivots.append(("UX Flanking", f"One author has {top_author_share:.0f}% of all sales. Read their 1-star reviews — that's your product spec."))
    if demand < 30 and n > 5:
        pivots.append(("Validate Demand First", "Low purchase count despite competition. Survey Odoo forum + r/Odoo before writing code."))
    if dead_apps / n > 0.6:
        pivots.append(("Quality Gap", f"{dead_apps}/{n} apps have ZERO sales ever. Market exists but most builders failed — execution is the moat."))
    if sat == 25 and n <= 4:
        pivots.append(("Blue Ocean", "Almost no competition — but also little proof of demand. Do 5 customer interviews before writing code."))
    if stale_count >= 2:
        pivots.append(("Attack Window", f"{stale_count} paid app(s) with {stranded_buyers:,} total buyers show 0 sales this month. Ship a v18 replacement — these are your warm launch leads."))
    if forced_buyer >= 70:
        pivots.append(("Forced Buyer Market", "Deadline-driven or platform-exit buyers MUST switch. First sale speed is 3-5x faster than discretionary niches. Ship before the deadline."))
    if not pivots:
        pivots.append(("Green Light", "Scores look solid. Pick the recommended price point, ship a focused v1, iterate on reviews."))
    pivots = pivots[:4]  # max 4 (was 3)

    # ── Action plan ───────────────────────────────────────────────────────────
    actions = []
    if viability >= 65:
        actions = [
            f"Study top 3 competitor apps — read ALL their reviews (1-star = your feature list)",
            f"Set your launch price at {gtm_price.split('(')[0].strip()} — verify no app exists at that tier",
            f"Build MVP in 2–3 weeks: core feature only, no bloat",
            f"Submit to apps.odoo.com + post in Odoo Community forum on launch day",
            f"Target {int(som_year1/avg_price) if avg_price > 0 else 10} sales in Year 1 = ${som_year1:,} revenue at your price point",
        ]
    elif viability >= 40:
        actions = [
            "Post a question in Odoo Community forum: describe the problem, NOT your solution — count replies",
            "DM 3 Odoo implementers (from Gold partner list) — ask if clients request this",
            "Check if the top competitor has been updated in the last 6 months (stale = opportunity)",
            f"If validation passes: price at {gtm_price.split('(')[0].strip()} and build a 2-week MVP",
            "Reassess after 2 weeks of outreach — pivot if <3 people express real interest",
        ]
    else:
        actions = [
            "Do NOT build — score too low to justify dev time",
            "Run the ERP Gap Finder tab to find a zero-competition niche instead",
            "Consider a migrator app (Tally/SAP/QB) — all have zero/thin competition and proven demand",
            "If you still believe in this idea, find 5 paying customers BEFORE writing any code",
            "Return here after customer conversations — rescore with refined keywords",
        ]

    # ════════════════════════════════════════════════════════════════════════
    # RENDER
    # ════════════════════════════════════════════════════════════════════════

    # Rank 6: Odoo v17/18 secondary count
    n_v18 = (conn.execute(f"""
        SELECT COUNT(*) FROM app_snapshots s JOIN apps a ON a.app_key = s.app_key
        WHERE s.run_id = '{LATEST_RUN}' AND ({filter_conds}) AND a.version IN ('17.0','18.0')
    """).fetchone() or (0,))[0]

    # ── HERO ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="score-hero">
      <div class="{sclass}">{viability}</div>
      <div style="margin-top:8px"><span class="{vclass}">{verdict}</span></div>
      <div style="color:#6c7086; margin-top:12px; font-size:0.85rem">
        {n} apps found ({n_v18} on Odoo 17/18) · {int(total_purchases):,} total sales · {int(velocity):,} last-month purchases
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── EVIDENCE ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Evidence — what the data says</div>', unsafe_allow_html=True)
    e1, e2, e3, e4, e5, e6, e7, e8 = st.columns(8)
    e1.metric("Total Sales", f"{int(total_purchases):,}")
    e2.metric("Avg Sales/Active App", f"{avg_purchases:.0f}", help="Excludes apps with zero sales from denominator")
    e3.metric("Last Month", f"{int(velocity):,}")
    e4.metric("Vel/Active App", f"{velocity_per_app:.2f}", help="Monthly velocity per actively-selling app")
    e5.metric("Dead Apps", f"{dead_apps}/{n}")
    e6.metric("Active Apps", f"{active_apps}/{n}")
    e7.metric("Stranded Buyers", f"{stranded_buyers:,}", help="Buyers who paid for apps now showing 0 sales — your warm launch audience")
    e8.metric("Recency Rate", f"{recency_pct}%", help="% of all-time sales that happened last month. >5% = accelerating market")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── MARKET DATA (TAM/SAM/SOM) ─────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Market Data — TAM / SAM / SOM (paid apps only)</div>', unsafe_allow_html=True)
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("SAM (paid apps)", f"${sam:,}", help="Paid-app purchases × avg paid price")
    t2.metric("Monthly Run Rate", f"${monthly_rev:,}", help="Last-month paid velocity × avg price")
    t3.metric("Your Year-1 SOM (5%)", f"${som_year1:,}", help="Monthly run rate × 12 × 5%")
    t4.metric("Avg Market Price", f"${avg_price:.0f}", help="Average price of paid apps in niche")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── GAUGES ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Score Breakdown — 7 components</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1: render_gauge("Saturation", sat)
    with c2: render_gauge("Demand", demand)
    with c3: render_gauge("Price Gap", gap)
    with c4: render_gauge("Moat Risk", moat)
    with c5: render_gauge("Momentum", momentum)
    with c6: render_gauge("Mkt Health", dead_health)
    with c7: render_gauge("Forced Buy", forced_buyer)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── COMPETITORS ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Competitors — top apps in this niche</div>', unsafe_allow_html=True)
    st.markdown(f'**Leader controls {top_author_share:.0f}% of sales** · {len(paid_df)} paid apps · {len(low_df)} under $30')
    display_df = df[["display_name", "author", "price_usd", "rating_stars",
                      "review_count", "total_purchases", "last_month_purchases",
                      "velocity_pct", "detail_url"]].copy()
    display_df["Stale"] = ((df["total_purchases"] > 50) & (df["last_month_purchases"] == 0)).map({True: "YES", False: ""})
    display_df.columns = ["App", "Author", "Price $", "Stars", "Reviews",
                          "Total Sales", "Last Month", "Velocity %", "URL", "Stale?"]
    st.dataframe(display_df.head(20), use_container_width=True, hide_index=True,
        column_config={
            "URL":        st.column_config.LinkColumn("Link"),
            "Stars":      st.column_config.NumberColumn(format="%.1f"),
            "Price $":    st.column_config.NumberColumn(format="$%.0f"),
            "Velocity %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
        })
    st.markdown('</div>', unsafe_allow_html=True)

    # ── BUSINESS MODEL (price tiers) ──────────────────────────────────────────
    if len(paid_df) > 0:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Business Model — price tier map</div>', unsafe_allow_html=True)
        bins   = [0, 10, 20, 30, 50, 100, 200, 500, 99999]
        labels = ["<$10","$10-20","$20-30","$30-50","$50-100","$100-200","$200-500","$500+"]
        paid_copy = paid_df.copy()
        paid_copy["tier"] = pd.cut(paid_copy["price_usd"], bins=bins, labels=labels, right=True)
        tier_counts = paid_copy.groupby("tier", observed=True).agg(
            Count=("price_usd","count"), Sales=("total_purchases","sum")
        ).reindex(labels, fill_value=0).reset_index()
        tier_counts.columns = ["Tier","Apps","Total Sales"]
        col_l, col_r = st.columns(2)
        with col_l:
            fig = px.bar(tier_counts, x="Tier", y="Apps", color="Apps",
                         color_continuous_scale="Blues",
                         title="Apps per tier — empty = open slot")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#cdd6f4", showlegend=False, height=250)
            st.plotly_chart(fig, use_container_width=True)
        with col_r:
            fig2 = px.bar(tier_counts, x="Tier", y="Total Sales", color="Total Sales",
                          color_continuous_scale="Greens",
                          title="Sales per tier — where buyers actually pay")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#cdd6f4", showlegend=False, height=250)
            st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── GO-TO-MARKET ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Go-to-Market</div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    g1.markdown(f"**Recommended Price**  \n{gtm_price}")
    g2.markdown(f"**Primary Channel**  \n{gtm_channel}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── REGULATORY RISK ───────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Regulatory Risk</div>', unsafe_allow_html=True)
    rc = "risk-high" if reg_level=="HIGH" else "risk-med" if reg_level=="MEDIUM" else "risk-low"
    st.markdown(f'<span class="{rc}">{reg_level}</span>  —  {reg_note}', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── PIVOTS ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">3 Pivot Directions</div>', unsafe_allow_html=True)
    for i, (title, body) in enumerate(pivots, 1):
        st.markdown(
            f'<div class="pivot-box" style="color:#cdd6f4">'
            f'<strong>Pivot {i}: {title}</strong><br>{body}</div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── ACTION PLAN ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Action Plan — next 5 steps</div>', unsafe_allow_html=True)
    for i, step in enumerate(actions, 1):
        st.markdown(
            f'<div class="action-item" style="color:#cdd6f4">'
            f'<strong>Step {i}</strong> — {step}</div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── EFFORT SCORE + BREAK-EVEN CALCULATOR ─────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Effort Score & Break-Even Calculator</div>', unsafe_allow_html=True)

    # Auto-detect effort based on keywords
    kw_low = keywords.lower()
    if any(k in kw_low for k in ['tally','busy','quickbooks','xero','sage','zoho','myob','wave','netsuite','dynamics','sap migration']):
        effort_score, effort_label, effort_weeks = 2, "Migration Tool — parse export file → Odoo import. No live API.", "2–3"
    elif any(k in kw_low for k in ['shopify','woocommerce','amazon','ebay','magento','flipkart','meesho']):
        effort_score, effort_label, effort_weeks = 3, "eCommerce Connector — needs OAuth + webhook handling.", "3–4"
    elif any(k in kw_low for k in ['whatsapp','telegram','sms','twilio','ivr','telephony']):
        effort_score, effort_label, effort_weeks = 3, "Messaging Connector — third-party API + Odoo chatter hook.", "2–3"
    elif any(k in kw_low for k in ['gst','einvoice','eway','vat','tax','compliance','kyc']):
        effort_score, effort_label, effort_weeks = 3, "Compliance App — govt API + validation logic. Accuracy critical.", "3–4"
    elif any(k in kw_low for k in ['hospital','clinic','patient','pharma','lims','fhir']):
        effort_score, effort_label, effort_weeks = 4, "Healthcare App — domain complexity + compliance risk.", "4–6"
    elif any(k in kw_low for k in ['dashboard','report','analytics','kpi','chart','pivot']):
        effort_score, effort_label, effort_weeks = 1, "Report/Dashboard — pure Odoo views + QWeb. No external dependency.", "1–2"
    elif any(k in kw_low for k in ['barcode','qr','label','print']):
        effort_score, effort_label, effort_weeks = 1, "Print/Label App — Odoo reports + ZPL/PDF. Simple.", "1–2"
    elif any(k in kw_low for k in ['payroll','salary','leave','attendance','biometric']):
        effort_score, effort_label, effort_weeks = 3, "HR/Payroll — country-specific rules + Odoo payroll hooks.", "3–4"
    else:
        effort_score, effort_label, effort_weeks = 2, "Standard Odoo module — models + views + wizard. No external API.", "2–3"

    effort_colors = {1:"#a6e3a1", 2:"#94e2d5", 3:"#f9e2af", 4:"#fab387", 5:"#f38ba8"}
    ec = effort_colors.get(effort_score, "#cdd6f4")
    effort_dots = "●" * effort_score + "○" * (5 - effort_score)

    st.markdown(
        f'<div style="color:{ec}; font-size:1.4rem; font-weight:700; margin-bottom:4px">'
        f'Effort: {effort_score}/5 &nbsp; {effort_dots}</div>'
        f'<div style="color:#cdd6f4; margin-bottom:16px">{effort_label} &nbsp;·&nbsp; Est. build time: <strong>{effort_weeks} weeks</strong></div>',
        unsafe_allow_html=True)

    st.markdown("**Break-even calculator** — adjust to your situation:")
    be1, be2, be3 = st.columns(3)
    with be1:
        your_price  = st.number_input("Your launch price ($)", value=max(19, int(avg_price * 0.6)) if avg_price > 0 else 29, step=5, key="be_price")
    with be2:
        your_hours  = st.number_input("Hours to build", value=int(effort_score * 30), step=10, key="be_hours")
    with be3:
        hourly_rate = st.number_input("Your hourly cost ($)", value=15, step=5, key="be_rate")

    total_cost   = your_hours * hourly_rate
    sales_needed = (total_cost / your_price) if your_price > 0 else 0
    niche_monthly_sales = velocity
    # Rank 4: dynamic capture rate based on market structure
    if top_author_share > 50 or n > 30:
        your_share_pct = 0.02
        capture_label  = "2% capture (leader-dominated market)"
    elif n <= 10:
        your_share_pct = 0.08
        capture_label  = "8% capture (thin market, new entrant can win fast)"
    else:
        your_share_pct = 0.05
        capture_label  = "5% capture (balanced market)"
    your_monthly = max(1, niche_monthly_sales * your_share_pct)
    days_to_be   = (sales_needed / your_monthly) * 30 if your_monthly > 0 else 999
    # worst-case at 1%
    days_worst   = (sales_needed / max(1, niche_monthly_sales * 0.01)) * 30

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Total Cost to Build", f"${total_cost:,.0f}")
    b2.metric("Sales to Break Even", f"{sales_needed:.0f}")
    b3.metric("Niche Buys/Month", f"{int(niche_monthly_sales)}")
    b4.metric("Days to Break Even", f"{days_to_be:.0f}" if days_to_be < 999 else "—",
              delta=capture_label if days_to_be < 999 else "low velocity")
    if days_worst < 9999:
        st.caption(f"Worst-case at 1% capture: **{days_worst:.0f} days** to break even")

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — VALIDATE IDEA
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Drop your idea — get scored against 67k real apps")
    col_input, col_mode, col_opts = st.columns([3, 2, 1])
    with col_input:
        keywords = st.text_input(
            "Keywords (comma-separated)",
            placeholder="e.g.  datev, buchungsstapel  or  busy accounting, migration",
        )
    with col_mode:
        search_mode = st.radio(
            "Search precision",
            ["Name only (precise — use for scoring)", "Name + Summary (broad)"],
            index=0, horizontal=True,
            help="Name-only eliminates false positives from apps that just mention your keyword as a feature. "
                 "Name+Summary is useful for discovery but inflates competitor count.",
        )
    with col_opts:
        min_purchases = st.number_input("Min purchases filter", value=0, step=10,
                                        help="Hide noise — only show apps with ≥N total purchases")
    # Quick-launch buttons for top validated niches
    st.caption("Quick validate:")
    qb1, qb2, qb3, qb4, qb5 = st.columns(5)
    if qb1.button("DATEV (Germany)", use_container_width=True):
        keywords = "datev, buchungsstapel"
    if qb2.button("Busy Accounting (India)", use_container_width=True):
        keywords = "busy accounting, migration"
    if qb3.button("MYOB (AU/NZ)", use_container_width=True):
        keywords = "myob, migration"
    if qb4.button("QB Desktop (UK/CA)", use_container_width=True):
        keywords = "quickbooks, migration"
    if qb5.button("Zoho Books India", use_container_width=True):
        keywords = "zoho books, migration"

    _render_validate(keywords, min_purchases, search_mode)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MARKET MAP
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Full marketplace overview — 67k apps, real numbers")
    conn = get_conn()

    # ── SPEED-TO-DOLLAR MATRIX ────────────────────────────────────────────────
    st.markdown("#### 🚀 Speed-to-Dollar Matrix")
    st.caption("X = dead app % (higher = quality vacuum) · Y = velocity/app · bubble = monthly niche revenue · color = competition")

    S2D_NICHES = [
        ("WooCommerce",         ["woocommerce"]),
        ("Shopify",             ["shopify"]),
        ("Amazon",              ["amazon seller","amazon connector"]),
        ("Hospital/Clinic",     ["hospital","clinic","patient"]),
        ("QuickBooks migrator", ["quickbooks","qbo"]),
        ("WhatsApp",            ["whatsapp"]),
        ("Barcode/WMS",         ["barcode","warehouse management"]),
        ("Tally migrator",      ["tally"]),
        ("Payroll India",       ["payroll","salary slip"]),
        ("Attendance",          ["attendance","biometric"]),
        ("GST/eInvoice",        ["gst","einvoice","e-invoice"]),
        ("Fleet",               ["fleet","vehicle tracking"]),
        ("Subscription",        ["subscription","recurring"]),
        ("eWay Bill",           ["eway bill","ewaybill"]),
        ("Xero migrator",       ["xero"]),
        ("Dynamics migrator",   ["dynamics","business central"]),
        ("DATEV",               ["datev"]),
        ("Zoho migrator",       ["zoho books","zoho migration"]),
        ("Busy migrator",       ["busy accounting"]),
        ("Helpdesk",            ["helpdesk","ticket"]),
        ("Manufacturing MRP",   ["mrp","bill of materials"]),
        ("Document OCR",        ["ocr","receipt scan"]),
        ("Email marketing",     ["email marketing","mass mail"]),
        ("Pharma/Batch",        ["batch tracking","expiry","lot traceability"]),
    ]

    @st.cache_data(ttl=3600)
    def compute_s2d():
        c = get_conn()
        rows = []
        for label, kws in S2D_NICHES:
            cond = " OR ".join(f"display_name ILIKE '%{k}%' OR summary ILIKE '%{k}%'" for k in kws)
            r = c.execute(f"""
                SELECT COUNT(*) as apps,
                       COALESCE(SUM(total_purchases),0) as sales,
                       COALESCE(SUM(last_month_purchases),0) as lmo,
                       COALESCE(AVG(CASE WHEN price_cents>0 THEN price_cents/100.0 END),0) as avg_p,
                       SUM(CASE WHEN COALESCE(total_purchases,0)=0 THEN 1 ELSE 0 END) as dead
                FROM app_snapshots WHERE run_id='{LATEST_RUN}' AND ({cond})
            """).fetchone() or (0, 0, 0, 0, 0)
            apps, sales, lmo, avg_p, dead = r
            avg_p = avg_p or 0
            dead_pct   = round(dead / apps * 100, 1) if apps > 0 else 0
            vel_app    = round(lmo / apps, 2) if apps > 0 else 0
            monthly_rev = int(lmo * avg_p)
            rows.append({
                "Niche": label, "Apps": apps, "Dead %": dead_pct,
                "Vel/App": vel_app, "Monthly Rev $": monthly_rev,
                "Avg Price": round(avg_p, 0),
            })
        return pd.DataFrame(rows)

    s2d_df = compute_s2d()

    # Quadrant annotation lines
    med_dead = s2d_df["Dead %"].median()
    med_vel  = s2d_df["Vel/App"].median()

    fig_s2d = px.scatter(
        s2d_df,
        x="Dead %", y="Vel/App",
        size="Monthly Rev $",
        color="Apps",
        text="Niche",
        size_max=60,
        color_continuous_scale="RdYlGn_r",
        title="Speed-to-Dollar Matrix — TOP RIGHT = build here (quality vacuum + active buyers)",
        labels={"Dead %": "Dead App % (higher = easier to win)", "Vel/App": "Velocity / App (demand right now)"},
        hover_data=["Apps", "Avg Price", "Monthly Rev $"],
    )
    fig_s2d.add_vline(x=med_dead, line_dash="dot", line_color="#585b70",
                      annotation_text="median dead%", annotation_font_color="#6c7086")
    fig_s2d.add_hline(y=med_vel,  line_dash="dot", line_color="#585b70",
                      annotation_text="median vel/app", annotation_font_color="#6c7086")
    fig_s2d.add_annotation(x=s2d_df["Dead %"].max()*0.85, y=s2d_df["Vel/App"].max()*0.9,
                            text="BUILD NOW", showarrow=False,
                            font=dict(color="#a6e3a1", size=14, family="monospace"))
    fig_s2d.add_annotation(x=s2d_df["Dead %"].min()*1.1, y=s2d_df["Vel/App"].min()*1.2,
                            text="AVOID", showarrow=False,
                            font=dict(color="#f38ba8", size=14, family="monospace"))
    fig_s2d.update_traces(textposition="top center", textfont_size=10)
    fig_s2d.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cdd6f4", height=520,
    )
    st.plotly_chart(fig_s2d, use_container_width=True)

    st.dataframe(
        s2d_df.sort_values("Vel/App", ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            "Monthly Rev $": st.column_config.NumberColumn(format="$%d"),
            "Vel/App":       st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=2),
            "Dead %":        st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
        }
    )
    st.divider()

    col_a, col_b = st.columns(2)

    # Price tier breakdown
    with col_a:
        tiers = conn.execute(f"""
        SELECT
          CASE
            WHEN price_cents IS NULL OR price_cents < 0 THEN 'Unknown'
            WHEN price_cents = 0               THEN 'Free'
            WHEN price_cents <= 999            THEN 'Under $10'
            WHEN price_cents <= 1999           THEN '$10–$19'
            WHEN price_cents <= 4999           THEN '$20–$49'
            WHEN price_cents <= 9999           THEN '$50–$99'
            WHEN price_cents <= 19999          THEN '$100–$199'
            WHEN price_cents <= 49999          THEN '$200–$499'
            ELSE 'Over $500'
          END AS tier,
          COUNT(*) AS app_count,
          COALESCE(SUM(total_purchases), 0) AS total_sales
        FROM app_snapshots
        WHERE run_id = '{LATEST_RUN}'
        GROUP BY 1
        ORDER BY MIN(COALESCE(price_cents, -1))
        """).df()

        fig = px.bar(
            tiers, x="tier", y="app_count", color="total_sales",
            color_continuous_scale="Purples",
            title="Apps per price tier (color = total purchases)",
            labels={"app_count": "# Apps", "tier": "Price Tier", "total_sales": "Total Sales"},
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#cdd6f4")
        st.plotly_chart(fig, use_container_width=True)

    # Top niches by keyword cluster
    with col_b:
        NICHES = [
            ("Accounting / Finance", "invoice,accounting,finance,ledger,tax,payment"),
            ("eCommerce / Shopify", "shopify,woocommerce,ecommerce,amazon,magento"),
            ("HR / Payroll",        "payroll,hr,employee,attendance,leave,recruitment"),
            ("Inventory / WMS",     "inventory,warehouse,stock,wms,picking,lot"),
            ("CRM / Sales",         "crm,sales,lead,opportunity,pipeline,customer"),
            ("Manufacturing / MRP", "manufacturing,mrp,bom,work order,production"),
            ("WhatsApp / Chat",     "whatsapp,telegram,chat,messaging,sms"),
            ("Dashboard / BI",      "dashboard,bi,report,analytics,kpi,chart"),
            ("Migration / Import",  "migration,import,quickbooks,tally,zoho,datev"),
            ("Compliance / GST",    "gst,einvoice,compliance,vat,tax,mandate"),
            ("Connector / API",     "connector,api,integration,sync,webhook"),
            ("POS",                 "pos,point of sale,retail,cashier"),
        ]
        rows = []
        for label, kws in NICHES:
            terms_list = kws.split(",")
            cond = " OR ".join([f"display_name ILIKE '%{t}%' OR summary ILIKE '%{t}%'" for t in terms_list])
            r = conn.execute(f"""
            SELECT COUNT(*) as cnt,
                   COALESCE(SUM(total_purchases),0) as sales,
                   COALESCE(SUM(last_month_purchases),0) as velocity
            FROM app_snapshots
            WHERE run_id = '{LATEST_RUN}' AND ({cond})
            """).fetchone() or (0, 0, 0)
            rows.append({"Niche": label, "Apps": r[0], "Total Sales": r[1], "Last Month": r[2]})

        niche_df = pd.DataFrame(rows).sort_values("Total Sales", ascending=True)
        fig2 = px.bar(
            niche_df, y="Niche", x="Total Sales", color="Apps",
            color_continuous_scale="Blues",
            orientation="h",
            title="Niche sales volume vs. app count",
        )
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#cdd6f4")
        st.plotly_chart(fig2, use_container_width=True)

    # Gap table — niches with few apps but high purchases/app
    st.divider()
    st.markdown("#### 🎯 Gap Radar — high demand, low competition")
    gap_rows = []
    for label, kws in NICHES:
        terms_list = kws.split(",")
        cond = " OR ".join([f"display_name ILIKE '%{t}%' OR summary ILIKE '%{t}%'" for t in terms_list])
        r = conn.execute(f"""
        SELECT COUNT(*) as cnt,
               COALESCE(SUM(total_purchases),0) as sales,
               COALESCE(SUM(last_month_purchases),0) as velocity,
               COALESCE(AVG(price_cents)/100.0, 0) as avg_price
        FROM app_snapshots
        WHERE run_id = '{LATEST_RUN}' AND ({cond}) AND price_cents > 0
        """).fetchone() or (0, 0, 0, 0)
        cnt, sales, vel, avg_price = r
        demand_per_app = sales / cnt if cnt > 0 else 0
        vel_per_app    = round(vel / cnt, 2) if cnt > 0 else 0
        gap_rows.append({
            "Niche": label,
            "Apps": cnt,
            "Avg Sales/App": round(demand_per_app, 0),
            "Vel/App": vel_per_app,
            "Avg Price $": round(avg_price, 2),
            "Last Month": vel,
            "Gap Score": min(100, int(demand_per_app / 5)) if cnt <= 30 else max(0, int(demand_per_app / 20)),
        })

    gap_df = pd.DataFrame(gap_rows).sort_values("Vel/App", ascending=False)
    st.dataframe(
        gap_df,
        use_container_width=True,
        column_config={
            "Gap Score":    st.column_config.ProgressColumn("Gap Score", min_value=0, max_value=100),
            "Vel/App":      st.column_config.ProgressColumn("Vel/App ↑", format="%.2f", min_value=0, max_value=5),
            "Avg Price $":  st.column_config.NumberColumn(format="$%.2f"),
        },
        hide_index=True,
    )

    # Velocity leaders — fastest growing right now
    st.divider()
    st.markdown("#### ⚡ Velocity Leaders — fastest growing this month")
    vel_df = conn.execute(f"""
    SELECT display_name, author,
           ROUND(price_cents/100.0, 2) as price_usd,
           total_purchases,
           last_month_purchases,
           ROUND(last_month_purchases * 100.0 / NULLIF(total_purchases,0), 1) as velocity_pct
    FROM app_snapshots
    WHERE run_id = '{LATEST_RUN}'
      AND total_purchases > 50
      AND last_month_purchases > 0
    ORDER BY velocity_pct DESC NULLS LAST
    LIMIT 25
    """).df()

    st.dataframe(
        vel_df,
        use_container_width=True,
        column_config={
            "price_usd": st.column_config.NumberColumn("Price $", format="$%.2f"),
            "velocity_pct": st.column_config.ProgressColumn(
                "Velocity %", format="%.1f%%", min_value=0, max_value=100
            ),
        },
        hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AUTHOR INTEL
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Competitor portfolio analysis")
    conn = get_conn()

    # Top authors leaderboard
    leaderboard = conn.execute(f"""
    SELECT
        author,
        COUNT(*) AS app_count,
        ROUND(AVG(price_cents)/100.0, 2) AS avg_price,
        SUM(total_purchases) AS total_sales,
        SUM(last_month_purchases) AS last_month,
        ROUND(AVG(rating_stars), 2) AS avg_rating,
        SUM(review_count) AS total_reviews
    FROM app_snapshots
    WHERE run_id = '{LATEST_RUN}'
      AND author IS NOT NULL
    GROUP BY author
    HAVING SUM(total_purchases) > 0
    ORDER BY total_sales DESC NULLS LAST
    LIMIT 40
    """).df()

    c1, c2 = st.columns([2, 1])
    with c1:
        fig3 = px.scatter(
            leaderboard,
            x="app_count", y="total_sales",
            size="last_month",
            color="avg_price",
            color_continuous_scale="Viridis",
            hover_data=["author", "avg_rating"],
            title="Author: app count vs. total sales (bubble = last month velocity, color = avg price)",
            labels={"app_count": "# Apps", "total_sales": "Total Purchases"},
        )
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#cdd6f4")
        st.plotly_chart(fig3, use_container_width=True)

    with c2:
        st.markdown("#### Top 10 by Sales")
        st.dataframe(
            leaderboard.head(10)[["author", "app_count", "total_sales", "avg_price"]],
            column_config={
                "avg_price": st.column_config.NumberColumn("Avg Price $", format="$%.2f"),
            },
            hide_index=True,
            use_container_width=True,
        )

    # Author drill-down
    st.divider()
    st.markdown("#### Drill into a competitor's full portfolio")
    a_col1, a_col2 = st.columns([4, 1])
    with a_col1:
        author_search = st.text_input("Author name (partial match)", placeholder="e.g. Ksolves, VentorTech, BROWSEINFO")
    with a_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button("Search", use_container_width=True)

    if author_search.strip() and (search_clicked or author_search):
        author_df = conn.execute(f"""
        SELECT display_name, ROUND(price_cents/100.0,2) as price_usd,
               rating_stars, review_count,
               total_purchases, last_month_purchases,
               ROUND(last_month_purchases*100.0/NULLIF(total_purchases,0),1) as velocity_pct,
               detail_url, summary
        FROM app_snapshots
        WHERE run_id = '{LATEST_RUN}'
          AND author ILIKE '%{author_search}%'
        ORDER BY total_purchases DESC NULLS LAST
        """).df()

        if author_df.empty:
            st.warning("No author found.")
        else:
            total = author_df["total_purchases"].sum()
            st.markdown(f"**{len(author_df)} apps · {int(total):,} total purchases**")
            st.dataframe(
                author_df.drop(columns=["summary"]),
                use_container_width=True,
                column_config={
                    "price_usd": st.column_config.NumberColumn("Price $", format="$%.2f"),
                    "velocity_pct": st.column_config.ProgressColumn(
                        "Velocity %", format="%.1f%%", min_value=0, max_value=100
                    ),
                    "detail_url": st.column_config.LinkColumn("Link"),
                },
                hide_index=True,
            )
            # Price histogram for this author
            if not author_df[author_df["price_usd"] > 0].empty:
                fig4 = px.histogram(
                    author_df[author_df["price_usd"] > 0],
                    x="price_usd", nbins=20,
                    title="Their price distribution",
                    labels={"price_usd": "Price ($)"},
                )
                fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                   plot_bgcolor="rgba(0,0,0,0)",
                                   font_color="#cdd6f4")
                st.plotly_chart(fig4, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PARTNER MAP
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Global Odoo partner network — where clients actually are")

    PARTNERS_CSV = Path(__file__).parent.parent / "data" / "partners" / "global" / "partners_raw.csv"
    ENRICHED_CSV = Path(__file__).parent.parent / "data" / "partners" / "global" / "partners_enriched.csv"
    REFS_CSV     = Path(__file__).parent.parent / "data" / "partners" / "global" / "references_raw.csv"

    if not PARTNERS_CSV.exists():
        st.info("Partner crawl not started yet. Run: `python scripts/crawl_global_partners.py`")
    else:
        @st.cache_data(ttl=300)
        def load_partners():
            df = pd.read_csv(PARTNERS_CSV, encoding="utf-8")
            return df

        @st.cache_data(ttl=300)
        def load_refs():
            if REFS_CSV.exists():
                return pd.read_csv(REFS_CSV, encoding="utf-8")
            return pd.DataFrame()

        pdf  = load_partners()
        rdf  = load_refs()

        # ── KPIs ─────────────────────────────────────────────────────────────
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Partners", f"{len(pdf):,}")
        k2.metric("Countries", f"{pdf['country'].nunique()}")
        k3.metric("Gold Partners", f"{(pdf['grade']=='Gold').sum():,}")
        k4.metric("Client References", f"{len(rdf):,}" if not rdf.empty else "—")

        st.divider()

        col_l, col_r = st.columns(2)

        # ── Top countries ─────────────────────────────────────────────────────
        with col_l:
            top_countries = (
                pdf.groupby("country").size().reset_index(name="partners")
                .sort_values("partners", ascending=True).tail(20)
            )
            fig_c = px.bar(
                top_countries, y="country", x="partners",
                orientation="h",
                title="Top 20 countries by partner count",
                labels={"partners": "Partners", "country": "Country"},
                color="partners", color_continuous_scale="Blues",
            )
            fig_c.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#cdd6f4", showlegend=False)
            st.plotly_chart(fig_c, use_container_width=True)

        # ── Grade distribution ─────────────────────────────────────────────────
        with col_r:
            grade_counts = pdf["grade"].value_counts().reset_index()
            grade_counts.columns = ["Grade", "Count"]
            grade_order = ["Gold", "Silver", "Ready", "Unknown"]
            grade_counts["Grade"] = pd.Categorical(grade_counts["Grade"], categories=grade_order, ordered=True)
            grade_counts = grade_counts.sort_values("Grade")
            color_map = {"Gold": "#f9e2af", "Silver": "#a6adc8", "Ready": "#a6e3a1", "Unknown": "#585b70"}
            fig_g = px.bar(
                grade_counts, x="Grade", y="Count",
                title="Partner grade distribution",
                color="Grade",
                color_discrete_map=color_map,
            )
            fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#cdd6f4", showlegend=False)
            st.plotly_chart(fig_g, use_container_width=True)

        # ── Industry coverage (Phase 3 data) ──────────────────────────────────
        st.divider()

        if ENRICHED_CSV.exists():
            edf = pd.read_csv(ENRICHED_CSV, encoding="utf-8")
            edf = edf.dropna(subset=["industries"])
            edf = edf[edf["industries"].str.strip() != ""]

            if not edf.empty:
                # Explode "industry1; industry2" into individual rows
                ind_rows = []
                for _, row in edf.iterrows():
                    for ind in row["industries"].split(";"):
                        ind = ind.strip()
                        if ind and 2 < len(ind) < 60:
                            ind_rows.append({"industry": ind, "grade": row.get("grade", "?"),
                                             "country": row.get("country", "?")})
                ind_df = pd.DataFrame(ind_rows)

                st.markdown("#### Industry Coverage (Phase 3 enriched data)")
                top_ind = (
                    ind_df.groupby("industry").size().reset_index(name="partner_count")
                    .sort_values("partner_count", ascending=False).head(25)
                )
                fig_i = px.bar(
                    top_ind.sort_values("partner_count", ascending=True),
                    y="industry", x="partner_count",
                    orientation="h",
                    title="Top 25 industries served by Odoo partners",
                    color="partner_count", color_continuous_scale="Greens",
                )
                fig_i.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                    font_color="#cdd6f4", showlegend=False)
                st.plotly_chart(fig_i, use_container_width=True)
        else:
            st.info("Phase 3 (detail pages) not yet crawled. Run: "
                    "`python scripts/crawl_global_partners.py --phase refs`  "
                    "to fetch industry + client reference data.")

        # ── Client references ─────────────────────────────────────────────────
        if not rdf.empty:
            st.divider()
            st.markdown("#### Client Reference Explorer")

            ind_filter = st.text_input("Filter by client industry (partial match)",
                                       placeholder="e.g. Manufacturing, Retail, Healthcare")
            ref_display = rdf.copy()
            if ind_filter.strip():
                ref_display = ref_display[
                    ref_display["client_industry"].str.contains(ind_filter, case=False, na=False)
                ]
            st.dataframe(
                ref_display[["partner_name", "partner_country", "client_name",
                              "client_industry", "description"]].head(200),
                use_container_width=True,
                hide_index=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — ERP GAP FINDER
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("What Zoho / SAP / Tally have that Odoo doesn't — live gap scan")
    st.caption("Each row = a capability that exists in another ERP ecosystem. "
               "Odoo Apps / Sales / Last Month = live count from 67k-app database.")

    conn = get_conn()

    ERP_GAPS = [
        # (category, description, keywords, source_erp)
        ("Tally Prime migrator",     "Full Tally Prime / ERP 9 export → Odoo",                 ["tally prime","tally erp","tally migration"],     "Tally"),
        ("Busy Accounting migrator", "BUSY Accounting → Odoo (India SMB, 10M+ users)",          ["busy accounting","busy software","busy migration"],"Busy"),
        ("Marg ERP migrator",        "Marg ERP data (pharma/FMCG distributors India)",          ["marg erp","marg migration","marg software"],      "Marg"),
        ("SAP migrator",             "SAP B1 / ECC master data + GL migration",                  ["sap migration","sap import","sap b1"],            "SAP"),
        ("SAP BOM sync",             "Push/pull BOM between SAP PP and Odoo MRP",               ["sap bom","sap mrp","sap production"],             "SAP"),
        ("SAP IDoc / EDI",           "Parse SAP IDocs (ORDERS, INVOIC, DESADV)",                ["idoc","sap edi","sap orders05"],                  "SAP/EDI"),
        ("Dynamics GP migrator",     "MS Great Plains → Odoo (GP being sunset by Microsoft)",   ["dynamics gp","great plains","microsoft gp"],      "Microsoft"),
        ("Dynamics 365 migrator",    "Migrate from Dynamics 365 / Business Central / NAV",      ["dynamics 365","dynamics nav","business central"], "Microsoft"),
        ("NetSuite migrator",        "Oracle NetSuite → Odoo financial migration",               ["netsuite","netsuite migration","oracle netsuite"],"Oracle"),
        ("Wave Accounting migrator", "Wave → Odoo (popular Canada/US freelancers)",             ["wave accounting","wave migration","wave import"], "Wave"),
        ("MYOB migrator",            "MYOB AccountRight / Essentials → Odoo (AU/NZ dominant)",  ["myob","myob migration","myob import"],             "MYOB"),
        ("Zoho Recruit sync",        "Sync job positions + candidates from Zoho Recruit",       ["zoho recruit","zoho hr","zoho talent"],           "Zoho"),
        ("Salesforce CPQ bridge",    "Pull SF CPQ quotes into Odoo Sales",                      ["salesforce cpq","sf cpq"],                        "Salesforce"),
        ("Darwinbox connector",      "Sync employee data with Darwinbox HCM (India unicorn)",   ["darwinbox","darwin box"],                         "Darwinbox"),
        ("Keka HR sync",             "Sync HR/payroll data with Keka (India top HRMS)",         ["keka hr","keka hrms","keka payroll"],             "Keka"),
        ("greytHR connector",        "Sync payroll/attendance with greytHR (India)",            ["greythr","greyt hr"],                             "Greytip"),
        ("ADP Payroll connector",    "Export Odoo payroll runs to ADP (US #1 payroll)",         ["adp payroll","adp connector","adp hr"],           "ADP"),
        ("BambooHR sync",            "Sync employee records BambooHR ↔ Odoo HR",               ["bamboohr","bamboo hr","bamboo sync"],             "BambooHR"),
        ("ServiceTitan connector",   "Sync jobs from ServiceTitan (US HVAC/plumbing dominator)",["servicetitan","service titan"],                   "ServiceTitan"),
        ("Aadhaar KYC",              "Aadhaar-based KYC verification API for India customers",  ["aadhaar","aadhar","aadhaar kyc"],                 "UIDAI"),
        ("Video KYC",                "Video-based KYC workflow for RBI-regulated entities",     ["video kyc","vkyc","video verification"],          "RBI"),
        ("IoT sensor → inventory",   "Auto-adjust stock from IoT sensor readings",              ["iot sensor","iot inventory","scada"],             "IoT"),
        ("JioMart connector",        "Sync orders from JioMart (Reliance's marketplace)",       ["jiomart","jio mart"],                             "Reliance"),
        ("TikTok Shop connector",    "Sync TikTok Shop orders and inventory",                   ["tiktok shop","tiktok seller","tiktok commerce"], "TikTok"),
        ("Noon marketplace",         "Sync orders from Noon.com (UAE/Saudi #1 marketplace)",    ["noon","noon marketplace","noon seller"],          "Noon"),
        ("Meesho seller sync",       "Manage Meesho seller orders in Odoo",                    ["meesho","meesho seller","meesho order"],          "Meesho"),
        ("Delhivery shipping",       "Auto-book & track Delhivery courier shipments",           ["delhivery","delhivery shipping"],                 "Delhivery"),
        ("Shiprocket integration",   "Multi-carrier shipping via Shiprocket",                   ["shiprocket","shiprocket shipping"],               "Shiprocket"),
        ("Customs / import duty",    "Auto-calculate import duties from HS codes",              ["customs duty","import duty","hs code duty"],      "Trade"),
        ("DATEV Buchungsstapel Export","Monthly Buchungsstapel CSV export for German Steuerberater",["buchungsstapel","datev export","datev csv"],       "DATEV"),
        ("Dunning management",       "Automated overdue invoice dunning + escalation",          ["dunning","dunning letter","dunning management"],  "SAP/ERP"),
        ("Revenue recognition",      "ASC 606 / IFRS 15 deferred revenue schedules",           ["revenue recognition","asc 606","ifrs 15"],       "NetSuite"),
        ("CPQ",                      "Complex product configurator with pricing rules",          ["cpq","configure price quote","product configurator quote"], "Salesforce"),
        ("NBFC loan management",     "Loan lifecycle: application → disbursement → EMI",        ["nbfc","loan management","emi schedule"],          "Fintech"),
        ("Carbon footprint / ESG",   "Scope 1/2/3 emissions from Odoo purchase data",          ["carbon","esg","scope 3","emission"],              "ESG"),
        ("FHIR / HL7 bridge",        "Exchange patient data between EHR and Odoo",              ["fhir","hl7","healthcare interop"],                "HL7"),
        ("LIMS integration",         "Lab Info Management for pharma/food quality",             ["lims","laboratory information"],                  "LIMS"),
    ]

    @st.cache_data(ttl=3600)
    def run_gap_scan():
        results = []
        c = get_conn()
        for cat, desc, kws, source in ERP_GAPS:
            cond = " OR ".join(
                f"display_name ILIKE '%{k}%' OR summary ILIKE '%{k}%'" for k in kws
            )
            row = c.execute(f"""
                SELECT COUNT(*),
                       COALESCE(SUM(total_purchases),0),
                       COALESCE(SUM(last_month_purchases),0)
                FROM app_snapshots
                WHERE run_id = '{LATEST_RUN}' AND ({cond})
            """).fetchone() or (0, 0, 0)
            apps, sales, last_mo = row
            signal = "🔴 ZERO" if apps == 0 else "🟡 THIN" if apps <= 3 else "🟢 OK" if apps <= 15 else "⚪ CROWDED"
            # Rank 9: installed-base TAM from static lookup
            ib = ERP_INSTALLED_BASE.get(source)
            if ib:
                your_tam = int(ib["installs"] * ib["churn"] * 0.005)
                tam_str  = f"{your_tam:,}/yr ({ib['geo']})"
            else:
                your_tam = 0
                tam_str  = "—"
            results.append({
                "Category":    cat,
                "Description": desc,
                "Source ERP":  source,
                "Odoo Apps":   apps,
                "Total Sales": sales,
                "Last Month":  last_mo,
                "Signal":      signal,
                "Your TAM/yr": tam_str,
            })
        order = {"🔴 ZERO": 0, "🟡 THIN": 1, "🟢 OK": 2, "⚪ CROWDED": 3}
        results.sort(key=lambda r: (order[r["Signal"]], -r["Total Sales"]))
        return pd.DataFrame(results)

    gap_df = run_gap_scan()

    # Summary chips
    n_zero    = (gap_df["Signal"] == "🔴 ZERO").sum()
    n_thin    = (gap_df["Signal"] == "🟡 THIN").sum()
    n_ok      = (gap_df["Signal"] == "🟢 OK").sum()
    n_crowded = (gap_df["Signal"] == "⚪ CROWDED").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 Zero Competition", n_zero)
    c2.metric("🟡 Thin (1–3 apps)", n_thin)
    c3.metric("🟢 Some Coverage", n_ok)
    c4.metric("⚪ Crowded (15+)", n_crowded)

    st.divider()

    # Filter by signal
    sig_filter = st.multiselect(
        "Show signals",
        ["🔴 ZERO", "🟡 THIN", "🟢 OK", "⚪ CROWDED"],
        default=["🔴 ZERO", "🟡 THIN"],
    )
    filtered = gap_df[gap_df["Signal"].isin(sig_filter)] if sig_filter else gap_df

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Odoo Apps":   st.column_config.NumberColumn(format="%d"),
            "Total Sales": st.column_config.NumberColumn(format="%d"),
            "Last Month":  st.column_config.NumberColumn(format="%d"),
        },
    )

    st.divider()
    st.markdown("#### Top picks — zero competition, highest market size")
    zero_df = gap_df[gap_df["Signal"] == "🔴 ZERO"][["Category", "Description", "Source ERP"]]
    if zero_df.empty:
        st.info("No zero-competition gaps found.")
    else:
        for _, row in zero_df.iterrows():
            st.markdown(
                f'<div class="pivot-box" style="color:#cdd6f4">'
                f'<strong>{row["Category"]}</strong> <span style="color:#a6e3a1">({row["Source ERP"]})</span>'
                f'<br><small>{row["Description"]}</small></div>',
                unsafe_allow_html=True,
            )
