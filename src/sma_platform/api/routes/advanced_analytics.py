"""Advanced Analytics API routes (Phase 7.2–7.5).

Combines:
- Phase 7.2: Cross-Species Regeneration Signatures
- Phase 7.3: NMJ Retrograde Signaling  ← PostgreSQL-backed
- Phase 7.4: Multisystem SMA
- Phase 7.5: Bioelectric Reprogramming → routes/bioelectric.py (DB-driven)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from ...core.database import execute_script, fetch, fetchval
from ...reasoning.regeneration_signatures import (
    get_pathway_comparisons,
    get_regeneration_genes,
    identify_silenced_programs,
)
from ...reasoning.multisystem_sma import (
    analyze_multisystem_sma,
    get_combination_therapies,
    get_energy_budget,
    get_organ_systems,
)


logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Phase 7.3: NMJ table DDL (idempotent)
# ---------------------------------------------------------------------------

_NMJ_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS nmj_signals (
    id          SERIAL PRIMARY KEY,
    signal_name TEXT    NOT NULL UNIQUE,
    molecule_type TEXT  NOT NULL,
    source      TEXT    NOT NULL,
    target      TEXT    NOT NULL,
    sma_status  TEXT    NOT NULL CHECK (sma_status IN ('reduced','absent','increased','normal')),
    normal_function TEXT NOT NULL,
    therapeutic_strategy TEXT,
    therapeutic_potential NUMERIC(3,2) NOT NULL DEFAULT 0.0,
    evidence_strength TEXT NOT NULL DEFAULT 'emerging'
        CHECK (evidence_strength IN ('strong','moderate','emerging')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nmj_signals_status ON nmj_signals(sma_status);

CREATE TABLE IF NOT EXISTS nmj_ev_cargo (
    id          SERIAL PRIMARY KEY,
    cargo_name  TEXT   NOT NULL UNIQUE,
    cargo_type  TEXT   NOT NULL CHECK (cargo_type IN ('mirna','protein','mrna','lipid')),
    function    TEXT   NOT NULL,
    sma_context TEXT   NOT NULL,
    delivery_mechanism TEXT NOT NULL DEFAULT 'Engineered EV loading',
    feasibility NUMERIC(3,2) NOT NULL DEFAULT 0.0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nmj_chip_models (
    id              SERIAL PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    cell_types      TEXT[]  NOT NULL DEFAULT '{}',
    readouts        TEXT[]  NOT NULL DEFAULT '{}',
    trl             SMALLINT NOT NULL CHECK (trl BETWEEN 1 AND 9),
    supplier        TEXT,
    validation_assays TEXT[] NOT NULL DEFAULT '{}',
    sma_modeling    TEXT,
    cost_per_chip   TEXT,
    throughput      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nmj_chips_trl ON nmj_chip_models(trl DESC);
"""

_NMJ_SEED_SQL = """
-- nmj_signals seed data (skip if already present)
INSERT INTO nmj_signals (signal_name, molecule_type, source, target, sma_status, normal_function, therapeutic_strategy, therapeutic_potential, evidence_strength)
VALUES
  ('BDNF (muscle-derived)',    'protein',  'muscle fiber',          'motor neuron soma',       'reduced',  'Activity-dependent release from muscle; binds TrkB on MN axon terminals; retrograde transport promotes MN survival via PI3K/Akt and MAPK/ERK.', 'Muscle-specific BDNF overexpression or engineered EV delivery of BDNF to NMJ.',                              0.80, 'strong'),
  ('NT-4/5',                   'protein',  'muscle fiber',          'motor neuron soma',       'reduced',  'Activity-dependent neurotrophin; supports MN survival at fast-fatigable NMJ subtypes most vulnerable in SMA.',              'Recombinant NT-4/5 supplementation targeted at fast-fatigable MN subtypes.',                                  0.65, 'moderate'),
  ('GDNF',                     'protein',  'muscle fiber',          'motor neuron soma',       'reduced',  'Potent MN survival factor; binds GFRalpha1/RET on MN terminals; retrograde survival signaling via lipid raft endocytosis.',   'GDNF gene therapy to muscle; sustained local delivery to NMJ.',                                               0.75, 'strong'),
  ('Gdf5/BMP (Glass bottom boat)', 'protein', 'muscle fiber',        'presynaptic terminal',   'reduced',  'BMP retrograde signal maintains presynaptic structure; Gbb in Drosophila, Gdf5 in vertebrates; regulates synaptic homeostasis.', 'Recombinant Gdf5 supplementation or BMP pathway activation in muscle.',                                      0.60, 'strong'),
  ('Laminin-beta2 (LAMB2)',     'protein',  'muscle fiber',          'presynaptic terminal',   'reduced',  'Synaptic basal lamina component; organizes presynaptic active zones and calcium channel clustering at NMJ.', 'LAMB2 supplementation or AAV-mediated restoration in muscle basement membrane.',                                  0.50, 'moderate'),
  ('Muscle-derived EVs (exosomes)', 'exosome', 'muscle fiber',       'motor neuron soma',      'reduced',  'Muscle exosomes carry miRNAs (miR-206, miR-1) and HSP70 that promote MN survival.',                        'Engineered EVs loaded with miR-206 + BDNF + agrin for NMJ-targeted delivery.',                                 0.70, 'emerging'),
  ('Agrin',                    'protein',  'motor neuron terminal',  'muscle fiber (NMJ)',     'reduced',  'Neural agrin clusters AChRs via MuSK/LRP4; in SMA agrin is reduced leading to AChR dispersal and NMJ denervation.', 'Agrin mimetic (Z+ agrin fragment) injection or AAV-agrin to rescue NMJ integrity.',                              0.75, 'strong'),
  ('Endocannabinoids (2-AG)',   'lipid',    'muscle fiber',          'presynaptic terminal',   'normal',   'Lipid retrograde messenger; modulates presynaptic release probability at NMJ via CB1 receptor.',             'Not a primary target; modulation could tune synaptic homeostasis in advanced disease.',                         0.40, 'emerging'),
  ('Schwann cell-derived VEGF','protein',  'terminal Schwann cell', 'motor neuron terminal',   'reduced',  'Terminal Schwann cells sense synaptic activity and release VEGF to maintain NMJ vasculature and presynaptic health.', 'VEGF-A supplementation or Schwann cell activation to restore glial NMJ support.',                               0.55, 'moderate'),
  ('FGF-BP1',                  'protein',  'muscle fiber',          'presynaptic terminal',   'reduced',  'Concentrates FGF signaling at NMJ; maintains presynaptic terminal integrity and synapse stability.',         'FGF-BP1 recombinant protein delivery or expression modulation at NMJ.',                                       0.50, 'moderate')
ON CONFLICT (signal_name) DO NOTHING;

-- nmj_ev_cargo seed data
INSERT INTO nmj_ev_cargo (cargo_name, cargo_type, function, sma_context, delivery_mechanism, feasibility)
VALUES
  ('miR-206',      'mirna',   'NMJ maturation signal; promotes AChR clustering and NMJ integrity.',  'Downregulated in SMA muscle; restoring it delays denervation.', 'Engineered EV electroporation with miR-206 mimic; muscle-tropic EVs.',                0.75),
  ('miR-1',        'mirna',   'Muscle differentiation and ion channel regulation.',                   'Reduced in SMA; affects muscle fiber identity.',                  'EV loading with miR-1 mimic; co-delivered with miR-206.',                             0.70),
  ('miR-133a',     'mirna',   'Muscle proliferation/differentiation balance.',                        'Altered in SMA; disrupts satellite cell homeostasis.',            'EV-encapsulated miR-133a-3p; anti-miR-133a-3p for muscle rescue.',                    0.65),
  ('HSP70',        'protein', 'Chaperone; protein quality control; anti-apoptotic in MNs.',           'Reduced MN protection in SMA; HSP70 overexpression extends survival in mouse models.', 'EV surface-displayed or luminal HSP70; recombinant delivery.', 0.60),
  ('SMN mRNA',     'mrna',    'Direct SMN protein production in target cells.',                       'Absent (root cause of SMA); mRNA delivery bypasses splicing defect.', 'Modified mRNA in lipid NPs or EVs; short half-life requires repeat dosing.', 0.55),
  ('BDNF protein', 'protein', 'Neuroprotective survival signaling via TrkB.',                         'Reduced at SMA NMJ; low endogenous muscle production.',           'Engineered EV luminal BDNF; sustained release from hydrogel depot at NMJ.',          0.70),
  ('Agrin fragment','protein','AChR clustering and NMJ stability via MuSK/LRP4.',                    'Reduced agrin in SMA leads to NMJ fragmentation.',                'Z+ agrin mini-agrin fragment encapsulated in EVs; local injection.',                  0.65)
ON CONFLICT (cargo_name) DO NOTHING;

-- nmj_chip_models seed data
INSERT INTO nmj_chip_models (name, cell_types, readouts, trl, supplier, validation_assays, sma_modeling, cost_per_chip, throughput)
VALUES
  ('NMJ-on-Chip (2-compartment)',
   ARRAY['iPSC-MNs', 'C2C12 myotubes', 'Matrigel channel'],
   ARRAY['Contraction force', 'AChR clustering', 'Calcium imaging', 'Electrophysiology'],
   5,
   'Hesperos / custom academic fab',
   ARRAY['Immunofluorescence BTX/AChR', 'MEA recording', 'Twitching frequency'],
   'SMA patient iPSC-derived MNs show reduced NMJ formation and contraction force.',
   '$50-100',
   'Low (10-20 chips/week)'),
  ('Motor Unit-on-Chip (3-compartment)',
   ARRAY['iPSC-MNs', 'Primary myofibers', 'Schwann cells', 'Microfluidic gradient'],
   ARRAY['Axon growth', 'Myelination', 'NMJ maturation', 'Retrograde transport'],
   4,
   'Custom academic / Mimetas',
   ARRAY['MBP staining (myelination)', 'Retrograde dye tracing', 'NMJ morphometry'],
   'Models complete motor unit with glial support — captures Schwann cell defects in SMA.',
   '$100-200',
   'Low (5-10 chips/week)'),
  ('High-throughput NMJ plate (optogenetic)',
   ARRAY['iPSC-MNs (ChR2)', 'Engineered muscle strips', '96-well format'],
   ARRAY['Light-evoked contraction', 'Force measurement', 'Compound screening'],
   6,
   'Acuitas / AxoSim / custom',
   ARRAY['Optogenetic contraction assay', 'Force transducer', 'CaFlux kinetics'],
   'Optogenetic activation isolates muscle vs neural defects; SMA compounds testable at scale.',
   '$20-40',
   'High (96 conditions/plate)')
ON CONFLICT (name) DO NOTHING;
"""

_nmj_tables_ensured = False


async def _ensure_nmj_tables() -> None:
    """Create NMJ tables and seed data if not yet done this process lifetime."""
    global _nmj_tables_ensured
    if _nmj_tables_ensured:
        return
    try:
        await execute_script(_NMJ_TABLES_SQL)
        await execute_script(_NMJ_SEED_SQL)
        _nmj_tables_ensured = True
        logger.info("NMJ tables ensured (created or already exist).")
    except Exception as exc:
        logger.warning("_ensure_nmj_tables error (may already exist): %s", exc)
        _nmj_tables_ensured = True


# ---------------------------------------------------------------------------
# Phase 7.2: Regeneration Signatures
# ---------------------------------------------------------------------------

@router.get("/regen/genes")
async def regeneration_genes():
    """Get regeneration-associated genes with SMA comparison."""
    return get_regeneration_genes()


@router.get("/regen/pathways")
async def pathway_comparisons():
    """Compare regeneration pathways with SMA state."""
    return get_pathway_comparisons()


@router.get("/regen/silenced")
async def silenced_programs():
    """Identify silenced regeneration programs in human SMA."""
    return identify_silenced_programs()


# ---------------------------------------------------------------------------
# Phase 7.3: NMJ Retrograde Signaling — DB-backed
# ---------------------------------------------------------------------------

@router.get("/nmj/signals")
async def retrograde_signals() -> dict[str, Any]:
    """Get retrograde signaling molecules at the NMJ (PostgreSQL-backed)."""
    await _ensure_nmj_tables()
    rows = await fetch(
        """SELECT signal_name, molecule_type, source, target, sma_status,
                  normal_function, therapeutic_strategy, therapeutic_potential,
                  evidence_strength
           FROM nmj_signals
           ORDER BY therapeutic_potential DESC"""
    )
    signals = [dict(r) for r in rows]
    by_status: dict[str, list[str]] = {"reduced": [], "absent": [], "increased": [], "normal": []}
    for s in signals:
        key = s["sma_status"]
        if key in by_status:
            by_status[key].append(s["signal_name"])

    total = len(signals)
    reduced_count = len(by_status["reduced"])
    happy_score = round(reduced_count / total, 2) if total else 0.0

    return {
        "total_signals": total,
        "signals": signals,
        "status_summary": {k: len(v) for k, v in by_status.items()},
        "top_therapeutic": signals[:5],
        "happy_muscle_score": happy_score,
        "insight": (
            f"{reduced_count}/{total} retrograde signals are reduced in SMA, supporting the "
            "'happy muscle → surviving neuron' hypothesis. The NMJ actively sustains motor neurons "
            "through BDNF, GDNF, and EV-mediated retrograde signaling. "
            "Restoring muscle health could create a positive feedback loop for MN survival."
        ),
    }


@router.get("/nmj/ev-cargo")
async def ev_cargo() -> dict[str, Any]:
    """Get EV therapeutic cargo options for NMJ delivery (PostgreSQL-backed)."""
    await _ensure_nmj_tables()
    rows = await fetch(
        """SELECT cargo_name, cargo_type, function, sma_context, delivery_mechanism, feasibility
           FROM nmj_ev_cargo
           ORDER BY feasibility DESC"""
    )
    cargo = [dict(r) for r in rows]
    return {
        "total_cargo": len(cargo),
        "cargo": cargo,
        "top_feasible": cargo[:3],
        "insight": (
            "Engineered EVs loaded with miR-206 + BDNF + agrin fragments could serve as a "
            "'care package' for denervating NMJs. Muscle-derived EVs naturally home to the NMJ, "
            "providing a built-in targeting mechanism for retrograde trophic delivery."
        ),
    }


@router.get("/nmj/chip-models")
async def chip_models() -> dict[str, Any]:
    """Get organ-on-chip models for NMJ validation (PostgreSQL-backed)."""
    await _ensure_nmj_tables()
    rows = await fetch(
        """SELECT name, cell_types, readouts, trl, supplier, validation_assays,
                  sma_modeling, cost_per_chip, throughput
           FROM nmj_chip_models
           ORDER BY trl DESC"""
    )
    models = [dict(r) for r in rows]
    recommended = models[0] if models else None
    return {
        "total_models": len(models),
        "models": models,
        "recommended": recommended,
        "insight": (
            "The high-throughput optogenetic NMJ plate (TRL 6) is closest to drug screening "
            "readiness. For mechanistic studies of retrograde signaling, the 3-compartment "
            "Motor Unit-on-Chip with Schwann cells is ideal but lower throughput."
        ),
    }


@router.get("/nmj/happy-muscle")
async def happy_muscle() -> dict[str, Any]:
    """Full analysis of the 'happy muscle → surviving neuron' hypothesis (DB-backed)."""
    await _ensure_nmj_tables()

    signals_resp = await retrograde_signals()
    ev_resp = await ev_cargo()
    chips_resp = await chip_models()

    reduced = [s for s in signals_resp["signals"] if s["sma_status"] == "reduced"]
    avg_potential = (
        sum(float(s["therapeutic_potential"]) for s in reduced) / len(reduced)
        if reduced else 0.0
    )

    return {
        "hypothesis": (
            "Improving muscle health restores retrograde trophic signaling to motor neurons, "
            "creating a positive feedback loop that slows or halts motor neuron degeneration."
        ),
        "evidence_for": [
            f"{len(reduced)}/{signals_resp['total_signals']} retrograde signals reduced in SMA",
            "NMJ denervation precedes MN death (Kariya 2008)",
            "Myostatin inhibition improves muscle + extends survival in SMA mice",
            "Exercise (mild) improves outcomes in SMA patients",
            "Muscle-specific SMN restoration partially rescues motor neurons",
        ],
        "evidence_against": [
            "Cell-autonomous MN death occurs even with healthy muscle in severe SMA",
            "Some SMA types have normal muscle but still lose MNs",
            "SMN is required cell-autonomously in motor neurons",
        ],
        "hypothesis_score": round(avg_potential, 2),
        "signals": signals_resp,
        "ev_delivery": ev_resp,
        "validation_chips": chips_resp,
        "combination_strategy": {
            "approach": "SMN restoration + muscle support + retrograde enhancement",
            "components": [
                "Nusinersen/risdiplam (SMN restoration in MNs)",
                "Apitegromab (anti-myostatin, muscle mass)",
                "EV-BDNF (retrograde trophic support)",
                "Exercise therapy (activity-dependent NMJ maintenance)",
            ],
            "rationale": "Attacking SMA from both sides — neuron AND muscle — maximizes therapeutic effect",
        },
    }


# ---------------------------------------------------------------------------
# Phase 7.4: Multisystem SMA
# ---------------------------------------------------------------------------

@router.get("/multisystem/organs")
async def organ_systems():
    """Get organ systems affected in SMA beyond motor neurons."""
    return get_organ_systems()


@router.get("/multisystem/combinations")
async def combination_therapies():
    """Get combination therapy strategies for multisystem SMA."""
    return get_combination_therapies()


@router.get("/multisystem/energy")
async def energy_budget():
    """Get energy budget analysis for SMA motor neurons."""
    return get_energy_budget()


@router.get("/multisystem/full")
async def multisystem_full():
    """Full multisystem SMA analysis."""
    return analyze_multisystem_sma()


# Phase 7.5: Bioelectric Reprogramming — moved to routes/bioelectric.py (DB-driven)
