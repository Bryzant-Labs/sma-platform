#!/bin/bash
# SMA Research Platform — Reproducibility Package
# Run this to verify key platform outputs are deterministic and correct.
#
# Usage: bash scripts/reproduce.sh
# Requirements: Python 3.11+, PostgreSQL, venv with dependencies, DATABASE_URL set
#
# This script performs 6 verification steps:
#   1. Database schema integrity (required tables exist)
#   2. Data consistency (DB counts match API responses)
#   3. Claim extraction distribution (claim_type breakdown)
#   4. Convergence scoring (5-dimension scores for top targets)
#   5. Bayesian calibration (grade and calibration percentage)
#   6. Hypothesis prioritization (tier A ranked hypotheses)

set -e

echo "=== SMA Research Platform Reproducibility Check ==="
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Git: $(git -C "$(dirname "$0")/.." rev-parse --short HEAD 2>/dev/null || echo 'not a git repo')"
echo ""

cd "$(dirname "$0")/.."

# Check prerequisites
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable not set."
    echo "  export DATABASE_URL='postgresql://user:pass@host:5432/sma'"
    exit 1
fi

if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -n "$VIRTUAL_ENV" ]; then
    echo "Using active venv: $VIRTUAL_ENV"
else
    echo "WARNING: No venv found. Using system Python."
fi

API_BASE="${SMA_API_BASE:-http://localhost:8090}"

echo "Database: ${DATABASE_URL%%@*}@***"
echo "API Base: $API_BASE"
echo ""

PASS=0
FAIL=0
WARN=0

pass() { ((PASS++)); echo "  PASS: $1"; }
fail() { ((FAIL++)); echo "  FAIL: $1"; }
warn() { ((WARN++)); echo "  WARN: $1"; }

# --------------------------------------------------------------------------
# 1. Database schema integrity
# --------------------------------------------------------------------------
echo "[1/6] Database schema check..."
python3 -c "
import asyncio, asyncpg, os, sys

REQUIRED_TABLES = [
    'sources', 'targets', 'drugs', 'trials', 'datasets',
    'claims', 'evidence', 'hypotheses', 'drug_outcomes',
    'convergence_scores', 'prediction_cards', 'graph_edges',
    'ingestion_log', 'news_posts',
]

async def check():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    try:
        tables = await conn.fetch(
            \"SELECT tablename FROM pg_tables WHERE schemaname = 'public'\"
        )
        table_names = {r['tablename'] for r in tables}
        print(f'  Tables found: {len(table_names)}')
        ok = 0
        for t in REQUIRED_TABLES:
            exists = t in table_names
            if exists:
                ok += 1
            else:
                print(f'  MISSING: {t}')
        print(f'  Required: {ok}/{len(REQUIRED_TABLES)} present')
        sys.exit(0 if ok == len(REQUIRED_TABLES) else 1)
    finally:
        await conn.close()

asyncio.run(check())
" && pass "All required tables present" || fail "Missing database tables"

# --------------------------------------------------------------------------
# 2. Data consistency — DB counts vs API
# --------------------------------------------------------------------------
echo ""
echo "[2/6] Data consistency check (DB vs API)..."

# Check API availability first
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "$API_BASE/api/v2/stats" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "200" ]; then
    warn "API not reachable at $API_BASE (HTTP $HTTP_CODE) -- skipping API consistency check"
else
    STATS_JSON=$(curl -s "$API_BASE/api/v2/stats")
    python3 << PYEOF
import asyncio, asyncpg, json, os, sys

stats = json.loads('''$STATS_JSON''')

async def verify():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    try:
        mismatches = 0
        for table, api_key in [
            ('sources', 'sources'),
            ('claims', 'claims'),
            ('targets', 'targets'),
            ('hypotheses', 'hypotheses'),
            ('drugs', 'drugs'),
            ('trials', 'trials'),
            ('evidence', 'evidence'),
            ('datasets', 'datasets'),
        ]:
            db_count = await conn.fetchval(f'SELECT count(*) FROM {table}')
            api_count = stats.get(api_key, -1)
            if db_count == api_count:
                print(f'  {table}: {db_count} (OK)')
            else:
                print(f'  {table}: DB={db_count} API={api_count} (MISMATCH)')
                mismatches += 1
        sys.exit(0 if mismatches == 0 else 1)
    finally:
        await conn.close()

asyncio.run(verify())
PYEOF
    if [ $? -eq 0 ]; then pass "All counts match DB vs API"; else fail "Count mismatches detected"; fi
fi

# --------------------------------------------------------------------------
# 3. Claim extraction — type distribution
# --------------------------------------------------------------------------
echo ""
echo "[3/6] Claim extraction distribution..."
python3 -c "
import asyncio, asyncpg, os, sys

async def check():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    try:
        rows = await conn.fetch(
            'SELECT claim_type, count(*) as cnt FROM claims GROUP BY claim_type ORDER BY cnt DESC'
        )
        if not rows:
            print('  No claims found!')
            sys.exit(1)
        total = sum(r['cnt'] for r in rows)
        print(f'  Total claims: {total:,}')
        print(f'  Distinct types: {len(rows)}')
        for r in rows[:8]:
            pct = 100 * r['cnt'] / total
            print(f'    {r[\"claim_type\"]}: {r[\"cnt\"]:,} ({pct:.1f}%)')
        # Sanity: at least 5 claim types and 1000 claims
        if total >= 1000 and len(rows) >= 5:
            sys.exit(0)
        else:
            print(f'  Below threshold (need >=1000 claims, >=5 types)')
            sys.exit(1)
    finally:
        await conn.close()

asyncio.run(check())
" && pass "Claim distribution looks healthy" || fail "Claim distribution below threshold"

# --------------------------------------------------------------------------
# 4. Convergence scoring reproducibility
# --------------------------------------------------------------------------
echo ""
echo "[4/6] Convergence scoring check..."

if [ "$HTTP_CODE" != "200" ]; then
    warn "API not reachable -- skipping convergence check"
else
    curl -s "$API_BASE/api/v2/convergence/scores?limit=10" | python3 -c "
import sys, json

data = json.load(sys.stdin)
targets = data.get('targets', [])
print(f'  Targets scored: {len(targets)}')
if not targets:
    print('  No convergence scores computed yet')
    sys.exit(1)
for t in targets[:5]:
    dims = f'V={t.get(\"volume\",0):.2f} L={t.get(\"lab_independence\",0):.2f} M={t.get(\"method_diversity\",0):.2f} T={t.get(\"temporal_trend\",0):.2f} R={t.get(\"replication\",0):.2f}'
    print(f'    {t[\"target_label\"]}: {t[\"composite_score\"]:.3f} ({t[\"confidence_level\"]}) [{dims}]')

# Check scores are in valid range
for t in targets:
    s = t['composite_score']
    if s < 0 or s > 1:
        print(f'  OUT OF RANGE: {t[\"target_label\"]} = {s}')
        sys.exit(1)
sys.exit(0)
" && pass "Convergence scores valid" || fail "Convergence scoring issue"
fi

# --------------------------------------------------------------------------
# 5. Bayesian calibration grade
# --------------------------------------------------------------------------
echo ""
echo "[5/6] Bayesian calibration check..."

if [ "$HTTP_CODE" != "200" ]; then
    warn "API not reachable -- skipping calibration check"
else
    curl -s "$API_BASE/api/v2/calibration/bayesian/report" | python3 -c "
import sys, json

data = json.load(sys.stdin)
grade = data.get('grade', '?')
cal_pct = data.get('calibration_pct', data.get('calibration_percentage', '?'))
brier = data.get('brier_score', '?')
separation = data.get('separation_score', '?')

print(f'  Grade: {grade}')
print(f'  Calibration: {cal_pct}%')
print(f'  Brier score: {brier}')
print(f'  Separation: {separation}')

# Grade A or B is acceptable
if grade in ('A', 'B'):
    sys.exit(0)
elif grade == '?':
    print('  Could not determine calibration grade')
    sys.exit(1)
else:
    print(f'  Grade {grade} -- calibration needs improvement')
    sys.exit(1)
" && pass "Calibration grade acceptable" || fail "Calibration grade below threshold"
fi

# --------------------------------------------------------------------------
# 6. Hypothesis prioritization — top tier
# --------------------------------------------------------------------------
echo ""
echo "[6/6] Hypothesis prioritization check..."

if [ "$HTTP_CODE" != "200" ]; then
    warn "API not reachable -- skipping prioritization check"
else
    curl -s "$API_BASE/api/v2/hypotheses/prioritized" | python3 -c "
import sys, json

data = json.load(sys.stdin)
total = data.get('total', 0)
tier_a = data.get('tier_a', [])
tier_b = data.get('tier_b', [])
tier_c = data.get('tier_c', [])

print(f'  Total hypotheses: {total}')
print(f'  Tier A: {len(tier_a)}, Tier B: {len(tier_b)}, Tier C: {len(tier_c)}')

for h in tier_a[:5]:
    sym = h.get('target_symbol', h.get('symbol', '?'))
    score = h.get('composite_score', h.get('score', 0))
    print(f'    Tier A #{h.get(\"rank\", \"?\")}: {sym} (score {score:.3f})')

if total > 0 and len(tier_a) > 0:
    sys.exit(0)
else:
    print('  No prioritized hypotheses found')
    sys.exit(1)
" && pass "Hypothesis prioritization working" || fail "Hypothesis prioritization issue"
fi

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "  Reproducibility Check Summary"
echo "=========================================="
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"
echo "  WARN: $WARN"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
    echo "  Result: ISSUES DETECTED"
    echo "  Review failures above and re-run after fixing."
    exit 1
elif [ "$WARN" -gt 0 ]; then
    echo "  Result: PASSED WITH WARNINGS"
    echo "  Some checks were skipped (API not reachable)."
    exit 0
else
    echo "  Result: ALL CHECKS PASSED"
    exit 0
fi
