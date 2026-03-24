# SMA Research Platform — API Guide for Researchers

**Base URL:** `https://sma-research.info/api/v2`
**OpenAPI/Swagger UI:** [https://sma-research.info/api/v2/docs](https://sma-research.info/api/v2/docs)
**ReDoc:** [https://sma-research.info/api/v2/redoc](https://sma-research.info/api/v2/redoc)

All endpoints return JSON. No authentication required for read-only (GET) access.
Write endpoints (POST/PUT) require an admin API key via `X-Admin-Key` header.

---

## 1. Quick Start — 3 Commands to Get Going

```bash
# 1. Platform overview — how much data is available?
curl -s https://sma-research.info/api/v2/stats | python3 -m json.tool

# 2. Get all molecular targets ranked by prioritization score
curl -s "https://sma-research.info/api/v2/scores?mode=discovery" | python3 -m json.tool

# 3. Search claims about drug efficacy
curl -s "https://sma-research.info/api/v2/claims?claim_type=drug_efficacy&limit=10" | python3 -m json.tool
```

---

## 2. Key Endpoints

### Platform Statistics

| Endpoint | Description |
|----------|-------------|
| `GET /stats` | Overview counts: sources, targets, drugs, trials, datasets, claims, evidence, hypotheses |
| `GET /stats/freshness` | Last ingestion timestamps and data freshness |
| `GET /stats/pipeline` | Pipeline stage statistics |
| `GET /health` | Health check (returns `{"status": "ok"}`) |

**Example:**
```bash
curl -s https://sma-research.info/api/v2/stats
```
```json
{
  "sources": 4200,
  "targets": 68,
  "drugs": 312,
  "trials": 187,
  "datasets": 45,
  "claims": 14176,
  "evidence": 8500,
  "hypotheses": 1285
}
```

---

### Molecular Targets

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /targets` | List all targets | `target_type`, `limit` (1-2000, default 100), `offset` |
| `GET /targets/{target_id}` | Single target by UUID | — |
| `GET /targets/symbol/{symbol}` | Target by gene symbol | e.g., `SMN2`, `ROCK2`, `LIMK1` |
| `GET /targets/{target_id}/deep-dive` | Full view: claims, hypotheses, drugs, trials, network | — |

**Example — get target by symbol:**
```bash
curl -s https://sma-research.info/api/v2/targets/symbol/ROCK2
```

**Example — list all gene targets:**
```bash
curl -s "https://sma-research.info/api/v2/targets?target_type=gene&limit=200"
```

---

### Evidence Claims

Claims are LLM-extracted, quality-filtered assertions from PubMed literature.

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /claims` | Search and filter claims | `claim_type`, `confidence_min`, `confidence_max`, `target`, `q` (text search), `enriched` (bool), `limit` (1-10000), `offset` |
| `GET /claims/count` | Get total counts by type | Same filters as above |
| `GET /claims/{claim_id}` | Single claim by UUID | — |
| `GET /claims/{claim_id}/evidence` | Evidence backing a claim | — |

**Valid `claim_type` values:**
`gene_expression`, `protein_interaction`, `pathway_membership`, `drug_target`, `drug_efficacy`, `biomarker`, `splicing_event`, `neuroprotection`, `motor_function`, `survival`, `safety`, `functional_interaction`, `other`

**Example — high-confidence drug efficacy claims:**
```bash
curl -s "https://sma-research.info/api/v2/claims?claim_type=drug_efficacy&confidence_min=0.8&limit=20"
```

**Example — claims mentioning a specific target (enriched with source paper info):**
```bash
curl -s "https://sma-research.info/api/v2/claims?target=ROCK2&enriched=true&limit=50"
```

---

### Hypotheses

Ranked hypotheses generated from convergence analysis of the evidence graph.

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /hypotheses` | List hypotheses ranked by confidence | `status`, `limit` (1-10000), `offset` |

**Example:**
```bash
curl -s "https://sma-research.info/api/v2/hypotheses?limit=20"
```

---

### Target Prioritization Scores

7-dimension scoring: genetic evidence, druggability, novelty, pathway centrality, cross-species conservation, clinical proximity, and safety.

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /scores` | All targets with composite prioritization scores | `min_score` (0-1), `mode` (`discovery` or `clinical`) |
| `GET /scores/{target_id}` | Detailed scorecard for one target | — |

**Example — discovery-mode scores (boosts novel targets):**
```bash
curl -s "https://sma-research.info/api/v2/scores?mode=discovery"
```

**Example — clinical-mode (weights established evidence):**
```bash
curl -s "https://sma-research.info/api/v2/scores?mode=clinical&min_score=0.5"
```

---

### Drugs & Therapies

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /drugs` | List drugs/therapies | `approval_status`, `drug_type`, `limit`, `offset` |
| `GET /drugs/{drug_id}` | Single drug details | — |

**Example — approved SMA drugs:**
```bash
curl -s "https://sma-research.info/api/v2/drugs?approval_status=approved"
```

---

### Clinical Trials

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /trials` | List clinical trials | `limit`, `offset` |

---

### Drug Screening & Virtual Screening

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /screen/pipeline-stats` | Screening funnel statistics (homepage viz) | — |
| `GET /screen/molecules` | Screened molecules from ChEMBL | — |
| `GET /screen/dual-target` | Dual-target screening candidates | — |
| `GET /screen/dual-target/synergy` | Synergy predictions | — |
| `GET /dock/score` | Score compounds against binding pockets | `pocket`, `limit` |

**Available binding pockets:** `SMN2_ISS_N1`, `SMN2_SPLICE_SITE`, `HDAC_CATALYTIC`, `MTOR_ATP_SITE`, `NCALD_CALCIUM_SITE`, `PLS3_ACTIN_INTERFACE`, `UBA1_UBIQUITIN_SITE`

**Example — top compounds for a binding pocket:**
```bash
curl -s "https://sma-research.info/api/v2/dock/score?pocket=SMN2_SPLICE_SITE&limit=20"
```

---

### AI-Designed Molecules (GenMol)

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /molecules/browser` | Paginated list with filters + sort | `target`, `method`, `bbb_only`, `min_qed`, `sort_by`, `limit`, `offset` |
| `GET /molecules/browser/stats` | Aggregate counts by target, method, BBB | — |
| `GET /molecules/browser/{id}` | Single molecule detail | — |
| `GET /molecules/browser/export` | Download as CSV or SDF | `fmt` (`csv` or `sdf`), `target`, `limit` |

**Example — BBB-permeable molecules for LIMK1:**
```bash
curl -s "https://sma-research.info/api/v2/molecules/browser?target=LIMK1&bbb_only=true&limit=50"
```

---

### Protein Structures

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /structures` | Predicted structures (best per target by pLDDT) | `symbol`, `source_filter`, `min_plddt`, `limit`, `offset` |
| `GET /pockets` | Binding pockets from fpocket analysis | — |
| `GET /pockets/druggable` | Druggable pockets only | — |
| `GET /pockets/{symbol}` | Pockets for a specific target | — |

**Example — high-confidence structures (pLDDT > 80):**
```bash
curl -s "https://sma-research.info/api/v2/structures?min_plddt=80"
```

---

### SMN2 Splice Prediction

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /splice/predict` | Predict variant effect on SMN2 splicing | `variant` (e.g., `c.6T>C`, `p.K42R`, `exon7:25G>C`) |
| `GET /splice/known-variants` | Curated known SMN2 variants with clinical annotations | — |
| `GET /splice/elements` | Key regulatory elements around SMN2 exon 7 | — |
| `GET /splice/benchmark` | Splicing benchmark data | — |

**Example — the critical SMN1/SMN2 difference:**
```bash
curl -s "https://sma-research.info/api/v2/splice/predict?variant=c.6T>C"
```

---

### News & Discoveries

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /news` | Published research highlights | `limit`, `offset`, `category` |
| `GET /news/{slug}` | Single post by URL slug | — |
| `GET /news/rss` | RSS feed | — |

**News categories:** `discovery`, `gpu_result`, `hypothesis`, `data_update`, `announcement`

---

### Convergence Analysis

| Endpoint | Description |
|----------|-------------|
| `GET /convergence/signals` | Cross-evidence convergence signals |
| `GET /convergence/synthesis` | Cross-paper synthesis results |

---

### Interaction Network

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /interactions` | Protein-protein and drug-target interaction network | — |
| `GET /interactions/target/{symbol}` | Interactions for a specific target | — |

---

### Semantic Search

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /search` | Semantic + keyword hybrid search across claims and sources | `q`, `mode` (`semantic`, `keyword`, `hybrid`), `limit` |

**Example:**
```bash
curl -s "https://sma-research.info/api/v2/search?q=ROCK+inhibitor+motor+neuron&mode=hybrid&limit=20"
```

---

### Cross-Disease Candidates

| Endpoint | Description |
|----------|-------------|
| `GET /candidates` | Cross-disease drug repurposing candidates |
| `GET /candidates/target/{symbol}` | Candidates for a specific target |
| `GET /candidates/disease/{disease}` | Candidates from a specific disease |

---

### Cascade Predictions

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /cascade/predict` | Predict downstream signaling cascade effects | `gene`, `perturbation` |
| `GET /cascade/known` | Known signaling cascades in SMA | — |

---

### Experiment Design

| Endpoint | Description |
|----------|-------------|
| `GET /experiment/suggest/{target_symbol}` | Suggest experiments for a target |
| `GET /experiment/gaps` | Evidence gaps needing experimental validation |
| `GET /experiments/propose/{hypothesis_id}` | Propose experiments for a specific hypothesis |

---

### Advanced Analytics

| Endpoint | Description |
|----------|-------------|
| `GET /spatial/penetration` | Drug penetration modeling across CNS regions |
| `GET /spatial/expression` | Spatial gene expression data |
| `GET /spatial/silent-zones` | Therapeutic silent zones |
| `GET /omics/nanopore/catalog` | Nanopore sequencing datasets |
| `GET /comparative/species` | Cross-species target conservation |

---

## 3. Python Examples

### Basic: Get All Targets with Scores

```python
import requests

BASE = "https://sma-research.info/api/v2"

# Get scored and ranked targets
scores = requests.get(f"{BASE}/scores", params={"mode": "discovery"}).json()

for t in scores[:10]:
    print(f"{t['symbol']:10s} score={t['composite_score']:.3f}  "
          f"novelty={t.get('novelty_score', 'N/A')}")
```

### Search Claims by Type and Confidence

```python
import requests

BASE = "https://sma-research.info/api/v2"

# High-confidence drug efficacy claims with source info
resp = requests.get(f"{BASE}/claims", params={
    "claim_type": "drug_efficacy",
    "confidence_min": 0.8,
    "enriched": True,
    "limit": 100
})
claims = resp.json()

for c in claims:
    print(f"[{c['confidence']:.2f}] {c['predicate'][:80]}")
    if c.get("source_title"):
        print(f"  Source: {c['source_title']} (PMID: {c.get('source_pmid', '?')})")
```

### Deep-Dive into a Target

```python
import requests

BASE = "https://sma-research.info/api/v2"

# Find target UUID by symbol
target = requests.get(f"{BASE}/targets/symbol/ROCK2").json()
target_id = target["id"]

# Get full deep-dive: claims, hypotheses, drugs, trials, network edges
dive = requests.get(f"{BASE}/targets/{target_id}/deep-dive").json()

print(f"Target: {dive['target']['symbol']} — {dive['target']['name']}")
print(f"Claims: {len(dive.get('claims', []))}")
print(f"Hypotheses: {len(dive.get('hypotheses', []))}")
print(f"Drugs: {len(dive.get('drugs', []))}")
print(f"Trials: {len(dive.get('trials', []))}")
```

### Predict SMN2 Splice Variant Effect

```python
import requests

BASE = "https://sma-research.info/api/v2"

result = requests.get(f"{BASE}/splice/predict", params={
    "variant": "c.6T>C"
}).json()

print(f"Variant: {result['variant']}")
print(f"Effect: {result['predicted_effect']}")
print(f"Confidence: {result['confidence']}")
print(f"Mechanism: {result.get('mechanism', 'N/A')}")
```

### Download Molecules as CSV

```python
import requests
import pandas as pd
from io import StringIO

BASE = "https://sma-research.info/api/v2"

# Download BBB-permeable molecules as CSV
resp = requests.get(f"{BASE}/molecules/browser/export", params={
    "fmt": "csv",
    "bbb_only": True,
    "limit": 500
})

df = pd.read_csv(StringIO(resp.text))
print(f"Downloaded {len(df)} molecules")
print(df[["smiles", "target_symbol", "qed", "bbb_permeable"]].head(10))
```

---

## 4. R Examples

### Basic: Get Platform Stats

```r
library(httr)
library(jsonlite)

base_url <- "https://sma-research.info/api/v2"

# Platform overview
stats <- fromJSON(content(GET(paste0(base_url, "/stats")), "text"))
print(stats)
```

### Get Targets and Scores

```r
library(httr)
library(jsonlite)

base_url <- "https://sma-research.info/api/v2"

# All targets with discovery-mode scores
scores <- fromJSON(content(
  GET(paste0(base_url, "/scores"), query = list(mode = "discovery")),
  "text"
))

# Top 10 by composite score
top10 <- head(scores[order(-scores$composite_score), ], 10)
print(top10[, c("symbol", "composite_score", "novelty_score")])
```

### Search Claims and Build a Data Frame

```r
library(httr)
library(jsonlite)

base_url <- "https://sma-research.info/api/v2"

claims <- fromJSON(content(
  GET(paste0(base_url, "/claims"), query = list(
    claim_type = "gene_expression",
    confidence_min = 0.7,
    enriched = "true",
    limit = 200
  )),
  "text"
))

# Convert to data frame for analysis
df <- as.data.frame(claims)
cat("Total claims:", nrow(df), "\n")
cat("Unique sources:", length(unique(df$source_pmid)), "\n")
```

### Export Table as CSV

```r
library(httr)

base_url <- "https://sma-research.info/api/v2"

# Export targets table as CSV
resp <- GET(paste0(base_url, "/export/targets"), query = list(fmt = "csv", limit = 5000))
writeLines(content(resp, "text"), "sma_targets.csv")
cat("Saved sma_targets.csv\n")
```

---

## 5. Data Export

Bulk download any major table as JSON or CSV:

| Endpoint | Format | Description |
|----------|--------|-------------|
| `GET /export/{table_name}?fmt=json` | JSON | Default format |
| `GET /export/{table_name}?fmt=csv` | CSV | Download as CSV file |
| `GET /export/target/{symbol}?fmt=json` | JSON | All evidence for a specific target |
| `GET /export/target/{symbol}?fmt=csv` | CSV | Target evidence as CSV |
| `GET /export/target/{symbol}?fmt=bibtex` | BibTeX | Source citations for a target |
| `GET /molecules/browser/export?fmt=csv` | CSV | AI-designed molecules |
| `GET /molecules/browser/export?fmt=sdf` | SDF | Molecules in chemical SDF format |

**Exportable tables:** `targets`, `drugs`, `trials`, `claims`, `hypotheses`, `graph_edges`, `drug_outcomes`, `cross_species_targets`, `target_scores`, `molecule_screenings`

**Example — export all claims as CSV:**
```bash
curl -s "https://sma-research.info/api/v2/export/claims?fmt=csv&limit=5000" -o sma_claims.csv
```

**Example — export all evidence for ROCK2 as BibTeX:**
```bash
curl -s "https://sma-research.info/api/v2/export/target/ROCK2?fmt=bibtex"
```

---

## 6. Rate Limits & Practical Considerations

- **No authentication** required for GET requests
- **No formal rate limiting** is enforced, but please be respectful:
  - Avoid more than ~10 requests/second sustained
  - For bulk downloads, use the `/export` endpoints instead of paginating through `/claims`
  - Cache results locally when possible
- **Maximum `limit`** varies by endpoint (typically 100-10000, see parameter docs)
- **CORS** is restricted to `sma-research.info` — if calling from a browser on another domain, use a server-side proxy or curl
- **Write endpoints** (POST/PUT) require an admin API key and are not available for public use

**If you need higher limits or write access**, contact: christian@bryzant.com

---

## 7. Citation

If you use data from the SMA Research Platform in your research, please cite:

```
Fischer, C. (2026). SMA Research Platform — Open Evidence Graph for Spinal Muscular Atrophy.
https://sma-research.info
Bryzant Labs. Accessed [date].
```

**BibTeX:**
```bibtex
@misc{fischer2026sma,
  author = {Fischer, Christian},
  title = {{SMA Research Platform --- Open Evidence Graph for Spinal Muscular Atrophy}},
  year = {2026},
  url = {https://sma-research.info},
  note = {Accessed: 2026-03-25}
}
```

---

## 8. Full Endpoint Reference

For the complete list of 200+ endpoints with request/response schemas, see the interactive documentation:

- **Swagger UI:** [https://sma-research.info/api/v2/docs](https://sma-research.info/api/v2/docs)
- **ReDoc:** [https://sma-research.info/api/v2/redoc](https://sma-research.info/api/v2/redoc)
- **OpenAPI JSON:** [https://sma-research.info/api/v2/openapi.json](https://sma-research.info/api/v2/openapi.json)

---

*Last updated: 2026-03-25 | Platform version: 0.1.0 | Contact: christian@bryzant.com*
