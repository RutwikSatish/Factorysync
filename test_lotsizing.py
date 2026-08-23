"""
test_lotsizing.py — regression tests for the MRP lot sizing module.

Every test here corresponds to a defect found during audit. Run with:
    python -m pytest test_lotsizing.py -v
or standalone:
    python test_lotsizing.py
"""

import math
import random

from lotsizing import (
    METHOD_NAMES,
    compute_costs,
    economic_order_quantity,
    net_requirements,
    planned_order_releases,
    projected_available,
    run_all_methods,
    silver_meal,
    stockout_periods,
    wagner_whitin,
)

# The pre-loaded example: 12 periods of variable demand, one scheduled receipt.
GR = [0, 50, 0, 80, 120, 0, 60, 40, 0, 100, 70, 30]
SR = [50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
INIT = 0.0
S = 150.0
UNIT_COST = 25.0
H = (0.25 * UNIT_COST) / 12          # monthly holding cost per unit


# ── Netting ──────────────────────────────────────────────────────────────────
def test_netting_consumes_scheduled_receipts():
    net = net_requirements(GR, SR, INIT)
    assert net[0] == 0 and net[1] == 0, "the P1 receipt of 50 should cover P2 demand of 50"
    assert net[3] == 80


def test_netting_carries_surplus_forward():
    net = net_requirements([10, 10, 10], [0, 0, 0], initial_inventory=25)
    assert net == [0.0, 0.0, 5.0]


# ── Feasibility: the bug that made Silver-Meal look cheapest ────────────────
def test_no_method_ever_stocks_out():
    """
    Regression: the original Silver-Meal advanced t past the periods a lot
    covered without consuming their demand, so it under-ordered and the plan
    ran negative from P7 onward. Holding cost was floored at zero, which made
    the infeasible plan appear to be the cheapest.
    """
    results = run_all_methods(GR, SR, INIT, S, H, moq=1)
    for name, r in results.items():
        assert r["stockouts"] == [], f"{name} produced stockouts in periods {r['stockouts']}"


def test_supply_covers_demand():
    results = run_all_methods(GR, SR, INIT, S, H, moq=1)
    for name, r in results.items():
        supply = sum(SR) + INIT + sum(r["receipts"])
        assert supply >= sum(GR) - 1e-9, f"{name} supplies {supply} against demand {sum(GR)}"


def test_silver_meal_specific_regression():
    net = net_requirements(GR, SR, INIT)
    receipts = silver_meal(net, ordering_cost=S, holding_per_period=H)
    assert sum(receipts) >= sum(net) - 1e-9
    assert stockout_periods(GR, SR, INIT, receipts) == []


# ── EOQ time basis ───────────────────────────────────────────────────────────
def test_eoq_uses_consistent_time_basis():
    """
    Regression: Q* = sqrt(2 D S / H) with D as horizon total and H per period
    inflated the result by sqrt(n). Hand-computed: D/period = 550/12 = 45.83,
    S = 150, H = 0.5208  ->  Q* = 162.5.
    """
    q = economic_order_quantity(total_demand=550, n_periods=12,
                                ordering_cost=150.0, holding_per_period=H)
    assert abs(q - 162.5) < 0.5, f"expected ~162.5, got {q:.1f}"

    wrong = math.sqrt(2 * 550 * 150 / H)
    assert abs(wrong / q - math.sqrt(12)) < 0.05   # documents the old error


# ── Costing ──────────────────────────────────────────────────────────────────
def test_costs_include_opening_inventory():
    """
    Regression: compute_costs accepted initial_inventory and never used it,
    so holding cost ignored opening stock entirely.
    """
    receipts = [0.0] * 3
    gr, sr, init = [10, 10, 10], [0, 0, 0], 60.0
    pab = projected_available(gr, sr, init, receipts)     # 50, 40, 30
    expected = (50 + 40 + 30) * H
    got = compute_costs(receipts, gr, sr, init, S, H)["holding"]
    assert abs(got - expected) < 1e-6, f"expected {expected:.4f}, got {got:.4f}"


def test_ordering_cost_counts_orders_not_periods():
    c = compute_costs([100, 0, 0, 50], [50] * 4, [0] * 4, 0.0, S, H)
    assert c["n_orders"] == 2
    assert abs(c["ordering"] - 2 * S) < 1e-9


# ── Wagner-Whitin optimality ────────────────────────────────────────────────
def test_wagner_whitin_is_at_least_as_good_as_every_heuristic():
    """
    Regression: the DP charged a setup in zero-requirement periods, inflating
    f[] and breaking the benchmark. With moq = 1, WW must be a lower bound.
    """
    results = run_all_methods(GR, SR, INIT, S, H, moq=1)
    ww = results["Wagner-Whitin"]["total"]
    for name, r in results.items():
        assert r["total"] >= ww - 1e-6, f"{name} (${r['total']:.2f}) beat WW (${ww:.2f})"


def test_wagner_whitin_matches_brute_force_on_small_instances():
    """Exhaustively check the DP against every possible order pattern."""
    random.seed(7)
    for _ in range(40):
        n = random.randint(3, 8)
        net = [float(random.choice([0, 0, 10, 25, 40, 60])) for _ in range(n)]
        if sum(net) == 0:
            continue

        best = float("inf")
        for mask in range(1 << n):
            order_at = [bool(mask >> i & 1) for i in range(n)]
            receipts, ok, bal, cost = [0.0] * n, True, 0.0, 0.0
            for t in range(n):
                if order_at[t]:
                    cost += S
                    nxt = next((j for j in range(t + 1, n) if order_at[j]), n)
                    receipts[t] = sum(net[t:nxt])
                bal += receipts[t] - net[t]
                if bal < -1e-9:
                    ok = False
                    break
                cost += bal * H
            if ok:
                best = min(best, cost)

        dp = wagner_whitin(net, ordering_cost=S, holding_per_period=H, moq=1)
        dp_cost = compute_costs(dp, net, [0.0] * n, 0.0, S, H)["total"]
        assert dp_cost <= best + 1e-6, f"DP {dp_cost:.2f} worse than brute force {best:.2f} on {net}"


# ── Lead time offsetting ────────────────────────────────────────────────────
def test_past_due_quantity_is_reported_not_dropped():
    """
    Regression: releases falling before period 1 were silently discarded, so
    quantity vanished from the plan with no warning.
    """
    receipts = [100.0, 0.0, 50.0]
    releases, past_due = planned_order_releases(receipts, lead_time=2)
    assert past_due == 100.0
    assert releases == [50.0, 0.0, 0.0]
    assert sum(releases) + past_due == sum(receipts)


def test_zero_lead_time_is_identity():
    receipts = [10.0, 0.0, 25.0]
    releases, past_due = planned_order_releases(receipts, lead_time=0)
    assert releases == receipts and past_due == 0.0


# ── Property tests over randomised demand ───────────────────────────────────
def test_property_feasible_and_conserving_across_random_instances():
    random.seed(42)
    for trial in range(300):
        n = random.randint(2, 18)
        gr = [float(random.choice([0, 0, 5, 20, 45, 80, 130])) for _ in range(n)]
        sr = [0.0] * n
        if random.random() < 0.4:
            sr[0] = float(random.choice([0, 25, 60]))
        init = float(random.choice([0, 0, 30, 90]))
        s = random.choice([25.0, 150.0, 600.0])
        h = random.choice([0.02, 0.52, 3.0])
        moq = random.choice([1, 1, 10, 25])

        results = run_all_methods(gr, sr, init, s, h, moq=moq)
        for name, r in results.items():
            ctx = f"trial={trial} method={name} gr={gr} init={init} moq={moq}"
            assert r["stockouts"] == [], f"stockout: {ctx}"
            assert sum(r["receipts"]) + sum(sr) + init >= sum(gr) - 1e-9, f"short: {ctx}"
            assert all(q >= 0 for q in r["receipts"]), f"negative order: {ctx}"
            if moq > 1:
                assert all(abs(q % moq) < 1e-9 for q in r["receipts"] if q > 0), f"moq: {ctx}"


def test_property_wagner_whitin_dominates_when_moq_is_one():
    random.seed(99)
    for _ in range(150):
        n = random.randint(2, 14)
        net = [float(random.choice([0, 0, 15, 35, 70])) for _ in range(n)]
        if sum(net) == 0:
            continue
        s = random.choice([50.0, 150.0, 400.0])
        h = random.choice([0.1, 0.52, 2.0])

        results = run_all_methods(net, [0.0] * n, 0.0, s, h, moq=1)
        ww = results["Wagner-Whitin"]["total"]
        for name, r in results.items():
            assert r["total"] >= ww - 1e-6, f"{name} beat WW on {net}"


def test_zero_demand_produces_no_orders():
    results = run_all_methods([0] * 6, [0] * 6, 0.0, S, H)
    for name, r in results.items():
        assert sum(r["receipts"]) == 0, f"{name} ordered against zero demand"


def test_all_methods_present():
    results = run_all_methods(GR, SR, INIT, S, H)
    assert sorted(results.keys()) == sorted(METHOD_NAMES)


if __name__ == "__main__":
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
                passed += 1
            except AssertionError as e:
                print(f"  FAIL  {name}\n        {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)
