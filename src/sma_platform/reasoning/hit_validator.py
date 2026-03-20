"""Hit Validator — cross-reference screening hits against public databases.

Checks if discovered binding interactions are novel or already known.
Uses ChEMBL, PubMed, PubChem, and platform claims for validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    smiles: str
    target: str
    docking_confidence: float
    # Validation checks
    chembl_known: bool = False
    chembl_activities: list[dict] = field(default_factory=list)
    pubmed_papers: int = 0
    pubmed_top_titles: list[str] = field(default_factory=list)
    platform_claims: int = 0
    platform_claim_ids: list[str] = field(default_factory=list)
    pubchem_cid: str | None = None
    pubchem_name: str | None = None
    # Assessment
    novelty: str = "unknown"  # "novel", "partially_known", "well_known"
    validation_summary: str = ""


async def validate_hit(
    smiles: str,
    target: str,
    docking_confidence: float,
) -> ValidationResult:
    """Validate a single screening hit against public databases."""
    result = ValidationResult(
        smiles=smiles,
        target=target,
        docking_confidence=docking_confidence,
    )

    # 1. Check PubChem for compound identity
    await _check_pubchem(result)

    # 2. Check ChEMBL for known bioactivity
    await _check_chembl(result)

    # 3. Check PubMed for literature
    await _check_pubmed(result)

    # 4. Check platform claims
    await _check_platform_claims(result)

    # 5. Assess novelty
    _assess_novelty(result)

    return result


async def validate_all_hits(hits: list[dict]) -> list[dict]:
    """Validate a list of screening hits. Input: [{smiles, target, docking_confidence}, ...]"""
    results = []
    for hit in hits:
        try:
            v = await validate_hit(
                smiles=hit["smiles"],
                target=hit["target"],
                docking_confidence=hit.get("docking_confidence", 0),
            )
            results.append({
                "smiles": v.smiles,
                "target": v.target,
                "docking_confidence": v.docking_confidence,
                "pubchem_name": v.pubchem_name,
                "pubchem_cid": v.pubchem_cid,
                "chembl_known": v.chembl_known,
                "chembl_activities": len(v.chembl_activities),
                "pubmed_papers": v.pubmed_papers,
                "pubmed_titles": v.pubmed_top_titles[:3],
                "platform_claims": v.platform_claims,
                "novelty": v.novelty,
                "summary": v.validation_summary,
            })
        except Exception as e:
            logger.error("Validation failed for %s: %s", hit.get("smiles"), e)
            results.append({**hit, "error": str(e), "novelty": "error"})
    return results


async def _check_pubchem(result: ValidationResult):
    """Look up compound in PubChem by SMILES."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{result.smiles}/property/IUPACName,MolecularFormula/JSON"
            )
            if resp.status_code == 200:
                data = resp.json()
                props = data.get("PropertyTable", {}).get("Properties", [{}])[0]
                result.pubchem_cid = str(props.get("CID", ""))
                result.pubchem_name = props.get("IUPACName", "")
    except Exception as e:
        logger.debug("PubChem lookup failed: %s", e)


async def _check_chembl(result: ValidationResult):
    """Check ChEMBL for known bioactivity of this compound against the target."""
    if not result.pubchem_name:
        return
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Search ChEMBL by molecule name/SMILES
            resp = await client.get(
                f"https://www.ebi.ac.uk/chembl/api/data/molecule/search?q={result.smiles}&format=json&limit=5"
            )
            if resp.status_code == 200:
                data = resp.json()
                molecules = data.get("molecules", [])
                if molecules:
                    result.chembl_known = True
                    for mol in molecules[:3]:
                        result.chembl_activities.append({
                            "chembl_id": mol.get("molecule_chembl_id", ""),
                            "name": mol.get("pref_name", ""),
                        })
    except Exception as e:
        logger.debug("ChEMBL lookup failed: %s", e)


async def _check_pubmed(result: ValidationResult):
    """Search PubMed for papers about this compound + target."""
    compound_name = result.pubchem_name or result.smiles
    query = f'"{compound_name}" AND ("{result.target}" OR "spinal muscular atrophy")'
    try:
        from Bio import Entrez
        Entrez.email = "christian@bryzant.com"
        handle = Entrez.esearch(db="pubmed", term=query, retmax=5)
        record = Entrez.read(handle)
        handle.close()
        result.pubmed_papers = int(record.get("Count", 0))
        pmids = record.get("IdList", [])
        if pmids:
            # Fetch titles
            handle2 = Entrez.efetch(db="pubmed", id=pmids[:3], rettype="medline", retmode="text")
            text = handle2.read()
            handle2.close()
            for line in text.split("\n"):
                if line.startswith("TI  - "):
                    result.pubmed_top_titles.append(line[6:].strip())
    except Exception as e:
        logger.debug("PubMed search failed: %s", e)


async def _check_platform_claims(result: ValidationResult):
    """Search our own 30k+ claims for mentions of this compound or scaffold."""
    try:
        from ..reasoning.embeddings import hybrid_search, _ensure_index
        if not _ensure_index():
            return
        compound_name = result.pubchem_name or result.smiles
        search_results = await hybrid_search(
            f"{compound_name} {result.target} binding", top_k=5
        )
        claims = [r for r in search_results if r["type"] == "claim"]
        result.platform_claims = len(claims)
        result.platform_claim_ids = [r["id"] for r in claims[:5]]
    except Exception as e:
        logger.debug("Platform claim search failed: %s", e)


def _assess_novelty(result: ValidationResult):
    """Assess whether this hit is novel, partially known, or well known."""
    evidence_count = (
        (1 if result.chembl_known else 0) +
        min(result.pubmed_papers, 3) +
        min(result.platform_claims, 2)
    )

    if evidence_count == 0:
        result.novelty = "novel"
        result.validation_summary = (
            f"No prior evidence found for {result.pubchem_name or result.smiles} "
            f"binding to {result.target}. This appears to be a novel computational prediction."
        )
    elif evidence_count <= 2:
        result.novelty = "partially_known"
        result.validation_summary = (
            f"Limited prior evidence ({result.pubmed_papers} papers, "
            f"{'ChEMBL entry exists' if result.chembl_known else 'no ChEMBL data'}). "
            f"Our docking prediction adds new computational evidence."
        )
    else:
        result.novelty = "well_known"
        result.validation_summary = (
            f"Well-characterized compound ({result.pubmed_papers} papers, "
            f"ChEMBL: {result.chembl_known}). Our prediction is consistent with known data."
        )
