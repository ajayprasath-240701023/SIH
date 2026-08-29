"""
/api/cases — in-memory case storage (placeholder for Phase 4 persistence).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.models import CaseDetail, CaseSummary, TraceResult

router = APIRouter(prefix="/api/cases", tags=["cases"])

# In-memory store
_cases: dict[str, CaseDetail] = {}


@router.post("", response_model=CaseSummary)
async def save_case(trace_result: TraceResult, notes: str = ""):
    """Save a completed trace as an investigation case."""
    case_id = trace_result.case_id

    detail = CaseDetail(
        case_id=case_id,
        trace_result=trace_result,
        created_at=datetime.now(tz=timezone.utc).isoformat(),
        notes=notes,
    )
    _cases[case_id] = detail

    return CaseSummary(
        case_id=case_id,
        wallet_address=trace_result.wallet_address,
        risk_level=trace_result.risk.level,
        risk_score=trace_result.risk.score,
        exchange_count=len(trace_result.exchange_matches),
        created_at=detail.created_at,
    )


@router.get("", response_model=list[CaseSummary])
async def list_cases():
    """List all saved cases."""
    summaries = []
    for detail in _cases.values():
        tr = detail.trace_result
        summaries.append(CaseSummary(
            case_id=detail.case_id,
            wallet_address=tr.wallet_address,
            risk_level=tr.risk.level,
            risk_score=tr.risk.score,
            exchange_count=len(tr.exchange_matches),
            created_at=detail.created_at,
        ))
    return summaries


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(case_id: str):
    """Retrieve a saved case by ID."""
    detail = _cases.get(case_id)
    if not detail:
        raise HTTPException(404, "Case not found.")
    return detail
