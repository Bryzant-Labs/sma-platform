"""Semantic search engine for SMA Research Platform.

Uses sentence-transformers (all-mpnet-base-v2, 768-dim) + FAISS for vector
similarity search across claims and sources.  Supports pure semantic,
keyword-only, and hybrid (vector + keyword) modes.

Model and index are loaded lazily on first use so that importing this module
has zero startup cost.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from ..core.database import fetch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy globals — populated on first use
# ---------------------------------------------------------------------------
_model: Any = None  # SentenceTransformer instance
_claims_index: Any = None  # faiss.Index
_sources_index: Any = None
_claims_ids: list[str] = []
_sources_ids: list[str] = []
_index_meta: dict = {}

MODEL_NAME = "all-mpnet-base-v2"
EMBEDDING_DIM = 768
DEFAULT_DATA_DIR = "/home/bryzant/sma-platform/data/search_index"


# ---------------------------------------------------------------------------
# Model loading (lazy)
# ---------------------------------------------------------------------------

def _get_model():
    """Return the SentenceTransformer model, loading it on first call."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers model %s ...", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded (dim=%d)", EMBEDDING_DIM)
    return _model


# ---------------------------------------------------------------------------
# Text preparation helpers
# ---------------------------------------------------------------------------

def _claim_text(row: dict) -> str:
    """Build the embedding text for a claim row."""
    parts = [row.get("predicate") or ""]

    meta = row.get("metadata")
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except (json.JSONDecodeError, TypeError):
            meta = {}
    elif meta is None:
        meta = {}

    subject_label = meta.get("subject_label") or row.get("subject_type") or ""
    object_label = meta.get("object_label") or row.get("object_type") or ""
    claim_type = (row.get("claim_type") or "").replace("_", " ")

    if subject_label:
        parts.insert(0, subject_label)
    if object_label:
        parts.append(object_label)
    if claim_type:
        parts.append(f"[{claim_type}]")

    return " ".join(parts).strip()


def _source_text(row: dict) -> str:
    """Build the embedding text for a source row."""
    title = row.get("title") or ""
    abstract = row.get("abstract") or ""
    # Limit abstract to first 500 chars to keep embeddings focused
    if len(abstract) > 500:
        abstract = abstract[:500]
    return f"{title} {abstract}".strip()


# ---------------------------------------------------------------------------
# Index build / load
# ---------------------------------------------------------------------------

async def build_index(data_dir: str = DEFAULT_DATA_DIR) -> dict:
    """Fetch all claims + sources from DB, compute embeddings, save FAISS indexes.

    Returns metadata dict with counts and timing.
    """
    import faiss

    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    t0 = time.time()

    # ---- Fetch data (async) ----
    logger.info("Fetching claims from database ...")
    claim_rows = await fetch(
        "SELECT id, claim_type, subject_type, predicate, object_type, metadata FROM claims"
    )
    logger.info("Fetched %d claims", len(claim_rows))

    logger.info("Fetching sources from database ...")
    source_rows = await fetch(
        "SELECT id, title, abstract FROM sources WHERE abstract IS NOT NULL AND abstract != ''"
    )
    logger.info("Fetched %d sources with abstracts", len(source_rows))

    # ---- Prepare texts ----
    claim_texts = [_claim_text(dict(r)) for r in claim_rows]
    claim_ids = [str(r["id"]) for r in claim_rows]

    source_texts = [_source_text(dict(r)) for r in source_rows]
    source_ids = [str(r["id"]) for r in source_rows]

    # ---- Compute embeddings (CPU-bound → run in executor) ----
    loop = asyncio.get_event_loop()
    model = _get_model()

    logger.info("Encoding %d claim texts ...", len(claim_texts))
    claim_embeddings = await loop.run_in_executor(
        None, lambda: model.encode(claim_texts, show_progress_bar=True, batch_size=256)
    )

    logger.info("Encoding %d source texts ...", len(source_texts))
    source_embeddings = await loop.run_in_executor(
        None, lambda: model.encode(source_texts, show_progress_bar=True, batch_size=256)
    )

    # ---- Build FAISS indexes ----
    claim_embeddings = np.array(claim_embeddings, dtype="float32")
    source_embeddings = np.array(source_embeddings, dtype="float32")

    # Normalize for cosine similarity via inner-product index
    faiss.normalize_L2(claim_embeddings)
    faiss.normalize_L2(source_embeddings)

    claims_idx = faiss.IndexFlatIP(EMBEDDING_DIM)
    claims_idx.add(claim_embeddings)

    sources_idx = faiss.IndexFlatIP(EMBEDDING_DIM)
    sources_idx.add(source_embeddings)

    # ---- Save to disk ----
    faiss.write_index(claims_idx, str(data_path / "claims.index"))
    faiss.write_index(sources_idx, str(data_path / "sources.index"))

    with open(data_path / "claims_ids.json", "w") as f:
        json.dump(claim_ids, f)
    with open(data_path / "sources_ids.json", "w") as f:
        json.dump(source_ids, f)

    elapsed = round(time.time() - t0, 2)
    meta = {
        "model": MODEL_NAME,
        "embedding_dim": EMBEDDING_DIM,
        "claims_count": len(claim_ids),
        "sources_count": len(source_ids),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "build_time_secs": elapsed,
    }
    with open(data_path / "index_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    # Populate module-level cache so search works immediately
    global _claims_index, _sources_index, _claims_ids, _sources_ids, _index_meta
    _claims_index = claims_idx
    _sources_index = sources_idx
    _claims_ids = claim_ids
    _sources_ids = source_ids
    _index_meta = meta

    logger.info("Index built in %.1fs — %d claims, %d sources", elapsed, len(claim_ids), len(source_ids))
    return meta


def load_index(data_dir: str = DEFAULT_DATA_DIR) -> bool:
    """Load pre-built FAISS indexes from disk into module globals.

    Returns True if indexes were loaded, False if files don't exist.
    """
    import faiss

    global _claims_index, _sources_index, _claims_ids, _sources_ids, _index_meta

    data_path = Path(data_dir)
    required = ["claims.index", "sources.index", "claims_ids.json", "sources_ids.json", "index_meta.json"]
    if not all((data_path / f).exists() for f in required):
        logger.warning("Index files not found in %s — run /search/reindex first", data_dir)
        return False

    _claims_index = faiss.read_index(str(data_path / "claims.index"))
    _sources_index = faiss.read_index(str(data_path / "sources.index"))

    with open(data_path / "claims_ids.json") as f:
        _claims_ids = json.load(f)
    with open(data_path / "sources_ids.json") as f:
        _sources_ids = json.load(f)
    with open(data_path / "index_meta.json") as f:
        _index_meta = json.load(f)

    logger.info("Index loaded — %d claims, %d sources", len(_claims_ids), len(_sources_ids))
    return True


def _ensure_index(data_dir: str = DEFAULT_DATA_DIR) -> bool:
    """Make sure the index is loaded, loading from disk if needed."""
    if _claims_index is not None and _sources_index is not None:
        return True
    return load_index(data_dir)


# ---------------------------------------------------------------------------
# Search functions
# ---------------------------------------------------------------------------

async def search(query: str, top_k: int = 20, data_dir: str = DEFAULT_DATA_DIR) -> list[dict]:
    """Pure vector similarity search across both claims and sources indexes.

    Returns up to top_k results sorted by descending cosine similarity score.
    """
    if not _ensure_index(data_dir):
        return []

    model = _get_model()
    loop = asyncio.get_event_loop()

    # Encode query in executor to avoid blocking
    q_vec = await loop.run_in_executor(
        None, lambda: model.encode([query], normalize_embeddings=True)
    )
    q_vec = np.array(q_vec, dtype="float32")

    results: list[dict] = []

    # Search claims
    if _claims_index is not None and _claims_index.ntotal > 0:
        k_claims = min(top_k, _claims_index.ntotal)
        scores, indices = _claims_index.search(q_vec, k_claims)
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append({
                "type": "claim",
                "id": _claims_ids[idx],
                "score": round(float(score), 4),
            })

    # Search sources
    if _sources_index is not None and _sources_index.ntotal > 0:
        k_sources = min(top_k, _sources_index.ntotal)
        scores, indices = _sources_index.search(q_vec, k_sources)
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append({
                "type": "source",
                "id": _sources_ids[idx],
                "score": round(float(score), 4),
            })

    # Merge by score, take top_k
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


async def _keyword_search(query: str, top_k: int = 20) -> list[dict]:
    """SQL ILIKE keyword search across claims and sources."""
    pattern = f"%{query}%"

    claim_rows = await fetch(
        """SELECT id, 'claim' AS type FROM claims
           WHERE predicate ILIKE $1
              OR claim_type ILIKE $1
              OR subject_type ILIKE $1
              OR object_type ILIKE $1
              OR metadata::text ILIKE $1
           LIMIT $2""",
        pattern, top_k,
    )

    source_rows = await fetch(
        """SELECT id, 'source' AS type FROM sources
           WHERE title ILIKE $1
              OR abstract ILIKE $1
              OR journal ILIKE $1
           LIMIT $2""",
        pattern, top_k,
    )

    results: list[dict] = []
    for r in claim_rows:
        results.append({"type": "claim", "id": str(r["id"]), "score": 0.5})
    for r in source_rows:
        results.append({"type": "source", "id": str(r["id"]), "score": 0.5})

    return results[:top_k]


async def hybrid_search(query: str, top_k: int = 20, data_dir: str = DEFAULT_DATA_DIR) -> list[dict]:
    """Combine vector similarity + keyword SQL search, deduplicate, re-rank.

    Scoring: vector score (0-1) + 0.3 keyword bonus for items found by both.
    """
    # Run both searches in parallel
    vector_results, keyword_results = await asyncio.gather(
        search(query, top_k=top_k * 2, data_dir=data_dir),
        _keyword_search(query, top_k=top_k * 2),
    )

    # Build lookup by (type, id)
    merged: dict[tuple[str, str], dict] = {}

    for r in vector_results:
        key = (r["type"], r["id"])
        merged[key] = {**r, "match_modes": ["semantic"]}

    for r in keyword_results:
        key = (r["type"], r["id"])
        if key in merged:
            # Boost score for items found by both methods
            merged[key]["score"] = min(merged[key]["score"] + 0.3, 1.0)
            merged[key]["match_modes"].append("keyword")
        else:
            merged[key] = {**r, "match_modes": ["keyword"]}

    results = sorted(merged.values(), key=lambda r: r["score"], reverse=True)
    return results[:top_k]


async def get_index_stats(data_dir: str = DEFAULT_DATA_DIR) -> dict:
    """Return index statistics: size, model info, last build time."""
    data_path = Path(data_dir)
    meta_file = data_path / "index_meta.json"

    if meta_file.exists():
        with open(meta_file) as f:
            meta = json.load(f)
    elif _index_meta:
        meta = _index_meta
    else:
        meta = {}

    # Add live index status
    loaded = _claims_index is not None and _sources_index is not None
    index_files_exist = all(
        (data_path / f).exists()
        for f in ["claims.index", "sources.index", "claims_ids.json", "sources_ids.json"]
    )

    # Disk sizes
    disk_bytes = 0
    if index_files_exist:
        for f in data_path.iterdir():
            if f.is_file():
                disk_bytes += f.stat().st_size

    return {
        "model": meta.get("model", MODEL_NAME),
        "embedding_dim": meta.get("embedding_dim", EMBEDDING_DIM),
        "claims_indexed": meta.get("claims_count", 0),
        "sources_indexed": meta.get("sources_count", 0),
        "built_at": meta.get("built_at"),
        "build_time_secs": meta.get("build_time_secs"),
        "index_loaded": loaded,
        "index_files_exist": index_files_exist,
        "disk_size_mb": round(disk_bytes / (1024 * 1024), 2) if disk_bytes else 0,
    }
