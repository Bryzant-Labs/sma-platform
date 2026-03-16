-- Screening Funnel Pipeline — stores results from billion-molecule virtual screening runs

CREATE TABLE IF NOT EXISTS screening_funnels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT UNIQUE NOT NULL,
    target TEXT NOT NULL,
    n_generated INTEGER,
    n_filtered INTEGER,
    n_proxy_passed INTEGER,
    n_docked INTEGER,
    top_candidates JSONB DEFAULT '[]',
    timing JSONB DEFAULT '{}',
    status TEXT DEFAULT 'running',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_screening_funnels_run_id ON screening_funnels(run_id);
CREATE INDEX IF NOT EXISTS idx_screening_funnels_status ON screening_funnels(status);
CREATE INDEX IF NOT EXISTS idx_screening_funnels_target ON screening_funnels(target);
