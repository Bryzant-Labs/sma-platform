-- Migration 023: Bioelectric Reprogramming Tables
-- Migrates hardcoded bioelectric data from reasoning/bioelectric_module.py
-- into queryable PostgreSQL tables.

-- -------------------------------------------------------------------------
-- Ion channels
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bioelectric_channels (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gene                TEXT NOT NULL,
    channel_name        TEXT NOT NULL,
    channel_type        TEXT NOT NULL CHECK (channel_type IN ('Na', 'K', 'Ca', 'Cl', 'HCN')),
    vmem_role           TEXT CHECK (vmem_role IN ('depolarizing', 'repolarizing', 'resting', 'modulatory')),
    sma_expression      TEXT CHECK (sma_expression IN ('upregulated', 'downregulated', 'unchanged', 'dysregulated')),
    sma_impact          TEXT,
    therapeutic_target  BOOLEAN DEFAULT FALSE,
    drug_candidates     TEXT[],
    target_id           UUID REFERENCES targets(id),
    source_id           UUID REFERENCES sources(id),
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (gene, channel_name)
);

CREATE INDEX IF NOT EXISTS idx_bioelectric_channels_type ON bioelectric_channels(channel_type);
CREATE INDEX IF NOT EXISTS idx_bioelectric_channels_expression ON bioelectric_channels(sma_expression);
CREATE INDEX IF NOT EXISTS idx_bioelectric_channels_therapeutic ON bioelectric_channels(therapeutic_target);

-- -------------------------------------------------------------------------
-- Vmem states
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bioelectric_vmem_states (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state_name          TEXT NOT NULL UNIQUE,
    vmem_range          TEXT NOT NULL,
    phenotype           TEXT,
    sma_relevance       TEXT,
    prevalence_in_sma   NUMERIC(4, 3) CHECK (prevalence_in_sma >= 0 AND prevalence_in_sma <= 1),
    therapeutic_target  BOOLEAN DEFAULT FALSE,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------------------
-- Electroceutical interventions
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bioelectric_interventions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                TEXT NOT NULL UNIQUE,
    modality            TEXT CHECK (modality IN ('epidural', 'transcutaneous', 'patch', 'implantable', 'pharmacological')),
    target_vmem_state   TEXT,
    mechanism           TEXT,
    evidence_level      TEXT CHECK (evidence_level IN ('clinical', 'preclinical', 'theoretical')),
    feasibility         NUMERIC(3, 2) CHECK (feasibility >= 0 AND feasibility <= 1),
    sma_specific_notes  TEXT,
    source_id           UUID REFERENCES sources(id),
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bioelectric_interventions_modality ON bioelectric_interventions(modality);
CREATE INDEX IF NOT EXISTS idx_bioelectric_interventions_evidence ON bioelectric_interventions(evidence_level);
