-- SMA Research Platform — SQLite Schema v1
-- Mirror of schema.sql but SQLite-compatible (no extensions, no UUID type, no arrays)

CREATE TABLE IF NOT EXISTS sources (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    source_type TEXT NOT NULL CHECK (source_type IN ('pubmed', 'clinicaltrials', 'geo', 'pride', 'knowledgebase', 'preprint', 'manual', 'patent')),
    external_id TEXT NOT NULL,
    title       TEXT,
    authors     TEXT,  -- JSON array as string
    journal     TEXT,
    pub_date    TEXT,
    doi         TEXT,
    url         TEXT,
    abstract    TEXT,
    full_text   TEXT,
    metadata    TEXT DEFAULT '{}',
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now')),
    UNIQUE (source_type, external_id)
);

CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_external ON sources(external_id);

CREATE TABLE IF NOT EXISTS targets (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    symbol      TEXT NOT NULL,
    name        TEXT,
    target_type TEXT NOT NULL CHECK (target_type IN ('gene', 'protein', 'pathway', 'cell_state', 'phenotype', 'other')),
    organism    TEXT DEFAULT 'Homo sapiens',
    identifiers TEXT DEFAULT '{}',
    description TEXT,
    metadata    TEXT DEFAULT '{}',
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now')),
    UNIQUE (symbol, target_type, organism)
);

CREATE INDEX IF NOT EXISTS idx_targets_symbol ON targets(symbol);

CREATE TABLE IF NOT EXISTS drugs (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name            TEXT NOT NULL,
    brand_names     TEXT,  -- JSON array
    drug_type       TEXT CHECK (drug_type IN ('small_molecule', 'aso', 'gene_therapy', 'splice_modifier', 'neuroprotectant', 'antibody', 'cell_therapy', 'other')),
    mechanism       TEXT,
    targets         TEXT DEFAULT '[]',
    approval_status TEXT CHECK (approval_status IN ('approved', 'phase3', 'phase2', 'phase1', 'preclinical', 'discontinued', 'investigational')),
    approved_for    TEXT,  -- JSON array
    manufacturer    TEXT,
    metadata        TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trials (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    nct_id          TEXT UNIQUE,
    title           TEXT NOT NULL,
    status          TEXT,
    phase           TEXT,
    conditions      TEXT,  -- JSON array
    interventions   TEXT DEFAULT '[]',
    sponsor         TEXT,
    start_date      TEXT,
    completion_date TEXT,
    enrollment      INTEGER,
    locations       TEXT DEFAULT '[]',
    results_summary TEXT,
    url             TEXT,
    metadata        TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_trials_nct ON trials(nct_id);
CREATE INDEX IF NOT EXISTS idx_trials_status ON trials(status);

CREATE TABLE IF NOT EXISTS datasets (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    accession       TEXT NOT NULL UNIQUE,
    source_db       TEXT NOT NULL,
    title           TEXT,
    modality        TEXT,
    organism        TEXT DEFAULT 'Homo sapiens',
    tissue          TEXT,
    evidence_tier   TEXT CHECK (evidence_tier IN ('tier1', 'tier2', 'tier3')),
    usage_class     TEXT CHECK (usage_class IN ('use_now', 'use_later', 'optional')),
    sample_count    INTEGER,
    description     TEXT,
    url             TEXT,
    metadata        TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS claims (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    claim_type      TEXT NOT NULL CHECK (claim_type IN (
        'gene_expression', 'protein_interaction', 'pathway_membership',
        'drug_target', 'drug_efficacy', 'biomarker', 'splicing_event',
        'neuroprotection', 'motor_function', 'survival', 'safety', 'other'
    )),
    subject_id      TEXT,
    subject_type    TEXT,
    predicate       TEXT NOT NULL,
    object_id       TEXT,
    object_type     TEXT,
    value           TEXT,
    confidence      REAL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    metadata        TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evidence (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    claim_id    TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    source_id   TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    excerpt     TEXT,
    figure_ref  TEXT,
    method      TEXT,
    sample_size INTEGER,
    p_value     REAL,
    effect_size REAL,
    metadata    TEXT DEFAULT '{}',
    created_at  TEXT DEFAULT (datetime('now')),
    UNIQUE (claim_id, source_id)
);

CREATE TABLE IF NOT EXISTS graph_edges (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    src_id      TEXT NOT NULL REFERENCES targets(id),
    dst_id      TEXT NOT NULL REFERENCES targets(id),
    relation    TEXT NOT NULL,
    direction   TEXT DEFAULT 'src_to_dst' CHECK (direction IN ('undirected', 'src_to_dst', 'dst_to_src')),
    effect      TEXT DEFAULT 'unknown' CHECK (effect IN ('activates', 'inhibits', 'associates', 'unknown')),
    confidence  REAL DEFAULT 0.5,
    evidence_ids TEXT DEFAULT '[]',
    metadata    TEXT DEFAULT '{}',
    created_at  TEXT DEFAULT (datetime('now')),
    UNIQUE (src_id, dst_id, relation)
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    hypothesis_type TEXT NOT NULL CHECK (hypothesis_type IN ('target', 'combination', 'repurposing', 'biomarker', 'mechanism')),
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    rationale       TEXT,
    supporting_evidence TEXT DEFAULT '[]',
    contradicting_evidence TEXT DEFAULT '[]',
    confidence      REAL DEFAULT 0.5,
    status          TEXT DEFAULT 'proposed' CHECK (status IN ('proposed', 'under_review', 'validated', 'refuted', 'published')),
    generated_by    TEXT,
    metadata        TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ingestion_log (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    source_type     TEXT NOT NULL,
    query           TEXT,
    items_found     INTEGER DEFAULT 0,
    items_new       INTEGER DEFAULT 0,
    items_updated   INTEGER DEFAULT 0,
    errors          TEXT,
    run_at          TEXT DEFAULT (datetime('now')),
    duration_secs   REAL,
    metadata        TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name        TEXT NOT NULL,
    email       TEXT NOT NULL,
    message     TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_name  TEXT NOT NULL,
    task_type   TEXT,
    status      TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    input       TEXT DEFAULT '{}',
    output      TEXT DEFAULT '{}',
    error       TEXT,
    started_at  TEXT DEFAULT (datetime('now')),
    finished_at TEXT,
    duration_secs REAL
);

CREATE TABLE IF NOT EXISTS cross_species_targets (
    id TEXT PRIMARY KEY,
    human_symbol TEXT NOT NULL,
    human_target_id TEXT,
    species TEXT NOT NULL,
    species_taxon_id TEXT,
    ortholog_symbol TEXT,
    ortholog_id TEXT,
    conservation_score REAL,
    functional_divergence TEXT,
    regeneration_relevant BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
