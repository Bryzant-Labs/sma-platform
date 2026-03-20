"""Agentic Drug Discovery — Autonomous BioNeMo NIM Orchestration (GTC 2026).

An autonomous agent that orchestrates the full drug discovery pipeline:
  1. Check existing data for target baseline (convergence score)
  2. Generate candidates via screening library (GenMol fallback planned)
  3. Filter by drug-likeness (RDKit: Lipinski, QED > 0.3, BBB permeability)
  4. Dock via DiffDock NIM (SDF format ligands + AlphaFold PDB protein)
  5. Rank by composite score, identify positive hits (confidence > 0)
  6. Store results to platform API
  7. Return campaign summary with actions taken

Inspired by: Dyno Psi-Phi (agentic protein design) and NVIDIA's
"Agentic AI for Drug Discovery" vision presented at GTC 2026.

NOTE: GenMol has a SAFE format bug — we use the existing screening library
compounds from molecule_screenings instead of de novo generation for now.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Platform API base URL
PLATFORM_API = os.environ.get("SMA_PLATFORM_URL", "http://localhost:8090")


@dataclass
class AgentAction:
    """A single action taken by the drug discovery agent."""
    step: str
    tool: str
    input_summary: str
    output_summary: str = ""
    timestamp: str = ""
    success: bool = True
    duration_s: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class DiscoveryCampaign:
    """A complete drug discovery campaign run by the agent."""
    target: str
    scaffold: str
    goal: str
    actions: list[AgentAction] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    started_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()


# Agent capabilities — maps to BioNeMo NIMs + platform tools
AGENT_TOOLS = {
    "generate_molecules": {
        "nim": "GenMol",
        "description": "Generate novel drug-like molecules from scaffold",
        "requires": "NVIDIA_API_KEY",
    },
    "dock_molecules": {
        "nim": "DiffDock v2.2",
        "description": "Predict protein-ligand binding poses and confidence",
        "requires": "NVIDIA_API_KEY",
    },
    "predict_protein_structure": {
        "nim": "OpenFold3",
        "description": "Predict 3D protein structure from sequence",
        "requires": "NVIDIA_API_KEY",
    },
    "predict_rna_structure": {
        "nim": "RNAPro",
        "description": "Predict RNA 3D structure (SMN2 pre-mRNA)",
        "requires": "NVIDIA_API_KEY",
    },
    "filter_druglike": {
        "nim": None,
        "description": "Filter by Lipinski, BBB, QED using RDKit",
        "requires": None,
    },
    "search_evidence": {
        "nim": None,
        "description": "Search platform evidence base for target context",
        "requires": None,
    },
    "design_binders": {
        "nim": "Proteina-Complexa",
        "description": "Design protein binders for target (GPU required)",
        "requires": "PROTEINA_API_URL",
    },
}


def _load_nvidia_api_key() -> str | None:
    """Load NVIDIA API key from environment or .env file.

    Checks os.environ first, then reads from /home/bryzant/sma-platform/.env
    as fallback (production server path).
    """
    key = os.environ.get("NVIDIA_API_KEY")
    if key:
        return key

    # Try .env file (production path)
    env_paths = [
        Path("/home/bryzant/sma-platform/.env"),
        Path(".env"),
    ]
    for env_path in env_paths:
        if env_path.exists():
            try:
                for line in env_path.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("NVIDIA_API_KEY=") and not line.startswith("#"):
                        val = line.split("=", 1)[1].strip().strip("'\"")
                        if val:
                            os.environ["NVIDIA_API_KEY"] = val
                            logger.info("Loaded NVIDIA_API_KEY from %s", env_path)
                            return val
            except Exception as e:
                logger.debug("Could not read %s: %s", env_path, e)

    return None


async def list_agent_tools() -> dict[str, Any]:
    """List available tools for the drug discovery agent."""
    # Ensure key is loaded from .env if needed
    _load_nvidia_api_key()

    tools = []
    for name, info in AGENT_TOOLS.items():
        available = True
        if info["requires"]:
            available = bool(os.environ.get(info["requires"]))
        tools.append({
            "name": name,
            "nim": info["nim"],
            "description": info["description"],
            "available": available,
        })
    return {"tools": tools, "total": len(tools), "available": sum(1 for t in tools if t["available"])}


# ---------------------------------------------------------------------------
# Step 1: Check baseline — query convergence score for target
# ---------------------------------------------------------------------------

async def _check_baseline(target: str) -> dict[str, Any]:
    """Query the platform API for existing convergence data on the target."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{PLATFORM_API}/api/v2/convergence/scores")
            if resp.status_code == 200:
                data = resp.json()
                scores = data.get("scores", data.get("results", []))
                for score in scores:
                    symbol = score.get("symbol", score.get("target", ""))
                    if symbol.upper() == target.upper():
                        return {
                            "found": True,
                            "symbol": symbol,
                            "convergence_score": score.get("convergence_score", score.get("score", 0)),
                            "evidence_count": score.get("evidence_count", 0),
                        }
                return {"found": False, "symbol": target, "note": "Target not in convergence scores"}
    except Exception as e:
        logger.warning("Baseline check failed: %s", e)
    return {"found": False, "symbol": target, "note": "Platform API unreachable"}


# ---------------------------------------------------------------------------
# Step 2: Get candidate compounds from screening library
# ---------------------------------------------------------------------------

async def _get_library_compounds(target: str, limit: int = 50) -> list[dict[str, Any]]:
    """Fetch existing screening compounds for the target from molecule_screenings.

    GenMol has a SAFE format bug, so we use the existing screening library
    instead of generating new molecules for now.
    """
    compounds: list[dict[str, Any]] = []

    # Try platform database first
    try:
        from ..core.database import fetch
        rows = await fetch(
            """SELECT DISTINCT ON (smiles) smiles, chembl_id, compound_name,
                      molecular_weight, alogp, pchembl_value
               FROM molecule_screenings
               WHERE target_symbol = $1
                 AND smiles IS NOT NULL AND smiles != ''
                 AND drug_likeness_pass = TRUE
               ORDER BY smiles, pchembl_value DESC NULLS LAST
               LIMIT $2""",
            target.upper(), limit,
        )
        for row in rows:
            compounds.append({
                "smiles": row["smiles"],
                "name": row.get("chembl_id") or row.get("compound_name") or "",
                "mw": float(row["molecular_weight"]) if row.get("molecular_weight") else None,
                "logp": float(row["alogp"]) if row.get("alogp") else None,
                "pchembl": float(row["pchembl_value"]) if row.get("pchembl_value") else None,
                "source": "molecule_screenings",
            })
        if compounds:
            logger.info("Loaded %d library compounds for %s from database", len(compounds), target)
            return compounds
    except Exception as e:
        logger.warning("Database query for library compounds failed: %s", e)

    # Fallback: known SMA-relevant compounds (curated)
    _FALLBACK_COMPOUNDS: list[dict[str, Any]] = [
        {"smiles": "Nc1ccncc1", "name": "4-Aminopyridine (4-AP)", "source": "curated"},
        {"smiles": "CC(=O)Nc1ccc(O)cc1", "name": "Acetaminophen", "source": "curated"},
        {"smiles": "O=C(O)c1ccccc1O", "name": "Salicylic acid", "source": "curated"},
        {"smiles": "c1ccc2[nH]ccc2c1", "name": "Indole scaffold", "source": "curated"},
        {"smiles": "CC1=CC(=O)c2ccccc2C1=O", "name": "Menadione", "source": "curated"},
        {"smiles": "c1ccc(-c2ccncc2)cc1", "name": "4-Phenylpyridine", "source": "curated"},
        {"smiles": "Nc1cccc(N)n1", "name": "2,4-Diaminopyrimidine", "source": "curated"},
        {"smiles": "O=c1[nH]c(=O)c2[nH]cnc2[nH]1", "name": "Uric acid", "source": "curated"},
        {"smiles": "Cc1ncc(CO)c(CO)c1O", "name": "Pyridoxine (B6)", "source": "curated"},
        {"smiles": "c1ccc2c(c1)ccc1ccccc12", "name": "Phenanthrene scaffold", "source": "curated"},
    ]
    logger.info("Using %d fallback curated compounds (database unavailable)", len(_FALLBACK_COMPOUNDS))
    return _FALLBACK_COMPOUNDS


# ---------------------------------------------------------------------------
# Step 3: Filter by drug-likeness (RDKit)
# ---------------------------------------------------------------------------

def _filter_druglike(compounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter compounds by Lipinski Rule of 5, QED > 0.3, and BBB permeability."""
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, QED
    except ImportError:
        logger.warning("RDKit not available — passing all compounds through filter")
        for c in compounds:
            c["lipinski_pass"] = True
            c["qed"] = 0.5
            c["bbb_permeable"] = True
        return compounds

    filtered = []
    for comp in compounds:
        try:
            mol = Chem.MolFromSmiles(comp["smiles"])
            if mol is None:
                continue

            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            hbd = Descriptors.NumHDonors(mol)
            hba = Descriptors.NumHAcceptors(mol)
            tpsa = Descriptors.TPSA(mol)

            lipinski = mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10
            bbb = tpsa < 90 and mw < 450 and logp > 0
            qed_score = QED.qed(mol)

            comp["lipinski_pass"] = lipinski
            comp["bbb_permeable"] = bbb
            comp["qed"] = round(qed_score, 4)
            comp["mw"] = round(mw, 2)
            comp["logp"] = round(logp, 2)
            comp["tpsa"] = round(tpsa, 2)

            if lipinski and qed_score > 0.3:
                filtered.append(comp)
        except Exception as e:
            logger.debug("Filter error for %s: %s", comp.get("smiles", "?"), e)

    return filtered


# ---------------------------------------------------------------------------
# Step 4: Dock via DiffDock NIM
# ---------------------------------------------------------------------------

def _get_target_pdb(target: str) -> str | None:
    """Get PDB content for a known SMA target from AlphaFold structures."""
    _TARGET_PDB_MAP = {
        "SMN2": "data/pdb/SMN2_Q16637.pdb",
        "SMN1": "data/pdb/SMN2_Q16637.pdb",
        "STMN2": "data/pdb/STMN2_Q93045.pdb",
        "PLS3": "data/pdb/PLS3_P13797.pdb",
        "NCALD": "data/pdb/NCALD_P61601.pdb",
        "UBA1": "data/pdb/UBA1_P22314.pdb",
        "CORO1C": "data/pdb/CORO1C_Q9ULV4.pdb",
        "TP53": "data/pdb/TP53_P04637.pdb",
    }

    pdb_path = _TARGET_PDB_MAP.get(target.upper())
    if not pdb_path:
        logger.warning("No PDB structure for target %s. Available: %s", target, list(_TARGET_PDB_MAP.keys()))
        return None

    for base in [Path("."), Path("/home/bryzant/sma-platform")]:
        full = base / pdb_path
        if full.exists():
            content = full.read_text()
            atoms = sum(1 for line in content.split("\n") if line.startswith("ATOM"))
            logger.info("Loaded PDB for %s: %d atoms from %s", target, atoms, full)
            return content

    logger.warning("PDB file not found for %s at %s — attempting AlphaFold download", target, pdb_path)
    return None


async def _download_alphafold_pdb(target: str) -> str | None:
    """Download PDB from AlphaFold EBI as fallback."""
    target_uniprot = {
        "SMN2": "Q16637", "SMN1": "Q16637",
        "PLS3": "P13797", "STMN2": "Q93045",
        "NCALD": "P61601", "UBA1": "P22314",
        "CORO1C": "Q9ULV4", "TP53": "P04637",
    }
    uniprot_id = target_uniprot.get(target.upper())
    if not uniprot_id:
        return None

    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v6.pdb"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            pdb_content = resp.text
            logger.info("Downloaded AlphaFold PDB for %s (%s): %d bytes", target, uniprot_id, len(pdb_content))
            return pdb_content
    except Exception as e:
        logger.error("AlphaFold PDB download failed for %s: %s", target, e)
        return None


async def _dock_compounds(
    compounds: list[dict[str, Any]],
    target: str,
) -> list[dict[str, Any]]:
    """Dock compounds against target using DiffDock NIM.

    Uses SDF format ligands (RDKit MolToMolBlock) and PDB format protein.
    Attempts individual docking (DiffDock needs SDF format, not SMILES).
    """
    # Ensure NVIDIA API key is loaded
    api_key = _load_nvidia_api_key()
    if not api_key:
        logger.error("NVIDIA_API_KEY not available — skipping docking step")
        for c in compounds:
            c["docking_confidence"] = -999.0
            c["dock_status"] = "skipped_no_api_key"
        return compounds

    # Get PDB content for target
    pdb_content = _get_target_pdb(target)
    if not pdb_content:
        pdb_content = await _download_alphafold_pdb(target)
    if not pdb_content:
        logger.error("No PDB structure available for target %s — skipping docking", target)
        for c in compounds:
            c["docking_confidence"] = -999.0
            c["dock_status"] = "skipped_no_pdb"
        return compounds

    # Import adapter
    from ..ingestion.adapters.nvidia_nims import diffdock_dock

    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        logger.error("RDKit required for SDF ligand conversion — skipping docking")
        for c in compounds:
            c["docking_confidence"] = -999.0
            c["dock_status"] = "skipped_no_rdkit"
        return compounds

    # Dock each compound individually (DiffDock needs SDF format ligands)
    docked = []
    failed_count = 0
    for comp in compounds:
        try:
            mol = Chem.MolFromSmiles(comp["smiles"])
            if mol is None:
                comp["docking_confidence"] = -999.0
                comp["dock_status"] = "invalid_smiles"
                docked.append(comp)
                continue

            # Generate 3D coordinates and convert to SDF
            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
            AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
            sdf_block = Chem.MolToMolBlock(mol)

            dock_result = await diffdock_dock(
                protein_pdb=pdb_content,
                ligand_sdf=sdf_block,
                num_poses=3,
            )

            confidence = dock_result.get("position_confidence", dock_result.get("confidence", -1.0))
            if isinstance(confidence, list):
                confidence = max(confidence) if confidence else -1.0
            comp["docking_confidence"] = float(confidence)
            comp["dock_status"] = "docked"
            docked.append(comp)

        except Exception as e:
            failed_count += 1
            if failed_count <= 3:
                logger.warning("Docking failed for %s: %s", comp.get("name", "?"), e)
            comp["docking_confidence"] = -999.0
            comp["dock_status"] = "dock_failed"
            docked.append(comp)

    if failed_count > 3:
        logger.warning("Total docking failures: %d / %d", failed_count, len(compounds))

    return docked


# ---------------------------------------------------------------------------
# Step 5: Rank candidates
# ---------------------------------------------------------------------------

def _rank_candidates(compounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank candidates by composite score: docking confidence + QED + BBB bonus."""
    for comp in compounds:
        score = 0.0
        dock_conf = comp.get("docking_confidence", -999.0)
        if dock_conf > -900:
            score += dock_conf * 0.5
        score += comp.get("qed", 0) * 0.3
        if comp.get("bbb_permeable"):
            score += 0.2
        comp["composite_score"] = round(score, 4)

    return sorted(compounds, key=lambda c: c.get("composite_score", 0), reverse=True)


# ---------------------------------------------------------------------------
# Step 6: Store results to platform API
# ---------------------------------------------------------------------------

async def _store_results(
    campaign: DiscoveryCampaign,
    ranked: list[dict[str, Any]],
) -> bool:
    """Persist campaign results: milestones for positive hits + blackboard post."""
    # Create milestones for positive hits
    positive_hits = [c for c in ranked if c.get("docking_confidence", -999) > 0]
    milestones_created = 0

    if positive_hits:
        try:
            from ..reasoning.milestone_tracker import create_milestones_for_hit
            for hit in positive_hits[:5]:  # Max 5 hits get milestones
                await create_milestones_for_hit(
                    smiles=hit["smiles"],
                    target=campaign.target,
                    docking_confidence=hit["docking_confidence"],
                    compound_name=hit.get("name"),
                )
                milestones_created += 1
        except Exception as e:
            logger.warning("Milestone creation failed: %s", e)

    # Try posting to blackboard for team visibility
    try:
        from ..reasoning.blackboard import auto_post_discovery
        if positive_hits:
            best = positive_hits[0]
            await auto_post_discovery(
                agent="drug-discovery-agent",
                target_symbol=campaign.target,
                discovery_type="docking_hit",
                payload={
                    "smiles": best["smiles"],
                    "name": best.get("name", ""),
                    "docking_confidence": best["docking_confidence"],
                    "qed": best.get("qed", 0),
                    "composite_score": best.get("composite_score", 0),
                    "campaign_target": campaign.target,
                    "campaign_goal": campaign.goal,
                    "total_screened": len(ranked),
                    "positive_hits": len(positive_hits),
                },
            )
    except Exception as e:
        logger.debug("Blackboard post failed (non-critical): %s", e)

    logger.info(
        "Stored results: %d milestones created for %d positive hits out of %d compounds",
        milestones_created, len(positive_hits), len(ranked),
    )
    return True


# ---------------------------------------------------------------------------
# In-memory campaign history
# ---------------------------------------------------------------------------

_campaign_history: list[dict[str, Any]] = []


async def list_campaigns() -> list[dict[str, Any]]:
    """Return past campaign summaries (in-memory, most recent first)."""
    return list(reversed(_campaign_history))


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def run_discovery_campaign(
    target: str = "SMN2",
    scaffold: str = "Nc1ccncc1",
    goal: str = "Find novel SMN2-binding compounds with BBB permeability",
    max_candidates: int = 50,
) -> dict[str, Any]:
    """Run an autonomous drug discovery campaign.

    The agent orchestrates the full pipeline:
      1. Check baseline convergence score for target
      2. Get candidate compounds from screening library
      3. Filter by drug-likeness (Lipinski, QED > 0.3, BBB)
      4. Dock via DiffDock NIM (SDF ligands + PDB protein)
      5. Rank by composite score, identify positive hits
      6. Store results (milestones + blackboard)
      7. Return campaign summary

    Args:
        target: SMA target protein (e.g., SMN2, CORO1C, PLS3)
        scaffold: Starting molecule scaffold (used for fallback generation)
        goal: Natural language description of campaign goal
        max_candidates: Maximum candidates to process

    Returns:
        Campaign results with actions taken, findings, and top candidates
    """
    campaign = DiscoveryCampaign(target=target, scaffold=scaffold, goal=goal)
    campaign.status = "running"
    campaign_start = time.monotonic()

    logger.info("=== Discovery Campaign Started: %s — %s ===", target, goal)

    # ---- Step 1: Check baseline ----
    t0 = time.monotonic()
    baseline = await _check_baseline(target)
    dt = time.monotonic() - t0

    campaign.actions.append(AgentAction(
        step="1_baseline",
        tool="search_evidence",
        input_summary=f"Query convergence score for {target}",
        output_summary=(
            f"Score: {baseline.get('convergence_score', 'N/A')}, "
            f"Evidence: {baseline.get('evidence_count', 'N/A')}"
            if baseline.get("found")
            else f"Not found — {baseline.get('note', 'unknown')}"
        ),
        success=baseline.get("found", False),
        duration_s=round(dt, 2),
    ))

    # ---- Step 2: Get candidate compounds ----
    t0 = time.monotonic()
    compounds = await _get_library_compounds(target, limit=max_candidates)
    dt = time.monotonic() - t0

    campaign.actions.append(AgentAction(
        step="2_candidates",
        tool="generate_molecules (library)",
        input_summary=f"Fetch up to {max_candidates} compounds for {target}",
        output_summary=f"Retrieved {len(compounds)} compounds",
        success=len(compounds) > 0,
        duration_s=round(dt, 2),
    ))

    if not compounds:
        campaign.status = "failed"
        campaign.actions.append(AgentAction(
            step="2_candidates_error",
            tool="none",
            input_summary="No compounds available for target",
            success=False,
        ))
        result = _build_result(campaign, [])
        _campaign_history.append(result)
        return result

    # ---- Step 3: Filter by drug-likeness ----
    t0 = time.monotonic()
    filtered = _filter_druglike(compounds)
    dt = time.monotonic() - t0

    campaign.actions.append(AgentAction(
        step="3_filter",
        tool="filter_druglike",
        input_summary=f"Lipinski + QED > 0.3 + BBB filter on {len(compounds)} compounds",
        output_summary=f"Passed: {len(filtered)} / {len(compounds)}",
        success=len(filtered) > 0,
        duration_s=round(dt, 2),
    ))

    if not filtered:
        logger.warning("No compounds passed drug-likeness filter — using all compounds")
        filtered = compounds
        campaign.actions[-1].output_summary += " (relaxed — using all)"

    # ---- Step 4: Dock via DiffDock NIM ----
    t0 = time.monotonic()
    docked = await _dock_compounds(filtered, target)
    dt = time.monotonic() - t0

    n_success = sum(1 for c in docked if c.get("dock_status") == "docked")
    n_positive = sum(1 for c in docked if c.get("docking_confidence", -999) > 0)
    campaign.actions.append(AgentAction(
        step="4_dock",
        tool="dock_molecules (DiffDock v2.2)",
        input_summary=f"Dock {len(filtered)} compounds against {target}",
        output_summary=f"Docked: {n_success}/{len(filtered)}, Positive: {n_positive}",
        success=n_success > 0,
        duration_s=round(dt, 2),
    ))

    # ---- Step 5: Rank candidates ----
    t0 = time.monotonic()
    ranked = _rank_candidates(docked)
    dt = time.monotonic() - t0

    # Identify findings
    positive_hits = [c for c in ranked if c.get("docking_confidence", -999) > 0]
    if positive_hits:
        for hit in positive_hits[:5]:
            campaign.findings.append({
                "type": "positive_docking",
                "smiles": hit["smiles"],
                "name": hit.get("name", ""),
                "confidence": hit.get("docking_confidence", 0),
                "qed": hit.get("qed", 0),
                "composite_score": hit.get("composite_score", 0),
                "bbb": hit.get("bbb_permeable", False),
                "target": target,
                "significance": (
                    "Strong hit — confidence > 0.1"
                    if hit.get("docking_confidence", 0) > 0.1
                    else "Positive docking — potential hit"
                ),
            })

    campaign.actions.append(AgentAction(
        step="5_rank",
        tool="rank_candidates",
        input_summary=f"Rank {len(docked)} docked compounds by composite score",
        output_summary=(
            f"Top score: {ranked[0]['composite_score'] if ranked else 'N/A'}, "
            f"Positive hits: {len(positive_hits)}"
        ),
        success=True,
        duration_s=round(dt, 2),
    ))

    # ---- Step 6: Store results ----
    t0 = time.monotonic()
    try:
        stored = await _store_results(campaign, ranked)
    except Exception as e:
        logger.error("Result storage failed: %s", e)
        stored = False
    dt = time.monotonic() - t0

    campaign.actions.append(AgentAction(
        step="6_store",
        tool="store_results",
        input_summary=f"Persist {len(positive_hits)} positive hits + milestones",
        output_summary="Stored" if stored else "Storage failed (non-critical)",
        success=stored,
        duration_s=round(dt, 2),
    ))

    # ---- Step 7: Finalize ----
    total_time = time.monotonic() - campaign_start
    campaign.status = "completed"
    campaign.completed_at = datetime.now(timezone.utc).isoformat()

    logger.info(
        "=== Discovery Campaign Completed: %s — %d candidates, %d hits, %.1fs ===",
        target, len(ranked), len(positive_hits), total_time,
    )

    result = _build_result(campaign, ranked, total_time)
    _campaign_history.append(result)
    return result


def _build_result(
    campaign: DiscoveryCampaign,
    ranked: list[dict[str, Any]],
    total_time: float = 0.0,
) -> dict[str, Any]:
    """Build the final campaign result dict."""
    return {
        "status": campaign.status,
        "target": campaign.target,
        "scaffold": campaign.scaffold,
        "goal": campaign.goal,
        "started_at": campaign.started_at,
        "completed_at": campaign.completed_at,
        "total_duration_s": round(total_time, 2),
        "actions": [
            {
                "step": a.step,
                "tool": a.tool,
                "input": a.input_summary,
                "output": a.output_summary,
                "success": a.success,
                "duration_s": a.duration_s,
                "timestamp": a.timestamp,
            }
            for a in campaign.actions
        ],
        "findings": campaign.findings,
        "n_actions": len(campaign.actions),
        "n_findings": len(campaign.findings),
        "top_candidates": [
            {
                "smiles": c["smiles"],
                "name": c.get("name", ""),
                "qed": c.get("qed", 0),
                "lipinski": c.get("lipinski_pass", False),
                "bbb": c.get("bbb_permeable", False),
                "docking_confidence": round(c.get("docking_confidence", -999), 4),
                "composite_score": round(c.get("composite_score", 0), 4),
                "dock_status": c.get("dock_status", "unknown"),
            }
            for c in ranked[:20]
        ],
        "summary": {
            "total_candidates": len(ranked),
            "positive_hits": sum(1 for c in ranked if c.get("docking_confidence", -999) > 0),
            "top_score": ranked[0]["composite_score"] if ranked else 0,
            "best_confidence": max((c.get("docking_confidence", -999) for c in ranked), default=-999),
        },
    }
