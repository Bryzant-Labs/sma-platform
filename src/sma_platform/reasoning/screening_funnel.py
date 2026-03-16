"""Screening Funnel Pipeline Orchestrator — billion-molecule screening for SMA.

Pipeline stages:
    Generate -> Filter -> ML Proxy -> DiffDock -> Boltz-2 -> Candidates

This module orchestrates the full virtual screening funnel:
1. Generate N molecules (random SMILES or GenMol scaffold decoration)
2. Filter by drug-likeness (Lipinski-like, pure SMILES analysis — no RDKit)
3. ML proxy prediction (pharmacophore-based docking scorer)
4. Queue top candidates for real DiffDock (via NIM API or self-hosted)
5. Store results and return funnel statistics

All drug-likeness estimation is done via pure SMILES string analysis,
so this module works without RDKit installed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import re
import string
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from ..core.database import execute, execute_script, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DDL — screening_funnels table
# ---------------------------------------------------------------------------

_CREATE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS screening_funnels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT UNIQUE NOT NULL,
    target TEXT NOT NULL,
    n_generated INTEGER,
    n_filtered INTEGER,
    n_proxy_passed INTEGER,
    n_docked INTEGER,
    top_candidates JSONB DEFAULT '[]',
    timing JSONB DEFAULT '{}',
    status TEXT DEFAULT 'running',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_screening_funnels_run_id ON screening_funnels(run_id);
CREATE INDEX IF NOT EXISTS idx_screening_funnels_status ON screening_funnels(status);
CREATE INDEX IF NOT EXISTS idx_screening_funnels_target ON screening_funnels(target);
"""

_table_ready = False


async def _ensure_table() -> None:
    """Create the screening_funnels table if it does not exist."""
    global _table_ready
    if _table_ready:
        return
    try:
        await execute_script(_CREATE_TABLE_DDL)
        _table_ready = True
        logger.info("screening_funnels table ensured")
    except Exception as exc:
        logger.error("Failed to create screening_funnels table: %s", exc, exc_info=True)
        raise


# ---------------------------------------------------------------------------
# Global state for tracking running funnel
# ---------------------------------------------------------------------------

_current_funnel: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# SMILES generation — random drug-like molecules
# ---------------------------------------------------------------------------

# Common drug-like fragments for assembling random SMILES
_AROMATIC_RINGS = [
    "c1ccccc1",       # benzene
    "c1ccncc1",       # pyridine
    "c1ccoc1",        # furan
    "c1ccsc1",        # thiophene
    "c1cc[nH]c1",     # pyrrole
    "c1cnc2ccccc2n1", # quinazoline
    "c1ccc2[nH]ccc2c1",  # indole
    "c1cnc[nH]1",     # imidazole
    "c1ccnc(N)c1",    # 2-aminopyridine
    "c1ccc(O)cc1",    # phenol
    "c1ccc(F)cc1",    # fluorobenzene
    "c1ccc(Cl)cc1",   # chlorobenzene
    "c1ccc(C)cc1",    # toluene
    "c1cc(F)cc(F)c1", # difluorobenzene
]

_LINKERS = [
    "CC", "CCC", "CC(=O)", "C(=O)N", "CC(O)", "COC",
    "CCNC", "CCO", "CCS", "C(=O)O", "NC", "OC",
    "C(F)(F)", "CCN", "C=C",
]

_FUNCTIONAL_GROUPS = [
    "O", "N", "F", "Cl", "S", "C(=O)O", "C(=O)N",
    "NC(=O)", "S(=O)(=O)N", "OC", "NC", "C#N",
    "C(F)(F)F", "NO", "NS(=O)(=O)",
]

# SMA-relevant scaffolds for seeding the generator
_SMA_SCAFFOLDS = [
    "Nc1ccncc1",                          # 4-Aminopyridine
    "c1ccc2c(c1)nc(N)n2",                 # 2-aminobenzimidazole (risdiplam-like)
    "O=C(O)CCCCC(=O)O",                   # adipic acid (HDAC linker)
    "c1ccc(NC(=O)c2ccccc2)cc1",           # benzanilide
    "c1cnc2cc(F)ccc2n1",                  # fluoroquinazoline
    "c1ccc(S(=O)(=O)N)cc1",              # sulfonamide
    "CC(=O)Nc1ccc(O)cc1",                 # acetaminophen-like
    "c1cc(N)c(Cl)cc1Cl",                  # dichloroaniline
    "c1ccc(-c2ccccn2)cc1",                # 2-phenylpyridine
    "Nc1ncc(F)c(N)n1",                    # difluorodiaminopyrimidine
]


def _generate_random_smiles(n: int) -> list[str]:
    """Generate N random drug-like SMILES strings.

    Assembles molecules from aromatic rings, linkers, and functional groups.
    Not guaranteed to be synthesizable — this is for screening volume.
    """
    molecules = []
    for _ in range(n):
        # 30% chance to use an SMA-relevant scaffold as base
        if random.random() < 0.3:
            base = random.choice(_SMA_SCAFFOLDS)
        else:
            base = random.choice(_AROMATIC_RINGS)

        # Add 0-2 linker+ring extensions
        n_extensions = random.randint(0, 2)
        parts = [base]
        for _ in range(n_extensions):
            linker = random.choice(_LINKERS)
            ring = random.choice(_AROMATIC_RINGS)
            parts.append(linker)
            parts.append(ring)

        # Add 0-2 functional groups
        n_func = random.randint(0, 2)
        for _ in range(n_func):
            parts.append(random.choice(_FUNCTIONAL_GROUPS))

        smiles = "".join(parts)
        molecules.append(smiles)

    return molecules


# ---------------------------------------------------------------------------
# Drug-likeness estimation (pure SMILES, no RDKit)
# ---------------------------------------------------------------------------

# Atom weight lookup for MW estimation
_ATOM_WEIGHTS: dict[str, float] = {
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "S": 32.065,
    "F": 18.998,
    "P": 30.974,
    "I": 126.904,
    "H": 1.008,
}
# Two-char atoms must be checked first
_DIATOMIC: dict[str, float] = {
    "Cl": 35.453,
    "Br": 79.904,
    "Si": 28.086,
    "Se": 78.971,
}

# Atom-additive LogP contributions (simplified Wildman-Crippen-like)
_LOGP_CONTRIBUTIONS: dict[str, float] = {
    "C": 0.24,       # aliphatic carbon
    "c": 0.15,       # aromatic carbon
    "N": -0.57,      # nitrogen
    "n": -0.28,      # aromatic nitrogen
    "O": -0.47,      # oxygen
    "o": -0.14,      # aromatic oxygen (furan)
    "S": 0.00,       # sulfur (neutral)
    "s": 0.05,       # aromatic sulfur (thiophene)
    "F": 0.37,       # fluorine (lipophilic)
    "Cl": 0.87,      # chlorine
    "Br": 1.09,      # bromine
    "I": 1.40,       # iodine
    "H": 0.00,       # hydrogen (implicit)
    "P": -0.20,      # phosphorus
}


def estimate_drug_likeness(smiles: str) -> dict[str, Any]:
    """Estimate Lipinski properties from a SMILES string without RDKit.

    Returns dict with keys:
        mw: estimated molecular weight
        logp: estimated LogP (atom-additive)
        hbd: H-bond donor count (NH, OH patterns)
        hba: H-bond acceptor count (N, O atoms)
        rotatable: estimated rotatable bonds
        lipinski_pass: bool (passes Ro5 with 1 violation tolerance)
    """
    if not smiles:
        return {"mw": 0, "logp": 0, "hbd": 0, "hba": 0, "rotatable": 0, "lipinski_pass": False}

    # --- Molecular weight estimation ---
    mw = 0.0
    i = 0
    atom_counts: dict[str, int] = {}
    aromatic_atoms = 0
    total_heavy_atoms = 0

    while i < len(smiles):
        # Skip brackets, charges, digits, bonds, parens, stereo
        ch = smiles[i]
        if ch in "[]()=#/\\@+-.0123456789%":
            # Inside bracket: count the atom
            if ch == "[":
                # Find closing bracket
                j = smiles.find("]", i)
                if j == -1:
                    j = len(smiles) - 1
                bracket_content = smiles[i + 1 : j]
                # Extract atom from bracket (e.g., [nH] -> N, [C@@H] -> C)
                atom_match = re.match(r"(\d*)([A-Z][a-z]?)", bracket_content)
                if atom_match:
                    atom = atom_match.group(2)
                    atom_upper = atom.upper() if len(atom) == 1 else atom.capitalize()
                    w = _DIATOMIC.get(atom_upper) or _ATOM_WEIGHTS.get(atom_upper, 12.0)
                    mw += w
                    atom_counts[atom_upper] = atom_counts.get(atom_upper, 0) + 1
                    total_heavy_atoms += 1
                    # Check for H inside bracket (explicit hydrogen)
                    if "H" in bracket_content and atom_upper != "H":
                        h_match = re.search(r"H(\d?)", bracket_content)
                        if h_match:
                            n_h = int(h_match.group(1)) if h_match.group(1) else 1
                            mw += n_h * 1.008
                i = j + 1
                continue
            i += 1
            continue

        # Check two-character atoms first
        if i + 1 < len(smiles):
            two_char = smiles[i : i + 2]
            two_upper = two_char.capitalize()
            if two_upper in _DIATOMIC and two_char[0].isupper():
                mw += _DIATOMIC[two_upper]
                atom_counts[two_upper] = atom_counts.get(two_upper, 0) + 1
                total_heavy_atoms += 1
                i += 2
                continue

        # Single-character atoms
        if ch.isalpha():
            is_aromatic = ch.islower()
            atom_upper = ch.upper()
            w = _ATOM_WEIGHTS.get(atom_upper, 0)
            if w > 0:
                mw += w
                atom_counts[atom_upper] = atom_counts.get(atom_upper, 0) + 1
                total_heavy_atoms += 1
                if is_aromatic:
                    aromatic_atoms += 1
            i += 1
            continue

        i += 1

    # Add implicit hydrogens estimate (rough: each C gets ~2H, N gets ~1H, O gets ~1H)
    implicit_h = 0
    implicit_h += max(0, atom_counts.get("C", 0) * 2 - aromatic_atoms)
    implicit_h += atom_counts.get("N", 0) * 1
    implicit_h += atom_counts.get("O", 0) * 1
    # Cap at reasonable range
    implicit_h = max(0, min(implicit_h, total_heavy_atoms * 3))
    mw += implicit_h * 1.008
    mw = round(mw, 1)

    # --- H-bond donors: count NH, OH patterns ---
    # Matches: [nH], NH, nH, OH, oH plus explicit patterns
    hbd = len(re.findall(r"[NnOo]H|(?<=[Nn])\[H\]|\[nH\]|\[NH\d?\]", smiles))
    # Also count bare N with implicit H in non-aromatic context
    hbd += len(re.findall(r"(?<![cnos])N(?![+\-=])", smiles))
    # Count OH groups
    hbd += smiles.count("O") - smiles.count("O=") - smiles.count("OC") - smiles.count("Oc")
    hbd = max(0, min(hbd, 15))

    # --- H-bond acceptors: count N, O atoms ---
    hba = atom_counts.get("N", 0) + atom_counts.get("O", 0)

    # --- LogP estimation (atom-additive) ---
    logp = 0.0
    # Walk through SMILES for aromatic/aliphatic distinction
    for ch in smiles:
        if ch in _LOGP_CONTRIBUTIONS:
            logp += _LOGP_CONTRIBUTIONS[ch]
        elif ch.upper() + ch[0:0] in _LOGP_CONTRIBUTIONS:
            pass  # handled above
    # Check two-char atoms
    for atom, contrib in [("Cl", 0.87), ("Br", 1.09)]:
        logp += smiles.count(atom) * contrib
        # Remove double-counted single chars
        if atom == "Cl":
            logp -= smiles.count("Cl") * _LOGP_CONTRIBUTIONS.get("C", 0)
    logp = round(logp, 2)

    # --- Rotatable bonds: count non-ring single bonds ---
    # Approximate: count single-bond carbons minus ring bonds
    # Simple heuristic: C-C, C-N, C-O single bonds outside rings
    ring_atoms = smiles.count("1") + smiles.count("2") + smiles.count("3")
    # Count explicit single bonds between heavy atoms
    chain_bonds = max(0, total_heavy_atoms - 1 - ring_atoms)
    # Subtract double/triple bonds
    chain_bonds -= smiles.count("=") + smiles.count("#")
    # Subtract aromatic bonds (ring-internal)
    chain_bonds -= max(0, aromatic_atoms - ring_atoms)
    rotatable = max(0, min(chain_bonds, 30))

    # --- Lipinski Rule of Five ---
    violations = 0
    if mw > 500:
        violations += 1
    if logp > 5:
        violations += 1
    if hbd > 5:
        violations += 1
    if hba > 10:
        violations += 1
    lipinski_pass = violations <= 1

    return {
        "mw": mw,
        "logp": logp,
        "hbd": hbd,
        "hba": hba,
        "rotatable": rotatable,
        "lipinski_pass": lipinski_pass,
    }


# ---------------------------------------------------------------------------
# Drug-likeness filter for funnel
# ---------------------------------------------------------------------------

def _passes_funnel_filter(props: dict[str, Any]) -> bool:
    """Check if molecule passes the funnel drug-likeness gate.

    Criteria:
        MW: 150 - 500
        LogP: -1 to 5
        Rotatable bonds: < 10
        HBD: < 5
        HBA: < 10
    """
    mw = props.get("mw", 0)
    logp = props.get("logp", 0)
    rot = props.get("rotatable", 0)
    hbd = props.get("hbd", 0)
    hba = props.get("hba", 0)

    return (
        150 <= mw <= 500
        and -1 <= logp <= 5
        and rot < 10
        and hbd < 5
        and hba < 10
    )


# ---------------------------------------------------------------------------
# ML Proxy scoring (uses existing docking_scorer)
# ---------------------------------------------------------------------------

def _proxy_score(smiles: str, props: dict[str, Any], target: str) -> dict[str, Any]:
    """Score a molecule using the pharmacophore-based docking proxy.

    Returns the composite score and binding class.
    """
    from .docking_scorer import BINDING_POCKETS, predict_docking_score

    # Map target name to a binding pocket key
    pocket_map: dict[str, str] = {
        "SMN2": "SMN2_SPLICE_SITE",
        "SMN1": "SMN2_ISS_N1",
        "HDAC": "HDAC_CATALYTIC",
        "MTOR": "MTOR_ATP_SITE",
        "NCALD": "NCALD_CALCIUM_SITE",
        "PLS3": "PLS3_ACTIN_INTERFACE",
        "UBA1": "UBA1_UBIQUITIN_SITE",
    }
    pocket_key = pocket_map.get(target.upper(), "SMN2_SPLICE_SITE")

    mw = props.get("mw", 300)
    logp = props.get("logp", 2)
    hbd = props.get("hbd", 2)
    hba = props.get("hba", 4)
    rot = props.get("rotatable", 5)

    # Estimate TPSA and aromatic rings from SMILES
    est_tpsa = 20 + mw * 0.15
    est_aromatic = smiles.lower().count("c1") + smiles.lower().count("c2")
    bbb = mw < 450 and est_tpsa < 90 and hbd <= 3

    score = predict_docking_score(
        compound_id=smiles[:20],
        mw=mw,
        logp=logp,
        hbd=hbd,
        hba=hba,
        tpsa=est_tpsa,
        rotatable_bonds=rot,
        aromatic_rings=est_aromatic,
        pocket_key=pocket_key,
        bbb_permeable=bbb,
    )

    if score is None:
        return {"composite_score": 0.0, "binding_class": "unlikely", "affinity_kcal": 0.0}

    return {
        "composite_score": score.composite_score,
        "binding_class": score.binding_class,
        "affinity_kcal": score.predicted_affinity_kcal,
    }


# ---------------------------------------------------------------------------
# Main funnel pipeline
# ---------------------------------------------------------------------------

async def run_funnel(
    n_generate: int = 100_000,
    target: str = "SMN2",
) -> dict[str, Any]:
    """Run the full screening funnel pipeline.

    Pipeline:
        1. Generate N molecules (random SMILES assembly)
        2. Filter by drug-likeness (MW 150-500, LogP -1 to 5, etc.)
        3. ML proxy prediction (pharmacophore scorer). Keep top 1%.
        4. Queue top candidates for real DiffDock
        5. Return funnel stats, top candidates, timing

    Parameters
    ----------
    n_generate : Number of molecules to generate (default 100,000).
    target : Target protein (default "SMN2").

    Returns
    -------
    dict with funnel statistics, top candidates, and timing.
    """
    global _current_funnel

    await _ensure_table()

    run_id = f"funnel-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    timing: dict[str, float] = {}
    t_total_start = time.monotonic()

    _current_funnel = {
        "run_id": run_id,
        "target": target,
        "status": "running",
        "stage": "generating",
        "n_generate": n_generate,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    # Insert initial row
    await execute(
        """INSERT INTO screening_funnels (run_id, target, n_generated, status)
           VALUES ($1, $2, $3, 'running')""",
        run_id, target, n_generate,
    )

    try:
        # ---- Stage 1: Generate molecules ----
        t0 = time.monotonic()
        _current_funnel["stage"] = "generating"
        logger.info("Funnel %s: generating %d molecules for target %s", run_id, n_generate, target)

        # Try GenMol via NIM API first, fall back to random generation
        generated_smiles: list[str] = []
        genmol_used = False

        try:
            from ..ingestion.adapters.nvidia_nims import check_api_key, genmol_generate
            if check_api_key() and n_generate <= 1000:
                # GenMol is rate-limited, only use for small batches
                result = await genmol_generate(
                    scaffold_smiles="Nc1ccncc1",
                    num_molecules=min(n_generate, 500),
                    mode="de_novo",
                )
                genmol_smiles = result.get("molecules", [])
                if isinstance(genmol_smiles, list):
                    for item in genmol_smiles:
                        if isinstance(item, str):
                            generated_smiles.append(item)
                        elif isinstance(item, dict) and "smiles" in item:
                            generated_smiles.append(item["smiles"])
                    genmol_used = True
                    logger.info("GenMol generated %d molecules", len(generated_smiles))
        except Exception as exc:
            logger.info("GenMol not available, using random generation: %s", exc)

        # Fill remaining with random generation
        remaining = n_generate - len(generated_smiles)
        if remaining > 0:
            generated_smiles.extend(_generate_random_smiles(remaining))

        timing["generate_secs"] = round(time.monotonic() - t0, 3)
        n_generated = len(generated_smiles)

        # ---- Stage 2: Drug-likeness filter ----
        t0 = time.monotonic()
        _current_funnel["stage"] = "filtering"
        logger.info("Funnel %s: filtering %d molecules by drug-likeness", run_id, n_generated)

        filtered: list[tuple[str, dict[str, Any]]] = []
        for smi in generated_smiles:
            props = estimate_drug_likeness(smi)
            if _passes_funnel_filter(props):
                filtered.append((smi, props))

        timing["filter_secs"] = round(time.monotonic() - t0, 3)
        n_filtered = len(filtered)
        logger.info("Funnel %s: %d/%d passed drug-likeness filter (%.1f%%)",
                     run_id, n_filtered, n_generated, 100 * n_filtered / max(1, n_generated))

        # ---- Stage 3: ML Proxy scoring ----
        t0 = time.monotonic()
        _current_funnel["stage"] = "proxy_scoring"
        logger.info("Funnel %s: scoring %d filtered molecules with ML proxy", run_id, n_filtered)

        scored: list[dict[str, Any]] = []
        for smi, props in filtered:
            proxy = _proxy_score(smi, props, target)
            scored.append({
                "smiles": smi,
                "props": props,
                "proxy": proxy,
            })

        # Sort by composite score, keep top 1%
        scored.sort(key=lambda x: x["proxy"]["composite_score"], reverse=True)
        top_pct = max(1, int(len(scored) * 0.01))
        proxy_passed = scored[:top_pct]

        timing["proxy_secs"] = round(time.monotonic() - t0, 3)
        n_proxy_passed = len(proxy_passed)
        logger.info("Funnel %s: top 1%% = %d candidates (composite >= %.3f)",
                     run_id, n_proxy_passed,
                     proxy_passed[-1]["proxy"]["composite_score"] if proxy_passed else 0)

        # ---- Stage 4: Queue for DiffDock (record candidates) ----
        t0 = time.monotonic()
        _current_funnel["stage"] = "queuing_docking"

        # Build top candidates list
        top_candidates = []
        for i, cand in enumerate(proxy_passed[:100]):  # Cap at 100 for storage
            top_candidates.append({
                "rank": i + 1,
                "smiles": cand["smiles"],
                "mw": cand["props"]["mw"],
                "logp": cand["props"]["logp"],
                "hbd": cand["props"]["hbd"],
                "hba": cand["props"]["hba"],
                "rotatable": cand["props"]["rotatable"],
                "composite_score": cand["proxy"]["composite_score"],
                "binding_class": cand["proxy"]["binding_class"],
                "affinity_kcal": cand["proxy"]["affinity_kcal"],
                "docking_status": "queued",
            })

        # Attempt real DiffDock for top 5 candidates if NIM API available
        n_docked = 0
        try:
            from ..ingestion.adapters.nvidia_nims import check_api_key, diffdock_dock_smiles
            if check_api_key() and top_candidates:
                dock_limit = min(5, len(top_candidates))
                logger.info("Funnel %s: docking top %d candidates via DiffDock NIM", run_id, dock_limit)

                for cand in top_candidates[:dock_limit]:
                    try:
                        # Download AlphaFold structure
                        import urllib.request
                        target_uniprot = {
                            "SMN2": "Q16637", "SMN1": "Q16637",
                            "PLS3": "P13797", "NCALD": "P61601",
                            "UBA1": "P22314", "HDAC": "P56524",
                        }
                        uniprot_id = target_uniprot.get(target.upper(), "Q16637")
                        url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v6.pdb"
                        with urllib.request.urlopen(url, timeout=15) as resp:
                            protein_pdb = resp.read().decode()

                        dock_result = await diffdock_dock_smiles(
                            protein_pdb=protein_pdb,
                            smiles=cand["smiles"],
                            num_poses=5,
                        )
                        cand["docking_status"] = "completed"
                        cand["diffdock_result"] = dock_result
                        n_docked += 1
                    except Exception as dock_exc:
                        cand["docking_status"] = "failed"
                        cand["docking_error"] = str(dock_exc)[:200]
                        logger.warning("DiffDock failed for %s: %s", cand["smiles"][:30], dock_exc)
        except Exception as exc:
            logger.info("DiffDock NIM not available: %s", exc)

        timing["docking_secs"] = round(time.monotonic() - t0, 3)
        timing["total_secs"] = round(time.monotonic() - t_total_start, 3)

        # ---- Store results ----
        _current_funnel["stage"] = "storing"

        await execute(
            """UPDATE screening_funnels
               SET n_generated = $1, n_filtered = $2, n_proxy_passed = $3,
                   n_docked = $4, top_candidates = $5::jsonb,
                   timing = $6::jsonb, status = 'completed'
               WHERE run_id = $7""",
            n_generated,
            n_filtered,
            n_proxy_passed,
            n_docked,
            json.dumps(top_candidates),
            json.dumps(timing),
            run_id,
        )

        result = {
            "run_id": run_id,
            "target": target,
            "status": "completed",
            "genmol_used": genmol_used,
            "funnel_stats": {
                "n_generated": n_generated,
                "n_filtered": n_filtered,
                "filter_rate": round(n_filtered / max(1, n_generated) * 100, 1),
                "n_proxy_passed": n_proxy_passed,
                "proxy_rate": round(n_proxy_passed / max(1, n_filtered) * 100, 1),
                "n_docked": n_docked,
            },
            "timing": timing,
            "top_candidates": top_candidates[:20],  # Return top 20 in response
            "note": (
                "Pharmacophore-based proxy scoring — candidates should be validated "
                "with DiffDock / Boltz-2 for binding pose confirmation."
            ),
        }

        _current_funnel = None
        logger.info(
            "Funnel %s complete: %d -> %d -> %d -> %d docked (%.1fs)",
            run_id, n_generated, n_filtered, n_proxy_passed, n_docked,
            timing.get("total_secs", 0),
        )
        return result

    except Exception as exc:
        # Mark as failed
        logger.error("Funnel %s failed: %s", run_id, exc, exc_info=True)
        try:
            await execute(
                """UPDATE screening_funnels SET status = 'failed',
                   timing = $1::jsonb WHERE run_id = $2""",
                json.dumps({"error": str(exc)[:500]}),
                run_id,
            )
        except Exception:
            pass
        _current_funnel = None
        raise


# ---------------------------------------------------------------------------
# Status & results
# ---------------------------------------------------------------------------

async def get_funnel_status() -> dict[str, Any]:
    """Return the status of any currently running funnel job."""
    if _current_funnel:
        return {
            "running": True,
            **_current_funnel,
        }

    # Check DB for latest running job
    await _ensure_table()
    row = await fetchrow(
        """SELECT run_id, target, status, n_generated, n_filtered,
                  n_proxy_passed, n_docked, created_at
           FROM screening_funnels
           WHERE status = 'running'
           ORDER BY created_at DESC
           LIMIT 1"""
    )
    if row:
        d = dict(row)
        d["running"] = True
        d["created_at"] = str(d["created_at"]) if d.get("created_at") else None
        return d

    return {"running": False, "message": "No funnel job currently running"}


async def get_funnel_results(run_id: str = "latest") -> dict[str, Any]:
    """Return results from a completed funnel run.

    Parameters
    ----------
    run_id : The run ID, or "latest" for the most recent completed run.
    """
    await _ensure_table()

    if run_id == "latest":
        row = await fetchrow(
            """SELECT id, run_id, target, n_generated, n_filtered,
                      n_proxy_passed, n_docked, top_candidates, timing,
                      status, created_at
               FROM screening_funnels
               WHERE status = 'completed'
               ORDER BY created_at DESC
               LIMIT 1"""
        )
    else:
        row = await fetchrow(
            """SELECT id, run_id, target, n_generated, n_filtered,
                      n_proxy_passed, n_docked, top_candidates, timing,
                      status, created_at
               FROM screening_funnels
               WHERE run_id = $1""",
            run_id,
        )

    if not row:
        return {"error": f"No funnel run found for run_id={run_id}"}

    d = dict(row)
    d["id"] = str(d["id"]) if d.get("id") else None
    d["created_at"] = str(d["created_at"]) if d.get("created_at") else None

    # Parse JSONB fields
    if isinstance(d.get("top_candidates"), str):
        try:
            d["top_candidates"] = json.loads(d["top_candidates"])
        except (json.JSONDecodeError, TypeError):
            pass
    if isinstance(d.get("timing"), str):
        try:
            d["timing"] = json.loads(d["timing"])
        except (json.JSONDecodeError, TypeError):
            pass

    return d


async def funnel_summary() -> dict[str, Any]:
    """Return summary of all funnel runs with aggregate statistics."""
    await _ensure_table()

    total = await fetchval("SELECT COUNT(*) FROM screening_funnels") or 0
    if total == 0:
        return {
            "total_runs": 0,
            "completed": 0,
            "running": 0,
            "failed": 0,
            "aggregate": {},
            "runs": [],
        }

    stats = await fetchrow(
        """SELECT
               COUNT(*) AS total_runs,
               COUNT(*) FILTER (WHERE status = 'completed') AS completed,
               COUNT(*) FILTER (WHERE status = 'running') AS running,
               COUNT(*) FILTER (WHERE status = 'failed') AS failed,
               SUM(n_generated) FILTER (WHERE status = 'completed') AS total_generated,
               SUM(n_filtered) FILTER (WHERE status = 'completed') AS total_filtered,
               SUM(n_proxy_passed) FILTER (WHERE status = 'completed') AS total_proxy_passed,
               SUM(n_docked) FILTER (WHERE status = 'completed') AS total_docked
           FROM screening_funnels"""
    )

    runs = await fetch(
        """SELECT run_id, target, n_generated, n_filtered, n_proxy_passed,
                  n_docked, status, created_at
           FROM screening_funnels
           ORDER BY created_at DESC
           LIMIT 50"""
    )

    run_list = []
    for r in runs:
        rd = dict(r)
        rd["created_at"] = str(rd["created_at"]) if rd.get("created_at") else None
        run_list.append(rd)

    s = dict(stats) if stats else {}

    return {
        "total_runs": int(s.get("total_runs", 0)),
        "completed": int(s.get("completed", 0)),
        "running": int(s.get("running", 0)),
        "failed": int(s.get("failed", 0)),
        "aggregate": {
            "total_generated": int(s.get("total_generated", 0) or 0),
            "total_filtered": int(s.get("total_filtered", 0) or 0),
            "total_proxy_passed": int(s.get("total_proxy_passed", 0) or 0),
            "total_docked": int(s.get("total_docked", 0) or 0),
            "avg_filter_rate": (
                round(int(s.get("total_filtered", 0) or 0) / max(1, int(s.get("total_generated", 0) or 0)) * 100, 1)
            ),
            "avg_proxy_rate": (
                round(int(s.get("total_proxy_passed", 0) or 0) / max(1, int(s.get("total_filtered", 0) or 0)) * 100, 1)
            ),
        },
        "runs": run_list,
    }
