"""
Exchange / VASP address database.

Loads a seed JSON file of known exchange wallet addresses and provides
lookup helpers used by the tracer and risk scorer.
"""

from __future__ import annotations

import json
from typing import Optional

from backend import config


# ── Internal state ─────────────────────────────────────────
_exchange_map: dict[str, dict] | None = None


def _load() -> dict[str, dict]:
    """Load the exchange address file into an address → info dict."""
    global _exchange_map
    if _exchange_map is None:
        path = config.DATA_DIR / "known_exchanges.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _exchange_map = {}
        for entry in data.get("exchanges", []):
            addr = entry["address"].lower()
            _exchange_map[addr] = {
                "name": entry["name"],
                "type": entry.get("type", "hot_wallet"),
            }
    return _exchange_map


# ── Public API ─────────────────────────────────────────────
def lookup(address: str) -> Optional[dict]:
    """
    Look up a single address.

    Returns ``{"name": "Binance", "type": "hot_wallet"}`` or ``None``.
    """
    db = _load()
    return db.get(address.lower())


def is_exchange(address: str) -> bool:
    """Return True if *address* is a known exchange wallet."""
    return lookup(address) is not None


def get_exchange_name(address: str) -> Optional[str]:
    """Return the exchange name for *address*, or None."""
    info = lookup(address)
    return info["name"] if info else None


def match_addresses(addresses: list[str]) -> list[dict]:
    """
    Given a list of addresses, return all that are known exchanges.

    Each result dict contains ``address``, ``name``, and ``type``.
    """
    db = _load()
    matches = []
    for addr in addresses:
        info = db.get(addr.lower())
        if info:
            matches.append({
                "address": addr.lower(),
                "name": info["name"],
                "type": info["type"],
            })
    return matches


def get_all_exchange_addresses() -> list[str]:
    """Return all known exchange addresses."""
    db = _load()
    return list(db.keys())
