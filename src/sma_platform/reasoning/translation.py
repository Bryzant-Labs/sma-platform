"""Translation & Impact Module (Phase 11).

Tools for translating platform discoveries into real-world impact:
- Regulatory pathway mapping (FDA/EMA)
- Grant application support
- Hypothesis validation scoring
- Collaboration matching
- Drug repurposing report generation

References:
- FDA Rare Disease Guidance (2021)
- EMA PRIME designation requirements
- NIH NCATS Therapeutics for Rare and Neglected Diseases (TRND)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Regulatory pathways
# ---------------------------------------------------------------------------

@dataclass
class RegulatoryPathway:
    """A regulatory pathway for SMA therapeutics."""
    name: str
    agency: str                 # FDA, EMA, both
    designation: str
    requirements: list[str]
    timeline: str
    benefits: list[str]
    sma_relevance: str
    current_sma_drugs: list[str]  # drugs that used this pathway


REGULATORY_PATHWAYS = [
    RegulatoryPathway(
        name="Orphan Drug Designation",
        agency="both",
        designation="Orphan Drug",
        requirements=[
            "Disease affects <200,000 patients in US (SMA: ~25,000)",
            "Demonstrate plausibility of therapeutic effect",
            "No approved satisfactory therapy OR superiority over existing",
        ],
        timeline="90 days for designation decision",
        benefits=[
            "7 years market exclusivity (FDA) / 10 years (EMA)",
            "Tax credits for clinical development costs (25% FDA)",
            "Waived PDUFA filing fees (~$3M saved)",
            "Protocol assistance from FDA/EMA",
        ],
        sma_relevance="All 3 approved SMA drugs have orphan designation. Essential for any SMA therapeutic.",
        current_sma_drugs=["Nusinersen", "Risdiplam", "Onasemnogene"],
    ),
    RegulatoryPathway(
        name="Breakthrough Therapy Designation",
        agency="FDA",
        designation="Breakthrough Therapy",
        requirements=[
            "Intended for serious/life-threatening condition",
            "Preliminary clinical evidence of substantial improvement over existing therapies",
            "At least one clinically significant endpoint",
        ],
        timeline="60 days for designation decision",
        benefits=[
            "Intensive FDA guidance on efficient drug development",
            "Organizational commitment involving senior managers",
            "Rolling review of marketing application",
            "Earlier communication about manufacturing",
        ],
        sma_relevance="Nusinersen and onasemnogene both received breakthrough designation. "
                      "New SMA therapeutics with novel mechanisms (e.g., myostatin inhibition, "
                      "gene editing) could also qualify if they show superior outcomes.",
        current_sma_drugs=["Nusinersen", "Onasemnogene"],
    ),
    RegulatoryPathway(
        name="PRIME (Priority Medicines)",
        agency="EMA",
        designation="PRIME",
        requirements=[
            "Unmet medical need in serious condition",
            "Preliminary clinical evidence of major therapeutic advantage",
            "OR compelling non-clinical + early clinical data for conditional approval",
        ],
        timeline="Decision within timeframe of accelerated assessment",
        benefits=[
            "Early dialogue with EMA CHMP rapporteur",
            "Accelerated assessment (150 days vs 210 days)",
            "Support for pediatric investigation plan (PIP)",
            "Fee reductions for SMEs",
        ],
        sma_relevance="Risdiplam received PRIME. Relevant for EU-focused SMA therapeutics "
                      "and combination therapies.",
        current_sma_drugs=["Risdiplam"],
    ),
    RegulatoryPathway(
        name="Accelerated Approval (Subpart H)",
        agency="FDA",
        designation="Accelerated Approval",
        requirements=[
            "Serious condition with unmet need",
            "Surrogate endpoint reasonably likely to predict clinical benefit",
            "For SMA: SMN protein levels or motor function scores",
            "Post-marketing confirmatory trial required",
        ],
        timeline="Priority review: 6 months (vs 10 months standard)",
        benefits=[
            "Approval based on surrogate endpoint (faster than clinical outcome)",
            "Earlier patient access",
            "Can be combined with other designations",
        ],
        sma_relevance="SMN protein level is an accepted surrogate endpoint for SMA. New therapies "
                      "could use motor function scores (CHOP INTEND, HFMSE) as surrogates.",
        current_sma_drugs=["Nusinersen (used motor function as clinical endpoint)"],
    ),
    RegulatoryPathway(
        name="Pediatric Rare Disease Priority Review Voucher",
        agency="FDA",
        designation="PRV",
        requirements=[
            "Approved for prevention/treatment of a rare pediatric disease",
            "SMA qualifies as rare pediatric disease",
        ],
        timeline="Voucher awarded upon approval",
        benefits=[
            "Priority Review Voucher — transferable, sellable ($100M-350M value)",
            "Accelerates review of ANY future application (not just SMA)",
            "Major financial incentive for rare disease development",
        ],
        sma_relevance="Significant financial incentive. Nusinersen and onasemnogene both received PRVs.",
        current_sma_drugs=["Nusinersen", "Onasemnogene"],
    ),
    RegulatoryPathway(
        name="Regenerative Medicine Advanced Therapy (RMAT)",
        agency="FDA",
        designation="RMAT",
        requirements=[
            "Regenerative medicine therapy (cell therapy, gene therapy, tissue engineering)",
            "Intended for serious condition",
            "Preliminary clinical evidence of addressing unmet need",
        ],
        timeline="60 days for designation",
        benefits=[
            "All benefits of Breakthrough Therapy designation",
            "Eligibility for accelerated approval based on surrogate/intermediate endpoint",
            "Potential for conditional approval with post-market commitments",
        ],
        sma_relevance="Applicable to gene therapies (Zolgensma) and gene editing approaches "
                      "(CRISPR/prime editing for SMA). Any AAV or cell therapy for SMA should seek RMAT.",
        current_sma_drugs=["Onasemnogene"],
    ),
]


# ---------------------------------------------------------------------------
# Grant templates
# ---------------------------------------------------------------------------

@dataclass
class GrantTemplate:
    """A grant application template for SMA research."""
    name: str
    funder: str
    mechanism: str              # R01, R21, U01, etc.
    budget_range: str
    duration_years: int
    sma_fit: str
    key_sections: list[str]
    success_tips: list[str]


GRANT_TEMPLATES = [
    GrantTemplate(
        name="NIH R01 — SMA Therapeutic Target Validation",
        funder="NINDS (National Institute of Neurological Disorders and Stroke)",
        mechanism="R01",
        budget_range="$250K-$500K/year direct costs",
        duration_years=5,
        sma_fit="Validate novel targets identified by the platform (e.g., NCALD, PLS3, NEDD4L)",
        key_sections=[
            "Specific Aims (1 page): 3 aims — in vitro validation, in vivo testing, mechanism",
            "Significance: Unmet need despite 3 approved therapies, platform-identified targets",
            "Innovation: AI-driven target discovery, evidence graph methodology",
            "Approach: iPSC-MN assays → SMA mouse models → biomarker development",
            "Preliminary Data: Platform evidence scores, target expression data, initial screens",
        ],
        success_tips=[
            "Emphasize clinical translational path — NINDS loves bench-to-bedside",
            "Include preliminary iPSC-MN data if possible",
            "Reference the platform's open data (cite HuggingFace dataset)",
            "Show why this target is different from SMN-focused approaches",
        ],
    ),
    GrantTemplate(
        name="NIH R21 — Exploratory SMA Bioelectric Therapy",
        funder="NINDS",
        mechanism="R21 (Exploratory/Developmental)",
        budget_range="$275K total (2 years)",
        duration_years=2,
        sma_fit="Test the bioelectric reprogramming hypothesis from Phase 7.5",
        key_sections=[
            "Specific Aims (1 page): 2 aims — ion channel profiling, spinal stimulation in SMA mice",
            "Significance: 40% of SMA MNs may be electrically dormant and rescuable",
            "Innovation: First application of bioelectric framework to SMA",
            "Approach: Patch clamp on iPSC-MNs → transcutaneous stimulation in SMA mice",
        ],
        success_tips=[
            "R21 is for HIGH RISK, HIGH REWARD — emphasize novelty",
            "Reference Michael Levin's bioelectricity work + Gill Nature Med 2024 (SCS)",
            "Keep scope focused — 2 years, proof of concept only",
            "Show digital twin predictions as preliminary data",
        ],
    ),
    GrantTemplate(
        name="CureSMA Basic Research Grant",
        funder="Cure SMA Foundation",
        mechanism="Basic Research Grant",
        budget_range="$100K-$200K/year",
        duration_years=2,
        sma_fit="Any novel SMA biology or therapeutic approach",
        key_sections=[
            "Lay Summary: Write for non-scientists (parent-friendly language)",
            "Scientific Abstract: 300 words max",
            "Research Plan: 5 pages, focus on SMA relevance",
            "Timeline and Milestones: Quarterly deliverables",
        ],
        success_tips=[
            "Cure SMA funds what NIH won't — be creative",
            "Patient impact statement is CRUCIAL — explain how this helps families",
            "They love combination approaches (SMN + other target)",
            "Reference platform data as evidence base",
        ],
    ),
    GrantTemplate(
        name="ERC Starting Grant — Computational SMA",
        funder="European Research Council",
        mechanism="StG (Starting Grant)",
        budget_range="Up to 1.5M EUR over 5 years",
        duration_years=5,
        sma_fit="Computational approaches to SMA drug discovery",
        key_sections=[
            "B1 Extended Synopsis (5 pages): Ground-breaking nature, methodology, resources",
            "B2 Scientific Proposal (15 pages): State-of-art, objectives, methodology, timeline",
            "CV and track record",
        ],
        success_tips=[
            "ERC values PI independence and ambition — think BIG",
            "The digital twin / AI-driven discovery angle is perfect for ERC",
            "Emphasize open-source, reproducibility, data sharing",
            "Include federated learning as cross-institutional collaboration",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Hypothesis validation framework
# ---------------------------------------------------------------------------

@dataclass
class ValidationLevel:
    """A level in the hypothesis validation pipeline."""
    level: int
    name: str
    description: str
    assays: list[str]
    evidence_required: str
    timeline: str
    cost_estimate: str
    go_no_go: str


VALIDATION_PIPELINE = [
    ValidationLevel(
        level=1,
        name="Computational Validation",
        description="In silico evidence from the platform — target scores, evidence convergence, "
                   "digital twin simulation, docking scores.",
        assays=["Evidence graph score", "Digital twin simulation", "Docking prediction", "RNA-binding prediction"],
        evidence_required="Composite evidence score >= 40%, positive digital twin prediction",
        timeline="1 day (automated)",
        cost_estimate="$0 (platform built-in)",
        go_no_go="Score >= 40% AND digital twin functional improvement > 5% → proceed",
    ),
    ValidationLevel(
        level=2,
        name="Biochemical Validation",
        description="Cell-free assays confirming molecular interaction — RNA binding, "
                   "enzyme activity, protein-protein interaction.",
        assays=["RNA-Binding Fluorescence Polarization", "SMN Protein ELISA", "Thermal shift assay"],
        evidence_required="Measurable binding/activity at < 10 uM concentration",
        timeline="1-2 weeks",
        cost_estimate="$1,000-5,000",
        go_no_go="KD or EC50 < 10 uM → proceed to cell-based",
    ),
    ValidationLevel(
        level=3,
        name="Cell-Based Validation",
        description="Functional effects in SMA patient-derived cells — splicing, protein levels, "
                   "motor neuron survival, NMJ formation.",
        assays=["SMN2 Splicing Reporter", "Motor Neuron Survival (iPSC-MN)", "NMJ Formation Assay"],
        evidence_required="Significant effect vs vehicle with dose-response",
        timeline="2-4 weeks",
        cost_estimate="$5,000-25,000",
        go_no_go="EC50 < 1 uM AND >2-fold SMN increase AND no cytotoxicity → proceed",
    ),
    ValidationLevel(
        level=4,
        name="Animal Model Validation",
        description="In vivo efficacy in SMA mouse model — survival extension, motor function, "
                   "motor neuron count, NMJ preservation.",
        assays=["SMA Mouse Survival Study (delta7)", "Motor neuron count", "NMJ analysis"],
        evidence_required="Significant survival extension AND motor function improvement vs vehicle",
        timeline="2-3 months",
        cost_estimate="$50,000-200,000",
        go_no_go="p<0.05 survival extension AND >20% motor function improvement → IND-enabling",
    ),
    ValidationLevel(
        level=5,
        name="Clinical Translation",
        description="IND-enabling studies, first-in-human planning, regulatory strategy.",
        assays=["GLP toxicology", "PK/PD", "Manufacturing scale-up", "IND filing"],
        evidence_required="Clean safety profile, predictable PK, scalable manufacturing",
        timeline="12-18 months",
        cost_estimate="$1M-5M",
        go_no_go="IND approved by FDA → Phase 1 clinical trial",
    ),
]


# ---------------------------------------------------------------------------
# API functions
# ---------------------------------------------------------------------------

def get_regulatory_pathways() -> dict[str, Any]:
    """Return regulatory pathway map for SMA therapeutics."""
    return {
        "total_pathways": len(REGULATORY_PATHWAYS),
        "pathways": [asdict(p) for p in REGULATORY_PATHWAYS],
        "recommended_combination": [
            "Orphan Drug Designation (always)",
            "Breakthrough Therapy (if clinical evidence of superiority)",
            "RMAT (for gene/cell therapies)",
            "Pediatric Rare Disease PRV (upon approval — $100M+ value)",
        ],
        "insight": "All SMA therapeutics should pursue Orphan Drug Designation (guaranteed for SMA) + "
                   "Breakthrough Therapy (if preliminary clinical data exists). Gene therapies should "
                   "add RMAT. The Pediatric Rare Disease PRV alone can fund further development.",
    }


def _budget_key(g: GrantTemplate) -> float:
    """Extract approximate max budget for sorting."""
    try:
        # Budget format: "$250K-$500K/year direct costs" or "Up to 1.5M EUR over 5 years"
        raw = g.budget_range.replace('€', '').replace('$', '').replace(',', '')
        parts = raw.split('-')
        last = parts[-1].strip().split('/')[0].split()[0]
        if 'M' in last:
            return float(last.replace('M', '')) * 1000
        elif 'K' in last:
            return float(last.replace('K', ''))
        return float(last)
    except (ValueError, IndexError):
        return 0


def get_grant_templates() -> dict[str, Any]:
    """Return grant application templates for SMA research."""
    return {
        "total_templates": len(GRANT_TEMPLATES),
        "templates": [asdict(g) for g in GRANT_TEMPLATES],
        "quickest_funding": asdict(min(GRANT_TEMPLATES, key=lambda x: x.duration_years)),
        "largest_budget": asdict(max(GRANT_TEMPLATES, key=_budget_key)),
        "insight": "Start with Cure SMA Basic Research Grant (fastest, most flexible) to generate "
                   "preliminary data, then apply for NIH R01 (larger budget, longer term). "
                   "European researchers should consider ERC Starting Grant for computational approaches.",
    }


def get_validation_pipeline() -> dict[str, Any]:
    """Return the 5-level hypothesis validation pipeline."""
    return {
        "total_levels": len(VALIDATION_PIPELINE),
        "levels": [asdict(v) for v in VALIDATION_PIPELINE],
        "total_timeline": "~18-24 months from computational validation to IND",
        "total_cost": "$1.1M-5.2M estimated from Level 1 to IND",
        "platform_contribution": "Level 1 (computational validation) is fully automated by the platform. "
                                 "This eliminates months of manual literature review and target prioritization.",
        "insight": "The platform provides Level 1 validation for free — every hypothesis, target, "
                   "and compound is automatically scored. This compresses the traditional 1-2 year "
                   "target identification phase to days. The real cost starts at Level 2 (wet lab).",
    }


def validate_hypothesis(hypothesis_id: str, evidence_score: float,
                        twin_improvement: float) -> dict[str, Any]:
    """Run a hypothesis through the validation pipeline gate check."""
    level_1_pass = evidence_score >= 0.40 and twin_improvement >= 0.05

    return {
        "hypothesis_id": hypothesis_id,
        "evidence_score": evidence_score,
        "twin_improvement": twin_improvement,
        "level_1_pass": level_1_pass,
        "current_level": 1 if level_1_pass else 0,
        "next_step": (
            "Proceed to Level 2: Biochemical Validation — run RNA-binding assay or SMN ELISA"
            if level_1_pass else
            "Does not pass Level 1 gate. Review evidence base and digital twin parameters."
        ),
        "recommended_assays": (
            ["RNA-Binding Fluorescence Polarization", "SMN Protein ELISA"]
            if level_1_pass else []
        ),
        "estimated_cost_to_next_gate": "$1,000-5,000" if level_1_pass else "$0",
    }


# ---------------------------------------------------------------------------
# Grant-Ready Hypothesis Export
# ---------------------------------------------------------------------------

# Supported grant formats and their section requirements
GRANT_FORMATS: dict[str, dict[str, Any]] = {
    "NIH_R01": {
        "funder": "NINDS (National Institute of Neurological Disorders and Stroke)",
        "mechanism": "R01",
        "budget_range": "$250K-$500K/year direct costs",
        "duration_years": 5,
        "sections": [
            "specific_aim", "significance", "innovation",
            "approach", "timeline", "budget_estimate",
        ],
    },
    "NIH_R21": {
        "funder": "NINDS",
        "mechanism": "R21 (Exploratory/Developmental)",
        "budget_range": "$275K total (2 years)",
        "duration_years": 2,
        "sections": [
            "specific_aim", "significance", "innovation",
            "approach", "timeline", "budget_estimate",
        ],
    },
    "ERC_StG": {
        "funder": "European Research Council",
        "mechanism": "Starting Grant",
        "budget_range": "Up to 1.5M EUR over 5 years",
        "duration_years": 5,
        "sections": [
            "specific_aim", "significance", "innovation",
            "approach", "timeline", "budget_estimate",
        ],
    },
    "CURE_SMA": {
        "funder": "Cure SMA Foundation",
        "mechanism": "Basic Research Grant",
        "budget_range": "$100K-$200K/year",
        "duration_years": 2,
        "sections": [
            "specific_aim", "significance", "innovation",
            "approach", "timeline", "budget_estimate",
        ],
    },
}


def _build_specific_aim(
    symbol: str,
    target_name: str,
    target_desc: str,
    convergence: dict | None,
    hypotheses: list[dict],
    screening_hits: list[dict],
    grant_format: str,
) -> str:
    """Compose a Specific Aims section from platform data."""
    # Determine the primary therapeutic angle
    has_hits = len(screening_hits) > 0
    hit_count = len(screening_hits)

    mechanism = target_desc if target_desc else f"{symbol}-mediated pathways"
    if len(mechanism) > 120:
        mechanism = mechanism[:117] + "..."

    aim_text = (
        f"To determine whether {symbol}-targeted interventions can restore "
        f"motor neuron function in SMA through modulation of {mechanism}."
    )

    aims = [aim_text]

    # Aim 1: always in vitro validation
    aim1 = (
        f"Aim 1: Validate {symbol} as a therapeutic target in iPSC-derived "
        f"SMA motor neurons using SMN protein quantification and motor neuron "
        f"survival assays."
    )
    aims.append(aim1)

    # Aim 2: depends on screening hits
    if has_hits:
        aim2 = (
            f"Aim 2: Evaluate {hit_count} computationally identified "
            f"{symbol}-binding compound(s) for dose-dependent efficacy "
            f"and selectivity in cell-based assays."
        )
    else:
        aim2 = (
            f"Aim 2: Perform structure-guided virtual screening against "
            f"{symbol} to identify candidate small molecules, followed by "
            f"biochemical validation of top hits."
        )
    aims.append(aim2)

    # Aim 3: in vivo for R01/ERC (longer grants)
    if grant_format in ("NIH_R01", "ERC_StG"):
        aim3 = (
            f"Aim 3: Assess lead {symbol}-targeting compound(s) in the "
            f"SMN-delta7 SMA mouse model for survival extension, motor "
            f"function improvement, and motor neuron preservation."
        )
        aims.append(aim3)

    return "\n".join(aims)


def _build_significance(
    symbol: str,
    target_name: str,
    convergence: dict | None,
    claims: list[dict],
    hypotheses: list[dict],
) -> str:
    """Compose a Significance section using convergence data."""
    parts = []

    # Opening: SMA unmet need
    parts.append(
        "Spinal Muscular Atrophy (SMA) affects approximately 1 in 10,000 live births "
        "and remains a leading genetic cause of infant mortality. While three FDA-approved "
        "therapies (nusinersen, risdiplam, onasemnogene abeparvovec) target SMN restoration, "
        "significant unmet needs persist: incomplete motor recovery in treated patients, "
        "declining efficacy with later treatment initiation, and multi-organ manifestations "
        "that SMN-focused therapies do not address."
    )

    # Target-specific significance from convergence data
    if convergence:
        score = convergence.get("composite_score", 0)
        claim_count = convergence.get("claim_count", 0)
        source_count = convergence.get("source_count", 0)
        confidence = convergence.get("confidence_level", "unknown")

        parts.append(
            f"{symbol} ({target_name}) has emerged as a compelling SMN-independent "
            f"therapeutic target through systematic evidence synthesis: {claim_count} "
            f"claims from {source_count} independent sources yield a convergence score "
            f"of {score:.0%} (confidence: {confidence}). This multi-lab, multi-method "
            f"evidence base substantially reduces the risk of target validation failure."
        )

        # Dimension breakdown
        dims = []
        if convergence.get("lab_independence", 0) > 0.5:
            dims.append(
                f"high lab independence ({convergence['lab_independence']:.0%})"
            )
        if convergence.get("method_diversity", 0) > 0.5:
            dims.append(
                f"diverse experimental methods ({convergence['method_diversity']:.0%})"
            )
        if convergence.get("replication", 0) > 0.5:
            dims.append(
                f"strong replication ({convergence['replication']:.0%})"
            )
        if dims:
            parts.append(
                f"The evidence for {symbol} is characterized by {', '.join(dims)}, "
                f"indicating robust and reproducible findings across the field."
            )
    else:
        parts.append(
            f"{symbol} ({target_name}) represents an emerging target in SMA research "
            f"identified through computational evidence synthesis. Further convergence "
            f"analysis is ongoing to quantify the strength of the evidence base."
        )

    # Key claims as supporting evidence
    if claims:
        top_claims = claims[:3]
        claim_lines = []
        for c in top_claims:
            pmid = c.get("pmid", "")
            pmid_ref = f" (PMID:{pmid})" if pmid else ""
            text = c.get("text", "")
            if len(text) > 150:
                text = text[:147] + "..."
            claim_lines.append(f"  - {text}{pmid_ref}")
        parts.append(
            f"Key findings supporting {symbol} as a therapeutic target include:\n"
            + "\n".join(claim_lines)
        )

    return "\n\n".join(parts)


def _build_innovation(
    symbol: str,
    screening_hits: list[dict],
    convergence: dict | None,
    grant_format: str,
) -> str:
    """Compose the Innovation section."""
    parts = []

    parts.append(
        f"This proposal leverages AI-driven drug discovery to identify and validate "
        f"{symbol}-targeting compounds for SMA, representing a paradigm shift from "
        f"traditional single-study target nomination to systematic evidence convergence."
    )

    parts.append(
        "Innovation 1 (Computational): The SMA Research Platform integrates >25,000 "
        "evidence claims from thousands of publications, applying Bayesian convergence "
        "scoring across five dimensions (claim volume, lab independence, method diversity, "
        "temporal trend, replication) to prioritize targets with the highest probability "
        "of therapeutic success."
    )

    if screening_hits:
        parts.append(
            f"Innovation 2 (Drug Discovery): Virtual screening using DiffDock and "
            f"molecular docking has identified {len(screening_hits)} positive binding "
            f"hit(s) against {symbol}, providing immediate chemical starting points "
            f"for medicinal chemistry optimization — compressing the traditional hit "
            f"identification phase from years to weeks."
        )
    else:
        parts.append(
            f"Innovation 2 (Drug Discovery): Structure-guided virtual screening "
            f"using DiffDock molecular docking will be applied to {symbol} to rapidly "
            f"identify candidate compounds, compressing the traditional hit identification "
            f"phase from years to weeks."
        )

    parts.append(
        "Innovation 3 (Integration): By combining computational target validation, "
        "automated virtual screening, and AI-generated experiment design, this approach "
        "creates a reproducible, data-driven pipeline that can be applied to any emerging "
        "SMA target — establishing a new standard for rare disease drug discovery."
    )

    if grant_format == "ERC_StG":
        parts.append(
            "Innovation 4 (Open Science): All platform data, models, and screening results "
            "are available as open-source resources, enabling federated collaboration "
            "across institutions and accelerating the global SMA research effort."
        )

    return "\n\n".join(parts)


def _build_approach(
    symbol: str,
    screening_hits: list[dict],
    assay_suggestion: dict | None,
    experiment_suggestions: list[dict],
    grant_format: str,
) -> str:
    """Compose the Approach / Research Plan section."""
    parts = []
    has_hits = len(screening_hits) > 0

    # Aim 1: In vitro validation
    parts.append(
        f"AIM 1: In Vitro Target Validation\n"
        f"Rationale: Confirm that modulation of {symbol} produces measurable "
        f"effects on SMA-relevant phenotypes in patient-derived cells.\n"
        f"Design: iPSC-derived motor neurons from SMA Type I patients (SMA1-MNs) "
        f"will serve as the primary model system. We will measure: (a) SMN protein "
        f"levels by quantitative Western blot and ELISA, (b) motor neuron survival "
        f"at 14 and 28 days in vitro, (c) neurite outgrowth and NMJ formation "
        f"in motor neuron-muscle co-cultures."
    )

    # Add experiment suggestions if available
    if experiment_suggestions:
        top_exps = experiment_suggestions[:3]
        exp_lines = []
        for exp in top_exps:
            assay = exp.get("recommended_assay", "")
            gap = exp.get("missing_evidence_type", "")
            cost = exp.get("estimated_cost", "")
            exp_lines.append(f"  - {assay} (fills {gap} evidence gap; est. {cost})")
        if exp_lines:
            parts.append(
                f"Platform-identified evidence gaps for {symbol} and recommended "
                f"experiments:\n" + "\n".join(exp_lines)
            )

    # Aim 2: Compound validation / screening
    if has_hits:
        top_hit = screening_hits[0]
        confidence = top_hit.get("docking_confidence", 0)
        parts.append(
            f"AIM 2: Lead Compound Characterization\n"
            f"Rationale: {len(screening_hits)} compound(s) with predicted binding "
            f"to {symbol} (top hit confidence: {confidence:.2f}) will be advanced "
            f"through dose-response profiling.\n"
            f"Design: (a) Dose-response in SMA1-MNs (8-point, 0.01-30 uM), "
            f"(b) selectivity profiling against related targets, "
            f"(c) preliminary ADMET assessment, (d) synergy testing with "
            f"nusinersen or risdiplam in combination experiments."
        )
    else:
        parts.append(
            f"AIM 2: Virtual Screening and Hit Identification\n"
            f"Rationale: No existing small-molecule hits are available for {symbol}, "
            f"necessitating de novo virtual screening.\n"
            f"Design: (a) Obtain or model {symbol} 3D structure (AlphaFold2/OpenFold), "
            f"(b) DiffDock virtual screening of 10M+ compound library, "
            f"(c) top 100 hits → dose-response validation in SMA1-MNs, "
            f"(d) lead optimization by medicinal chemistry."
        )

    # Assay-specific details from assay_ready module
    if assay_suggestion:
        assay_name = assay_suggestion.get("assay_type", "")
        go_criteria = assay_suggestion.get("go_criteria", "")
        nogo_criteria = assay_suggestion.get("nogo_criteria", "")
        if go_criteria:
            parts.append(
                f"Go/No-Go Criteria ({assay_name}):\n"
                f"  GO: {go_criteria}\n"
                f"  NO-GO: {nogo_criteria}"
            )

    # Aim 3: In vivo (for longer grants only)
    if grant_format in ("NIH_R01", "ERC_StG"):
        parts.append(
            f"AIM 3: In Vivo Efficacy in SMA Mouse Model\n"
            f"Rationale: Translate in vitro efficacy to the gold-standard SMA "
            f"mouse model (SMN2+/+; SMN-delta7+/+; Smn-/-).\n"
            f"Design: (a) Lead compound delivered IP or IT from P1, "
            f"(b) primary endpoint: median survival extension (>30% vs vehicle), "
            f"(c) secondary endpoints: righting reflex time, grip strength, "
            f"motor neuron counts (L1-L5), NMJ innervation (TVA muscle)."
        )

    return "\n\n".join(parts)


def _build_timeline(
    symbol: str,
    screening_hits: list[dict],
    grant_format: str,
) -> str:
    """Compose the timeline section."""
    fmt = GRANT_FORMATS.get(grant_format, GRANT_FORMATS["NIH_R01"])
    duration = fmt["duration_years"]
    has_hits = len(screening_hits) > 0

    if duration <= 2:
        # Short grants (R21, Cure SMA)
        if has_hits:
            return (
                f"Year 1 (Months 1-12): In vitro validation — iPSC-MN assays, "
                f"dose-response of {len(screening_hits)} hit(s), selectivity profiling.\n"
                f"Year 2 (Months 13-24): Combination testing with approved therapies, "
                f"preliminary ADMET, manuscript preparation, and R01 application."
            )
        else:
            return (
                f"Year 1 (Months 1-12): Virtual screening against {symbol}, "
                f"biochemical validation of top 20 hits, iPSC-MN dose-response.\n"
                f"Year 2 (Months 13-24): Lead optimization, selectivity profiling, "
                f"combination testing, manuscript preparation, and R01 application."
            )
    else:
        # Long grants (R01, ERC)
        if has_hits:
            return (
                f"Year 1: In vitro validation — iPSC-MN assays, dose-response of "
                f"{len(screening_hits)} computationally identified hit(s), selectivity.\n"
                f"Year 2: Lead optimization, ADMET profiling, combination studies "
                f"with nusinersen/risdiplam, PK characterization.\n"
                f"Year 3: SMA mouse model efficacy study (SMN-delta7), dose optimization, "
                f"biomarker development.\n"
                f"Year 4: Confirmatory in vivo study, IND-enabling toxicology (if warranted), "
                f"mechanism of action studies.\n"
                f"Year 5: Data integration, publications, IND preparation or partnership "
                f"with pharma for clinical development."
            )
        else:
            return (
                f"Year 1: Structure determination/modeling of {symbol}, DiffDock virtual "
                f"screening, biochemical validation of top hits.\n"
                f"Year 2: iPSC-MN dose-response, selectivity, early ADMET.\n"
                f"Year 3: Lead optimization, combination studies, PK characterization.\n"
                f"Year 4: SMA mouse model efficacy, biomarker development.\n"
                f"Year 5: Confirmatory in vivo, IND-enabling studies, publications, "
                f"partnership development."
            )


def _build_budget_estimate(
    grant_format: str,
    screening_hits: list[dict],
) -> str:
    """Compose a budget summary."""
    fmt = GRANT_FORMATS.get(grant_format, GRANT_FORMATS["NIH_R01"])
    duration = fmt["duration_years"]
    budget_range = fmt["budget_range"]
    has_hits = len(screening_hits) > 0

    if grant_format == "CURE_SMA":
        return (
            f"Budget: {budget_range} for {duration} years.\n"
            f"Major costs: iPSC-MN differentiation and maintenance ($30K/yr), "
            f"compound synthesis/purchase ($15K/yr), assay reagents and consumables "
            f"($25K/yr), personnel (1 postdoc at 50% effort, $40K/yr), "
            f"computational resources ($5K/yr)."
        )
    elif grant_format == "NIH_R21":
        return (
            f"Budget: {budget_range}.\n"
            f"Year 1 ($150K): iPSC-MN assays ($40K), virtual screening compute ($10K), "
            f"compound purchase ($20K), personnel ($60K), supplies ($20K).\n"
            f"Year 2 ($125K): Combination studies ($30K), ADMET profiling ($25K), "
            f"personnel ($50K), publication costs ($5K), travel ($15K)."
        )
    elif grant_format == "ERC_StG":
        return (
            f"Budget: {budget_range}.\n"
            f"Personnel (60%): 1 postdoc (5 yr), 1 PhD student (4 yr), 1 technician (3 yr).\n"
            f"Consumables (25%): iPSC culture, screening compounds, mouse studies.\n"
            f"Equipment (10%): Computational GPU cluster access, plate reader.\n"
            f"Travel and dissemination (5%): Conferences, open access fees."
        )
    else:
        # NIH_R01 default
        total_low = 250 * duration
        total_high = 500 * duration
        mouse_line = ""
        if duration >= 3:
            mouse_line = (
                f"Years 3-{duration}: SMA mouse colony ($30K/yr), behavioral testing "
                f"equipment ($15K), histology ($20K/yr).\n"
            )
        return (
            f"Budget: {budget_range} for {duration} years "
            f"(${total_low}K-${total_high}K total direct costs).\n"
            f"Personnel: PI (15% effort), 1 postdoc (100%), 1 research technician (50%).\n"
            f"Years 1-2: iPSC-MN assays ($50K/yr), compound screening ($30K/yr), "
            f"ADMET profiling ($25K/yr).\n"
            + mouse_line
            + f"Computational: GPU compute and platform hosting ($10K/yr).\n"
            f"Other: Publication costs, conference travel, subaward (if applicable)."
        )


async def generate_grant_export(
    symbol: str,
    grant_format: str = "NIH_R01",
) -> dict[str, Any]:
    """Generate grant-ready formatted text sections for a target.

    Fetches live platform data (convergence score, claims, screening hits,
    hypotheses, experiment suggestions) and composes structured prose
    suitable for grant applications (NIH R01, R21, ERC StG, Cure SMA).

    Returns dict with: target, grant_format, sections, evidence_citations,
    convergence_data, and metadata.
    """
    sym = symbol.upper().strip()

    if grant_format not in GRANT_FORMATS:
        return {
            "error": f"Unsupported grant format '{grant_format}'. "
                     f"Supported: {', '.join(sorted(GRANT_FORMATS.keys()))}",
        }

    # -----------------------------------------------------------------------
    # 1. Fetch target basics
    # -----------------------------------------------------------------------
    target = await fetchrow(
        "SELECT * FROM targets WHERE UPPER(symbol) = $1", sym
    )
    if not target:
        return {"error": f"Target '{sym}' not found in database"}

    target = dict(target)
    target_id = str(target["id"])
    target_name = target.get("name") or sym
    target_desc = target.get("description") or ""

    # -----------------------------------------------------------------------
    # 2. Fetch convergence score
    # -----------------------------------------------------------------------
    convergence: dict | None = None
    conv_row = await fetchrow(
        "SELECT * FROM convergence_scores WHERE target_id = $1 "
        "ORDER BY computed_at DESC LIMIT 1",
        target["id"],
    )
    if conv_row:
        c = dict(conv_row)
        convergence = {
            "composite_score": float(c.get("composite_score", 0)),
            "confidence_level": c.get("confidence_level"),
            "volume": float(c.get("volume", 0)),
            "lab_independence": float(c.get("lab_independence", 0)),
            "method_diversity": float(c.get("method_diversity", 0)),
            "temporal_trend": float(c.get("temporal_trend", 0)),
            "replication": float(c.get("replication", 0)),
            "claim_count": c.get("claim_count", 0),
            "source_count": c.get("source_count", 0),
        }

    # -----------------------------------------------------------------------
    # 3. Fetch top claims with citation info
    # -----------------------------------------------------------------------
    claim_rows = await fetch(
        """SELECT c.id, c.claim_number, c.claim_type, c.predicate, c.confidence,
                  s.title AS source_title, s.external_id AS pmid
           FROM claims c
           JOIN evidence e ON e.claim_id = c.id
           JOIN sources s ON e.source_id = s.id
           WHERE c.subject_id = $1 OR c.object_id = $1
           ORDER BY c.confidence DESC, c.created_at DESC
           LIMIT 15""",
        target["id"],
    )
    claims = []
    citations: list[str] = []
    for r in claim_rows:
        d = dict(r)
        pmid = d.get("pmid")
        claims.append({
            "claim_id": f"CLAIM-{d.get('claim_number', 0):05d}" if d.get("claim_number") else str(d["id"])[:8],
            "type": d.get("claim_type"),
            "text": d.get("predicate"),
            "confidence": float(d["confidence"]) if d.get("confidence") is not None else None,
            "source": d.get("source_title"),
            "pmid": pmid,
        })
        if pmid and pmid.strip():
            ref = f"PMID:{pmid}"
            if ref not in citations:
                citations.append(ref)

    # -----------------------------------------------------------------------
    # 4. Fetch screening hits
    # -----------------------------------------------------------------------
    hit_rows = await fetch(
        """SELECT hit_smiles, docking_confidence, stage, status, result
           FROM screening_milestones
           WHERE hit_target = $1
           ORDER BY docking_confidence DESC""",
        sym,
    )
    hits: dict[str, dict] = {}
    for r in hit_rows:
        key = r["hit_smiles"]
        if key not in hits:
            hits[key] = {
                "smiles": key,
                "docking_confidence": float(r["docking_confidence"]),
                "stages_completed": 0,
                "stages_total": 0,
            }
        hits[key]["stages_total"] += 1
        if r["status"] == "completed":
            hits[key]["stages_completed"] += 1
    screening_hits = sorted(
        hits.values(), key=lambda x: x["docking_confidence"], reverse=True
    )

    # -----------------------------------------------------------------------
    # 5. Fetch hypotheses
    # -----------------------------------------------------------------------
    hyp_rows = await fetch(
        """SELECT id, title, description, hypothesis_type, confidence
           FROM hypotheses
           WHERE title ILIKE $1 OR description ILIKE $1
           ORDER BY confidence DESC
           LIMIT 5""",
        f"%{sym}%",
    )
    hypotheses = [
        {
            "id": str(r["id"])[:8],
            "title": r["title"],
            "summary": r["description"][:200] if r.get("description") else None,
            "type": r.get("hypothesis_type"),
            "score": float(r["confidence"]) if r.get("confidence") is not None else None,
        }
        for r in hyp_rows
    ]

    # -----------------------------------------------------------------------
    # 6. Fetch experiment suggestions (evidence gaps)
    # -----------------------------------------------------------------------
    from .experiment_designer import suggest_experiments
    exp_result = await suggest_experiments(sym)
    experiment_suggestions = exp_result.get("suggestions", [])

    # -----------------------------------------------------------------------
    # 7. Fetch assay suggestion for best screening hit
    # -----------------------------------------------------------------------
    assay_suggestion = None
    if screening_hits:
        from .assay_ready import generate_assay_card
        try:
            best_hit = screening_hits[0]
            assay_suggestion = generate_assay_card(
                smiles=best_hit["smiles"],
                target=sym,
                docking_confidence=best_hit["docking_confidence"],
            )
        except Exception as exc:
            logger.warning("Assay card generation failed for %s: %s", sym, exc)

    # -----------------------------------------------------------------------
    # 8. Compose grant sections
    # -----------------------------------------------------------------------
    fmt = GRANT_FORMATS[grant_format]

    sections = {
        "specific_aim": _build_specific_aim(
            symbol=sym,
            target_name=target_name,
            target_desc=target_desc,
            convergence=convergence,
            hypotheses=hypotheses,
            screening_hits=screening_hits,
            grant_format=grant_format,
        ),
        "significance": _build_significance(
            symbol=sym,
            target_name=target_name,
            convergence=convergence,
            claims=claims,
            hypotheses=hypotheses,
        ),
        "innovation": _build_innovation(
            symbol=sym,
            screening_hits=screening_hits,
            convergence=convergence,
            grant_format=grant_format,
        ),
        "approach": _build_approach(
            symbol=sym,
            screening_hits=screening_hits,
            assay_suggestion=assay_suggestion,
            experiment_suggestions=experiment_suggestions,
            grant_format=grant_format,
        ),
        "timeline": _build_timeline(
            symbol=sym,
            screening_hits=screening_hits,
            grant_format=grant_format,
        ),
        "budget_estimate": _build_budget_estimate(
            grant_format=grant_format,
            screening_hits=screening_hits,
        ),
    }

    return {
        "target": sym,
        "target_name": target_name,
        "grant_format": grant_format,
        "funder": fmt["funder"],
        "mechanism": fmt["mechanism"],
        "duration_years": fmt["duration_years"],
        "sections": sections,
        "evidence_citations": citations,
        "convergence_data": convergence,
        "screening_hits_used": len(screening_hits),
        "claims_referenced": len(claims),
        "hypotheses_referenced": len(hypotheses),
        "experiment_suggestions_count": len(experiment_suggestions),
        "supported_formats": sorted(GRANT_FORMATS.keys()),
    }
