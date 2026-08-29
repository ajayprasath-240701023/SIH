"""
/api/trace — fund-flow tracing endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from backend import config
from backend.blockchain import get_demo_wallets
from backend.exchange_db import match_addresses, lookup
from backend.models import (
    ExchangeMatch,
    GraphEdge,
    GraphNode,
    RiskResult,
    TraceRequest,
    TraceResult,
)
from backend.report_generator import generate_html_report
from backend.risk_scorer import score as score_graph
from backend.tracer import trace_fund_flow

router = APIRouter(prefix="/api", tags=["trace"])

# In-memory store so the report endpoint can look up results by case_id
_results_store: dict[str, TraceResult] = {}


@router.get("/demo-wallets")
async def demo_wallets():
    """Return demo wallet addresses for quick testing."""
    return {
        "wallets": get_demo_wallets(),
        "mode": config.MODE,
    }


@router.post("/trace", response_model=TraceResult)
async def run_trace(req: TraceRequest):
    """
    Trace fund flow from a wallet address.

    1. BFS fund-flow traversal
    2. Risk scoring
    3. Exchange matching
    4. Build structured result
    """
    address = req.wallet_address.strip().lower()
    if not address:
        raise HTTPException(400, "wallet_address is required")

    # ── 1. Trace ──────────────────────────────────────────
    graph, all_txs = await trace_fund_flow(address, max_depth=req.depth)

    if graph.number_of_nodes() == 0:
        raise HTTPException(404, "No transactions found for this address.")

    # ── 2. Risk score ─────────────────────────────────────
    risk_raw = score_graph(graph, address)

    # ── 3. Exchange matches ───────────────────────────────
    all_addrs = list(graph.nodes)
    ex_matches_raw = match_addresses(all_addrs)

    # Compute total ETH received at each matched exchange
    exchange_matches: list[ExchangeMatch] = []
    for em in ex_matches_raw:
        total_eth = sum(
            d.get("value_eth", 0)
            for _, _, d in graph.in_edges(em["address"], data=True)
        )
        exchange_matches.append(ExchangeMatch(
            address=em["address"],
            exchange_name=em["name"],
            wallet_type=em["type"],
            total_received_eth=round(total_eth, 6),
        ))

    # ── 4. Build nodes / edges for the frontend ──────────
    nodes: list[GraphNode] = []
    for nid, ndata in graph.nodes(data=True):
        nodes.append(GraphNode(
            id=nid,
            label=ndata.get("label", nid[:10]),
            type=ndata.get("type", "unknown"),
            exchange_name=ndata.get("exchange_name"),
        ))

    edges: list[GraphEdge] = []
    for u, v, edata in graph.edges(data=True):
        edges.append(GraphEdge(
            from_addr=u,
            to_addr=v,
            value_eth=round(edata.get("value_eth", 0), 6),
            tx_hash=edata.get("tx_hash", ""),
            timestamp=edata.get("timestamp", 0),
            label=f"{edata.get('value_eth', 0):.4f} ETH",
        ))

    # ── 5. Summary text ──────────────────────────────────
    ex_names = list({em.exchange_name for em in exchange_matches})
    total_value = sum(e.value_eth for e in edges) / 2  # edges are double-counted in/out
    total_value = sum(
        edata.get("value_eth", 0)
        for _, _, edata in graph.out_edges(address, data=True)
    )

    summary_parts = [
        f"Traced {graph.number_of_nodes()} wallets and {graph.number_of_edges()} connections from suspect address {address[:10]}…",
    ]
    if ex_names:
        summary_parts.append(f"Funds ultimately reached: {', '.join(ex_names)}.")
    summary_parts.append(f"Risk level: {risk_raw['level']} ({risk_raw['score']}/100).")

    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"

    result = TraceResult(
        case_id=case_id,
        wallet_address=address,
        mode=config.MODE,
        nodes=nodes,
        edges=edges,
        transactions=[],  # kept slim; full txs available in graph
        risk=RiskResult(**risk_raw),
        exchange_matches=exchange_matches,
        summary=" ".join(summary_parts),
        trace_depth=req.depth,
        total_wallets=graph.number_of_nodes(),
        total_transactions=graph.number_of_edges(),
        total_value_eth=round(total_value, 6),
    )

    _results_store[case_id] = result
    return result


@router.get("/trace/{case_id}/report", response_class=HTMLResponse)
async def get_report(case_id: str):
    """Return the HTML investigation report for a completed trace."""
    result = _results_store.get(case_id)
    if not result:
        raise HTTPException(404, "Case not found. Run a trace first.")
    return generate_html_report(result)
