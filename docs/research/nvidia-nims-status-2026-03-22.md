# NVIDIA NIM Biology API Status Report

**Date**: 2026-03-22
**Tested from**: moltbot server (217.154.10.79)
**API Key**: `nvapi-wEj_...` (70 chars, valid)
**Platform adapter**: `src/sma_platform/ingestion/adapters/nvidia_nims.py` (476 lines)

---

## Summary

| NIM | Status | HTTP Code | Cloud Available | In Our Adapter |
|-----|--------|-----------|-----------------|----------------|
| DiffDock v2.2 | LIVE | 400/500 (responds to POST) | Yes | Yes |
| OpenFold3 | LIVE | 422 (validates input) | Yes | Yes |
| GenMol v1.0 | LIVE (tested) | 200 | Yes | Yes |
| MolMIM | LIVE (tested) | 200 | Yes | Yes |
| ESM-2 650M | DEGRADED | 500 (internal error) | Yes (intermittent) | No (used via other routes) |
| RNAPro | NOT AVAILABLE | 404 | No cloud API | Yes (adapter exists, endpoint dead) |
| AlphaFold2 | LIVE | 422 (validates input) | Yes | No |
| AlphaFold2-Multimer | LIVE | 422 (validates input) | Yes | No |
| ESMfold | LIVE | 422 (validates input) | Yes | No |
| RFdiffusion | LIVE | 422 (validates input) | Yes | No |
| ProteinMPNN | LIVE | 422 (validates input) | Yes | No |
| MSA Search | LIVE (tested) | 200 | Yes | No |
| Evo2 (40B) | NOT AVAILABLE | 404 | No cloud API (self-host only) | No |
| OpenFold2 | NOT AVAILABLE | 404 | No cloud API | No |
| Boltz-2 | NOT AVAILABLE | 404 | No cloud API | No |
| ReaSyn v2 | NOT AVAILABLE | 404 | No cloud API | No |
| nvQSP | NOT AVAILABLE | 404 | No cloud API | No |

**Legend**: LIVE = endpoint responds and validates input; LIVE (tested) = returned actual data; DEGRADED = endpoint exists but returns errors; NOT AVAILABLE = 404, no cloud endpoint exists.

---

## Detailed Results per NIM

### 1. DiffDock v2.2 (Molecular Docking) -- LIVE

- **Endpoint**: `https://health.api.nvidia.com/v1/biology/mit/diffdock`
- **Our adapter URL**: `DIFFDOCK_CLOUD_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"` (CORRECT)
- **Test result**: POST with empty body returns HTTP 500 (expected -- needs valid PDB/SDF). POST with minimal data returns HTTP 400 ("Bad request") confirming the endpoint is parsing input.
- **Status**: Operational. Our adapter is correctly configured.
- **Note**: DiffDock V2 (trained on PLINDER dataset) is 6.2x faster and 16% more accurate than V1.

### 2. OpenFold3 (Biomolecular Structure Prediction) -- LIVE

- **Endpoint**: `https://health.api.nvidia.com/v1/biology/openfold/openfold3/predict`
- **Our adapter URL**: `OPENFOLD3_URL = "https://health.api.nvidia.com/v1/biology/openfold/openfold3"` + `/predict` appended (CORRECT)
- **Test result**: HTTP 422 -- `{"error":"Invalid request: body -> inputs: Field required"}` -- endpoint exists and validates input schema.
- **Status**: Operational. Our adapter is correctly configured.
- **Note**: Supports protein + RNA + DNA + ligand complex prediction. Version 1.1.0+ adds structural template support.

### 3. GenMol v1.0 (De Novo Molecule Generation) -- LIVE (TESTED)

- **Endpoint**: `https://health.api.nvidia.com/v1/biology/nvidia/genmol/generate`
- **Our adapter URL**: `GENMOL_GENERATE_URL` (CORRECT)
- **Test result**: HTTP 200 -- returned actual molecules:
  ```json
  {"status":"success","molecules":[{"smiles":"c1ccccc1","score":0.443}]}
  ```
- **Status**: Fully operational and returning data.
- **Input format**: `{"smiles": "c1ccccc1.[*{5-10}]", "num_molecules": 2, "scoring": "QED"}`
- **Note**: Uses SAFE (Sequential Attachment-based Fragment Embedding) format. Our `genmol_from_4ap()` function should work.

### 4. MolMIM (Molecular Optimization) -- LIVE (TESTED)

- **Endpoint**: `https://health.api.nvidia.com/v1/biology/nvidia/molmim/generate`
- **Our adapter URL**: `MOLMIM_URL` (CORRECT)
- **Test result**: HTTP 200 -- returned actual molecules with QED scores:
  ```json
  {"molecules":"[{\"sample\": \"CCOc1ccccc1Oc1cnsc1CO\", \"score\": 0.887}, ...]","score_type":"QED"}
  ```
- **Status**: Fully operational and returning data.
- **Input format**: `{"smi": "CCO", "num_molecules": 2, "algorithm": "CMA-ES"}`

### 5. ESM-2 650M (Protein Embeddings) -- DEGRADED

- **Endpoint**: `https://health.api.nvidia.com/v1/biology/meta/esm2-650m`
- **Our adapter**: Not directly in `nvidia_nims.py`; used via `prioritization_v2.py`, `digital_twin.py`, `cascade.py`, `gpu.py`, `splice_predictor.py`
- **Test result**: HTTP 422 with wrong fields (confirms endpoint exists), but HTTP 500 ("Unknown error") with correct `{"sequences": [...]}` payload.
- **Status**: DEGRADED -- endpoint exists but returns internal server errors on valid requests. This may be a temporary NVIDIA infrastructure issue. The NVIDIA Developer Forums report similar 500 errors with NIM APIs.
- **Impact**: Our 15 existing protein embeddings are stored in DB and not affected. New embedding generation will fail until NVIDIA fixes this.

### 6. RNAPro (RNA 3D Structure Prediction) -- NOT AVAILABLE AS CLOUD API

- **Endpoint attempted**: `https://health.api.nvidia.com/v1/biology/nvidia/rnapro` (and `/predict`, `/generate` variants)
- **Our adapter URL**: `RNAPRO_URL = "https://health.api.nvidia.com/v1/biology/nvidia/rnapro"` (ENDPOINT DOES NOT EXIST)
- **Test result**: HTTP 404 on all path variants.
- **Status**: RNAPro does NOT have a cloud-hosted NIM on build.nvidia.com. It is only available as:
  - Self-hosted via NGC container: `catalog.ngc.nvidia.com/orgs/nvidia/teams/clara/collections/rnapro`
  - Open-source on GitHub: `github.com/NVIDIA-Digital-Bio/RNAPro`
  - Model weights on HuggingFace: `nvidia/RNAPro-Public-Best-500M`
- **Impact**: Our `rnapro_predict()` function in the adapter will always fail. Need to either self-host on Vast.ai or remove from the adapter.
- **Action needed**: Deploy RNAPro container on Vast.ai GPU instance, or wait for NVIDIA to add it as a cloud NIM.

### 7. MSA Search (Multiple Sequence Alignment) -- LIVE (TESTED)

- **Endpoint**: `https://health.api.nvidia.com/v1/biology/colabfold/msa-search/predict`
- **Our adapter**: Not integrated.
- **Test result**: HTTP 200 -- returned actual MSA alignments against Uniref30, PDB70, and colabfold_envdb databases.
- **Status**: Fully operational. Required by AlphaFold2 for structure prediction pipeline.

---

## NIMs NOT in Our Adapter But Available as Cloud APIs

### AlphaFold2 -- LIVE
- **Endpoint**: `https://health.api.nvidia.com/v1/biology/deepmind/alphafold2`
- **HTTP 422**: Validates input -- requires `sequence` field
- **Use case**: Protein structure prediction (5x speedup). Could complement OpenFold3 for single-protein structures.

### AlphaFold2-Multimer -- LIVE
- **Endpoint**: `https://health.api.nvidia.com/v1/biology/deepmind/alphafold2-multimer`
- **HTTP 422**: Validates input -- requires `sequences` field
- **Use case**: Multi-protein complex structure prediction (1-6 chains).

### ESMfold -- LIVE
- **Endpoint**: `https://health.api.nvidia.com/v1/biology/meta/esmfold`
- **HTTP 422**: Validates input -- requires `sequence` field
- **Use case**: Fast single-sequence protein structure prediction (no MSA needed). Faster than AlphaFold2 for screening.

### RFdiffusion -- LIVE
- **Endpoint**: `https://health.api.nvidia.com/v1/biology/ipd/rfdiffusion/generate`
- **HTTP 422**: Validates input -- requires `contigs` field
- **Use case**: Protein design/generation. Could design novel binders for SMA-relevant proteins.

### ProteinMPNN -- LIVE
- **Endpoint**: `https://health.api.nvidia.com/v1/biology/ipd/proteinmpnn/predict`
- **HTTP 422**: Validates input -- requires PDB input
- **Use case**: Predict amino acid sequences for protein backbones. Useful for protein engineering.

---

## NIMs NOT Available as Cloud APIs (Self-Host Only)

| NIM | Status | Where Available |
|-----|--------|-----------------|
| Evo2 (40B) | 404 | NGC container only. DNA generative model, 1M bp context. |
| OpenFold2 | 404 | NGC container only. Predecessor to OpenFold3. |
| Boltz-2 | 404 | NGC container only. Alternative structure predictor. |
| ReaSyn v2 | 404 | Not found anywhere as cloud API. |
| nvQSP | 404 | Not found as cloud API. GPU-accelerated QSP simulation. |
| RNAPro | 404 | NGC + GitHub + HuggingFace only. |

---

## GTC 2026 New Announcements (March 16, 2026)

Models announced at GTC 2026 that are relevant to SMA research:

### Already Available as NIMs
1. **DiffDock V2** -- Already in our adapter, LIVE
2. **OpenFold3** -- Already in our adapter, LIVE
3. **GenMol** -- Already in our adapter, LIVE

### New at GTC 2026 -- Not Yet Integrated
4. **Proteina-Complexa** -- Protein binder design model (presented at ICLR 2026). NOT yet available as cloud NIM (404). Available via NVIDIA research.
5. **nvQSP** -- GPU-accelerated Quantitative Systems Pharmacology. 77x faster than CPU. NOT a NIM, but a simulation tool.
6. **AlphaFold DB Expansion** -- 30M new protein complex predictions added to AlphaFold DB (collaboration with DeepMind, EMBL, Seoul National University).
7. **Evo2** -- DNA generative AI with 1M bp context. Available as blueprint on build.nvidia.com but NOT as cloud API.
8. **BioNeMo Recipes** -- Standardized model training/customization format (January 2026).

---

## Adapter Code Issues Found

### 1. RNAPro endpoint is dead
```python
RNAPRO_URL = "https://health.api.nvidia.com/v1/biology/nvidia/rnapro"
```
This endpoint returns 404. RNAPro has no cloud NIM. The `rnapro_predict()` function will always fail.

### 2. GenMol uses correct field names
The adapter sends `"smiles"` which is CORRECT per the docs. The endpoint accepts both SMILES and SAFE format through the `smiles` field. Our adapter is correct.

### 3. ESM-2 not in NIM adapter
ESM-2 is used across 5 route files but not through the NIM adapter. It may be using a different integration path. If it relies on the cloud API, it will currently fail (500 errors).

### 4. Missing NIMs we could integrate
The following cloud NIMs are LIVE and could add value to our platform:
- **AlphaFold2**: Single protein structure prediction (fast, reliable)
- **AlphaFold2-Multimer**: Protein complex structures
- **ESMfold**: Ultra-fast protein folding (no MSA needed)
- **RFdiffusion**: De novo protein design
- **ProteinMPNN**: Protein sequence design
- **MSA Search**: Required for AlphaFold2 pipeline

---

## Recommendations

### Immediate (This Week)
1. **Fix RNAPro**: Remove from health check or add clear error handling. Consider self-hosting on Vast.ai if RNA structure prediction is needed.
2. **Monitor ESM-2**: The 500 errors may be temporary. Check again in 24-48 hours. If persistent, file a bug on NVIDIA Developer Forums.
3. **Test DiffDock end-to-end**: Run `redock_4ap_with_diffdock_v2()` to validate our DiffDock V2 integration actually works with real data.

### Short-term (This Month)
4. **Integrate AlphaFold2**: Add to adapter for fast protein structure prediction as complement to OpenFold3.
5. **Integrate ESMfold**: Ultra-fast structure screening without MSA requirement.
6. **Integrate MSA Search**: Already returning data, useful as prerequisite for AlphaFold2.

### Medium-term (April 2026)
7. **Self-host RNAPro on Vast.ai**: Critical for SMN2 pre-mRNA structure analysis.
8. **Evaluate Proteina-Complexa**: When/if it becomes a cloud NIM, integrate for binder design.
9. **Evaluate Evo2**: If we need DNA-level analysis (SMN2 locus), self-host the 40B model.

---

## Credit Usage

Unable to verify remaining NVIDIA API credits via API. Check manually at https://build.nvidia.com (account started with 1000 free credits).

---

## Sources

- [NVIDIA NIM Biology Models Catalog](https://build.nvidia.com/explore/biology)
- [NVIDIA NIM DiffDock Documentation](https://docs.nvidia.com/nim/bionemo/diffdock/latest/index.html)
- [NVIDIA NIM OpenFold3 Documentation](https://docs.nvidia.com/nim/bionemo/openfold3/latest/overview.html)
- [NVIDIA NIM GenMol Endpoints](https://docs.nvidia.com/nim/bionemo/genmol/latest/endpoints.html)
- [NVIDIA NIM AlphaFold2 Endpoints](https://docs.nvidia.com/nim/bionemo/alphafold2/latest/endpoints.html)
- [NVIDIA GTC 2026 News](https://blogs.nvidia.com/blog/gtc-2026-news/)
- [NVIDIA BioNeMo Expansion (January 2026)](https://nvidianews.nvidia.com/news/nvidia-bionemo-platform-adopted-by-life-sciences-leaders-to-accelerate-ai-driven-drug-discovery)
- [NVIDIA NIM ESM-2 650M](https://build.nvidia.com/meta/esm2-650m/modelcard)
- [RNAPro on GitHub](https://github.com/NVIDIA-Digital-Bio/RNAPro)
- [RNAPro on HuggingFace](https://huggingface.co/nvidia/RNAPro-Public-Best-500M)
- [NVIDIA Developer Forums - NIM 500 Errors](https://forums.developer.nvidia.com/t/nvidia-nim-api-invoked-by-langchain-returns-statuscode-500/305501)
