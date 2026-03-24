#!/usr/bin/env bash
# Post 3 convergence v2 hypothesis cards to the SMA platform API.
# Requires the updated hypothesis_gen.py with POST /hypotheses endpoint.
#
# Usage: bash scripts/post_convergence_v2_hypotheses.sh
#
# NOTE: Deploy the updated hypothesis_gen.py first, then run this script.

BASE_URL="https://sma-research.info/api/v2"
ADMIN_KEY="sma-admin-2026"

echo "=== Posting Convergence Synthesis v2 Hypotheses ==="
echo ""

# Hypothesis 1: ROCK-LIMK2-CFL2 axis
echo "--- Hypothesis 1: ROCK-LIMK2-CFL2 axis ---"
curl -s -X POST "${BASE_URL}/hypotheses" \
  -H "Content-Type: application/json" \
  -H "x-admin-key: ${ADMIN_KEY}" \
  -d '{
    "hypothesis_type": "mechanism",
    "title": "ROCK-LIMK2-CFL2 axis is the primary druggable cascade in SMA motor neurons",
    "description": "Cross-dataset convergence from GSE287257 (ALS snRNA-seq, 61,664 cells) and GSE208629 (SMA scRNA-seq, 39,136 cells) identifies the ROCK-LIMK2-CFL2 signaling cascade as the most consistently dysregulated druggable pathway in SMA motor neurons. LIMK2 is upregulated +2.81x (p=0.002) in SMA MNs, ROCK1/2 are both elevated, and CFL2 is up +1.83x (p=2e-4) as a compensatory response. Fasudil (ROCK inhibitor) has Phase 2 ALS safety data (PMID 39424560) and SMA mouse efficacy (PMID 22397316).",
    "rationale": "SMN deficiency disrupts the SMN-PFN2a complex (PMID 21920940), leading to RhoA/ROCK hyperactivation (PMID 25221469). ROCK phosphorylates LIMK2 (not LIMK1 in SMA context), which hyperphosphorylates CFL2, inactivating it and disrupting actin dynamics. 10/14 actin pathway genes are upregulated in SMA MNs (GSE208629). CORO1C deprioritized as glial marker (depleted in SMA MNs: -1.81 log2FC). LIMK1-to-LIMK2 switch (LIMK2 UP +2.81x in SMA, LIMK1 DOWN -0.81x in ALS) confirms LIMK2 as the disease-relevant kinase.",
    "confidence": 0.82,
    "status": "proposed",
    "generated_by": "convergence-synthesis-v2",
    "metadata": {
      "convergence_version": "v2",
      "datasets": ["GSE287257", "GSE208629", "GSE69175", "GSE113924"],
      "key_genes": ["ROCK1", "ROCK2", "LIMK2", "CFL2", "PFN2"],
      "drug_candidates": ["Fasudil", "LIMK2 inhibitor (MDI-114215 class)", "Risdiplam"],
      "therapeutic_strategy": "Triple therapy: Risdiplam + Fasudil + LIMK2i",
      "single_cell_validated": true
    }
  }' | python3 -m json.tool 2>/dev/null
echo ""

# Hypothesis 2: CFL2 biomarker
echo "--- Hypothesis 2: CFL2 phosphorylation biomarker ---"
curl -s -X POST "${BASE_URL}/hypotheses" \
  -H "Content-Type: application/json" \
  -H "x-admin-key: ${ADMIN_KEY}" \
  -d '{
    "hypothesis_type": "biomarker",
    "title": "CFL2 phosphorylation status as SMA-specific biomarker distinguishing compensation from failure",
    "description": "CFL2 shows opposite regulation in SMA vs ALS motor neurons: UP +1.83x (p=2e-4) in SMA MNs (GSE208629) vs DOWN -0.94x (p=0.024) in ALS MNs (GSE287257). This disease-specific signature makes CFL2 and its phosphorylation state (p-CFL2/CFL2 ratio) a candidate biomarker for: (1) distinguishing SMA from ALS molecularly, (2) monitoring therapeutic response to ROCK/LIMK inhibitors, (3) tracking compensation-to-failure transition.",
    "rationale": "In SMA MNs, CFL2 upregulation = active compensation (maintaining actin dynamics despite SMN-profilin disruption). In ALS MNs, CFL2 downregulation = compensation collapse. p-CFL2/CFL2 ratio reflects LIMK2 activity: high = LIMK2 hyperphosphorylating cofilin (SMA), low = kinase failure (late ALS). Measurable in CSF or via RNAscope/IHC. Fasudil treatment should decrease p-CFL2/CFL2 ratio (target engagement). Bulk GSE69175 (+2.9x) and single-cell GSE208629 (+1.83x) both confirm CFL2 upregulation in SMA MNs.",
    "confidence": 0.68,
    "status": "proposed",
    "generated_by": "convergence-synthesis-v2",
    "metadata": {
      "convergence_version": "v2",
      "datasets": ["GSE287257", "GSE208629", "GSE69175"],
      "key_genes": ["CFL2"],
      "biomarker_type": "disease-specific molecular marker",
      "measurement_methods": ["Western blot (p-CFL2/CFL2)", "CSF proteomics", "RNAscope", "IHC"],
      "single_cell_validated": true
    }
  }' | python3 -m json.tool 2>/dev/null
echo ""

# Hypothesis 3: LIMK2 inhibitor strategy
echo "--- Hypothesis 3: LIMK2-selective inhibition ---"
curl -s -X POST "${BASE_URL}/hypotheses" \
  -H "Content-Type: application/json" \
  -H "x-admin-key: ${ADMIN_KEY}" \
  -d '{
    "hypothesis_type": "therapeutic",
    "title": "LIMK2-selective inhibition as Fasudil augmentation strategy in SMA",
    "description": "LIMK2 is upregulated +2.81x (p=0.002) in SMA motor neurons (GSE208629), the most strongly induced kinase in the ROCK-cofilin pathway. Adding a LIMK2-selective inhibitor to Fasudil provides dual-level pathway blockade. Tool compounds exist (MDI-114215, LX7101 Phase I glaucoma), but no LIMK inhibitor has been tested in any motor neuron disease model.",
    "rationale": "LIMK1-to-LIMK2 switch: LIMK2 (not LIMK1) is the SMA-relevant kinase. In ALS MNs, LIMK1 DOWN (-0.81, p=0.004) while LIMK2 UP (+1.01, p=0.009). In SMA MNs, LIMK2 even stronger (+2.81x). Fasudil alone may be insufficient because: (1) ROCK has many substrates beyond LIMK; (2) LIMK2 can be activated by PAK independently of ROCK; (3) SMA mouse Fasudil data shows improvement but not cure (PMID 22397316). Priority experiment: test MDI-114215 in SMA iPSC-MNs measuring neurite length, actin rods, p-CFL2/CFL2 ratio.",
    "confidence": 0.72,
    "status": "proposed",
    "generated_by": "convergence-synthesis-v2",
    "metadata": {
      "convergence_version": "v2",
      "datasets": ["GSE287257", "GSE208629"],
      "key_genes": ["LIMK2", "LIMK1", "CFL2", "ROCK1", "ROCK2"],
      "drug_candidates": ["MDI-114215", "LX7101", "FRAX486"],
      "combination_with": "Fasudil",
      "therapeutic_strategy": "Dual kinase cascade blockade: ROCK + LIMK2",
      "single_cell_validated": true
    }
  }' | python3 -m json.tool 2>/dev/null
echo ""

echo "=== Done ==="
echo "NOTE: If POST /hypotheses returns 405, deploy the updated hypothesis_gen.py first."
