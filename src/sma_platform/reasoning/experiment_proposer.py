"""
Hypothesis-to-Experiment Proposer
==================================
Automatically converts platform hypotheses into structured experimental
proposals with assays, model systems, readouts, and go/no-go criteria.

Takes a hypothesis ID, analyzes its type/content, and generates a concrete
experimental proposal that bridges computational prediction to wet lab.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hypothesis-type detection patterns
# ---------------------------------------------------------------------------

# Keywords that signal the hypothesis category (checked against title + description)
_BINDING_KEYWORDS = {
    "bind", "binding", "interact", "interaction", "co-ip", "complex",
    "docking", "affinity", "spr", "kd", "dissociation", "protein-protein",
    "dimerization", "heterocomplex", "association",
}
_EXPRESSION_KEYWORDS = {
    "expression", "upregulation", "downregulation", "transcription",
    "mrna", "transcript", "promoter", "enhancer", "rt-qpcr",
    "rna-seq", "fold-change", "gene expression",
}
_DRUG_KEYWORDS = {
    "efficacy", "drug", "compound", "therapeutic", "dose-response",
    "ec50", "ic50", "viability", "cytotoxicity", "treatment",
    "neuroprotection", "rescue", "cell death", "apoptosis",
}
_SPLICING_KEYWORDS = {
    "splicing", "exon", "intron", "splice", "inclusion", "skipping",
    "smn2", "iss-n1", "minigene", "spliceosome", "exon 7",
}
_SPECIFIC_TARGET_KEYWORDS = {
    "smn", "smn1", "smn2", "pls3", "ncald", "uba1", "stmn2",
    "coro1c", "tp53", "plastin", "neurocalcin",
}


def _classify_hypothesis(title: str, description: str, claim_type: str) -> str:
    """Classify hypothesis into experimental category based on content.

    Returns one of: binding, expression, drug_efficacy, splicing, general
    """
    text = f"{title} {description}".lower()

    # Check claim_type first (most reliable signal)
    type_map = {
        "protein_interaction": "binding",
        "gene_expression": "expression",
        "drug_efficacy": "drug_efficacy",
        "drug_target": "drug_efficacy",
        "splicing_event": "splicing",
        "neuroprotection": "drug_efficacy",
        "biomarker": "expression",
        "survival": "drug_efficacy",
        "motor_function": "drug_efficacy",
    }
    if claim_type in type_map:
        return type_map[claim_type]

    # Keyword scoring
    scores = {
        "binding": sum(1 for kw in _BINDING_KEYWORDS if kw in text),
        "expression": sum(1 for kw in _EXPRESSION_KEYWORDS if kw in text),
        "drug_efficacy": sum(1 for kw in _DRUG_KEYWORDS if kw in text),
        "splicing": sum(1 for kw in _SPLICING_KEYWORDS if kw in text),
    }

    best = max(scores, key=scores.get)
    if scores[best] >= 2:
        return best

    return "general"


# ---------------------------------------------------------------------------
# Assay recommendation templates by category
# ---------------------------------------------------------------------------

ASSAY_TEMPLATES: dict[str, dict[str, Any]] = {
    "binding": {
        "assay": "Surface Plasmon Resonance (SPR) or Isothermal Titration Calorimetry (ITC)",
        "rationale": (
            "SPR measures real-time binding kinetics (ka, kd, KD) with minimal protein. "
            "ITC provides thermodynamic parameters (deltaH, deltaS, stoichiometry). "
            "SPR is preferred for initial screening; ITC for mechanistic characterization."
        ),
        "model_systems": [
            {"name": "Recombinant purified proteins (SPR)", "tier": "primary", "cost_usd": 3000, "time_weeks": 3},
            {"name": "HEK293T co-IP validation", "tier": "secondary", "cost_usd": 2000, "time_weeks": 2},
            {"name": "iPSC-MN proximity ligation assay", "tier": "tertiary", "cost_usd": 8000, "time_weeks": 6},
        ],
        "primary_readout": "Equilibrium dissociation constant (KD) in nM range",
        "secondary_readouts": [
            "Association rate (ka)",
            "Dissociation rate (kd)",
            "Stoichiometry (ITC)",
            "Co-IP Western blot confirmation",
        ],
        "go_nogo": {
            "go": "KD < 500 nM with reproducible binding curve (n >= 3); confirmed by orthogonal method",
            "no_go": "No detectable binding (KD > 100 uM) or non-specific binding pattern",
            "borderline": "KD 500 nM - 10 uM — optimize constructs, try alternative binding partners",
        },
        "timeline_weeks": 4,
        "estimated_cost_usd": 5000,
        "required_reagents": [
            "Purified recombinant target protein (>90% purity, 1 mg)",
            "Purified interacting partner protein (>90% purity, 1 mg)",
            "SPR sensor chip (CM5 or NTA for His-tagged proteins)",
            "Running buffer optimized for target stability",
        ],
    },
    "expression": {
        "assay": "RT-qPCR + Western Blot (mRNA and protein quantification)",
        "rationale": (
            "RT-qPCR provides sensitive mRNA quantification with absolute copy numbers. "
            "Western blot confirms protein-level changes. Dual validation reduces false "
            "positives from post-transcriptional regulation."
        ),
        "model_systems": [
            {"name": "SMA patient fibroblasts (Type I/II/III)", "tier": "primary", "cost_usd": 1500, "time_weeks": 2},
            {"name": "iPSC-derived motor neurons", "tier": "secondary", "cost_usd": 8000, "time_weeks": 8},
            {"name": "SMA mouse spinal cord tissue", "tier": "tertiary", "cost_usd": 15000, "time_weeks": 12},
        ],
        "primary_readout": "mRNA fold-change vs healthy control (normalized to GAPDH/ACTB)",
        "secondary_readouts": [
            "Protein level by Western (densitometry, normalized to loading control)",
            "Cell-type specificity (if using mixed tissue)",
            "Dose-response if pharmacological perturbation",
        ],
        "go_nogo": {
            "go": ">= 1.5-fold change in expression (p < 0.05, n >= 3 biological replicates)",
            "no_go": "No significant change or < 1.2-fold (technical noise range)",
            "borderline": "1.2-1.5 fold — validate in motor neurons, consider single-cell resolution",
        },
        "timeline_weeks": 3,
        "estimated_cost_usd": 2500,
        "required_reagents": [
            "Validated qPCR primers (target gene + 2 housekeeping genes)",
            "Primary antibody against target protein (validated for Western)",
            "SMA patient fibroblast cell lines (Coriell repository)",
            "RNA extraction kit (TRIzol or column-based)",
            "cDNA synthesis kit + SYBR Green or TaqMan master mix",
        ],
    },
    "drug_efficacy": {
        "assay": "Cell viability dose-response assay (CellTiter-Glo or MTT)",
        "rationale": (
            "CellTiter-Glo measures ATP levels as proxy for viable cell number, with "
            "excellent sensitivity and dynamic range. Dose-response curves establish "
            "EC50/IC50 values for compound potency ranking."
        ),
        "model_systems": [
            {"name": "SMA patient fibroblasts (SMN-deficient)", "tier": "primary", "cost_usd": 2000, "time_weeks": 2},
            {"name": "iPSC-derived motor neurons (SMA Type I)", "tier": "secondary", "cost_usd": 12000, "time_weeks": 8},
            {"name": "SMN-delta7 mouse model", "tier": "tertiary", "cost_usd": 50000, "time_weeks": 16},
        ],
        "primary_readout": "EC50 for SMN protein rescue or cell viability improvement",
        "secondary_readouts": [
            "SMN protein level by ELISA or Western",
            "Motor neuron survival (HB9+/ChAT+ counting)",
            "Neurite length (automated imaging)",
            "Selectivity index (therapeutic window)",
        ],
        "go_nogo": {
            "go": "EC50 < 1 uM with >= 30% efficacy over vehicle; no cytotoxicity at 10x EC50",
            "no_go": "EC50 > 10 uM, or cytotoxicity at effective concentration, or < 10% efficacy",
            "borderline": "EC50 1-10 uM — medicinal chemistry optimization needed; test in motor neurons",
        },
        "timeline_weeks": 4,
        "estimated_cost_usd": 5000,
        "required_reagents": [
            "Test compound (>95% purity, 10 mg for dose-response)",
            "Positive control (nusinersen or risdiplam analog for benchmarking)",
            "CellTiter-Glo 2.0 reagent",
            "SMA patient cell lines (3 genotypes minimum)",
            "DMSO-tolerant culture media",
        ],
    },
    "splicing": {
        "assay": "RT-PCR with splice-specific primers + SMN2 minigene reporter",
        "rationale": (
            "RT-PCR with primers spanning the SMN2 exon 7 junction directly quantifies "
            "full-length vs delta7 isoforms. Minigene reporter assay enables high-throughput "
            "screening of splicing modifiers with luciferase readout."
        ),
        "model_systems": [
            {"name": "SMN2 minigene reporter in HEK293T", "tier": "primary", "cost_usd": 2000, "time_weeks": 2},
            {"name": "SMA patient fibroblasts (endogenous SMN2)", "tier": "secondary", "cost_usd": 2500, "time_weeks": 3},
            {"name": "iPSC-derived motor neurons", "tier": "tertiary", "cost_usd": 10000, "time_weeks": 8},
        ],
        "primary_readout": "Exon 7 inclusion ratio (FL-SMN / delta7-SMN by densitometry or qPCR)",
        "secondary_readouts": [
            "SMN protein level by Western blot",
            "Dose-response of splicing modifier (EC50)",
            "Off-target splicing events (RNA-seq panel of 50 critical exons)",
            "Gems per nucleus (nuclear SMN foci by immunofluorescence)",
        ],
        "go_nogo": {
            "go": ">= 2-fold increase in exon 7 inclusion ratio (p < 0.01); confirmed in patient cells",
            "no_go": "No change in splicing ratio, or < 1.2-fold increase, or off-target splicing hits",
            "borderline": "1.2-2.0 fold — optimize ASO/compound, check concentration dependence",
        },
        "timeline_weeks": 3,
        "estimated_cost_usd": 3000,
        "required_reagents": [
            "Splice-specific primer pairs (FL-SMN2 and delta7-SMN2)",
            "SMN2 minigene reporter plasmid (if using reporter assay)",
            "SMA patient fibroblasts (Coriell: GM03813, GM09677)",
            "RNA extraction + RT-PCR reagents",
            "Anti-SMN antibody (2B1 clone) for Western validation",
        ],
    },
    "general": {
        "assay": "Target-specific functional assay (phenotypic or biochemical)",
        "rationale": (
            "When the hypothesis mechanism is not clearly categorized, a target-specific "
            "functional assay is recommended. Start with the cheapest informative readout "
            "and escalate based on results."
        ),
        "model_systems": [
            {"name": "SMA patient fibroblasts", "tier": "primary", "cost_usd": 1500, "time_weeks": 2},
            {"name": "iPSC-derived motor neurons", "tier": "secondary", "cost_usd": 10000, "time_weeks": 8},
            {"name": "SMA mouse model (delta7 or Taiwanese)", "tier": "tertiary", "cost_usd": 50000, "time_weeks": 16},
        ],
        "primary_readout": "Target protein level or activity measurement",
        "secondary_readouts": [
            "Motor neuron viability",
            "SMN protein levels (downstream effect)",
            "Neurite morphology",
        ],
        "go_nogo": {
            "go": "Statistically significant effect in expected direction (p < 0.05, n >= 3)",
            "no_go": "No significant effect or effect in wrong direction",
            "borderline": "Trend in expected direction but not significant — increase N or use more sensitive assay",
        },
        "timeline_weeks": 4,
        "estimated_cost_usd": 5000,
        "required_reagents": [
            "Target-specific antibody (validated for Western/IF)",
            "SMA patient cell lines",
            "Appropriate positive and negative controls",
        ],
    },
}


# ---------------------------------------------------------------------------
# Target-specific reagent availability
# ---------------------------------------------------------------------------

TARGET_REAGENTS: dict[str, dict[str, Any]] = {
    "SMN1": {
        "antibodies": ["Anti-SMN (2B1, BD Biosciences)", "Anti-SMN (8F1, Bhatt lab)"],
        "cell_lines": ["GM03813 (SMA Type I fibroblasts)", "GM09677 (SMA Type II)"],
        "notes": "Well-characterized target, extensive reagent availability",
    },
    "SMN2": {
        "antibodies": ["Anti-SMN (2B1, does not distinguish SMN1/2 protein)", "Anti-exon 7 splice junction (custom)"],
        "cell_lines": ["GM03813 (3 copies SMN2)", "GM09677 (3 copies SMN2)"],
        "notes": "SMN2 minigene reporters available from multiple labs (Singh, Bhatt, Bhatt)",
    },
    "PLS3": {
        "antibodies": ["Anti-PLS3 (Sigma HPA029029)", "Anti-Plastin-3 (Proteintech 12942-1-AP)"],
        "cell_lines": ["SMA patient fibroblasts + PLS3 overexpression lentivirus"],
        "notes": "Genetic modifier — higher PLS3 correlates with milder phenotype in discordant siblings",
    },
    "NCALD": {
        "antibodies": ["Anti-NCALD (Atlas HPA015585)", "Anti-Neurocalcin delta (Abcam ab137109)"],
        "cell_lines": ["NCALD-knockdown iPSC-MN lines available (Wirth lab)"],
        "notes": "Protective modifier — NCALD reduction ameliorates SMA in model organisms",
    },
    "UBA1": {
        "antibodies": ["Anti-UBA1 (Cell Signaling #4891)", "Anti-UBE1 (Abcam ab181225)"],
        "cell_lines": ["SMA patient fibroblasts (UBA1 reduction observable)"],
        "notes": "Ubiquitin pathway disruption is a key non-SMN downstream effect in SMA",
    },
    "STMN2": {
        "antibodies": ["Anti-STMN2/SCG10 (Novus NBP1-49461)", "Anti-Stathmin-2 (Proteintech)"],
        "cell_lines": ["iPSC-MN (STMN2 is motor neuron enriched)"],
        "notes": "Axon maintenance factor — mis-spliced in TDP-43 proteinopathies, potential SMA overlap",
    },
    "CORO1C": {
        "antibodies": ["Anti-CORO1C (Proteintech 14749-1-AP)", "Anti-Coronin-1C (Sigma HPA041889)"],
        "cell_lines": ["NSC-34 motor neuron-like cells", "iPSC-MN"],
        "notes": "Actin dynamics regulator — 4-AP upregulates CORO1C with SMN correlation +0.251",
    },
    "TP53": {
        "antibodies": ["Anti-p53 (DO-1, Santa Cruz sc-126)", "Anti-p53 (Cell Signaling #2527)"],
        "cell_lines": ["SMA patient fibroblasts", "iPSC-MN"],
        "notes": "p53-mediated apoptosis pathway activated in SMA motor neurons — druggable target",
    },
}


# ---------------------------------------------------------------------------
# Literature references by category
# ---------------------------------------------------------------------------

RELEVANT_LITERATURE: dict[str, list[dict[str, str]]] = {
    "binding": [
        {"pmid": "19056867", "title": "SMN protein interactome in SMA", "relevance": "Maps SMN binding partners"},
        {"pmid": "21796585", "title": "Gemin complex assembly and SMN binding", "relevance": "SMN oligomerization and Gemin binding"},
    ],
    "expression": [
        {"pmid": "28007903", "title": "Transcriptomic changes in SMA motor neurons", "relevance": "Baseline expression data"},
        {"pmid": "29483295", "title": "Single-cell RNA-seq of spinal cord in SMA mice", "relevance": "Cell-type specific expression"},
    ],
    "drug_efficacy": [
        {"pmid": "28686856", "title": "Nusinersen Phase 3 ENDEAR trial", "relevance": "Gold standard efficacy benchmark"},
        {"pmid": "29091570", "title": "Risdiplam development and mechanism", "relevance": "Small molecule splicing modifier precedent"},
    ],
    "splicing": [
        {"pmid": "12524540", "title": "SMN2 exon 7 splicing regulation by ISS-N1", "relevance": "Core splicing mechanism"},
        {"pmid": "16648847", "title": "ASO-mediated SMN2 exon 7 inclusion", "relevance": "Antisense approach to splicing rescue"},
    ],
    "general": [
        {"pmid": "28686856", "title": "Nusinersen ENDEAR trial", "relevance": "Clinical efficacy benchmark"},
        {"pmid": "12524540", "title": "SMN2 splicing regulation", "relevance": "Core disease mechanism"},
    ],
}


# ---------------------------------------------------------------------------
# Core proposal generation
# ---------------------------------------------------------------------------

async def propose_experiment(hypothesis_id: str) -> dict[str, Any]:
    """Generate a concrete experimental proposal for a single hypothesis.

    Takes a hypothesis ID, analyzes its content and type, and returns a
    structured proposal with assay, model system, readouts, go/no-go
    criteria, timeline, reagents, and relevant literature.
    """
    # Fetch hypothesis
    hyp = await fetchrow(
        "SELECT * FROM hypotheses WHERE id = $1",
        hypothesis_id,
    )
    if not hyp:
        return {"error": f"Hypothesis '{hypothesis_id}' not found"}

    hyp = dict(hyp)
    title = hyp.get("title", "")
    description = hyp.get("description", "")
    confidence = float(hyp.get("confidence") or 0.5)

    # Parse metadata
    try:
        meta = json.loads(hyp.get("metadata") or "{}")
    except (json.JSONDecodeError, TypeError):
        meta = {}

    target_symbol = meta.get("target_symbol", "")
    target_id = meta.get("target_id", "")
    claim_type = meta.get("claim_type", "other")
    modality = meta.get("modality_suggestion", "unclear")

    # Fetch target info
    target_info = None
    if target_id:
        target_info = await fetchrow(
            "SELECT symbol, name, target_type, description FROM targets WHERE id = $1",
            target_id,
        )
        if target_info:
            target_info = dict(target_info)
            if not target_symbol:
                target_symbol = target_info.get("symbol", "")

    # Classify hypothesis type
    category = _classify_hypothesis(title, description, claim_type)

    # Get assay template
    template = ASSAY_TEMPLATES.get(category, ASSAY_TEMPLATES["general"])

    # Check for target-specific reagents
    reagent_info = TARGET_REAGENTS.get(target_symbol.upper(), None)
    reagents = list(template["required_reagents"])
    if reagent_info:
        reagents.append(f"Target-specific antibodies: {', '.join(reagent_info['antibodies'])}")
        reagents.append(f"Recommended cell lines: {', '.join(reagent_info['cell_lines'])}")

    # Get supporting claims for context
    supporting_claims = []
    try:
        claim_ids = json.loads(hyp.get("supporting_evidence") or "[]")
    except (json.JSONDecodeError, TypeError):
        claim_ids = []

    if claim_ids:
        claims = await fetch(
            "SELECT predicate, confidence, claim_type FROM claims WHERE id = ANY($1::uuid[]) LIMIT 5",
            claim_ids[:5],
        )
        if claims:
            supporting_claims = [
                {"predicate": dict(c)["predicate"], "confidence": float(dict(c).get("confidence") or 0.5)}
                for c in claims
            ]

    # If no claims from supporting_evidence, try target-linked claims
    if not supporting_claims and target_id:
        claims = await fetch(
            "SELECT predicate, confidence, claim_type FROM claims WHERE subject_id = $1 ORDER BY confidence DESC LIMIT 5",
            target_id,
        )
        if claims:
            supporting_claims = [
                {"predicate": dict(c)["predicate"], "confidence": float(dict(c).get("confidence") or 0.5)}
                for c in claims
            ]

    # Get relevant literature
    literature = RELEVANT_LITERATURE.get(category, RELEVANT_LITERATURE["general"])

    # Also check for platform sources mentioning this target
    platform_sources = []
    if target_symbol:
        sources = await fetch(
            """SELECT DISTINCT s.title, s.external_id as pmid, s.publication_date
               FROM sources s
               INNER JOIN evidence e ON e.source_id = s.id
               INNER JOIN claims c ON e.claim_id = c.id
               WHERE c.subject_id = $1
               ORDER BY s.publication_date DESC NULLS LAST
               LIMIT 5""",
            target_id,
        ) if target_id else []
        for s in sources:
            s = dict(s)
            platform_sources.append({
                "title": s.get("title", ""),
                "pmid": s.get("pmid", ""),
                "relevance": "Platform-indexed source for this target",
            })

    # Determine confidence-adjusted priority
    if confidence >= 0.7:
        priority = "high"
        priority_note = "High-confidence hypothesis — prioritize for immediate experimental validation"
    elif confidence >= 0.4:
        priority = "medium"
        priority_note = "Medium-confidence hypothesis — validate key assumptions before full experiment"
    else:
        priority = "low"
        priority_note = "Low-confidence hypothesis — consider pilot experiment or literature review first"

    return {
        "hypothesis_id": str(hyp["id"]),
        "hypothesis_title": title,
        "hypothesis_confidence": confidence,
        "hypothesis_status": hyp.get("status", "proposed"),
        "target_symbol": target_symbol,
        "target_info": {
            "name": target_info.get("name", "") if target_info else "",
            "type": target_info.get("target_type", "") if target_info else "",
            "description": target_info.get("description", "")[:200] if target_info else "",
        } if target_info else None,
        "experiment_category": category,
        "priority": priority,
        "priority_note": priority_note,
        "proposal": {
            "suggested_assay": template["assay"],
            "assay_rationale": template["rationale"],
            "model_systems": template["model_systems"],
            "primary_readout": template["primary_readout"],
            "secondary_readouts": template["secondary_readouts"],
            "go_nogo_criteria": template["go_nogo"],
            "estimated_timeline_weeks": template["timeline_weeks"],
            "estimated_cost_usd": template["estimated_cost_usd"],
            "required_reagents": reagents,
            "reagent_availability": {
                "antibodies_known": bool(reagent_info),
                "cell_lines_known": bool(reagent_info),
                "notes": reagent_info["notes"] if reagent_info else "Check vendor catalogs for target-specific reagents",
            },
        },
        "supporting_evidence": supporting_claims,
        "relevant_literature": literature + platform_sources,
        "modality_suggestion": modality,
        "escalation_path": _build_escalation_path(category, template["estimated_cost_usd"]),
    }


def _build_escalation_path(category: str, current_cost: int) -> list[dict[str, Any]]:
    """Build a step-by-step escalation path from initial experiment to in vivo."""
    steps = []

    if category == "splicing":
        steps = [
            {"step": 1, "assay": "Minigene reporter (HEK293T)", "cost_usd": 2000, "time_weeks": 2, "gate": "Exon 7 inclusion >= 2-fold"},
            {"step": 2, "assay": "Endogenous splicing (patient fibroblasts)", "cost_usd": 2500, "time_weeks": 3, "gate": "Confirmed in patient cells"},
            {"step": 3, "assay": "iPSC-MN splicing + survival", "cost_usd": 10000, "time_weeks": 8, "gate": "Motor neuron benefit"},
            {"step": 4, "assay": "SMA mouse model (delta7)", "cost_usd": 50000, "time_weeks": 16, "gate": "Survival extension >= 30%"},
        ]
    elif category == "binding":
        steps = [
            {"step": 1, "assay": "SPR binding kinetics", "cost_usd": 3000, "time_weeks": 3, "gate": "KD < 500 nM"},
            {"step": 2, "assay": "Co-IP in motor neurons", "cost_usd": 5000, "time_weeks": 4, "gate": "Confirmed cellular interaction"},
            {"step": 3, "assay": "Functional consequence assay", "cost_usd": 8000, "time_weeks": 6, "gate": "Phenotypic effect"},
            {"step": 4, "assay": "In vivo validation (mouse)", "cost_usd": 50000, "time_weeks": 16, "gate": "Motor function improvement"},
        ]
    elif category == "expression":
        steps = [
            {"step": 1, "assay": "RT-qPCR + Western (fibroblasts)", "cost_usd": 1500, "time_weeks": 2, "gate": "Expression change >= 1.5-fold"},
            {"step": 2, "assay": "iPSC-MN expression profiling", "cost_usd": 8000, "time_weeks": 8, "gate": "Confirmed in motor neurons"},
            {"step": 3, "assay": "Functional rescue assay", "cost_usd": 10000, "time_weeks": 8, "gate": "Survival or morphology improvement"},
            {"step": 4, "assay": "SMA mouse tissue analysis", "cost_usd": 25000, "time_weeks": 12, "gate": "In vivo expression correlation"},
        ]
    elif category == "drug_efficacy":
        steps = [
            {"step": 1, "assay": "Dose-response (fibroblasts)", "cost_usd": 2000, "time_weeks": 2, "gate": "EC50 < 1 uM"},
            {"step": 2, "assay": "iPSC-MN survival assay", "cost_usd": 12000, "time_weeks": 8, "gate": ">= 30% survival improvement"},
            {"step": 3, "assay": "ADMET profiling", "cost_usd": 15000, "time_weeks": 4, "gate": "Drug-like properties"},
            {"step": 4, "assay": "SMA mouse efficacy study", "cost_usd": 50000, "time_weeks": 16, "gate": "Survival + motor function"},
        ]
    else:
        steps = [
            {"step": 1, "assay": "Initial phenotypic screen", "cost_usd": 2000, "time_weeks": 3, "gate": "Detectable effect"},
            {"step": 2, "assay": "Motor neuron validation", "cost_usd": 10000, "time_weeks": 8, "gate": "Motor neuron relevance"},
            {"step": 3, "assay": "Mechanism characterization", "cost_usd": 10000, "time_weeks": 8, "gate": "Understood mechanism"},
            {"step": 4, "assay": "In vivo validation", "cost_usd": 50000, "time_weeks": 16, "gate": "Phenotypic rescue"},
        ]

    return steps


# ---------------------------------------------------------------------------
# Batch proposal generation
# ---------------------------------------------------------------------------

async def batch_propose(tier: str = "A") -> dict[str, Any]:
    """Generate experimental proposals for all hypotheses in a given tier.

    Uses the prioritization system's tier assignment. Tier A = top 5,
    Tier B = 6-15, Tier C = rest.

    Args:
        tier: "A", "B", "C", or "all"
    """
    # Get prioritized hypotheses with tier info
    # Import here to avoid circular imports
    from .hypothesis_prioritizer import prioritize_all_hypotheses

    prioritized = await prioritize_all_hypotheses()
    if not prioritized:
        return {"error": "No hypotheses found for prioritization", "proposals": []}

    # Select hypotheses by tier
    tier_key = f"tier_{tier.lower()}" if tier.lower() in ("a", "b", "c") else None

    if tier_key and tier_key in prioritized:
        hypothesis_list = prioritized[tier_key]
    elif tier.lower() == "all":
        hypothesis_list = (
            prioritized.get("tier_a", []) +
            prioritized.get("tier_b", []) +
            prioritized.get("tier_c", [])
        )
    else:
        return {"error": f"Invalid tier '{tier}'. Use A, B, C, or all", "proposals": []}

    proposals = []
    errors = 0
    for hyp in hypothesis_list:
        hyp_id = str(hyp.get("hypothesis_id", hyp.get("id", "")))
        if not hyp_id:
            errors += 1
            continue

        try:
            proposal = await propose_experiment(hyp_id)
            if "error" not in proposal:
                proposal["tier"] = tier.upper() if tier.lower() != "all" else hyp.get("tier", "C")
                proposal["prioritization_rank"] = hyp.get("rank", 0)
                proposal["composite_score"] = hyp.get("composite_score", 0)
                proposals.append(proposal)
            else:
                errors += 1
                logger.warning("Failed to propose for hypothesis %s: %s", hyp_id, proposal["error"])
        except Exception as e:
            errors += 1
            logger.error("Error proposing experiment for %s: %s", hyp_id, e, exc_info=True)

    # Sort by priority (high > medium > low), then by composite score
    priority_order = {"high": 0, "medium": 1, "low": 2}
    proposals.sort(key=lambda p: (priority_order.get(p["priority"], 3), -p.get("composite_score", 0)))

    # Summary stats
    total_cost = sum(p["proposal"]["estimated_cost_usd"] for p in proposals)
    total_weeks = max((p["proposal"]["estimated_timeline_weeks"] for p in proposals), default=0)
    categories = {}
    for p in proposals:
        cat = p["experiment_category"]
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "tier": tier.upper(),
        "total_proposals": len(proposals),
        "errors": errors,
        "summary": {
            "total_estimated_cost_usd": total_cost,
            "longest_timeline_weeks": total_weeks,
            "categories": categories,
            "high_priority_count": sum(1 for p in proposals if p["priority"] == "high"),
            "medium_priority_count": sum(1 for p in proposals if p["priority"] == "medium"),
            "low_priority_count": sum(1 for p in proposals if p["priority"] == "low"),
        },
        "proposals": proposals,
    }
