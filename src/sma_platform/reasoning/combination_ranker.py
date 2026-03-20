"""Therapy Combination Ranking — which drug combinations might work best.

Scores combinations based on:
1. Mechanistic complementarity (do they target different pathways?)
2. Evidence convergence (how strong is the evidence for each component?)
3. Target coverage (how many SMA-relevant pathways are covered?)
4. Clinical feasibility (are both components approved/in trials?)
"""

from __future__ import annotations
import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

# Known SMA therapeutic approaches with their mechanisms
THERAPIES = [
    {
        "name": "Nusinersen (Spinraza)",
        "mechanism": "ASO — SMN2 exon 7 inclusion",
        "targets": ["SMN2"],
        "pathway": "splicing",
        "route": "intrathecal",
        "status": "approved",
        "strength": 0.95,
    },
    {
        "name": "Risdiplam (Evrysdi)",
        "mechanism": "Small molecule splicing modifier",
        "targets": ["SMN2"],
        "pathway": "splicing",
        "route": "oral",
        "status": "approved",
        "strength": 0.90,
    },
    {
        "name": "Onasemnogene (Zolgensma)",
        "mechanism": "AAV9 SMN1 gene replacement",
        "targets": ["SMN1"],
        "pathway": "gene_therapy",
        "route": "IV (one-time)",
        "status": "approved",
        "strength": 0.92,
    },
    {
        "name": "Apitegromab",
        "mechanism": "Anti-myostatin antibody",
        "targets": ["NMJ_MATURATION"],
        "pathway": "muscle_growth",
        "route": "IV",
        "status": "phase_3",
        "strength": 0.70,
    },
    {
        "name": "Reldesemtiv",
        "mechanism": "Fast skeletal muscle troponin activator",
        "targets": ["NMJ_MATURATION"],
        "pathway": "muscle_function",
        "route": "oral",
        "status": "phase_3",
        "strength": 0.65,
    },
    {
        "name": "NCALD ASO",
        "mechanism": "ASO reducing NCALD expression",
        "targets": ["NCALD"],
        "pathway": "modifier",
        "route": "intrathecal",
        "status": "preclinical",
        "strength": 0.50,
    },
    {
        "name": "PLS3 enhancer",
        "mechanism": "PLS3 overexpression/activation",
        "targets": ["PLS3"],
        "pathway": "modifier",
        "route": "TBD",
        "status": "preclinical",
        "strength": 0.45,
    },
    {
        "name": "HDAC inhibitor (Givinostat)",
        "mechanism": "Epigenetic SMN2 upregulation",
        "targets": ["SMN2", "DNMT3B"],
        "pathway": "epigenetic",
        "route": "oral",
        "status": "repurposing_candidate",
        "strength": 0.55,
    },
    {
        "name": "Riluzole",
        "mechanism": "Glutamate inhibitor, neuroprotection",
        "targets": ["NMJ_MATURATION"],
        "pathway": "neuroprotection",
        "route": "oral",
        "status": "repurposing_candidate",
        "strength": 0.40,
    },
    {
        "name": "p53 inhibitor",
        "mechanism": "Block p53-mediated motor neuron death",
        "targets": ["TP53"],
        "pathway": "apoptosis",
        "route": "TBD",
        "status": "preclinical",
        "strength": 0.45,
    },
]


def score_combination(therapy_a: dict, therapy_b: dict) -> dict[str, Any]:
    """Score a two-drug combination."""
    # 1. Mechanistic complementarity (different pathways = better)
    same_pathway = therapy_a["pathway"] == therapy_b["pathway"]
    complementarity = 0.3 if same_pathway else 1.0

    # 2. Target coverage (unique targets)
    all_targets = set(therapy_a["targets"] + therapy_b["targets"])
    coverage = min(1.0, len(all_targets) / 4)  # 4+ targets = max

    # 3. Evidence strength (geometric mean)
    evidence = math.sqrt(therapy_a["strength"] * therapy_b["strength"])

    # 4. Clinical feasibility
    status_scores = {
        "approved": 1.0,
        "phase_3": 0.7,
        "phase_2": 0.5,
        "preclinical": 0.3,
        "repurposing_candidate": 0.4,
        "TBD": 0.2,
    }
    feasibility = (
        status_scores.get(therapy_a["status"], 0.2)
        + status_scores.get(therapy_b["status"], 0.2)
    ) / 2

    # 5. Route compatibility (oral+oral or oral+IT > IT+IT)
    routes = {therapy_a["route"], therapy_b["route"]}
    if "oral" in routes and len(routes) > 1:
        route_bonus = 0.1
    elif routes == {"oral"}:
        route_bonus = 0.15
    else:
        route_bonus = 0.0

    # Composite score
    composite = (
        0.30 * complementarity
        + 0.25 * coverage
        + 0.25 * evidence
        + 0.15 * feasibility
        + 0.05
        + route_bonus
    )

    return {
        "therapy_a": therapy_a["name"],
        "therapy_b": therapy_b["name"],
        "composite_score": round(composite, 3),
        "complementarity": round(complementarity, 3),
        "target_coverage": round(coverage, 3),
        "evidence_strength": round(evidence, 3),
        "clinical_feasibility": round(feasibility, 3),
        "combined_targets": list(all_targets),
        "combined_pathways": list({therapy_a["pathway"], therapy_b["pathway"]}),
        "routes": f"{therapy_a['route']} + {therapy_b['route']}",
    }


def rank_all_combinations() -> list[dict]:
    """Rank all possible two-drug combinations."""
    combos = []
    for i, a in enumerate(THERAPIES):
        for b in THERAPIES[i + 1 :]:
            combo = score_combination(a, b)
            combos.append(combo)
    combos.sort(key=lambda x: x["composite_score"], reverse=True)
    return combos
