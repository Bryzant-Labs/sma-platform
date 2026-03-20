"""Protein structure adapter — AlphaFold DB + variant effect prediction.

Fetches pre-computed 3D structures and per-residue confidence (pLDDT) from
the AlphaFold Protein Structure Database for core SMA-related proteins.
Integrates AlphaFold Missense pathogenicity predictions for variant analysis.

No API key required. Rate limits: AlphaFold DB — reasonable use policy.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

ALPHAFOLD_API = "https://alphafold.ebi.ac.uk/api"
UNIPROT_API = "https://rest.uniprot.org/uniprotkb"

# Core SMA proteins with UniProt accessions
SMA_PROTEINS: dict[str, dict[str, str]] = {
    "SMN1": {"uniprot": "P62316", "name": "Survival Motor Neuron 1"},
    "SMN2": {"uniprot": "Q16637", "name": "Survival Motor Neuron 2"},
    "PLS3": {"uniprot": "P13797", "name": "Plastin-3"},
    "STMN2": {"uniprot": "Q93045", "name": "Stathmin-2"},
    "NCALD": {"uniprot": "P61601", "name": "Neurocalcin-delta"},
    "UBA1": {"uniprot": "P22314", "name": "Ubiquitin-activating enzyme E1"},
    "CORO1C": {"uniprot": "Q9ULV4", "name": "Coronin-1C"},
}


async def fetch_alphafold_prediction(uniprot_id: str) -> dict[str, Any] | None:
    """Fetch pre-computed structure prediction from AlphaFold DB.

    Args:
        uniprot_id: UniProt accession (e.g. ``"P62316"``).

    Returns:
        Dict with structure metadata, model URLs, and pLDDT summary,
        or ``None`` if the protein is not in AlphaFold DB.
    """
    url = f"{ALPHAFOLD_API}/prediction/{uniprot_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 404:
                logger.debug("No AlphaFold prediction for %s", uniprot_id)
                return None
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("AlphaFold API error for %s: %s", uniprot_id, exc)
            return None
        except httpx.RequestError as exc:
            logger.error("AlphaFold request error for %s: %s", uniprot_id, exc)
            return None

    # API returns a list; take the first (latest) model
    data = resp.json()
    if not data:
        return None

    entry = data[0] if isinstance(data, list) else data

    return {
        "uniprot_id": uniprot_id,
        "entry_id": entry.get("entryId", ""),
        "gene": entry.get("gene", ""),
        "organism": entry.get("organismScientificName", ""),
        "sequence_length": entry.get("uniprotEnd", 0) - entry.get("uniprotStart", 0) + 1,
        "model_url": entry.get("pdbUrl", ""),
        "cif_url": entry.get("cifUrl", ""),
        "pae_url": entry.get("paeImageUrl", ""),
        "model_created_date": entry.get("modelCreatedDate", ""),
        "latest_version": entry.get("latestVersion", 0),
        "mean_plddt": entry.get("globalMetricValue"),
        "confidence_type": entry.get("confidenceType", ""),
        "confidence_version": entry.get("confidenceVersion"),
    }


async def fetch_alphafold_missense(uniprot_id: str) -> list[dict[str, Any]]:
    """Fetch pre-computed missense pathogenicity scores from AlphaFold.

    The AlphaFold Missense database provides pathogenicity scores for
    every possible single amino acid substitution in a protein.

    Args:
        uniprot_id: UniProt accession.

    Returns:
        List of variant effect dicts, or empty list if unavailable.
        Each dict: position, wildtype_aa, mutant_aa, pathogenicity_score,
        pathogenicity_class.
    """
    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-aa-substitutions.csv"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 404:
                logger.debug("No AlphaFold Missense data for %s", uniprot_id)
                return []
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.debug("AlphaFold Missense unavailable for %s: %s", uniprot_id, exc)
            return []

    lines = resp.text.strip().split("\n")
    if len(lines) < 2:
        return []

    # Parse CSV header
    header = lines[0].split(",")
    variants: list[dict[str, Any]] = []

    for line in lines[1:]:
        fields = line.split(",")
        if len(fields) < len(header):
            continue

        row = dict(zip(header, fields))

        try:
            score = float(row.get("am_pathogenicity", "0"))
        except (ValueError, TypeError):
            score = 0.0

        am_class = row.get("am_class", "")

        variants.append({
            "protein_variant": row.get("protein_variant", ""),
            "position": row.get("residue_number", ""),
            "wildtype_aa": row.get("wildtype_aa", ""),
            "mutant_aa": row.get("mutant_aa", ""),
            "pathogenicity_score": score,
            "pathogenicity_class": am_class,
        })

    logger.info(
        "AlphaFold Missense for %s: %d variant scores loaded",
        uniprot_id,
        len(variants),
    )
    return variants


async def fetch_uniprot_sequence(uniprot_id: str) -> str | None:
    """Fetch protein sequence from UniProt REST API.

    Args:
        uniprot_id: UniProt accession.

    Returns:
        Amino acid sequence string, or ``None`` on failure.
    """
    url = f"{UNIPROT_API}/{uniprot_id}.fasta"

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("UniProt fetch failed for %s: %s", uniprot_id, exc)
            return None

    lines = resp.text.strip().split("\n")
    # Skip the FASTA header line (starts with >)
    sequence = "".join(line.strip() for line in lines if not line.startswith(">"))
    return sequence if sequence else None


async def predict_variant_effect(
    uniprot_id: str,
    variant: str,
) -> dict[str, Any]:
    """Predict the effect of a single amino acid substitution.

    Uses AlphaFold Missense pre-computed scores when available.

    Args:
        uniprot_id: UniProt accession of the protein.
        variant: Variant in format ``"A123V"`` (original AA, position, new AA).

    Returns:
        Dict with variant, pathogenicity_score, pathogenicity_class,
        and source information.
    """
    missense_data = await fetch_alphafold_missense(uniprot_id)

    if missense_data:
        # Search for the specific variant
        for v in missense_data:
            if v.get("protein_variant", "").upper() == variant.upper():
                return {
                    "variant": variant,
                    "uniprot_id": uniprot_id,
                    "pathogenicity_score": v["pathogenicity_score"],
                    "pathogenicity_class": v["pathogenicity_class"],
                    "source": "alphafold_missense",
                    "found": True,
                }

    return {
        "variant": variant,
        "uniprot_id": uniprot_id,
        "pathogenicity_score": None,
        "pathogenicity_class": "unknown",
        "source": "not_found",
        "found": False,
    }


async def fetch_sma_protein_structures() -> list[dict[str, Any]]:
    """Fetch AlphaFold predictions for all core SMA proteins.

    Returns:
        List of structure prediction dicts, one per successfully fetched protein.
    """
    results: list[dict[str, Any]] = []

    for symbol, info in SMA_PROTEINS.items():
        uniprot_id = info["uniprot"]
        logger.debug("Fetching AlphaFold structure for %s (%s)", symbol, uniprot_id)

        prediction = await fetch_alphafold_prediction(uniprot_id)
        if prediction is not None:
            prediction["symbol"] = symbol
            prediction["protein_name"] = info["name"]
            results.append(prediction)

        await asyncio.sleep(0.3)

    logger.info(
        "fetch_sma_protein_structures: %d/%d proteins have AlphaFold structures",
        len(results),
        len(SMA_PROTEINS),
    )
    return results


def build_structure_summary(
    prediction: dict[str, Any],
    missense_count: int = 0,
) -> str:
    """Build a plain-text summary of a protein structure for the platform.

    Args:
        prediction: A prediction dict from ``fetch_alphafold_prediction()``.
        missense_count: Number of missense variant scores available.

    Returns:
        Multi-line plain-text string.
    """
    lines: list[str] = []

    symbol = prediction.get("symbol", prediction.get("gene", ""))
    name = prediction.get("protein_name", "")
    uniprot = prediction.get("uniprot_id", "")

    lines.append(f"Protein structure: {symbol} ({name}) — UniProt {uniprot}")

    organism = prediction.get("organism", "")
    if organism:
        lines.append(f"Organism: {organism}")

    seq_len = prediction.get("sequence_length", 0)
    if seq_len:
        lines.append(f"Sequence length: {seq_len} residues")

    mean_plddt = prediction.get("mean_plddt")
    if mean_plddt is not None:
        confidence = (
            "Very High" if mean_plddt > 90
            else "Confident" if mean_plddt > 70
            else "Low" if mean_plddt > 50
            else "Very Low"
        )
        lines.append(f"Mean pLDDT: {mean_plddt:.1f} ({confidence} confidence)")

    model_date = prediction.get("model_created_date", "")
    if model_date:
        lines.append(f"Model date: {model_date}")

    if missense_count > 0:
        lines.append(
            f"AlphaFold Missense: {missense_count} variant pathogenicity scores available"
        )

    model_url = prediction.get("model_url", "")
    if model_url:
        lines.append(f"3D structure: {model_url}")

    return "\n".join(lines)


# =============================================================================
# AlphaFold Protein Complex Predictions (GTC 2026 — 1.7M new complexes)
# =============================================================================

# SMA-relevant protein complexes to check
SMA_COMPLEX_QUERIES = [
    # SMN complexes
    {"name": "SMN-Gemin2", "uniprot_ids": ["Q16637", "O14893"], "desc": "Core SMN complex — essential for snRNP assembly"},
    {"name": "SMN-Gemin3", "uniprot_ids": ["Q16637", "O15541"], "desc": "SMN complex RNA helicase component"},
    {"name": "SMN-Gemin5", "uniprot_ids": ["Q16637", "Q8TEQ6"], "desc": "SMN complex snRNA binding component"},
    {"name": "SMN-p53", "uniprot_ids": ["Q16637", "P04637"], "desc": "SMN-p53 direct interaction — motor neuron death pathway"},
    {"name": "SMN-UBA1", "uniprot_ids": ["Q16637", "P22314"], "desc": "Ubiquitin pathway dysregulation in SMA"},
    # Modifier complexes
    {"name": "PLS3-actin", "uniprot_ids": ["P13797", "P60709"], "desc": "Plastin 3 actin-bundling — SMA severity modifier"},
    {"name": "NCALD-CaM", "uniprot_ids": ["P61601", "P62158"], "desc": "Neurocalcin delta calcium sensing"},
    {"name": "STMN2-tubulin", "uniprot_ids": ["Q93045", "Q13509"], "desc": "Stathmin-2 microtubule regulation"},
]

ALPHAFOLD_COMPLEX_API = "https://alphafold.ebi.ac.uk/api"


async def check_complex_predictions() -> list[dict]:
    """Check AlphaFold DB for predicted structures of SMA protein complexes.

    The AlphaFold DB was expanded with 1.7M new protein complexes at GTC 2026.
    We check if any SMA-relevant complexes now have predicted structures.
    """
    results = []
    async with httpx.AsyncClient(timeout=30) as client:
        for complex_info in SMA_COMPLEX_QUERIES:
            found = False
            structure_url = None
            confidence = None

            # Try searching by UniProt ID pairs
            for uid in complex_info["uniprot_ids"]:
                try:
                    resp = await client.get(
                        f"{ALPHAFOLD_COMPLEX_API}/prediction/{uid}",
                        headers={"Accept": "application/json"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list) and len(data) > 0:
                            entry = data[0]
                            structure_url = entry.get("pdbUrl") or entry.get("cifUrl")
                            confidence = entry.get("globalMetricValue")
                            found = True
                except Exception as e:
                    logger.debug("AlphaFold query for %s failed: %s", uid, e)

                await asyncio.sleep(0.2)  # Rate limit

            results.append({
                "complex": complex_info["name"],
                "description": complex_info["desc"],
                "uniprot_ids": complex_info["uniprot_ids"],
                "predicted": found,
                "structure_url": structure_url,
                "confidence": confidence,
            })

    return results
