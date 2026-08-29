"""
Application configuration via environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# ── Etherscan ──────────────────────────────────────────────
ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")
ETHERSCAN_BASE_URL: str = "https://api.etherscan.io/api"

# ── Mode ───────────────────────────────────────────────────
# "demo" → use bundled sample data   "live" → hit Etherscan API
MODE: str = os.getenv("MODE", "demo").lower()

# ── Tracer limits ──────────────────────────────────────────
MAX_TRACE_DEPTH: int = int(os.getenv("MAX_TRACE_DEPTH", "3"))
MAX_TX_PER_ADDRESS: int = int(os.getenv("MAX_TX_PER_ADDRESS", "50"))

# ── Paths ──────────────────────────────────────────────────
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
TEMPLATES_DIR: Path = Path(__file__).resolve().parent / "templates"
FRONTEND_DIR: Path = PROJECT_ROOT / "frontend"
