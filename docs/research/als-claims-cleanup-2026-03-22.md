# ALS Claims Cleanup Report - 2026-03-22

## Problem

ALS-only claims leaked into the SMA Research Platform because both ALS and SMA involve "motor neuron" keywords. The extractor has been updated to block new ALS claims, but existing ones needed classification and cleanup.

## Database Stats

| Metric | Value |
|--------|-------|
| Total claims in DB | 10,905 |
| ALS-related claims (no SMA/SMN mention) | 564 |
| Claims tagged `als_only: true` | 497 (4.6% of total) |
| Untagged ALS claims (cross-disease, kept clean) | 67 |

## Classification Results

### TAGGED: `als_only: true, als_category: "pure_sod1"` -- 429 claims

Pure SOD1 mutation research with no direct SMA pathway overlap. These are ALS-specific but retained in the database for potential future cross-disease analysis. Filtered from default queries via the `als_only` metadata flag.

**Examples:**
- `#25345` G93A SOD1 mutant localizes to the nucleus and associates with DNA.
- `#25618` Mutant SOD1 (G93A) associated with familial ALS causes selective motor neuron loss.
- `#25826` Iron chelation with VK-28 and M30 significantly delays disease onset in SOD1(G93A) transgenic mice.
- `#25859` Mutations in Cu/Zn-superoxide dismutase (SOD1) are associated with familial ALS.

### TAGGED: `als_only: true, als_category: "als_clinical_no_shared_biology", delete_candidate: true` -- 68 claims

ALS clinical observations and therapeutic trials with no shared motor neuron biology relevant to SMA. These are safe to delete but tagged for now so they can be reviewed before permanent removal.

**Examples:**
- `#25309` GGGGCC hexanucleotide repeat expansion in the C9orf72 gene is a major causative factor in ALS.
- `#25873` CXCL12 levels are increased in cerebrospinal fluid of sporadic ALS patients.
- `#25972` ALS patients demonstrate declined thymic output.
- `#25975` ALS patients demonstrate a restricted T-cell repertoire.
- `#25985` PACAP and PAC1R are differentially expressed in motor cortex of ALS patients.
- `#26609` Copper chelation therapy delays disease onset in the FALS model.
- `#26611` Riluzole extends survival by increasing duration of symptomatic disease in the FALS model.

### KEPT CLEAN (no tag) -- 67 claims

These ALS claims have genuine cross-disease value for SMA research and remain untagged:

| Sub-category | Count | Rationale |
|-------------|-------|-----------|
| TDP-43/FUS motor neuron biology | 33 | Shared RNA metabolism pathways with SMN |
| Shared MN biology (apoptosis, axonal transport, caspase) | 17 | Motor neuron death mechanisms relevant to SMA |
| PFN1/actin/ROCK/cofilin pathways | 11 | Direct SMA-ALS convergence (actin dynamics) |
| Other overlapping biology | 6 | Various shared pathways |

**Cross-disease examples (kept):**
- `#31167` Eight DNA mutations in the PFN1 gene are associated with human ALS. *(PFN1 = SMA-ALS convergence)*
- `#31172` C71G-PFN1 mutant causes ALS by gain of toxicity and motor neuron degeneration preceded by actin accumulation.
- `#25522` Activated caspase-3 cleaves beta-actin in apoptotic neurons in anterior horn spinal cord of mSOD1 mice. *(actin + motor neuron death)*

## Query to Filter ALS-Only Claims

To exclude tagged ALS claims from any query:

```sql
-- Add to WHERE clause:
AND (metadata->>'als_only' IS NULL OR metadata->>'als_only' != 'true')
```

To find deletion candidates:

```sql
SELECT claim_number, predicate FROM claims
WHERE metadata->>'delete_candidate' = 'true';
```

## Recommendations

1. **Immediate**: The 497 tagged claims are now filterable. Update platform queries to exclude `als_only: true` claims from default views.
2. **Review**: The 68 `delete_candidate` claims can be permanently deleted after manual spot-check. Run: `DELETE FROM claims WHERE metadata->>'delete_candidate' = 'true';`
3. **Future**: The updated extractor blocks new ALS claims. Monitor for edge cases where ALS-SMA convergence papers should still be admitted.
4. **Cross-disease module**: The 67 kept claims are valuable for the SMA-ALS convergence analysis. Consider a dedicated cross-disease section.
