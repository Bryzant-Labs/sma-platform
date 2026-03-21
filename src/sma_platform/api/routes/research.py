"""Research directions endpoints — cutting-edge SMA research connections."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Query

from ...core.database import fetch, fetchrow

logger = logging.getLogger(__name__)
router = APIRouter()

# 16 research directions from Querdenker + Harvard-level thinking
RESEARCH_DIRECTIONS = [
    {
        "id": "spatial-multi-omics",
        "title": "Spatial Multi-Omics",
        "category": "harvard_cutting_edge",
        "description": "Slide-seqV2 and MERFISH mapping drug penetration zones and resistant niches in SMA spinal cord tissue.",
        "connected_targets": ["SMN2", "SMN_PROTEIN"],
        "key_concepts": ["spatial transcriptomics", "slide-seq", "MERFISH", "niche", "drug penetration"],
    },
    {
        "id": "nmj-on-chip",
        "title": "NMJ-on-a-Chip",
        "category": "harvard_cutting_edge",
        "description": "Wyss Institute microphysiological systems modeling neuromuscular junction, EV drug delivery, and retrograde muscle→nerve signaling.",
        "connected_targets": ["NMJ_MATURATION", "PLS3"],
        "key_concepts": ["organ-on-chip", "neuromuscular junction", "extracellular vesicle", "retrograde signal", "microphysiological"],
    },
    {
        "id": "bioelectric-reprogramming",
        "title": "Bioelectric Reprogramming",
        "category": "harvard_cutting_edge",
        "description": "Michael Levin's Vmem manipulation and electroceuticals for activating endogenous regeneration in motor neurons.",
        "connected_targets": ["ANK3", "NCALD"],
        "key_concepts": ["bioelectric", "Vmem", "ion channel", "electroceutical", "satellite cell", "Michael Levin"],
    },
    {
        "id": "epigenetic-dimming",
        "title": "Epigenetic Dimming",
        "category": "querdenker_gemini",
        "description": "dCas9/CRISPRi silencing disease-causing genes without DNA cuts, modeled on FSHD/DUX4 approach for SMN2 upregulation.",
        "connected_targets": ["DNMT3B", "SMN2"],
        "key_concepts": ["CRISPRi", "dCas9", "epigenetic", "DUX4", "chromatin remodeling", "methylation"],
    },
    {
        "id": "bear-hibernation",
        "title": "Bear Hibernation / Muscle Preservation",
        "category": "querdenker_gemini",
        "description": "Hibernating bears preserve muscle mass through SUMOylation and protein homeostasis — mechanisms potentially applicable to SMA.",
        "connected_targets": ["UBA1", "SPATA18", "CAST"],
        "key_concepts": ["hibernation", "torpor", "muscle preservation", "SUMOylation", "protein homeostasis"],
    },
    {
        "id": "ndrg1-atrofish",
        "title": "NDRG1 / Atrofish / Dormancy",
        "category": "harvard_cutting_edge",
        "description": "Cell dormancy and quiescence as neuroprotection strategy, inspired by zebrafish survivorship and NDRG1 stress response.",
        "connected_targets": ["LDHA", "SPATA18", "NCALD"],
        "key_concepts": ["NDRG1", "dormancy", "quiescence", "zebrafish", "survivorship", "stress response"],
    },
    {
        "id": "multisystem-sma",
        "title": "SMA as Multisystem Disease",
        "category": "harvard_cutting_edge",
        "description": "Lee Rubin (Harvard) — liver/metabolic involvement in SMA suggests combination therapy targeting both neuronal and systemic pathways.",
        "connected_targets": ["MTOR_PATHWAY", "LDHA", "SMN_PROTEIN"],
        "key_concepts": ["multisystem", "liver", "metabolic", "energy metabolism", "fatty acid", "systemic"],
    },
    {
        "id": "ecm-engineering",
        "title": "ECM Engineering / Fibrosis Reversal",
        "category": "querdenker_gemini",
        "description": "Targeting extracellular matrix remodeling and fibrosis in SMA muscle, including SULF1/CD44 pathway connections.",
        "connected_targets": ["SULF1", "CD44", "CTNNA1", "GALNT6"],
        "key_concepts": ["extracellular matrix", "fibrosis", "decellularized", "MMP", "SULF1", "CD44"],
    },
    {
        "id": "cross-species-regeneration",
        "title": "Cross-Species Regeneration",
        "category": "querdenker_gemini",
        "description": "Axolotl and zebrafish splicing programs for regeneration — identifying silenced regeneration genes in human SMA motor neurons.",
        "connected_targets": ["PLS3", "SMN2"],
        "key_concepts": ["axolotl", "regeneration", "splicing program", "newt", "salamander", "zebrafish motor neuron"],
    },
    {
        "id": "dual-target-molecules",
        "title": "Dual-Target Molecules",
        "category": "harvard_cutting_edge",
        "description": "Designing compounds that modify SMN2 splicing AND influence ion channels or anti-fibrotic pathways simultaneously.",
        "connected_targets": ["SMN2", "ANK3"],
        "key_concepts": ["dual target", "bifunctional", "multitarget", "polypharmacology", "SMN2 splicing modifier"],
    },
    {
        "id": "rna-decoy-sponge",
        "title": "RNA Decoy / Sponge Strategy",
        "category": "unconventional",
        "description": "Sequestering hnRNP A1 via RNA decoys to prevent SMN2 exon 7 skipping — inspired by splicing factor competition models.",
        "connected_targets": ["SMN2"],
        "key_concepts": ["RNA decoy", "sponge", "hnRNP", "splicing factor", "decoy oligonucleotide"],
    },
    {
        "id": "mitochondrial-overdrive",
        "title": "Mitochondrial Overdrive / PGC-1alpha",
        "category": "unconventional",
        "description": "Bioenergetic rescue via PGC-1alpha activation and NAD+ supplementation to compensate for SMN-dependent metabolic deficits.",
        "connected_targets": ["MTOR_PATHWAY", "LDHA"],
        "key_concepts": ["PGC-1alpha", "mitochondrial", "NAD+", "bioenergetic", "AMPK", "energy metabolism"],
    },
    {
        "id": "dubtacs",
        "title": "DUBTACs — Protein Stabilization",
        "category": "unconventional",
        "description": "Reverse PROTACs: targeted deubiquitination to stabilize SMN protein and prevent degradation.",
        "connected_targets": ["UBA1", "SMN_PROTEIN"],
        "key_concepts": ["DUBTAC", "deubiquitin", "PROTAC", "ubiquitin", "protein stabilization", "degradation"],
    },
    {
        "id": "mechanotransduction",
        "title": "Mechanotransduction / Vibration Therapy",
        "category": "unconventional",
        "description": "Mechanical stimulation activating HSP chaperones for neuroprotection — whole body vibration as adjunct SMA therapy.",
        "connected_targets": ["PLS3", "NMJ_MATURATION"],
        "key_concepts": ["mechanotransduction", "vibration", "HSP", "chaperone", "mechanical stimulation"],
    },
    {
        "id": "engineered-probiotics",
        "title": "Engineered Probiotics / Microbiome",
        "category": "unconventional",
        "description": "Gut-brain axis modulation via engineered probiotics producing butyrate/HDAC inhibitors for systemic SMN upregulation.",
        "connected_targets": ["SMN2", "MTOR_PATHWAY"],
        "key_concepts": ["probiotic", "microbiome", "gut-brain", "butyrate", "HDAC", "living therapeutic"],
    },
    {
        "id": "spinal-cord-stimulation",
        "title": "Spinal Cord Stimulation in SMA",
        "category": "unconventional",
        "description": (
            "Epidural spinal cord stimulation targeting proprioceptive circuits to reactivate "
            "dormant motor neurons — Capogrosso (Pittsburgh) / Simon (Leipzig) / ESPACE Europe. "
            "Sub-motor threshold stimulation activates Ia afferents, re-establishing proprioceptive-motor "
            "circuit. Pilot results show 'spectacular' motor improvement after 1 month of 2h/day stimulation."
        ),
        "connected_targets": ["NMJ_MATURATION", "ANK3", "STMN2"],
        "key_concepts": [
            "epidural stimulation", "spinal cord stimulation", "proprioception",
            "Capogrosso", "Ia afferent", "H-reflex", "motor neuron reactivation",
            "ESPACE consortium", "neuromodulation",
        ],
        "researcher": "Marco Capogrosso (University of Pittsburgh)",
        "collaborators": ["ESPACE Europe consortium", "Christian Simon (Leipzig)"],
    },
    {
        "id": "proprioceptive-circuit",
        "title": "Proprioceptive Circuit Dysfunction",
        "category": "circuit_biology",
        "description": (
            "SMA is increasingly recognized as a circuit disease, not just motor neuron death. "
            "Mentis lab (Columbia) showed Ia afferent synapse loss on motor neurons precedes motor neuron "
            "degeneration. DRG neuron dysfunction, disrupted sensory-motor connectivity, and proprioceptive "
            "innervation specificity loss contribute to motor circuit failure. Motor neuron counting varies "
            "0-80% across labs — methodology problems confound disease understanding. Therapeutic window "
            "may be larger than thought if circuit rescue happens before cell death."
        ),
        "connected_targets": ["SMN1", "SMN2", "STMN2", "NMJ_MATURATION", "BDNF"],
        "key_concepts": [
            "proprioception", "Ia afferent", "DRG neuron", "sensory-motor circuit",
            "Mentis lab", "non-cell-autonomous", "circuit disease", "motor neuron counting",
            "NMJ vulnerability", "glial contribution",
        ],
        "researcher": "George Mentis (Columbia University)",
        "collaborators": ["Christian Simon (Leipzig)", "Prof. Schoeneberg"],
    },
    {
        "id": "actin-rock-cofilin-pathway",
        "title": "Actin-ROCK-Cofilin Pathway / Fasudil",
        "category": "drug_repurposing",
        "description": (
            "SMN directly interacts with Profilin 1 (PFN1) in motor neurons (PMID 26401655). "
            "Pathway: SMN→PFN1→RhoA→ROCK→LIMK→CFL2→actin-cofilin rods→TDP-43 aggregation. "
            "ROCK1/2 elevated in SMNΔ7 mice, phospho-cofilin elevated in SMA models + patient fibroblasts. "
            "Fasudil (ROCK inhibitor, approved in Japan/China for stroke) crosses BBB, Phase 2 in ALS "
            "(NCT03792490). Nobody has tested ROCK inhibitors in SMA — first-in-field opportunity. "
            "MDI-117740 (LIMK inhibitor, published 2025) is more specific alternative."
        ),
        "connected_targets": ["PFN1", "CFL2", "ROCK2", "CORO1C", "PLS3", "TARDBP"],
        "key_concepts": [
            "Fasudil", "ROCK inhibitor", "cofilin phosphorylation", "actin-cofilin rods",
            "TDP-43", "LIMK", "MDI-117740", "profilin", "SMA-ALS convergence",
            "drug repurposing", "BBB penetration",
        ],
        "researcher": "Novel — no lab currently pursuing this",
        "collaborators": [],
    },
]

DIRECTION_MAP = {d["id"]: d for d in RESEARCH_DIRECTIONS}


@router.get("/research/directions")
async def list_research_directions(
    category: str | None = Query(default=None, description="Filter by category"),
):
    """List all 16 cutting-edge SMA research directions with connected targets."""
    results = RESEARCH_DIRECTIONS
    if category:
        results = [d for d in results if d["category"] == category]

    # Add target counts
    enriched = []
    for d in results:
        enriched.append({
            **d,
            "target_count": len(d["connected_targets"]),
            "concept_count": len(d["key_concepts"]),
        })

    categories = {}
    for d in RESEARCH_DIRECTIONS:
        cat = d["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "total": len(enriched),
        "categories": categories,
        "directions": enriched,
    }


@router.get("/research/directions/{direction_id}")
async def get_research_direction(direction_id: str):
    """Deep-dive into a research direction with connected targets, claims, and hypotheses."""
    direction = DIRECTION_MAP.get(direction_id)
    if not direction:
        raise HTTPException(404, f"Research direction '{direction_id}' not found")

    result = {**direction}

    # Look up connected targets from DB
    targets = []
    for symbol in direction["connected_targets"]:
        t = await fetchrow(
            "SELECT id, symbol, name, target_type, description FROM targets WHERE symbol = $1",
            symbol,
        )
        if t:
            t = dict(t)
            t["id"] = str(t["id"])
            targets.append(t)
    result["targets"] = targets
    target_ids = [t["id"] for t in targets]

    # Find claims matching key_concepts
    claims = []
    seen_claim_ids = set()
    for concept in direction["key_concepts"][:8]:
        rows = await fetch(
            """SELECT id, predicate, claim_type, confidence, subject_id
               FROM claims
               WHERE LOWER(predicate) LIKE $1
               ORDER BY confidence DESC
               LIMIT 10""",
            f"%{concept.lower()}%",
        )
        for row in rows:
            r = dict(row)
            cid = str(r["id"])
            if cid not in seen_claim_ids:
                seen_claim_ids.add(cid)
                r["id"] = cid
                r["subject_id"] = str(r["subject_id"]) if r.get("subject_id") else None
                claims.append(r)

    result["claims"] = claims[:50]
    result["claim_count"] = len(claims)

    # Find hypotheses linked to connected targets
    # Full UUIDs are 36 chars — LIKE matching is safe (no partial collisions)
    hypotheses = []
    for tid in target_ids:
        rows = await fetch(
            """SELECT id, title, description, confidence, status, metadata
               FROM hypotheses
               WHERE CAST(metadata AS TEXT) LIKE $1
               ORDER BY confidence DESC
               LIMIT 10""",
            f'%"{tid}"%',
        )
        for row in rows:
            r = dict(row)
            r["id"] = str(r["id"])
            if isinstance(r.get("metadata"), str):
                try:
                    r["metadata"] = json.loads(r["metadata"])
                except json.JSONDecodeError:
                    pass
            hypotheses.append(r)

    result["hypotheses"] = hypotheses
    result["hypothesis_count"] = len(hypotheses)

    # Find graph edges involving connected targets
    edge_count = 0
    if target_ids:
        for tid in target_ids:
            row = await fetchrow(
                """SELECT COUNT(*) as c FROM graph_edges
                   WHERE CAST(src_id AS TEXT) = $1 OR CAST(dst_id AS TEXT) = $1""",
                tid,
            )
            if row:
                edge_count += dict(row)["c"]
    result["edge_count"] = edge_count

    return result


@router.get("/research/spinal-stimulation")
async def spinal_stimulation():
    """Spinal cord stimulation for SMA — Capogrosso/Simon approach."""
    from ...reasoning.spinal_stimulation import get_stimulation_info
    return get_stimulation_info()


@router.get("/research/links")
async def list_research_links(
    category: str | None = Query(default=None, description="Filter by category"),
    limit: int = Query(default=100, ge=1, le=500),
):
    """List curated research links from the research_links table."""
    try:
        if category:
            rows = await fetch(
                """SELECT id, title, url, category, description, source_type, added_at
                   FROM research_links
                   WHERE category = $1
                   ORDER BY added_at DESC
                   LIMIT $2""",
                category, limit,
            )
        else:
            rows = await fetch(
                """SELECT id, title, url, category, description, source_type, added_at
                   FROM research_links
                   ORDER BY added_at DESC
                   LIMIT $1""",
                limit,
            )

        links = []
        for row in rows:
            r = dict(row)
            r["id"] = str(r["id"])
            links.append(r)

        categories = {}
        for link in links:
            cat = link.get("category", "uncategorized")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total": len(links),
            "categories": categories,
            "links": links,
        }
    except Exception as e:
        if "does not exist" in str(e) or "no such table" in str(e):
            return {"total": 0, "categories": {}, "links": [], "note": "research_links table not yet created"}
        raise
