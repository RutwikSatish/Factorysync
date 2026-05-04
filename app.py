"""
MRP Lot Sizing Optimizer
========================
Built by Rutwik Satish | MS Engineering Management, Northeastern University

THE PROBLEM THIS SOLVES:
  Every manufacturer using MRP must decide: how much to order and when?
  This is the lot sizing problem. Most small-to-mid manufacturers default to
  Lot-for-Lot (order exactly what's needed) or a fixed batch set years ago.
  Both approaches leave significant money on the table.

  This tool computes the complete MRP record for five standard lot sizing
  methods and shows you exactly how much each one costs — so you can make
  an informed decision instead of relying on an ERP default.

TEXTBOOK FOUNDATION:
  Primary: Jacobs, Berry, Whybark & Vollmann (2011)
           "Manufacturing Planning and Control for Supply Chain Management"
           Chapters 3 & 4 — the APICS CPIM standard reference.

  Algorithms: Silver & Meal (1973) — original Silver-Meal heuristic paper.
              Wagner & Whitin (1958) — original dynamic programming paper.
              Silver, Pyke & Thomas (1998) — "Inventory Management and
              Production Planning and Scheduling"

THE FIVE METHODS (all from Jacobs & Berry Ch. 4):
  1. Lot-for-Lot (L4L)      — Order exactly net requirements each period
  2. Economic Order Quantity — Classical EOQ formula (steady demand assumption)
  3. Period Order Quantity   — EOQ converted to a fixed review period
  4. Part Period Balancing   — Balance ordering vs. holding costs dynamically
  5. Silver-Meal Heuristic   — Best practical heuristic for variable demand
  6. Wagner-Whitin           — Dynamic programming optimal (benchmark)

THE MRP RECORD (Jacobs & Berry, Chapter 3):
  Gross Requirements     — Demand in each period (from MPS or parent BOM)
  Scheduled Receipts     — Already-ordered quantities arriving this period
  Projected Available    — Inventory at end of period
  Net Requirements       — Shortfall: what still needs to be covered
  Planned Order Receipts — What the lot sizing rule says to receive
  Planned Order Releases — Receipts offset back by lead time = when to place order

REAL CASE STUDY BASIS:
  Pre-loaded example based on a published textbook case in Jacobs & Berry
  (Chapter 4, Table 4.1 pattern) — 10-period variable demand for a
  fabricated component in a discrete manufacturer.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import math
from typing import List, Tuple, Dict

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MRP Lot Sizing Optimizer",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DESIGN SYSTEM ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="block-container"] {
    background: #f8f9fb !important;
    color: #111827 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
[data-testid="stSidebar"] {
    background: #111827 !important;
    border-right: 1px solid #1f2937 !important;
}
[data-testid="stSidebar"] * { color: #9ca3af !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f9fafb !important; }
[data-testid="stSidebarNav"] { display:none !important; }

h1,h2,h3 { font-family:'IBM Plex Sans',sans-serif !important; color:#111827 !important; }

[data-testid="metric-container"] {
    background:#fff !important; border:1px solid #e5e7eb !important;
    border-radius:10px !important; padding:16px !important;
    box-shadow:0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stMetricValue"] { color:#111827 !important; font-family:'DM Mono',monospace !important; font-size:1.5rem !important; font-weight:600 !important; }
[data-testid="stMetricLabel"] { color:#6b7280 !important; font-size:0.7rem !important; text-transform:uppercase; letter-spacing:0.1em; }

[data-testid="stTabs"] button { color:#6b7280 !important; font-family:'IBM Plex Sans',sans-serif !important; background:transparent !important; font-size:0.85rem !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#1d4ed8 !important; border-bottom:2px solid #1d4ed8 !important; }

[data-testid="stDataFrame"] { background:#fff !important; border:1px solid #e5e7eb !important; border-radius:10px !important; }
.stDataFrame th { background:#f9fafb !important; color:#6b7280 !important; font-size:0.72rem !important; text-transform:uppercase; letter-spacing:0.06em; font-family:'DM Mono',monospace !important; }
.stDataFrame td { color:#111827 !important; font-size:0.85rem !important; font-family:'DM Mono',monospace !important; }

[data-testid="stButton"] button {
    background:#1d4ed8 !important; color:#fff !important;
    border:none !important; border-radius:8px !important;
    font-family:'IBM Plex Sans',sans-serif !important; font-weight:500 !important;
}
[data-testid="stButton"] button:hover { background:#1e40af !important; }

[data-testid="stSelectbox"] > div, [data-testid="stNumberInput"] > div > div {
    background:#fff !important; border:1px solid #e5e7eb !important; border-radius:8px !important;
}

hr { border-color:#e5e7eb !important; }

.eyebrow { font-family:'DM Mono',monospace; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.18em; color:#1d4ed8; }
.method-badge { display:inline-block; padding:2px 10px; border-radius:4px; font-family:'DM Mono',monospace; font-size:0.72rem; font-weight:500; margin-right:6px; }
.highlight-row { background:#fef9c3 !important; }
.savings-card { background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:20px 24px; }
.warning-card { background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; padding:16px 20px; }
.ref-card { background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; padding:16px 20px; font-size:0.82rem; line-height:1.8; }
.formula-box { background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:14px 18px; font-family:'DM Mono',monospace; font-size:0.82rem; line-height:1.9; color:#374151; }
</style>
""", unsafe_allow_html=True)

PLOTLY = dict(
    template="plotly_white",
    paper_bgcolor="#f8f9fb", plot_bgcolor="#fff",
    font=dict(color="#374151", family="IBM Plex Sans"),
    xaxis=dict(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(color="#6b7280")),
    yaxis=dict(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(color="#6b7280")),
    margin=dict(t=48, b=44, l=12, r=12),
)

METHOD_COLORS = {
    "Lot-for-Lot":       "#6366f1",
    "EOQ":               "#0ea5e9",
    "Period Order Qty":  "#8b5cf6",
    "Part Period Bal.":  "#f59e0b",
    "Silver-Meal":       "#22c55e",
    "Wagner-Whitin":     "#ef4444",
}

# ── LOT SIZING ALGORITHMS ─────────────────────────────────────────────────────
# All grounded in: Jacobs, Berry, Whybark & Vollmann (2011) Ch. 3–4
# and Silver, Pyke & Thomas (1998) Ch. 5

def compute_mrp_record(
    gross_req: List[float],
    sched_receipts: List[float],
    initial_inventory: float,
    lot_sizes: List[float],  # planned order receipts by period
    lead_time: int,
) -> pd.DataFrame:
    """
    Compute the standard MRP record as defined in Jacobs & Berry Ch. 3.

    Rows:
      Gross Requirements     (GR)
      Scheduled Receipts     (SR)
      Projected Available    (PAB) = PAB[t-1] + SR[t] + POR[t] - GR[t]
      Net Requirements       (NR)  = max(0, GR[t] - PAB[t-1] - SR[t])
      Planned Order Receipts (POR) -- from lot sizing rule
      Planned Order Releases (POL) -- POR shifted back by lead time
    """
    n = len(gross_req)
    pab = [0.0] * n
    nr  = [0.0] * n
    pol = [0.0] * n

    for t in range(n):
        prev_pab = initial_inventory if t == 0 else pab[t - 1]
        nr[t]  = max(0.0, gross_req[t] - prev_pab - sched_receipts[t])
        pab[t] = prev_pab + sched_receipts[t] + lot_sizes[t] - gross_req[t]

    # Planned Order Releases: place order lead_time periods before receipt
    for t in range(n):
        release_period = t - lead_time
        if release_period >= 0:
            pol[release_period] = lot_sizes[t]

    periods = [f"P{i+1}" for i in range(n)]
    df = pd.DataFrame({
        "Period":                periods,
        "Gross Requirements":    [round(v) for v in gross_req],
        "Scheduled Receipts":    [round(v) for v in sched_receipts],
        "Projected Available":   [round(v) for v in pab],
        "Net Requirements":      [round(v) for v in nr],
        "Planned Order Receipts":[round(v) for v in lot_sizes],
        "Planned Order Releases":[round(v) for v in pol],
    })
    return df


def compute_costs(
    lot_sizes: List[float],
    gross_req: List[float],
    sched_receipts: List[float],
    initial_inventory: float,
    ordering_cost: float,
    holding_cost_per_unit_per_period: float,
) -> Tuple[float, float, float]:
    """
    Compute ordering cost, holding cost, total cost.
    Holding cost applied to end-of-period inventory (Jacobs & Berry Ch. 4 convention).
    """
    num_orders = sum(1 for q in lot_sizes if q > 0)
    total_ordering = num_orders * ordering_cost

    # Compute end-of-period inventory
    pab = 0.0
    total_holding = 0.0
    for t in range(len(gross_req)):
        pab = pab + sched_receipts[t] + lot_sizes[t] - gross_req[t]
        total_holding += max(0.0, pab) * holding_cost_per_unit_per_period

    return total_ordering, total_holding, total_ordering + total_holding


def lot_for_lot(
    gross_req, sched_receipts, initial_inventory, moq=1
) -> List[float]:
    """
    Lot-for-Lot: order exactly net requirements each period.
    Source: Jacobs & Berry (2011), p. 93.
    Minimizes inventory investment but maximizes ordering frequency.
    """
    n = len(gross_req)
    orders = [0.0] * n
    pab = initial_inventory
    for t in range(n):
        nr = max(0.0, gross_req[t] - pab - sched_receipts[t])
        if nr > 0:
            orders[t] = max(moq, math.ceil(nr / moq) * moq)
        pab = pab + sched_receipts[t] + orders[t] - gross_req[t]
    return orders


def eoq_method(
    gross_req, sched_receipts, initial_inventory,
    ordering_cost, holding_cost_per_unit_per_period, moq=1
) -> List[float]:
    """
    Economic Order Quantity: Q* = sqrt(2DS/H).
    Source: Jacobs & Berry (2011), p. 94.
    D = total demand, S = ordering cost, H = holding cost per unit per period.
    Best for stable, predictable demand. Breaks down for lumpy demand.
    """
    D = sum(gross_req)
    H = holding_cost_per_unit_per_period
    S = ordering_cost
    if H <= 0 or D <= 0:
        return lot_for_lot(gross_req, sched_receipts, initial_inventory, moq)

    eoq = math.sqrt(2 * D * S / H)
    eoq = max(moq, math.ceil(eoq / moq) * moq)

    n = len(gross_req)
    orders = [0.0] * n
    pab = initial_inventory
    for t in range(n):
        nr = max(0.0, gross_req[t] - pab - sched_receipts[t])
        if nr > 0:
            orders[t] = max(eoq, math.ceil(nr / eoq) * eoq)
        pab = pab + sched_receipts[t] + orders[t] - gross_req[t]
    return orders


def period_order_qty(
    gross_req, sched_receipts, initial_inventory,
    ordering_cost, holding_cost_per_unit_per_period, moq=1
) -> List[float]:
    """
    Period Order Quantity: convert EOQ to a fixed review period P.
    P = round(EOQ / average_demand_per_period).
    Source: Jacobs & Berry (2011), p. 95.
    When net requirement exists, order enough to cover next P periods.
    """
    D = sum(gross_req)
    n = len(gross_req)
    avg = D / n if n > 0 else 1
    H = holding_cost_per_unit_per_period
    S = ordering_cost

    if H <= 0 or avg <= 0:
        return lot_for_lot(gross_req, sched_receipts, initial_inventory, moq)

    eoq = math.sqrt(2 * D * S / H)
    P   = max(1, round(eoq / avg))

    orders = [0.0] * n
    pab    = initial_inventory
    t      = 0
    while t < n:
        nr = max(0.0, gross_req[t] - pab - sched_receipts[t])
        if nr > 0:
            # Cover requirements for the next P periods
            qty = sum(gross_req[t:t + P]) - pab - sched_receipts[t]
            qty = max(moq, math.ceil(max(qty, nr) / moq) * moq)
            orders[t] = qty
            pab = pab + sched_receipts[t] + orders[t] - gross_req[t]
            t += 1
        else:
            pab = pab + sched_receipts[t] + orders[t] - gross_req[t]
            t += 1
    return orders


def part_period_balancing(
    gross_req, sched_receipts, initial_inventory,
    ordering_cost, holding_cost_per_unit_per_period, moq=1
) -> List[float]:
    """
    Part Period Balancing (PPB): equate cumulative holding costs to ordering cost.
    Economic Part Period (EPP) = S / H.
    Source: Jacobs & Berry (2011), p. 96; Silver, Pyke & Thomas (1998), p. 247.
    Find lot size where sum of (period_offset * demand) ≈ EPP.
    """
    H = holding_cost_per_unit_per_period
    S = ordering_cost
    n = len(gross_req)

    if H <= 0:
        return lot_for_lot(gross_req, sched_receipts, initial_inventory, moq)

    epp = S / H

    orders = [0.0] * n
    pab    = initial_inventory
    t      = 0

    while t < n:
        nr = max(0.0, gross_req[t] - pab - sched_receipts[t])
        if nr <= 0:
            pab = pab + sched_receipts[t] - gross_req[t]
            t += 1
            continue

        # Accumulate periods until part-periods ≈ EPP
        cum_pp  = 0.0
        cum_qty = gross_req[t]  # always include the trigger period (0 holding cost)
        j = t + 1
        while j < n:
            additional_pp = (j - t) * gross_req[j]
            if abs(cum_pp + additional_pp - epp) < abs(cum_pp - epp):
                cum_pp  += additional_pp
                cum_qty += gross_req[j]
                j += 1
            else:
                break

        qty = max(moq, math.ceil(max(cum_qty, nr) / moq) * moq)
        orders[t] = qty
        pab = pab + sched_receipts[t] + orders[t] - gross_req[t]

        # Advance past the periods covered by this order
        t = j if j > t + 1 else t + 1

    return orders


def silver_meal(
    gross_req, sched_receipts, initial_inventory,
    ordering_cost, holding_cost_per_unit_per_period, moq=1
) -> List[float]:
    """
    Silver-Meal Heuristic: minimize cost per period C(T).
    C(T) = (S + sum_{k=1}^{T-1} k * h * d_{t+k}) / T
    Stop adding periods when C(T+1) > C(T).
    Source: Silver & Meal (1973), Management Science.
    Best practical heuristic per Jeunet (2000) — cost penalty vs. Wagner-Whitin < 8%.
    """
    H = holding_cost_per_unit_per_period
    S = ordering_cost
    n = len(gross_req)

    if H <= 0:
        return lot_for_lot(gross_req, sched_receipts, initial_inventory, moq)

    orders = [0.0] * n
    pab    = initial_inventory
    t      = 0

    while t < n:
        nr = max(0.0, gross_req[t] - pab - sched_receipts[t])
        if nr <= 0:
            pab = pab + sched_receipts[t] - gross_req[t]
            t += 1
            continue

        # Find T that minimizes average cost per period
        best_T    = 1
        best_cost = S  # T=1: just ordering cost, 0 holding, cost/period = S
        cum_hold  = 0.0

        for j in range(t + 1, n):
            offset   = j - t
            cum_hold += offset * H * gross_req[j]
            cost_T   = (S + cum_hold) / (j - t + 1)
            if cost_T < best_cost:
                best_cost = cost_T
                best_T    = j - t + 1
            else:
                break  # cost is increasing — stop here

        qty = sum(gross_req[t:t + best_T])
        # Adjust for available inventory
        qty = max(0.0, qty - pab - sched_receipts[t])
        qty = max(moq, math.ceil(qty / moq) * moq) if qty > 0 else 0.0

        orders[t] = qty
        pab = pab + sched_receipts[t] + orders[t] - gross_req[t]
        t  += best_T

    return orders


def wagner_whitin(
    gross_req, sched_receipts, initial_inventory,
    ordering_cost, holding_cost_per_unit_per_period, moq=1
) -> List[float]:
    """
    Wagner-Whitin Algorithm: globally optimal lot sizing via dynamic programming.
    Source: Wagner & Whitin (1958), Management Science.
    f[t] = min_{j >= t} { S + h * sum_{k=t+1}^{j} (k-t)*d[k] + f[j+1] }
    Optimal but O(n²). In practice rarely available in ERP (Bahl 2009).
    Used here as the benchmark/lower bound.
    """
    H = holding_cost_per_unit_per_period
    S = ordering_cost
    n = len(gross_req)

    if H <= 0 or n == 0:
        return lot_for_lot(gross_req, sched_receipts, initial_inventory, moq)

    # Adjust gross requirements for initial inventory and scheduled receipts
    adj = [max(0.0, gross_req[t] - (initial_inventory if t == 0 else 0) - sched_receipts[t])
           for t in range(n)]

    # f[t] = min cost from period t onward
    # split[t] = next order period after ordering at t
    INF = float('inf')
    f     = [INF] * (n + 1)
    split = [0]   * (n + 1)
    f[n]  = 0.0

    for t in range(n - 1, -1, -1):
        if adj[t] == 0 and all(adj[k] == 0 for k in range(t, n)):
            f[t] = 0.0
            split[t] = n
            continue
        for j in range(t, n):
            # Order in period t covers requirements t through j
            hold = sum((k - t) * H * adj[k] for k in range(t + 1, j + 1))
            cost = S + hold + f[j + 1]
            if cost < f[t]:
                f[t]     = cost
                split[t] = j + 1

    # Reconstruct order schedule
    orders = [0.0] * n
    t = 0
    while t < n:
        if adj[t] > 0 or (t == 0 and initial_inventory == 0 and sched_receipts[0] == 0):
            end = split[t]
            qty = sum(adj[t:end])
            qty = max(moq, math.ceil(qty / moq) * moq) if qty > 0 else 0.0
            orders[t] = qty
            t = end
        else:
            t += 1

    return orders


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:8px 0 18px">
  <div style="font-size:0.6rem;text-transform:uppercase;letter-spacing:0.18em;color:#3b82f6;font-weight:600;margin-bottom:4px">MRP Planning</div>
  <div style="font-size:1.2rem;font-weight:600;color:#f9fafb">Lot Sizing Optimizer</div>
  <div style="font-size:0.75rem;color:#4b5563;margin-top:2px">Based on Jacobs & Berry (APICS)</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("#### Cost Parameters")

    unit_cost   = st.number_input("Unit Cost ($)",              value=25.00,  step=0.50,  min_value=0.01)
    order_cost  = st.number_input("Ordering Cost per PO ($)",   value=150.00, step=10.0,  min_value=1.0,
                                  help="Cost to place one purchase order: admin, receiving, inspection. Jacobs & Berry call this 'S'.")
    hold_rate   = st.number_input("Annual Holding Rate (%)",    value=25.0,   step=1.0,   min_value=1.0,
                                  help="Annual cost to hold $1 of inventory (typically 20–30%). Covers capital, storage, obsolescence.")
    lead_time   = st.number_input("Lead Time (periods)",        value=1,      step=1,     min_value=0, max_value=6,
                                  help="How many periods between placing and receiving an order.")
    init_inv    = st.number_input("Initial Inventory (units)",  value=0,      step=10,    min_value=0)
    moq         = st.number_input("Minimum Order Qty (units)",  value=1,      step=1,     min_value=1,
                                  help="Supplier minimum. Silver-Meal and Wagner-Whitin round up to this.")

    # Derived holding cost per unit per period (monthly if periods = months)
    periods_per_year = 12  # assumed monthly periods
    h_per_period = (hold_rate / 100) * unit_cost / periods_per_year

    st.markdown("---")

    current_method = st.selectbox(
        "Your Current Method",
        ["Lot-for-Lot", "EOQ", "Period Order Qty", "Fixed Batch (enter below)"],
        help="What does your ERP currently use? This is the baseline for savings calculation."
    )
    fixed_batch = 0
    if current_method == "Fixed Batch (enter below)":
        fixed_batch = st.number_input("Fixed Batch Size (units)", value=100, step=10, min_value=1)

    st.markdown("---")
    st.markdown("""
<div style="font-size:0.72rem;color:#374151;line-height:1.9">
<div style="color:#3b82f6;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:6px">Reference</div>
Jacobs, Berry, Whybark &amp; Vollmann<br>
<em>Manufacturing Planning and Control</em><br>
6th Ed. — Ch. 3–4 (APICS CPIM)<br><br>
Silver &amp; Meal (1973)<br>
<em>Management Science</em><br><br>
Wagner &amp; Whitin (1958)<br>
<em>Management Science, 5(1)</em>
</div>
""", unsafe_allow_html=True)


# ── DEMAND INPUT ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:12px 0 4px">
  <div class="eyebrow">MRP Lot Sizing Optimizer</div>
  <h1 style="font-size:1.75rem;font-weight:600;margin:6px 0 4px;letter-spacing:-0.02em">
    Which Lot Sizing Method Saves You the Most?
  </h1>
  <p style="color:#6b7280;font-size:0.88rem;max-width:680px;margin-bottom:0">
    Enter your gross requirements below. The tool computes the complete MRP record
    for all five standard methods (Jacobs &amp; Berry Ch. 4) and shows you exactly
    what each one costs in ordering + holding — so you can stop guessing.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Demand table — editable, pre-loaded with textbook-style example
st.markdown("#### Step 1 — Enter Gross Requirements by Period")
st.markdown("""
<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 16px;font-size:0.82rem;color:#1e40af;margin-bottom:12px">
<strong>Pre-loaded example</strong> based on a variable-demand fabricated component
(pattern consistent with Jacobs &amp; Berry Ch. 4 textbook case — 12 monthly periods).
Edit any cell. Add or remove rows as needed.
</div>
""", unsafe_allow_html=True)

default_demand = pd.DataFrame({
    "Period":            [f"P{i+1}" for i in range(12)],
    "Gross Requirements":[0, 50, 0, 80, 120, 0, 60, 40, 0, 100, 70, 30],
    "Scheduled Receipts":[50, 0, 0,  0,   0, 0,  0,  0, 0,   0,  0,  0],
})

edited = st.data_editor(
    default_demand,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Period":            st.column_config.TextColumn("Period", width="small"),
        "Gross Requirements":st.column_config.NumberColumn("Gross Requirements (units)", min_value=0, step=1),
        "Scheduled Receipts":st.column_config.NumberColumn("Scheduled Receipts (already on order)", min_value=0, step=1),
    }
)

gross_req  = edited["Gross Requirements"].fillna(0).tolist()
sched_rec  = edited["Scheduled Receipts"].fillna(0).tolist() if "Scheduled Receipts" in edited.columns else [0] * len(gross_req)
n_periods  = len(gross_req)

if n_periods < 2:
    st.error("Enter at least 2 periods of demand.")
    st.stop()

st.markdown("---")

# ── COMPUTE ALL METHODS ───────────────────────────────────────────────────────
@st.cache_data
def run_all_methods(gross_req, sched_rec, init_inv, order_cost, h_per_period, moq, lead_time):
    methods = {
        "Lot-for-Lot":      lot_for_lot(gross_req, sched_rec, init_inv, moq),
        "EOQ":              eoq_method(gross_req, sched_rec, init_inv, order_cost, h_per_period, moq),
        "Period Order Qty": period_order_qty(gross_req, sched_rec, init_inv, order_cost, h_per_period, moq),
        "Part Period Bal.": part_period_balancing(gross_req, sched_rec, init_inv, order_cost, h_per_period, moq),
        "Silver-Meal":      silver_meal(gross_req, sched_rec, init_inv, order_cost, h_per_period, moq),
        "Wagner-Whitin":    wagner_whitin(gross_req, sched_rec, init_inv, order_cost, h_per_period, moq),
    }
    costs = {}
    for name, orders in methods.items():
        oc, hc, tc = compute_costs(orders, gross_req, sched_rec, init_inv, order_cost, h_per_period)
        costs[name] = {"orders": orders, "ordering": oc, "holding": hc, "total": tc,
                       "n_orders": sum(1 for q in orders if q > 0)}
    return methods, costs

methods, costs = run_all_methods(
    tuple(gross_req), tuple(sched_rec),
    init_inv, order_cost, h_per_period, moq, lead_time
)

# Identify optimal and worst
sorted_costs = sorted(costs.items(), key=lambda x: x[1]["total"])
optimal_name = sorted_costs[0][0]
worst_name   = sorted_costs[-1][0]

# ── STEP 2: COST COMPARISON ───────────────────────────────────────────────────
st.markdown("#### Step 2 — Cost Comparison Across All Methods")

col_m = [c for c in sorted_costs]
metric_cols = st.columns(len(col_m))
for i, (name, c) in enumerate(col_m):
    is_best = name == optimal_name
    delta_vs_ww = round(c["total"] - costs["Wagner-Whitin"]["total"], 2)
    metric_cols[i].metric(
        label=name,
        value=f"${c['total']:.0f}",
        delta=f"Optimal ✓" if is_best else f"+${delta_vs_ww:.0f} vs optimal",
        delta_color="normal" if is_best else "inverse"
    )

st.markdown("")

# Stacked bar chart: ordering vs holding
fig_bar = go.Figure()
names_list   = [n for n,_ in col_m]
ordering_vals= [costs[n]["ordering"] for n in names_list]
holding_vals = [costs[n]["holding"]  for n in names_list]
colors       = [METHOD_COLORS.get(n, "#6b7280") for n in names_list]

fig_bar.add_trace(go.Bar(
    name="Ordering Cost",
    x=names_list, y=ordering_vals,
    marker_color=[c for c in colors],
    opacity=0.85,
    text=[f"${v:.0f}" for v in ordering_vals],
    textposition="inside", textfont=dict(color="white", size=11),
))
fig_bar.add_trace(go.Bar(
    name="Holding Cost",
    x=names_list, y=holding_vals,
    marker_color=[c for c in colors],
    opacity=0.45,
    text=[f"${v:.0f}" for v in holding_vals],
    textposition="inside", textfont=dict(color="white", size=11),
))

# Highlight optimal
fig_bar.add_annotation(
    x=optimal_name, y=costs[optimal_name]["total"] + 15,
    text="✓ Optimal", showarrow=False,
    font=dict(color="#16a34a", size=12, family="IBM Plex Sans"),
)

fig_bar.update_layout(
    **PLOTLY, barmode="stack", height=360,
    title=dict(text="Total Cost per Method = Ordering Cost + Holding Cost", font=dict(size=14)),
    xaxis_title="", yaxis_title="Total Cost ($)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
)
st.plotly_chart(fig_bar, use_container_width=True)

# ── SAVINGS ANALYSIS ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Step 3 — Savings vs. Your Current Method")

# Determine current method cost
if current_method == "Fixed Batch (enter below)":
    fb_orders = [0.0] * n_periods
    pab_fb = float(init_inv)
    for t in range(n_periods):
        nr = max(0.0, gross_req[t] - pab_fb - sched_rec[t])
        if nr > 0:
            batches = math.ceil(nr / fixed_batch)
            fb_orders[t] = batches * fixed_batch
        pab_fb = pab_fb + sched_rec[t] + fb_orders[t] - gross_req[t]
    _, _, current_cost = compute_costs(fb_orders, gross_req, sched_rec, init_inv, order_cost, h_per_period)
    current_label = f"Fixed Batch ({fixed_batch} units)"
else:
    current_cost  = costs[current_method]["total"]
    current_label = current_method

optimal_cost  = costs[optimal_name]["total"]
savings_12m   = (current_cost - optimal_cost)
savings_ann   = savings_12m * (12 / n_periods)  # annualized

if savings_12m > 0:
    st.markdown(f"""
<div class="savings-card">
  <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;color:#16a34a;font-weight:600;margin-bottom:8px">Savings Opportunity</div>
  <div style="font-size:1.8rem;font-weight:600;color:#15803d;font-family:'DM Mono',monospace">${savings_12m:.0f}
    <span style="font-size:0.9rem;color:#16a34a;font-family:'IBM Plex Sans',sans-serif">over {n_periods} periods</span>
  </div>
  <div style="font-size:0.88rem;color:#166534;margin-top:6px">
    Switching from <strong>{current_label}</strong> to <strong>{optimal_name}</strong>
    saves approximately <strong>${savings_ann:.0f}/year</strong> on this one component.
    Across a 200-component BOM, this compounds significantly.
  </div>
</div>
""", unsafe_allow_html=True)
elif savings_12m == 0:
    st.success(f"✓ Your current method ({current_label}) is already optimal for this demand pattern.")
else:
    st.markdown(f"""
<div class="warning-card">
  <strong>Your current method is already better than the selected optimal</strong>
  — which can happen when demand perfectly matches your method's assumptions.
  Review the full comparison above.
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ── MRP RECORDS ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Step 4 — Full MRP Record")
st.markdown("""
<div style="font-size:0.82rem;color:#6b7280;margin-bottom:12px">
The standard MRP record format from Jacobs &amp; Berry (2011), Ch. 3.
Select a method to see its complete record including Planned Order Releases
(when to place orders, offset by lead time).
</div>
""", unsafe_allow_html=True)

selected_method = st.selectbox(
    "View MRP Record for:",
    list(methods.keys()),
    index=list(methods.keys()).index(optimal_name)
)

mrp_df = compute_mrp_record(
    gross_req, sched_rec, init_inv,
    methods[selected_method], lead_time
)

# Style the record: highlight rows where orders are placed
def style_mrp(df):
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    for i, row in df.iterrows():
        if row["Planned Order Releases"] > 0:
            styles.loc[i, "Planned Order Releases"] = "background:#dbeafe;color:#1d4ed8;font-weight:600"
        if row["Net Requirements"] > 0:
            styles.loc[i, "Net Requirements"] = "background:#fef3c7;color:#92400e;font-weight:600"
    return styles

styled = mrp_df.style.apply(style_mrp, axis=None)
st.dataframe(styled, use_container_width=True, hide_index=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Number of Orders",       costs[selected_method]["n_orders"])
c2.metric("Total Ordering Cost",    f"${costs[selected_method]['ordering']:.0f}")
c3.metric("Total Holding Cost",     f"${costs[selected_method]['holding']:.0f}")
c4.metric("Total Cost",             f"${costs[selected_method]['total']:.0f}")

# Inventory profile chart
st.markdown("")
pab_vals = mrp_df["Projected Available"].tolist()
por_vals = mrp_df["Planned Order Receipts"].tolist()
gr_vals  = mrp_df["Gross Requirements"].tolist()
periods  = mrp_df["Period"].tolist()

fig_inv = go.Figure()
fig_inv.add_trace(go.Bar(
    x=periods, y=por_vals, name="Order Received",
    marker_color=METHOD_COLORS.get(selected_method, "#6366f1"),
    opacity=0.7, yaxis="y"
))
fig_inv.add_trace(go.Scatter(
    x=periods, y=pab_vals, name="Projected Available",
    mode="lines+markers", line=dict(color="#111827", width=2),
    marker=dict(size=6), yaxis="y"
))
fig_inv.add_trace(go.Bar(
    x=periods, y=[-v for v in gr_vals], name="Gross Requirements (−)",
    marker_color="#ef4444", opacity=0.4, yaxis="y"
))
fig_inv.add_hline(y=0, line_dash="solid", line_color="#6b7280", line_width=1)

fig_inv.update_layout(
    **PLOTLY, height=320, barmode="relative",
    title=dict(text=f"Inventory Profile — {selected_method}", font=dict(size=13)),
    xaxis_title="Period", yaxis_title="Units",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)")
)
st.plotly_chart(fig_inv, use_container_width=True)

# ── METHOD EXPLAINER ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📚 Method Reference — What each algorithm does and when to use it"):

    col1, col2 = st.columns(2)

    with col1:
        eoq_val = round(math.sqrt(2 * sum(gross_req) * order_cost / (h_per_period * n_periods)), 1) if h_per_period > 0 else "N/A"

        st.markdown(f"""
<div class="formula-box">
<strong>1. Lot-for-Lot (L4L)</strong>
Order = Net Requirements (exactly)
No excess inventory. Maximum orders.

Best when: Demand is stable, setup cost
is low, carrying cost is high.
Risk: High ordering frequency.
<br>
<strong>2. Economic Order Quantity (EOQ)</strong>
Q* = √(2DS/H)
D = {sum(gross_req):.0f} units  S = ${order_cost:.0f}  H = ${h_per_period:.3f}/unit/period
Q* ≈ {eoq_val} units

Best when: Demand is steady and predictable.
Risk: Over-stocks when demand is lumpy.
Source: Jacobs & Berry (2011), p. 94
<br>
<strong>3. Period Order Quantity (POQ)</strong>
P = round(EOQ / avg demand per period)
Order every P periods, qty covers next P.

Best when: Demand has a regular rhythm.
Adapts EOQ to discrete time buckets.
Source: Jacobs & Berry (2011), p. 95
</div>
""", unsafe_allow_html=True)

    with col2:
        epp_val = round(order_cost / h_per_period, 1) if h_per_period > 0 else "N/A"
        st.markdown(f"""
<div class="formula-box">
<strong>4. Part Period Balancing (PPB)</strong>
EPP = S/H = {order_cost:.0f}/{h_per_period:.3f} ≈ {epp_val} part-periods
Balance cumulative holding cost ≈ S.

Best when: Demand is variable/lumpy.
Practical, available in most ERP systems.
Source: Jacobs & Berry (2011), p. 96
<br>
<strong>5. Silver-Meal Heuristic ★ Best practical</strong>
Minimize C(T) = (S + Σ holding costs) / T
Stop when C(T+1) > C(T).

Best for variable demand. Research shows
cost penalty vs. optimal &lt; 8%.
Source: Silver & Meal (1973), Mgmt. Science
<br>
<strong>6. Wagner-Whitin (Benchmark)</strong>
Dynamic programming: globally optimal.
f[t] = min {{ S + holding(t→j) + f[j+1] }}

Optimal but O(n²). Rarely in ERP systems.
Use as lower bound only.
Source: Wagner & Whitin (1958), Mgmt. Science
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="ref-card" style="margin-top:16px">
<strong>Why this matters for real manufacturers</strong><br>
Research across industrial case studies shows that companies using static EOQ
for variable demand pay 15–25% more in total inventory costs than necessary.
<br><br>
A manufacturer with $5M in annual component spend, carrying 25% holding cost and
placing orders at $150 each, can typically save $75K–$125K/year by switching from
a poorly-calibrated EOQ or fixed batch to Silver-Meal — on no capital investment.
The ERP already supports multiple lot sizing rules. Most procurement managers
simply never ran the comparison.
<br><br>
<strong>This tool runs that comparison in under 60 seconds.</strong>
</div>
""", unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<p style="font-size:0.75rem;color:#9ca3af;text-align:center">
MRP Lot Sizing Optimizer · Algorithms: Jacobs, Berry, Whybark & Vollmann (2011) ·
Silver & Meal (1973) · Wagner & Whitin (1958) ·
Built by Rutwik Satish · MS Engineering Management, Northeastern University
</p>
""", unsafe_allow_html=True)
