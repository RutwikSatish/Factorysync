"""
MRP Lot Sizing Optimizer — Streamlit interface
==============================================
Built by Rutwik Satish | M.S. Engineering Management, Northeastern University

THE PROBLEM THIS SOLVES
  Every manufacturer running MRP must decide how much to order and when. Most
  small-to-mid manufacturers default to lot-for-lot or a fixed batch set years
  ago and never revisited. This tool computes the full MRP record under six
  standard lot sizing rules and prices each one, so the choice is made against
  numbers instead of an ERP default.

TEXTBOOK FOUNDATION
  Jacobs, Berry, Whybark & Vollmann (2011), "Manufacturing Planning and
      Control for Supply Chain Management", Ch. 3-4 (APICS CPIM reference).
  Silver & Meal (1973), Management Science.
  Wagner & Whitin (1958), Management Science 5(1).
  Silver, Pyke & Thomas (1998), Ch. 5.

THE SIX METHODS
  1. Lot-for-Lot            5. Silver-Meal heuristic
  2. Economic Order Qty     6. Wagner-Whitin (dynamic programming reference)
  3. Period Order Qty
  4. Part Period Balancing

All algorithms live in lotsizing.py and are covered by test_lotsizing.py.
"""

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lotsizing import (
    compute_costs,
    economic_order_quantity,
    fixed_batch,
    net_requirements,
    planned_order_releases,
    projected_available,
    run_all_methods,
    stockout_periods,
)

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
[data-testid="stSidebar"] { background:#111827 !important; border-right:1px solid #1f2937 !important; }
[data-testid="stSidebar"] * { color:#9ca3af !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color:#f9fafb !important; }
[data-testid="stSidebarNav"] { display:none !important; }

h1,h2,h3 { font-family:'IBM Plex Sans',sans-serif !important; color:#111827 !important; }

[data-testid="metric-container"] {
    background:#fff !important; border:1px solid #e5e7eb !important;
    border-radius:10px !important; padding:16px !important;
    box-shadow:0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stMetricValue"] { color:#111827 !important; font-family:'DM Mono',monospace !important; font-size:1.5rem !important; font-weight:600 !important; }
[data-testid="stMetricLabel"] { color:#6b7280 !important; font-size:0.7rem !important; text-transform:uppercase; letter-spacing:0.1em; }

[data-testid="stDataFrame"] { background:#fff !important; border:1px solid #e5e7eb !important; border-radius:10px !important; }
.stDataFrame th { background:#f9fafb !important; color:#6b7280 !important; font-size:0.72rem !important; text-transform:uppercase; letter-spacing:0.06em; font-family:'DM Mono',monospace !important; }
.stDataFrame td { color:#111827 !important; font-size:0.85rem !important; font-family:'DM Mono',monospace !important; }

[data-testid="stButton"] button { background:#1d4ed8 !important; color:#fff !important; border:none !important; border-radius:8px !important; font-weight:500 !important; }
[data-testid="stSelectbox"] > div, [data-testid="stNumberInput"] > div > div { background:#fff !important; border:1px solid #e5e7eb !important; border-radius:8px !important; }
hr { border-color:#e5e7eb !important; }

.eyebrow { font-family:'DM Mono',monospace; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.18em; color:#1d4ed8; }
.savings-card { background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:20px 24px; }
.warning-card { background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; padding:16px 20px; }
.error-card   { background:#fef2f2; border:1px solid #fecaca; border-radius:10px; padding:16px 20px; color:#991b1b; }
.ref-card     { background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; padding:16px 20px; font-size:0.82rem; line-height:1.8; }
.formula-box  { background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:14px 18px; font-family:'DM Mono',monospace; font-size:0.82rem; line-height:1.9; color:#374151; }
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
    "Lot-for-Lot":      "#6366f1",
    "EOQ":              "#0ea5e9",
    "Period Order Qty": "#8b5cf6",
    "Part Period Bal.": "#f59e0b",
    "Silver-Meal":      "#22c55e",
    "Wagner-Whitin":    "#ef4444",
}

PERIOD_UNITS = {"Weeks": 52, "Months": 12, "Quarters": 4}


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:8px 0 18px">
  <div style="font-size:0.6rem;text-transform:uppercase;letter-spacing:0.18em;color:#3b82f6;font-weight:600;margin-bottom:4px">MRP Planning</div>
  <div style="font-size:1.2rem;font-weight:600;color:#f9fafb">Lot Sizing Optimizer</div>
  <div style="font-size:0.75rem;color:#4b5563;margin-top:2px">Based on Jacobs &amp; Berry (APICS)</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("#### Planning Calendar")
    period_unit = st.selectbox(
        "Period Bucket", list(PERIOD_UNITS.keys()), index=1,
        help="What one period represents. This converts the annual holding rate "
             "into a per-period rate — getting it wrong scales every holding cost.",
    )
    periods_per_year = PERIOD_UNITS[period_unit]

    st.markdown("#### Cost Parameters")
    unit_cost  = st.number_input("Unit Cost ($)", value=25.00, step=0.50, min_value=0.01)
    order_cost = st.number_input(
        "Ordering Cost per PO ($)", value=150.00, step=10.0, min_value=1.0,
        help="Cost to place one purchase order: admin, receiving, inspection. Jacobs & Berry call this 'S'.",
    )
    hold_rate  = st.number_input(
        "Annual Holding Rate (%)", value=25.0, step=1.0, min_value=0.1,
        help="Annual cost to hold $1 of inventory (typically 20-30%): capital, storage, obsolescence.",
    )
    lead_time  = st.number_input("Lead Time (periods)", value=1, step=1, min_value=0, max_value=12)
    init_inv   = st.number_input("Initial Inventory (units)", value=0, step=10, min_value=0)
    moq        = st.number_input(
        "Minimum Order Qty / Multiple", value=1, step=1, min_value=1,
        help="Supplier minimum or order multiple. Note: above 1, Wagner-Whitin is no longer a proven optimum.",
    )

    h_per_period = (hold_rate / 100.0) * unit_cost / periods_per_year
    st.caption(f"Holding cost = ${h_per_period:,.4f} per unit per {period_unit.lower()[:-1]}")

    st.markdown("---")
    current_method = st.selectbox(
        "Your Current Method",
        ["Lot-for-Lot", "EOQ", "Period Order Qty", "Part Period Bal.", "Fixed Batch (enter below)"],
        help="What does your ERP use today? This is the baseline for the savings comparison.",
    )
    fixed_batch_size = 0
    if current_method == "Fixed Batch (enter below)":
        fixed_batch_size = st.number_input("Fixed Batch Size (units)", value=100, step=10, min_value=1)

    st.markdown("---")
    st.markdown("""
<div style="font-size:0.72rem;color:#374151;line-height:1.9">
<div style="color:#3b82f6;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:6px">Reference</div>
Jacobs, Berry, Whybark &amp; Vollmann<br>
<em>Manufacturing Planning and Control</em>, Ch. 3-4<br><br>
Silver &amp; Meal (1973), <em>Management Science</em><br><br>
Wagner &amp; Whitin (1958), <em>Management Science 5(1)</em>
</div>
""", unsafe_allow_html=True)


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:12px 0 4px">
  <div class="eyebrow">MRP Lot Sizing Optimizer</div>
  <h1 style="font-size:1.75rem;font-weight:600;margin:6px 0 4px;letter-spacing:-0.02em">
    Which Lot Sizing Method Costs You Least?
  </h1>
  <p style="color:#6b7280;font-size:0.88rem;max-width:700px;margin-bottom:0">
    Enter gross requirements below. The tool nets them against on-hand stock and
    scheduled receipts, then computes the full MRP record and total cost under six
    standard rules (Jacobs &amp; Berry Ch. 4) so you can compare them directly.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── STEP 1: DEMAND ────────────────────────────────────────────────────────────
st.markdown("#### Step 1 — Enter Gross Requirements by Period")
st.markdown("""
<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 16px;font-size:0.82rem;color:#1e40af;margin-bottom:12px">
<strong>Illustrative example loaded below</strong> — 12 periods of variable demand for a
fabricated component, with one scheduled receipt already on order. Edit any cell,
or add and remove rows.
</div>
""", unsafe_allow_html=True)

default_demand = pd.DataFrame({
    "Period":             [f"P{i+1}" for i in range(12)],
    "Gross Requirements": [0, 50, 0, 80, 120, 0, 60, 40, 0, 100, 70, 30],
    "Scheduled Receipts": [50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
})

edited = st.data_editor(
    default_demand,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Period":             st.column_config.TextColumn("Period", width="small"),
        "Gross Requirements": st.column_config.NumberColumn("Gross Requirements (units)", min_value=0, step=1),
        "Scheduled Receipts": st.column_config.NumberColumn("Scheduled Receipts (on order)", min_value=0, step=1),
    },
)

gross_req = [float(v) for v in edited["Gross Requirements"].fillna(0).tolist()]
sched_rec = [float(v) for v in edited["Scheduled Receipts"].fillna(0).tolist()]
n_periods = len(gross_req)
periods    = [f"P{i+1}" for i in range(n_periods)]

if n_periods < 2:
    st.error("Enter at least 2 periods of demand.")
    st.stop()
if sum(gross_req) <= 0:
    st.warning("Total gross requirements are zero — nothing to plan.")
    st.stop()

st.markdown("---")


# ── COMPUTE ───────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _run(gross_req, sched_rec, init_inv, order_cost, h_per_period, moq):
    return run_all_methods(list(gross_req), list(sched_rec), init_inv,
                           order_cost, h_per_period, moq)

results = _run(tuple(gross_req), tuple(sched_rec), float(init_inv),
               order_cost, h_per_period, int(moq))

net_req = net_requirements(gross_req, sched_rec, float(init_inv))

# Feasibility guard: no rule should ever produce a plan that runs negative.
infeasible = {name: r["stockouts"] for name, r in results.items() if r["stockouts"]}
if infeasible:
    detail = "; ".join(f"{k} in periods {v}" for k, v in infeasible.items())
    st.markdown(f"""
<div class="error-card">
<strong>Plan infeasible — do not use these results.</strong><br>
Projected available goes negative for: {detail}.<br>
This indicates a defect in the lot sizing logic, not a property of your data.
</div>
""", unsafe_allow_html=True)

sorted_costs = sorted(results.items(), key=lambda kv: kv[1]["total"])
optimal_name = sorted_costs[0][0]
ww_cost      = results["Wagner-Whitin"]["total"]


# ── STEP 2: COST COMPARISON ───────────────────────────────────────────────────
st.markdown("#### Step 2 — Cost Comparison Across All Methods")

cols = st.columns(len(sorted_costs))
for i, (name, r) in enumerate(sorted_costs):
    gap = r["total"] - ww_cost
    cols[i].metric(
        label=name,
        value=f"${r['total']:,.0f}",
        delta="Lowest cost" if name == optimal_name else f"+${gap:,.0f} vs reference",
        delta_color="normal" if name == optimal_name else "inverse",
    )

if int(moq) > 1:
    st.caption(
        "Minimum order quantity is above 1, so Wagner-Whitin is a strong reference "
        "point rather than a proven lower bound."
    )

names_list    = [n for n, _ in sorted_costs]
ordering_vals = [results[n]["ordering"] for n in names_list]
holding_vals  = [results[n]["holding"] for n in names_list]
colors        = [METHOD_COLORS.get(n, "#6b7280") for n in names_list]

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    name="Ordering Cost", x=names_list, y=ordering_vals,
    marker_color=colors, opacity=0.85,
    text=[f"${v:,.0f}" for v in ordering_vals],
    textposition="inside", textfont=dict(color="white", size=11),
))
fig_bar.add_trace(go.Bar(
    name="Holding Cost", x=names_list, y=holding_vals,
    marker_color=colors, opacity=0.45,
    text=[f"${v:,.0f}" for v in holding_vals],
    textposition="inside", textfont=dict(color="white", size=11),
))
fig_bar.update_layout(
    **PLOTLY, barmode="stack", height=360,
    title=dict(text="Total Cost = Ordering Cost + Holding Cost", font=dict(size=14)),
    xaxis_title="", yaxis_title="Total Cost ($)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
)
st.plotly_chart(fig_bar, use_container_width=True)


# ── STEP 3: SAVINGS ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Step 3 — Savings vs. Your Current Method")

if current_method == "Fixed Batch (enter below)":
    fb_receipts   = fixed_batch(net_req, batch=float(fixed_batch_size), moq=int(moq))
    current_cost  = compute_costs(fb_receipts, gross_req, sched_rec, float(init_inv),
                                  order_cost, h_per_period)["total"]
    current_label = f"Fixed Batch ({fixed_batch_size} units)"
    current_bad   = stockout_periods(gross_req, sched_rec, float(init_inv), fb_receipts)
else:
    current_cost  = results[current_method]["total"]
    current_label = current_method
    current_bad   = results[current_method]["stockouts"]

optimal_cost = results[optimal_name]["total"]
savings      = current_cost - optimal_cost
annualised   = savings * (periods_per_year / n_periods)

if current_bad:
    st.markdown(f"""
<div class="error-card">
Your current method leaves projected available negative in periods {current_bad}.
Fix the shortage before comparing costs — an infeasible plan is not cheaper, it is short.
</div>
""", unsafe_allow_html=True)
elif savings > 0.5:
    st.markdown(f"""
<div class="savings-card">
  <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;color:#16a34a;font-weight:600;margin-bottom:8px">Savings Opportunity</div>
  <div style="font-size:1.8rem;font-weight:600;color:#15803d;font-family:'DM Mono',monospace">${savings:,.0f}
    <span style="font-size:0.9rem;color:#16a34a;font-family:'IBM Plex Sans',sans-serif">over {n_periods} {period_unit.lower()}</span>
  </div>
  <div style="font-size:0.88rem;color:#166534;margin-top:6px">
    On this component, switching from <strong>{current_label}</strong> to
    <strong>{optimal_name}</strong> lowers ordering plus holding cost by
    <strong>${savings:,.0f}</strong> across the horizon shown
    (about <strong>${annualised:,.0f}</strong> at an annual run rate, if this
    demand pattern is representative).
  </div>
  <div style="font-size:0.75rem;color:#4d7c0f;margin-top:10px">
    Scope: one item, ordering and holding cost only. Purchase cost is excluded
    because total units bought is unchanged absent quantity discounts. Extrapolating
    to a full bill of materials requires running each item on its own demand pattern.
  </div>
</div>
""", unsafe_allow_html=True)
elif abs(savings) <= 0.5:
    st.success(f"Your current method ({current_label}) is already the lowest-cost option for this demand pattern.")
else:
    st.markdown("""
<div class="warning-card">
<strong>Your current method already beats the alternatives on this data.</strong>
That is a real result — it usually means demand matches the method's assumptions well.
</div>
""", unsafe_allow_html=True)


# ── STEP 4: MRP RECORD ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Step 4 — Full MRP Record")
st.markdown("""
<div style="font-size:0.82rem;color:#6b7280;margin-bottom:12px">
Standard MRP record format (Jacobs &amp; Berry Ch. 3). Planned Order Releases are
Planned Order Receipts offset back by the lead time.
</div>
""", unsafe_allow_html=True)

selected = st.selectbox(
    "View MRP Record for:", list(results.keys()),
    index=list(results.keys()).index(optimal_name),
)

receipts        = results[selected]["receipts"]
pab             = projected_available(gross_req, sched_rec, float(init_inv), receipts)
releases, due   = planned_order_releases(receipts, int(lead_time))

mrp_df = pd.DataFrame({
    "Period":                 periods,
    "Gross Requirements":     [round(v) for v in gross_req],
    "Scheduled Receipts":     [round(v) for v in sched_rec],
    "Projected Available":    [round(v) for v in pab],
    "Net Requirements":       [round(v) for v in net_req],
    "Planned Order Receipts": [round(v) for v in receipts],
    "Planned Order Releases": [round(v) for v in releases],
})


def style_mrp(df):
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    for i, row in df.iterrows():
        if row["Planned Order Releases"] > 0:
            styles.loc[i, "Planned Order Releases"] = "background:#dbeafe;color:#1d4ed8;font-weight:600"
        if row["Net Requirements"] > 0:
            styles.loc[i, "Net Requirements"] = "background:#fef3c7;color:#92400e;font-weight:600"
        if row["Projected Available"] < 0:
            styles.loc[i, "Projected Available"] = "background:#fee2e2;color:#991b1b;font-weight:600"
    return styles


st.dataframe(mrp_df.style.apply(style_mrp, axis=None), use_container_width=True, hide_index=True)

if due > 0:
    st.markdown(f"""
<div class="warning-card">
<strong>Past due: {due:,.0f} units.</strong> With a lead time of {lead_time} period(s),
these orders would have needed releasing before the start of the horizon. A live MRP
system raises this as a past-due action message — expedite, or shorten the lead time.
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Number of Orders",    results[selected]["n_orders"])
c2.metric("Ordering Cost",       f"${results[selected]['ordering']:,.0f}")
c3.metric("Holding Cost",        f"${results[selected]['holding']:,.0f}")
c4.metric("Total Cost",          f"${results[selected]['total']:,.0f}")

fig_inv = go.Figure()
fig_inv.add_trace(go.Bar(
    x=periods, y=receipts, name="Order Received",
    marker_color=METHOD_COLORS.get(selected, "#6366f1"), opacity=0.7,
))
fig_inv.add_trace(go.Scatter(
    x=periods, y=pab, name="Projected Available",
    mode="lines+markers", line=dict(color="#111827", width=2), marker=dict(size=6),
))
fig_inv.add_trace(go.Bar(
    x=periods, y=[-v for v in gross_req], name="Gross Requirements (−)",
    marker_color="#ef4444", opacity=0.4,
))
fig_inv.add_hline(y=0, line_dash="solid", line_color="#6b7280", line_width=1)
fig_inv.update_layout(
    **PLOTLY, height=320, barmode="relative",
    title=dict(text=f"Inventory Profile — {selected}", font=dict(size=13)),
    xaxis_title="Period", yaxis_title="Units",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
)
st.plotly_chart(fig_inv, use_container_width=True)


# ── METHOD REFERENCE ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("Method Reference — what each algorithm does and when to use it"):
    total_net = sum(net_req)
    eoq_val = economic_order_quantity(total_net, n_periods, order_cost, h_per_period)
    epp_val = order_cost / h_per_period if h_per_period > 0 else float("nan")
    avg_net = total_net / n_periods if n_periods else 0.0
    poq_p   = max(1, int(round(eoq_val / avg_net))) if avg_net > 0 else 1

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
<div class="formula-box">
<strong>1. Lot-for-Lot (L4L)</strong>
Order = net requirement, exactly.
No carried inventory, maximum order count.
Use when setup cost is low relative to
holding cost. Jacobs &amp; Berry p. 93
<br>
<strong>2. Economic Order Quantity (EOQ)</strong>
Q* = sqrt(2 D S / H), D and H on the
SAME time basis.
D = {avg_net:,.1f} units per {period_unit.lower()[:-1]}
S = ${order_cost:,.0f}   H = ${h_per_period:,.4f}/unit/period
Q* = {eoq_val:,.1f} units
Assumes steady demand; over-orders when
demand is lumpy. Jacobs &amp; Berry p. 94
<br>
<strong>3. Period Order Quantity (POQ)</strong>
P = round(Q* / average demand) = {poq_p}
Order every P periods, covering P periods.
Adapts EOQ to discrete buckets.
Jacobs &amp; Berry p. 95
</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
<div class="formula-box">
<strong>4. Part Period Balancing (PPB)</strong>
EPP = S / H = {epp_val:,.1f} part-periods
Extend the lot until cumulative part-periods
are closest to EPP. Handles lumpy demand and
is available in most ERP systems.
Jacobs &amp; Berry p. 96
<br>
<strong>5. Silver-Meal Heuristic</strong>
Minimise C(T) = (S + holding to T) / T,
stopping when C(T+1) &gt; C(T).
Designed for variable demand; widely reported
to land close to optimal in simulation studies.
Silver &amp; Meal (1973)
<br>
<strong>6. Wagner-Whitin (Reference)</strong>
f[t] = min over j of S + hold(t..j) + f[j+1]
Exact optimum for the uncapacitated problem,
O(n^2). Seldom implemented in ERP; used here
as the comparison benchmark.
Wagner &amp; Whitin (1958)
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="ref-card" style="margin-top:16px">
<strong>How to read these results</strong><br>
The comparison covers one item over the horizon you entered, and counts ordering
and holding cost only. It assumes demand is known, supply is uncapacitated, no
stockouts are permitted, and unit price does not vary with order quantity. Where
those assumptions do not hold — quantity discounts, shared capacity, demand
uncertainty requiring safety stock — treat the ranking as a starting point for
analysis rather than a decision.
<br><br>
The practical value is usually not the dollar figure on one part. It is that most
ERP systems already support several of these rules, and the parameter is often set
once at item creation and never revisited against actual demand behaviour.
</div>
""", unsafe_allow_html=True)


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<p style="font-size:0.75rem;color:#9ca3af;text-align:center">
MRP Lot Sizing Optimizer · Algorithms: Jacobs, Berry, Whybark &amp; Vollmann (2011) ·
Silver &amp; Meal (1973) · Wagner &amp; Whitin (1958)<br>
Logic in <code>lotsizing.py</code>, verified by <code>test_lotsizing.py</code> ·
Built by Rutwik Satish · M.S. Engineering Management, Northeastern University
</p>
""", unsafe_allow_html=True)
