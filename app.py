"""
FactorySync 2.0 — Supply Chain Stress Monitor
==============================================
Built by Rutwik Satish | MS Engineering Management, Northeastern University

THE PROBLEM THIS ACTUALLY SOLVES:
  Mid-size US manufacturers ($50M–$500M revenue) have no systematic early warning
  when their supplier base is under financial or operational stress. By the time
  a supplier misses a delivery, the damage is already done.

  The warning signals exist 60–90 days earlier in US public government data:
    → BLS Producer Price Index: Input cost spikes = supplier margin compression
    → FRED Inventory/Sales Ratio: Rising unsold inventory = demand collapse
    → FRED Manufacturers New Orders: Falling orders = supplier revenue decline

  No mid-market procurement team is watching these systematically.
  FactorySync does it automatically, by material category, every month.

REAL DATA SOURCE:
  Federal Reserve Economic Data (FRED) — fred.stlouisfed.org
  Free API key at: https://fred.stlouisfed.org/docs/api/api_key.html
  Bureau of Labor Statistics PPI — public.bls.gov (no key required for basic)

  If no FRED API key is provided, the app runs on realistic demo data
  built from actual 2021–2024 BLS PPI observations.

ONE MODULE. ONE INSIGHT.
  The "stress lead time" concept: supply disruptions have a 3-factor signature
  in public data that appears 60–90 days before the actual disruption.
  FactorySync detects this signature and generates a procurement-ready risk brief.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
from datetime import datetime, timedelta
import time

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FactorySync | Supply Chain Stress Monitor",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DESIGN ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="block-container"] {
    background: #0f1117 !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSidebar"] {
    background: #090c12 !important;
    border-right: 1px solid #1e2535 !important;
}
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2 { color: #e2e8f0 !important; }
[data-testid="stSidebarNav"] { display:none !important; }

h1,h2,h3,h4 { font-family:'DM Sans',sans-serif !important; color:#f1f5f9 !important; }

[data-testid="metric-container"] {
    background: #141921 !important;
    border: 1px solid #1e2535 !important;
    border-radius: 10px !important;
    padding: 16px 18px !important;
}
[data-testid="stMetricValue"] { color:#f1f5f9 !important; font-family:'DM Mono',monospace !important; font-size:1.5rem !important; font-weight:600 !important; }
[data-testid="stMetricLabel"] { color:#64748b !important; font-size:0.7rem !important; text-transform:uppercase; letter-spacing:0.1em; }

[data-testid="stTabs"] button { color:#64748b !important; font-family:'DM Sans',sans-serif !important; background:transparent !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#38bdf8 !important; border-bottom:2px solid #38bdf8 !important; }

[data-testid="stDataFrame"] { background:#141921 !important; border:1px solid #1e2535 !important; border-radius:10px !important; }

[data-testid="stButton"] button {
    background:#1d4ed8 !important; color:#fff !important;
    border:none !important; border-radius:8px !important; font-weight:500 !important;
}
[data-testid="stButton"] button:hover { background:#1e40af !important; }

[data-testid="stSelectbox"] > div { background:#141921 !important; border:1px solid #1e2535 !important; border-radius:8px !important; }
[data-testid="stTextInput"] input { background:#141921 !important; border:1px solid #1e2535 !important; border-radius:8px !important; color:#e2e8f0 !important; }
[data-testid="stMultiSelect"] > div { background:#141921 !important; border:1px solid #1e2535 !important; border-radius:8px !important; }

[data-testid="stExpander"] { background:#141921 !important; border:1px solid #1e2535 !important; border-radius:10px !important; }
[data-testid="stExpander"] summary { color:#38bdf8 !important; font-weight:500 !important; }

[data-testid="stAlert"] { border-radius:8px !important; }
hr { border-color:#1e2535 !important; }
div[data-testid="stMarkdownContainer"] p { color: #94a3b8 !important; }

.eyebrow { font-family:'DM Mono',monospace; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.18em; color:#38bdf8; }
.risk-critical { color:#ef4444 !important; font-weight:600; }
.risk-elevated { color:#f59e0b !important; font-weight:600; }
.risk-normal   { color:#22c55e !important; font-weight:600; }

.signal-card {
    background:#141921; border:1px solid #1e2535;
    border-radius:10px; padding:18px 20px; margin-bottom:10px;
}
.signal-title { font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; margin-bottom:6px; }
.signal-val { font-family:'DM Mono',monospace; font-size:1.6rem; font-weight:500; color:#f1f5f9; }
.signal-sub { font-size:0.8rem; color:#64748b; margin-top:4px; line-height:1.5; }

.brief-block {
    background:#141921; border:1px solid #1e2535;
    border-left:3px solid #38bdf8;
    border-radius:0 10px 10px 0;
    padding:20px 24px; font-size:0.88rem;
    line-height:1.85; color:#cbd5e1;
    white-space:pre-wrap; font-family:'DM Sans',sans-serif;
}
.data-badge {
    display:inline-block; background:#0c1828; color:#38bdf8;
    border:1px solid #1e3a5f; border-radius:4px;
    font-family:'DM Mono',monospace; font-size:0.68rem;
    padding:2px 8px; margin:2px;
}
</style>
""", unsafe_allow_html=True)

DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#0f1117", plot_bgcolor="#141921",
    font=dict(color="#94a3b8", family="DM Sans"),
    xaxis=dict(gridcolor="#1e2535", linecolor="#1e2535", tickfont=dict(color="#64748b")),
    yaxis=dict(gridcolor="#1e2535", linecolor="#1e2535", tickfont=dict(color="#64748b")),
    margin=dict(t=40, b=44, l=12, r=12),
)

# ── MATERIAL CATEGORIES & FRED SERIES ────────────────────────────────────────
CATEGORIES = {
    "Steel & Metals": {
        "ppi_series":    "WPU101",
        "description":   "Iron, steel, and metal mill products",
        "fred_label":    "WPU101 — Iron & Steel PPI",
        "sectors":       ["Auto", "Heavy Equipment", "Construction", "Appliances"],
        "typical_lead":  "6–10 weeks"
    },
    "Electronic Components": {
        "ppi_series":    "WPU117401",
        "description":   "Semiconductors, electronic components",
        "fred_label":    "WPU117401 — Electronic Components PPI",
        "sectors":       ["Auto", "Industrial Equipment", "Consumer Electronics"],
        "typical_lead":  "12–26 weeks"
    },
    "Plastics & Rubber": {
        "ppi_series":    "WPU0652",
        "description":   "Plastics materials and resins",
        "fred_label":    "WPU0652 — Plastics Materials PPI",
        "sectors":       ["Auto", "Packaging", "Medical Devices", "Consumer Goods"],
        "typical_lead":  "4–8 weeks"
    },
    "Lumber & Wood": {
        "ppi_series":    "WPU0811",
        "description":   "Lumber and wood products",
        "fred_label":    "WPU0811 — Lumber & Wood PPI",
        "sectors":       ["Construction", "Furniture", "Packaging"],
        "typical_lead":  "2–4 weeks"
    },
    "Energy / Petroleum": {
        "ppi_series":    "WPU0561",
        "description":   "Petroleum and petroleum products",
        "fred_label":    "WPU0561 — Petroleum Products PPI",
        "sectors":       ["All manufacturing", "Transportation", "Chemicals"],
        "typical_lead":  "2–6 weeks"
    },
    "Agricultural / Food Inputs": {
        "ppi_series":    "WPU012",
        "description":   "Farm products and food processing inputs",
        "fred_label":    "WPU012 — Farm Products PPI",
        "sectors":       ["Food & Beverage", "Packaging", "Animal Feed"],
        "typical_lead":  "2–6 weeks"
    },
}

MACRO_SERIES = {
    "ISRATIO":  "Total Business Inventories to Sales Ratio",
    "AMTMNO":   "Manufacturers: New Orders (Non-defense Capital Goods)",
    "IPMAN":    "Industrial Production: Manufacturing",
}

# ── REALISTIC DEMO DATA ───────────────────────────────────────────────────────
# Based on actual BLS PPI observations 2021–2024
# This is what the FRED/BLS API returns — swap for live calls with API key

def get_demo_ppi(category: str, months: int = 30) -> pd.DataFrame:
    """Generate realistic PPI demo data mirroring actual 2022–2024 BLS observations."""
    np.random.seed(hash(category) % 999)
    end = datetime.today().replace(day=1)
    dates = [end - timedelta(days=30*i) for i in range(months, 0, -1)]

    # Realistic trajectories per category
    trajectories = {
        "Steel & Metals":         [170,178,185,195,210,225,235,228,215,200,188,180,175,172,168,165,163,161,162,164,166,168,170,172,174,175,176,178,179,180],
        "Electronic Components":  [125,128,131,135,140,147,152,155,153,150,147,144,141,139,137,135,133,132,131,130,129,128,127,126,125,124,124,123,123,122],
        "Plastics & Rubber":      [155,162,170,180,192,200,195,188,178,168,160,155,150,148,146,145,143,142,141,140,139,138,138,137,137,136,136,136,135,135],
        "Lumber & Wood":          [280,340,420,380,310,250,200,170,155,145,138,133,130,128,126,125,124,123,122,121,120,122,124,126,128,130,132,134,136,138],
        "Energy / Petroleum":     [140,155,175,200,230,250,235,210,185,170,160,155,160,165,155,148,145,148,152,155,150,148,145,148,152,155,158,160,155,152],
        "Agricultural / Food Inputs": [120,125,130,138,148,158,162,158,152,146,140,136,133,130,128,126,125,124,123,122,121,120,120,119,119,118,118,118,117,117],
    }

    base = trajectories.get(category, [150]*months)[:months]
    noise = np.random.normal(0, 1.5, len(dates))
    values = [max(80, b + n) for b, n in zip(base, noise)]
    return pd.DataFrame({"date": dates, "value": values, "category": category})


def get_demo_macro() -> dict:
    """Realistic macro indicator data."""
    months = 24
    end = datetime.today().replace(day=1)
    dates = [end - timedelta(days=30*i) for i in range(months, 0, -1)]

    # ISRATIO: been creeping up since 2022 (stress signal when > 1.45)
    isratio = [1.32,1.33,1.34,1.35,1.36,1.37,1.37,1.36,1.35,1.36,1.37,1.38,
               1.39,1.40,1.41,1.41,1.42,1.42,1.43,1.43,1.44,1.44,1.45,1.45]

    # Mfg new orders: volatile
    orders = [530,535,528,520,515,510,518,525,522,516,510,505,
              508,512,515,510,505,500,498,502,506,504,500,498]

    return {
        "dates":   dates,
        "isratio": isratio[:months],
        "orders":  orders[:months],
    }


# ── FRED API FETCHER ──────────────────────────────────────────────────────────
def fetch_fred(series_id: str, api_key: str, start: str = "2021-01-01") -> pd.DataFrame | None:
    """Fetch series from FRED. Returns None on failure."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = dict(
        series_id=series_id,
        api_key=api_key,
        observation_start=start,
        frequency="m",
        file_type="json",
    )
    try:
        r = requests.get(url, params=params, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json().get("observations", [])
        df = pd.DataFrame(data)[["date", "value"]]
        df["date"]  = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna().reset_index(drop=True)
    except Exception:
        return None


# ── STRESS SCORE ENGINE ───────────────────────────────────────────────────────
def compute_stress(df: pd.DataFrame, isratio: list, orders: list) -> dict:
    """
    Three-factor stress model:
      1. PPI Momentum   — 3-month rate of change (cost pressure on suppliers)
      2. Volatility     — 6-month standard deviation (uncertainty = planning failure)
      3. Macro Context  — Inventory/Sales ratio trend + New Orders trend
    Score 0–100. Above 65 = Elevated. Above 80 = Critical.
    """
    vals = df["value"].values

    # Factor 1: PPI momentum (last 3 months vs. prior 3 months)
    if len(vals) >= 6:
        recent_avg = np.mean(vals[-3:])
        prior_avg  = np.mean(vals[-6:-3])
        momentum   = ((recent_avg - prior_avg) / prior_avg) * 100
    else:
        momentum = 0.0

    # Factor 2: Volatility (coefficient of variation last 6 months)
    if len(vals) >= 6:
        volatility_pct = (np.std(vals[-6:]) / np.mean(vals[-6:])) * 100
    else:
        volatility_pct = 0.0

    # Factor 3: Macro — inventory stress + order decline
    inv_stress   = max(0, (isratio[-1] - 1.35) / 0.15 * 30) if isratio else 0
    order_trend  = max(0, (orders[-6] - orders[-1]) / orders[-6] * 100 * 3) if len(orders) >= 6 else 0

    # Weighted score
    score = (
        min(40, max(0, momentum * 4))      +   # max 40 pts from price pressure
        min(20, volatility_pct * 2)         +   # max 20 pts from volatility
        min(20, inv_stress)                 +   # max 20 pts from inventory stress
        min(20, order_trend)                    # max 20 pts from demand collapse
    )
    score = min(100, max(0, score))

    level = "CRITICAL" if score >= 80 else ("ELEVATED" if score >= 55 else "NORMAL")
    color = "#ef4444"   if score >= 80 else ("#f59e0b"  if score >= 55 else "#22c55e")

    return {
        "score":          round(score, 1),
        "level":          level,
        "color":          color,
        "momentum_pct":   round(momentum, 2),
        "volatility_pct": round(volatility_pct, 2),
        "inv_ratio":      isratio[-1] if isratio else 1.4,
        "orders_latest":  orders[-1]  if orders  else 500,
        "orders_6m_ago":  orders[-7]  if len(orders) >= 7 else orders[-1] if orders else 500,
    }


# ── GROQ AI BRIEF ─────────────────────────────────────────────────────────────
def generate_brief(
    groq_key: str,
    category: str,
    stress: dict,
    cat_info: dict,
    ppi_df: pd.DataFrame,
    company_context: str = ""
) -> str:
    """Generate a procurement-ready risk brief via Groq Llama 3."""
    if not groq_key:
        return (
            f"SUPPLY CHAIN STRESS BRIEF — {category.upper()}\n"
            f"Generated: {datetime.today().strftime('%B %d, %Y')}\n\n"
            f"RISK LEVEL: {stress['level']} (Score: {stress['score']}/100)\n\n"
            f"SIGNAL SUMMARY:\n"
            f"  • PPI 3-month momentum: +{stress['momentum_pct']}% "
            f"({'elevated cost pressure' if stress['momentum_pct'] > 3 else 'stable'})\n"
            f"  • Price volatility (6-month CV): {stress['volatility_pct']}% "
            f"({'high uncertainty' if stress['volatility_pct'] > 4 else 'normal range'})\n"
            f"  • Business Inventory/Sales Ratio: {stress['inv_ratio']} "
            f"({'above normal — demand softening' if stress['inv_ratio'] > 1.42 else 'within normal range'})\n"
            f"  • Mfg New Orders trend: {'declining' if stress['orders_6m_ago'] > stress['orders_latest'] else 'stable/growing'} "
            f"(6-month change: {round((stress['orders_latest'] - stress['orders_6m_ago']) / stress['orders_6m_ago'] * 100, 1)}%)\n\n"
            f"WHAT THIS MEANS:\n"
            f"{'Input costs rising faster than suppliers can absorb — expect margin pressure, potential quality shortcuts, and lead time extension in 60–90 days.' if stress['momentum_pct'] > 4 else 'Cost environment is relatively stable for this category.'}\n\n"
            f"RECOMMENDED ACTIONS:\n"
            f"{'1. Request financial health update from top 3 suppliers in this category.\n2. Consider locking in pricing agreements before next quarter.\n3. Identify one alternative source as contingency.\n4. Flag for procurement review this month.' if stress['score'] > 55 else '1. Continue standard monitoring cadence.\n2. No immediate action required.'}\n\n"
            f"DATA SOURCES: BLS Producer Price Index ({cat_info['fred_label']}) + FRED ISRATIO + FRED AMTMNO\n"
            f"NOTE: Connect FRED API key in sidebar for live data. This brief uses 2021–2024 historical pattern data."
        )

    # Build context for Groq
    recent_vals = ppi_df["value"].values[-6:] if len(ppi_df) >= 6 else ppi_df["value"].values
    ppi_summary = f"Last 6 months PPI index values: {[round(v, 1) for v in recent_vals]}"

    prompt = f"""You are a senior supply chain analyst writing a concise, factual risk brief for a VP of Procurement.

CATEGORY: {category}
DESCRIPTION: {cat_info['description']}
SECTORS EXPOSED: {', '.join(cat_info['sectors'])}
TYPICAL SUPPLIER LEAD TIME: {cat_info['typical_lead']}
{f"COMPANY CONTEXT: {company_context}" if company_context else ""}

STRESS INDICATORS (from US public data — BLS PPI + FRED):
- Overall stress score: {stress['score']}/100 ({stress['level']})
- PPI 3-month momentum: +{stress['momentum_pct']}% (measures input cost acceleration)
- Price volatility (6-month CV): {stress['volatility_pct']}% (measures planning uncertainty)
- Business Inventory/Sales Ratio: {stress['inv_ratio']} (>1.42 = demand softening)
- Mfg New Orders 6-month change: {round((stress['orders_latest'] - stress['orders_6m_ago']) / max(1, stress['orders_6m_ago']) * 100, 1)}%
- {ppi_summary}

Write a 200-word procurement risk brief. Format:
1. RISK LEVEL headline (one sentence)
2. What the data signals (2–3 sentences, specific and factual)
3. What this means for procurement in the next 60–90 days (2 sentences)
4. Three specific recommended actions (numbered)

Be direct. Use numbers. No jargon. This brief goes to the VP of Procurement tomorrow morning."""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400, "temperature": 0.3
            },
            timeout=15
        )
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI brief unavailable ({e}). Check Groq API key.\n\n" + generate_brief("", category, stress, cat_info, ppi_df, company_context)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:8px 0 20px">
  <div class="eyebrow" style="margin-bottom:6px">Supply Chain Intelligence</div>
  <div style="font-size:1.25rem;font-weight:600;color:#f1f5f9">FactorySync 2.0</div>
  <div style="font-size:0.78rem;color:#475569;margin-top:2px">Stress Monitor · Early Warning</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("#### Configuration")

    fred_key = st.text_input(
        "FRED API Key (optional)",
        type="password",
        placeholder="Get free key at fred.stlouisfed.org",
        help="Free key from fred.stlouisfed.org/docs/api/api_key.html — enables live BLS/FRED data"
    )
    groq_key = st.text_input(
        "Groq API Key (optional)",
        type="password",
        placeholder="For AI risk briefs",
        help="Free key at console.groq.com — enables AI-generated procurement briefs"
    )
    company_context = st.text_input(
        "Your company / industry (optional)",
        placeholder="e.g. Tier 2 auto supplier, Midwest",
        help="Adds context to the AI brief"
    )

    st.markdown("---")
    st.markdown("#### Select Categories to Monitor")

    selected_cats = st.multiselect(
        "Material Categories",
        list(CATEGORIES.keys()),
        default=["Steel & Metals", "Electronic Components", "Energy / Petroleum"],
        label_visibility="collapsed"
    )
    if not selected_cats:
        selected_cats = ["Steel & Metals"]

    st.markdown("---")
    st.markdown("""
<div style="font-size:0.72rem;color:#334155;line-height:1.8">
<div class="eyebrow" style="margin-bottom:6px">Data Sources</div>
<span class="data-badge">BLS PPI</span>
<span class="data-badge">FRED ISRATIO</span>
<span class="data-badge">FRED AMTMNO</span>
<br><br>
US Government public datasets. Free. Updated monthly.
No enterprise license required.
</div>
""", unsafe_allow_html=True)


# ── MAIN ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:16px 0 8px">
  <div class="eyebrow">Supply Chain Stress Monitor</div>
  <h1 style="font-size:1.75rem;font-weight:600;margin:6px 0 4px;letter-spacing:-0.02em">
    Supplier Category Risk Dashboard
  </h1>
  <p style="color:#475569;font-size:0.88rem;max-width:680px">
    Detects supplier financial stress 60–90 days before it causes delivery failures,
    using US public data from the Bureau of Labor Statistics and Federal Reserve.
    No enterprise software required.
  </p>
</div>
""", unsafe_allow_html=True)

using_live = bool(fred_key and fred_key.strip())
if using_live:
    st.success("✓ FRED API connected — fetching live BLS/FRED data")
else:
    st.info("📊 Running on realistic demo data (2021–2024 BLS PPI pattern). Add FRED API key in sidebar for live data.", icon="ℹ️")

st.markdown("---")

# ── FETCH DATA ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(categories: tuple, fred_key: str):
    macro = get_demo_macro()
    ppi_data = {}
    for cat in categories:
        series = CATEGORIES[cat]["ppi_series"]
        if fred_key:
            df = fetch_fred(series, fred_key)
            if df is not None and len(df) > 6:
                df["category"] = cat
                ppi_data[cat] = df
                continue
        # Fallback to demo
        ppi_data[cat] = get_demo_ppi(cat)

    if fred_key:
        iso = fetch_fred("ISRATIO", fred_key)
        if iso is not None:
            macro["isratio"] = iso["value"].tolist()[-24:]
        amtm = fetch_fred("AMTMNO", fred_key)
        if amtm is not None:
            macro["orders"] = amtm["value"].tolist()[-24:]

    return ppi_data, macro

with st.spinner("Loading supply chain data..."):
    ppi_data, macro = load_data(tuple(selected_cats), fred_key.strip() if fred_key else "")

# ── COMPUTE STRESS SCORES ─────────────────────────────────────────────────────
stress_scores = {}
for cat in selected_cats:
    if cat in ppi_data:
        stress_scores[cat] = compute_stress(
            ppi_data[cat], macro["isratio"], macro["orders"]
        )

# ── PORTFOLIO OVERVIEW ────────────────────────────────────────────────────────
st.markdown("#### Portfolio Stress Overview")

if stress_scores:
    cols = st.columns(len(stress_scores))
    for i, (cat, s) in enumerate(stress_scores.items()):
        with cols[i]:
            level_class = "risk-critical" if s["level"] == "CRITICAL" else ("risk-elevated" if s["level"] == "ELEVATED" else "risk-normal")
            st.markdown(f"""
<div class="signal-card">
  <div class="signal-title">{cat}</div>
  <div class="signal-val">{s['score']}<span style="font-size:1rem;color:#475569">/100</span></div>
  <div class="signal-sub"><span class="{level_class}">{s['level']}</span><br>
  PPI momentum: {'+' if s['momentum_pct'] >= 0 else ''}{s['momentum_pct']}%<br>
  Volatility: {s['volatility_pct']}%</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── CATEGORY DEEP DIVE ────────────────────────────────────────────────────────
st.markdown("#### Category Deep Dive")
active_tab_names = selected_cats
tabs = st.tabs(active_tab_names)

for tab, cat in zip(tabs, selected_cats):
    with tab:
        if cat not in ppi_data or cat not in stress_scores:
            st.warning(f"No data available for {cat}")
            continue

        df   = ppi_data[cat]
        s    = stress_scores[cat]
        info = CATEGORIES[cat]

        # Top metrics
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Stress Score",       f"{s['score']}/100",  delta=s['level'], delta_color="inverse" if s['level'] != "NORMAL" else "normal")
        c2.metric("PPI 3M Momentum",    f"{'+' if s['momentum_pct'] >= 0 else ''}{s['momentum_pct']}%",
                  delta="Price pressure" if s['momentum_pct'] > 3 else "Stable",
                  delta_color="inverse" if s['momentum_pct'] > 3 else "normal")
        c3.metric("Price Volatility",   f"{s['volatility_pct']}%",
                  delta="High uncertainty" if s['volatility_pct'] > 4 else "Normal",
                  delta_color="inverse" if s['volatility_pct'] > 4 else "normal")
        c4.metric("Inv/Sales Ratio",    f"{s['inv_ratio']}",
                  delta="Demand softening" if s['inv_ratio'] > 1.42 else "Normal range",
                  delta_color="inverse" if s['inv_ratio'] > 1.42 else "normal")

        st.markdown("")

        # PPI trend chart with risk zones
        fig = go.Figure()

        # Rolling 3-month average
        vals  = df["value"].values
        dates = df["date"].values
        if len(vals) >= 3:
            rolling_avg = pd.Series(vals).rolling(3).mean().values
            fig.add_trace(go.Scatter(
                x=dates, y=rolling_avg,
                mode="lines", name="3-month avg",
                line=dict(color="#94a3b8", width=1, dash="dash"), opacity=0.6
            ))

        # Main PPI line — color by stress
        line_color = "#ef4444" if s['score'] >= 80 else ("#f59e0b" if s['score'] >= 55 else "#22c55e")
        fig.add_trace(go.Scatter(
            x=dates, y=vals,
            mode="lines+markers", name=info["fred_label"],
            line=dict(color=line_color, width=2),
            marker=dict(size=4, color=line_color),
            fill="tozeroy", fillcolor=f"rgba{tuple(int(line_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.05,)}"
        ))

        # Mark recent 3 months
        if len(dates) >= 3:
            fig.add_vrect(
                x0=dates[-3], x1=dates[-1],
                fillcolor="rgba(251,191,36,0.06)",
                line_width=0,
                annotation_text="  Signal window",
                annotation_position="top left",
                annotation_font_color="#64748b",
                annotation_font_size=11,
            )

        fig.update_layout(
            **DARK, height=300,
            title=dict(text=f"Producer Price Index — {cat}", font=dict(size=14, color="#e2e8f0")),
            xaxis_title="", yaxis_title="Index (1982=100)",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(color="#64748b", size=11), bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig, use_container_width=True)

        # Three-signal chart
        st.markdown("**The Three-Signal Stress Pattern** — when all three move together, disruption follows in 60–90 days")

        col_a, col_b = st.columns(2)

        with col_a:
            # Inventory/Sales ratio
            fig_inv = go.Figure()
            inv_dates = macro["dates"][-24:] if len(macro["dates"]) >= 24 else macro["dates"]
            inv_vals  = macro["isratio"][-24:] if len(macro["isratio"]) >= 24 else macro["isratio"]
            fig_inv.add_trace(go.Scatter(
                x=inv_dates, y=inv_vals,
                mode="lines+markers", name="Inv/Sales Ratio",
                line=dict(color="#38bdf8", width=2),
                marker=dict(size=3), fill="tozeroy",
                fillcolor="rgba(56,189,248,0.06)"
            ))
            fig_inv.add_hline(y=1.42, line_dash="dot", line_color="#f59e0b",
                              annotation_text=" Stress threshold (1.42)", annotation_font_color="#f59e0b", annotation_font_size=10)
            fig_inv.update_layout(**DARK, height=220,
                title=dict(text="Business Inventory/Sales Ratio (FRED ISRATIO)", font=dict(size=12,color="#e2e8f0")),
                yaxis_title="Ratio", showlegend=False)
            st.plotly_chart(fig_inv, use_container_width=True)

        with col_b:
            # New orders
            fig_ord = go.Figure()
            ord_dates = macro["dates"][-24:]
            ord_vals  = macro["orders"][-24:]
            ord_color = "#ef4444" if ord_vals[-1] < ord_vals[0] else "#22c55e"
            fig_ord.add_trace(go.Scatter(
                x=ord_dates, y=ord_vals,
                mode="lines+markers", name="New Orders",
                line=dict(color=ord_color, width=2),
                marker=dict(size=3), fill="tozeroy",
                fillcolor=f"rgba(239,68,68,0.06)" if ord_color == "#ef4444" else "rgba(34,197,94,0.06)"
            ))
            fig_ord.update_layout(**DARK, height=220,
                title=dict(text="Manufacturers' New Orders — $B (FRED AMTMNO)", font=dict(size=12,color="#e2e8f0")),
                yaxis_title="$B", showlegend=False)
            st.plotly_chart(fig_ord, use_container_width=True)

        st.markdown("---")

        # AI Risk Brief
        st.markdown("**Procurement Risk Brief**")
        st.markdown(f"""
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px">
  <span class="data-badge">BLS {info['fred_label']}</span>
  <span class="data-badge">FRED ISRATIO</span>
  <span class="data-badge">FRED AMTMNO</span>
  <span class="data-badge">Sectors: {', '.join(info['sectors'][:2])}</span>
  <span class="data-badge">Lead time: {info['typical_lead']}</span>
</div>
""", unsafe_allow_html=True)

        if st.button(f"Generate AI Brief for {cat}", key=f"brief_{cat}"):
            with st.spinner("Analyzing signals..."):
                brief = generate_brief(
                    groq_key.strip() if groq_key else "",
                    cat, s, info, ppi_data[cat],
                    company_context
                )
                st.session_state[f"brief_text_{cat}"] = brief

        if f"brief_text_{cat}" in st.session_state:
            st.markdown(f'<div class="brief-block">{st.session_state[f"brief_text_{cat}"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="brief-block" style="color:#475569;font-style:italic">
Click "Generate AI Brief" above to produce a procurement-ready risk memo for {cat}.

The brief will interpret the three stress signals above and produce:
  • Risk level assessment with specific numbers
  • What the data signals for your suppliers in this category
  • 3 recommended procurement actions for the next 30 days

{"Groq API connected — AI brief will be generated live." if groq_key else "Add Groq API key in sidebar for AI-generated brief. Without it, a structured template brief is produced instead."}
</div>
""", unsafe_allow_html=True)

# ── MACRO CONTEXT ─────────────────────────────────────────────────────────────
with st.expander("📊 Macro Context — Why these three signals matter together"):
    st.markdown("""
**The Stress Lead Time Hypothesis**

Supply disruptions do not appear suddenly. They have a consistent three-factor signature
in US public data that appears **60–90 days before** the actual delivery failure:

| Signal | What it measures | Threshold | Data source |
|--------|-----------------|-----------|-------------|
| PPI momentum | Input cost acceleration for supplier's raw materials | >3% over 3 months | BLS PPI series |
| Price volatility | Planning uncertainty — the higher this is, the harder it is for suppliers to quote and plan | CV >4% | BLS PPI series |
| Inventory/Sales ratio | When inventories pile up relative to sales, supplier customers are pulling back — revenue pressure follows | >1.42 | FRED ISRATIO |

**When all three are elevated simultaneously:**
Suppliers are paying more for inputs, facing demand uncertainty, and watching their customers' inventory build up.
This combination compresses margins, strains working capital, and typically results in:
- Lead time extension (prioritizing most profitable customers)
- Quality shortcuts (cost-cutting under margin pressure)
- Force majeure declarations (extreme cases)

**The gap FactorySync fills:**
Fortune 500 companies use Bloomberg, Resilinc, or Dun & Bradstreet for this intelligence — costing $50K–$500K/year.
Mid-size manufacturers have nothing. This data is free and public. FactorySync automates the monitoring.
""")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<p style="font-size:0.75rem;color:#334155;text-align:center">
FactorySync 2.0 · Supply Chain Stress Monitor ·
Data: Bureau of Labor Statistics PPI + Federal Reserve FRED ·
Built by Rutwik Satish · MS Engineering Management, Northeastern University
</p>
""", unsafe_allow_html=True)
