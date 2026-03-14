"""Shared utilities for the UCM data pipeline."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def sha256_file(path: str | Path) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(path: str | Path) -> None:
    """Create directory and parents if they don't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def read_tsv(path: str | Path) -> pd.DataFrame | None:
    """Read a TSV file. Returns None if file doesn't exist."""
    p = Path(path)
    if not p.exists():
        return None
    return pd.read_csv(p, sep="\t", dtype=str, keep_default_na=False)


def normalize_confidence(x: Any) -> float:
    """Clamp a value to [0.0, 1.0] float."""
    try:
        v = float(x)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, v))


def now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix: str, *parts: str) -> str:
    """Create a deterministic ID from parts (not for biology IDs)."""
    raw = "|".join(p.strip() for p in parts if p is not None)
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}{h}"
