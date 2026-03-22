# New Molecular Targets Added — 2026-03-22

**Date**: 2026-03-22
**Total targets after insertion**: 63
**New targets inserted**: 5 (TMEM41B already existed from 2026-03-21)

## Targets Added

### MDM2 — E3 ubiquitin-protein ligase Mdm2
- **Type**: gene
- **UniProt**: Q00987 | **HGNC**: 6973 | **Ensembl**: ENSG00000135679
- **SMA relevance**: E3 ubiquitin ligase and primary p53 repressor. SMN deficiency causes Mdm2 mis-splicing (exon 3 skipping) leading to loss of p53 repression and motor neuron apoptosis. Druggable with nutlin-3.
- **Druggable**: Yes

### MDM4 — Protein Mdm4 / MDMX
- **Type**: gene
- **UniProt**: O15151 | **HGNC**: 6974 | **Ensembl**: ENSG00000198625
- **SMA relevance**: Non-redundant p53 repressor, also mis-spliced in SMA motor neurons. MDM2-MDM4 heterodimerization required for full p53 suppression.
- **Druggable**: No (currently)

### MAPK14 — p38-alpha MAPK
- **Type**: gene
- **UniProt**: Q16539 | **HGNC**: 6876 | **Ensembl**: ENSG00000112062
- **SMA relevance**: Phosphorylates p53 at Ser18, stabilizing it and promoting apoptosis. MW150 (selective p38alpha inhibitor) shows synergy with risdiplam in SMA models (EMBO Mol Med 2025).
- **Druggable**: Yes (MW150)

### C1QA — Complement C1q subcomponent subunit A
- **Type**: gene
- **UniProt**: P02745 | **HGNC**: 1241 | **Ensembl**: ENSG00000173372
- **SMA relevance**: Tags ~25% of proprioceptive synapses onto SMA motor neurons for microglial elimination. Blocking C1q rescues synapses independent of SMN levels (PMID 31801075).
- **Druggable**: Yes

### LIMK1 — LIM domain kinase 1
- **Type**: gene
- **UniProt**: P53667 | **HGNC**: 6613 | **Ensembl**: ENSG00000106683
- **SMA relevance**: Downstream of ROCK2 in Rho-ROCK-LIMK-cofilin pathway. Phosphorylates cofilin leading to actin rod formation. MDI-117740 (most selective LIMK inhibitor, J Med Chem 2025).
- **Druggable**: Yes (MDI-117740)

### TMEM41B — Stasimon (already existed)
- **Previously added**: 2026-03-21
- **SMA relevance**: U12 minor intron gene with dual role — protects proprioceptive neurons AND blocks p53-mediated apoptosis. AAV9-U11/U12 delivery rescues synapses without increasing SMN.

## Pathway Context

These targets expand coverage across three key SMA pathways:

1. **p53 death axis**: MDM2, MDM4, MAPK14 (upstream of existing TP53 target)
2. **Complement-mediated synapse elimination**: C1QA (non-cell-autonomous mechanism)
3. **Actin dynamics / cytoskeletal collapse**: LIMK1 (between existing ROCK2 and CFL2 targets)

## Verification Query

```sql
SELECT symbol, name, target_type, created_at
FROM targets
WHERE symbol IN ('MDM2','MDM4','MAPK14','TMEM41B','C1QA','LIMK1')
ORDER BY symbol;
```

All 6 targets confirmed present in database.
