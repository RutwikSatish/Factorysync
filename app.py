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
    - **PPAP Tracker** — Tracks Production Part Approval milestones and supplier risk scores
    - **SPC Dashboards** — Monitors process quality with control charts and flags deviations
    - **Change Action Analyzer** — Models obsolescence risk and ramp timing when engineering changes are introduced

    Use the sidebar to navigate between modules.
    """)

# ============================================================
# MODULE 1: MRP ENGINE
# ============================================================
elif module == "📦 MRP Engine":
    st.title("📦 MRP Simulation Engine")
    st.markdown("Explode your Bill of Materials, apply lead times, and generate an order schedule.")
    st.markdown("---")

    # ── STEP 1: Define the Bill of Materials ─────────────────
    st.subheader("Step 1 — Define your Bill of Materials (BOM)")
    st.markdown("Each row = one component. Fill in the details below.")

    # Default BOM data shown when app loads
    # 'Component' = part name
    # 'Parent' = what it goes into ('Finished Good' = top level)
    # 'Qty Per' = how many needed per parent unit
    # 'Lead Time (days)' = how long to get this part
    default_bom = pd.DataFrame({
        "Component":       ["Battery Pack", "Motor Assembly", "Chassis Frame",
                            "Battery Cell", "Battery Housing", "Stator", "Rotor",
                            "Frame Rail", "Cross Member"],
        "Parent":          ["Finished Good", "Finished Good", "Finished Good",
                            "Battery Pack", "Battery Pack", "Motor Assembly", "Motor Assembly",
                            "Chassis Frame", "Chassis Frame"],
        "Qty Per":         [1, 1, 1, 96, 1, 1, 1, 2, 3],
        "Lead Time (days)":[14, 21, 10, 45, 20, 30, 25, 15, 12]
    })

    # st.data_editor lets users edit the table directly in the app
    bom_df = st.data_editor(default_bom, num_rows="dynamic", use_container_width=True)

    st.markdown("---")

    # ── STEP 2: Enter Demand ──────────────────────────────────
    st.subheader("Step 2 — Enter Demand")

    col1, col2 = st.columns(2)
    demand_qty   = col1.number_input("Finished Goods Required (units)", min_value=1, value=10)
    # Date picker — when do you need the finished good?
    due_date     = col2.date_input("Required By Date", value=datetime.today() + timedelta(days=60))

    st.markdown("---")

    # ── STEP 3: Calculate and Show Order Schedule ─────────────
    st.subheader("Step 3 — Order Schedule")

    if st.button("Generate MRP Schedule", type="primary"):

        # BOM EXPLOSION:
        # Multiply demand qty down through each level of the BOM
        # e.g. 10 Finished Goods × 96 Battery Cells = 960 Battery Cells needed
        schedule = []

        for _, row in bom_df.iterrows():
            # Find how many of this component we need total
            total_qty = demand_qty * row["Qty Per"]

            # LEAD TIME OFFSETTING:
            # Work backward from the due date to find when to ORDER
            # If Battery Cells take 45 days, order them 45 days before due date
            order_date = pd.to_datetime(due_date) - timedelta(days=int(row["Lead Time (days)"]))

            schedule.append({
                "Component":       row["Component"],
                "Parent":          row["Parent"],
                "Qty Needed":      total_qty,
                "Lead Time (days)": row["Lead Time (days)"],
                "Order By":        order_date.strftime("%Y-%m-%d"),
                "Due Date":        str(due_date),
                "Status":          "On Track" if order_date > datetime.today() else "⚠️ Past Due"
            })

        schedule_df = pd.DataFrame(schedule)

        # Color the Status column: red for past due, green for on track
        def highlight_status(val):
            if "Past Due" in str(val):
                return "background-color: #fce8e8; color: #a32d2d"
            return "background-color: #eaf3de; color: #3b6d11"

        st.dataframe(
            schedule_df.style.applymap(highlight_status, subset=["Status"]),
            use_container_width=True
        )

        # Summary metrics
        past_due = schedule_df[schedule_df["Status"].str.contains("Past Due")]
        st.metric("Parts with Past Due Order Dates", len(past_due))
        if len(past_due) > 0:
            st.warning(f"⚠️ {len(past_due)} component(s) need to be ordered immediately to meet your due date.")
        else:
            st.success("✅ All components can be ordered in time to meet your due date.")

# ============================================================
# MODULE 2: PPAP TRACKER
# ============================================================
elif module == "✅ PPAP Tracker":
    st.title("✅ PPAP Readiness Tracker")
    st.markdown("Track Production Part Approval Process milestones across your supplier base.")
    st.markdown("---")

    # The 18 official PPAP elements (simplified to 10 for clarity)
    ppap_elements = [
        "Design Records",
        "Engineering Change Documents",
        "Customer Engineering Approval",
        "Design FMEA",
        "Process Flow Diagram",
        "Process FMEA",
        "Control Plan",
        "MSA Studies",
        "Dimensional Results",
        "Initial Process Studies (SPC)"
    ]

    # List of suppliers
    suppliers = [
        "Supplier A — Battery Cells",
        "Supplier B — Motor Stator",
        "Supplier C — Chassis Rails",
        "Supplier D — Battery Housing",
        "Supplier E — Rotor Assembly"
    ]

    st.subheader("Select Supplier")
    selected_supplier = st.selectbox("Choose a supplier to review", suppliers)

    st.markdown("---")
    st.subheader(f"PPAP Checklist — {selected_supplier}")

    # Status options for each element
    status_options = ["Not Started", "In Progress", "Submitted", "Approved", "Rejected"]

    # Build a form so users can set status for each PPAP element
    # We use session_state to remember what was entered between interactions
    if "ppap_data" not in st.session_state:
        # Initialize with random statuses for demo purposes
        st.session_state.ppap_data = {}

    if selected_supplier not in st.session_state.ppap_data:
        # Default statuses when a supplier is first selected
        np.random.seed(hash(selected_supplier) % 100)
        st.session_state.ppap_data[selected_supplier] = {
            el: np.random.choice(status_options, p=[0.1, 0.2, 0.2, 0.4, 0.1])
            for el in ppap_elements
        }

    # Display each element as a row with a dropdown
    statuses = []
    cols_header = st.columns([3, 2, 1])
    cols_header[0].markdown("**PPAP Element**")
    cols_header[1].markdown("**Status**")
    cols_header[2].markdown("**Risk**")

    for element in ppap_elements:
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.markdown(element)

        current = st.session_state.ppap_data[selected_supplier][element]
        new_status = col2.selectbox(
            "", status_options,
            index=status_options.index(current),
            key=f"{selected_supplier}_{element}",
            label_visibility="collapsed"
        )
        st.session_state.ppap_data[selected_supplier][element] = new_status
        statuses.append(new_status)

        # Risk flag based on status
        if new_status == "Approved":
            col3.markdown("🟢")
        elif new_status in ["Submitted", "In Progress"]:
            col3.markdown("🟡")
        elif new_status == "Rejected":
            col3.markdown("🔴")
        else:
            col3.markdown("⚪")

    st.markdown("---")

    # ── Calculate Risk Score ──────────────────────────────────
    # Score: Approved=1, Submitted=0.7, In Progress=0.4, Not Started=0, Rejected=-0.5
    score_map = {"Approved": 1.0, "Submitted": 0.7, "In Progress": 0.4,
                 "Not Started": 0.0, "Rejected": -0.5}
    raw_score  = sum(score_map[s] for s in statuses)
    max_score  = len(ppap_elements) * 1.0
    pct        = max(0, raw_score / max_score * 100)

    col1, col2, col3 = st.columns(3)
    col1.metric("PPAP Completion Score", f"{pct:.0f}%")
    col2.metric("Elements Approved", statuses.count("Approved"))
    col3.metric("Elements Rejected", statuses.count("Rejected"))

    # Risk rating
    if pct >= 80:
        st.success("✅ LOW RISK — Supplier is on track for PPAP approval.")
    elif pct >= 50:
        st.warning("⚠️ MEDIUM RISK — Several elements need attention before launch.")
    else:
        st.error("🔴 HIGH RISK — SCAR recommended. Escalate to supplier quality team.")

    # Progress bar
    st.progress(int(pct))

# ============================================================
# MODULE 3: SPC DASHBOARDS
# ============================================================
elif module == "📊 SPC Dashboards":
    st.title("📊 Statistical Process Control (SPC) Dashboards")
    st.markdown("Monitor critical component quality using control charts. Flag process deviations in real time.")
    st.markdown("---")

    chart_type = st.radio("Select Chart Type", ["Xbar-R Chart (variable data)", "p-Chart (defect rate)"], horizontal=True)
    st.markdown("---")

    # ── XBAR-R CHART ─────────────────────────────────────────
    if "Xbar" in chart_type:
        st.subheader("Xbar-R Chart — Process Mean & Range Control")
        st.markdown("""
        - **Xbar chart**: Tracks the *average* measurement of each subgroup. Is the process centered?
        - **R chart**: Tracks the *range* (max - min) of each subgroup. Is the process consistent?
        - **Red points** = out of control. Investigate immediately.
        """)

        col1, col2, col3 = st.columns(3)
        n_subgroups  = col1.slider("Number of Subgroups", 10, 30, 20)
        subgroup_size = col2.slider("Subgroup Size (n)", 2, 6, 4)
        process_mean = col3.number_input("Target Process Mean", value=10.0)

        # Simulate measurement data
        # Normal process with occasional out-of-control points
        np.random.seed(42)
        data = np.random.normal(loc=process_mean, scale=0.5,
                                size=(n_subgroups, subgroup_size))

        # Inject 2 out-of-control points to make the chart realistic
        data[int(n_subgroups * 0.4)] += 2.0
        data[int(n_subgroups * 0.75)] -= 1.8

        # Calculate subgroup means and ranges
        xbar = data.mean(axis=1)    # average of each subgroup
        R    = data.max(axis=1) - data.min(axis=1)  # range of each subgroup

        # Control limit constants (standard SPC table values based on subgroup size)
        A2 = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483}
        D3 = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        D4 = {2: 3.267, 3: 2.574, 4: 2.282, 5: 2.115, 6: 2.004}

        n = subgroup_size
        xbar_bar = xbar.mean()   # grand average
        R_bar    = R.mean()      # average range

        # Xbar control limits
        UCL_xbar = xbar_bar + A2[n] * R_bar
        LCL_xbar = xbar_bar - A2[n] * R_bar

        # R chart control limits
        UCL_R = D4[n] * R_bar
        LCL_R = D3[n] * R_bar

        # ── Xbar Chart ────────────────────────────────────────
        fig_xbar = go.Figure()

        # Color points: red if outside control limits
        colors_x = ["red" if (x > UCL_xbar or x < LCL_xbar) else "#185FA5"
                    for x in xbar]

        fig_xbar.add_trace(go.Scatter(
            x=list(range(1, n_subgroups+1)), y=xbar,
            mode="lines+markers",
            marker=dict(color=colors_x, size=9),
            line=dict(color="#185FA5"),
            name="Subgroup Mean"
        ))

        # Reference lines
        for y, name, color, dash in [
            (UCL_xbar, f"UCL = {UCL_xbar:.3f}", "red", "dash"),
            (xbar_bar, f"CL = {xbar_bar:.3f}",  "green", "solid"),
            (LCL_xbar, f"LCL = {LCL_xbar:.3f}", "red", "dash"),
        ]:
            fig_xbar.add_hline(y=y, line_dash=dash, line_color=color,
                               annotation_text=name, annotation_position="right")

        fig_xbar.update_layout(title="Xbar Chart — Subgroup Means",
                               xaxis_title="Subgroup", yaxis_title="Mean",
                               height=350)
        st.plotly_chart(fig_xbar, use_container_width=True)

        # ── R Chart ───────────────────────────────────────────
        fig_r = go.Figure()
        colors_r = ["red" if (r > UCL_R or r < LCL_R) else "#1D9E75" for r in R]

        fig_r.add_trace(go.Scatter(
            x=list(range(1, n_subgroups+1)), y=R,
            mode="lines+markers",
            marker=dict(color=colors_r, size=9),
            line=dict(color="#1D9E75"),
            name="Subgroup Range"
        ))

        for y, name, color, dash in [
            (UCL_R, f"UCL = {UCL_R:.3f}", "red", "dash"),
            (R_bar, f"CL = {R_bar:.3f}",  "green", "solid"),
        ]:
            fig_r.add_hline(y=y, line_dash=dash, line_color=color,
                            annotation_text=name, annotation_position="right")

        fig_r.update_layout(title="R Chart — Subgroup Ranges",
                            xaxis_title="Subgroup", yaxis_title="Range",
                            height=300)
        st.plotly_chart(fig_r, use_container_width=True)

        # Summary
        ooc_xbar = sum(1 for x in xbar if x > UCL_xbar or x < LCL_xbar)
        ooc_r    = sum(1 for r in R if r > UCL_R)
        col1, col2 = st.columns(2)
        col1.metric("Out-of-Control Points (Xbar)", ooc_xbar,
                    delta="Investigate" if ooc_xbar > 0 else "In Control",
                    delta_color="inverse")
        col2.metric("Out-of-Control Points (R)", ooc_r,
                    delta="Investigate" if ooc_r > 0 else "In Control",
                    delta_color="inverse")

    # ── P-CHART ───────────────────────────────────────────────
    else:
        st.subheader("p-Chart — Defect Rate Control")
        st.markdown("""
        - Tracks the *proportion defective* in each inspection batch
        - Use this when you're counting defective items (pass/fail), not measuring dimensions
        - **Red points** = defect rate is out of control
        """)

        col1, col2 = st.columns(2)
        n_batches  = col1.slider("Number of Batches", 10, 30, 20)
        batch_size = col2.slider("Parts per Batch", 50, 200, 100)

        np.random.seed(99)
        # Simulate defects: mostly ~3% defect rate with spikes
        defects = np.random.binomial(n=batch_size, p=0.03, size=n_batches)
        defects[int(n_batches * 0.35)] = int(batch_size * 0.12)   # spike
        defects[int(n_batches * 0.70)] = int(batch_size * 0.10)   # spike

        p_i    = defects / batch_size          # defect proportion each batch
        p_bar  = defects.sum() / (n_batches * batch_size)  # overall average

        # Control limits for p-chart
        UCL_p = p_bar + 3 * np.sqrt(p_bar * (1 - p_bar) / batch_size)
        LCL_p = max(0, p_bar - 3 * np.sqrt(p_bar * (1 - p_bar) / batch_size))

        colors_p = ["red" if p > UCL_p or p < LCL_p else "#534AB7" for p in p_i]

        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(
            x=list(range(1, n_batches+1)), y=p_i,
            mode="lines+markers",
            marker=dict(color=colors_p, size=9),
            line=dict(color="#534AB7"),
            name="Defect Rate"
        ))

        for y, name, color, dash in [
            (UCL_p, f"UCL = {UCL_p:.3f}", "red", "dash"),
            (p_bar, f"CL = {p_bar:.3f}",  "green", "solid"),
            (LCL_p, f"LCL = {LCL_p:.3f}", "red", "dash"),
        ]:
            fig_p.add_hline(y=y, line_dash=dash, line_color=color,
                            annotation_text=name, annotation_position="right")

        fig_p.update_layout(title="p-Chart — Proportion Defective",
                            xaxis_title="Batch Number",
                            yaxis_title="Defect Rate",
                            yaxis_tickformat=".1%",
                            height=400)
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

# ============================================================
# MODULE 4: CHANGE ACTION ANALYZER
# ============================================================
elif module == "🔄 Change Action Analyzer":
    st.title("🔄 Change Action (CA) Impact Analyzer")
    st.markdown("Model obsolescence risk and ramp timing when engineering changes are introduced.")
    st.markdown("---")

    st.info("""
    **What is a Change Action?**
    When engineering changes a part (redesign, supplier switch, material change),
    you need to figure out:
    1. How much old inventory will be left over (stranded/obsolete)?
    2. When should you start ordering the new part?
    3. What does this cost the business?
    """)

    st.markdown("---")
    st.subheader("Enter Change Action Details")

    col1, col2 = st.columns(2)

    part_name        = col1.text_input("Part Name", value="Battery Cell v1.0")
    old_part_cost    = col1.number_input("Old Part Unit Cost ($)", value=45.00, step=0.5)
    current_inventory = col1.number_input("Current Inventory on Hand (units)", value=2400)
    on_order_qty     = col1.number_input("Qty Currently On Order (units)", value=800)

    daily_demand     = col2.number_input("Daily Demand Rate (units/day)", value=80)
    new_part_cost    = col2.number_input("New Part Unit Cost ($)", value=42.00, step=0.5)
    new_part_lead    = col2.number_input("New Part Lead Time (days)", value=45)
    ca_effective_date = col2.date_input("Engineering Change Effective Date",
                                        value=datetime.today() + timedelta(days=30))

    st.markdown("---")

    if st.button("Run Change Action Analysis", type="primary"):

        today = datetime.today()
        ca_date = datetime.combine(ca_effective_date, datetime.min.time())

        # Days until engineering change kicks in
        days_until_ca = max(0, (ca_date - today).days)

        # How much old inventory will be consumed before CA date?
        consumed_before_ca = min(current_inventory + on_order_qty,
                                 daily_demand * days_until_ca)

        # Stranded inventory = what's left over after CA date
        total_old_stock = current_inventory + on_order_qty
        stranded_units  = max(0, total_old_stock - consumed_before_ca)
        stranded_value  = stranded_units * old_part_cost

        # When to place first order for new part
        # Order new part so it arrives exactly on CA effective date
        new_part_order_date = ca_date - timedelta(days=new_part_lead)
        days_to_order_new   = max(0, (new_part_order_date - today).days)

        # Cost savings from new part (if cheaper)
        daily_savings       = (old_part_cost - new_part_cost) * daily_demand
        annual_savings      = daily_savings * 365

        # ── Results ───────────────────────────────────────────
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
        col3.metric("Annual Cost Savings (new part)", f"${annual_savings:,.0f}",
                    delta="savings" if annual_savings > 0 else "cost increase")

        st.markdown("---")

        # ── Inventory Burn-Down Chart ─────────────────────────
        st.subheader("Old Part Inventory Burn-Down")

        # Simulate day-by-day inventory level until it hits 0
        days_range   = range(0, int(total_old_stock / daily_demand) + days_until_ca + 10)
        inventory_levels = []
        for d in days_range:
            level = max(0, total_old_stock - daily_demand * d)
            inventory_levels.append(level)

        fig = go.Figure()

        # Inventory line
        fig.add_trace(go.Scatter(
            x=list(days_range),
            y=inventory_levels,
            mode="lines",
            fill="tozeroy",
            line=dict(color="#185FA5"),
            fillcolor="rgba(24, 95, 165, 0.15)",
            name="Old Part Inventory"
        ))

        # Vertical line at CA date
        fig.add_vline(
            x=days_until_ca,
            line_dash="dash", line_color="red",
            annotation_text="CA Effective Date",
            annotation_position="top right"
        )

        # Horizontal line at stranded quantity
        if stranded_units > 0:
            fig.add_hline(
                y=stranded_units,
                line_dash="dot", line_color="orange",
                annotation_text=f"Stranded: {stranded_units:,} units",
                annotation_position="right"
            )

        fig.update_layout(
            xaxis_title="Days from Today",
            yaxis_title="Units on Hand",
            height=380
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Recommended Actions ───────────────────────────────
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
