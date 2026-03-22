# CRISPR Guide Design — DB Migration Report
**Date:** 2026-03-22
**Scope:** Migrate CRISPR Guide Design section from hardcoded in-memory computation to PostgreSQL persistence

---

## Summary

The CRISPR section previously computed all guides on every API call using the in-memory
`design_smn2_guides()` function, with no persistence or queryability. This migration moves
the data into two PostgreSQL tables and rewrites the API route to serve results from the DB,
while retaining the compute path for custom sequences.

---

## Tables Created

### `crispr_strategies`
Stores the three therapeutic strategies defined for SMN2 exon 7 targeting.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| name | TEXT UNIQUE | Strategy display name |
| target_gene | TEXT | Default 'SMN2' |
| target_region | TEXT | 'intron7', 'exon7' |
| mechanism | TEXT | 'CRISPRi' or 'CRISPRa' |
| description | TEXT | Rationale text |
| created_at | TIMESTAMPTZ | Auto |

### `crispr_guides`
Stores all 19 designed sgRNA guides for the SMN2 exon 7 region.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| strategy_id | INT FK -> crispr_strategies | Nullable for unclassified guides |
| sequence | TEXT | 20 nt protospacer |
| pam | TEXT | NGG trinucleotide |
| strand | CHAR(1) | '+' or '-' |
| position | INT | 0-indexed in SMN2_REGION (intron6[-100] + exon7[55] + intron7[+100]) |
| region | TEXT | 'exon7', 'intron6', 'intron7' |
| gc_pct | FLOAT | GC fraction 0-1 |
| on_target_score | FLOAT | Doench 2016-inspired score 0-1 |
| cfd_score | FLOAT | CFD off-target score (0.0 = not yet computed) |
| motifs | TEXT[] | Overlapping regulatory motifs (GIN indexed) |
| notes | TEXT | Therapeutic annotation |
| metadata | JSONB | specificity_score, has_polyT, reference |
| created_at | TIMESTAMPTZ | Auto |

**Indexes:**
- `idx_crispr_guides_strategy` - fast join to strategies
- `idx_crispr_guides_on_target` - descending score sort
- `idx_crispr_guides_region` - region filter
- `idx_crispr_guides_motifs` - GIN for ANY(motifs) queries

---

## Seeded Data

**Strategies:** 3

| ID | Name | Mechanism | Target Region |
|----|------|-----------|---------------|
| 1 | CRISPRi at ISS-N1 | CRISPRi | intron7 |
| 2 | CRISPRi at Exon 7 ESS | CRISPRi | exon7 |
| 3 | CRISPRa at Tra2-beta ESE | CRISPRa | exon7 |

**Guides:** 19 total
- 2 in exon7 (both overlap ESE_Tra2beta, strategy 3)
- 17 in intron6/intron7
- 1 overlaps ISS-N1 (nusinersen target, strategy 1) -- sequence AAGATTCACTTTCATAATGC
- 3 overlap Branch_point
- 0 assigned to CRISPRi at Exon 7 ESS (no NGG PAM without polyT in the ESS window)

**Reference:** SMN2 NG_008728.1, 255 nt window (intron6[-100] + exon7[55] + intron7[+100])

---

## API Changes

**File:** src/sma_platform/api/routes/crispr.py
**Backup:** crispr.py.bak (retained on server)

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v2/crispr/guides | Query guides from DB with filters |
| POST | /api/v2/crispr/guides | Design guides for custom sequence (compute-only) |
| GET | /api/v2/crispr/strategies | List all strategies with guide counts |
| GET | /api/v2/crispr/strategies/{id} | One strategy with its guides |
| GET | /api/v2/crispr/motifs | SMN2 regulatory motifs reference |
| POST | /api/v2/crispr/seed | Admin: re-seed DB from computed SMN2 guides |

### Query parameters for GET /crispr/guides

| Param | Type | Description |
|-------|------|-------------|
| symbol | str | 'SMN2'/'SMN1' for DB; others redirect to POST |
| strategy_id | int | Filter by strategy ID |
| region | str | 'exon7', 'intron6', 'intron7' |
| motif | str | ANY(motifs) filter e.g. 'ISS-N1' |
| min_score | float | Minimum on_target_score |
| limit | int | 1-200, default 20 |
| offset | int | Pagination |

---

## Verification Results

All tests passed on live server (127.0.0.1:8090):

- GET /api/v2/crispr/strategies -> 3 strategies, correct guide counts
- GET /api/v2/crispr/guides?symbol=SMN2&limit=5 -> 19 total, top 5 returned
- GET /api/v2/crispr/guides?motif=ISS-N1 -> 1 guide (AAGATTCACTTTCATAATGC, intron7)
- GET /api/v2/crispr/strategies/1 -> ISS-N1 strategy with 1 guide

---

## Notes & Known Limitations

1. **CRISPRi at Exon 7 ESS has 0 guides** - The ESS_hnRNP_A1 motif (exon7 pos 45-55) has no valid 20nt+NGG guide without polyT in the current 255 nt reference. Biologically real constraint. Future: extend window or relax filter.

2. **CFD score is 0.0** - Off-target scoring requires whole-genome alignment (Cas-OFFinder). Reserved for Phase 8 GPU integration.

3. **specificity_score in metadata JSONB** - Entropy-based proxy, not validated. Promote to top-level column when Cas-OFFinder lands.

4. **Backward compatibility** - Response shape changed. Old GET /crispr/guides returned strategies[]+all_guides[]+motifs{} in one blob. New shape is paginated guides list. Use /crispr/strategies and /crispr/motifs for the rest.

5. **POST /crispr/seed** - Re-derives and reloads all SMN2 guides from the reference sequence. Use after updating crispr_designer.py scoring logic.
