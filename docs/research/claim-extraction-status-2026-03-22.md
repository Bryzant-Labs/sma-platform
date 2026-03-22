# Claim Extraction Run — 2026-03-22

## Summary

Triggered bulk claim extraction on **4,719 unprocessed sources** on moltbot.

| Metric | Value |
|--------|-------|
| Sources processed | 4,719 |
| LLM calls (Gemini Flash) | 883 |
| Claims extracted | 3,126 |
| Sources skipped (non-SMA) | 3,836 |
| Errors | 0 |
| Duration | 5,113s (~85 min) |
| Rate (overall) | ~56 sources/min |

## Database Totals After Run

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total claims (evidence table) | 11,050 | 14,176 | +3,126 |
| Total claims (claims table) | ~11,061 | 14,187 | +3,126 |
| Targets with claims | ~50 | 59 | +9 |
| Unprocessed sources remaining | 4,719 | 3,836 (non-SMA) | -883 SMA-relevant processed |

## New Claims by Target (Top 20)

| Target | New Claims |
|--------|-----------|
| SMN2 | 871 |
| SMN1 | 829 |
| NEFL | 50 |
| NMJ_MATURATION | 44 |
| PLS3 | 37 |
| MSTN | 27 |
| STMN2 | 21 |
| UBA1 | 20 |
| NEFH | 19 |
| MAPK_PATHWAY | 13 |
| MTOR_PATHWAY | 9 |
| SMN_PROTEIN | 9 |
| NCALD | 9 |
| TP53 | 8 |
| HDAC_PATHWAY | 6 |
| NOTCH_PATHWAY | 4 |
| FUS | 4 |
| TARDBP | 3 |
| TMEM41B | 3 |
| IGF1 | 3 |

## New Claims by Type

| Claim Type | Count |
|-----------|-------|
| other | 672 |
| drug_efficacy | 618 |
| biomarker | 420 |
| motor_function | 325 |
| gene_expression | 295 |
| safety | 149 |
| splicing_event | 148 |
| neuroprotection | 134 |
| drug_target | 121 |
| pathway_membership | 108 |
| protein_interaction | 71 |
| survival | 65 |

## Configuration

- **Extraction LLM**: Gemini 2.0 Flash (free tier) — set via `EXTRACTION_LLM=gemini` in `.env`
- **Rate limiting**: 15s pause every 8 LLM calls
- **Quality gate**: confidence floor 0.4, ALS in blocklist, title included in check
- **Word-boundary regex**: prevents false matches (e.g., "SMN" in "TRANSMISSION")
- **35+ target aliases**: PFN1, CFL2, ROCK2, p53 pathway, LIMK, C1Q, etc.

## Notes

- 3,836 sources remain "unprocessed" but these all failed the SMA relevance keyword filter — they contain no SMA-related keywords in title or abstract
- A few Gemini JSON parse errors occurred (truncated responses) but were handled gracefully with 0 total errors
- The extraction script was run via `screen -S claims` on moltbot with unbuffered Python output (`python3 -u`) for real-time logging to `/tmp/claim_extraction.log`

## Next Steps

- Run `/api/v2/ingest/relink/claims` to retroactively link any unlinked claims to targets
- Run `/api/v2/ingest/generate/hypotheses` to generate updated hypothesis cards
- Consider reviewing the 3,836 non-SMA sources — some may be importable under broader keyword criteria
