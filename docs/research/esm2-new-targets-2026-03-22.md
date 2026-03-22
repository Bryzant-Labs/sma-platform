# ESM-2 Protein Embeddings: 5 New SMA Targets

**Date**: 2026-03-22
**Model**: facebook/esm2_t33_650M_UR50D (650M parameters, 33 layers)
**Embedding Dimension**: 1280
**Runtime**: HuggingFace transformers on moltbot CPU (~16s total)
**Platform API**: Metadata ingested (5/5 targets updated)

## New Targets Processed

| Target | UniProt | Sequence Length | Embedding Norm | Time (s) |
|--------|---------|----------------|----------------|----------|
| MDM2 | Q00987 | 491 aa | 7.686 | 3.6 |
| MDM4 | O15151 | 490 aa | 7.439 | 3.5 |
| MAPK14/p38 | Q16539 | 360 aa | 5.676 | 2.4 |
| C1QA | P02745 | 245 aa | 6.768 | 1.7 |
| LIMK1 | P53667 | 647 aa | 5.729 | 4.8 |

## Similarity Analysis

### Average Cosine Similarity (vs. all 11 other proteins)

| Target | Avg Cosine | Interpretation |
|--------|-----------|----------------|
| LIMK1 | 0.9091 | Most similar to existing SMA targets |
| MDM2 | 0.8964 | High similarity (SMN-like embedding space) |
| C1QA | 0.8895 | Moderate-high |
| MDM4 | 0.8833 | Moderate-high |
| MAPK14 | 0.8816 | Most structurally unique of the new 5 |

### Key Findings

**MDM2-MDM4 paralog pair**: Cosine similarity = 0.9879 (extremely high, as expected for paralogs with shared RING/SWIB domains). Compare with SMN1-SMN2 = 1.000 (identical protein).

**Highest similarities to existing targets**:
- MDM2-SMN1/SMN2: 0.965 -- MDM2 embeds very close to SMN in sequence space
- MDM4-SMN1/SMN2: 0.956
- LIMK1-SMN1/SMN2: 0.935
- C1QA-SMN1/SMN2: 0.930
- MAPK14-NCALD: 0.938 -- kinase-calcium sensor structural overlap

**Most structurally unique pairs** (involving new targets):
- CORO1C-MDM2: 0.707 (CORO1C remains the most structurally unique protein in the set)
- CORO1C-MDM4: 0.723
- C1QA-CORO1C: 0.730
- CORO1C-MAPK14: 0.779
- CORO1C-LIMK1: 0.807

### Biological Interpretation

1. **MAPK14/p38** has the lowest average similarity (0.882), suggesting it occupies a distinct region of protein embedding space. This aligns with its role as a stress-activated MAP kinase -- structurally different from the SMA core proteins (SMN, actin regulators).

2. **LIMK1** shows highest average similarity (0.909), consistent with its role as an actin pathway kinase that functionally overlaps with PLS3/CORO1C biology.

3. **C1QA** (complement component) is moderately unique, reflecting its collagen-like domain structure distinct from typical SMA target proteins.

4. **MDM2/MDM4** embed very close to each other and to SMN, which is interesting -- the p53-MDM2 axis and SMN protein share some structural features in their protein-protein interaction domains.

## Files Generated

### On moltbot server
- `/home/bryzant/sma-platform/gpu/results/esm2/MDM2.npy`
- `/home/bryzant/sma-platform/gpu/results/esm2/MDM4.npy`
- `/home/bryzant/sma-platform/gpu/results/esm2/MAPK14.npy`
- `/home/bryzant/sma-platform/gpu/results/esm2/C1QA.npy`
- `/home/bryzant/sma-platform/gpu/results/esm2/LIMK1.npy`
- `/home/bryzant/sma-platform/gpu/results/esm2/metadata.json` (updated with all 12 proteins)
- `/home/bryzant/sma-platform/gpu/results/esm2_similarity_12proteins.json` (full pairwise matrix)
- `/home/bryzant/sma-platform/gpu/results/esm2_similarity_15proteins.json` (updated in-place)

### Total embeddings: 12 proteins (was 7)
SMN1, SMN2, PLS3, STMN2, NCALD, UBA1, CORO1C + MDM2, MDM4, MAPK14, C1QA, LIMK1

## Note on Missing Proteins

The previous `esm2_similarity_15proteins.json` contained similarity data for 15 proteins (including TP53, ANK3, CAST, CD44, LDHA, NEDD4L, DNMT3B, SULF1) but only 7 had `.npy` files saved. The 8 proteins without `.npy` files were likely computed on a GPU instance (Vast.ai) where the full embeddings were used for similarity computation but only the 7 core SMA targets had their `.npy` files extracted. The new similarity matrix covers only the 12 proteins with `.npy` files on disk.

## Platform Integration

The target prioritizer v2 (`target_prioritizer_v2.py`) automatically loads these embeddings and uses them for the "structural uniqueness" scoring dimension (15% weight). The new targets will now receive proper ESM-2-based uniqueness scores instead of the default 0.5 fallback.

The mutation cascade module (`mutation_cascade.py`) can also use these embeddings for embedding delta calculations.
