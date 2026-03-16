-- Extraction Benchmark: gold-standard evaluations for claim quality assessment
CREATE TABLE IF NOT EXISTS benchmark_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES claims(id),
    gold_label TEXT NOT NULL CHECK (gold_label IN ('correct', 'incorrect', 'partial')),
    notes TEXT,
    evaluated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_benchmark_eval_claim ON benchmark_evaluations(claim_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_eval_label ON benchmark_evaluations(gold_label);
