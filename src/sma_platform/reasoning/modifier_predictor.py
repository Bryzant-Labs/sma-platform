"""Modifier-Aware Phenotype Prediction for SMA.

Given SMN2 copy number and modifier gene status, predicts SMA phenotype
severity using evidence-based rules from published literature.

The 5q-SMA phenotype is primarily determined by SMN2 copy number, but
modifier genes can shift severity significantly. PLS3 and NCALD are the
best-characterized protective modifiers — both discovered in discordant
SMA families where affected siblings with identical SMN1/SMN2 genotypes
had different clinical outcomes.

References:
- Wirth et al., Hum Mol Genet 2006 (SMN2 copy number–phenotype correlation)
- Oprea et al., Science 2008 (PLS3 as protective modifier, PMID 18327258)
- Hosseinibarkooie et al., Am J Hum Genet 2017 (NCALD, PMID 28622510)
- Roy et al., Am J Hum Genet 1995 (NAIP deletion, PMID 9462747)
- Helmken et al., Neurogenetics 2003 (GTF2H2, PMID 10615131)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

from ..core.database import fetch, fetchrow

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base severity mapping: SMN2 copy number → SMA type
# ---------------------------------------------------------------------------

BASE_SEVERITY: dict[int, str] = {
    1: "Type I (severe)",
    2: "Type I/II",
    3: "Type II/III",
    4: "Type III/IV",
    5: "Type IV (mild)",
}

# SMN2 copies → baseline severity score (0 = lethal, 1 = asymptomatic)
BASE_SEVERITY_SCORE: dict[int, float] = {
    1: 0.10,
    2: 0.30,
    3: 0.55,
    4: 0.75,
    5: 0.90,
}


# ---------------------------------------------------------------------------
# Known modifier genes with published evidence
# ---------------------------------------------------------------------------

@dataclass
class ModifierGene:
    """A gene known or predicted to modify SMA phenotype severity."""
    symbol: str
    effect: str              # "protective", "modifying", "unknown_protective"
    mechanism: str
    magnitude: float         # positive = milder, negative = more severe
    evidence_pmids: list[str]
    high_expression_effect: str
    low_expression_effect: str


MODIFIERS: dict[str, ModifierGene] = {
    "PLS3": ModifierGene(
        symbol="PLS3",
        effect="protective",
        mechanism="Actin bundling compensates cytoskeleton defects in motor neurons. "
                  "Overexpression rescues endocytosis and NMJ morphology in SMA models.",
        magnitude=0.5,
        evidence_pmids=["18327258", "22075251"],
        high_expression_effect="Significant protective shift — discordant siblings with "
                               "high PLS3 remain asymptomatic despite homozygous SMN1 deletion",
        low_expression_effect="No additional harm beyond SMN2 baseline",
    ),
    "NCALD": ModifierGene(
        symbol="NCALD",
        effect="protective",
        mechanism="Neuronal calcium sensor. Knockdown/low expression rescues "
                  "endocytosis defect and NMJ transmission in SMA models.",
        magnitude=0.4,
        evidence_pmids=["28622510"],
        high_expression_effect="No protective effect — may slightly worsen endocytosis defect",
        low_expression_effect="Protective — reduced NCALD rescues calcium-dependent "
                              "endocytosis at motor nerve terminals",
    ),
    "NAIP": ModifierGene(
        symbol="NAIP",
        effect="modifying",
        mechanism="Anti-apoptotic gene on 5q13. Homozygous deletion frequently "
                  "co-occurs with SMN1 deletion and correlates with more severe phenotype.",
        magnitude=-0.3,
        evidence_pmids=["9462747"],
        high_expression_effect="Intact NAIP provides anti-apoptotic protection to motor neurons",
        low_expression_effect="NAIP deletion removes apoptosis brake — worsens severity",
    ),
    "SERF1": ModifierGene(
        symbol="SERF1",
        effect="modifying",
        mechanism="Small EDRK-rich factor on 5q13. Copy number correlates "
                  "with severity — higher copies associated with milder phenotype.",
        magnitude=0.2,
        evidence_pmids=["9462747"],
        high_expression_effect="Higher copy number mildly protective",
        low_expression_effect="Lower copy number associated with more severe disease",
    ),
    "GTF2H2": ModifierGene(
        symbol="GTF2H2",
        effect="modifying",
        mechanism="General transcription factor IIH subunit on 5q13. "
                  "Copy number variation may affect transcription efficiency of SMN2.",
        magnitude=0.1,
        evidence_pmids=["10615131"],
        high_expression_effect="Marginally protective — improved transcription capacity",
        low_expression_effect="Slightly reduced transcription of SMN2",
    ),
    "CORO1C": ModifierGene(
        symbol="CORO1C",
        effect="unknown_protective",
        mechanism="Coronin-1C — actin remodeling protein. Computational prediction "
                  "only: may compensate cytoskeleton defects similar to PLS3.",
        magnitude=0.2,
        evidence_pmids=[],
        high_expression_effect="Predicted protective (computational only, no clinical data)",
        low_expression_effect="No predicted effect",
    ),
}

# Valid expression levels for query parameters
VALID_LEVELS = {"high", "low", "normal", "absent", "deleted"}


# ---------------------------------------------------------------------------
# Phenotype prediction engine
# ---------------------------------------------------------------------------

def _validate_smn2_copies(smn2_copies: int) -> None:
    """Validate SMN2 copy number is in expected range."""
    if not isinstance(smn2_copies, int) or smn2_copies < 0 or smn2_copies > 8:
        raise ValueError(
            f"SMN2 copy number must be an integer between 0 and 8, got {smn2_copies}"
        )


def _level_to_multiplier(level: str, modifier: ModifierGene) -> float:
    """Convert expression level to a magnitude multiplier.

    For protective modifiers (PLS3): high expression = positive effect.
    For NCALD (inverse protective): low expression = positive effect.
    For NAIP: absent/deleted = negative effect (loss of anti-apoptosis).
    """
    level = level.lower().strip()
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid expression level '{level}'. Must be one of: {VALID_LEVELS}")

    # NCALD is special: LOW expression is protective (knockdown rescues)
    if modifier.symbol == "NCALD":
        return {
            "high": -0.3,     # high NCALD worsens
            "normal": 0.0,
            "low": 1.0,       # low NCALD is protective
            "absent": 1.2,    # very low is most protective
            "deleted": 1.2,
        }.get(level, 0.0)

    # NAIP: deletion is harmful
    if modifier.symbol == "NAIP":
        return {
            "high": 0.3,       # intact NAIP is mildly protective
            "normal": 0.0,
            "low": -0.5,
            "absent": -1.0,    # homozygous deletion
            "deleted": -1.0,
        }.get(level, 0.0)

    # Default: high = full positive effect, low = no effect
    return {
        "high": 1.0,
        "normal": 0.3,
        "low": 0.0,
        "absent": 0.0,
        "deleted": 0.0,
    }.get(level, 0.0)


async def predict_phenotype(
    smn2_copies: int,
    modifiers_dict: dict[str, str],
) -> dict[str, Any]:
    """Predict SMA phenotype given SMN2 copy number and modifier gene status.

    Args:
        smn2_copies: Number of SMN2 gene copies (0-8, typically 1-5).
        modifiers_dict: Mapping of gene symbol → expression level
                        (e.g. {"PLS3": "high", "NCALD": "low"}).

    Returns:
        Dictionary with predicted_type, severity_score (0-1),
        confidence, contributing_factors, and evidence_summary.
    """
    _validate_smn2_copies(smn2_copies)

    # Handle edge case: 0 copies
    if smn2_copies == 0:
        return {
            "smn2_copies": 0,
            "predicted_type": "Type 0 (prenatal lethal)",
            "severity_score": 0.0,
            "severity_label": "lethal",
            "confidence": 0.95,
            "confidence_rationale": "Zero SMN2 copies is incompatible with postnatal survival "
                                    "regardless of modifier status.",
            "contributing_factors": [],
            "modifiers_applied": {},
            "evidence_summary": {
                "base_evidence": "Zero SMN2 copies results in complete loss of SMN protein. "
                                 "Extremely rare — most SMA patients retain at least 1 copy.",
                "modifier_notes": "No modifier can compensate for complete SMN absence.",
            },
            "evidence_pmids": [],
            "clinical_note": "Zero SMN2 copies: no modifier can rescue. "
                             "Prenatal lethal or neonatal death.",
        }

    # Clamp to known range for scoring
    capped = min(smn2_copies, 5)
    base_score = BASE_SEVERITY_SCORE.get(capped, 0.90)
    base_type = BASE_SEVERITY.get(capped, "Type IV (mild)")

    # Apply modifier effects
    contributing_factors: list[dict[str, Any]] = []
    total_modifier_shift = 0.0
    all_pmids: list[str] = []
    modifiers_applied: dict[str, dict[str, Any]] = {}

    for symbol_raw, level in modifiers_dict.items():
        symbol = symbol_raw.upper().strip()
        if symbol not in MODIFIERS:
            logger.warning("Unknown modifier gene: %s (skipped)", symbol)
            continue

        modifier = MODIFIERS[symbol]
        multiplier = _level_to_multiplier(level, modifier)
        shift = modifier.magnitude * multiplier

        factor = {
            "symbol": symbol,
            "level": level.lower(),
            "effect_type": modifier.effect,
            "mechanism": modifier.mechanism,
            "magnitude": modifier.magnitude,
            "multiplier": round(multiplier, 2),
            "shift": round(shift, 3),
            "direction": "protective" if shift > 0 else ("worsening" if shift < 0 else "neutral"),
            "evidence_pmids": modifier.evidence_pmids,
            "note": modifier.high_expression_effect if level.lower() in ("high",)
                    else modifier.low_expression_effect if level.lower() in ("low", "absent", "deleted")
                    else "Normal expression — baseline effect",
        }
        contributing_factors.append(factor)
        total_modifier_shift += shift
        all_pmids.extend(modifier.evidence_pmids)
        modifiers_applied[symbol] = {
            "level": level.lower(),
            "shift": round(shift, 3),
            "direction": factor["direction"],
        }

    # Calculate final score (clamped 0-1)
    final_score = max(0.0, min(1.0, base_score + total_modifier_shift))

    # Map final score to predicted SMA type
    predicted_type = _score_to_type(final_score)

    # Calculate confidence based on evidence quality
    confidence = _calculate_confidence(smn2_copies, contributing_factors)

    # Severity label
    severity_label = _score_to_severity_label(final_score)

    # Try to enrich with DB evidence
    db_evidence = await _fetch_modifier_evidence_from_db(
        [f["symbol"] for f in contributing_factors]
    )

    return {
        "smn2_copies": smn2_copies,
        "base_type": base_type,
        "base_severity_score": base_score,
        "modifier_shift": round(total_modifier_shift, 3),
        "predicted_type": predicted_type,
        "severity_score": round(final_score, 3),
        "severity_label": severity_label,
        "confidence": round(confidence, 3),
        "confidence_rationale": _confidence_rationale(confidence, contributing_factors),
        "contributing_factors": contributing_factors,
        "modifiers_applied": modifiers_applied,
        "evidence_summary": {
            "base_evidence": f"SMN2 copy number {smn2_copies} typically presents as {base_type} "
                             f"(baseline score {base_score:.2f}).",
            "modifier_notes": _modifier_summary(contributing_factors),
            "db_claims_found": len(db_evidence),
            "db_evidence": db_evidence[:10],  # Top 10 relevant claims
        },
        "evidence_pmids": sorted(set(all_pmids)),
        "clinical_note": _clinical_note(smn2_copies, predicted_type, contributing_factors),
    }


def _score_to_type(score: float) -> str:
    """Map a severity score (0-1) to an SMA type classification."""
    if score <= 0.15:
        return "Type I (severe)"
    elif score <= 0.35:
        return "Type I/II"
    elif score <= 0.55:
        return "Type II/III"
    elif score <= 0.75:
        return "Type III/IV"
    else:
        return "Type IV (mild)"


def _score_to_severity_label(score: float) -> str:
    """Map score to a human-readable severity label."""
    if score <= 0.15:
        return "severe"
    elif score <= 0.35:
        return "severe-moderate"
    elif score <= 0.55:
        return "moderate"
    elif score <= 0.75:
        return "moderate-mild"
    else:
        return "mild"


def _calculate_confidence(smn2_copies: int, factors: list[dict]) -> float:
    """Estimate prediction confidence based on evidence strength.

    Confidence is highest for well-characterized genotypes (2-3 copies)
    with well-evidenced modifiers (PLS3, NCALD, NAIP).
    """
    # Base confidence from SMN2 copies (well-studied range = higher confidence)
    base_conf = {1: 0.75, 2: 0.85, 3: 0.85, 4: 0.70, 5: 0.60}.get(
        min(smn2_copies, 5), 0.50
    )

    # Adjust for modifier evidence quality
    modifier_conf_adjustments: list[float] = []
    for f in factors:
        pmid_count = len(f.get("evidence_pmids", []))
        if pmid_count >= 2:
            modifier_conf_adjustments.append(0.05)   # well-evidenced
        elif pmid_count == 1:
            modifier_conf_adjustments.append(0.02)   # some evidence
        else:
            modifier_conf_adjustments.append(-0.10)  # computational only

        # Unknown protective = lower confidence
        if f.get("effect_type") == "unknown_protective":
            modifier_conf_adjustments.append(-0.08)

    total_adj = sum(modifier_conf_adjustments)
    conf = max(0.20, min(0.95, base_conf + total_adj))

    # No modifiers = moderate confidence (just SMN2 copy number)
    if not factors:
        conf = min(conf, 0.80)

    return conf


def _confidence_rationale(confidence: float, factors: list[dict]) -> str:
    """Explain why confidence is at its current level."""
    parts = []
    if confidence >= 0.80:
        parts.append("High confidence based on well-characterized SMN2–phenotype correlation")
    elif confidence >= 0.60:
        parts.append("Moderate confidence — SMN2 correlation is strong but modifier evidence varies")
    else:
        parts.append("Low confidence — limited evidence for some modifiers or unusual genotype")

    for f in factors:
        if f.get("effect_type") == "unknown_protective":
            parts.append(f"{f['symbol']}: computational prediction only, no clinical validation")
        elif not f.get("evidence_pmids"):
            parts.append(f"{f['symbol']}: no published evidence — reduces confidence")

    return ". ".join(parts) + "."


def _modifier_summary(factors: list[dict]) -> str:
    """Generate a human-readable summary of modifier contributions."""
    if not factors:
        return "No modifier genes specified — prediction based on SMN2 copy number alone."

    parts = []
    for f in factors:
        direction = f["direction"]
        symbol = f["symbol"]
        level = f["level"]
        shift = f["shift"]
        if direction == "neutral":
            parts.append(f"{symbol} ({level}): neutral effect at this expression level.")
        else:
            parts.append(
                f"{symbol} ({level}): {direction} shift of {abs(shift):.2f} — {f['mechanism']}"
            )

    return " ".join(parts)


def _clinical_note(smn2_copies: int, predicted_type: str, factors: list[dict]) -> str:
    """Generate a clinical context note."""
    protective = [f for f in factors if f["direction"] == "protective"]
    worsening = [f for f in factors if f["direction"] == "worsening"]

    note = f"With {smn2_copies} SMN2 copies, the predicted phenotype is {predicted_type}."

    if protective:
        symbols = ", ".join(f["symbol"] for f in protective)
        note += f" Protective modifiers ({symbols}) shift toward milder presentation."

    if worsening:
        symbols = ", ".join(f["symbol"] for f in worsening)
        note += f" Worsening modifiers ({symbols}) shift toward more severe presentation."

    note += (" This prediction is for research purposes only and should not be used "
             "for clinical decision-making without genetic counseling.")

    return note


async def _fetch_modifier_evidence_from_db(symbols: list[str]) -> list[dict[str, Any]]:
    """Query claims and evidence tables for modifier-related data."""
    if not symbols:
        return []

    results: list[dict[str, Any]] = []
    for symbol in symbols:
        try:
            rows = await fetch(
                """SELECT c.id, c.claim_type, c.predicate, c.confidence, c.metadata,
                          s.title AS source_title, s.external_id AS source_pmid
                   FROM claims c
                   LEFT JOIN evidence e ON e.claim_id = c.id
                   LEFT JOIN sources s ON e.source_id = s.id
                   WHERE LOWER(c.predicate) LIKE $1
                      OR CAST(c.metadata AS TEXT) LIKE $2
                   ORDER BY c.confidence DESC
                   LIMIT 10""",
                f"%{symbol.lower()}%",
                f'%"{symbol}"%',
            )
            for r in rows:
                r = dict(r)
                r["modifier_symbol"] = symbol
                results.append(r)
        except Exception as e:
            logger.warning("DB query failed for modifier %s: %s", symbol, e)

    return results


# ---------------------------------------------------------------------------
# Modifier factor listing
# ---------------------------------------------------------------------------

async def get_modifier_factors() -> list[dict[str, Any]]:
    """Return all known modifier genes with their evidence and effects.

    Enriches the static modifier data with claim counts from the database
    where available.
    """
    factors = []
    for symbol, mod in MODIFIERS.items():
        entry = asdict(mod)
        entry["evidence_count"] = len(mod.evidence_pmids)

        # Try to get DB claim count for this modifier
        try:
            row = await fetchrow(
                """SELECT COUNT(*) AS cnt FROM claims
                   WHERE LOWER(predicate) LIKE $1
                      OR CAST(metadata AS TEXT) LIKE $2""",
                f"%{symbol.lower()}%",
                f'%"{symbol}"%',
            )
            entry["db_claim_count"] = row["cnt"] if row else 0
        except Exception:
            entry["db_claim_count"] = 0

        # Try to get target info from targets table
        try:
            target_row = await fetchrow(
                "SELECT id, name, description FROM targets WHERE symbol = $1",
                symbol,
            )
            if target_row:
                entry["target_id"] = str(target_row["id"])
                entry["target_name"] = target_row["name"]
                entry["target_description"] = target_row["description"]
        except Exception:
            pass

        factors.append(entry)

    return factors


# ---------------------------------------------------------------------------
# Per-modifier evidence lookup
# ---------------------------------------------------------------------------

async def get_modifier_evidence(symbol: str) -> dict[str, Any]:
    """Get all evidence supporting a specific modifier gene's role in SMA.

    Combines static literature references with database claims.

    Args:
        symbol: Gene symbol (e.g. "PLS3", "NCALD").

    Returns:
        Dictionary with modifier info, literature references, and DB claims.
    """
    symbol = symbol.upper().strip()

    if symbol not in MODIFIERS:
        return {
            "symbol": symbol,
            "known": False,
            "error": f"'{symbol}' is not a recognized SMA modifier gene. "
                     f"Known modifiers: {', '.join(sorted(MODIFIERS.keys()))}",
        }

    modifier = MODIFIERS[symbol]
    entry = asdict(modifier)
    entry["known"] = True

    # Fetch related claims from DB
    try:
        claims = await fetch(
            """SELECT c.id, c.claim_type, c.predicate, c.confidence, c.metadata,
                      e.excerpt AS evidence_excerpt, e.method AS evidence_method,
                      s.title AS source_title, s.external_id AS source_pmid,
                      s.journal, s.pub_date, s.doi
               FROM claims c
               LEFT JOIN evidence e ON e.claim_id = c.id
               LEFT JOIN sources s ON e.source_id = s.id
               WHERE LOWER(c.predicate) LIKE $1
                  OR CAST(c.metadata AS TEXT) LIKE $2
               ORDER BY c.confidence DESC
               LIMIT 50""",
            f"%{symbol.lower()}%",
            f'%"{symbol}"%',
        )
        entry["db_claims"] = [dict(r) for r in claims]
        entry["db_claim_count"] = len(claims)
    except Exception as e:
        logger.warning("DB query failed for modifier evidence %s: %s", symbol, e)
        entry["db_claims"] = []
        entry["db_claim_count"] = 0

    # Fetch target record if exists
    try:
        target = await fetchrow(
            "SELECT id, name, target_type, description, identifiers FROM targets WHERE symbol = $1",
            symbol,
        )
        if target:
            entry["target"] = dict(target)
    except Exception:
        pass

    # Build PubMed links for convenience
    entry["pubmed_links"] = [
        f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        for pmid in modifier.evidence_pmids
    ]

    return entry
