# PRIVATE: Patient data — admin-only access, never expose publicly
"""Personal Digital Twin — personalized SMA analysis for a single patient.

This module allows a patient (the platform creator has SMA) to input their own
clinical data and receive a personalized Digital Twin analysis. All functions
require admin-level access; no public endpoints exist for this module.

Uses:
- modifier_predictor: phenotype prediction from SMN2 copies + modifiers
- digital_twin: drug combination simulation on motor neuron model
- synergy_predictor: drug-target synergy scoring
- experiment_value: EVE scoring for hypothesis prioritization
- bayesian_convergence: posterior evidence strength per target

Tables: patient_profiles (new), trials, drugs, targets, hypotheses, claims,
         evidence, convergence_scores.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from ..core.database import execute, fetch, fetchrow, fetchval

from .modifier_predictor import predict_phenotype
from .digital_twin import simulate_drug_combination, DRUG_EFFECTS, COMPARTMENTS, PATHWAYS
from .synergy_predictor import predict_drug_target_synergy
from .experiment_value import score_hypotheses_eve
from .bayesian_convergence import bayesian_score

logger = logging.getLogger(__name__)

# ============================================================================
# SECURITY: All functions in this module access PRIVATE PATIENT DATA.
# ALL callers MUST enforce authentication before invoking these functions.
# The API routes in api/routes/personal_twin.py use require_admin_key.
# If you create any new route or CLI command that calls these functions,
# you MUST add authentication. Unauthenticated access = data breach.
# ============================================================================


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_SMA_TYPES = {"type0", "type1", "type2", "type3", "type4", "presymptomatic", "unknown"}

# Therapy modalities for gap analysis
THERAPY_MODALITIES = {
    "splicing_modifier": {
        "description": "SMN2 exon 7 inclusion enhancer",
        "examples": ["Nusinersen", "Risdiplam"],
        "target": "SMN2 splicing",
    },
    "gene_therapy": {
        "description": "SMN1 gene replacement via AAV9",
        "examples": ["Zolgensma (onasemnogene abeparvovec)"],
        "target": "SMN1 replacement",
    },
    "muscle_support": {
        "description": "Anti-myostatin or muscle-targeted therapy",
        "examples": ["Apitegromab", "SRK-015"],
        "target": "Muscle growth / anti-atrophy",
    },
    "nmj_enhancer": {
        "description": "Neuromuscular junction transmission enhancer",
        "examples": ["4-Aminopyridine", "GV-58"],
        "target": "NMJ calcium / ACh release",
    },
    "neuroprotectant": {
        "description": "Mitochondrial or neuroprotective support",
        "examples": ["NMN (NAD+)", "CoQ10", "Olesoxime"],
        "target": "Mitochondrial bioenergetics",
    },
}

# Map therapy names to modalities for gap detection
_THERAPY_TO_MODALITY: dict[str, str] = {
    "nusinersen": "splicing_modifier",
    "risdiplam": "splicing_modifier",
    "zolgensma": "gene_therapy",
    "onasemnogene": "gene_therapy",
    "apitegromab": "muscle_support",
    "srk-015": "muscle_support",
    "4-aminopyridine": "nmj_enhancer",
    "4-ap": "nmj_enhancer",
    "gv-58": "nmj_enhancer",
    "nmn": "neuroprotectant",
    "coq10": "neuroprotectant",
    "olesoxime": "neuroprotectant",
}

# Biomarkers recommended for SMA monitoring
RECOMMENDED_BIOMARKERS = [
    {
        "name": "Neurofilament light chain (NfL)",
        "specimen": "CSF or plasma",
        "purpose": "Motor neuron degeneration marker — tracks acute damage",
        "frequency": "Every 3-6 months",
        "relevance": "Elevated NfL correlates with disease progression; drops after treatment onset",
    },
    {
        "name": "SMN protein level",
        "specimen": "Blood (PBMCs)",
        "purpose": "Direct measure of SMN protein — primary target of all splicing therapies",
        "frequency": "Every 3-6 months",
        "relevance": "Correlates with SMN2-modifying therapy efficacy",
    },
    {
        "name": "pNfH (phosphorylated neurofilament heavy chain)",
        "specimen": "CSF or plasma",
        "purpose": "Axonal damage marker — more specific to large motor neurons than NfL",
        "frequency": "Every 6 months",
        "relevance": "Elevated in SMA Type I/II; may normalize with effective treatment",
    },
    {
        "name": "CMAP (compound muscle action potential)",
        "specimen": "Electrophysiology",
        "purpose": "Functional measure of motor unit number and NMJ transmission",
        "frequency": "Every 6-12 months",
        "relevance": "Directly measures neuromuscular function; key for 4-AP / NMJ therapies",
    },
    {
        "name": "Creatinine",
        "specimen": "Serum or urine",
        "purpose": "Muscle mass proxy — low creatinine reflects muscle wasting",
        "frequency": "Every 3 months",
        "relevance": "Tracks muscle mass changes; may improve with myostatin inhibitors",
    },
    {
        "name": "CK (creatine kinase)",
        "specimen": "Serum",
        "purpose": "Muscle damage marker — elevated during active muscle breakdown",
        "frequency": "Every 3-6 months",
        "relevance": "Transient elevation normal after treatment start; persistent elevation = concern",
    },
]


# ---------------------------------------------------------------------------
# Table initialization
# ---------------------------------------------------------------------------

async def _ensure_table() -> None:
    """Create patient_profiles table if it does not exist."""
    await execute("""
        CREATE TABLE IF NOT EXISTS patient_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_name TEXT NOT NULL DEFAULT 'default',
            sma_type TEXT,
            smn2_copies INTEGER,
            age_years INTEGER,
            age_at_diagnosis_months INTEGER,
            current_therapies JSONB DEFAULT '[]',
            therapy_history JSONB DEFAULT '[]',
            functional_scores JSONB DEFAULT '{}',
            biomarkers JSONB DEFAULT '{}',
            genetic_modifiers JSONB DEFAULT '{}',
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)


# ---------------------------------------------------------------------------
# Profile CRUD
# ---------------------------------------------------------------------------

async def create_or_update_profile(data: dict) -> dict:
    """Save or update a patient profile.

    Args:
        data: Dictionary with profile fields. Must include 'profile_name'
              (defaults to 'default'). Validated fields:
              sma_type, smn2_copies, age_years, age_at_diagnosis_months,
              current_therapies, therapy_history, functional_scores,
              biomarkers, genetic_modifiers, notes.

    Returns:
        The saved profile as a dict.

    Raises:
        ValueError: If validation fails (invalid SMA type, SMN2 out of range, etc.).
    """
    await _ensure_table()

    profile_name = data.get("profile_name", "default").strip()
    if not profile_name:
        raise ValueError("profile_name cannot be empty")

    # Validate sma_type
    sma_type = data.get("sma_type")
    if sma_type and sma_type.lower().strip() not in VALID_SMA_TYPES:
        raise ValueError(
            f"Invalid sma_type '{sma_type}'. Must be one of: {sorted(VALID_SMA_TYPES)}"
        )
    if sma_type:
        sma_type = sma_type.lower().strip()

    # Validate smn2_copies
    smn2_copies = data.get("smn2_copies")
    if smn2_copies is not None:
        smn2_copies = int(smn2_copies)
        if smn2_copies < 0 or smn2_copies > 8:
            raise ValueError("smn2_copies must be between 0 and 8")

    # Validate age
    age_years = data.get("age_years")
    if age_years is not None:
        age_years = int(age_years)
        if age_years < 0 or age_years > 150:
            raise ValueError("age_years must be between 0 and 150")

    age_at_diagnosis_months = data.get("age_at_diagnosis_months")
    if age_at_diagnosis_months is not None:
        age_at_diagnosis_months = int(age_at_diagnosis_months)
        if age_at_diagnosis_months < 0:
            raise ValueError("age_at_diagnosis_months must be non-negative")

    # JSON fields — ensure they are valid JSON
    current_therapies = data.get("current_therapies", [])
    if isinstance(current_therapies, str):
        current_therapies = json.loads(current_therapies)

    therapy_history = data.get("therapy_history", [])
    if isinstance(therapy_history, str):
        therapy_history = json.loads(therapy_history)

    functional_scores = data.get("functional_scores", {})
    if isinstance(functional_scores, str):
        functional_scores = json.loads(functional_scores)

    biomarkers = data.get("biomarkers", {})
    if isinstance(biomarkers, str):
        biomarkers = json.loads(biomarkers)

    genetic_modifiers = data.get("genetic_modifiers", {})
    if isinstance(genetic_modifiers, str):
        genetic_modifiers = json.loads(genetic_modifiers)

    notes = data.get("notes")

    # Check if profile exists
    existing = await fetchrow(
        "SELECT id FROM patient_profiles WHERE profile_name = $1",
        profile_name,
    )

    now = datetime.now(timezone.utc).isoformat()

    if existing:
        # Update
        await execute(
            """UPDATE patient_profiles
               SET sma_type = $1,
                   smn2_copies = $2,
                   age_years = $3,
                   age_at_diagnosis_months = $4,
                   current_therapies = $5::jsonb,
                   therapy_history = $6::jsonb,
                   functional_scores = $7::jsonb,
                   biomarkers = $8::jsonb,
                   genetic_modifiers = $9::jsonb,
                   notes = $10,
                   updated_at = $11
               WHERE profile_name = $12""",
            sma_type,
            smn2_copies,
            age_years,
            age_at_diagnosis_months,
            json.dumps(current_therapies),
            json.dumps(therapy_history),
            json.dumps(functional_scores),
            json.dumps(biomarkers),
            json.dumps(genetic_modifiers),
            notes,
            now,
            profile_name,
        )
        logger.info("Updated patient profile: %s", profile_name)
    else:
        # Insert
        await execute(
            """INSERT INTO patient_profiles
               (profile_name, sma_type, smn2_copies, age_years,
                age_at_diagnosis_months, current_therapies, therapy_history,
                functional_scores, biomarkers, genetic_modifiers, notes)
               VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb,
                       $8::jsonb, $9::jsonb, $10::jsonb, $11)""",
            profile_name,
            sma_type,
            smn2_copies,
            age_years,
            age_at_diagnosis_months,
            json.dumps(current_therapies),
            json.dumps(therapy_history),
            json.dumps(functional_scores),
            json.dumps(biomarkers),
            json.dumps(genetic_modifiers),
            notes,
        )
        logger.info("Created patient profile: %s", profile_name)

    return await get_profile(profile_name)


async def get_profile(profile_name: str = "default") -> dict:
    """Retrieve a patient profile by name.

    Args:
        profile_name: Profile identifier (default: 'default').

    Returns:
        Profile dict, or error dict if not found.
    """
    await _ensure_table()

    row = await fetchrow(
        "SELECT * FROM patient_profiles WHERE profile_name = $1",
        profile_name,
    )
    if not row:
        return {"error": f"Profile '{profile_name}' not found"}

    result = dict(row)

    # Parse JSONB fields if they come back as strings
    for field in ("current_therapies", "therapy_history", "functional_scores",
                  "biomarkers", "genetic_modifiers"):
        val = result.get(field)
        if isinstance(val, str):
            try:
                result[field] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass

    return result


# ---------------------------------------------------------------------------
# Full personal Digital Twin analysis
# ---------------------------------------------------------------------------

async def run_personal_twin(profile_name: str = "default") -> dict:
    """Run the full Digital Twin analysis on a patient's data.

    Integrates:
    1. Modifier-aware phenotype prediction (predicted vs actual calibration)
    2. Drug combination simulation on motor neuron model
    3. Synergy predictions for therapy additions
    4. EVE scoring filtered to patient-relevant hypotheses
    5. Bayesian convergence for patient-specific targets
    6. Personalized report with recommendations

    Args:
        profile_name: Profile to analyze.

    Returns:
        Comprehensive personal analysis dict.
    """
    profile = await get_profile(profile_name)
    if "error" in profile:
        return profile

    report: dict[str, Any] = {
        "profile_name": profile_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # --- 1. Phenotype prediction vs actual ---
    smn2_copies = profile.get("smn2_copies")
    genetic_modifiers = profile.get("genetic_modifiers") or {}
    sma_type_actual = profile.get("sma_type")

    if smn2_copies is not None:
        try:
            phenotype = await predict_phenotype(smn2_copies, genetic_modifiers)
            predicted_type = phenotype.get("predicted_type", "unknown")

            # Calibration check: does prediction match reality?
            calibration = "unknown"
            if sma_type_actual and predicted_type:
                pred_lower = predicted_type.lower()
                actual_lower = sma_type_actual.lower()
                # Rough match check
                if actual_lower in pred_lower or pred_lower.startswith(actual_lower.replace("type", "type ")):
                    calibration = "concordant"
                else:
                    calibration = "discordant"

            report["phenotype_prediction"] = {
                "predicted_type": predicted_type,
                "actual_type": sma_type_actual,
                "calibration": calibration,
                "severity_score": phenotype.get("severity_score"),
                "confidence": phenotype.get("confidence"),
                "modifier_shift": phenotype.get("modifier_shift"),
                "contributing_factors": phenotype.get("contributing_factors", []),
                "clinical_note": phenotype.get("clinical_note"),
                "note": (
                    "Concordant prediction confirms the genetic model accurately reflects "
                    "your clinical presentation."
                    if calibration == "concordant"
                    else "Discordant prediction suggests additional modifiers, environmental "
                         "factors, or epigenetic influences not captured in the model."
                    if calibration == "discordant"
                    else "Provide SMA type in profile for calibration check."
                ),
            }
        except Exception as e:
            logger.error("Phenotype prediction failed: %s", e, exc_info=True)
            report["phenotype_prediction"] = {"error": str(e)}
    else:
        report["phenotype_prediction"] = {
            "error": "SMN2 copy number not set in profile — required for phenotype prediction"
        }

    # --- 2. Current therapy effectiveness simulation ---
    current_therapies = profile.get("current_therapies") or []
    therapy_names = []
    for t in current_therapies:
        if isinstance(t, dict):
            therapy_names.append(t.get("name", ""))
        elif isinstance(t, str):
            therapy_names.append(t)

    therapy_names = [n for n in therapy_names if n]

    if therapy_names:
        sim = simulate_drug_combination(therapy_names)
        report["current_therapy_simulation"] = {
            "drugs_applied": sim.get("drugs_applied", []),
            "drugs_not_found": [n for n in therapy_names if n not in sim.get("drugs_applied", [])],
            "functional_score": sim.get("functional_score"),
            "overall_health": sim.get("overall_health"),
            "improvement_vs_baseline": sim.get("improvement_vs_baseline"),
            "compartment_health": sim.get("compartment_health"),
            "pathway_activity": sim.get("pathway_activity"),
            "interpretation": _interpret_simulation(sim),
        }
    else:
        report["current_therapy_simulation"] = {
            "note": "No current therapies listed in profile",
            "baseline_health": simulate_drug_combination([]).get("overall_health"),
        }

    # --- 3. Recommended therapy additions (synergy-ranked) ---
    try:
        additions = _rank_therapy_additions(therapy_names)
        report["recommended_additions"] = additions
    except Exception as e:
        logger.error("Therapy addition ranking failed: %s", e, exc_info=True)
        report["recommended_additions"] = {"error": str(e)}

    # --- 4. Relevant clinical trials ---
    try:
        trials = await get_relevant_trials(profile_name)
        report["relevant_trials"] = {
            "count": len(trials),
            "trials": trials[:20],  # Top 20
        }
    except Exception as e:
        logger.error("Trial filtering failed: %s", e, exc_info=True)
        report["relevant_trials"] = {"error": str(e)}

    # --- 5. Biomarker monitoring recommendations ---
    tracked_biomarkers = profile.get("biomarkers") or {}
    report["biomarker_recommendations"] = _biomarker_recommendations(
        tracked_biomarkers, therapy_names
    )

    # --- 6. Evidence quality for genetic profile (Bayesian) ---
    if genetic_modifiers:
        bayesian_results = {}
        for symbol in genetic_modifiers:
            try:
                score = await bayesian_score(symbol.upper())
                if "error" not in score:
                    bayesian_results[symbol.upper()] = {
                        "posterior_mean": score.get("posterior_mean"),
                        "bayes_factor": score.get("bayes_factor"),
                        "bayes_factor_interpretation": score.get("bayes_factor_interpretation"),
                        "evidence_sufficiency": score.get("evidence_sufficiency"),
                        "claim_count": score.get("claim_count"),
                        "credible_interval_95": score.get("credible_interval_95"),
                    }
            except Exception as e:
                logger.warning("Bayesian score for %s failed: %s", symbol, e)
                bayesian_results[symbol.upper()] = {"error": str(e)}

        report["evidence_quality"] = bayesian_results
    else:
        report["evidence_quality"] = {
            "note": "No genetic modifiers specified — add modifiers to profile for evidence assessment"
        }

    # --- 7. Top experiments for THIS patient ---
    try:
        all_eve = await score_hypotheses_eve(limit=100)
        # Filter to patient-relevant: match SMA type or current targets
        relevant_eve = _filter_patient_relevant_experiments(all_eve, profile)
        report["top_experiments"] = relevant_eve[:10]
    except Exception as e:
        logger.error("EVE scoring failed: %s", e, exc_info=True)
        report["top_experiments"] = {"error": str(e)}

    return report


# ---------------------------------------------------------------------------
# Relevant clinical trials
# ---------------------------------------------------------------------------

async def get_relevant_trials(profile_name: str = "default") -> list[dict]:
    """Filter clinical trials relevant to this patient.

    Filters by:
    - SMA type (from conditions or interventions text)
    - Age eligibility (if available)
    - Current therapy overlap (exclude already-on-therapy trials, include addons)
    - Status (prefer recruiting > active > completed)

    Args:
        profile_name: Profile to filter for.

    Returns:
        List of relevant trial dicts, scored and sorted.
    """
    profile = await get_profile(profile_name)
    if "error" in profile:
        return []

    sma_type = profile.get("sma_type") or ""
    age_years = profile.get("age_years")
    current_therapies = profile.get("current_therapies") or []

    # Extract therapy names for overlap check
    therapy_name_set: set[str] = set()
    for t in current_therapies:
        name = t.get("name", "") if isinstance(t, dict) else str(t)
        if name:
            therapy_name_set.add(name.lower())

    # Fetch all trials
    try:
        rows = await fetch(
            "SELECT id, nct_id, title, status, phase, conditions, interventions, "
            "sponsor, start_date, enrollment, url FROM trials ORDER BY start_date DESC NULLS LAST"
        )
    except Exception as e:
        logger.error("Failed to fetch trials: %s", e)
        return []

    scored_trials: list[dict[str, Any]] = []

    for row in rows:
        trial = dict(row)
        score = 0.0
        reasons: list[str] = []

        # Parse fields
        title_lower = (trial.get("title") or "").lower()
        conditions_text = json.dumps(trial.get("conditions") or []).lower()
        interventions = trial.get("interventions") or []
        if isinstance(interventions, str):
            try:
                interventions = json.loads(interventions)
            except (json.JSONDecodeError, TypeError):
                interventions = []
        interventions_text = json.dumps(interventions).lower()
        status = (trial.get("status") or "").lower()

        # SMA type match
        if sma_type:
            type_num = sma_type.replace("type", "").strip()
            type_patterns = [
                f"type {type_num}", f"type{type_num}", f"sma {type_num}",
                f"type {_roman(type_num)}", f"sma type {_roman(type_num)}",
            ]
            for pat in type_patterns:
                if pat in title_lower or pat in conditions_text or pat in interventions_text:
                    score += 3.0
                    reasons.append(f"Matches SMA {sma_type}")
                    break

            # Generic SMA match (still relevant)
            if not reasons and ("spinal muscular atrophy" in title_lower or "sma" in conditions_text):
                score += 1.5
                reasons.append("General SMA trial")

        # Status scoring
        status_scores = {
            "recruiting": 3.0,
            "not yet recruiting": 2.5,
            "active, not recruiting": 1.5,
            "enrolling by invitation": 2.0,
            "completed": 0.5,
        }
        status_bonus = status_scores.get(status, 0.0)
        score += status_bonus
        if status_bonus > 0:
            reasons.append(f"Status: {status}")

        # Phase scoring (later phases = more translational)
        phase = (trial.get("phase") or "").lower()
        phase_scores = {"phase 3": 3.0, "phase 2/phase 3": 2.5, "phase 2": 2.0,
                        "phase 1/phase 2": 1.5, "phase 1": 1.0}
        for p, ps in phase_scores.items():
            if p in phase:
                score += ps
                reasons.append(f"Phase: {phase}")
                break

        # Therapy overlap — if already on a therapy, de-prioritize trials for same drug
        for tn in therapy_name_set:
            if tn in interventions_text:
                score -= 1.0
                reasons.append(f"Already on {tn} — lower priority")

        # Only include if some relevance
        if score > 0:
            trial["relevance_score"] = round(score, 2)
            trial["relevance_reasons"] = reasons
            scored_trials.append(trial)

    # Sort by relevance score descending
    scored_trials.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_trials


# ---------------------------------------------------------------------------
# Therapy optimization
# ---------------------------------------------------------------------------

async def therapy_optimization(profile_name: str = "default") -> dict:
    """Given current therapies, suggest optimizations.

    Analyzes:
    - Missing modalities (e.g., has splicing modifier but no muscle support)
    - Combination opportunities (e.g., risdiplam + apitegromab + 4-AP)
    - Monitoring gaps (which biomarkers should be tracked)
    - Digital twin simulation of optimized regimen

    Args:
        profile_name: Profile to optimize.

    Returns:
        Optimization report dict.
    """
    profile = await get_profile(profile_name)
    if "error" in profile:
        return profile

    current_therapies = profile.get("current_therapies") or []
    therapy_names: list[str] = []
    for t in current_therapies:
        if isinstance(t, dict):
            therapy_names.append(t.get("name", ""))
        elif isinstance(t, str):
            therapy_names.append(t)
    therapy_names = [n for n in therapy_names if n]

    tracked_biomarkers = profile.get("biomarkers") or {}

    # --- 1. Modality gap analysis ---
    covered_modalities: set[str] = set()
    for tn in therapy_names:
        modality = _THERAPY_TO_MODALITY.get(tn.lower().strip())
        if modality:
            covered_modalities.add(modality)

    missing_modalities: list[dict[str, Any]] = []
    for mod_key, mod_info in THERAPY_MODALITIES.items():
        if mod_key not in covered_modalities:
            missing_modalities.append({
                "modality": mod_key,
                "description": mod_info["description"],
                "examples": mod_info["examples"],
                "target": mod_info["target"],
                "rationale": f"No current therapy covers {mod_info['description'].lower()}. "
                             f"Adding a {mod_key.replace('_', ' ')} could address "
                             f"{mod_info['target'].lower()}.",
            })

    # --- 2. Combination simulation ---
    # Simulate current
    current_sim = simulate_drug_combination(therapy_names)

    # Try adding each missing modality's lead example
    addition_candidates: list[dict[str, Any]] = []
    for mm in missing_modalities:
        for example in mm["examples"]:
            combo = therapy_names + [example]
            combo_sim = simulate_drug_combination(combo)
            improvement = combo_sim["functional_score"] - current_sim["functional_score"]
            if improvement > 0:
                addition_candidates.append({
                    "drug": example,
                    "modality": mm["modality"],
                    "current_score": current_sim["functional_score"],
                    "combo_score": combo_sim["functional_score"],
                    "marginal_improvement": round(improvement, 4),
                    "rationale": mm["rationale"],
                })

    addition_candidates.sort(key=lambda x: x["marginal_improvement"], reverse=True)

    # --- 3. Best optimized regimen ---
    best_regimen = list(therapy_names)
    best_score = current_sim["functional_score"]
    for cand in addition_candidates:
        test_regimen = best_regimen + [cand["drug"]]
        test_sim = simulate_drug_combination(test_regimen)
        if test_sim["functional_score"] > best_score:
            best_regimen = test_regimen
            best_score = test_sim["functional_score"]

    optimized_sim = simulate_drug_combination(best_regimen)

    # --- 4. Monitoring gaps ---
    monitoring = _biomarker_recommendations(tracked_biomarkers, best_regimen)

    # --- 5. Synergy predictions for current targets ---
    synergy_info: list[dict] = []
    try:
        all_synergies = await predict_drug_target_synergy(limit=50)
        current_drug_names_lower = {n.lower() for n in therapy_names}
        for syn in all_synergies:
            if syn.get("drug_name", "").lower() in current_drug_names_lower:
                synergy_info.append(syn)
    except Exception as e:
        logger.warning("Synergy prediction failed: %s", e)

    return {
        "profile_name": profile_name,
        "current_therapies": therapy_names,
        "current_simulation": {
            "functional_score": current_sim.get("functional_score"),
            "overall_health": current_sim.get("overall_health"),
            "improvement_vs_baseline": current_sim.get("improvement_vs_baseline"),
        },
        "modality_coverage": {
            "covered": sorted(covered_modalities),
            "missing": missing_modalities,
        },
        "addition_candidates": addition_candidates,
        "optimized_regimen": {
            "drugs": best_regimen,
            "functional_score": optimized_sim.get("functional_score"),
            "overall_health": optimized_sim.get("overall_health"),
            "improvement_vs_current": round(
                optimized_sim.get("functional_score", 0) - current_sim.get("functional_score", 0),
                4,
            ),
            "improvement_vs_baseline": optimized_sim.get("improvement_vs_baseline"),
        },
        "monitoring_recommendations": monitoring,
        "synergy_insights": synergy_info[:10],
        "disclaimer": (
            "These optimization suggestions are computational predictions based on "
            "published evidence and the digital twin model. They are for research "
            "purposes only and must NOT be used as medical advice. Always consult "
            "your treating neurologist before making any therapy changes."
        ),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _interpret_simulation(sim: dict) -> str:
    """Generate human-readable interpretation of simulation results."""
    score = sim.get("functional_score", 0)
    improvement = sim.get("improvement_vs_baseline", 0)
    drugs = sim.get("drugs_applied", [])

    if not drugs:
        return "No drugs recognized in the simulation model."

    parts = [f"Current regimen ({', '.join(drugs)}) achieves a functional score of {score:.2f} "]
    parts.append(f"({improvement:+.2f} vs untreated SMA baseline).")

    if score >= 0.7:
        parts.append(" This represents strong therapeutic coverage.")
    elif score >= 0.5:
        parts.append(" Moderate therapeutic coverage — room for improvement with additional modalities.")
    else:
        parts.append(" Limited therapeutic coverage — consider adding complementary therapies.")

    # Identify weakest compartments
    health = sim.get("compartment_health", {})
    if health:
        weakest = min(health, key=health.get)
        parts.append(f" Weakest compartment: {weakest} ({health[weakest]:.2f}).")

    return "".join(parts)


def _rank_therapy_additions(current_drugs: list[str]) -> list[dict]:
    """Rank potential therapy additions by marginal improvement on digital twin."""
    current_sim = simulate_drug_combination(current_drugs)
    current_score = current_sim["functional_score"]

    candidates: list[dict] = []
    for de in DRUG_EFFECTS:
        if de.drug in current_drugs:
            continue

        combo_sim = simulate_drug_combination(current_drugs + [de.drug])
        improvement = combo_sim["functional_score"] - current_score

        if improvement > 0.001:
            candidates.append({
                "drug": de.drug,
                "marginal_improvement": round(improvement, 4),
                "combo_functional_score": round(combo_sim["functional_score"], 4),
                "pathways_affected": list(de.pathway_effects.keys()),
                "compartments_affected": list(de.compartment_health_delta.keys()),
            })

    candidates.sort(key=lambda x: x["marginal_improvement"], reverse=True)
    return candidates


def _biomarker_recommendations(
    tracked: dict, therapy_names: list[str]
) -> dict[str, Any]:
    """Generate biomarker monitoring recommendations based on therapy and tracked markers."""
    tracked_names = {k.lower() for k in tracked}
    therapy_lower = {n.lower() for n in therapy_names}

    recommendations: list[dict] = []
    missing: list[dict] = []

    for bm in RECOMMENDED_BIOMARKERS:
        is_tracked = any(bm["name"].lower().startswith(tn) or tn in bm["name"].lower()
                         for tn in tracked_names) if tracked_names else False

        rec = dict(bm)
        rec["currently_tracked"] = is_tracked

        # Therapy-specific relevance boost
        if "cmap" in bm["name"].lower() and ("4-aminopyridine" in therapy_lower or "gv-58" in therapy_lower):
            rec["priority"] = "HIGH"
            rec["therapy_note"] = "Critical for monitoring NMJ-targeted therapy (4-AP / GV-58)"
        elif "smn protein" in bm["name"].lower() and (
            "nusinersen" in therapy_lower or "risdiplam" in therapy_lower
        ):
            rec["priority"] = "HIGH"
            rec["therapy_note"] = "Essential for measuring splicing modifier efficacy"
        elif "neurofilament" in bm["name"].lower():
            rec["priority"] = "HIGH"
            rec["therapy_note"] = "Universal neurodegeneration marker — track for all SMA patients"
        else:
            rec["priority"] = "MEDIUM"

        recommendations.append(rec)
        if not is_tracked:
            missing.append(rec)

    return {
        "all_recommended": recommendations,
        "currently_missing": missing,
        "tracking_completeness": f"{len(recommendations) - len(missing)}/{len(recommendations)}",
    }


def _filter_patient_relevant_experiments(
    eve_results: list[dict], profile: dict
) -> list[dict]:
    """Filter EVE-scored experiments to those relevant for this patient."""
    sma_type = (profile.get("sma_type") or "").lower()
    modifiers = profile.get("genetic_modifiers") or {}
    modifier_symbols = {s.upper() for s in modifiers}

    therapies = profile.get("current_therapies") or []
    therapy_names_lower = set()
    for t in therapies:
        name = t.get("name", "") if isinstance(t, dict) else str(t)
        therapy_names_lower.add(name.lower())

    relevant: list[dict] = []
    for exp in eve_results:
        relevance_score = exp.get("eve_score", 0)
        reasons: list[str] = []

        # Boost if experiment target is one of the patient's modifier genes
        target_sym = (exp.get("target_symbol") or "").upper()
        if target_sym in modifier_symbols:
            relevance_score *= 1.5
            reasons.append(f"Target {target_sym} is in patient's modifier gene profile")

        # Boost if claim type relates to patient's therapy modalities
        claim_type = exp.get("claim_type", "")
        if claim_type in ("drug_efficacy", "drug_target"):
            relevance_score *= 1.2
            reasons.append("Drug-related experiment — directly therapy-relevant")

        exp_copy = dict(exp)
        exp_copy["patient_relevance_score"] = round(relevance_score, 4)
        exp_copy["patient_relevance_reasons"] = reasons
        relevant.append(exp_copy)

    relevant.sort(key=lambda x: x["patient_relevance_score"], reverse=True)
    return relevant


def _roman(num_str: str) -> str:
    """Convert '1', '2', etc. to Roman numerals for trial matching."""
    mapping = {"0": "0", "1": "I", "2": "II", "3": "III", "4": "IV"}
    return mapping.get(num_str.strip(), num_str)
