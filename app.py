# ============================================================
# FACTORYSYNC — Supplier Industrialization & MRP Platform
# Built with Streamlit + Pandas + Plotly + NumPy
# ============================================================
# HOW TO RUN:
#   1. Install libraries: pip install streamlit pandas plotly numpy scipy
#   2. Save this file as app.py
#   3. In terminal: streamlit run app.py
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ── App-wide config ──────────────────────────────────────────
st.set_page_config(
    page_title="FactorySync",
    page_icon="🏭",
    layout="wide"
)

# ── Sidebar navigation ───────────────────────────────────────
st.sidebar.title("🏭 FactorySync")
st.sidebar.markdown("Supplier Industrialization & MRP Platform")
st.sidebar.markdown("---")

module = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home",
        "📦 MRP Engine",
        "✅ PPAP Tracker",
        "📊 SPC Dashboards",
        "🔄 Change Action Analyzer"
    ]
)

# ── Data source banner (shown on all pages) ──────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("#### 📂 Data Source")
    st.info(
        "All data in this platform is **simulated** for demonstration purposes. "
        "It replicates the structure and failure modes of real SAP S/4HANA supply chain environments. "
        "No proprietary or confidential data is used.",
        icon="ℹ️"
    )
    st.markdown(
        "**Data model based on:**\n"
        "- SAP S/4HANA MM / MRP module logic\n"
        "- AIAG PPAP 4th Edition standard\n"
        "- AIAG SPC reference manual\n"
        "- Industry-standard BOM structures (automotive EV assembly)\n"
    )

# ============================================================
# HOME PAGE
# ============================================================
if module == "🏠 Home":
    st.title("🏭 FactorySync")
    st.subheader("Supplier Industrialization & MRP Simulation Platform")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Suppliers", "15")
    col2.metric("PPAP Completion", "68%")
    col3.metric("Parts In Control", "11 / 15")
    col4.metric("Open Change Actions", "3")

    st.markdown("---")

    st.markdown("""
    ### What this tool does
    FactorySync replicates the core workflows of a Supplier Industrialization team:

    - **MRP Engine** — Explodes your Bill of Materials, offsets lead times, and generates an order schedule
    - **PPAP Tracker** — Tracks Production Part Approval Process milestones and supplier risk scores
    - **SPC Dashboards** — Monitors process quality with control charts and flags deviations
    - **Change Action Analyzer** — Models obsolescence risk and ramp timing when engineering changes are introduced

    Use the sidebar to navigate between modules.
    """)

    st.markdown("---")
    st.markdown("### 📂 Data Source & Methodology")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **What data powers this tool?**

        All data is synthetically generated to replicate realistic manufacturing
        supply chain scenarios. The BOM structure, lead times, PPAP statuses,
        and SPC measurements are modelled after:

        - Automotive EV battery pack assembly (multi-level BOM)
        - Typical SAP S/4HANA MRP and MM module data structures
        - AIAG PPAP 4th Edition element requirements
        - Industry-standard SPC control chart parameters (AIAG SPC manual)
        - Real-world engineering change management timelines
        """)
    with c2:
        st.markdown("""
        **Why simulate rather than use real data?**

        Real SAP production data is proprietary and confidential.
        This simulation is designed to faithfully replicate the *structure*
        and *failure modes* of live ERP environments — including:

        - Stale lead time fields causing MRP planning deviations
        - Incomplete PPAP approvals blocking production readiness
        - Out-of-control SPC points triggering SCAR escalations
        - Engineering changes creating obsolescence risk in inventory

        These are the exact scenarios encountered in supplier industrialization
        roles at automotive OEMs and Tier 1 suppliers.
        """)

    st.markdown("---")
    st.markdown("### 🔍 Preview: Sample Data Across Modules")

    preview_tab1, preview_tab2, preview_tab3, preview_tab4 = st.tabs([
        "BOM / MRP Data", "PPAP Data", "SPC Data", "Change Action Data"
    ])

    with preview_tab1:
        st.markdown("**Sample Bill of Materials — EV Battery Pack Assembly**")
        preview_bom = pd.DataFrame({
            "Component":        ["Battery Pack", "Motor Assembly", "Chassis Frame",
                                 "Battery Cell", "Battery Housing", "Stator", "Rotor",
                                 "Frame Rail", "Cross Member"],
            "Parent":           ["Finished Good", "Finished Good", "Finished Good",
                                 "Battery Pack", "Battery Pack", "Motor Assembly", "Motor Assembly",
                                 "Chassis Frame", "Chassis Frame"],
            "Qty Per Unit":     [1, 1, 1, 1, 1, 1, 1, 2, 3],
            "Lead Time (days)": [14, 21, 10, 45, 20, 30, 25, 15, 12],
            "Supplier":         ["Internal", "Internal", "Internal",
                                 "Supplier A", "Supplier B", "Supplier C",
                                 "Supplier D", "Supplier E", "Supplier E"],
            "Data Source":      ["SAP MM"] * 9
        })
        st.dataframe(preview_bom, use_container_width=True, hide_index=True)
        st.caption("Source: Simulated SAP S/4HANA material master and BOM data. "
                   "Structure based on automotive EV assembly BOM conventions.")

    with preview_tab2:
        st.markdown("**Sample PPAP Status Matrix — 5 Suppliers × 10 Elements**")
        np.random.seed(7)
        status_opts = ["Not Started", "In Progress", "Submitted", "Approved", "Rejected"]
        ppap_elements_short = ["Design Records", "Eng. Change Docs", "FMEA",
                                "Process Flow", "Control Plan", "MSA Studies",
                                "Dimensional Results", "SPC Studies", "PSW", "Customer Approval"]
        preview_ppap = pd.DataFrame(
            {el: np.random.choice(status_opts, 5, p=[0.1,0.2,0.2,0.4,0.1])
             for el in ppap_elements_short},
            index=["Supplier A", "Supplier B", "Supplier C", "Supplier D", "Supplier E"]
        )
        st.dataframe(preview_ppap, use_container_width=True)
        st.caption("Source: Simulated PPAP element status data based on AIAG PPAP 4th Edition. "
                   "Status values represent typical supplier readiness profiles at SOP minus 60 days.")

    with preview_tab3:
        st.markdown("**Sample SPC Measurement Data — Battery Cell Diameter (mm)**")
        np.random.seed(42)
        spc_data = []
        for i in range(1, 21):
            measurements = np.random.normal(18.0, 0.3, 4)
            if i == 8:  measurements += 1.2
            if i == 15: measurements -= 1.0
            spc_data.append({
                "Subgroup": i,
                "M1": round(measurements[0], 3),
                "M2": round(measurements[1], 3),
                "M3": round(measurements[2], 3),
                "M4": round(measurements[3], 3),
                "X-bar": round(measurements.mean(), 3),
                "Range": round(measurements.max() - measurements.min(), 3),
                "Status": "OUT OF CONTROL" if i in [8, 15] else "In Control"
            })
        preview_spc = pd.DataFrame(spc_data)
        st.dataframe(preview_spc, use_container_width=True, hide_index=True)
        st.caption("Source: Simulated dimensional measurement data. "
                   "Control limits calculated per AIAG SPC manual using standard A2/D3/D4 constants. "
                   "Subgroups 8 and 15 are seeded as out-of-control points.")

    with preview_tab4:
        st.markdown("**Sample Change Action Scenario — Battery Cell v1.0 → v2.0**")
        preview_ca = pd.DataFrame({
            "Parameter": [
                "Old Part", "New Part", "Engineering Change Date",
                "Current Inventory on Hand", "Qty On Order",
                "Daily Demand Rate", "Old Part Cost", "New Part Cost",
                "New Part Lead Time", "Stranded Risk",
                "Recommended Order Date (new part)", "Annual Cost Saving"
            ],
            "Value": [
                "Battery Cell v1.0", "Battery Cell v2.0", "May 6, 2026",
                "2,400 units", "800 units",
                "80 units/day", "$45.00", "$42.00",
                "45 days", "$108,000",
                "March 22, 2026", "$87,600/year"
            ],
            "Data Source": [
                "SAP MM", "SAP MM", "Engineering Change Order (ECO)",
                "SAP WM / Inventory", "SAP PO register",
                "SAP PP demand plan", "SAP MM pricing", "Supplier quote",
                "Supplier lead time register", "Calculated", "Calculated", "Calculated"
            ]
        })
        st.dataframe(preview_ca, use_container_width=True, hide_index=True)
        st.caption("Source: Simulated engineering change management scenario. "
                   "Mirrors real ECO workflows in automotive OEM environments where "
                   "part supersession triggers simultaneous obsolescence risk and new part ramp planning.")


# ============================================================
# MODULE 1: MRP ENGINE
# ============================================================
elif module == "📦 MRP Engine":
    st.title("📦 MRP Simulation Engine")
    st.markdown("Explode your Bill of Materials, apply lead times, and generate an order schedule.")

    with st.expander("📂 Data Source & Preview", expanded=False):
        st.markdown("""
        **Data model:** Simulated SAP S/4HANA MRP and MM module data.

        The BOM structure below replicates a multi-level automotive EV battery pack assembly.
        Lead times are representative of real Tier 1 and Tier 2 supplier relationships.
        The MRP logic — BOM explosion, lead time offsetting, order quantity calculation —
        mirrors the core planning mechanics of SAP's MRP run (MD01/MD02).

        **Key data fields:**
        - **Component / Parent** — SAP material master hierarchy (MM60 / CS03 BOM view)
        - **Qty Per** — Bill of Materials quantity per parent unit (SAP CS01)
        - **Lead Time (days)** — Planned delivery time from material master (SAP MM02, field: Planned Deliv. Time)

        **What the red flags mean:** If the order date required to meet your due date has already
        passed today, the component is flagged Past Due. In a live SAP environment this would
        trigger an exception message in the MRP controller's work queue (MD06).
        """)
        preview_bom = pd.DataFrame({
            "Component":        ["Battery Pack", "Motor Assembly", "Chassis Frame",
                                 "Battery Cell", "Battery Housing", "Stator", "Rotor",
                                 "Frame Rail", "Cross Member"],
            "Parent":           ["Finished Good", "Finished Good", "Finished Good",
                                 "Battery Pack", "Battery Pack", "Motor Assembly", "Motor Assembly",
                                 "Chassis Frame", "Chassis Frame"],
            "Qty Per Unit":     [1, 1, 1, 1, 1, 1, 1, 2, 3],
            "Lead Time (days)": [14, 21, 10, 45, 20, 30, 25, 15, 12],
            "SAP Transaction":  ["CS03", "CS03", "CS03", "MM02", "MM02",
                                 "MM02", "MM02", "MM02", "MM02"]
        })
        st.dataframe(preview_bom, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Step 1 — Define your Bill of Materials (BOM)")
    st.markdown("Each row = one component. Fill in the details below.")

    default_bom = pd.DataFrame({
        "Component":       ["Battery Pack", "Motor Assembly", "Chassis Frame",
                            "Battery Cell", "Battery Housing", "Stator", "Rotor",
                            "Frame Rail", "Cross Member"],
        "Parent":          ["Finished Good", "Finished Good", "Finished Good",
                            "Battery Pack", "Battery Pack", "Motor Assembly", "Motor Assembly",
                            "Chassis Frame", "Chassis Frame"],
        "Qty Per":         [1, 1, 1, 1, 1, 1, 1, 2, 3],
        "Lead Time (days)":[14, 21, 10, 45, 20, 30, 25, 15, 12]
    })

    bom_df = st.data_editor(default_bom, num_rows="dynamic", use_container_width=True)

    st.markdown("---")
    st.subheader("Step 2 — Enter Demand")

    col1, col2 = st.columns(2)
    demand_qty = col1.number_input("Finished Goods Required (units)", min_value=1, value=10)
    due_date   = col2.date_input("Required By Date",
                                  value=datetime.today() + timedelta(days=60))

    st.markdown("---")
    st.subheader("Step 3 — Order Schedule")

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
                # FIX: compare pd.Timestamp to pd.Timestamp (not datetime)
                "Status":           "On Track" if order_date > pd.Timestamp.today() else "⚠️ Past Due"
            })

        schedule_df = pd.DataFrame(schedule)

        def highlight_status(val):
            if "Past Due" in str(val):
                return "background-color: #fce8e8; color: #a32d2d"
            return "background-color: #eaf3de; color: #3b6d11"

        st.dataframe(
            schedule_df.style.map(highlight_status, subset=["Status"]),
            use_container_width=True
        )

        past_due = schedule_df[schedule_df["Status"].str.contains("Past Due")]
        st.metric("Parts with Past Due Order Dates", len(past_due))
        if len(past_due) > 0:
            st.warning(
                f"⚠️ {len(past_due)} component(s) need to be ordered immediately "
                f"to meet your due date. In SAP, these would appear as exception "
                f"messages in the MRP controller work queue (MD06)."
            )
        else:
            st.success("✅ All components can be ordered in time to meet your due date.")

        st.caption(
            "Data source: Simulated SAP S/4HANA MRP output. "
            "Order By dates are calculated by offsetting the due date by each component's "
            "Planned Delivery Time (SAP MM02). Status flags replicate SAP MRP exception messages."
        )


# ============================================================
# MODULE 2: PPAP TRACKER
# ============================================================
elif module == "✅ PPAP Tracker":
    st.title("✅ PPAP Readiness Tracker")
    st.markdown("Track Production Part Approval Process milestones across your supplier base.")

    with st.expander("📂 Data Source & Preview", expanded=False):
        st.markdown("""
        **Standard:** AIAG PPAP 4th Edition (Production Part Approval Process).
        PPAP is the automotive industry standard for validating that a supplier's
        production process can consistently meet engineering requirements before
        start of production (SOP).

        **Data model:** Each PPAP element represents a submission requirement.
        Status values (Not Started / In Progress / Submitted / Approved / Rejected)
        mirror the workflow states used in automotive OEM supplier portals
        (e.g. Stellantis Supply Chain Portal, Ford Supplier Portal, GM GPSC).

        **Risk score methodology:**
        Approved = 1.0 · Submitted = 0.7 · In Progress = 0.4 · Not Started = 0.0 · Rejected = −0.5
        Score is normalised to 0–100%. Below 50% triggers SCAR escalation recommendation.
        """)
        st.markdown("**Sample PPAP Status — Supplier A (Battery Cells)**")
        np.random.seed(1)
        status_opts = ["Not Started", "In Progress", "Submitted", "Approved", "Rejected"]
        ppap_preview = pd.DataFrame({
            "PPAP Element":  ["Design Records", "Eng. Change Docs", "Design FMEA",
                              "Process Flow", "Process FMEA", "Control Plan",
                              "MSA Studies", "Dimensional Results", "SPC Studies", "PSW"],
            "Status":        np.random.choice(status_opts, 10, p=[0.1,0.2,0.2,0.4,0.1]),
            "AIAG Reference":["Section 2.1","Section 2.2","Section 2.3","Section 2.4",
                              "Section 2.5","Section 2.6","Section 2.7","Section 2.8",
                              "Section 2.9","Section 2.10"]
        })
        st.dataframe(ppap_preview, use_container_width=True, hide_index=True)

    st.markdown("---")

    ppap_elements = [
        "Design Records", "Engineering Change Documents", "Customer Engineering Approval",
        "Design FMEA", "Process Flow Diagram", "Process FMEA",
        "Control Plan", "MSA Studies", "Dimensional Results", "Initial Process Studies (SPC)"
    ]
    suppliers = [
        "Supplier A — Battery Cells", "Supplier B — Motor Stator",
        "Supplier C — Chassis Rails", "Supplier D — Battery Housing",
        "Supplier E — Rotor Assembly"
    ]

    st.subheader("Select Supplier")
    selected_supplier = st.selectbox("Choose a supplier to review", suppliers)
    st.markdown("---")
    st.subheader(f"PPAP Checklist — {selected_supplier}")

    status_options = ["Not Started", "In Progress", "Submitted", "Approved", "Rejected"]

    if "ppap_data" not in st.session_state:
        st.session_state.ppap_data = {}

    if selected_supplier not in st.session_state.ppap_data:
        np.random.seed(hash(selected_supplier) % 100)
        st.session_state.ppap_data[selected_supplier] = {
            el: np.random.choice(status_options, p=[0.1, 0.2, 0.2, 0.4, 0.1])
            for el in ppap_elements
        }

    statuses = []
    cols_header = st.columns([3, 2, 1])
    cols_header[0].markdown("**PPAP Element**")
    cols_header[1].markdown("**Status**")
    cols_header[2].markdown("**Risk**")

    for element in ppap_elements:
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.markdown(element)
        current    = st.session_state.ppap_data[selected_supplier][element]
        new_status = col2.selectbox(
            "", status_options, index=status_options.index(current),
            key=f"{selected_supplier}_{element}", label_visibility="collapsed"
        )
        st.session_state.ppap_data[selected_supplier][element] = new_status
        statuses.append(new_status)

        if new_status == "Approved":       col3.markdown("🟢")
        elif new_status in ["Submitted", "In Progress"]: col3.markdown("🟡")
        elif new_status == "Rejected":     col3.markdown("🔴")
        else:                              col3.markdown("⚪")

    st.markdown("---")
    score_map  = {"Approved": 1.0, "Submitted": 0.7, "In Progress": 0.4,
                  "Not Started": 0.0, "Rejected": -0.5}
    raw_score  = sum(score_map[s] for s in statuses)
    pct        = max(0, raw_score / len(ppap_elements) * 100)

    col1, col2, col3 = st.columns(3)
    col1.metric("PPAP Completion Score", f"{pct:.0f}%")
    col2.metric("Elements Approved", statuses.count("Approved"))
    col3.metric("Elements Rejected", statuses.count("Rejected"))

    if pct >= 80:   st.success("✅ LOW RISK — Supplier is on track for PPAP approval.")
    elif pct >= 50: st.warning("⚠️ MEDIUM RISK — Several elements need attention before launch.")
    else:           st.error("🔴 HIGH RISK — SCAR recommended. Escalate to supplier quality team.")

    st.progress(int(pct))
    st.caption("Data source: Simulated PPAP status data. Standard: AIAG PPAP 4th Edition.")


# ============================================================
# MODULE 3: SPC DASHBOARDS
# ============================================================
elif module == "📊 SPC Dashboards":
    st.title("📊 Statistical Process Control (SPC) Dashboards")
    st.markdown("Monitor critical component quality using control charts. Flag process deviations in real time.")

    with st.expander("📂 Data Source & Preview", expanded=False):
        st.markdown("""
        **Standard:** AIAG SPC Reference Manual (2nd Edition).

        **Data model:** Simulated dimensional measurement data for a critical
        automotive component (Battery Cell diameter, target 18.0mm ± 1.5mm).
        Each subgroup contains 4 measurements taken at regular production intervals.

        **Control limit methodology:**
        - Xbar-R Chart: UCL/LCL calculated using A2, D3, D4 constants from AIAG SPC table
        - p-Chart: UCL/LCL calculated using 3-sigma binomial limits
        - Out-of-control points are seeded at subgroups 8 and 15 to simulate
          real process deviations (tool wear, operator change, incoming material shift)

        **In a live environment** this data would feed from CMM (Coordinate Measuring Machine)
        outputs or production line gauging systems, exported to SAP QM module.
        """)
        np.random.seed(42)
        spc_prev = []
        for i in range(1, 11):
            m = np.random.normal(18.0, 0.3, 4)
            if i == 8: m += 1.2
            spc_prev.append({
                "Subgroup": i, "M1": round(m[0],3), "M2": round(m[1],3),
                "M3": round(m[2],3), "M4": round(m[3],3),
                "X-bar": round(m.mean(),3), "Range": round(m.max()-m.min(),3),
                "Flag": "⚠️ OOC" if i == 8 else "✅"
            })
        st.dataframe(pd.DataFrame(spc_prev), use_container_width=True, hide_index=True)
        st.caption("Showing first 10 subgroups. Subgroup 8 is seeded out-of-control (+1.2mm shift).")

    st.markdown("---")
    chart_type = st.radio("Select Chart Type",
                          ["Xbar-R Chart (variable data)", "p-Chart (defect rate)"],
                          horizontal=True)
    st.markdown("---")

    if "Xbar" in chart_type:
        st.subheader("Xbar-R Chart — Process Mean & Range Control")
        st.markdown("""
        - **Xbar chart**: Tracks the *average* measurement of each subgroup. Is the process centered?
        - **R chart**: Tracks the *range* (max - min) of each subgroup. Is the process consistent?
        - **Red points** = out of control. Investigate immediately.
        """)

        col1, col2, col3 = st.columns(3)
        n_subgroups   = col1.slider("Number of Subgroups", 10, 30, 20)
        subgroup_size = col2.slider("Subgroup Size (n)", 2, 6, 4)
        process_mean  = col3.number_input("Target Process Mean", value=10.0)

        np.random.seed(42)
        data = np.random.normal(loc=process_mean, scale=0.5, size=(n_subgroups, subgroup_size))
        data[int(n_subgroups * 0.4)]  += 2.0
        data[int(n_subgroups * 0.75)] -= 1.8

        xbar = data.mean(axis=1)
        R    = data.max(axis=1) - data.min(axis=1)

        A2 = {2:1.880, 3:1.023, 4:0.729, 5:0.577, 6:0.483}
        D3 = {2:0, 3:0, 4:0, 5:0, 6:0}
        D4 = {2:3.267, 3:2.574, 4:2.282, 5:2.115, 6:2.004}

        n        = subgroup_size
        xbar_bar = xbar.mean()
        R_bar    = R.mean()
        UCL_xbar = xbar_bar + A2[n] * R_bar
        LCL_xbar = xbar_bar - A2[n] * R_bar
        UCL_R    = D4[n] * R_bar
        LCL_R    = D3[n] * R_bar

        colors_x = ["red" if (x > UCL_xbar or x < LCL_xbar) else "#185FA5" for x in xbar]
        fig_xbar = go.Figure()
        fig_xbar.add_trace(go.Scatter(
            x=list(range(1, n_subgroups+1)), y=xbar,
            mode="lines+markers",
            marker=dict(color=colors_x, size=9),
            line=dict(color="#185FA5"), name="Subgroup Mean"
        ))
        for y, name, color, dash in [
            (UCL_xbar, f"UCL = {UCL_xbar:.3f}", "red", "dash"),
            (xbar_bar, f"CL = {xbar_bar:.3f}", "green", "solid"),
            (LCL_xbar, f"LCL = {LCL_xbar:.3f}", "red", "dash"),
        ]:
            fig_xbar.add_hline(y=y, line_dash=dash, line_color=color,
                               annotation_text=name, annotation_position="right")
        fig_xbar.update_layout(title="Xbar Chart — Subgroup Means",
                               xaxis_title="Subgroup", yaxis_title="Mean", height=350)
        st.plotly_chart(fig_xbar, use_container_width=True)

        colors_r = ["red" if (r > UCL_R or r < LCL_R) else "#1D9E75" for r in R]
        fig_r = go.Figure()
        fig_r.add_trace(go.Scatter(
            x=list(range(1, n_subgroups+1)), y=R,
            mode="lines+markers",
            marker=dict(color=colors_r, size=9),
            line=dict(color="#1D9E75"), name="Subgroup Range"
        ))
        for y, name, color, dash in [
            (UCL_R, f"UCL = {UCL_R:.3f}", "red", "dash"),
            (R_bar, f"CL = {R_bar:.3f}", "green", "solid"),
        ]:
            fig_r.add_hline(y=y, line_dash=dash, line_color=color,
                            annotation_text=name, annotation_position="right")
        fig_r.update_layout(title="R Chart — Subgroup Ranges",
                            xaxis_title="Subgroup", yaxis_title="Range", height=300)
        st.plotly_chart(fig_r, use_container_width=True)

        ooc_xbar = sum(1 for x in xbar if x > UCL_xbar or x < LCL_xbar)
        ooc_r    = sum(1 for r in R if r > UCL_R)
        col1, col2 = st.columns(2)
        col1.metric("Out-of-Control Points (Xbar)", ooc_xbar,
                    delta="Investigate" if ooc_xbar > 0 else "In Control",
                    delta_color="inverse")
        col2.metric("Out-of-Control Points (R)", ooc_r,
                    delta="Investigate" if ooc_r > 0 else "In Control",
                    delta_color="inverse")
        st.caption("Data source: Simulated measurement data. "
                   "Constants A2/D3/D4 from AIAG SPC Reference Manual Table C.")

    else:
        st.subheader("p-Chart — Defect Rate Control")
        st.markdown("""
        - Tracks the *proportion defective* in each inspection batch
        - Use when counting defective items (pass/fail), not measuring dimensions
        - **Red points** = defect rate is out of control
        """)

        col1, col2 = st.columns(2)
        n_batches  = col1.slider("Number of Batches", 10, 30, 20)
        batch_size = col2.slider("Parts per Batch", 50, 200, 100)

        np.random.seed(99)
        defects = np.random.binomial(n=batch_size, p=0.03, size=n_batches)
        defects[int(n_batches * 0.35)] = int(batch_size * 0.12)
        defects[int(n_batches * 0.70)] = int(batch_size * 0.10)

        p_i   = defects / batch_size
        p_bar = defects.sum() / (n_batches * batch_size)
        UCL_p = p_bar + 3 * np.sqrt(p_bar * (1 - p_bar) / batch_size)
        LCL_p = max(0, p_bar - 3 * np.sqrt(p_bar * (1 - p_bar) / batch_size))

        colors_p = ["red" if p > UCL_p or p < LCL_p else "#534AB7" for p in p_i]
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(
            x=list(range(1, n_batches+1)), y=p_i,
            mode="lines+markers",
            marker=dict(color=colors_p, size=9),
            line=dict(color="#534AB7"), name="Defect Rate"
        ))
        for y, name, color, dash in [
            (UCL_p, f"UCL = {UCL_p:.3f}", "red", "dash"),
            (p_bar, f"CL = {p_bar:.3f}", "green", "solid"),
            (LCL_p, f"LCL = {LCL_p:.3f}", "red", "dash"),
        ]:
            fig_p.add_hline(y=y, line_dash=dash, line_color=color,
                            annotation_text=name, annotation_position="right")
        fig_p.update_layout(title="p-Chart — Proportion Defective",
                            xaxis_title="Batch Number", yaxis_title="Defect Rate",
                            yaxis_tickformat=".1%", height=400)
        st.plotly_chart(fig_p, use_container_width=True)

        ooc = sum(1 for p in p_i if p > UCL_p or p < LCL_p)
        col1, col2, col3 = st.columns(3)
        col1.metric("Average Defect Rate", f"{p_bar:.1%}")
        col2.metric("Out-of-Control Batches", ooc)
        col3.metric("Total Defects Found", int(defects.sum()))

        if ooc > 0:
            st.error(f"🔴 {ooc} batch(es) are out of control. Initiate failure analysis immediately.")
        else:
            st.success("✅ Process is in control. No action required.")
        st.caption("Data source: Simulated binomial defect data. "
                   "Baseline defect rate 3%. Spikes seeded at batches 7 and 14.")


# ============================================================
# MODULE 4: CHANGE ACTION ANALYZER
# ============================================================
elif module == "🔄 Change Action Analyzer":
    st.title("🔄 Change Action (CA) Impact Analyzer")
    st.markdown("Model obsolescence risk and ramp timing when engineering changes are introduced.")

    with st.expander("📂 Data Source & Preview", expanded=False):
        st.markdown("""
        **What is a Change Action?**
        An Engineering Change Order (ECO) triggers a part supersession — the old part is
        discontinued and a new part introduced. The planning team must simultaneously:
        1. Determine how much old inventory will be stranded (obsolescence risk)
        2. Calculate when to place the first PO for the new part
        3. Quantify the unit cost impact

        **Data model:** All inputs are simulated values representative of a real
        Battery Cell version upgrade in an automotive EV program.

        **Data sources in a live environment:**
        - Current inventory: SAP WM (Warehouse Management) / MB52
        - Qty on order: SAP MM open PO report (ME2M)
        - Daily demand rate: SAP PP production plan (MD04)
        - Part costs: SAP MM pricing conditions (ME13)
        - Engineering change date: Engineering Change Management system (ECM)
        """)
        preview_ca_data = pd.DataFrame({
            "Input":            ["Current Inventory", "On-Order Qty", "Daily Demand",
                                 "Old Part Cost", "New Part Cost", "New Part Lead Time",
                                 "CA Effective Date"],
            "Sample Value":     ["2,400 units", "800 units", "80 units/day",
                                 "$45.00", "$42.00", "45 days", "May 6, 2026"],
            "SAP Source":       ["MB52 / WM", "ME2M open POs", "MD04 demand list",
                                 "MM03 pricing", "Supplier quote", "MM02 planned deliv.",
                                 "ECM change record"],
            "Risk if Stale":    [
                "Understated stranded risk",
                "Double-counted obsolescence",
                "Wrong consumption forecast",
                "Understated write-off value",
                "Wrong ROI calculation",
                "Late new part arrival",
                "Wrong order timing"
            ]
        })
        st.dataframe(preview_ca_data, use_container_width=True, hide_index=True)
        st.caption("This is exactly the kind of master data quality issue FactorySync "
                   "is designed to surface — stale inputs producing wrong planning outputs.")

    st.markdown("---")
    st.info("""
    **What is a Change Action?**
    When engineering changes a part (redesign, supplier switch, material change), you need to figure out:
    1. How much old inventory will be left over (stranded/obsolete)?
    2. When should you start ordering the new part?
    3. What does this cost the business?
    """)

    st.markdown("---")
    st.subheader("Enter Change Action Details")

    col1, col2 = st.columns(2)
    part_name         = col1.text_input("Part Name", value="Battery Cell v1.0")
    old_part_cost     = col1.number_input("Old Part Unit Cost ($)", value=45.00, step=0.5)
    current_inventory = col1.number_input("Current Inventory on Hand (units)", value=2400)
    on_order_qty      = col1.number_input("Qty Currently On Order (units)", value=800)

    daily_demand      = col2.number_input("Daily Demand Rate (units/day)", value=80)
    new_part_cost     = col2.number_input("New Part Unit Cost ($)", value=42.00, step=0.5)
    new_part_lead     = col2.number_input("New Part Lead Time (days)", value=45)
    ca_effective_date = col2.date_input("Engineering Change Effective Date",
                                        value=datetime.today() + timedelta(days=30))

    st.markdown("---")

    if st.button("Run Change Action Analysis", type="primary"):
        today   = datetime.today()
        ca_date = datetime.combine(ca_effective_date, datetime.min.time())

        days_until_ca      = max(0, (ca_date - today).days)
        total_old_stock    = current_inventory + on_order_qty
        consumed_before_ca = min(total_old_stock, daily_demand * days_until_ca)
        stranded_units     = max(0, total_old_stock - consumed_before_ca)
        stranded_value     = stranded_units * old_part_cost

        new_part_order_date = ca_date - timedelta(days=new_part_lead)
        days_to_order_new   = max(0, (new_part_order_date - today).days)
        daily_savings       = (old_part_cost - new_part_cost) * daily_demand
        annual_savings      = daily_savings * 365

        st.subheader("Analysis Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Days Until Change Effective", days_until_ca)
        col2.metric("Stranded Units", f"{stranded_units:,}")
        col3.metric("Obsolescence Risk ($)", f"${stranded_value:,.0f}",
                    delta="Write-off risk" if stranded_value > 0 else "No risk",
                    delta_color="inverse")

        col1, col2, col3 = st.columns(3)
        col1.metric("Order New Part By", new_part_order_date.strftime("%Y-%m-%d"))
        col2.metric("Days Left to Place Order", days_to_order_new)
        col3.metric("Annual Cost Savings", f"${annual_savings:,.0f}",
                    delta="savings" if annual_savings > 0 else "cost increase")

        st.markdown("---")
        st.subheader("Old Part Inventory Burn-Down")

        days_range       = range(0, int(total_old_stock / max(daily_demand,1)) + days_until_ca + 10)
        inventory_levels = [max(0, total_old_stock - daily_demand * d) for d in days_range]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(days_range), y=inventory_levels,
            mode="lines", fill="tozeroy",
            line=dict(color="#185FA5"),
            fillcolor="rgba(24, 95, 165, 0.15)",
            name="Old Part Inventory"
        ))
        fig.add_vline(x=days_until_ca, line_dash="dash", line_color="red",
                      annotation_text="CA Effective Date", annotation_position="top right")
        if stranded_units > 0:
            fig.add_hline(y=stranded_units, line_dash="dot", line_color="orange",
                          annotation_text=f"Stranded: {stranded_units:,} units",
                          annotation_position="right")
        fig.update_layout(xaxis_title="Days from Today", yaxis_title="Units on Hand", height=380)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Recommended Actions")
        actions = []
        if days_to_order_new <= 7:
            actions.append("🔴 **ORDER NEW PART NOW** — Lead time window is closing. Place PO immediately.")
        elif days_to_order_new <= 14:
            actions.append("🟡 **Order new part within 2 weeks** to ensure on-time delivery at changeover.")
        else:
            actions.append(f"🟢 **Place new part order in {days_to_order_new} days** ({new_part_order_date.strftime('%b %d, %Y')}).")
        if stranded_units > 0:
            actions.append(f"⚠️ **Reduce old part POs** — {stranded_units:,} units at ${stranded_value:,.0f} risk of obsolescence.")
            actions.append("💡 **Consider:** Accelerating old part consumption, returning to supplier, or engineering a rework plan.")
        if annual_savings > 0:
            actions.append(f"✅ **New part saves ${annual_savings:,.0f}/year** — transition as scheduled to capture savings.")
        for action in actions:
            st.markdown(action)

        st.caption("Data source: User-entered values simulating SAP MM / PP / WM data. "
                   "Calculations replicate standard ECO impact analysis methodology.")
