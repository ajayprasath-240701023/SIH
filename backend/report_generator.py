"""
Automated investigation report generator.

Renders an HTML report from a Jinja2 template that includes case metadata,
risk score breakdown, transaction timeline, exchange matches, and a
fund-flow summary. The HTML is print-friendly (can be saved as PDF via
the browser's Print → Save as PDF).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from backend import config
from backend.models import TraceResult

# ── Template engine ────────────────────────────────────────
_env = Environment(
    loader=FileSystemLoader(str(config.TEMPLATES_DIR)),
    autoescape=True,
)


def _ts_to_str(ts: int) -> str:
    """Convert a UNIX timestamp to a human-readable UTC string."""
    if ts <= 0:
        return "N/A"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def generate_html_report(result: TraceResult) -> str:
    """
    Render the full investigation report as an HTML string.
    """
    template = _env.get_template("report.html")

    # Prepare transaction rows
    tx_rows = []
    seen_hashes: set[str] = set()
    for edge in result.edges:
        if edge.tx_hash in seen_hashes:
            continue
        seen_hashes.add(edge.tx_hash)
        tx_rows.append({
            "hash": edge.tx_hash,
            "from": edge.from_addr,
            "to": edge.to_addr,
            "value_eth": f"{edge.value_eth:.4f}",
            "time": _ts_to_str(edge.timestamp),
        })

    return template.render(
        case_id=result.case_id,
        wallet_address=result.wallet_address,
        mode=result.mode,
        risk_score=result.risk.score,
        risk_level=result.risk.level,
        risk_reasons=result.risk.reasons,
        exchange_matches=result.exchange_matches,
        transactions=tx_rows,
        total_wallets=result.total_wallets,
        total_transactions=result.total_transactions,
        total_value_eth=f"{result.total_value_eth:.4f}",
        trace_depth=result.trace_depth,
        generated_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        summary=result.summary,
    )
