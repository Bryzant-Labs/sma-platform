#!/bin/bash
# Daily SMA Platform ingestion — runs at 06:00 UTC via cron
# Pulls new papers, trials, extracts claims, relinks, and refreshes scores

set -euo pipefail

API="http://localhost:8090/api/v2"
KEY="${SMA_ADMIN_KEY:?SMA_ADMIN_KEY env var is required}"
LOG="/home/bryzant/sma-platform/logs/daily_ingest.log"

mkdir -p "$(dirname "$LOG")"

echo "============================================" >> "$LOG"
echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Starting daily ingestion" >> "$LOG"

# 1. PubMed — pull papers from last 7 days
echo "[$(date -u '+%H:%M:%S')] PubMed ingestion..." >> "$LOG"
curl -s -X POST "$API/ingest/pubmed?days_back=7" -H "x-admin-key: $KEY" >> "$LOG" 2>&1
echo "" >> "$LOG"

# 2. ClinicalTrials.gov — refresh all SMA trials
echo "[$(date -u '+%H:%M:%S')] Trials ingestion..." >> "$LOG"
curl -s -X POST "$API/ingest/trials" -H "x-admin-key: $KEY" >> "$LOG" 2>&1
echo "" >> "$LOG"

# 3. Extract claims from new abstracts
echo "[$(date -u '+%H:%M:%S')] Claim extraction..." >> "$LOG"
curl -s -m 300 -X POST "$API/extract/claims" -H "x-admin-key: $KEY" >> "$LOG" 2>&1
echo "" >> "$LOG"

# 4. Relink claims to targets
echo "[$(date -u '+%H:%M:%S')] Claim relinking..." >> "$LOG"
curl -s -X POST "$API/relink/claims" -H "x-admin-key: $KEY" >> "$LOG" 2>&1
echo "" >> "$LOG"

# 5. Refresh scores
echo "[$(date -u '+%H:%M:%S')] Score refresh..." >> "$LOG"
curl -s -X POST "$API/scores/refresh" -H "x-admin-key: $KEY" >> "$LOG" 2>&1
echo "" >> "$LOG"

echo "[$(date -u '+%H:%M:%S')] Daily ingestion complete" >> "$LOG"
echo "============================================" >> "$LOG"
