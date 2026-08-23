"""
lotsizing.py — MRP lot sizing algorithms (pure logic, no UI dependencies)
========================================================================
Separated from the Streamlit layer so every algorithm can be unit tested.

REFERENCES
  Jacobs, Berry, Whybark & Vollmann (2011), "Manufacturing Planning and
      Control for Supply Chain Management", Ch. 3-4 (APICS CPIM reference).
  Silver, E.A. & Meal, H.C. (1973), Management Science.
  Wagner, H.M. & Whitin, T.M. (1958), Management Science 5(1).
  Silver, Pyke & Thomas (1998), "Inventory Management and Production
      Planning and Scheduling", Ch. 5.

DESIGN NOTE — why net requirements are computed once, up front
  All six lot sizing rules are defined in the literature over a *demand
  series*. Netting off opening inventory and scheduled receipts first, then
  handing the resulting net requirement series to each rule, keeps the rules
  faithful to their published definitions and makes them directly comparable.
  It also avoids the class of bug where a rule that covers several periods at
  once forgets to consume inventory in the periods it skipped.

MINIMUM ORDER QUANTITY CAVEAT
  Wagner-Whitin is provably optimal for the uncapacitated single-item problem
  with no order multiples. Once a minimum order quantity or rounding multiple
  is imposed, that optimality guarantee no longer holds. With moq > 1 treat
  Wagner-Whitin as a strong reference point, not a proven lower bound.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence

EPS = 1e-9

METHOD_NAMES = [
    "Lot-for-Lot",
    "EOQ",
    "Period Order Qty",
    "Part Period Bal.",
    "Silver-Meal",
    "Wagner-Whitin",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _round_up(qty: float, moq: int) -> float:
    """Round an order quantity up to a whole unit, and to a multiple of moq."""
    if qty <= EPS:
        return 0.0
    if moq is None or moq <= 1:
        return float(math.ceil(qty - EPS))
    return float(math.ceil((qty - EPS) / moq) * moq)


def net_requirements(
    gross_req: Sequence[float],
    sched_receipts: Sequence[float],
    initial_inventory: float,
) -> List[float]:
    """
    Standard MRP netting (Jacobs & Berry Ch. 3).

    Net requirement in period t is the shortfall after applying inventory
    carried in from t-1 plus any scheduled receipt arriving in t. Surplus is
    carried forward; shortfalls are NOT carried forward as backlog, because a
    net requirement that is covered by a planned order is satisfied in-period.
    """
    n = len(gross_req)
    net = [0.0] * n
    on_hand = float(initial_inventory)

    for t in range(n):
        available = on_hand + float(sched_receipts[t])
        demand = float(gross_req[t])
        if available >= demand - EPS:
            net[t] = 0.0
            on_hand = available - demand
        else:
            net[t] = demand - available
            on_hand = 0.0
    return net


def projected_available(
    gross_req: Sequence[float],
    sched_receipts: Sequence[float],
    initial_inventory: float,
    planned_receipts: Sequence[float],
) -> List[float]:
    """End-of-period projected available balance, including planned receipts."""
    n = len(gross_req)
    pab = [0.0] * n
    prev = float(initial_inventory)
    for t in range(n):
        prev = prev + float(sched_receipts[t]) + float(planned_receipts[t]) - float(gross_req[t])
        pab[t] = prev
    return pab


def stockout_periods(
    gross_req: Sequence[float],
    sched_receipts: Sequence[float],
    initial_inventory: float,
    planned_receipts: Sequence[float],
) -> List[int]:
    """1-indexed periods where projected available goes negative. Empty == feasible."""
    pab = projected_available(gross_req, sched_receipts, initial_inventory, planned_receipts)
    return [i + 1 for i, v in enumerate(pab) if v < -EPS]


def planned_order_releases(
    planned_receipts: Sequence[float], lead_time: int
) -> tuple[List[float], float]:
    """
    Offset planned order receipts back by lead time.

    Returns (releases, past_due_qty). Any receipt whose release period falls
    before period 1 cannot be released on time; that quantity is returned as
    past due rather than silently dropped, matching how a real MRP system
    raises a past-due action message.
    """
    n = len(planned_receipts)
    releases = [0.0] * n
    past_due = 0.0
    for t in range(n):
        rel = t - lead_time
        if rel >= 0:
            releases[rel] = float(planned_receipts[t])
        else:
            past_due += float(planned_receipts[t])
    return releases, past_due


def compute_costs(
    planned_receipts: Sequence[float],
    gross_req: Sequence[float],
    sched_receipts: Sequence[float],
    initial_inventory: float,
    ordering_cost: float,
    holding_cost_per_unit_per_period: float,
) -> Dict[str, float]:
    """
    Ordering + holding cost. Holding is charged on end-of-period projected
    available (Jacobs & Berry Ch. 4 convention), and correctly includes
    opening inventory.

    Unit purchase cost is deliberately excluded: total units bought is the
    same under every rule absent quantity discounts, so it cannot discriminate
    between methods.
    """
    n_orders = sum(1 for q in planned_receipts if q > EPS)
    ordering = n_orders * float(ordering_cost)

    pab = projected_available(gross_req, sched_receipts, initial_inventory, planned_receipts)
    holding = sum(max(0.0, v) for v in pab) * float(holding_cost_per_unit_per_period)

    return {
        "n_orders": n_orders,
        "ordering": ordering,
        "holding": holding,
        "total": ordering + holding,
    }


def economic_order_quantity(
    total_demand: float, n_periods: int, ordering_cost: float, holding_per_period: float
) -> float:
    """
    Classical EOQ: Q* = sqrt(2 D S / H).

    D and H must share a time basis. D here is average demand PER PERIOD and
    H is holding cost per unit PER PERIOD, so the result is a quantity in the
    same units as demand. Passing total-horizon demand against a per-period
    holding rate inflates Q* by sqrt(n_periods).
    """
    if holding_per_period <= 0 or total_demand <= 0 or n_periods <= 0:
        return 0.0
    demand_per_period = total_demand / n_periods
    return math.sqrt(2.0 * demand_per_period * ordering_cost / holding_per_period)


# ─────────────────────────────────────────────────────────────────────────────
# Lot sizing rules — each takes a NET REQUIREMENT series, returns planned
# order receipts of the same length.
# ─────────────────────────────────────────────────────────────────────────────
def lot_for_lot(net: Sequence[float], moq: int = 1, **_) -> List[float]:
    """Order exactly the net requirement each period. Jacobs & Berry p. 93."""
    return [_round_up(q, moq) for q in net]


def eoq_rule(
    net: Sequence[float], ordering_cost: float, holding_per_period: float, moq: int = 1, **_
) -> List[float]:
    """
    Order in EOQ-sized lots whenever the running balance cannot cover the
    period's net requirement. Jacobs & Berry p. 94.
    """
    n = len(net)
    total = sum(net)
    eoq = economic_order_quantity(total, n, ordering_cost, holding_per_period)
    if eoq <= 0:
        return lot_for_lot(net, moq)
    eoq = max(_round_up(eoq, moq), float(moq))

    orders = [0.0] * n
    balance = 0.0
    for t in range(n):
        if net[t] > EPS and balance < net[t] - EPS:
            shortfall = net[t] - balance
            lots = math.ceil((shortfall - EPS) / eoq)
            qty = lots * eoq
            orders[t] = qty
            balance += qty
        balance -= net[t]
        if balance < 0:
            balance = 0.0
    return orders


def period_order_quantity(
    net: Sequence[float], ordering_cost: float, holding_per_period: float, moq: int = 1, **_
) -> List[float]:
    """
    EOQ expressed as a fixed review period P = round(EOQ / average demand).
    Order enough to cover the next P periods. Jacobs & Berry p. 95.
    """
    n = len(net)
    total = sum(net)
    if total <= 0:
        return [0.0] * n
    eoq = economic_order_quantity(total, n, ordering_cost, holding_per_period)
    avg = total / n
    if eoq <= 0 or avg <= 0:
        return lot_for_lot(net, moq)

    P = max(1, int(round(eoq / avg)))

    orders = [0.0] * n
    t = 0
    while t < n:
        if net[t] <= EPS:
            t += 1
            continue
        orders[t] = _round_up(sum(net[t : t + P]), moq)
        t += P
    return orders


def part_period_balancing(
    net: Sequence[float], ordering_cost: float, holding_per_period: float, moq: int = 1, **_
) -> List[float]:
    """
    Part Period Balancing: extend the lot until cumulative part-periods are as
    close as possible to the Economic Part Period, EPP = S / H.
    Jacobs & Berry p. 96; Silver, Pyke & Thomas p. 247.
    """
    n = len(net)
    if holding_per_period <= 0:
        return lot_for_lot(net, moq)
    epp = ordering_cost / holding_per_period

    orders = [0.0] * n
    t = 0
    while t < n:
        if net[t] <= EPS:
            t += 1
            continue

        cum_pp = 0.0            # part-periods for a lot covering t..t (zero)
        best_T = 1
        best_diff = abs(cum_pp - epp)

        for j in range(t + 1, n):
            cum_pp += (j - t) * net[j]
            diff = abs(cum_pp - epp)
            if diff < best_diff:
                best_diff = diff
                best_T = j - t + 1
            if cum_pp > epp:
                break

        orders[t] = _round_up(sum(net[t : t + best_T]), moq)
        t += best_T
    return orders


def silver_meal(
    net: Sequence[float], ordering_cost: float, holding_per_period: float, moq: int = 1, **_
) -> List[float]:
    """
    Silver-Meal: choose the coverage T minimising average cost per period,
        C(T) = ( S + sum_{k=1}^{T-1} k * h * d_{t+k} ) / T
    stopping as soon as C(T+1) exceeds C(T). Silver & Meal (1973).
    """
    n = len(net)
    if holding_per_period <= 0:
        return lot_for_lot(net, moq)

    orders = [0.0] * n
    t = 0
    while t < n:
        if net[t] <= EPS:
            t += 1
            continue

        best_T = 1
        best_cost = ordering_cost          # T = 1: setup only, no holding
        cum_hold = 0.0

        for j in range(t + 1, n):
            cum_hold += (j - t) * holding_per_period * net[j]
            cost = (ordering_cost + cum_hold) / (j - t + 1)
            if cost < best_cost - EPS:
                best_cost = cost
                best_T = j - t + 1
            else:
                break                       # average cost has turned upward

        orders[t] = _round_up(sum(net[t : t + best_T]), moq)
        t += best_T
    return orders


def wagner_whitin(
    net: Sequence[float], ordering_cost: float, holding_per_period: float, moq: int = 1, **_
) -> List[float]:
    """
    Wagner-Whitin dynamic program (1958).

        f[t] = min over j >= t of  S + holding(t..j) + f[j+1]

    Orders are only ever placed in a period with a positive net requirement —
    charging a setup in a zero-requirement period is never optimal, and doing
    so inflates every downstream f[] value.

    O(n^2). Exact for the uncapacitated problem when moq = 1; see the module
    docstring for the moq caveat.
    """
    n = len(net)
    if n == 0:
        return []
    if holding_per_period <= 0:
        return lot_for_lot(net, moq)

    INF = float("inf")
    f = [INF] * (n + 1)
    split = [n] * (n + 1)
    f[n] = 0.0

    for t in range(n - 1, -1, -1):
        if net[t] <= EPS:
            f[t] = f[t + 1]        # nothing due in t; defer
            split[t] = t + 1
            continue

        hold = 0.0
        for j in range(t, n):
            if j > t:
                hold += (j - t) * holding_per_period * net[j]
            cost = ordering_cost + hold + f[j + 1]
            if cost < f[t]:
                f[t] = cost
                split[t] = j + 1

    orders = [0.0] * n
    t = 0
    while t < n:
        if net[t] > EPS:
            end = split[t]
            orders[t] = _round_up(sum(net[t:end]), moq)
            t = end
        else:
            t += 1
    return orders


def fixed_batch(net: Sequence[float], batch: float, moq: int = 1, **_) -> List[float]:
    """Order whole multiples of a fixed batch size. Common ERP default."""
    n = len(net)
    orders = [0.0] * n
    balance = 0.0
    for t in range(n):
        if net[t] > EPS and balance < net[t] - EPS:
            lots = math.ceil((net[t] - balance - EPS) / batch)
            qty = lots * batch
            orders[t] = qty
            balance += qty
        balance -= net[t]
        if balance < 0:
            balance = 0.0
    return orders


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────
def run_all_methods(
    gross_req: Sequence[float],
    sched_receipts: Sequence[float],
    initial_inventory: float,
    ordering_cost: float,
    holding_per_period: float,
    moq: int = 1,
) -> Dict[str, dict]:
    """
    Run every rule and return, per method: planned receipts, cost breakdown,
    and any stockout periods (which should always be empty — the presence of
    one indicates a bug, and the UI surfaces it rather than hiding it).
    """
    net = net_requirements(gross_req, sched_receipts, initial_inventory)

    kwargs = dict(
        ordering_cost=ordering_cost,
        holding_per_period=holding_per_period,
        moq=moq,
    )
    rules = {
        "Lot-for-Lot": lambda: lot_for_lot(net, moq=moq),
        "EOQ": lambda: eoq_rule(net, **kwargs),
        "Period Order Qty": lambda: period_order_quantity(net, **kwargs),
        "Part Period Bal.": lambda: part_period_balancing(net, **kwargs),
        "Silver-Meal": lambda: silver_meal(net, **kwargs),
        "Wagner-Whitin": lambda: wagner_whitin(net, **kwargs),
    }

    out: Dict[str, dict] = {}
    for name, fn in rules.items():
        receipts = fn()
        costs = compute_costs(
            receipts, gross_req, sched_receipts, initial_inventory,
            ordering_cost, holding_per_period,
        )
        out[name] = {
            "receipts": receipts,
            "stockouts": stockout_periods(gross_req, sched_receipts, initial_inventory, receipts),
            **costs,
        }
    return out
