"""Publish SMA Research Platform data to HuggingFace as a public dataset.

Exports claims, hypotheses, targets, drugs, trials, and evidence as Parquet files
with a dataset card. This makes the SMA evidence graph available for ML research.

Run:   python scripts/publish_huggingface_dataset.py
Deps:  pip install huggingface_hub pandas pyarrow

Env:   HF_TOKEN — HuggingFace write token (https://huggingface.co/settings/tokens)
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hf-publish")

REPO_ID = "Bryzant-Labs/sma-evidence-graph"
EXPORT_DIR = Path(__file__).parent.parent / "data" / "hf-export"

TABLES = [
    ("targets", "SELECT id, symbol, name, target_type, organism, description, identifiers, metadata, created_at, updated_at FROM targets ORDER BY symbol"),
    ("drugs", "SELECT id, name, brand_names, drug_type, mechanism, targets, approval_status, approved_for, manufacturer, metadata, created_at FROM drugs ORDER BY name"),
    ("trials", "SELECT nct_id, title, status, phase, conditions, interventions, sponsor, start_date, completion_date, enrollment, results_summary, url FROM trials ORDER BY nct_id"),
    ("sources", "SELECT id, source_type, external_id, title, authors, journal, pub_date, doi, url, abstract, created_at FROM sources ORDER BY pub_date DESC"),
    ("claims", "SELECT id, claim_type, subject_id, subject_type, predicate, object_id, object_type, value, confidence, metadata, created_at FROM claims ORDER BY confidence DESC"),
    ("evidence", "SELECT id, claim_id, source_id, excerpt, figure_ref, method, sample_size, p_value, effect_size, metadata FROM evidence"),
    ("hypotheses", "SELECT id, hypothesis_type, title, description, rationale, supporting_evidence, confidence, status, generated_by, metadata, created_at FROM hypotheses ORDER BY confidence DESC"),
    ("graph_edges", "SELECT id, src_id, dst_id, relation, direction, confidence, metadata, created_at FROM graph_edges ORDER BY confidence DESC"),
    ("drug_outcomes", "SELECT id, compound_name, target, mechanism, outcome, failure_reason, failure_detail, trial_phase, model_system, key_finding, confidence, source_id, created_at FROM drug_outcomes ORDER BY compound_name"),
]

DATASET_CARD = """---
license: cc-by-4.0
language:
- en
tags:
- biology
- spinal-muscular-atrophy
- sma
- drug-discovery
- evidence-graph
- biomedical
- clinical-trials
- gene-targets
size_categories:
- 10K<n<100K
task_categories:
- text-classification
- question-answering
pretty_name: SMA Evidence Graph
---

# SMA Evidence Graph

An open-source, evidence-first dataset for Spinal Muscular Atrophy (SMA) drug research.

## Description

This dataset contains structured evidence extracted from PubMed papers, clinical trials
from ClinicalTrials.gov, and computationally generated hypotheses linking gene targets
to potential therapeutic interventions for SMA.

**Built by a researcher who has SMA**, this dataset aims to accelerate drug discovery
by making the evidence landscape machine-readable and openly accessible.

## Dataset Structure

| Split | Description | Records |
|-------|-------------|---------|
| `targets` | Gene/protein/pathway targets relevant to SMA | {targets_count} |
| `drugs` | Approved and investigational therapies | {drugs_count} |
| `trials` | Clinical trials from ClinicalTrials.gov | {trials_count} |
| `sources` | PubMed papers with abstracts | {sources_count} |
| `claims` | Structured claims extracted from abstracts (LLM) | {claims_count} |
| `evidence` | Links between claims and source papers | {evidence_count} |
| `hypotheses` | Generated hypothesis cards per target | {hypotheses_count} |
| `graph_edges` | Knowledge graph edges (STRING, KEGG, ChEMBL) | {edges_count} |

## Key Features

- **Evidence-first**: Every claim traces back to a PubMed source with excerpt and method
- **Multi-modal**: Combines literature, clinical trials, protein interactions, and pathway data
- **Scored**: Claims and hypotheses have computed confidence scores
- **Typed claims**: gene_expression, drug_efficacy, splicing_event, biomarker, etc.
- **Knowledge graph**: Protein-protein interactions (STRING), pathway co-membership (KEGG), compound bioactivity (ChEMBL)

## Core SMA Targets

| Symbol | Role |
|--------|------|
| SMN1 | Primary SMA gene (absent in patients) |
| SMN2 | Paralog, copy number = severity modifier |
| STMN2 | Axonal growth regulator |
| PLS3 | Actin-bundling, natural severity modifier |
| NCALD | Calcium sensor, knockdown rescues SMA |
| UBA1 | Ubiquitin homeostasis, dysregulated in SMA |

## Approved Therapies

1. **Nusinersen** (Spinraza) — ASO targeting SMN2 ISS-N1
2. **Risdiplam** (Evrysdi) — Small molecule SMN2 splicing modifier
3. **Onasemnogene** (Zolgensma) — AAV9 gene replacement

## Usage

```python
from datasets import load_dataset

ds = load_dataset("Bryzant-Labs/sma-evidence-graph")

# Access claims
claims = ds["claims"]
high_confidence = claims.filter(lambda x: x["confidence"] and x["confidence"] > 0.7)

# Access hypotheses
hypotheses = ds["hypotheses"]

# Access knowledge graph
edges = ds["graph_edges"]
```

## Citation

If you use this dataset, please cite:

```bibtex
@misc{{sma-evidence-graph-2026,
  title={{SMA Evidence Graph: An Open Dataset for Spinal Muscular Atrophy Drug Discovery}},
  author={{Christian Fischer}},
  year={{2026}},
  publisher={{HuggingFace}},
  url={{https://huggingface.co/datasets/Bryzant-Labs/sma-evidence-graph}}
}}
```

## Updates

This dataset is updated daily via an automated pipeline that pulls new PubMed papers,
clinical trials, and re-extracts claims from new abstracts.

Last updated: {last_updated}

## License

CC-BY-4.0 — free to use for research, attribution required.

## Links

- Platform: [sma-research.info](https://sma-research.info)
- GitHub: [Bryzant-Labs/sma-platform](https://github.com/Bryzant-Labs/sma-platform)
"""


def serialize_row(row: dict) -> dict:
    """Convert a database row to JSON-safe dict for Parquet."""
    out = {}
    for k, v in row.items():
        if v is None:
            out[k] = None
        elif isinstance(v, UUID):
            out[k] = str(v)
        elif isinstance(v, (list, dict)):
            out[k] = json.dumps(v, default=str)
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = str(v) if not isinstance(v, (int, float, bool)) else v
    return out


async def export_tables() -> dict[str, int]:
    """Export all tables to Parquet files."""
    from sma_platform.core.config import settings
    from sma_platform.core.database import close_pool, fetch, init_pool

    await init_pool(settings.database_url)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    counts = {}

    try:
        import pandas as pd

        for table_name, query in TABLES:
            logger.info("Exporting %s...", table_name)
            rows = await fetch(query)
            data = [serialize_row(dict(r)) for r in rows]

            if not data:
                logger.warning("  %s: no data, skipping", table_name)
                counts[table_name] = 0
                continue

            df = pd.DataFrame(data)
            output_path = EXPORT_DIR / f"{table_name}.parquet"
            df.to_parquet(output_path, index=False, engine="pyarrow")

            counts[table_name] = len(data)
            logger.info("  %s: %d rows → %s", table_name, len(data), output_path.name)

    finally:
        await close_pool()

    return counts


def write_dataset_card(counts: dict[str, int]) -> Path:
    """Write the README.md dataset card with actual counts."""
    card = DATASET_CARD.format(
        targets_count=counts.get("targets", 0),
        drugs_count=counts.get("drugs", 0),
        trials_count=counts.get("trials", 0),
        sources_count=counts.get("sources", 0),
        claims_count=counts.get("claims", 0),
        evidence_count=counts.get("evidence", 0),
        hypotheses_count=counts.get("hypotheses", 0),
        edges_count=counts.get("graph_edges", 0),
        last_updated=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )
    readme_path = EXPORT_DIR / "README.md"
    readme_path.write_text(card)
    logger.info("Dataset card written to %s", readme_path)
    return readme_path


def upload_to_huggingface(counts: dict[str, int]) -> str:
    """Upload Parquet files and dataset card to HuggingFace Hub."""
    from huggingface_hub import HfApi

    token = os.environ.get("HF_TOKEN")
    if not token:
        logger.error("HF_TOKEN not set — cannot upload. Export files are in %s", EXPORT_DIR)
        return "local_only"

    api = HfApi(token=token)

    # Create repo if it doesn't exist
    try:
        api.create_repo(repo_id=REPO_ID, repo_type="dataset", exist_ok=True)
    except Exception as e:
        logger.error("Failed to create HF repo: %s", e)
        return "error"

    # Upload all files
    files_to_upload = list(EXPORT_DIR.glob("*.parquet")) + [EXPORT_DIR / "README.md"]
    for f in files_to_upload:
        if not f.exists():
            continue
        logger.info("Uploading %s...", f.name)
        api.upload_file(
            path_or_fileobj=str(f),
            path_in_repo=f.name,
            repo_id=REPO_ID,
            repo_type="dataset",
        )

    logger.info("Upload complete: https://huggingface.co/datasets/%s", REPO_ID)
    return "uploaded"


async def main():
    logger.info("=== SMA HuggingFace Dataset Export ===")

    # Export tables to Parquet
    counts = await export_tables()
    total = sum(counts.values())
    logger.info("Exported %d total rows across %d tables", total, len([c for c in counts.values() if c > 0]))

    # Write dataset card
    write_dataset_card(counts)

    # Upload to HuggingFace
    status = upload_to_huggingface(counts)
    if status == "local_only":
        logger.info("Files exported to %s — set HF_TOKEN to upload", EXPORT_DIR)
    elif status == "uploaded":
        logger.info("Dataset published to https://huggingface.co/datasets/%s", REPO_ID)

    logger.info("=== Export complete ===")


if __name__ == "__main__":
    asyncio.run(main())
