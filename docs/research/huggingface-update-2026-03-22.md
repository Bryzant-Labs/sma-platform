# HuggingFace Dataset Update — 2026-03-22

## Dataset

- **Repository**: [SMAResearch/sma-evidence-graph](https://huggingface.co/datasets/SMAResearch/sma-evidence-graph)
- **License**: CC-BY-4.0
- **Format**: Parquet (11 tables)

## Export Summary

| Table | Rows | Notes |
|-------|------|-------|
| `targets` | 63 | Gene/protein/pathway targets |
| `drugs` | 21 | Approved and investigational therapies |
| `trials` | 451 | Clinical trials from ClinicalTrials.gov |
| `sources` | 6,535 | PubMed papers with abstracts |
| `claims` | 14,187 | Structured claims (LLM-extracted) |
| `evidence` | 14,176 | Claim-to-source evidence links |
| `hypotheses` | 1,472 | Generated hypothesis cards |
| `graph_edges` | 582 | Knowledge graph edges (STRING, KEGG, ChEMBL) |
| `drug_outcomes` | 227 | Drug success/failure database |
| `molecule_screenings` | 21,229 | ChEMBL/PubChem bioactive compounds |
| `splice_variants` | 726 | SMN2 splice variant benchmark |
| **Total** | **59,669** | |

## Upload Details

- **Script**: `scripts/publish_huggingface_dataset.py`
- **Token**: Moltbot HF_TOKEN (write access to SMAResearch org)
- **huggingface_hub**: v1.7.1
- **Workaround**: Temporarily commented out `NVIDIA_API_KEY_2` from `.env` to avoid Pydantic `extra_forbidden` validation error in `Settings` model. The `.env` was restored after the run.

## Issue Found

The `Settings` class in `src/sma_platform/core/config.py` does not allow extra fields (`extra="forbid"` is the default). The `.env` file contains `NVIDIA_API_KEY_2` which is not declared in the model. This should be fixed by either:
1. Adding `nvidia_api_key_2: str = ""` to the Settings model, or
2. Setting `model_config = {"extra": "ignore", ...}` to allow unknown env vars

## Dataset Card

Updated automatically by the publish script with current row counts and date (2026-03-22).
