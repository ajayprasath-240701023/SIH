"""
Explainable rule-based risk scorer.

Evaluates the traced fund-flow graph against a set of heuristic rules and
produces a composite risk score (0 – 100), a risk level, and a list of
human-readable reasons explaining each triggered rule.
"""

from __future__ import annotations

from datetime import datetime, timezone

import networkx as nx


# ── Rule weights (sum of max contributions = 100) ─────────
_WEIGHTS = {
    "rapid_passthrough": 20,
    "fund_splitting": 20,
    "layering_depth": 20,
    "exchange_convergence": 15,
    "network_size": 10,
    "round_amounts": 10,
    "self_transfer": 5,
}


def score(graph: nx.DiGraph, start_address: str) -> dict:
    """
    Score the traced graph and return a dict with ``score``, ``level``,
    and ``reasons``.
    """
    start = start_address.lower()
    total = 0
    reasons: list[str] = []

    # ── 1. Rapid pass-through ─────────────────────────────
    rapid = _check_rapid_passthrough(graph)
    if rapid["triggered"]:
        total += rapid["points"]
        reasons.append(rapid["reason"])

    # ── 2. Fund splitting ─────────────────────────────────
    splitting = _check_fund_splitting(graph, start)
    if splitting["triggered"]:
        total += splitting["points"]
        reasons.append(splitting["reason"])

    # ── 3. Layering depth ─────────────────────────────────
    layering = _check_layering_depth(graph, start)
    if layering["triggered"]:
        total += layering["points"]
        reasons.append(layering["reason"])

    # ── 4. Exchange convergence ───────────────────────────
    convergence = _check_exchange_convergence(graph)
    if convergence["triggered"]:
        total += convergence["points"]
        reasons.append(convergence["reason"])

    # ── 5. Network size ───────────────────────────────────
    net_size = _check_network_size(graph)
    if net_size["triggered"]:
        total += net_size["points"]
        reasons.append(net_size["reason"])

    # ── 6. Round amounts ──────────────────────────────────
    rnd = _check_round_amounts(graph)
    if rnd["triggered"]:
        total += rnd["points"]
        reasons.append(rnd["reason"])

    # ── 7. Self-transfer ──────────────────────────────────
    self_tx = _check_self_transfer(graph)
    if self_tx["triggered"]:
        total += self_tx["points"]
        reasons.append(self_tx["reason"])

    # Clamp
    total = min(total, 100)

    level = "Low" if total < 35 else ("Medium" if total < 65 else "High")

    if not reasons:
        reasons.append("No suspicious patterns detected.")

    return {"score": total, "level": level, "reasons": reasons}


# ── Individual rules ──────────────────────────────────────

def _check_rapid_passthrough(graph: nx.DiGraph) -> dict:
    """Funds moved through a wallet within 10 minutes of arrival."""
    threshold_seconds = 600
    count = 0
    for node in graph.nodes:
        in_edges = list(graph.in_edges(node, data=True))
        out_edges = list(graph.out_edges(node, data=True))
        if not in_edges or not out_edges:
            continue
        earliest_in = min(e[2].get("timestamp", 0) for e in in_edges)
        earliest_out = min(e[2].get("timestamp", 0) for e in out_edges)
        if earliest_in > 0 and earliest_out > 0:
            diff = earliest_out - earliest_in
            if 0 < diff <= threshold_seconds:
                count += 1

    if count > 0:
        points = min(_WEIGHTS["rapid_passthrough"], count * 7)
        return {
            "triggered": True,
            "points": points,
            "reason": f"Rapid pass-through detected: {count} wallet(s) forwarded funds within 10 minutes of receipt.",
        }
    return {"triggered": False, "points": 0, "reason": ""}


def _check_fund_splitting(graph: nx.DiGraph, start: str) -> dict:
    """Suspect wallet sends to 3+ distinct destinations."""
    out_degree = graph.out_degree(start) if start in graph else 0
    if out_degree >= 3:
        points = min(_WEIGHTS["fund_splitting"], out_degree * 5)
        return {
            "triggered": True,
            "points": points,
            "reason": f"Fund splitting: suspect wallet sent funds to {out_degree} different wallets.",
        }
    return {"triggered": False, "points": 0, "reason": ""}


def _check_layering_depth(graph: nx.DiGraph, start: str) -> dict:
    """Longest path from the suspect wallet to any exchange is >= 3 hops."""
    exchange_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "exchange"]
    max_hops = 0
    for ex in exchange_nodes:
        try:
            path_len = nx.shortest_path_length(graph, start, ex)
            max_hops = max(max_hops, path_len)
        except nx.NetworkXNoPath:
            continue

    if max_hops >= 3:
        points = min(_WEIGHTS["layering_depth"], max_hops * 5)
        return {
            "triggered": True,
            "points": points,
            "reason": f"Layering detected: funds traversed up to {max_hops} hops before reaching an exchange.",
        }
    return {"triggered": False, "points": 0, "reason": ""}


def _check_exchange_convergence(graph: nx.DiGraph) -> dict:
    """Multiple paths converge to the same exchange."""
    exchange_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "exchange"]
    for ex in exchange_nodes:
        in_degree = graph.in_degree(ex)
        if in_degree >= 2:
            name = graph.nodes[ex].get("exchange_name", ex[:10])
            return {
                "triggered": True,
                "points": _WEIGHTS["exchange_convergence"],
                "reason": f"Exchange convergence: {in_degree} separate paths deposit into {name}.",
            }
    return {"triggered": False, "points": 0, "reason": ""}


def _check_network_size(graph: nx.DiGraph) -> dict:
    """The traced graph has an unusually large number of wallets."""
    n = graph.number_of_nodes()
    if n >= 8:
        points = min(_WEIGHTS["network_size"], (n - 5) * 2)
        return {
            "triggered": True,
            "points": points,
            "reason": f"Large network: {n} wallets involved in fund movement.",
        }
    return {"triggered": False, "points": 0, "reason": ""}


def _check_round_amounts(graph: nx.DiGraph) -> dict:
    """Transactions with suspiciously round ETH values (e.g. 1.0, 2.5, 5.0)."""
    round_count = 0
    for u, v, data in graph.edges(data=True):
        val = data.get("value_eth", 0)
        if val > 0 and (val == int(val) or val * 2 == int(val * 2)):
            round_count += 1

    if round_count >= 2:
        points = min(_WEIGHTS["round_amounts"], round_count * 3)
        return {
            "triggered": True,
            "points": points,
            "reason": f"Round amounts: {round_count} transactions have suspiciously round ETH values.",
        }
    return {"triggered": False, "points": 0, "reason": ""}


def _check_self_transfer(graph: nx.DiGraph) -> dict:
    """Any wallet sends to itself (potential obfuscation)."""
    for u, v in graph.edges():
        if u == v:
            return {
                "triggered": True,
                "points": _WEIGHTS["self_transfer"],
                "reason": "Self-transfer detected: a wallet sent funds to itself, possibly to obfuscate the trail.",
            }
    return {"triggered": False, "points": 0, "reason": ""}
