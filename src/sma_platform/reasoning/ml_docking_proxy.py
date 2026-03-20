"""
ML Docking Proxy -- Fast binding prediction from DiffDock training data
======================================================================
Trains a random forest on Morgan fingerprints -> DiffDock confidence scores.
Enables screening 1M+ molecules without GPU docking.

Training: 4,116 DiffDock v2.2 results (630 compounds x 7 targets)
Features: 2048-bit Morgan fingerprint (ECFP4) + 7-dim target one-hot
Target: DiffDock confidence score (continuous, typically -3 to +1)

Upgrade from v1 docking_proxy.py:
- v1: 12 SMILES string-level features (character counting)
- v2: 2048-bit Morgan/ECFP4 fingerprints (captures real molecular topology)
- v2 also loads the 10k_screen batch results (4,116 compounds) from moltbot

Feature engineering: RDKit Morgan fingerprints when available; falls back
to the v1 SMILES string descriptors if RDKit is not installed.
Model: sklearn RandomForestRegressor (primary) or GradientBoosting; k-NN fallback.

Security note: pickle is used for sklearn model persistence to /tmp. The model
file is only ever loaded from a fixed local path that we control -- never from
user-supplied paths or network sources. sklearn models cannot be serialized to
JSON; pickle is the standard approach for scikit-learn model persistence.
"""

from __future__ import annotations

import json
import logging
import math
import os
import pickle  # noqa: S403 -- safe: only loads from fixed local path we control
import random
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RDKit availability
# ---------------------------------------------------------------------------

_USE_RDKIT = False
try:
    from rdkit import Chem  # type: ignore[import-untyped]
    from rdkit.Chem import AllChem, Descriptors  # type: ignore[import-untyped]
    _USE_RDKIT = True
    logger.info("RDKit available -- using Morgan fingerprints (ECFP4, 2048-bit)")
except ImportError:
    logger.info("RDKit not available -- falling back to SMILES string features")

# ---------------------------------------------------------------------------
# sklearn availability
# ---------------------------------------------------------------------------

_USE_SKLEARN = False
try:
    from sklearn.ensemble import (  # type: ignore[import-untyped]
        GradientBoostingRegressor,
        RandomForestRegressor,
    )
    from sklearn.metrics import mean_absolute_error, r2_score as sklearn_r2  # type: ignore[import-untyped]
    from sklearn.model_selection import cross_val_score  # type: ignore[import-untyped]
    _USE_SKLEARN = True
except ImportError:
    logger.info("sklearn not available -- using built-in k-NN proxy model")

# ---------------------------------------------------------------------------
# Paths -- resolved relative to project root (gpu/results/)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # sma-platform/
_RESULTS_DIR = _PROJECT_ROOT / "gpu" / "results"

# Legacy result files (v1)
_V1_RESULTS = _RESULTS_DIR / "diffdock_results.json"
_MULTI_RESULTS = _RESULTS_DIR / "diffdock_multi_results.json"
_NIM_BATCH_RESULTS = _RESULTS_DIR / "nim_batch" / "diffdock_results.json"

# New 10k_screen batch results (v2 -- 4,116 entries, on moltbot)
_10K_SCREEN_RESULTS = _RESULTS_DIR / "10k_screen" / "diffdock_results.json"
_10K_SCREEN_CHECKPOINT = _RESULTS_DIR / "10k_screen" / "checkpoint.json"

_MODEL_PATH = Path("/tmp/sma_ml_docking_proxy_v2.pkl")

# ---------------------------------------------------------------------------
# Morgan fingerprint parameters
# ---------------------------------------------------------------------------

MORGAN_RADIUS = 2       # ECFP4 (radius 2 = diameter 4)
MORGAN_NBITS = 2048     # standard fingerprint length
TARGET_DIM = 7           # one-hot encoding dimension

# Feature dimension: 2048 (Morgan) + 7 (target) = 2055 when RDKit available
# Fallback: 12 (string) + 7 (target) = 19 when RDKit not available
FEATURE_DIM = MORGAN_NBITS + TARGET_DIM if _USE_RDKIT else 19

# ---------------------------------------------------------------------------
# Known SMA targets (one-hot encoding order)
# ---------------------------------------------------------------------------

SMA_TARGETS = ["SMN2", "SMN1", "PLS3", "STMN2", "NCALD", "UBA1", "CORO1C"]
_TARGET_INDEX = {t: i for i, t in enumerate(SMA_TARGETS)}

# ---------------------------------------------------------------------------
# Known compound SMILES (from our screening library + ChEMBL lookups)
# Used to map compound names / IDs back to SMILES for feature extraction.
# ---------------------------------------------------------------------------

KNOWN_SMILES: dict[str, str] = {
    # Named drugs
    "4-aminopyridine": "Nc1ccncc1",
    "riluzole": "Nc1nc2cc(OC(F)(F)F)ccc2s1",
    "valproic_acid": "CCCC(CCC)C(=O)O",
    "risdiplam": "N=c1[nH]c(=O)c2c(n1)c(-c1cnc3ccccc3n1)cc1c(C(F)(F)F)nn(-c3ccccn3)c12",
    # ChEMBL compounds -- representative SMA splicing modifiers & screening hits
    "CHEMBL1575581": "O=C(Nc1ccc(-c2nc3cc(F)ccc3[nH]2)cc1)c1ccncc1",
    "CHEMBL1328375": "O=C(Nc1ccc(-c2nc3ccccc3[nH]2)cc1)c1ccncc1",
    "CHEMBL1301789": "CC(=O)Nc1ccc(-c2nc3cc(Cl)ccc3[nH]2)cc1",
    "CHEMBL1399783": "O=C(Nc1cccc(-c2nc3ccccc3[nH]2)c1)c1ccncc1",
    "CHEMBL1320775": "O=C(Nc1ccc(-c2nc3cc(C(F)(F)F)ccc3[nH]2)cc1)c1ccncc1",
    "CHEMBL1604526": "Cn1c(=O)c2cc(-c3ccc(NC(=O)c4ccncc4)cc3)ccc2n1C",
    "CHEMBL1399869": "O=C(Nc1ccc(-c2nc3ccc(F)cc3[nH]2)cc1)c1ccncc1",
    "CHEMBL1409019": "O=C(Nc1ccccc1-c1nc2ccccc2[nH]1)c1ccncc1",
    "CHEMBL1420277": "O=C(Nc1ccc(-c2nc3cc(OC(F)(F)F)ccc3[nH]2)cc1)c1ccncc1",
    "CHEMBL1329887": "CC(=O)Nc1ccc(-c2nc3ccccc3[nH]2)cc1",
    "CHEMBL1301787": "O=C(Nc1ccc(-c2nc3ccccc3[nH]2)cc1)c1ccccc1",
    "CHEMBL1411446": "O=C(Nc1ccc(-c2nc3cc(C#N)ccc3[nH]2)cc1)c1ccncc1",
    "CHEMBL1408926": "CCc1ccc(-c2[nH]c3ccccc3n2)cc1NC(=O)c1ccncc1",
    "CHEMBL1301860": "CC(=O)Nc1ccc(-c2nc3cc(F)ccc3[nH]2)cc1",
    "CHEMBL1410628": "O=C(Nc1ccc(-c2nc3cc(Br)ccc3[nH]2)cc1)c1ccncc1",
    "CHEMBL1527043": "Cn1c(=O)c2ccc(-c3ccc(NC(=O)c4ccncc4)cc3)cc2n1C",
    "CHEMBL1421168": "O=C(Nc1ccc2[nH]c(-c3ccc(O)cc3)nc2c1)c1ccncc1",
    "CHEMBL1411716": "O=C(Nc1ccc(-c2nc3cc(C(F)(F)F)ccc3[nH]2)cc1)c1cccnc1",
    "CHEMBL1339798": "Nc1ccc(-c2nc3ccc(C(F)(F)F)cc3[nH]2)cc1",
    "CHEMBL1409365": "O=C(Nc1ccc2[nH]c(-c3ccccc3)nc2c1)c1ccncc1",
    "CHEMBL1381595": "CC(=O)Nc1ccc(-c2nc3cc(OC(F)(F)F)ccc3[nH]2)cc1",
    "CHEMBL1411784": "O=C(Nc1ccc(-c2nc3ccc(Cl)cc3[nH]2)cc1)c1ccncc1",
    "CHEMBL1301743": "O=C(Nc1ccc(-c2nc3ccccc3[nH]2)cc1)c1cccc(O)c1",
    "CHEMBL36": "CC(=O)Oc1ccccc1C(=O)O",  # aspirin
    "CHEMBL3190627": "O=C(Nc1ccc2c(c1)nc(-c1ccc(F)cc1)n2C1CC1)c1ccncc1",
    "CHEMBL1319158": "O=C(Nc1ccc(-c2nc3cc(Cl)ccc3[nH]2)cc1)c1ccccc1",
    "CHEMBL1381710": "O=C(Nc1ccc(-c2nc3cc(Cl)ccc3[nH]2)cc1)c1cccnc1",
    "CHEMBL1332861": "O=C(Nc1ccc(-c2nc3cc(F)ccc3[nH]2)cc1)c1ccncc1",
    "CHEMBL1419250": "O=C(Nc1ccc(-c2nc3ccc(F)cc3[nH]2)cc1)c1cccnc1",
    "CHEMBL1360645": "O=C(Nc1cccc(-c2nc3ccc(F)cc3[nH]2)c1)c1ccncc1",
    "CHEMBL137448": "O=c1[nH]c(=O)n(C2CCCO2)cc1F",
    "CHEMBL1372066": "O=C(Nc1cccc(-c2nc3ccccc3[nH]2)c1)c1ccncc1",
    "CHEMBL1409166": "O=C(Nc1ccc(-c2nc3cc(F)ccc3[nH]2)cc1)c1ccccc1",
    "CHEMBL1340738": "O=C(Nc1cccc(-c2nc3cc(Cl)ccc3[nH]2)c1)c1ccncc1",
    "CHEMBL1331875": "O=C(Nc1cccc(-c2nc3cc(F)ccc3[nH]2)c1)c1ccncc1",
    "CHEMBL1411542": "O=C(Nc1ccc(-c2nc3ccccc3[nH]2)cc1)c1cccnc1",
    "CHEMBL1409329": "O=C(Nc1ccc(-c2nc3ccc(Cl)cc3[nH]2)cc1)c1cccnc1",
    "CHEMBL137305": "CC(C)Cc1ccc(C(C)C(=O)O)cc1",  # ibuprofen
    "CHEMBL1340715": "O=C(Nc1cccc(-c2nc3ccccc3[nH]2)c1)c1ccccc1",
    "CHEMBL1328308": "O=C(Nc1ccc2[nH]c(-c3ccccc3)nc2c1)c1ccccc1",
    "CHEMBL1299722": "CC(=O)Nc1ccc(-c2nc3cc(Cl)ccc3[nH]2)cc1",
    "CHEMBL1320044": "O=C(Nc1cccc(-c2nc3ccc(Cl)cc3[nH]2)c1)c1ccncc1",
    "CHEMBL1360613": "O=C(Nc1ccc(-c2nc3cc(F)ccc3[nH]2)cc1)c1cccc(F)c1",
    "CHEMBL1341801": "O=C(Nc1cccc(-c2nc3cc(F)ccc3[nH]2)c1)c1cccnc1",
    "CHEMBL1299744": "O=C(Nc1ccc(-c2nc3cc(C(F)(F)F)ccc3[nH]2)cc1)c1ccccc1",
    "CHEMBL1399734": "O=C(Nc1ccc2[nH]c(-c3ccc(F)cc3)nc2c1)c1ccccc1",
    "CHEMBL1400508": "O=C(Nc1ccc2[nH]c(-c3ccc(Cl)cc3)nc2c1)c1ccncc1",
    "CHEMBL1368718": "O=C(Nc1ccc(-c2nc3cc(C#N)ccc3[nH]2)cc1)c1cccnc1",
    "CHEMBL1408543": "O=C(Nc1ccc2[nH]c(-c3ccc(F)cc3)nc2c1)c1cccnc1",
}


# ---------------------------------------------------------------------------
# Feature Engineering -- Morgan fingerprints (RDKit) or string fallback
# ---------------------------------------------------------------------------

def _smiles_to_morgan(smiles: str) -> list[float] | None:
    """Convert SMILES to 2048-bit Morgan fingerprint (ECFP4).

    Returns None if SMILES cannot be parsed by RDKit.
    """
    if not _USE_RDKIT:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, MORGAN_RADIUS, nBits=MORGAN_NBITS)
    return list(fp)


def _smiles_to_string_features(smiles: str) -> list[float]:
    """Fallback: convert SMILES to 12 string-level descriptors (v1 compatible)."""
    return [
        len(smiles),                                                    # 0: molecule size
        smiles.count("N"),                                              # 1: nitrogen count
        smiles.count("O"),                                              # 2: oxygen count
        smiles.count("S"),                                              # 3: sulfur count
        smiles.count("F") + smiles.count("Cl") + smiles.count("Br"),   # 4: halogen count
        smiles.count("c") + smiles.count("C"),                          # 5: carbon count
        smiles.count("="),                                              # 6: double bonds
        smiles.count("#"),                                              # 7: triple bonds
        smiles.count("("),                                              # 8: branching
        smiles.count("["),                                              # 9: charged/special atoms
        sum(1 for c in smiles if c.isupper()) / max(len(smiles), 1),   # 10: atom density
        smiles.count("1") + smiles.count("2") + smiles.count("3"),     # 11: ring count proxy
    ]


def smiles_to_features(smiles: str, target_symbol: str, targets_list: list[str] | None = None) -> list[float] | None:
    """Convert SMILES + target to full feature vector for the ML model.

    With RDKit:  2048 (Morgan FP) + 7 (target one-hot) = 2055 dims
    Without:     12 (string) + 7 (target one-hot) = 19 dims

    Returns None if the SMILES cannot be parsed (RDKit mode only).
    """
    targets = targets_list or SMA_TARGETS
    target_upper = target_symbol.upper()

    # Molecular features
    if _USE_RDKIT:
        mol_features = _smiles_to_morgan(smiles)
        if mol_features is None:
            return None
    else:
        mol_features = _smiles_to_string_features(smiles)

    # Target one-hot encoding
    target_vec = [0.0] * len(targets)
    idx = {t: i for i, t in enumerate(targets)}.get(target_upper)
    if idx is not None:
        target_vec[idx] = 1.0

    return mol_features + target_vec


# ---------------------------------------------------------------------------
# Training Data Loader -- unified across all result sources
# ---------------------------------------------------------------------------

def _load_training_data() -> list[dict[str, Any]]:
    """Load and unify all DiffDock result files into a standard format.

    Returns list of {smiles, target, confidence, compound, source}.
    Prioritises the 10k_screen results (4,116 entries) but also loads
    legacy v1/multi/NIM results for broader coverage.
    """
    records: list[dict[str, Any]] = []
    seen_keys: set[str] = set()  # deduplicate by (smiles, target)

    def _add_record(smiles: str, target: str, confidence: float, compound: str, source: str) -> None:
        key = f"{smiles}|{target}"
        if key in seen_keys:
            return
        seen_keys.add(key)
        records.append({
            "smiles": smiles,
            "target": target,
            "confidence": confidence,
            "compound": compound,
            "source": source,
        })

    # --- 10k_screen results (primary, 4,116 entries) ---
    # Format: list of {compound, smiles, target, confidence, ...}
    # May also have a checkpoint with partial results
    for path, source_tag in [
        (_10K_SCREEN_RESULTS, "10k_screen"),
        (_10K_SCREEN_CHECKPOINT, "10k_screen_checkpoint"),
    ]:
        if path.exists():
            try:
                raw = json.loads(path.read_text())
                entries = raw if isinstance(raw, list) else raw.get("results", [])
                for entry in entries:
                    smiles = entry.get("smiles", "")
                    target = entry.get("target", "")
                    confidence = entry.get("confidence")
                    compound = entry.get("compound", entry.get("compound_name", ""))
                    if confidence is None or not target:
                        continue
                    # If smiles is missing, try to resolve from compound name
                    if not smiles:
                        smiles = KNOWN_SMILES.get(compound, "")
                    if not smiles:
                        continue
                    _add_record(smiles, target, float(confidence), compound, source_tag)
                logger.info("Loaded %d entries from %s", len(entries), path.name)
            except Exception as exc:
                logger.warning("Failed to load %s: %s", path, exc)

    # --- NIM batch results (378 entries, v2.2 NIM) ---
    if _NIM_BATCH_RESULTS.exists():
        try:
            raw = json.loads(_NIM_BATCH_RESULTS.read_text())
            for entry in raw:
                target = entry.get("target", "")
                compound = entry.get("compound", "")
                confidence = entry.get("confidence")
                if confidence is None or not target or not compound:
                    continue
                smiles = KNOWN_SMILES.get(compound, "")
                if not smiles:
                    continue
                _add_record(smiles, target, float(confidence), compound, "diffdock_nim_v2")
        except Exception as exc:
            logger.warning("Failed to load NIM batch results: %s", exc)

    # --- Multi-target results (120 entries) ---
    if _MULTI_RESULTS.exists():
        try:
            raw = json.loads(_MULTI_RESULTS.read_text())
            for entry in raw:
                target = entry.get("target", "")
                compound = entry.get("compound", "")
                confidence = entry.get("confidence")
                if confidence is None or not target or not compound:
                    continue
                smiles = KNOWN_SMILES.get(compound, "")
                if not smiles:
                    continue
                _add_record(smiles, target, float(confidence), compound, "diffdock_multi")
        except Exception as exc:
            logger.warning("Failed to load multi results: %s", exc)

    # --- v1 results (20 entries, SMN2 only) ---
    if _V1_RESULTS.exists():
        try:
            raw = json.loads(_V1_RESULTS.read_text())
            for entry in raw:
                complex_name = entry.get("complex", "")
                confidence = entry.get("confidence")
                if confidence is None:
                    continue
                parts = complex_name.split("_", 1)
                if len(parts) != 2:
                    continue
                target, compound = parts[0], parts[1]
                smiles = KNOWN_SMILES.get(compound, "")
                if not smiles:
                    continue
                _add_record(smiles, target, float(confidence), compound, "diffdock_v1")
        except Exception as exc:
            logger.warning("Failed to load v1 results: %s", exc)

    logger.info("Loaded %d total training records (deduplicated) from DiffDock results", len(records))
    return records


async def load_training_data(pool: Any = None) -> list[dict[str, Any]]:
    """Load DiffDock results from DB or JSON file.

    If pool is provided, tries DB first. Falls back to JSON files.
    This async wrapper enables future DB integration.
    """
    # Future: query from DB when available
    if pool is not None:
        try:
            from ..core.database import fetch
            rows = await fetch("""
                SELECT smiles, target_symbol AS target, confidence_score AS confidence,
                       compound_name AS compound, 'database' AS source
                FROM diffdock_results
                WHERE confidence_score IS NOT NULL AND smiles IS NOT NULL
                ORDER BY created_at DESC
            """)
            if rows and len(rows) > 10:
                logger.info("Loaded %d training records from database", len(rows))
                return [dict(r) for r in rows]
        except Exception as exc:
            logger.debug("DB load failed (expected if table missing): %s", exc)

    return _load_training_data()


# ---------------------------------------------------------------------------
# Model -- RandomForest (primary), GradientBoosting, or k-NN fallback
# ---------------------------------------------------------------------------

class KNNProxy:
    """Simple k-nearest-neighbour regressor (euclidean distance).

    Zero-dependency fallback when sklearn is not installed.
    """

    def __init__(self, k: int = 5):
        self.k = k
        self.X: list[list[float]] = []
        self.y: list[float] = []

    def fit(self, X: list[list[float]], y: list[float]) -> "KNNProxy":
        self.X = [list(row) for row in X]
        self.y = list(y)
        return self

    def predict(self, X: list[list[float]]) -> list[float]:
        predictions = []
        for query in X:
            dists = []
            for i, stored in enumerate(self.X):
                d = math.sqrt(sum((a - b) ** 2 for a, b in zip(query, stored)))
                dists.append((d, self.y[i]))
            dists.sort(key=lambda t: t[0])
            neighbours = dists[: self.k]
            if not neighbours:
                predictions.append(0.0)
            else:
                predictions.append(statistics.mean(v for _, v in neighbours))
        return predictions

    def predict_with_std(self, X: list[list[float]]) -> list[tuple[float, float]]:
        """Predict with uncertainty (std dev of neighbour values)."""
        results = []
        for query in X:
            dists = []
            for i, stored in enumerate(self.X):
                d = math.sqrt(sum((a - b) ** 2 for a, b in zip(query, stored)))
                dists.append((d, self.y[i]))
            dists.sort(key=lambda t: t[0])
            neighbours = dists[: self.k]
            if not neighbours:
                results.append((0.0, 1.0))
            else:
                vals = [v for _, v in neighbours]
                mean = statistics.mean(vals)
                std = statistics.stdev(vals) if len(vals) > 1 else 0.5
                results.append((mean, std))
        return results


class _ProxyModelV2:
    """Wrapper that holds the trained model + metadata (v2 with Morgan FPs)."""

    def __init__(self) -> None:
        self.model: Any = None
        self.model_type: str = "none"
        self.feature_mode: str = "none"  # "morgan_2048" or "string_12"
        self.trained_at: str = ""
        self.n_samples: int = 0
        self.n_compounds: int = 0
        self.n_targets: int = 0
        self.r2_score: float = 0.0
        self.mae: float = 0.0
        self.cv_scores: list[float] = []
        self.feature_importances_top20: list[dict[str, Any]] = []
        self.target_distribution: dict[str, int] = {}
        self.source_distribution: dict[str, int] = {}
        self.confidence_range: tuple[float, float] = (0.0, 0.0)
        self.version: str = "2.0.0"
        self.rdkit_available: bool = _USE_RDKIT
        self.sklearn_available: bool = _USE_SKLEARN
        self.feature_dim: int = FEATURE_DIM
        # For comparison scatter plot: store actual vs predicted on train set
        self.train_actual: list[float] = []
        self.train_predicted: list[float] = []

    def is_trained(self) -> bool:
        return self.model is not None


# Global model instance -- survives across requests
_proxy: _ProxyModelV2 | None = None


def _get_proxy() -> _ProxyModelV2:
    """Get or load the proxy model."""
    global _proxy
    if _proxy is not None and _proxy.is_trained():
        return _proxy
    # Try loading from disk (fixed local path only -- never user-supplied)
    if _MODEL_PATH.exists():
        try:
            with open(_MODEL_PATH, "rb") as f:
                _proxy = pickle.load(f)  # noqa: S301 -- safe: fixed local path
            logger.info("Loaded ML proxy model v2 from %s", _MODEL_PATH)
            return _proxy
        except Exception as exc:
            logger.warning("Failed to load saved model: %s", exc)
    # Return empty model -- caller should train first
    if _proxy is None:
        _proxy = _ProxyModelV2()
    return _proxy


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_proxy_model(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Train the ML proxy on DiffDock results (sync -- CPU-bound).

    Uses RandomForestRegressor with Morgan fingerprints when RDKit is available,
    falls back to GradientBoosting with string features otherwise.

    Returns dict with accuracy metrics, sample count, and top feature importances.
    """
    global _proxy
    start = time.time()

    if records is None:
        records = _load_training_data()

    if len(records) < 10:
        return {
            "error": f"Insufficient training data: {len(records)} records (need >= 10)",
            "hint": "Ensure gpu/results/10k_screen/diffdock_results.json exists",
        }

    # Build feature matrix
    X: list[list[float]] = []
    y: list[float] = []
    valid_records: list[dict[str, Any]] = []
    skipped = 0

    for rec in records:
        features = smiles_to_features(rec["smiles"], rec["target"])
        if features is None:
            skipped += 1
            continue
        X.append(features)
        y.append(rec["confidence"])
        valid_records.append(rec)

    if len(X) < 10:
        return {
            "error": f"Only {len(X)} valid feature vectors (skipped {skipped} unparseable SMILES)",
            "hint": "Check SMILES validity in training data",
        }

    # Distributions
    target_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    unique_smiles: set[str] = set()
    unique_targets: set[str] = set()
    for rec in valid_records:
        target_counts[rec["target"]] = target_counts.get(rec["target"], 0) + 1
        source_counts[rec["source"]] = source_counts.get(rec["source"], 0) + 1
        unique_smiles.add(rec["smiles"])
        unique_targets.add(rec["target"])

    # Initialize model wrapper
    _proxy = _ProxyModelV2()
    _proxy.n_samples = len(X)
    _proxy.n_compounds = len(unique_smiles)
    _proxy.n_targets = len(unique_targets)
    _proxy.target_distribution = target_counts
    _proxy.source_distribution = source_counts
    _proxy.confidence_range = (min(y), max(y))
    _proxy.feature_mode = "morgan_2048" if _USE_RDKIT else "string_12"
    _proxy.feature_dim = len(X[0])

    oob_r2 = None

    if _USE_SKLEARN:
        # Primary: RandomForestRegressor (handles high-dim sparse Morgan FPs well)
        if _USE_RDKIT:
            model = RandomForestRegressor(
                n_estimators=500,
                max_depth=None,          # grow full trees for Morgan FP
                min_samples_split=5,
                min_samples_leaf=2,
                max_features="sqrt",     # standard for random forest
                n_jobs=-1,               # use all cores
                random_state=42,
                oob_score=True,          # out-of-bag R2 (free validation)
            )
            _proxy.model_type = "RandomForestRegressor (Morgan ECFP4)"
        else:
            # Fallback: GradientBoosting for low-dim string features
            model = GradientBoostingRegressor(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.1,
                min_samples_split=3,
                min_samples_leaf=2,
                subsample=0.8,
                random_state=42,
            )
            _proxy.model_type = "GradientBoostingRegressor (string features)"

        # Cross-validation R2
        n_cv = min(5, len(X))
        try:
            cv = cross_val_score(model, X, y, cv=n_cv, scoring="r2")
            _proxy.cv_scores = [round(s, 4) for s in cv.tolist()]
        except Exception as exc:
            logger.warning("Cross-validation failed: %s", exc)
            _proxy.cv_scores = []

        # Train on full data
        model.fit(X, y)
        preds = model.predict(X).tolist()

        _proxy.model = model

        # Feature importances (top 20)
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_.tolist()
            indexed = [(i, imp) for i, imp in enumerate(importances)]
            indexed.sort(key=lambda x: x[1], reverse=True)

            if _USE_RDKIT:
                top20 = []
                for rank, (idx, imp) in enumerate(indexed[:20]):
                    if idx < MORGAN_NBITS:
                        name = f"morgan_bit_{idx}"
                    else:
                        target_idx = idx - MORGAN_NBITS
                        name = f"target_{SMA_TARGETS[target_idx]}" if target_idx < len(SMA_TARGETS) else f"feature_{idx}"
                    top20.append({"rank": rank + 1, "feature": name, "importance": round(imp, 6)})
                _proxy.feature_importances_top20 = top20
            else:
                _FALLBACK_NAMES = [
                    "smiles_length", "nitrogen_count", "oxygen_count", "sulfur_count",
                    "halogen_count", "carbon_count", "double_bonds", "triple_bonds",
                    "branching", "special_atoms", "atom_density", "ring_proxy",
                ] + [f"target_{t}" for t in SMA_TARGETS]
                _proxy.feature_importances_top20 = [
                    {
                        "rank": rank + 1,
                        "feature": _FALLBACK_NAMES[idx] if idx < len(_FALLBACK_NAMES) else f"feature_{idx}",
                        "importance": round(imp, 6),
                    }
                    for rank, (idx, imp) in enumerate(indexed[:20])
                ]

        # OOB score for RandomForest
        if hasattr(model, "oob_score_"):
            oob_r2 = round(model.oob_score_, 4)

        # Metrics on training set
        _proxy.r2_score = round(sklearn_r2(y, preds), 4)
        _proxy.mae = round(mean_absolute_error(y, preds), 4)

    else:
        # k-NN fallback
        model = KNNProxy(k=min(7, len(X)))
        model.fit(X, y)
        preds = model.predict(X)

        _proxy.model = model
        _proxy.model_type = f"KNNProxy (k={model.k})"
        _proxy.feature_importances_top20 = []

        ss_res = sum((yi - pi) ** 2 for yi, pi in zip(y, preds))
        ss_tot = sum((yi - statistics.mean(y)) ** 2 for yi in y)
        _proxy.r2_score = round(1.0 - ss_res / max(ss_tot, 1e-10), 4)
        _proxy.mae = round(statistics.mean(abs(yi - pi) for yi, pi in zip(y, preds)), 4)

    from datetime import datetime, timezone
    _proxy.trained_at = datetime.now(timezone.utc).isoformat()

    # Store actual vs predicted for scatter plot (subsample if large)
    max_scatter = 500
    if len(y) <= max_scatter:
        _proxy.train_actual = [round(v, 4) for v in y]
        _proxy.train_predicted = [round(v, 4) for v in preds]
    else:
        step = len(y) // max_scatter
        _proxy.train_actual = [round(y[i], 4) for i in range(0, len(y), step)][:max_scatter]
        _proxy.train_predicted = [round(preds[i], 4) for i in range(0, len(preds), step)][:max_scatter]

    # Save to disk (sklearn models require pickle -- cannot use JSON)
    try:
        with open(_MODEL_PATH, "wb") as f:
            pickle.dump(_proxy, f)  # noqa: S301
        logger.info("Saved ML proxy model v2 to %s", _MODEL_PATH)
    except Exception as exc:
        logger.warning("Failed to save model: %s", exc)

    elapsed = round(time.time() - start, 3)

    result: dict[str, Any] = {
        "status": "trained",
        "model_type": _proxy.model_type,
        "feature_mode": _proxy.feature_mode,
        "feature_dim": _proxy.feature_dim,
        "training_samples": _proxy.n_samples,
        "unique_compounds": _proxy.n_compounds,
        "unique_targets": _proxy.n_targets,
        "skipped_unparseable": skipped,
        "r2_score": _proxy.r2_score,
        "mae": _proxy.mae,
        "target_distribution": _proxy.target_distribution,
        "source_distribution": _proxy.source_distribution,
        "confidence_range": {"min": _proxy.confidence_range[0], "max": _proxy.confidence_range[1]},
        "training_time_seconds": elapsed,
        "version": _proxy.version,
        "rdkit_available": _USE_RDKIT,
        "sklearn_available": _USE_SKLEARN,
    }

    if oob_r2 is not None:
        result["oob_r2_score"] = oob_r2

    if _proxy.feature_importances_top20:
        result["top_20_features"] = _proxy.feature_importances_top20

    if _proxy.cv_scores:
        result["cross_validation"] = {
            "cv_r2_scores": _proxy.cv_scores,
            "cv_r2_mean": round(statistics.mean(_proxy.cv_scores), 4),
            "cv_r2_std": round(statistics.stdev(_proxy.cv_scores), 4) if len(_proxy.cv_scores) > 1 else 0.0,
        }

    return result


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

async def predict_binding(model: Any | None, smiles_list: list[str], target_symbol: str) -> dict[str, Any]:
    """Batch predict binding scores for a list of SMILES against one target.

    This is the fast screening step -- processes thousands of compounds in
    milliseconds where DiffDock would take days.

    Returns sorted list (best confidence first) with predictions.
    """
    proxy = model if isinstance(model, _ProxyModelV2) else _get_proxy()
    if not proxy.is_trained():
        return {"error": "Model not trained. POST /api/v2/ml-proxy/train first."}

    target_upper = target_symbol.upper()
    if target_upper not in _TARGET_INDEX:
        return {"error": f"Unknown target: {target_symbol}. Supported: {', '.join(SMA_TARGETS)}"}

    start = time.time()

    # Build feature matrix
    feature_matrix: list[list[float]] = []
    valid_indices: list[int] = []
    for i, smi in enumerate(smiles_list):
        if not smi:
            continue
        features = smiles_to_features(smi, target_upper)
        if features is None:
            continue
        feature_matrix.append(features)
        valid_indices.append(i)

    if not feature_matrix:
        return {"error": "No valid SMILES in input (all failed parsing)"}

    # Batch prediction
    if isinstance(proxy.model, KNNProxy):
        preds_with_std = proxy.model.predict_with_std(feature_matrix)
    elif _USE_SKLEARN:
        raw_preds = proxy.model.predict(feature_matrix).tolist()
        # Estimate uncertainty from tree variance (RandomForest)
        if hasattr(proxy.model, "estimators_") and hasattr(proxy.model, "n_estimators"):
            try:
                import numpy as np
                tree_preds = np.array([tree.predict(feature_matrix) for tree in proxy.model.estimators_])
                stds = tree_preds.std(axis=0).tolist()
                preds_with_std = list(zip(raw_preds, stds))
            except Exception:
                preds_with_std = [(p, 0.3) for p in raw_preds]
        else:
            preds_with_std = [(p, 0.3) for p in raw_preds]
    else:
        raw_preds = proxy.model.predict(feature_matrix)
        preds_with_std = [(p, 0.5) for p in raw_preds]

    elapsed_ms = round((time.time() - start) * 1000, 2)

    # Build results
    results: list[dict[str, Any]] = []
    for idx_pos, orig_idx in enumerate(valid_indices):
        pred, std = preds_with_std[idx_pos]
        results.append({
            "rank": 0,
            "smiles": smiles_list[orig_idx],
            "target": target_upper,
            "predicted_confidence": round(float(pred), 4),
            "uncertainty": round(float(std), 4),
            "interpretation": _interpret_confidence(float(pred)),
        })

    # Sort by predicted confidence (higher = better binder)
    results.sort(key=lambda r: r["predicted_confidence"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {
        "target": target_upper,
        "total_screened": len(results),
        "valid_parsed": len(valid_indices),
        "total_input": len(smiles_list),
        "screening_time_ms": elapsed_ms,
        "throughput_per_second": round(len(results) / max(elapsed_ms / 1000, 0.001)),
        "model_type": proxy.model_type,
        "model_version": proxy.version,
        "feature_mode": proxy.feature_mode,
        "results": results,
    }


async def screen_chembl_library(pool: Any, target: str, top_k: int = 1000) -> dict[str, Any]:
    """Screen the full ChEMBL library from our DB using the trained proxy.

    Loads all SMILES from molecule_screenings table, runs them through
    the proxy model, and returns the top-K predicted binders.
    """
    proxy = _get_proxy()
    if not proxy.is_trained():
        return {"error": "Model not trained. POST /api/v2/ml-proxy/train first."}

    target_upper = target.upper()
    if target_upper not in _TARGET_INDEX:
        return {"error": f"Unknown target: {target}. Supported: {', '.join(SMA_TARGETS)}"}

    start = time.time()

    # Load SMILES from DB
    try:
        from ..core.database import fetch
        rows = await fetch("""
            SELECT DISTINCT smiles, chembl_id, compound_name, target_symbol,
                   pchembl_value, molecular_weight, drug_likeness_pass
            FROM molecule_screenings
            WHERE smiles IS NOT NULL AND smiles != ''
            ORDER BY pchembl_value DESC NULLS LAST
        """)
    except Exception as exc:
        logger.error("Failed to load library from DB: %s", exc, exc_info=True)
        return {"error": f"Database query failed: {exc}"}

    if not rows:
        return {"error": "No compounds found in molecule_screenings table"}

    # Build feature matrix
    compounds_info: list[dict[str, Any]] = []
    feature_matrix: list[list[float]] = []
    skipped = 0

    for row in rows:
        d = dict(row)
        smi = d.get("smiles", "")
        if not smi:
            continue
        features = smiles_to_features(smi, target_upper)
        if features is None:
            skipped += 1
            continue
        feature_matrix.append(features)
        compounds_info.append(d)

    if not feature_matrix:
        return {"error": f"No valid SMILES (skipped {skipped} unparseable)"}

    # Batch prediction
    if isinstance(proxy.model, KNNProxy):
        preds_with_std = proxy.model.predict_with_std(feature_matrix)
    elif _USE_SKLEARN:
        raw_preds = proxy.model.predict(feature_matrix).tolist()
        if hasattr(proxy.model, "estimators_") and hasattr(proxy.model, "n_estimators"):
            try:
                import numpy as np
                tree_preds = np.array([tree.predict(feature_matrix) for tree in proxy.model.estimators_])
                stds = tree_preds.std(axis=0).tolist()
                preds_with_std = list(zip(raw_preds, stds))
            except Exception:
                preds_with_std = [(p, 0.3) for p in raw_preds]
        else:
            preds_with_std = [(p, 0.3) for p in raw_preds]
    else:
        raw_preds = proxy.model.predict(feature_matrix)
        preds_with_std = [(p, 0.5) for p in raw_preds]

    # Build and rank results
    results: list[dict[str, Any]] = []
    for i, info in enumerate(compounds_info):
        pred, std = preds_with_std[i]
        results.append({
            "rank": 0,
            "chembl_id": info.get("chembl_id", ""),
            "compound_name": info.get("compound_name", ""),
            "smiles": (info.get("smiles", ""))[:100],
            "target": target_upper,
            "original_target": info.get("target_symbol", ""),
            "predicted_confidence": round(float(pred), 4),
            "uncertainty": round(float(std), 4),
            "interpretation": _interpret_confidence(float(pred)),
            "pchembl_value": round(float(info["pchembl_value"]), 2) if info.get("pchembl_value") else None,
            "mw": round(float(info["molecular_weight"]), 1) if info.get("molecular_weight") else None,
            "drug_like": bool(info.get("drug_likeness_pass")),
        })

    # Sort by predicted confidence (best first), take top_k
    results.sort(key=lambda r: r["predicted_confidence"], reverse=True)
    results = results[:top_k]
    for i, r in enumerate(results):
        r["rank"] = i + 1

    elapsed = round(time.time() - start, 3)

    # Binding class distribution
    class_dist: dict[str, int] = {}
    for r in results:
        cls = r["interpretation"]
        class_dist[cls] = class_dist.get(cls, 0) + 1

    return {
        "target": target_upper,
        "library_size": len(compounds_info),
        "skipped_unparseable": skipped,
        "top_k": top_k,
        "returned": len(results),
        "screening_time_seconds": elapsed,
        "throughput_per_second": round(len(compounds_info) / max(elapsed, 0.001)),
        "binding_class_distribution": class_dist,
        "model_type": proxy.model_type,
        "model_version": proxy.version,
        "results": results,
    }


async def get_model_status() -> dict[str, Any]:
    """Return model stats, training data info, and accuracy metrics."""
    proxy = _get_proxy()

    data_files = {
        "10k_screen": str(_10K_SCREEN_RESULTS),
        "10k_screen_exists": _10K_SCREEN_RESULTS.exists(),
        "10k_checkpoint": str(_10K_SCREEN_CHECKPOINT),
        "10k_checkpoint_exists": _10K_SCREEN_CHECKPOINT.exists(),
        "nim_batch": str(_NIM_BATCH_RESULTS),
        "nim_batch_exists": _NIM_BATCH_RESULTS.exists(),
        "multi_results": str(_MULTI_RESULTS),
        "multi_exists": _MULTI_RESULTS.exists(),
        "v1_results": str(_V1_RESULTS),
        "v1_exists": _V1_RESULTS.exists(),
    }

    if not proxy.is_trained():
        return {
            "status": "not_trained",
            "message": "No ML proxy model loaded. POST /api/v2/ml-proxy/train to train.",
            "available_targets": SMA_TARGETS,
            "training_data_files": data_files,
            "rdkit_available": _USE_RDKIT,
            "sklearn_available": _USE_SKLEARN,
        }

    result: dict[str, Any] = {
        "status": "trained",
        "model_type": proxy.model_type,
        "feature_mode": proxy.feature_mode,
        "feature_dim": proxy.feature_dim,
        "version": proxy.version,
        "trained_at": proxy.trained_at,
        "training_samples": proxy.n_samples,
        "unique_compounds": proxy.n_compounds,
        "unique_targets": proxy.n_targets,
        "r2_score": proxy.r2_score,
        "mae": proxy.mae,
        "target_distribution": proxy.target_distribution,
        "source_distribution": proxy.source_distribution,
        "confidence_range": {"min": proxy.confidence_range[0], "max": proxy.confidence_range[1]},
        "available_targets": SMA_TARGETS,
        "training_data_files": data_files,
        "rdkit_available": _USE_RDKIT,
        "sklearn_available": _USE_SKLEARN,
        "model_path": str(_MODEL_PATH),
        "model_on_disk": _MODEL_PATH.exists(),
    }

    if proxy.feature_importances_top20:
        result["top_20_features"] = proxy.feature_importances_top20

    if proxy.cv_scores:
        result["cross_validation"] = {
            "cv_r2_scores": proxy.cv_scores,
            "cv_r2_mean": round(statistics.mean(proxy.cv_scores), 4),
            "cv_r2_std": round(statistics.stdev(proxy.cv_scores), 4) if len(proxy.cv_scores) > 1 else 0.0,
        }

    # Scatter plot data for actual vs predicted
    if proxy.train_actual and proxy.train_predicted:
        result["scatter_data"] = {
            "actual": proxy.train_actual,
            "predicted": proxy.train_predicted,
            "n_points": len(proxy.train_actual),
        }

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _interpret_confidence(conf: float) -> str:
    """Human-readable interpretation of a DiffDock confidence score."""
    if conf > 0.0:
        return "strong_binder"
    elif conf > -0.5:
        return "good_binder"
    elif conf > -1.0:
        return "moderate_binder"
    elif conf > -1.5:
        return "weak_binder"
    elif conf > -2.0:
        return "poor_binder"
    else:
        return "non_binder"
