"""Extract structured claims from paper abstracts using LLM.

Each claim is a factual assertion that can be evaluated against evidence.
Claims link back to their source paper and relate to known targets.

Schema reference:
  claims: id, claim_type, subject_id, subject_type, predicate, object_id, object_type, value, confidence, metadata
  evidence: id, claim_id, source_id, excerpt, figure_ref, method, sample_size, p_value, effect_size, metadata
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone

import httpx

from ..core.config import settings
from ..core.database import execute, fetch, fetchrow
from ..core.llm_client import call_llm

logger = logging.getLogger(__name__)


def _alias_in_text(alias: str, text: str) -> bool:
    """Check alias with word boundaries to prevent substring false positives.

    IMPORTANT: `text` MUST already be uppercased before calling this function.
    The lookbehind/lookahead uses [A-Z0-9] which is correct for uppercased text.
    All call sites pass scan_text = "...".upper(), so this is always satisfied.
    """
    pattern = r'(?<![A-Z0-9])' + re.escape(alias) + r'(?![A-Z0-9])'
    return bool(re.search(pattern, text))


# Keywords that indicate SMA relevance in a paper abstract.
# Used as a post-extraction filter to reject claims from unrelated papers.
SMA_KEYWORDS = {
    "spinal muscular atrophy", "sma type", "sma i", "sma ii", "sma iii", "sma iv",
    "smn1", "smn2", "smn protein", "survival motor neuron",
    "motor neuron", "motor neurone", "motoneuron", "anterior horn",
    "neuromuscular", "neuromuscular junction", "nmj",
    "nusinersen", "spinraza", "risdiplam", "evrysdi",
    "onasemnogene", "zolgensma", "branaplam",
    "amyotrophy", "muscular atrophy",
    # Actin pathway targets (ROCK-LIMK2-CFL2 therapeutic axis)
    "cofilin", "limk", "lim kinase", "rock inhibitor", "rho kinase",
    "actin rod", "actin dynamics", "profilin", "pak1", "pak4",
    "fasudil", "ripasudil", "actin cytoskeleton",
    # Proprioceptive circuit
    "proprioceptive", "proprioception",
}

def _abstract_is_sma_relevant(abstract: str, title: str = "") -> bool:
    """Check if an abstract is relevant to SMA/neuromuscular disease.

    Returns True if any SMA keyword is found in the title or abstract.
    This filters out papers about unrelated diseases (cancer, diabetes,
    bear hibernation, etc.) that occasionally appear in search results.
    """
    text = f"{title} {abstract}".lower()
    return any(kw in text for kw in SMA_KEYWORDS)


VALID_CLAIM_TYPES = {
    "gene_expression", "protein_interaction", "pathway_membership",
    "drug_target", "drug_efficacy", "biomarker", "splicing_event",
    "neuroprotection", "motor_function", "survival", "safety", "other",
}

# Map LLM-generated types to valid DB claim types
TYPE_MAP = {
    "mechanism": "pathway_membership",
    "efficacy": "drug_efficacy",
    "epidemiology": "other",
    "methodology": "other",
    "drug_mechanism": "drug_target",
    "gene_regulation": "gene_expression",
    "splicing": "splicing_event",
    "neuroprotective": "neuroprotection",
    "motor": "motor_function",
}

# Known aliases for SMA-relevant targets.
# Keys are uppercased labels the LLM may produce; values are canonical DB symbols.
TARGET_ALIASES: dict[str, str] = {
    "SMN PROTEIN": "SMN_PROTEIN",
    "SURVIVAL MOTOR NEURON": "SMN1",
    "SURVIVAL MOTOR NEURON 1": "SMN1",
    "SURVIVAL MOTOR NEURON 2": "SMN2",
    "STATHMIN": "STMN2",
    "STATHMIN-2": "STMN2",
    "STATHMIN2": "STMN2",
    "PLASTIN": "PLS3",
    "PLASTIN-3": "PLS3",
    "PLASTIN 3": "PLS3",
    "T-PLASTIN": "PLS3",
    "NEUROCALCIN DELTA": "NCALD",
    "NEUROCALCIN": "NCALD",
    "UBE1": "UBA1",
    "CORONIN": "CORO1C",
    "CORONIN-1C": "CORO1C",
    "MTOR": "MTOR_PATHWAY",
    "MAMMALIAN TARGET OF RAPAMYCIN": "MTOR_PATHWAY",
    "MTOR PATHWAY": "MTOR_PATHWAY",
    "NMJ": "NMJ_MATURATION",
    "NEUROMUSCULAR JUNCTION": "NMJ_MATURATION",
    # Discovery targets (TargetDiscovery_A omics convergence)
    "CD44 ANTIGEN": "CD44",
    "HERMES": "CD44",
    "SULFATASE 1": "SULF1",
    "HSULF-1": "SULF1",
    "DNA METHYLTRANSFERASE 3B": "DNMT3B",
    "DNMT3BETA": "DNMT3B",
    "ANKYRIN-G": "ANK3",
    "ANKYRIN 3": "ANK3",
    "ANKYRIN-3": "ANK3",
    "MD-2": "LY96",
    "MD2": "LY96",
    "LYMPHOCYTE ANTIGEN 96": "LY96",
    "MIEAP": "SPATA18",
    "LDH-A": "LDHA",
    "LACTATE DEHYDROGENASE A": "LDHA",
    "CALPASTATIN": "CAST",
    "NEDD4-2": "NEDD4L",
    "NEDD4.2": "NEDD4L",
    "ALPHA-CATENIN": "CTNNA1",
    "ALPHA CATENIN": "CTNNA1",
    "CATENIN ALPHA-1": "CTNNA1",
    # Additional gene name aliases for improved linking
    "SMN": "SMN1",
    "SURVIVAL MOTOR NEURON PROTEIN": "SMN1",
    "GEMIN1": "SMN1",
    "FULL-LENGTH SMN": "SMN1",
    "FL-SMN": "SMN1",
    "DELTA7 SMN": "SMN2",
    "SMN-DELTA7": "SMN2",
    "SMNDELTA7": "SMN2",
    "SMNC": "SMN2",
    "CENTROMERIC SMN": "SMN2",
    "STASIMON": "TMEM41B",
    "TMEM41B": "TMEM41B",
    "HTRA2": "HTRA2",
    "OMI": "HTRA2",
    "ZPR1": "ZPR1",
    "SENATAXIN": "SETX",
    "FUS": "FUS",
    "FUSED IN SARCOMA": "FUS",
    "TDP-43": "TARDBP",
    "TDP43": "TARDBP",
    "TARDBP": "TARDBP",
    "P53": "TP53",
    "TP53": "TP53",
    "BCL-2": "BCL2",
    "BCL2": "BCL2",
    "BCLXL": "BCL2L1",
    "BCL-XL": "BCL2L1",
    "CASPASE-3": "CASP3",
    "CASPASE 3": "CASP3",
    "CASP3": "CASP3",
    "CASPASE-9": "CASP9",
    "CASPASE 9": "CASP9",
    "SNRNP": "SMN1",
    "SNRNP ASSEMBLY": "SMN1",
    "SPLICEOSOME": "SMN1",
    "SPLICEOSOMAL": "SMN1",
    # Pathway-level aliases — link pathway mentions to their key SMA-relevant gene
    "UBIQUITIN PROTEASOME": "UBA1",
    "UBIQUITIN-PROTEASOME SYSTEM": "UBA1",
    "UPS": "UBA1",
    "UBIQUITIN PROTEASOME PATHWAY": "UBA1",
    "UBIQUITIN LIGASE": "UBA1",
    "PI3K/AKT": "MTOR_PATHWAY",
    "PI3K-AKT": "MTOR_PATHWAY",
    "PI3K/AKT/MTOR": "MTOR_PATHWAY",
    "AKT PATHWAY": "MTOR_PATHWAY",
    "MAPK": "MAPK_PATHWAY",
    "ERK": "MAPK_PATHWAY",
    "ERK1/2": "MAPK_PATHWAY",
    "RAS-MAPK": "MAPK_PATHWAY",
    "RAS/MAPK": "MAPK_PATHWAY",
    "RHO GTPASE": "ROCK2",
    "ROCK": "ROCK2",
    "ROCK2": "ROCK2",
    "RHO/ROCK": "ROCK2",
    "RHO KINASE": "ROCK2",
    "RHO-ASSOCIATED KINASE": "ROCK2",
    "ACTIN DYNAMICS": "PLS3",
    "ACTIN CYTOSKELETON": "PLS3",
    "F-ACTIN": "PLS3",
    "ENDOCYTOSIS": "PLS3",
    "CALCIUM SIGNALING": "NCALD",
    "CALCIUM HOMEOSTASIS": "NCALD",
    "CALCIUM CHANNEL": "NCALD",
    "INTRACELLULAR CALCIUM": "NCALD",
    "ER STRESS": "HTRA2",
    "ENDOPLASMIC RETICULUM STRESS": "HTRA2",
    "UNFOLDED PROTEIN RESPONSE": "HTRA2",
    "UPR": "HTRA2",
    "JNK": "JNK_PATHWAY",
    "JNK PATHWAY": "JNK_PATHWAY",
    "C-JUN": "JNK_PATHWAY",
    "NOTCH": "NOTCH_PATHWAY",
    "NOTCH SIGNALING": "NOTCH_PATHWAY",
    "NOTCH PATHWAY": "NOTCH_PATHWAY",
    "WNT": "WNT_PATHWAY",
    "WNT SIGNALING": "WNT_PATHWAY",
    "WNT PATHWAY": "WNT_PATHWAY",
    "BETA-CATENIN": "WNT_PATHWAY",
    "MYOSTATIN": "MSTN",
    "GDF-8": "MSTN",
    "GDF8": "MSTN",
    "FOLLISTATIN": "FST",
    "ACTIVIN": "FST",
    "AGRIN": "AGRN",
    "MUSK": "MUSK",
    "LRPN4": "LRPN4",
    "RAPSYN": "RAPSN",
    "ACETYLCHOLINE RECEPTOR": "CHRNA1",
    "ACHR": "CHRNA1",
    "NICOTINIC RECEPTOR": "CHRNA1",
    "BDNF": "BDNF",
    "BRAIN-DERIVED NEUROTROPHIC FACTOR": "BDNF",
    "CNTF": "CNTF",
    "CILIARY NEUROTROPHIC FACTOR": "CNTF",
    "GDNF": "GDNF",
    "IGF-1": "IGF1",
    "IGF1": "IGF1",
    "INSULIN-LIKE GROWTH FACTOR": "IGF1",
    "HDAC INHIBITOR": "HDAC_PATHWAY",
    "HDAC": "HDAC_PATHWAY",
    "HISTONE DEACETYLASE": "HDAC_PATHWAY",
    "VALPROIC ACID": "HDAC_PATHWAY",
    "VPA": "HDAC_PATHWAY",
    "NEUROFILAMENT": "NEFL",
    "NEUROFILAMENT LIGHT": "NEFL",
    "NFL": "NEFL",
    "NFL LIGHT CHAIN": "NEFL",
    "PHOSPHORYLATED NEUROFILAMENT": "NEFH",
    "PNFH": "NEFH",
    # Actin pathway targets (sprint additions)
    "PROFILIN": "PFN1",
    "PROFILIN-1": "PFN1",
    "PROFILIN 1": "PFN1",
    "PROFILIN1": "PFN1",
    "PFN1": "PFN1",
    "COFILIN": "CFL2",
    "COFILIN-2": "CFL2",
    "COFILIN 2": "CFL2",
    "CFL2": "CFL2",
    "ACTIN ROD": "CFL2",
    "COFILIN ROD": "CFL2",
    # p53 pathway (Simon's work)
    # MDM2 and MDM4 are now separate targets in the DB (confirmed 2026-03-22).
    # They are regulators of TP53, NOT synonyms — map each to its own symbol.
    "MDM2": "MDM2",
    "MDM4": "MDM4",
    "MDMX": "MDM4",  # MDMX is the alias for MDM4 (same protein)
    "P38 MAPK": "MAPK_PATHWAY",
    "P38": "MAPK_PATHWAY",
    "MAPK14": "MAPK_PATHWAY",
    # Necroptosis
    "RIPK1": "RIPK1",
    "RIP KINASE": "RIPK1",
    "NECROPTOSIS": "RIPK1",
    "SARM1": "SARM1",
    "WALLERIAN DEGENERATION": "SARM1",
    # Complement pathway
    "C1Q": "C1Q",
}

# Drug names → their primary mechanism-of-action target.
# Used in relinking: if a claim is about a drug, link it to the target it acts on.
DRUG_TARGET_MAP: dict[str, str] = {
    "NUSINERSEN": "SMN2",
    "SPINRAZA": "SMN2",
    "RISDIPLAM": "SMN2",
    "EVRYSDI": "SMN2",
    "BRANAPLAM": "SMN2",
    "LMI070": "SMN2",
    "ONASEMNOGENE": "SMN1",
    "ONASEMNOGENE ABEPARVOVEC": "SMN1",
    "ZOLGENSMA": "SMN1",
    "AVXS-101": "SMN1",
    "VALPROIC ACID": "HDAC_PATHWAY",
    "VPA": "HDAC_PATHWAY",
    "SODIUM BUTYRATE": "HDAC_PATHWAY",
    "TRICHOSTATIN A": "HDAC_PATHWAY",
    "TSA": "HDAC_PATHWAY",
    "SUBEROYLANILIDE HYDROXAMIC ACID": "HDAC_PATHWAY",
    "SAHA": "HDAC_PATHWAY",
    "VORINOSTAT": "HDAC_PATHWAY",
    "CELECOXIB": "TP53",
    "RILUZOLE": "SMN2",
    "OLESOXIME": "SMN_PROTEIN",
    # 4-AP / dalfampridine: potassium channel blocker (Kv1.x/KCNA family).
    # No KCNA target in DB. Best available SMA-relevant proxy = ROCK2,
    # supported by DiffDock score (+0.64 vs ROCK2) and neuronal rescue data.
    # Do NOT map to CORO1C — 4-AP has no known CORO1C mechanism.
    "4-AMINOPYRIDINE": "ROCK2",
    "4-AP": "ROCK2",
    "DALFAMPRIDINE": "ROCK2",
    "RELDESEMTIV": "TNNT3",
    "CK-2127107": "TNNT3",
    "APITEGROMAB": "MSTN",
    "SRK-015": "MSTN",
    "FASUDIL": "ROCK2",
    "MW150": "MAPK_PATHWAY",
    "PANOBINOSTAT": "HDAC_PATHWAY",
    "PIFITHRIN": "TP53",
    "PIFITHRIN-ALPHA": "TP53",
}


async def _resolve_target_id(label: str) -> str | None:
    """Resolve a free-text target label to a target ID using multiple strategies.

    Strategies (tried in order):
    1. Exact symbol match in DB
    2. Alias map lookup → then exact symbol match
    3. Case-insensitive partial name match in DB
    """
    if not label or not label.strip():
        return None

    normalized = label.strip().upper()

    # Strategy 1: Exact symbol match
    row = await fetchrow("SELECT id FROM targets WHERE symbol = $1", normalized)
    if row:
        return dict(row)["id"]

    # Strategy 2: Alias map → symbol lookup
    alias_symbol = TARGET_ALIASES.get(normalized)
    if alias_symbol:
        row = await fetchrow("SELECT id FROM targets WHERE symbol = $1", alias_symbol)
        if row:
            return dict(row)["id"]

    # Strategy 3: Case-insensitive partial name match
    label_lower = label.strip().lower()
    row = await fetchrow(
        "SELECT id FROM targets WHERE LOWER(name) LIKE $1 LIMIT 1",
        f"%{label_lower}%",
    )
    if row:
        return dict(row)["id"]

    return None


EXTRACTION_PROMPT = """You are a biomedical research analyst specializing in Spinal Muscular Atrophy (SMA).

Given the following paper abstract, extract structured claims. Each claim should be:
- A single factual assertion that is DIRECTLY STATED in the abstract — never infer or extrapolate beyond what the authors wrote
- Relevant to SMA biology, treatment, or targets
- Specific enough to be verified or refuted

CRITICAL — Hedging and Evidence Strength:
- Preserve the authors' hedging language. If they say "may", "suggests", "is associated with", or "appears to", your predicate MUST use the same cautious phrasing.
- NEVER upgrade tentative findings to definitive statements. For example, do NOT convert "X may regulate Y" into "X regulates Y".
- Include the evidence context in the predicate. Append one of these qualifiers when applicable:
  * "(demonstrated in vitro)" for cell culture experiments
  * "(observed in mouse model)" for animal studies
  * "(clinical trial result)" for human trial data
  * "(computational prediction)" for bioinformatics-only findings
  * "(observed in patient cohort)" for observational human studies
- If a claim type is ambiguous, prefer the more specific type (e.g., "splicing_event" over "gene_expression" if splicing is mentioned).

SMA Relevance:
- Only extract claims that are directly relevant to SMA, motor neurons, SMN protein biology, or neuromuscular disease.
- If the abstract is NOT about SMA or neuromuscular disease, return an empty array [].

For each claim, provide:
- predicate: The factual assertion using the authors' exact hedging language, with evidence context qualifier (1-2 sentences)
- claim_type: One of [gene_expression, protein_interaction, pathway_membership, drug_target, drug_efficacy, biomarker, splicing_event, neuroprotection, motor_function, survival, safety, other]
- confidence: Your confidence the abstract supports this claim (0.0-1.0)
- subject: The primary entity (gene symbol, drug name, pathway, or "SMA")
- subject_type: One of [gene, drug, pathway, disease, cell_type]
- object: The secondary entity if applicable, or null
- object_type: Same options as subject_type, or null
- related_targets: List of gene/protein symbols mentioned (e.g., SMN1, SMN2, STMN2)
- excerpt: The key sentence from the abstract supporting this claim

Return ONLY a JSON array of claim objects. No markdown, no explanation.

Paper title: {title}
Journal: {journal}
Abstract: {abstract}"""


def _is_als_primary_paper(title: str, abstract: str) -> bool:
    """Return True if this paper is primarily about ALS, not SMA.

    ALS papers often mention "motor neuron", "riluzole", or "TDP-43" — terms
    that also appear in SMA research. This function detects ALS-primary papers
    so their claims can be rejected even when they share vocabulary with SMA.

    A paper is ALS-primary if:
      - It contains "amyotrophic lateral sclerosis" or "SOD1" (ALS model gene)
        AND does NOT contain "spinal muscular atrophy", "SMN", or "nusinersen".
    """
    text = f"{title} {abstract}".lower()
    als_markers = (
        "amyotrophic lateral sclerosis" in text
        or "sod1" in text  # SOD1 is the canonical ALS mouse model gene
    )
    sma_markers = (
        "spinal muscular atrophy" in text
        or " smn" in text
        or "nusinersen" in text
        or "risdiplam" in text
        or "zolgensma" in text
    )
    return als_markers and not sma_markers


def _claim_passes_quality_gate(claim: dict, title: str, abstract: str) -> bool:
    """Post-extraction quality gate: reject claims that are clearly not SMA-relevant.

    This catches garbage that slips through the pre-filter — e.g., a paper
    about "motor proteins in breast cancer" that mentions "motor" but isn't SMA.
    """
    predicate = claim.get("predicate", "").lower()
    excerpt = claim.get("excerpt", "").lower()
    text = f"{title.lower()} {predicate} {excerpt}"

    # Reject claims from ALS-primary papers.
    # These pass the SMA relevance gate via shared terms ("motor neuron",
    # "riluzole", "TDP-43") but are not SMA papers.
    if _is_als_primary_paper(title, abstract):
        return False

    # Reject claims about clearly non-SMA diseases
    non_sma_diseases = [
        "breast cancer", "prostate cancer", "colorectal", "melanoma",
        "leukemia", "lymphoma", "hepatocellular", "glioblastoma",
        "pancreatic cancer", "lung cancer", "ovarian cancer",
        "parkinson", "alzheimer", "huntington",
        "amyotrophic lateral sclerosis",
        "diabetes", "obesity", "atherosclerosis",
        "carcinoma", "glioma", "sarcoma", "myeloma", "mesothelioma",
        "renal cell", "bladder cancer", "cervical cancer",
        "this paper is not about", "not about spinal muscular",
    ]
    for disease in non_sma_diseases:
        if disease in text:
            # Allow if SMA is ALSO mentioned (cross-disease comparison)
            sma_check = f"{predicate} {excerpt} {abstract.lower()}"
            if any(kw in sma_check for kw in ("spinal muscular atrophy", "smn1", "smn2", "nusinersen")):
                continue
            return False

    # Reject extremely generic claims
    if len(predicate) < 20:
        return False

    # Confidence floor — LLM-assigned confidence below 0.4 is usually noise
    if claim.get("confidence", 0.5) < 0.4:
        return False

    return True


async def extract_claims_from_abstract(
    source_id: str,
    title: str,
    abstract: str,
    journal: str | None = None,
) -> list[dict]:
    """Extract claims from a single paper abstract using multi-LLM pipeline.

    Uses Groq/Gemini/OpenAI for bulk extraction (cheap/fast) with automatic
    fallback. Quality gates filter out non-SMA garbage before storage.
    """
    if not abstract or len(abstract.strip()) < 50:
        logger.info("Abstract too short for %s, skipping", source_id)
        return []

    # SMA relevance gate — reject papers about unrelated diseases
    if not _abstract_is_sma_relevant(abstract, title or ""):
        logger.info("Skipping non-SMA paper %s: %s", source_id, (title or "")[:80])
        return []

    prompt = EXTRACTION_PROMPT.format(
        title=title or "Unknown",
        journal=journal or "Unknown",
        abstract=abstract,
    )

    content, provider_used = await call_llm(prompt)
    if not content:
        return []

    try:
        # Strip markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()
        logger.debug("LLM response via %s (first 200 chars): %s", provider_used, content[:200])
        claims = json.loads(content)
        if not isinstance(claims, list):
            claims = [claims]

        # Post-extraction quality gate
        original_count = len(claims)
        claims = [c for c in claims if _claim_passes_quality_gate(c, title or "", abstract)]
        if original_count != len(claims):
            logger.info(
                "Quality gate filtered %d/%d claims for %s",
                original_count - len(claims), original_count, source_id,
            )

        # Tag each claim with extraction metadata
        for c in claims:
            c["_extraction_model"] = provider_used

        return claims
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error("Failed to parse claims from %s: %s | Raw: %s", provider_used, e, content[:300])
        return []


async def process_source(source_id: str) -> int:
    """Extract claims from a source and store them in the database."""
    source = await fetchrow("SELECT * FROM sources WHERE id = $1", source_id)
    if not source:
        logger.error("Source %s not found", source_id)
        return 0

    source = dict(source)
    claims = await extract_claims_from_abstract(
        source_id=source["id"],
        title=source.get("title", ""),
        abstract=source.get("abstract", ""),
        journal=source.get("journal"),
    )

    stored = 0
    for claim in claims:
        try:
            predicate = claim.get("predicate", "")
            if not predicate:
                continue

            # Map claim_type to valid DB values
            raw_type = claim.get("claim_type", "other").lower().strip()
            claim_type = TYPE_MAP.get(raw_type, raw_type)
            if claim_type not in VALID_CLAIM_TYPES:
                claim_type = "other"

            # Resolve subject to a target ID if possible
            subject = claim.get("subject", "SMA")
            subject_type = claim.get("subject_type", "disease")
            subject_id = await _resolve_target_id(subject)

            # If subject is a drug name, map to its MOA target
            if subject_id is None and subject:
                drug_target_sym = DRUG_TARGET_MAP.get(subject.strip().upper())
                if drug_target_sym:
                    subject_id = await _resolve_target_id(drug_target_sym)

            # If subject didn't resolve, try related_targets from the LLM
            if subject_id is None:
                for rt in claim.get("related_targets", []):
                    subject_id = await _resolve_target_id(rt)
                    if subject_id:
                        break

            # If still not resolved, scan predicate + excerpt text for known aliases
            if subject_id is None:
                scan_text = f"{predicate} {claim.get('excerpt', '')}".upper()
                # Check target aliases in scan text (longest first to avoid partial matches)
                for alias in sorted(TARGET_ALIASES.keys(), key=len, reverse=True):
                    if _alias_in_text(alias, scan_text):
                        subject_id = await _resolve_target_id(TARGET_ALIASES[alias])
                        if subject_id:
                            break
                # Check drug names in scan text
                if subject_id is None:
                    for drug_name, target_sym in DRUG_TARGET_MAP.items():
                        if _alias_in_text(drug_name, scan_text):
                            subject_id = await _resolve_target_id(target_sym)
                            if subject_id:
                                break

            # Resolve object to a target ID if possible
            obj = claim.get("object")
            object_type = claim.get("object_type")
            object_id = None
            if obj:
                object_id = await _resolve_target_id(obj)
                # If object is a drug, try drug→target mapping
                if object_id is None:
                    drug_target_sym = DRUG_TARGET_MAP.get(obj.strip().upper())
                    if drug_target_sym:
                        object_id = await _resolve_target_id(drug_target_sym)

            # Insert claim and retrieve its ID atomically via RETURNING
            claim_row = await fetchrow(
                """INSERT INTO claims (claim_type, subject_id, subject_type, predicate, object_id, object_type, confidence, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id""",
                claim_type,
                subject_id,
                subject_type,
                predicate,
                object_id,
                object_type,
                claim.get("confidence", 0.5),
                json.dumps({
                    "subject_label": subject,
                    "object_label": obj,
                    "related_targets": claim.get("related_targets", []),
                    "extraction_model": claim.get("_extraction_model", "unknown"),
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "source_paper_id": str(source["id"]),
                }),
            )
            if claim_row:
                claim_id = dict(claim_row)["id"]
                # Create evidence link back to source paper
                excerpt = claim.get("excerpt", predicate[:200])
                await execute(
                    """INSERT INTO evidence (claim_id, source_id, excerpt, method, metadata)
                       VALUES ($1, $2, $3, $4, $5)""",
                    claim_id,
                    source["id"],
                    excerpt,
                    "llm_abstract_extraction",
                    json.dumps({"confidence": claim.get("confidence", 0.5)}),
                )
                stored += 1

        except Exception as e:
            logger.error("Failed to store claim: %s", e)

    logger.info("Extracted %d claims from source %s (%s)", stored, source_id, source.get("title", "")[:60])
    return stored


async def relink_all_claims() -> dict:
    """Retroactively link existing unlinked claims to targets using fuzzy matching.

    Scans all claims where subject_id IS NULL and attempts to resolve them
    using the alias map, case-insensitive name matching, related_targets
    metadata, and predicate text scanning. Also resolves object_id where possible.
    """
    rows = await fetch(
        "SELECT id, predicate, metadata FROM claims WHERE subject_id IS NULL",
    )

    # Pre-load all target symbols for predicate scanning
    all_targets = await fetch("SELECT id, symbol, name FROM targets")
    target_lookup = {dict(t)["symbol"]: str(dict(t)["id"]) for t in all_targets}
    # Build reverse alias map: alias → target_id (sorted by length desc for longest-match-first)
    alias_to_id: dict[str, str] = {}
    for alias, symbol in TARGET_ALIASES.items():
        tid = target_lookup.get(symbol)
        if tid:
            alias_to_id[alias] = tid
    sorted_aliases = sorted(alias_to_id.keys(), key=len, reverse=True)

    # Pre-load evidence excerpts for each claim to use in text scanning
    evidence_rows = await fetch(
        "SELECT claim_id, excerpt FROM evidence WHERE claim_id IN (SELECT id FROM claims WHERE subject_id IS NULL)",
    )
    claim_excerpts: dict[str, str] = {}
    for erow in evidence_rows:
        erow = dict(erow)
        claim_excerpts[str(erow["claim_id"])] = erow.get("excerpt", "")

    claims_checked = 0
    claims_updated = 0
    targets_linked: dict[str, int] = {}

    for row in rows:
        row = dict(row)
        claims_checked += 1

        try:
            meta = json.loads(row.get("metadata") or "{}")
        except (json.JSONDecodeError, TypeError):
            meta = {}

        subject_label = meta.get("subject_label", "")
        related_targets = meta.get("related_targets", [])
        object_label = meta.get("object_label")
        predicate = row.get("predicate", "")

        # Try to resolve subject_id
        subject_id = None
        if subject_label:
            subject_id = await _resolve_target_id(subject_label)

        # If subject is a drug name, map to its MOA target
        if subject_id is None and subject_label:
            drug_target_sym = DRUG_TARGET_MAP.get(subject_label.strip().upper())
            if drug_target_sym:
                subject_id = target_lookup.get(drug_target_sym)

        # If subject didn't resolve, try each symbol in related_targets
        if subject_id is None and related_targets:
            for rt in related_targets:
                subject_id = await _resolve_target_id(rt)
                if subject_id:
                    break

        # If still not resolved, scan predicate + excerpt text for target symbols/aliases
        if subject_id is None:
            excerpt_text = claim_excerpts.get(str(row["id"]), "")
            scan_text = f"{predicate} {excerpt_text}".upper()
            if scan_text.strip():
                # Check exact target symbols in text
                for symbol, tid in target_lookup.items():
                    if _alias_in_text(symbol, scan_text):
                        subject_id = tid
                        break
                # Check aliases in text (longest first to avoid partial matches)
                if subject_id is None:
                    for alias in sorted_aliases:
                        if _alias_in_text(alias, scan_text):
                            subject_id = alias_to_id[alias]
                            break
                # Check drug names in text → MOA target
                if subject_id is None:
                    for drug_name, target_sym in DRUG_TARGET_MAP.items():
                        if _alias_in_text(drug_name, scan_text):
                            subject_id = target_lookup.get(target_sym)
                            if subject_id:
                                break

        # Try to resolve object_id
        object_id = None
        if object_label:
            object_id = await _resolve_target_id(object_label)

        # Update if we resolved at least one
        if subject_id or object_id:
            if subject_id and object_id:
                await execute(
                    "UPDATE claims SET subject_id = $1, object_id = $2 WHERE id = $3",
                    subject_id, object_id, row["id"],
                )
            elif subject_id:
                await execute(
                    "UPDATE claims SET subject_id = $1 WHERE id = $2",
                    subject_id, row["id"],
                )
            else:
                await execute(
                    "UPDATE claims SET object_id = $1 WHERE id = $2",
                    object_id, row["id"],
                )
            claims_updated += 1

            # Track which target symbols got linked (for reporting)
            if subject_id:
                # Look up the symbol for the resolved target
                t_row = await fetchrow("SELECT symbol FROM targets WHERE id = $1", subject_id)
                if t_row:
                    sym = dict(t_row)["symbol"]
                    targets_linked[sym] = targets_linked.get(sym, 0) + 1

    logger.info(
        "Relinked %d/%d claims (targets: %s)",
        claims_updated, claims_checked, targets_linked,
    )

    return {
        "claims_checked": claims_checked,
        "claims_updated": claims_updated,
        "targets_linked": targets_linked,
    }


async def process_all_unprocessed() -> dict:
    """Extract claims from all sources that haven't been processed yet."""
    # Find sources that have no evidence rows pointing to them
    rows = await fetch(
        """SELECT s.id FROM sources s
           LEFT JOIN evidence e ON e.source_id = s.id
           WHERE e.id IS NULL AND s.abstract IS NOT NULL AND length(s.abstract) > 50
           ORDER BY s.created_at DESC""",
    )

    total_claims = 0
    processed = 0
    errors = 0

    for i, row in enumerate(rows):
        row = dict(row)
        try:
            count = await process_source(row["id"])
            total_claims += count
            processed += 1
            # Rate-limit: pause between extractions to stay under Groq/Gemini limits
            # Groq free: 12K TPM → ~10 abstracts/min at ~1.2K tokens each
            if i > 0 and i % 8 == 0:
                logger.info("Processed %d/%d sources (%d claims), pausing for rate limit...", processed, len(rows), total_claims)
                await asyncio.sleep(15)
        except Exception as e:
            logger.error("Failed to process source %s: %s", row["id"], e)
            errors += 1

    return {
        "sources_processed": processed,
        "claims_extracted": total_claims,
        "errors": errors,
    }
