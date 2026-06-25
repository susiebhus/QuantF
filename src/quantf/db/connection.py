from __future__ import annotations

from pathlib import Path

import duckdb

from quantf.config import DEFAULT_DB_PATH


def connect(db_path: Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))
