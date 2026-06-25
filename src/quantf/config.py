from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "quantf.duckdb"
DEFAULT_WATCHLIST_PATH = PROJECT_ROOT / "configs" / "watchlist.yaml"
DEFAULT_ALERTS_PATH = PROJECT_ROOT / "configs" / "alerts.yaml"
DEFAULT_PORTFOLIO_PATH = PROJECT_ROOT / "configs" / "portfolio.example.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_watchlist(path: Path = DEFAULT_WATCHLIST_PATH) -> list[str]:
    config = load_yaml(path)
    symbols: list[str] = []
    for group_symbols in config.get("symbols", {}).values():
        symbols.extend(group_symbols or [])
    return sorted(set(symbol.upper() for symbol in symbols))
