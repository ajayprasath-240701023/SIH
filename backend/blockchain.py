"""
Blockchain data layer.

* **Live mode** — async HTTP calls to the Etherscan API.
* **Demo mode** — loads transactions from the bundled sample dataset.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from backend import config

# ── In-memory cache (address → (timestamp, data)) ─────────
_cache: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL = 300  # seconds


def _cache_get(key: str) -> list[dict] | None:
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < _CACHE_TTL:
        return entry[1]
    return None


def _cache_set(key: str, data: list[dict]) -> None:
    _cache[key] = (time.time(), data)


# ── Demo dataset loader ───────────────────────────────────
_demo_data: dict[str, Any] | None = None


def _load_demo_data() -> dict[str, Any]:
    global _demo_data
    if _demo_data is None:
        path = config.DATA_DIR / "sample_transactions.json"
        with open(path, "r", encoding="utf-8") as f:
            _demo_data = json.load(f)
    return _demo_data


def get_demo_wallets() -> list[str]:
    """Return the list of suspect wallet addresses available in demo mode."""
    data = _load_demo_data()
    return data.get("suspect_wallets", [])


def get_all_demo_addresses() -> list[str]:
    """Return every address present in the demo dataset."""
    data = _load_demo_data()
    return list(data.get("wallets", {}).keys())


# ── Etherscan live fetcher ─────────────────────────────────
async def _fetch_etherscan(address: str) -> list[dict]:
    """Fetch normal transactions for *address* from Etherscan."""
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": config.MAX_TX_PER_ADDRESS,
        "sort": "asc",
        "apikey": config.ETHERSCAN_API_KEY,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(config.ETHERSCAN_BASE_URL, params=params)
        resp.raise_for_status()
        body = resp.json()

    if body.get("status") != "1":
        return []

    return body.get("result", [])


# ── Public API ─────────────────────────────────────────────
async def get_transactions(address: str) -> list[dict]:
    """
    Return a list of transaction dicts for *address*.

    Uses demo data or the Etherscan API depending on config.MODE.
    Results are cached in memory to avoid duplicate network calls during
    the BFS traversal.
    """
    address = address.lower()

    # Check cache first
    cached = _cache_get(address)
    if cached is not None:
        return cached

    if config.MODE == "demo":
        data = _load_demo_data()
        wallet_data = data.get("wallets", {}).get(address, {})
        txs = wallet_data.get("transactions", [])
        # Normalise field names to match Etherscan format
        normalised: list[dict] = []
        for tx in txs:
            normalised.append({
                "hash": tx.get("hash", ""),
                "from": tx.get("from", "").lower(),
                "to": tx.get("to", "").lower(),
                "value": tx.get("value_wei", "0"),
                "timeStamp": str(tx.get("timeStamp", "0")),
                "blockNumber": str(tx.get("blockNumber", "0")),
                "gas": tx.get("gas", "21000"),
                "gasPrice": tx.get("gasPrice", "20000000000"),
                "isError": tx.get("isError", "0"),
            })
        _cache_set(address, normalised)
        return normalised
    else:
        txs = await _fetch_etherscan(address)
        _cache_set(address, txs)
        return txs
