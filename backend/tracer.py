"""
Multi-hop BFS fund-flow tracer.

Starting from a suspect wallet address, performs a breadth-first traversal
of outgoing transactions up to a configurable depth. At each hop the tracer
fetches transactions via the blockchain module and builds a NetworkX DiGraph
annotating each edge with transaction metadata.
"""

from __future__ import annotations

import asyncio
from collections import deque

import networkx as nx

from backend import config
from backend.blockchain import get_transactions
from backend.exchange_db import is_exchange, get_exchange_name


async def trace_fund_flow(
    start_address: str,
    max_depth: int | None = None,
) -> tuple[nx.DiGraph, list[dict]]:
    """
    Trace outgoing fund flow from *start_address*.

    Returns
    -------
    graph : nx.DiGraph
        Nodes carry ``type``, ``label``, ``exchange_name`` attributes.
        Edges carry ``value_eth``, ``tx_hash``, ``timestamp`` attributes.
    all_transactions : list[dict]
        Flat list of every raw transaction encountered during the BFS.
    """
    if max_depth is None:
        max_depth = config.MAX_TRACE_DEPTH

    start = start_address.lower()
    graph = nx.DiGraph()
    all_txs: list[dict] = []

    # BFS state
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()  # (address, current_depth)
    queue.append((start, 0))

    # Mark the start node
    graph.add_node(start, type="suspect", label="Suspect", exchange_name=None)

    while queue:
        address, depth = queue.popleft()

        if address in visited:
            continue
        visited.add(address)

        # Don't expand exchange wallets (they are endpoints)
        if depth > 0 and is_exchange(address):
            continue

        # Don't exceed max depth
        if depth > max_depth:
            continue

        # Fetch transactions
        raw_txs = await get_transactions(address)
        all_txs.extend(raw_txs)

        for tx in raw_txs:
            from_addr = tx.get("from", "").lower()
            to_addr = tx.get("to", "").lower()
            if not to_addr:
                continue

            value_wei = int(tx.get("value", "0") or "0")
            value_eth = value_wei / 1e18
            tx_hash = tx.get("hash", "")
            timestamp = int(tx.get("timeStamp", "0") or "0")

            # We only trace *outgoing* from the current address
            if from_addr != address:
                # Still record the incoming edge for context, but don't enqueue
                if not graph.has_node(from_addr):
                    ex_name = get_exchange_name(from_addr)
                    node_type = "exchange" if ex_name else "unknown"
                    graph.add_node(from_addr, type=node_type, label=ex_name or _short(from_addr), exchange_name=ex_name)
                if not graph.has_edge(from_addr, address):
                    graph.add_edge(
                        from_addr, address,
                        value_eth=value_eth,
                        tx_hash=tx_hash,
                        timestamp=timestamp,
                    )
                continue

            # Outgoing edge — add destination node
            if not graph.has_node(to_addr):
                ex_name = get_exchange_name(to_addr)
                if ex_name:
                    node_type = "exchange"
                    label = ex_name
                elif depth + 1 <= max_depth:
                    node_type = "intermediary"
                    label = f"Wallet {_short(to_addr)}"
                else:
                    node_type = "unknown"
                    label = _short(to_addr)
                graph.add_node(to_addr, type=node_type, label=label, exchange_name=ex_name)

            # Add edge (or update if a higher-value tx exists)
            if graph.has_edge(address, to_addr):
                existing = graph[address][to_addr].get("value_eth", 0)
                graph[address][to_addr]["value_eth"] = existing + value_eth
                graph[address][to_addr]["tx_hash"] = tx_hash  # keep latest
                graph[address][to_addr]["timestamp"] = max(
                    graph[address][to_addr].get("timestamp", 0), timestamp
                )
            else:
                graph.add_edge(
                    address, to_addr,
                    value_eth=value_eth,
                    tx_hash=tx_hash,
                    timestamp=timestamp,
                )

            # Enqueue destination for the next hop
            if to_addr not in visited and depth + 1 <= max_depth:
                queue.append((to_addr, depth + 1))

    return graph, all_txs


def _short(address: str) -> str:
    """Shorten an address for display labels."""
    if len(address) > 10:
        return address[:6] + "…" + address[-4:]
    return address
