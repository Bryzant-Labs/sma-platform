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
