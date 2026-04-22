"""
FactorySync — Supplier Industrialization & MRP Platform
=========================================================
Built by Rutwik Satish | MS Engineering Management, Northeastern University

WHY THIS EXISTS:
  In automotive manufacturing, Start of Production (SOP) is a hard deadline.
  Missing it costs OEMs $1M–$5M per day in penalty clauses and lost production.
  Supplier Industrialization teams — the people responsible for getting suppliers
  ready before SOP — coordinate PPAP approvals, run SPC quality reviews, and
  manage MRP order schedules simultaneously, across dozens of suppliers, using
  a combination of SAP transactions and manual Excel trackers.

  When a PPAP element is rejected, it delays production readiness. When SPC
  goes out of control, it triggers a SCAR (Supplier Corrective Action Request).
  When MRP lead times are stale in SAP, planners order too late and production
  lines stop. These failures happen every week at automotive OEMs. FactorySync
  simulates the four core workflows that prevent them.

WHAT IT DOES:
  1. MRP Engine        — Explodes your BOM, offsets lead times, flags past-due orders
  2. PPAP Tracker      — Tracks 10 AIAG PPAP 4th Ed. elements per supplier, scores readiness
  3. SPC Dashboards    — Monitors critical dimensions with Xbar-R and p-charts
  4. Change Action     — Models obsolescence risk + ramp timing for engineering changes

DATA MODEL:
  All data is simulated to replicate SAP S/4HANA and AIAG standards.
  BOM structures mirror automotive EV battery pack assembly.
  SAP transaction codes are cited for every data field.

STACK: Python · Streamlit · Plotly · Pandas · NumPy · Groq (Llama 3, free)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FactorySync | Supplier Industrialization",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DESIGN SYSTEM ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="block-container"] {
    background-color: #f7f8fa !important;
    color: #1a1f2e !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #1a1f2e !important;
    border-right: 1px solid #252c3d !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }
[data-testid="stSidebarNav"] { display: none !important; }

h1,h2,h3,h4 { font-family: 'DM Sans', sans-serif !important; color: #0f172a !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #fff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stMetricValue"] { color: #0f172a !important; font-family: 'DM Mono', monospace !important; font-weight: 600 !important; font-size: 1.6rem !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetricDelta"] svg { display: none; }

/* Tabs */
[data-testid="stTabs"] button { color: #64748b !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.85rem !important; background: transparent !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #2563eb !important; border-bottom: 2px solid #2563eb !important; }

/* Dataframes */
[data-testid="stDataFrame"] { background: #fff !important; border: 1px solid #e2e8f0 !important; border-radius: 10px !important; }
.stDataFrame th { background: #f8fafc !important; color: #64748b !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.06em; }
.stDataFrame td { color: #1a1f2e !important; background: #fff !important; font-size: 0.84rem !important; }

/* Buttons */
[data-testid="stButton"] button {
    background: #2563eb !important; color: #fff !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
}
[data-testid="stButton"] button:hover { background: #1d4ed8 !important; }

/* Selectbox / inputs */
[data-testid="stSelectbox"] > div { background: #fff !important; border: 1px solid #e2e8f0 !important; border-radius: 8px !important; }
[data-testid="stSelectbox"] label { color: #64748b !important; font-size: 0.8rem !important; }
[data-testid="stNumberInput"] label { color: #64748b !important; font-size: 0.8rem !important; }

/* Data editor */
[data-testid="stDataFrameResizable"] { border: 1px solid #e2e8f0 !important; border-radius: 10px !important; }

/* Expander */
[data-testid="stExpander"] { background: #fff !important; border: 1px solid #e2e8f0 !important; border-radius: 10px !important; }
[data-testid="stExpander"] summary { color: #2563eb !important; font-weight: 500 !important; }

/* Alerts */
[data-testid="stAlert"] { border-radius: 8px !important; }
hr { border-color: #e2e8f0 !important; }

/* Custom */
.section-label {
    font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 0.14em; color: #2563eb; font-weight: 600; margin-bottom: 8px;
}
.problem-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-left: 3px solid #ef4444;
    border-radius: 10px; padding: 16px 20px; margin-bottom: 12px;
}
.solution-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-left: 3px solid #22c55e;
    border-radius: 10px; padding: 16px 20px; margin-bottom: 12px;
}
.module-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 18px 20px;
}
.module-number {
    font-family: 'DM Mono', monospace; font-size: 1.8rem;
    font-weight: 500; color: #2563eb; line-height: 1;
}
.module-title { font-weight: 600; font-size: 0.95rem; color: #0f172a; margin-top: 6px; }
.module-desc  { font-size: 0.82rem; color: #64748b; line-height: 1.6; margin-top: 4px; }
.sap-tag {
    display:inline-block; background:#f1f5f9; color:#475569;
    font-size:0.7rem; font-family:'DM Mono',monospace;
    padding:1px 7px; border-radius:4px; margin:2px 2px 0 0;
}
.ai-block {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-left: 3px solid #2563eb;
    border-radius: 10px; padding: 18px 22px;
    font-size: 0.87rem; line-height: 1.8;
    color: #1a1f2e; white-space: pre-wrap;
}
.status-approved  { color: #16a34a; font-weight: 600; }
.status-rejected  { color: #dc2626; font-weight: 600; }
.status-progress  { color: #d97706; font-weight: 600; }
.status-submitted { color: #2563eb; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── PLOTLY LIGHT TEMPLATE ─────────────────────────────────────────────────────
LIGHT = dict(
    template="plotly_white",
    paper_bgcolor="#f7f8fa", plot_bgcolor="#fff",
    font=dict(color="#1a1f2e", family="DM Sans"),
    xaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(color="#64748b")),
    yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(color="#64748b")),
    margin=dict(t=36, b=44, l=12, r=12),
)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:8px 0 16px">
  <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.16em;color:#60a5fa;font-weight:600;margin-bottom:4px">SUPPLIER INDUSTRIALIZATION</div>
  <div style="font-size:1.3rem;font-weight:600;color:#f1f5f9">FactorySync</div>
  <div style="font-size:0.78rem;color:#64748b;margin-top:2px">Pre-SOP Production Readiness</div>
</div>
""", unsafe_allow_html=True)

    module = st.radio(
        "Module",
        ["🏠  Overview", "📦  MRP Engine", "✅  PPAP Tracker", "📊  SPC Charts", "🔄  Change Action"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("""
<div style="font-size:0.72rem;color:#475569;line-height:1.7">
<div style="color:#94a3b8;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">DATA MODEL</div>
Simulated SAP S/4HANA data. Mirrors real EV battery pack assembly BOM structure, AIAG PPAP 4th Edition, and AIAG SPC manual.
<br><br>
<span style="color:#60a5fa">SAP transactions cited:</span><br>
MD01/MD06 · CS03 · MB52 · ME2M · MD04 · MM02
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if "Overview" in module:

    st.markdown("""
<div style="padding:24px 0 8px">
  <div class="section-label">PRE-SOP PRODUCTION READINESS PLATFORM</div>
  <h1 style="font-size:2rem;font-weight:600;margin:0;letter-spacing:-0.02em">FactorySync</h1>
  <p style="color:#64748b;font-size:0.9rem;margin-top:6px;max-width:640px">
    Replicates the four core workflows a Supplier Industrialization team runs in the 60–90 days before Start of Production — replacing a patchwork of SAP transactions and Excel trackers with a single integrated view.
  </p>
</div>
""", unsafe_allow_html=True)

    # Problem / Solution
    col_p, col_s = st.columns(2)
    with col_p:
        st.markdown("""
<div class="problem-card">
  <div class="section-label" style="color:#ef4444">THE INDUSTRY PROBLEM</div>
  <p style="font-size:0.87rem;line-height:1.75;color:#374151;margin:0">
    Automotive OEMs operate on hard SOP deadlines — missing them triggers
    <strong>$1M–$5M/day penalty clauses</strong>. The Supplier Industrialization team
    must confirm that every supplier can deliver conforming parts before production
    starts. This involves four simultaneous workflows: PPAP documentation approval,
    SPC quality sign-off, MRP order scheduling, and engineering change management.
    <br><br>
    Most teams manage this <strong style="color:#ef4444">across SAP, email, and Excel</strong>
    — with no integrated view of which suppliers are actually ready.
  </p>
</div>
""", unsafe_allow_html=True)
    with col_s:
        st.markdown("""
<div class="solution-card">
  <div class="section-label" style="color:#22c55e">HOW FACTORYSYNC SOLVES IT</div>
  <p style="font-size:0.87rem;line-height:1.75;color:#374151;margin:0">
    FactorySync integrates the four workflows into one platform, with data models
    that mirror real SAP fields and industry standards:
    <br><br>
    • <strong>MRP Engine</strong> — BOM explosion + lead time offset = order schedule with past-due flags<br>
    • <strong>PPAP Tracker</strong> — 10 AIAG elements per supplier, scored to a readiness % with SCAR recommendation<br>
    • <strong>SPC Charts</strong> — Xbar-R and p-charts using AIAG SPC manual constants (A2/D3/D4)<br>
    • <strong>Change Action</strong> — ECO impact model: stranded inventory + new part order timing
  </p>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # Portfolio summary metrics
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Active Suppliers",   "15")
    c2.metric("PPAP Completion",    "68%",  delta="SOP in 45 days", delta_color="inverse")
    c3.metric("Parts In SPC Control","11/15")
    c4.metric("Open Change Actions","3",    delta="$324K stranded risk", delta_color="inverse")

    st.markdown("---")

    # Module cards
    st.markdown('<div class="section-label">THE FOUR MODULES</div>', unsafe_allow_html=True)
    m1,m2,m3,m4 = st.columns(4)
    modules_info = [
        ("01", "MRP Engine", "Explodes your BOM, offsets lead times per SAP MD01 logic, and generates an order schedule with past-due exception flags.", ["CS03","MD01","MD06","MM02"]),
        ("02", "PPAP Tracker", "10-element AIAG PPAP 4th Edition tracker per supplier. Scores readiness 0–100%. Below 50% triggers SCAR recommendation.", ["AIAG PPAP","Section 2.1–2.10"]),
        ("03", "SPC Charts", "Xbar-R and p-control charts using AIAG SPC manual constants. Out-of-control points flagged in red with immediate action prompts.", ["AIAG SPC","A2/D3/D4","Xbar-R"]),
        ("04", "Change Action", "Models engineering change impact: stranded inventory value, new-part order date, production gap risk, and annual cost savings.", ["ECO","SAP MB52","ME2M","MD04"]),
    ]
    for col, (num, title, desc, tags) in zip([m1,m2,m3,m4], modules_info):
        tag_html = "".join([f'<span class="sap-tag">{t}</span>' for t in tags])
        col.markdown(
            f'<div class="module-card">'
            f'<div class="module-number">{num}</div>'
            f'<div class="module-title">{title}</div>'
            f'<div class="module-desc">{desc}</div>'
            f'<div style="margin-top:10px">{tag_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("""
<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px 20px;font-size:0.82rem;color:#64748b">
<strong style="color:#1a1f2e">Demo data</strong> — All data is synthetically generated to replicate realistic pre-SOP scenarios in automotive EV assembly. BOM structure mirrors a battery pack program. PPAP statuses reflect typical supplier readiness at SOP minus 60 days. SPC data includes seeded out-of-control points at known subgroups to simulate real process deviations. Select any module in the sidebar to explore.
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MODULE: MRP ENGINE
# ══════════════════════════════════════════════════════════════════════════════
elif "MRP" in module:
    st.markdown('<div class="section-label">MODULE 01</div>', unsafe_allow_html=True)
    st.markdown("## MRP Simulation Engine")
    st.markdown("""
<div style="background:#fff;border:1px solid #e2e8f0;border-left:3px solid #2563eb;border-radius:10px;padding:14px 20px;font-size:0.85rem;line-height:1.7;color:#374151;margin-bottom:16px">
<strong>What this replicates:</strong> SAP's MRP run (MD01/MD02) explodes a Bill of Materials, offsets each component's lead time backward from the finished goods due date, and generates a "latest order by" date per component. When that date has passed, SAP issues an exception message in the MRP controller's work queue (MD06). This module replicates that logic on any BOM you define.
<br><br>
<strong>Why it matters:</strong> Stale lead time fields in SAP MM (MM02) are one of the most common causes of MRP planning deviations. If the planned delivery time is wrong, the order schedule is wrong, and parts arrive late.
</div>
""", unsafe_allow_html=True)

    st.subheader("Step 1 — Define your Bill of Materials")

    default_bom = pd.DataFrame({
        "Component":        ["Battery Pack","Motor Assembly","Chassis Frame","Battery Cell","Battery Housing","Stator","Rotor","Frame Rail","Cross Member"],
        "Parent":           ["Finished Good","Finished Good","Finished Good","Battery Pack","Battery Pack","Motor Assembly","Motor Assembly","Chassis Frame","Chassis Frame"],
        "Qty Per":          [1,1,1,1,1,1,1,2,3],
        "Lead Time (days)": [14,21,10,45,20,30,25,15,12],
    })
    bom_df = st.data_editor(default_bom, num_rows="dynamic", use_container_width=True)

    st.subheader("Step 2 — Enter Demand")
    col1, col2 = st.columns(2)
    demand_qty = col1.number_input("Finished Goods Required (units)", min_value=1, value=10)
    due_date   = col2.date_input("Required By Date", value=datetime.today() + timedelta(days=60))

    if st.button("Generate MRP Schedule", type="primary"):
        schedule = []
        for _, row in bom_df.iterrows():
            total_qty  = demand_qty * row["Qty Per"]
            order_date = pd.to_datetime(due_date) - timedelta(days=int(row["Lead Time (days)"]))
            schedule.append({
                "Component":        row["Component"],
                "Parent":           row["Parent"],
                "Qty Needed":       total_qty,
                "Lead Time (days)": row["Lead Time (days)"],
                "Order By":         order_date.strftime("%Y-%m-%d"),
                "Due Date":         str(due_date),
                "Status":           "On Track" if order_date > pd.Timestamp.today() else "⚠️ Past Due",
            })
        st.session_state["schedule_df"] = pd.DataFrame(schedule)

    if "schedule_df" in st.session_state:
        sdf = st.session_state["schedule_df"]

        def highlight_status(val):
            if "Past Due" in str(val):
                return "background:#fef2f2;color:#dc2626;font-weight:600"
            return "background:#f0fdf4;color:#16a34a;font-weight:600"

        st.dataframe(
            sdf.style.map(highlight_status, subset=["Status"]),
            use_container_width=True,
        )
        past_due = sdf[sdf["Status"].str.contains("Past Due")]
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Components", len(sdf))
        c2.metric("Past Due Order Dates", len(past_due), delta="Immediate action" if len(past_due)>0 else "All clear", delta_color="inverse" if len(past_due)>0 else "normal")
        c3.metric("On Track", len(sdf)-len(past_due))

        if len(past_due)>0:
            st.warning(f"⚠️ {len(past_due)} component(s) need to be ordered immediately. In SAP, these would appear as exception messages in the MRP controller's work queue (MD06).")
        else:
            st.success("✅ All components can be ordered in time to meet your due date.")

        # Gantt-style chart
        gantt_data = []
        today = pd.Timestamp.today()
        for _, r in sdf.iterrows():
            gantt_data.append({
                "Component": r["Component"],
                "Start": r["Order By"],
                "End": r["Due Date"],
                "Status": r["Status"],
            })
        gantt_df = pd.DataFrame(gantt_data)
        fig_gantt = px.timeline(
            gantt_df, x_start="Start", x_end="End", y="Component",
            color="Status",
            color_discrete_map={"On Track": "#22c55e", "⚠️ Past Due": "#ef4444"},
            title="Order Window per Component",
        )
        fig_gantt.update_layout(**LIGHT, height=360)
        fig_gantt.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_gantt, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: PPAP TRACKER
# ══════════════════════════════════════════════════════════════════════════════
elif "PPAP" in module:
    st.markdown('<div class="section-label">MODULE 02</div>', unsafe_allow_html=True)
    st.markdown("## PPAP Readiness Tracker")
    st.markdown("""
<div style="background:#fff;border:1px solid #e2e8f0;border-left:3px solid #2563eb;border-radius:10px;padding:14px 20px;font-size:0.85rem;line-height:1.7;color:#374151;margin-bottom:16px">
<strong>What this replicates:</strong> PPAP (Production Part Approval Process) is the automotive industry standard (AIAG 4th Edition) for confirming a supplier's production process can consistently meet engineering requirements before Start of Production. Each of the 10 elements must be submitted and approved by the customer before a part can be run in production.
<br><br>
<strong>Why it matters:</strong> An unapproved PPAP element blocks production readiness. A rejected PSW (Part Submission Warrant) — even with 9 of 10 elements approved — means the supplier cannot ship conforming parts. OEM supplier portals (Stellantis, Ford, GM) track exactly these statuses. The risk score below matches how those portals classify readiness.
</div>
""", unsafe_allow_html=True)

    ppap_elements = [
        "Design Records","Engineering Change Documents","Customer Engineering Approval",
        "Design FMEA","Process Flow Diagram","Process FMEA",
        "Control Plan","MSA Studies","Dimensional Results","Initial Process Studies (SPC)",
    ]
    suppliers = ["Supplier A — Battery Cells","Supplier B — Motor Stator","Supplier C — Chassis Rails","Supplier D — Battery Housing","Supplier E — Rotor Assembly"]
    status_options = ["Not Started","In Progress","Submitted","Approved","Rejected"]
    score_map = {"Approved":1.0,"Submitted":0.7,"In Progress":0.4,"Not Started":0.0,"Rejected":-0.5}

    selected_supplier = st.selectbox("Select Supplier", suppliers)

    if "ppap_data" not in st.session_state:
        st.session_state.ppap_data = {}
    if selected_supplier not in st.session_state.ppap_data:
        np.random.seed(hash(selected_supplier) % 100)
        st.session_state.ppap_data[selected_supplier] = {
            el: np.random.choice(status_options, p=[0.1,0.2,0.2,0.4,0.1])
            for el in ppap_elements
        }

    st.markdown("---")
    status_colors = {"Approved":"#22c55e","Submitted":"#3b82f6","In Progress":"#f59e0b","Not Started":"#94a3b8","Rejected":"#ef4444"}

    cols_h = st.columns([4,3,1,3])
    cols_h[0].markdown('<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;font-weight:600">PPAP Element</div>', unsafe_allow_html=True)
    cols_h[1].markdown('<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;font-weight:600">Status</div>', unsafe_allow_html=True)
    cols_h[2].markdown('<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;font-weight:600"></div>', unsafe_allow_html=True)
    cols_h[3].markdown('<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;font-weight:600">AIAG Reference</div>', unsafe_allow_html=True)

    aiag_refs = ["§2.1","§2.2","§2.3 (if applicable)","§2.4","§2.5","§2.6","§2.7","§2.8","§2.9","§2.10"]
    statuses = []
    for i, element in enumerate(ppap_elements):
        c1,c2,c3,c4 = st.columns([4,3,1,3])
        c1.markdown(f'<p style="font-size:0.85rem;margin:8px 0;color:#1a1f2e">{element}</p>', unsafe_allow_html=True)
        current = st.session_state.ppap_data[selected_supplier][element]
        new_status = c2.selectbox(
            "", status_options, index=status_options.index(current),
            key=f"{selected_supplier}_{element}", label_visibility="collapsed",
        )
        st.session_state.ppap_data[selected_supplier][element] = new_status
        statuses.append(new_status)
        dot_color = status_colors.get(new_status,"#94a3b8")
        c3.markdown(f'<div style="width:10px;height:10px;border-radius:50%;background:{dot_color};margin-top:12px"></div>', unsafe_allow_html=True)
        c4.markdown(f'<p style="font-size:0.78rem;color:#94a3b8;margin:10px 0;font-family:DM Mono,monospace">{aiag_refs[i]}</p>', unsafe_allow_html=True)

    st.markdown("---")
    raw_score = sum(score_map[s] for s in statuses)
    pct = max(0, raw_score / len(ppap_elements) * 100)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("PPAP Readiness Score", f"{pct:.0f}%")
    c2.metric("Approved",    statuses.count("Approved"))
    c3.metric("Rejected",    statuses.count("Rejected"),  delta="SCAR required" if statuses.count("Rejected")>0 else "None", delta_color="inverse" if statuses.count("Rejected")>0 else "normal")
    c4.metric("Not Started", statuses.count("Not Started"), delta="At risk" if statuses.count("Not Started")>2 else "OK", delta_color="inverse" if statuses.count("Not Started")>2 else "normal")

    st.progress(int(pct))

    if pct >= 80:
        st.success("✅ LOW RISK — Supplier is on track for PPAP approval. No escalation required.")
    elif pct >= 50:
        st.warning("⚠️ MEDIUM RISK — Multiple elements need attention before SOP. Schedule supplier review.")
    else:
        st.error("🔴 HIGH RISK — SCAR escalation recommended. Escalate to Supplier Quality Engineering team immediately. Below 50% readiness with SOP approaching is a production risk event.")

    # Radar chart of element status
    status_vals = [score_map[s]*100 for s in statuses]
    short_labels = ["Design Rec.","Eng. Change","Cust. Appr.","Design FMEA",
                    "Proc. Flow","Proc. FMEA","Control Plan","MSA","Dim. Results","SPC Studies"]
    fig_radar = go.Figure(go.Scatterpolar(
        r=status_vals + [status_vals[0]],
        theta=short_labels + [short_labels[0]],
        fill="toself", fillcolor="rgba(37,99,235,0.12)",
        line=dict(color="#2563eb", width=2),
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0,100], tickfont=dict(size=9,color="#94a3b8"), gridcolor="#e2e8f0"),
            angularaxis=dict(tickfont=dict(size=9,color="#374151")),
            bgcolor="#fff",
        ),
        paper_bgcolor="#f7f8fa", showlegend=False, height=360,
        margin=dict(t=20,b=20,l=40,r=40),
        title=dict(text="PPAP Element Readiness", font=dict(size=13,color="#1a1f2e")),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: SPC CHARTS
# ══════════════════════════════════════════════════════════════════════════════
elif "SPC" in module:
    st.markdown('<div class="section-label">MODULE 03</div>', unsafe_allow_html=True)
    st.markdown("## Statistical Process Control (SPC) Dashboards")
    st.markdown("""
<div style="background:#fff;border:1px solid #e2e8f0;border-left:3px solid #2563eb;border-radius:10px;padding:14px 20px;font-size:0.85rem;line-height:1.7;color:#374151;margin-bottom:16px">
<strong>What this replicates:</strong> AIAG SPC Reference Manual (2nd Edition) Xbar-R and p-chart methodology. In automotive manufacturing, SPC sign-off is a PPAP element (Initial Process Studies, §2.10). A supplier must demonstrate their production process is statistically in control before shipping conforming parts. Control limits are calculated using A2, D3, D4 constants from the AIAG SPC table.
<br><br>
<strong>Why it matters:</strong> Out-of-control points are not defects — they're signals that the process has shifted and defects are coming. Identifying them early allows the supplier to stop production, investigate root cause, and correct before shipping bad parts. In a live environment, this data feeds from CMM outputs into SAP QM module.
</div>
""", unsafe_allow_html=True)

    chart_type = st.radio("Chart Type", ["Xbar-R Chart (variable / dimensional data)", "p-Chart (attribute / defect count data)"], horizontal=True)
    st.markdown("---")

    if "Xbar" in chart_type:
        st.subheader("Xbar-R Chart — Process Mean & Range")
        c1,c2,c3 = st.columns(3)
        n_sg   = c1.slider("Subgroups",      10, 30, 20)
        n_size = c2.slider("Subgroup size n", 2,  6,  4)
        pmean  = c3.number_input("Target Mean", value=18.0)

        A2 = {2:1.880,3:1.023,4:0.729,5:0.577,6:0.483}
        D3 = {2:0,3:0,4:0,5:0,6:0}
        D4 = {2:3.267,3:2.574,4:2.282,5:2.115,6:2.004}

        np.random.seed(42)
        data = np.random.normal(pmean, 0.3, (n_sg, n_size))
        data[int(n_sg*0.4)] += 1.2
        data[int(n_sg*0.75)] -= 1.0

        xbar = data.mean(axis=1); R = data.max(axis=1)-data.min(axis=1)
        xbar_bar = xbar.mean(); R_bar = R.mean()
        UCL_x = xbar_bar + A2[n_size]*R_bar; LCL_x = xbar_bar - A2[n_size]*R_bar
        UCL_r = D4[n_size]*R_bar;             LCL_r = D3[n_size]*R_bar
        ooc_x = [(i+1) for i,v in enumerate(xbar) if v>UCL_x or v<LCL_x]
        ooc_r = [(i+1) for i,v in enumerate(R)    if v>UCL_r]

        x_colors = ["#ef4444" if (v>UCL_x or v<LCL_x) else "#2563eb" for v in xbar]
        fig_x = go.Figure()
        fig_x.add_trace(go.Scatter(x=list(range(1,n_sg+1)),y=xbar,mode="lines+markers",
                                    marker=dict(color=x_colors,size=8),line=dict(color="#2563eb"),name="Xbar"))
        for y,nm,clr,dash in [(UCL_x,f"UCL={UCL_x:.3f}","#ef4444","dash"),(xbar_bar,f"CL={xbar_bar:.3f}","#22c55e","solid"),(LCL_x,f"LCL={LCL_x:.3f}","#ef4444","dash")]:
            fig_x.add_hline(y=y,line_dash=dash,line_color=clr,annotation_text=nm,annotation_position="right")
        fig_x.update_layout(**LIGHT,height=300,title="Xbar Chart — Subgroup Means",xaxis_title="Subgroup",yaxis_title="Mean")
        st.plotly_chart(fig_x, use_container_width=True)

        r_colors = ["#ef4444" if v>UCL_r else "#16a34a" for v in R]
        fig_r = go.Figure()
        fig_r.add_trace(go.Scatter(x=list(range(1,n_sg+1)),y=R,mode="lines+markers",
                                    marker=dict(color=r_colors,size=8),line=dict(color="#16a34a"),name="Range"))
        for y,nm,clr,dash in [(UCL_r,f"UCL={UCL_r:.3f}","#ef4444","dash"),(R_bar,f"CL={R_bar:.3f}","#22c55e","solid")]:
            fig_r.add_hline(y=y,line_dash=dash,line_color=clr,annotation_text=nm,annotation_position="right")
        fig_r.update_layout(**LIGHT,height=260,title="R Chart — Subgroup Ranges",xaxis_title="Subgroup",yaxis_title="Range")
        st.plotly_chart(fig_r, use_container_width=True)

        c1,c2,c3 = st.columns(3)
        c1.metric("Out-of-Control (Xbar)",f"{len(ooc_x)} points",delta="Investigate" if ooc_x else "In control",delta_color="inverse" if ooc_x else "normal")
        c2.metric("Out-of-Control (R)",   f"{len(ooc_r)} points",delta="Investigate" if ooc_r else "In control",delta_color="inverse" if ooc_r else "normal")
        c3.metric("Process Capability (est.)",f"{'Not capable' if ooc_x else 'In control'}")
        if ooc_x:
            st.error(f"🔴 Subgroup(s) {ooc_x} are out of control. Stop production on this characteristic and initiate root cause analysis. This must be resolved before PPAP §2.10 sign-off.")
    else:
        st.subheader("p-Chart — Proportion Defective")
        c1,c2 = st.columns(2)
        n_b = c1.slider("Batches",        10, 30, 20)
        b_s = c2.slider("Parts per batch", 50, 200, 100)

        np.random.seed(99)
        defects = np.random.binomial(b_s, 0.03, n_b)
        defects[int(n_b*0.35)] = int(b_s*0.12)
        defects[int(n_b*0.70)] = int(b_s*0.10)

        p_i = defects/b_s; p_bar = defects.sum()/(n_b*b_s)
        UCL_p = p_bar + 3*np.sqrt(p_bar*(1-p_bar)/b_s)
        LCL_p = max(0, p_bar - 3*np.sqrt(p_bar*(1-p_bar)/b_s))

        p_colors = ["#ef4444" if (p>UCL_p or p<LCL_p) else "#7c3aed" for p in p_i]
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=list(range(1,n_b+1)),y=p_i,mode="lines+markers",
                                    marker=dict(color=p_colors,size=8),line=dict(color="#7c3aed"),name="Defect rate"))
        for y,nm,clr,dash in [(UCL_p,f"UCL={UCL_p:.3f}","#ef4444","dash"),(p_bar,f"CL={p_bar:.3f}","#22c55e","solid"),(LCL_p,f"LCL={LCL_p:.3f}","#ef4444","dash")]:
            fig_p.add_hline(y=y,line_dash=dash,line_color=clr,annotation_text=nm,annotation_position="right")
        fig_p.update_layout(**LIGHT,height=400,title="p-Chart — Proportion Defective",xaxis_title="Batch",yaxis_title="Defect Rate",yaxis_tickformat=".1%")
        st.plotly_chart(fig_p, use_container_width=True)

        ooc = sum(1 for p in p_i if p>UCL_p or p<LCL_p)
        c1,c2,c3 = st.columns(3)
        c1.metric("Avg Defect Rate",f"{p_bar:.1%}")
        c2.metric("OOC Batches",ooc,delta="Investigate" if ooc>0 else "In control",delta_color="inverse" if ooc>0 else "normal")
        c3.metric("Total Defects",int(defects.sum()))
        if ooc>0:
            st.error(f"🔴 {ooc} batch(es) out of control. Initiate supplier failure analysis. This finding must be documented in PPAP §2.10 and will delay PSW approval until root cause is corrected.")

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: CHANGE ACTION ANALYZER
# ══════════════════════════════════════════════════════════════════════════════
elif "Change" in module:
    st.markdown('<div class="section-label">MODULE 04</div>', unsafe_allow_html=True)
    st.markdown("## Change Action (CA) Impact Analyzer")
    st.markdown("""
<div style="background:#fff;border:1px solid #e2e8f0;border-left:3px solid #2563eb;border-radius:10px;padding:14px 20px;font-size:0.85rem;line-height:1.7;color:#374151;margin-bottom:16px">
<strong>What this replicates:</strong> When engineering issues a Change Order (ECO) for a part supersession, the planning team must simultaneously: (1) determine how much old inventory will be stranded, (2) calculate the latest possible date to place the first PO for the new part without creating a production gap, and (3) quantify the unit cost impact. Missing this window means either stranded obsolete inventory or a production line stoppage.
<br><br>
<strong>Why it matters:</strong> Engineering changes are routine in automotive programs. The planning team at an OEM manages dozens of active change orders simultaneously. Getting the timing wrong costs $108K–$500K+ in stranded inventory write-offs or stoppage penalties.
</div>
""", unsafe_allow_html=True)

    st.subheader("Enter Change Action Details")
    st.markdown("""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 16px;font-size:0.8rem;color:#64748b;margin-bottom:16px">
<strong>Demo scenario pre-loaded:</strong> Battery Cell v1.0 → v2.0 supersession. 2,400 units on hand + 800 on order. 80 units/day demand. Change effective in 30 days.
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    part_name         = col1.text_input("Part Name", value="Battery Cell v1.0")
    old_part_cost     = col1.number_input("Old Part Unit Cost ($)", value=45.00, step=0.5)
    current_inventory = col1.number_input("Current Inventory on Hand (units)", value=2400)
    on_order_qty      = col1.number_input("Qty Currently On Order (units)", value=800)
    daily_demand      = col2.number_input("Daily Demand Rate (units/day)", value=80)
    new_part_cost     = col2.number_input("New Part Unit Cost ($)", value=42.00, step=0.5)
    new_part_lead     = col2.number_input("New Part Lead Time (days)", value=45)
    ppap_days         = col2.number_input("PPAP Qualification Days (new supplier)", value=90,
                                           help="Days to qualify new supplier. Includes PPAP approval window.")
    ca_effective_date = col1.date_input("Engineering Change Effective Date",
                                         value=datetime.today() + timedelta(days=30))

    if st.button("Run Change Action Analysis", type="primary"):
        today   = datetime.today()
        ca_date = datetime.combine(ca_effective_date, datetime.min.time())

        days_until_ca      = max(0,(ca_date - today).days)
        total_old_stock    = current_inventory + on_order_qty
        consumed_before_ca = min(total_old_stock, daily_demand * days_until_ca)
        stranded_units     = max(0, total_old_stock - consumed_before_ca)
        stranded_value     = stranded_units * old_part_cost

        new_part_order_date = ca_date - timedelta(days=int(new_part_lead))
        days_to_order_new   = max(0,(new_part_order_date - today).days)

        # Production gap calculation (FactorySync's unique contribution)
        runout_date  = today + timedelta(days=total_old_stock / max(daily_demand,1))
        new_part_arrival = new_part_order_date + timedelta(days=int(new_part_lead))
        gap_days     = (runout_date - new_part_arrival).days

        daily_savings   = (old_part_cost - new_part_cost) * daily_demand
        annual_savings  = daily_savings * 365

        # PPAP qualification check
        ppap_complete_date = today + timedelta(days=int(ppap_days))
        ppap_ready = ppap_complete_date <= new_part_arrival

        st.markdown("---")
        st.subheader("Analysis Results")

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Days Until Change",     days_until_ca)
        c2.metric("Stranded Units",        f"{stranded_units:,}")
        c3.metric("Obsolescence Risk",     f"${stranded_value:,.0f}",
                  delta="Write-off risk" if stranded_value>0 else "None",delta_color="inverse")
        c4.metric("Annual Savings (new)",  f"${annual_savings:,.0f}",delta="Post-transition")

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Order New Part By",     new_part_order_date.strftime("%b %d, %Y"))
        c2.metric("Days Left to Order",    days_to_order_new,
                  delta="URGENT" if days_to_order_new<=7 else ("Soon" if days_to_order_new<=14 else "On track"),
                  delta_color="inverse" if days_to_order_new<=14 else "normal")
        c3.metric("PPAP Ready Before Arrival", "✅ Yes" if ppap_ready else "⚠️ No",
                  delta="On track" if ppap_ready else "Risk — qualify earlier",
                  delta_color="normal" if ppap_ready else "inverse")
        c4.metric("Production Gap Risk",   f"{abs(gap_days)} days {'gap' if gap_days<0 else 'buffer'}",
                  delta="⚠️ GAP — expedite order" if gap_days<0 else "Buffer exists",
                  delta_color="inverse" if gap_days<0 else "normal")

        if gap_days < 0:
            st.error(f"🔴 PRODUCTION GAP DETECTED: If you order the new part today, it will arrive {abs(gap_days)} days after your old inventory runs out. Expedite the PO or arrange bridge supply from current supplier.")
        elif days_to_order_new <= 7:
            st.warning(f"⚠️ ORDER NEW PART IMMEDIATELY — {days_to_order_new} days remaining in order window.")
        else:
            st.success(f"✅ Order window open for {days_to_order_new} more days. Place PO by {new_part_order_date.strftime('%B %d, %Y')}.")

        if not ppap_ready:
            st.warning(f"⚠️ PPAP TIMING RISK: New supplier qualification ({ppap_days} days) completes {ppap_complete_date.strftime('%b %d')} but new parts arrive {new_part_arrival.strftime('%b %d')}. Start PPAP qualification now.")

        # Burn-down chart
        days_range = range(0, int(total_old_stock/max(daily_demand,1)) + days_until_ca + 10)
        inv_levels = [max(0, total_old_stock - daily_demand*d) for d in days_range]
        fig_bd = go.Figure()
        fig_bd.add_trace(go.Scatter(x=list(days_range), y=inv_levels, mode="lines",
                                     fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
                                     line=dict(color="#2563eb"), name="Old Part Inventory"))
        fig_bd.add_vline(x=days_until_ca, line_dash="dash", line_color="#ef4444",
                         annotation_text="Change effective", annotation_position="top right")
        fig_bd.add_vline(x=days_to_order_new, line_dash="dot", line_color="#f59e0b",
                         annotation_text="Order new part by", annotation_position="top left")
        if stranded_units > 0:
            fig_bd.add_hline(y=stranded_units, line_dash="dot", line_color="#f59e0b",
                             annotation_text=f"Stranded: {stranded_units:,} units = ${stranded_value:,.0f}",
                             annotation_position="right")
        fig_bd.update_layout(**LIGHT, height=360, title="Old Part Inventory Burn-Down",
                              xaxis_title="Days from Today", yaxis_title="Units on Hand")
        st.plotly_chart(fig_bd, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='font-size:0.75rem;color:#94a3b8;text-align:center'>"
    "FactorySync · Supplier Industrialization & MRP Platform · "
    "AIAG PPAP 4th Ed. · AIAG SPC Manual · SAP S/4HANA data model · "
    "Built by Rutwik Satish · MS Engineering Management, Northeastern University"
    "</p>",
    unsafe_allow_html=True,
)
