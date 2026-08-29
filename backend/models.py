"""
Pydantic models / schemas shared across the application.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Request / Input ────────────────────────────────────────
class TraceRequest(BaseModel):
    """Incoming request to trace a wallet address."""
    wallet_address: str = Field(..., description="Ethereum wallet address to trace")
    depth: int = Field(default=3, ge=1, le=5, description="Max BFS hop depth")


# ── Blockchain primitives ─────────────────────────────────
class Transaction(BaseModel):
    """A single on-chain transaction."""
    hash: str
    from_addr: str = Field(..., alias="from_address")
    to_addr: str = Field(..., alias="to_address")
    value_eth: float
    value_wei: str = ""
    timestamp: int = 0
    block_number: int = 0
    gas: str = ""
    gas_price: str = ""
    is_error: bool = False

    model_config = {"populate_by_name": True}


# ── Graph node / edge ─────────────────────────────────────
class GraphNode(BaseModel):
    """A wallet node in the traced fund-flow graph."""
    id: str                          # wallet address (lowercase)
    label: str = ""                  # short label or address snippet
    type: str = "unknown"            # suspect | intermediary | exchange | victim | unknown
    exchange_name: Optional[str] = None
    risk_flags: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    """A directed edge (transaction) between two wallets."""
    from_addr: str
    to_addr: str
    value_eth: float
    tx_hash: str
    timestamp: int = 0
    label: str = ""                  # e.g. "2.5 ETH"


# ── Risk scoring ──────────────────────────────────────────
class RiskResult(BaseModel):
    """Explainable risk assessment."""
    score: int = Field(ge=0, le=100)
    level: str           # Low | Medium | High
    reasons: list[str]


# ── Exchange match ────────────────────────────────────────
class ExchangeMatch(BaseModel):
    """A matched exchange/VASP wallet."""
    address: str
    exchange_name: str
    wallet_type: str = "hot_wallet"
    total_received_eth: float = 0.0


# ── Full trace result ─────────────────────────────────────
class TraceResult(BaseModel):
    """Complete output of a fund-flow trace."""
    case_id: str
    wallet_address: str
    mode: str                         # demo | live
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    transactions: list[Transaction]
    risk: RiskResult
    exchange_matches: list[ExchangeMatch]
    summary: str = ""
    trace_depth: int = 0
    total_wallets: int = 0
    total_transactions: int = 0
    total_value_eth: float = 0.0


# ── Case (saved investigation) ────────────────────────────
class CaseSummary(BaseModel):
    """Summary of a saved case for list views."""
    case_id: str
    wallet_address: str
    risk_level: str
    risk_score: int
    exchange_count: int
    created_at: str


class CaseDetail(BaseModel):
    """Full saved case."""
    case_id: str
    trace_result: TraceResult
    created_at: str
    notes: str = ""
