-- Migration 023: Bioelectric Reprogramming Tables
-- Migrates hardcoded data from reasoning/bioelectric_module.py to database

-- 1. Tables
CREATE TABLE IF NOT EXISTS bioelectric_channels (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gene                TEXT NOT NULL,
    channel_name        TEXT NOT NULL,
    channel_type        TEXT NOT NULL CHECK (channel_type IN ('Na', 'K', 'Ca', 'Cl', 'HCN')),
    vmem_role           TEXT CHECK (vmem_role IN ('depolarizing', 'repolarizing', 'resting', 'modulatory')),
    sma_expression      TEXT CHECK (sma_expression IN ('upregulated', 'downregulated', 'unchanged', 'dysregulated')),
    sma_impact          TEXT,
    therapeutic_target  BOOLEAN DEFAULT FALSE,
    drug_candidates     TEXT[] DEFAULT '{}',
    target_id           UUID REFERENCES targets(id),
    source_id           UUID REFERENCES sources(id),
    metadata            JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (gene, channel_name)
);

CREATE TABLE IF NOT EXISTS bioelectric_vmem_states (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state_name          TEXT NOT NULL UNIQUE,
    vmem_range          TEXT,
    phenotype           TEXT,
    sma_relevance       TEXT,
    prevalence_sma      NUMERIC(4,3) CHECK (prevalence_sma >= 0 AND prevalence_sma <= 1),
    reversible          BOOLEAN,
    therapeutic_window  TEXT,
    metadata            JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bioelectric_interventions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intervention_name   TEXT NOT NULL UNIQUE,
    modality            TEXT CHECK (modality IN ('epidural', 'transcutaneous', 'patch', 'implantable', 'pharmacological')),
    target_state        TEXT,
    mechanism           TEXT,
    evidence_level      TEXT CHECK (evidence_level IN ('clinical', 'preclinical', 'theoretical')),
    feasibility         NUMERIC(4,3) CHECK (feasibility >= 0 AND feasibility <= 1),
    sma_specific_notes  TEXT,
    risks               TEXT[] DEFAULT '{}',
    current_trials      TEXT[] DEFAULT '{}',
    source_id           UUID REFERENCES sources(id),
    metadata            JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Seed: Ion Channels
INSERT INTO bioelectric_channels (gene, channel_name, channel_type, vmem_role, sma_expression, sma_impact, therapeutic_target, drug_candidates)
VALUES
(
    'SCN1A', 'Nav1.1', 'Na', 'depolarizing', 'downregulated',
    'Reduced sodium channel density → decreased excitability → MN hypoexcitability',
    TRUE,
    ARRAY['Hm1a (Nav1.1 activator)', 'Low-dose veratridine']
),
(
    'SCN9A', 'Nav1.7', 'Na', 'depolarizing', 'downregulated',
    'Reduced action potential initiation threshold → sensorimotor deficits',
    FALSE,
    ARRAY[]::TEXT[]
),
(
    'KCNQ2', 'Kv7.2 (M-current)', 'K', 'repolarizing', 'upregulated',
    'Increased M-current → excessive hyperpolarization → MN silencing',
    TRUE,
    ARRAY['XE991 (Kv7 blocker)', 'Linopirdine (Kv7 blocker)']
),
(
    'KCNA2', 'Kv1.2 (delayed rectifier)', 'K', 'repolarizing', 'upregulated',
    'Accelerated repolarization → shortened action potential → reduced neurotransmitter release',
    TRUE,
    ARRAY['4-Aminopyridine (K+ channel blocker)', 'Dendrotoxin analogs']
),
(
    'CACNA1A', 'Cav2.1 (P/Q-type)', 'Ca', 'modulatory', 'downregulated',
    'Reduced calcium influx at presynaptic terminal → impaired neurotransmitter release at NMJ',
    TRUE,
    ARRAY['GV-58 (Cav2.1 agonist)', 'Roscovitine']
),
(
    'CACNA1C', 'Cav1.2 (L-type)', 'Ca', 'modulatory', 'dysregulated',
    'Altered calcium homeostasis → excitotoxicity or deficient signaling depending on context',
    FALSE,
    ARRAY['Nimodipine (Cav1.2 modulator)']
),
(
    'HCN1', 'HCN1 (pacemaker)', 'HCN', 'resting', 'downregulated',
    'Reduced Ih current → decreased MN spontaneous firing rate → reduced muscle tone',
    TRUE,
    ARRAY['Lamotrigine (HCN enhancer)', 'Gabapentin (indirect Ih modulation)']
),
(
    'CLCN2', 'ClC-2', 'Cl', 'resting', 'unchanged',
    'Chloride homeostasis maintained but may shift with NKCC1/KCC2 imbalance in immature MNs',
    FALSE,
    ARRAY[]::TEXT[]
),
(
    'TRPV1', 'TRPV1 (vanilloid)', 'Ca', 'modulatory', 'upregulated',
    'Pain and stress signaling. TRPV1 upregulation may contribute to sensory abnormalities in SMA.',
    FALSE,
    ARRAY['Capsaicin (desensitization)', 'SB-705498 (TRPV1 antagonist)']
)
ON CONFLICT (gene, channel_name) DO NOTHING;

-- 3. Seed: Vmem States
INSERT INTO bioelectric_vmem_states (state_name, vmem_range, phenotype, sma_relevance, prevalence_sma, reversible, therapeutic_window)
VALUES
(
    'Healthy resting',
    '-65 to -70 mV',
    'Normal firing, appropriate NMJ transmission, stable synaptic connections',
    'Target state for therapeutic intervention',
    0.15,
    TRUE,
    NULL
),
(
    'Hyperpolarized (silenced)',
    '-75 to -85 mV',
    'MN is alive but electrically silent. Reduced firing → NMJ denervation → muscle atrophy. May be rescuable.',
    'PRIMARY therapeutic target. These MNs could be reactivated with depolarizing interventions (K+ blockers, spinal stimulation).',
    0.40,
    TRUE,
    'Before irreversible NMJ retraction (~weeks to months post-onset)'
),
(
    'Depolarized (stressed)',
    '-45 to -55 mV',
    'Chronic depolarization → calcium overload → excitotoxicity → apoptosis pathway',
    'At-risk MNs heading toward death. Need calcium buffering and membrane potential stabilization.',
    0.25,
    TRUE,
    'Narrow window — calcium overload reversible only if caught early'
),
(
    'Committed to death',
    '-30 to -40 mV',
    'Severely depolarized, mitochondrial membrane permeabilized, caspase activation',
    'Beyond rescue. Focus on preventing other MNs from reaching this state.',
    0.20,
    FALSE,
    NULL
)
ON CONFLICT (state_name) DO NOTHING;

-- 4. Seed: Interventions
INSERT INTO bioelectric_interventions (intervention_name, modality, target_state, mechanism, evidence_level, feasibility, sma_specific_notes)
VALUES
(
    'Epidural Spinal Cord Stimulation (SCS)',
    'epidural',
    'Hyperpolarized (silenced)',
    'Electrical stimulation of dorsal spinal cord activates proprioceptive afferents → excites MN pools → re-engages silent motor circuits. FDA-approved for SCI.',
    'clinical',
    0.75,
    'Gill et al., Nature Medicine 2024 showed SCS restored voluntary movement in spinal cord injury. SMA analogy: reactivate silenced-but-alive MNs. Key difference: SMA MNs may be intrinsically compromised, not just disconnected.'
),
(
    'Transcutaneous Spinal Stimulation',
    'transcutaneous',
    'Hyperpolarized (silenced)',
    'Non-invasive stimulation via surface electrodes. Lower precision than epidural but no surgery required. Can be combined with physical therapy.',
    'preclinical',
    0.85,
    'Most practical for SMA — non-invasive, can be used in young children. Limited evidence specifically in SMA but strong rationale from SCI studies.'
),
(
    'Bioelectric Patch (Vmem modulation)',
    'patch',
    'Hyperpolarized (silenced)',
    'Wearable ionotronic device that delivers targeted ion currents to modulate local tissue Vmem. Based on Levin lab bioelectric pattern approaches.',
    'theoretical',
    0.40,
    'Concept: apply depolarizing bioelectric patterns to motor points overlying muscle. Activate satellite cell proliferation + NMJ remodeling. Technology exists for wound healing — adapting for neuromuscular is novel.'
),
(
    'FES (Functional Electrical Stimulation)',
    'transcutaneous',
    'Hyperpolarized (silenced)',
    'Direct muscle stimulation bypassing MNs entirely. Prevents disuse atrophy and maintains NMJ through activity-dependent signals.',
    'clinical',
    0.90,
    'Already used in SMA rehabilitation. Maintains muscle mass and retrograde trophic signaling even when MNs are compromised. Combines well with SMN therapy.'
),
(
    'Optogenetic MN activation (research only)',
    'implantable',
    'Hyperpolarized (silenced)',
    'Channelrhodopsin (ChR2) expression in MNs via AAV. Light activation restores precise MN firing patterns. Research tool, not yet clinical.',
    'preclinical',
    0.20,
    'Powerful research tool for organ-on-chip and animal models. Allows testing whether MN reactivation alone can rescue NMJ. Not feasible in humans yet but informs drug target selection.'
)
ON CONFLICT (intervention_name) DO NOTHING;

-- 5. Link channels to targets table where gene symbols match
UPDATE bioelectric_channels bc
SET target_id = t.id
FROM targets t
WHERE UPPER(bc.gene) = UPPER(t.symbol)
  AND bc.target_id IS NULL;
