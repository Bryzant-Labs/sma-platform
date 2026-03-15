-- SMA Research Platform — Canonical PostgreSQL Schema v1
-- Evidence-first design: every claim traces back to a source.

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- SOURCES & PAPERS
-- ============================================================

CREATE TABLE sources (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type TEXT NOT NULL CHECK (source_type IN ('pubmed', 'clinicaltrials', 'geo', 'pride', 'knowledgebase', 'preprint', 'manual', 'patent')),
    external_id TEXT NOT NULL,               -- PMID, NCT number, GSE accession, etc.
    title       TEXT,
    authors     TEXT[],
    journal     TEXT,
    pub_date    DATE,
    doi         TEXT,
    url         TEXT,
    abstract    TEXT,
    full_text   TEXT,                         -- if available / permitted
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source_type, external_id)
);

CREATE INDEX idx_sources_type ON sources(source_type);
CREATE INDEX idx_sources_external ON sources(external_id);
CREATE INDEX idx_sources_pubdate ON sources(pub_date);

-- ============================================================
-- TARGETS (genes, proteins, pathways)
-- ============================================================

CREATE TABLE targets (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol      TEXT NOT NULL,                -- e.g. SMN1, SMN2, STMN2, PLS3
    name        TEXT,                         -- full name
    target_type TEXT NOT NULL CHECK (target_type IN ('gene', 'protein', 'pathway', 'cell_state', 'phenotype', 'other')),
    organism    TEXT DEFAULT 'Homo sapiens',
    identifiers JSONB DEFAULT '{}',           -- {"hgnc": "...", "uniprot": "...", "ensembl": "..."}
    description TEXT,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (symbol, target_type, organism)
);

CREATE INDEX idx_targets_symbol ON targets(symbol);
CREATE INDEX idx_targets_type ON targets(target_type);

-- ============================================================
-- DRUGS & THERAPIES
-- ============================================================

CREATE TABLE drugs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,             -- generic name
    brand_names     TEXT[],
    drug_type       TEXT CHECK (drug_type IN ('small_molecule', 'aso', 'gene_therapy', 'splice_modifier', 'neuroprotectant', 'antibody', 'cell_therapy', 'other')),
    mechanism       TEXT,                      -- e.g. "SMN2 splice modifier"
    targets         UUID[] DEFAULT '{}',       -- FK refs to targets table
    approval_status TEXT CHECK (approval_status IN ('approved', 'phase3', 'phase2', 'phase1', 'preclinical', 'discontinued', 'investigational')),
    approved_for    TEXT[],                    -- SMA types: ["type1", "type2", "type3", "presymptomatic"]
    manufacturer    TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_drugs_status ON drugs(approval_status);
CREATE INDEX idx_drugs_type ON drugs(drug_type);

-- ============================================================
-- CLINICAL TRIALS
-- ============================================================

CREATE TABLE trials (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nct_id          TEXT UNIQUE,               -- NCT number
    title           TEXT NOT NULL,
    status          TEXT,                       -- recruiting, completed, terminated, etc.
    phase           TEXT,
    conditions      TEXT[],
    interventions   JSONB DEFAULT '[]',
    sponsor         TEXT,
    start_date      DATE,
    completion_date DATE,
    enrollment      INTEGER,
    locations       JSONB DEFAULT '[]',
    results_summary TEXT,
    url             TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trials_nct ON trials(nct_id);
CREATE INDEX idx_trials_status ON trials(status);
CREATE INDEX idx_trials_phase ON trials(phase);

-- ============================================================
-- DATASETS (omics: GEO, PRIDE, etc.)
-- ============================================================

CREATE TABLE datasets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    accession       TEXT NOT NULL UNIQUE,       -- GSE69175, PXD033055
    source_db       TEXT NOT NULL,              -- "geo", "pride", "arrayexpress"
    title           TEXT,
    modality        TEXT,                       -- "rna-seq", "scrna-seq", "proteomics"
    organism        TEXT DEFAULT 'Homo sapiens',
    tissue          TEXT,                       -- "motor neurons", "spinal cord"
    evidence_tier   TEXT CHECK (evidence_tier IN ('tier1', 'tier2', 'tier3')),
    usage_class     TEXT CHECK (usage_class IN ('use_now', 'use_later', 'optional')),
    sample_count    INTEGER,
    description     TEXT,
    url             TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_datasets_accession ON datasets(accession);
CREATE INDEX idx_datasets_tier ON datasets(evidence_tier);

-- ============================================================
-- EVIDENCE GRAPH (claims backed by sources)
-- ============================================================

-- Claims: factual assertions extracted from sources
CREATE TABLE claims (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_type      TEXT NOT NULL CHECK (claim_type IN (
        'gene_expression', 'protein_interaction', 'pathway_membership',
        'drug_target', 'drug_efficacy', 'biomarker', 'splicing_event',
        'neuroprotection', 'motor_function', 'survival', 'safety', 'other'
    )),
    subject_id      UUID,                       -- FK to targets, drugs, or trials
    subject_type    TEXT,                        -- 'target', 'drug', 'trial'
    predicate       TEXT NOT NULL,               -- e.g. "upregulates", "treats", "correlates_with"
    object_id       UUID,
    object_type     TEXT,
    value           TEXT,                        -- quantitative or qualitative value
    confidence      NUMERIC(3,2) DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_claims_type ON claims(claim_type);
CREATE INDEX idx_claims_subject ON claims(subject_id);
CREATE INDEX idx_claims_object ON claims(object_id);

-- Evidence: links claims to their sources
CREATE TABLE evidence (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id    UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    source_id   UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    excerpt     TEXT,                            -- relevant quote or data point
    figure_ref  TEXT,                            -- "Figure 3A", "Table 2"
    method      TEXT,                            -- experimental method
    sample_size INTEGER,
    p_value     NUMERIC,
    effect_size NUMERIC,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (claim_id, source_id)
);

CREATE INDEX idx_evidence_claim ON evidence(claim_id);
CREATE INDEX idx_evidence_source ON evidence(source_id);

-- ============================================================
-- KNOWLEDGE GRAPH EDGES (UCM layer)
-- ============================================================

CREATE TABLE graph_edges (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    src_id      UUID NOT NULL REFERENCES targets(id),
    dst_id      UUID NOT NULL REFERENCES targets(id),
    relation    TEXT NOT NULL,                   -- "regulates", "part_of", "inhibits", etc.
    direction   TEXT DEFAULT 'src_to_dst' CHECK (direction IN ('undirected', 'src_to_dst', 'dst_to_src')),
    effect      TEXT DEFAULT 'unknown' CHECK (effect IN ('activates', 'inhibits', 'associates', 'unknown')),
    confidence  NUMERIC(3,2) DEFAULT 0.5,
    evidence_ids UUID[] DEFAULT '{}',            -- FK refs to evidence table
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (src_id, dst_id, relation)
);

CREATE INDEX idx_graph_src ON graph_edges(src_id);
CREATE INDEX idx_graph_dst ON graph_edges(dst_id);

-- ============================================================
-- HYPOTHESES (generated by reasoning layer)
-- ============================================================

CREATE TABLE hypotheses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_type TEXT NOT NULL CHECK (hypothesis_type IN ('target', 'combination', 'repurposing', 'biomarker', 'mechanism')),
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    rationale       TEXT,                        -- why this hypothesis was generated
    supporting_evidence UUID[] DEFAULT '{}',     -- FK refs to evidence
    contradicting_evidence UUID[] DEFAULT '{}',
    confidence      NUMERIC(3,2) DEFAULT 0.5,
    status          TEXT DEFAULT 'proposed' CHECK (status IN ('proposed', 'under_review', 'validated', 'refuted', 'published')),
    generated_by    TEXT,                        -- agent name or "manual"
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_hypotheses_type ON hypotheses(hypothesis_type);
CREATE INDEX idx_hypotheses_status ON hypotheses(status);
CREATE INDEX idx_hypotheses_confidence ON hypotheses(confidence DESC);

-- ============================================================
-- INGESTION LOG (track what we've processed)
-- ============================================================

CREATE TABLE ingestion_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type     TEXT NOT NULL,
    query           TEXT,
    items_found     INTEGER DEFAULT 0,
    items_new       INTEGER DEFAULT 0,
    items_updated   INTEGER DEFAULT 0,
    errors          TEXT[],
    run_at          TIMESTAMPTZ DEFAULT NOW(),
    duration_secs   NUMERIC,
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_ingestion_source ON ingestion_log(source_type);
CREATE INDEX idx_ingestion_date ON ingestion_log(run_at DESC);

-- ============================================================
-- CONTACT MESSAGES
-- ============================================================

CREATE TABLE contact_messages (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    email       TEXT NOT NULL,
    message     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AGENT RUNS
-- ============================================================

CREATE TABLE agent_runs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name  TEXT NOT NULL,
    task_type   TEXT,
    status      TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    input       JSONB DEFAULT '{}',
    output      JSONB DEFAULT '{}',
    error       TEXT,
    started_at  TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    duration_secs NUMERIC
);

CREATE INDEX idx_agent_runs_name ON agent_runs(agent_name);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);

-- ============================================================
-- CROSS-SPECIES TARGETS (Querdenker comparative biology)
-- ============================================================

CREATE TABLE cross_species_targets (
    id          TEXT PRIMARY KEY,
    human_symbol TEXT NOT NULL,
    human_target_id TEXT,
    species     TEXT NOT NULL,
    species_taxon_id TEXT,
    ortholog_symbol TEXT,
    ortholog_id TEXT,
    conservation_score NUMERIC,
    functional_divergence TEXT,
    regeneration_relevant BOOLEAN DEFAULT FALSE,
    notes       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cross_species_human ON cross_species_targets(human_symbol);
CREATE INDEX idx_cross_species_species ON cross_species_targets(species_taxon_id);

-- ============================================================
-- DRUG OUTCOMES (failure & success database)
-- ============================================================

CREATE TABLE drug_outcomes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compound_name   TEXT NOT NULL,
    target          TEXT,
    mechanism       TEXT,
    outcome         TEXT NOT NULL CHECK (outcome IN ('success', 'partial_success', 'failure', 'inconclusive', 'discontinued', 'ongoing')),
    failure_reason  TEXT,
    failure_detail  TEXT,
    trial_phase     TEXT,
    model_system    TEXT,
    key_finding     TEXT,
    confidence      NUMERIC(3,2) DEFAULT 0.5,
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (compound_name, source_id)
);

CREATE INDEX idx_drug_outcomes_compound ON drug_outcomes(compound_name);
CREATE INDEX idx_drug_outcomes_outcome ON drug_outcomes(outcome);
CREATE INDEX idx_drug_outcomes_source ON drug_outcomes(source_id);
