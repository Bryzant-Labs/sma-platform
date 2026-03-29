"""Generate and seed 55+ hypotheses for SMA actin pathway targets.

Based on single-cell validation from GSE208629 (SMA mouse) and GSE287257
(human ALS), revealing the ROCK-LIMK2-CFL2 axis as the primary therapeutic
target in SMA motor neurons.

Supports two modes:
  1. Direct DB insert (default): python scripts/generate_hypotheses_actin_pathway.py
  2. HTTP POST to API:          python scripts/generate_hypotheses_actin_pathway.py --api

Run: python scripts/generate_hypotheses_actin_pathway.py [--api] [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ---------------------------------------------------------------------------
# All 55 hypotheses for the actin pathway targets
# ---------------------------------------------------------------------------

HYPOTHESES: list[dict] = [
    # ===================================================================
    # LIMK2 — PRIMARY SMA KINASE (12 hypotheses)
    # ===================================================================
    {
        "title": "LIMK2 hyperactivation drives actin-dependent motor neuron degeneration in SMA",
        "description": (
            "LIMK2 is upregulated +2.81x in SMA motor neurons (GSE208629, p=0.002) while "
            "LIMK1 is undetectable. This kinase switch means LIMK2 becomes the sole regulator "
            "of cofilin phosphorylation in SMA MNs, creating a pathological actin stabilization "
            "that impairs growth cone dynamics and synaptic vesicle recycling at the NMJ. "
            "Selective LIMK2 inhibition should restore actin turnover without affecting LIMK1-"
            "dependent processes in other cell types."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "mechanism",
        "tier": "A",
        "evidence_for": [
            "GSE208629: Limk2 UP +2.81x in SMA MNs (p=0.002)",
            "GSE208629: Limk1 NOT DETECTED in SMA MNs",
            "GSE287257: LIMK1 DOWN in ALS MNs, LIMK2 UP (compensatory switch)",
            "10/14 actin genes upregulated in SMA MNs (GSE208629)",
            "PMID 22397316: Fasudil (upstream ROCK inhibitor) improves SMA survival"
        ],
        "evidence_against": [
            "LIMK2 upregulation could be compensatory/protective rather than pathological",
            "No direct LIMK2 inhibitor tested in SMA models yet",
            "Single-cell data from mouse may not translate to human MN subtypes"
        ],
        "testable_prediction": "LIMK2-selective inhibitor (e.g., LIMKi3) should rescue neurite outgrowth in SMN-depleted iPSC-MNs without affecting LIMK1-dependent cortical neurons",
        "therapeutic_implication": "LIMK2-selective inhibitors could be more specific than pan-ROCK inhibitors like Fasudil, reducing off-target effects",
        "confidence": 0.78,
        "tags": ["actin", "kinase", "single-cell", "motor-neuron", "ROCK-LIMK2-CFL2"]
    },
    {
        "title": "LIMK1-to-LIMK2 isoform switch is a conserved motor neuron stress response across SMA and ALS",
        "description": (
            "In both SMA (GSE208629) and ALS (GSE287257), motor neurons show LIMK1 "
            "downregulation with compensatory LIMK2 upregulation. This suggests a conserved "
            "MN stress response where LIMK2, which has distinct substrate preferences and "
            "subcellular localization compared to LIMK1, becomes the dominant cofilin kinase "
            "under proteostatic stress. The switch may reflect differential regulation by "
            "Rho GTPases (ROCK to LIMK2) vs. Rac/Cdc42 to LIMK1 pathways."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "mechanism",
        "tier": "A",
        "evidence_for": [
            "GSE208629: Limk1 absent, Limk2 UP +2.81x in SMA MNs",
            "GSE287257: LIMK1 DOWN, LIMK2 UP in ALS MNs",
            "PMID 11978739: LIMK1 and LIMK2 have distinct tissue distributions",
            "PMID 18485879: LIMK2 preferentially activated by ROCK pathway"
        ],
        "evidence_against": [
            "Different MN subtypes may have different baseline LIMK ratios",
            "ALS and SMA have fundamentally different etiologies (protein aggregation vs. SMN loss)",
            "Cross-species comparison (mouse SMA vs. human ALS) limits direct comparison"
        ],
        "testable_prediction": "Single-cell RNA-seq of presymptomatic SMA and ALS MNs should show LIMK2/LIMK1 ratio increase as an early event before degeneration markers appear",
        "therapeutic_implication": "A shared LIMK isoform switch suggests LIMK2 inhibition could benefit both SMA and ALS, expanding therapeutic utility",
        "confidence": 0.72,
        "tags": ["actin", "kinase", "cross-disease", "ALS", "single-cell", "isoform-switch"]
    },
    {
        "title": "LIMK2 phosphorylation of CFL2 at Ser3 creates a toxic actin stabilization loop in SMA motor neurons",
        "description": (
            "Upregulated LIMK2 (+2.81x) phosphorylates CFL2 at Ser3, inactivating its "
            "actin-severing function. Simultaneously, CFL2 is transcriptionally upregulated "
            "(+1.83x), likely as a failed compensatory response to restore actin dynamics. "
            "The net result is excess phospho-CFL2 (inactive) accumulating while total CFL2 "
            "protein increases — a futile cycle that progressively stabilizes actin filaments "
            "and impairs synaptic vesicle endocytosis at the NMJ."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "mechanism",
        "tier": "A",
        "evidence_for": [
            "GSE208629: Limk2 UP +2.81x AND Cfl2 UP +1.83x in SMA MNs",
            "PMID 9390559: LIMK phosphorylates cofilin at Ser3, inactivating severing",
            "PMID 22397316: Fasudil (ROCK to LIMK inhibitor) rescues SMA phenotype",
            "PMID 28377503: Actin dynamics critical for NMJ maintenance in SMA"
        ],
        "evidence_against": [
            "Phospho-CFL2/total-CFL2 ratio not measured in SMA MNs",
            "CFL2 upregulation could be independently regulated, not a feedback response to LIMK2",
            "Other LIMK2 substrates (SSH1L) may contribute independently"
        ],
        "testable_prediction": "Western blot of SMA iPSC-MNs should show increased phospho-CFL2/total-CFL2 ratio compared to isogenic controls; LIMK2 inhibition should normalize the ratio",
        "therapeutic_implication": "Breaking the LIMK2-pCFL2 loop with LIMK2 inhibitors would be more specific than upstream ROCK inhibition",
        "confidence": 0.75,
        "tags": ["actin", "kinase", "phosphorylation", "CFL2", "ROCK-LIMK2-CFL2", "NMJ"]
    },
    {
        "title": "LIMK2 inhibition synergizes with Risdiplam by restoring SMN-independent actin homeostasis",
        "description": (
            "Risdiplam increases SMN protein but cannot fully restore actin pathway "
            "dysregulation in mature MNs. LIMK2 inhibition would directly normalize "
            "actin turnover downstream of SMN loss, addressing the residual actin "
            "pathology that persists even with partial SMN restoration. The combination "
            "attacks SMA from two independent axes: SMN protein level (Risdiplam) and "
            "actin dynamics (LIMK2i)."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "combinatorial",
        "tier": "B",
        "evidence_for": [
            "PMID 35587700: Risdiplam improves but does not normalize MN function in SMA patients",
            "GSE208629: Actin pathway massively dysregulated (10/14 genes UP) in SMA MNs",
            "PMID 22397316: Fasudil (ROCK/LIMK pathway) effective SMN-independently",
            "SMN-independent therapies needed for patients with advanced disease"
        ],
        "evidence_against": [
            "No clinical data on LIMK2 inhibitors in any neurodegenerative disease",
            "Drug-drug interactions between Risdiplam and LIMK2 inhibitors unknown",
            "LIMK2 inhibitors may not cross the blood-brain barrier efficiently"
        ],
        "testable_prediction": "Risdiplam + LIMKi3 should show greater neurite outgrowth rescue in SMN-depleted iPSC-MNs than either agent alone (synergy index >1.0)",
        "therapeutic_implication": "Combination therapy could improve outcomes for patients with incomplete Risdiplam response, especially late-treated Type 2/3 SMA",
        "confidence": 0.62,
        "tags": ["combination", "Risdiplam", "kinase", "SMN-independent", "clinical"]
    },
    {
        "title": "LIMK2 subcellular localization shifts to growth cones in SMA motor neurons",
        "description": (
            "LIMK2 has documented nuclear and cytoplasmic pools with distinct functions. "
            "In SMA MNs, the +2.81x LIMK2 upregulation may disproportionately increase the "
            "cytoplasmic/growth cone pool, creating localized actin hyperstabilization at "
            "the sites most critical for axon guidance and NMJ formation. This spatial "
            "redistribution, rather than total protein level alone, may drive the pathology."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "PMID 11809712: LIMK2 localizes to growth cones in developing neurons",
            "GSE208629: Limk2 UP +2.81x in SMA MNs",
            "PMID 28377503: Growth cone defects are early SMA pathology",
            "PMID 23263860: LIMK2 has nuclear export signal and shuttles between compartments"
        ],
        "evidence_against": [
            "Subcellular localization not measured in SMA — purely computational prediction",
            "scRNA-seq cannot resolve subcellular protein localization",
            "Growth cone-specific LIMK2 increase not distinguishable from global upregulation at RNA level"
        ],
        "testable_prediction": "Immunofluorescence of SMA iPSC-MN growth cones should show increased LIMK2 signal relative to soma compared to controls",
        "therapeutic_implication": "Growth cone-targeted LIMK2 inhibition could spare nuclear LIMK2 functions while rescuing axonal pathology",
        "confidence": 0.52,
        "tags": ["actin", "kinase", "growth-cone", "subcellular", "spatial"]
    },
    {
        "title": "LIMK2 overactivity impairs synaptic vesicle endocytosis at SMA neuromuscular junctions",
        "description": (
            "Actin dynamics are essential for clathrin-mediated endocytosis of synaptic "
            "vesicles at the NMJ. LIMK2-mediated cofilin phosphorylation stabilizes cortical "
            "actin, creating a rigid membrane skeleton that prevents vesicle retrieval. "
            "This mechanism explains the well-documented NMJ transmission failure in SMA "
            "that precedes MN death, and suggests LIMK2 inhibition could rescue synaptic "
            "function even in late-stage disease."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Limk2 UP +2.81x in SMA MNs",
            "PMID 16921379: Actin dynamics required for synaptic vesicle endocytosis",
            "PMID 26025607: NMJ transmission failure precedes MN death in SMA mice",
            "PMID 20457564: Cofilin regulates synaptic vesicle recycling"
        ],
        "evidence_against": [
            "NMJ defects could be primarily structural rather than endocytic",
            "Other actin regulators (PFN2, ACTG1) also contribute to NMJ dysfunction",
            "Endocytosis assays not performed in SMA NMJ context"
        ],
        "testable_prediction": "FM1-43 dye uptake at SMA mouse NMJs should be reduced; LIMK2 inhibition should restore vesicle cycling rate",
        "therapeutic_implication": "LIMK2 inhibition could rescue NMJ function in patients already on SMN-enhancing therapy with residual synaptic deficits",
        "confidence": 0.60,
        "tags": ["actin", "kinase", "NMJ", "endocytosis", "synaptic"]
    },
    {
        "title": "LIMK2 upregulation is driven by ROCK1/2 hyperactivation via RhoA in SMN-depleted motor neurons",
        "description": (
            "SMN depletion activates RhoA signaling, which activates ROCK1/2, which in turn "
            "phosphorylates and activates LIMK2. With ROCK1 and ROCK2 both upregulated in SMA "
            "MNs (GSE208629), the increased LIMK2 expression and activity is a downstream "
            "consequence of RhoA-ROCK hyperactivation. This places LIMK2 as the effector "
            "kinase and explains why Fasudil (ROCK inhibitor) rescues SMA: it works by "
            "reducing LIMK2 activity."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "mechanism",
        "tier": "A",
        "evidence_for": [
            "GSE208629: Rock1, Rock2, and Limk2 all UP in SMA MNs",
            "PMID 22397316: Fasudil (ROCK inhibitor) rescues SMA in Smn2B/- mice",
            "PMID 10783251: ROCK directly phosphorylates LIMK at Thr505/Thr508",
            "PMID 25143584: RhoA activated in SMN-depleted cells"
        ],
        "evidence_against": [
            "LIMK2 transcriptional upregulation may be independent of ROCK kinase activity",
            "PAK (p21-activated kinase) also activates LIMK2",
            "Fasudil has pleiotropic effects beyond LIMK2 (myosin phosphatase, intermediate filaments)"
        ],
        "testable_prediction": "Fasudil treatment should reduce phospho-LIMK2 levels in SMA iPSC-MNs; ROCK inhibitor-resistant LIMK2 mutant should block Fasudil neurite rescue",
        "therapeutic_implication": "Validates Fasudil mechanism via LIMK2 and supports development of more selective LIMK2 inhibitors as next-generation therapy",
        "confidence": 0.80,
        "tags": ["actin", "kinase", "ROCK", "RhoA", "Fasudil", "ROCK-LIMK2-CFL2"]
    },
    {
        "title": "LIMK2 expression level predicts motor neuron vulnerability in SMA spinal cord",
        "description": (
            "Not all motor neurons degenerate equally in SMA — lumbar MNs are most vulnerable "
            "while ocular MNs are spared. LIMK2 expression level may correlate with vulnerability: "
            "MNs with higher baseline LIMK2 and lower compensatory CFL2 capacity would have "
            "less actin buffering and degenerate faster. This would make LIMK2/CFL2 ratio a "
            "cell-intrinsic vulnerability marker."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "biomarker",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Limk2 UP in SMA MNs but heterogeneous across cells",
            "PMID 25349423: Differential MN vulnerability in SMA follows rostral-caudal gradient",
            "PMID 11139429: Oculomotor MNs resistant in SMA; may have different actin regulation"
        ],
        "evidence_against": [
            "MN vulnerability likely multifactorial (not LIMK2 alone)",
            "Spatial transcriptomics needed to test — not available for SMA spinal cord",
            "Ocular MN resistance may relate to different synaptic properties, not actin"
        ],
        "testable_prediction": "Spatial transcriptomics of SMA mouse spinal cord should show higher LIMK2/CFL2 ratio in ventral horn lumbar MNs vs. oculomotor nuclei",
        "therapeutic_implication": "LIMK2/CFL2 ratio could stratify patients by predicted MN loss rate, guiding treatment urgency",
        "confidence": 0.48,
        "tags": ["biomarker", "vulnerability", "spatial", "motor-neuron", "stratification"]
    },
    {
        "title": "LIMK2 inhibition rescues dendritic spine density in SMA cortical and spinal neurons",
        "description": (
            "SMA patients, especially Type 1, show cognitive deficits and reduced cortical "
            "connectivity. LIMK2-mediated cofilin inactivation leads to actin stabilization in "
            "dendritic spines, preventing the dynamic remodeling needed for synaptic plasticity. "
            "LIMK2 inhibition should restore spine dynamics and improve synaptic connectivity "
            "in both spinal MNs and cortical neurons."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "PMID 25157159: SMA Type 1 patients show hippocampal and cortical abnormalities",
            "PMID 10509164: LIMK1 knockout causes abnormal dendritic spines; LIMK2 may be similar",
            "GSE208629: Limk2 UP in SMA MNs",
            "PMID 17150100: Cofilin-actin dynamics regulate dendritic spine morphology"
        ],
        "evidence_against": [
            "Cognitive deficits in SMA may be secondary to motor limitation, not primary",
            "LIMK2 role in dendritic spines less characterized than LIMK1",
            "Most SMA research focuses on MNs, not cortical neurons"
        ],
        "testable_prediction": "SMA iPSC-derived cortical neurons should show reduced spine density; LIMKi3 treatment should increase spine density and mEPSC frequency",
        "therapeutic_implication": "LIMK2 inhibition could address cognitive aspects of SMA beyond motor function",
        "confidence": 0.42,
        "tags": ["actin", "kinase", "dendritic-spine", "cognition", "cortical"]
    },
    {
        "title": "Selective LIMK2 degraders (PROTACs) offer superior therapeutic index over kinase inhibitors in SMA",
        "description": (
            "Kinase inhibitors of LIMK2 face selectivity challenges due to the conserved "
            "kinase domain shared with LIMK1. PROTAC-based degraders targeting LIMK2-specific "
            "structural features could achieve isoform selectivity by exploiting differences "
            "in protein-protein interactions or subcellular localization. Degradation would also "
            "remove scaffolding functions of LIMK2 that kinase inhibitors cannot address."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "therapeutic",
        "tier": "C",
        "evidence_for": [
            "PMID 31634902: PROTACs achieve selectivity between kinase family members",
            "LIMK2 has unique N-terminal domain different from LIMK1 (targetable for PROTAC)",
            "GSE208629: LIMK2 (not LIMK1) is the relevant SMA target — selectivity critical"
        ],
        "evidence_against": [
            "No LIMK2-selective PROTAC exists yet",
            "CNS delivery of PROTACs remains challenging (high molecular weight)",
            "LIMK2 degradation may have more severe effects than inhibition"
        ],
        "testable_prediction": "LIMK2-selective PROTAC should degrade LIMK2 but not LIMK1 in iPSC-MNs; neurite outgrowth rescue should exceed that of LIMKi3 (pan-LIMK inhibitor)",
        "therapeutic_implication": "PROTAC approach could provide the isoform selectivity needed for safe chronic LIMK2 targeting in SMA",
        "confidence": 0.35,
        "tags": ["PROTAC", "kinase", "drug-design", "selectivity", "therapeutic"]
    },
    {
        "title": "LIMK2 is a convergence node for SMN-dependent and SMN-independent SMA pathology",
        "description": (
            "Multiple SMA pathways converge on LIMK2: (1) SMN loss leads to RhoA activation leads to ROCK leads to "
            "LIMK2; (2) Reduced PLS3 leads to impaired actin bundling leads to compensatory LIMK2 upregulation; "
            "(3) UBA1 dysfunction leads to altered ubiquitin homeostasis leads to LIMK2 protein stabilization. "
            "This makes LIMK2 a master integration point where SMN-dependent and SMN-independent "
            "signals merge to drive actin pathology."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Limk2, Rock1, Rock2 all UP in SMA MNs",
            "PMID 22397316: Fasudil rescues SMA SMN-independently",
            "PMID 19270694: PLS3 identified as SMA modifier affecting actin dynamics",
            "PMID 23475966: UBA1 dysregulation in SMA affects multiple pathways"
        ],
        "evidence_against": [
            "Convergence model is largely computational — not experimentally validated",
            "Individual pathway contributions to LIMK2 not quantified",
            "PLS3 and UBA1 links to LIMK2 are indirect"
        ],
        "testable_prediction": "Phosphoproteomics of SMA vs. control iPSC-MNs should show LIMK2 substrates as the most enriched kinase-substrate set",
        "therapeutic_implication": "Targeting LIMK2 addresses multiple SMA pathomechanisms simultaneously, potentially more effective than single-pathway approaches",
        "confidence": 0.58,
        "tags": ["actin", "kinase", "convergence", "network", "SMN-independent"]
    },
    {
        "title": "CSF phospho-LIMK2 level correlates with motor neuron degeneration rate in SMA patients",
        "description": (
            "If LIMK2 is hyperactivated in degenerating SMA MNs, phospho-LIMK2 (active form) "
            "should be released into cerebrospinal fluid as MNs die. CSF phospho-LIMK2 could "
            "serve as a pharmacodynamic biomarker for ROCK/LIMK pathway inhibitors and as a "
            "prognostic marker for disease progression rate."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "biomarker",
        "tier": "C",
        "evidence_for": [
            "GSE208629: Limk2 UP +2.81x in SMA MNs",
            "PMID 30150366: CSF neurofilament is already a biomarker for MN degeneration in SMA",
            "Phospho-kinases detectable in CSF in neurodegenerative diseases (precedent from tau kinases in AD)"
        ],
        "evidence_against": [
            "Phospho-LIMK2 may be too unstable for CSF measurement",
            "LIMK2 expressed in many cell types — CSF signal may not be MN-specific",
            "No existing ELISA for phospho-LIMK2 in human CSF"
        ],
        "testable_prediction": "CSF samples from SMA patients should show higher phospho-LIMK2 than controls; levels should decrease after Fasudil treatment",
        "therapeutic_implication": "Would provide a pharmacodynamic biomarker to dose-optimize LIMK2/ROCK pathway inhibitors in clinical trials",
        "confidence": 0.38,
        "tags": ["biomarker", "CSF", "phosphorylation", "pharmacodynamic", "clinical"]
    },
    # ===================================================================
    # CFL2 — DISEASE-SPECIFIC BIOMARKER + THERAPEUTIC (10 hypotheses)
    # ===================================================================
    {
        "title": "CFL2 upregulation is a compensatory mechanism that delays motor neuron death in SMA",
        "description": (
            "CFL2 is upregulated +1.83x in SMA MNs (GSE208629) but downregulated -0.94x in "
            "ALS MNs (GSE287257). This opposite pattern suggests CFL2 upregulation in SMA is "
            "a protective compensatory response to LIMK2-mediated actin stabilization. CFL2 "
            "(even if partly inactivated by LIMK2 phosphorylation) may provide sufficient "
            "residual severing activity to maintain minimal actin turnover. ALS MNs fail to "
            "upregulate CFL2, contributing to faster degeneration."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "mechanism",
        "tier": "A",
        "evidence_for": [
            "GSE208629: Cfl2 UP +1.83x in SMA MNs",
            "GSE287257: CFL2 DOWN -0.94x in ALS MNs",
            "This is the strongest disease-specific signature in the actin pathway",
            "PMID 9390559: CFL2 is the primary actin-severing protein in muscle and neurons"
        ],
        "evidence_against": [
            "CFL2 upregulation could be pathological (excess severing) rather than protective",
            "Compensatory interpretation requires showing that CFL2 knockdown worsens SMA",
            "ALS and SMA affect different MN populations — direct comparison limited"
        ],
        "testable_prediction": "CFL2 knockdown in SMA iPSC-MNs should accelerate degeneration; CFL2 overexpression in ALS iPSC-MNs should be neuroprotective",
        "therapeutic_implication": "Boosting CFL2 expression or activity (via LIMK2 inhibition to reduce CFL2 phosphorylation) could be therapeutic in both SMA and ALS",
        "confidence": 0.76,
        "tags": ["actin", "cofilin", "compensatory", "disease-specific", "ALS", "ROCK-LIMK2-CFL2"]
    },
    {
        "title": "CFL2/CFL1 ratio distinguishes SMA from ALS at the single-cell level",
        "description": (
            "CFL2 shows opposite regulation in SMA (UP) vs. ALS (DOWN), while CFL1 may show "
            "a different pattern. The CFL2/CFL1 ratio in motor neurons could serve as a "
            "molecular classifier distinguishing these two MN diseases, with implications for "
            "differential diagnosis in ambiguous cases and for understanding why certain MN "
            "populations are vulnerable in each disease."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "biomarker",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Cfl2 UP +1.83x in SMA MNs",
            "GSE287257: CFL2 DOWN -0.94x in ALS MNs",
            "CFL1 and CFL2 have partially redundant but distinct functions",
            "PMID 12832468: CFL1 (ubiquitous) vs CFL2 (muscle/neuron-enriched) have different regulation"
        ],
        "evidence_against": [
            "CFL1 expression not systematically compared in these datasets",
            "Ratio biomarker requires access to MN tissue — not practical clinically",
            "SMA and ALS are clinically distinct in most cases — differential diagnosis rarely needed"
        ],
        "testable_prediction": "CFL2/CFL1 ratio >1.5 in MNs classifies SMA; <0.8 classifies ALS; validated across independent scRNA-seq datasets",
        "therapeutic_implication": "Could guide therapy selection (LIMK2 inhibitor for SMA-pattern; CFL2 activator for ALS-pattern) in precision medicine approaches",
        "confidence": 0.55,
        "tags": ["biomarker", "disease-specific", "differential-diagnosis", "single-cell", "cofilin"]
    },
    {
        "title": "Plasma CFL2 protein level serves as an accessible biomarker for SMA disease progression",
        "description": (
            "CFL2 is abundantly expressed in muscle and upregulated in SMA MNs. As MNs "
            "degenerate and denervation atrophy progresses, CFL2 should be released from "
            "both dying MNs and atrophying muscle into the bloodstream. A decline in plasma "
            "CFL2 over time may indicate reduced compensatory capacity and predict clinical "
            "deterioration."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "biomarker",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Cfl2 UP +1.83x in SMA MNs",
            "PMID 12832468: CFL2 is highly expressed in skeletal muscle",
            "PMID 30150366: Blood-based biomarkers increasingly used in SMA monitoring"
        ],
        "evidence_against": [
            "CFL2 is intracellular — release into blood requires cell lysis or active secretion",
            "Muscle CFL2 may confound MN-specific signal",
            "No validated CFL2 ELISA for clinical use exists"
        ],
        "testable_prediction": "Longitudinal plasma CFL2 levels in SMA patients should correlate inversely with HFMSE motor scores; treatment-responsive patients should show stable CFL2",
        "therapeutic_implication": "Blood-based CFL2 monitoring could guide treatment decisions without invasive procedures (lumbar puncture)",
        "confidence": 0.45,
        "tags": ["biomarker", "blood", "clinical", "monitoring", "disease-progression"]
    },
    {
        "title": "CFL2 upregulation reflects a transcriptional program controlled by SRF/MRTF in SMA motor neurons",
        "description": (
            "Serum Response Factor (SRF) and its cofactor MRTF (myocardin-related transcription "
            "factor) sense the actin monomer/polymer ratio. In SMA MNs, LIMK2-mediated actin "
            "stabilization depletes the G-actin pool, releasing MRTF to translocate to the "
            "nucleus and activate SRF target genes including CFL2. This mechanistically links "
            "LIMK2 upregulation to CFL2 transcription via the actin-MRTF-SRF circuit."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Both Limk2 and Cfl2 UP in SMA MNs (suggesting coordinated regulation)",
            "PMID 15543159: MRTF senses G-actin levels and activates SRF target genes",
            "PMID 15808504: Cofilin genes are SRF/MRTF targets",
            "PMID 24463284: SRF regulates cytoskeletal genes in neurons"
        ],
        "evidence_against": [
            "SRF/MRTF activity not measured in SMA MNs",
            "CFL2 could be regulated by other transcription factors (MEF2, etc.)",
            "Chromatin accessibility at CFL2 locus not examined in SMA"
        ],
        "testable_prediction": "ATAC-seq of SMA iPSC-MNs should show increased chromatin accessibility at SRF binding sites in the CFL2 promoter; SRF knockdown should prevent CFL2 upregulation",
        "therapeutic_implication": "Understanding the SRF-CFL2 circuit identifies additional intervention points upstream of CFL2",
        "confidence": 0.50,
        "tags": ["transcription", "SRF", "MRTF", "actin", "cofilin", "mechanism"]
    },
    {
        "title": "Dephospho-CFL2 (active form) overexpression rescues SMA motor neuron phenotypes",
        "description": (
            "If CFL2 upregulation in SMA is compensatory but limited by LIMK2-mediated "
            "phosphorylation, then expressing a phospho-resistant CFL2 mutant (S3A) in SMA "
            "MNs should bypass the LIMK2 block and fully restore actin severing. This would "
            "rescue the phenotype more completely than either LIMK2 inhibition or wild-type "
            "CFL2 overexpression alone."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "therapeutic",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Cfl2 UP but likely phospho-inactivated by LIMK2",
            "PMID 9390559: CFL2-S3A is constitutively active, non-phosphorylatable",
            "PMID 16543135: Active cofilin rescues actin dynamics in multiple cell models"
        ],
        "evidence_against": [
            "Constitutively active CFL2 may cause excessive actin severing (opposite problem)",
            "Gene therapy delivery of CFL2-S3A to MNs is technically challenging",
            "Phospho-regulation of CFL2 may be needed for normal actin cycling"
        ],
        "testable_prediction": "AAV9-CFL2(S3A) should rescue neurite outgrowth and NMJ morphology in SMA iPSC-MNs and SMA mice more effectively than AAV9-CFL2(WT)",
        "therapeutic_implication": "Active CFL2 gene therapy could be an SMN-independent approach for SMA, especially in combination with LIMK2 inhibition",
        "confidence": 0.48,
        "tags": ["gene-therapy", "cofilin", "phospho-mutant", "actin", "therapeutic"]
    },
    {
        "title": "CFL2 expression trajectory predicts treatment response to Nusinersen/Risdiplam in SMA patients",
        "description": (
            "If CFL2 upregulation is a compensatory response to SMN loss, then effective "
            "SMN-restoring therapy should normalize CFL2 levels over time. Patients whose "
            "CFL2 normalizes with treatment are likely achieving sufficient SMN restoration; "
            "patients with persistently elevated CFL2 may have ongoing actin pathology "
            "requiring adjunctive therapy."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "biomarker",
        "tier": "C",
        "evidence_for": [
            "GSE208629: Cfl2 UP +1.83x in SMA MNs",
            "Compensatory response should resolve when primary insult (SMN loss) is corrected",
            "Treatment-responsive biomarkers needed for SMA clinical management"
        ],
        "evidence_against": [
            "CFL2 measurement in patient samples requires biopsy or CSF — invasive",
            "CFL2 normalization timeline unknown",
            "Epigenetic changes may lock CFL2 expression even after SMN restoration"
        ],
        "testable_prediction": "Nusinersen-treated SMA patients should show decreasing muscle CFL2 mRNA over 12 months; non-responders should maintain elevated CFL2",
        "therapeutic_implication": "CFL2 as a treatment-response biomarker could identify patients needing combination therapy earlier",
        "confidence": 0.40,
        "tags": ["biomarker", "treatment-response", "Nusinersen", "Risdiplam", "clinical"]
    },
    {
        "title": "CFL2 upregulation protects SMA motor neurons from apoptosis by maintaining mitochondrial actin dynamics",
        "description": (
            "Cofilin-mediated actin dynamics are required for mitochondrial fission/fusion. "
            "In SMA MNs, CFL2 upregulation may maintain sufficient mitochondrial dynamics "
            "despite LIMK2-mediated inhibition, preventing mitochondrial fragmentation and "
            "apoptosis. Loss of this compensatory CFL2 response (as in ALS) would lead to "
            "mitochondrial dysfunction and faster cell death."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "GSE208629: Cfl2 UP +1.83x in SMA MNs",
            "PMID 25609816: Cofilin regulates mitochondrial dynamics and apoptosis",
            "PMID 28377503: Mitochondrial defects documented in SMA MNs",
            "GSE287257: CFL2 DOWN in ALS MNs — faster degeneration"
        ],
        "evidence_against": [
            "CFL2 role in mitochondrial dynamics is less established than CFL1",
            "Mitochondrial defects in SMA may be SMN-dependent, not actin-dependent",
            "Link between CFL2 and mitochondria in MNs not directly tested"
        ],
        "testable_prediction": "CFL2 knockdown in SMA iPSC-MNs should increase mitochondrial fragmentation (MitoTracker) and apoptosis (cleaved caspase-3)",
        "therapeutic_implication": "Maintaining CFL2 activity (via LIMK2 inhibition) could prevent mitochondrial-mediated apoptosis in SMA MNs",
        "confidence": 0.40,
        "tags": ["cofilin", "mitochondria", "apoptosis", "neuroprotection", "mechanism"]
    },
    {
        "title": "CFL2 expression in muscle biopsies distinguishes SMA types and predicts ambulatory status",
        "description": (
            "CFL2 is highly expressed in skeletal muscle. In SMA, denervation leads to muscle "
            "atrophy with likely changes in CFL2 expression. The degree of CFL2 upregulation "
            "in remaining muscle fibers may reflect the compensatory capacity of the "
            "neuromuscular system and correlate with SMA type and functional status."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "biomarker",
        "tier": "C",
        "evidence_for": [
            "PMID 12832468: CFL2 is the predominant cofilin in skeletal muscle",
            "Muscle biopsies are part of standard SMA diagnostic workup",
            "Compensatory CFL2 changes should be detectable in accessible tissue"
        ],
        "evidence_against": [
            "Muscle CFL2 may not reflect MN CFL2 status",
            "Biopsy variability (fiber type composition, sampling site) may confound",
            "SMA typing is already well-established by genetic testing and clinical criteria"
        ],
        "testable_prediction": "Muscle biopsy CFL2 immunohistochemistry scores should be higher in Type 3 (milder) vs. Type 1 (severe) SMA patients",
        "therapeutic_implication": "Accessible muscle-based CFL2 biomarker could supplement genetic testing for functional prognosis",
        "confidence": 0.35,
        "tags": ["biomarker", "muscle", "clinical", "prognosis", "SMA-type"]
    },
    {
        "title": "CFL2 opposite regulation in SMA vs ALS reflects differential Rho GTPase pathway engagement",
        "description": (
            "SMA (CFL2 UP) and ALS (CFL2 DOWN) show opposite CFL2 regulation despite both "
            "being MN diseases. This may reflect which Rho GTPase is dominant: SMA activates "
            "RhoA then ROCK then LIMK2 (leading to compensatory CFL2 transcription via SRF/MRTF), while "
            "ALS preferentially activates Rac1 then PAK then LIMK1 (which does not trigger CFL2 "
            "compensation). The Rho/Rac balance determines whether CFL2 compensation occurs."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "GSE208629: SMA shows ROCK-LIMK2 axis activation",
            "GSE287257: ALS shows different LIMK regulation pattern",
            "PMID 18485879: ROCK and PAK activate LIMK through different mechanisms",
            "RhoA-ROCK-LIMK2 axis validated in SMA"
        ],
        "evidence_against": [
            "Rho GTPase activity not directly measured in SMA vs. ALS MNs",
            "Both pathways may be active in both diseases",
            "Model is speculative — requires direct GTPase activity assays"
        ],
        "testable_prediction": "Active RhoA (GTP-bound) should be higher in SMA MNs vs. ALS MNs; active Rac1 should be higher in ALS MNs",
        "therapeutic_implication": "Disease-specific Rho GTPase profiles could guide which pathway inhibitor to use in each disease",
        "confidence": 0.38,
        "tags": ["RhoA", "Rac1", "cofilin", "disease-specific", "cross-disease", "mechanism"]
    },
    {
        "title": "Slingshot phosphatase (SSH1) as a therapeutic target to reactivate phospho-CFL2 in SMA",
        "description": (
            "If LIMK2 hyperphosphorylates CFL2 in SMA MNs, then activating Slingshot "
            "phosphatase (SSH1), which dephosphorylates cofilin at Ser3, could restore "
            "CFL2 activity without needing to inhibit LIMK2 directly. SSH1 activation "
            "represents an orthogonal approach to rebalancing the LIMK2-CFL2 axis."
        ),
        "target_symbol": "CFL2",
        "hypothesis_type": "therapeutic",
        "tier": "C",
        "evidence_for": [
            "PMID 11553635: SSH1 dephosphorylates cofilin at Ser3, reactivating severing",
            "GSE208629: Cfl2 UP but likely phospho-inactivated by LIMK2",
            "SSH1 and LIMK2 form a phosphorylation/dephosphorylation cycle on cofilin"
        ],
        "evidence_against": [
            "SSH1 expression in SMA MNs not characterized",
            "Activating a phosphatase pharmacologically is harder than inhibiting a kinase",
            "SSH1 has other substrates — may cause off-target effects"
        ],
        "testable_prediction": "SSH1 overexpression in SMA iPSC-MNs should reduce phospho-CFL2 and rescue neurite morphology; SSH1 knockdown should worsen phenotype",
        "therapeutic_implication": "SSH1 activation is an alternative to LIMK2 inhibition for restoring CFL2 function in SMA",
        "confidence": 0.38,
        "tags": ["phosphatase", "cofilin", "therapeutic", "SSH1", "actin"]
    },
    # ===================================================================
    # PFN2 — MN-ENRICHED PROFILIN (5 hypotheses)
    # ===================================================================
    {
        "title": "PFN2 upregulation in SMA motor neurons compensates for impaired actin polymerization",
        "description": (
            "PFN2 (profilin 2), the neuron-enriched profilin isoform, is upregulated +1.22x "
            "in SMA MNs and +7.6x enriched in human motor neurons. Profilins catalyze "
            "ADP-to-ATP exchange on actin monomers, feeding the polymerization machinery. "
            "PFN2 upregulation in SMA may compensate for reduced actin turnover caused by "
            "LIMK2-CFL2 axis dysfunction, maintaining minimum polymerization needed for survival."
        ),
        "target_symbol": "PFN2",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Pfn2 UP +1.22x in SMA MNs",
            "GSE287257: PFN2 7.6x enriched in human MNs (strongest MN-enrichment)",
            "PMID 11076947: PFN2 is the dominant profilin in neurons",
            "Profilin promotes actin polymerization — upregulation logical in actin-stressed cells"
        ],
        "evidence_against": [
            "PFN2 upregulation is modest (+1.22x) compared to LIMK2 or CFL2",
            "Profilin has actin-independent functions (signaling, membrane trafficking)",
            "Compensatory interpretation requires functional validation"
        ],
        "testable_prediction": "PFN2 knockdown in SMA iPSC-MNs should accelerate degeneration; PFN2 overexpression should be mildly protective",
        "therapeutic_implication": "PFN2 supplementation (gene therapy) could support actin polymerization in SMA MNs",
        "confidence": 0.55,
        "tags": ["profilin", "actin-polymerization", "motor-neuron-enriched", "compensatory"]
    },
    {
        "title": "PFN2 loss-of-function mutations would phenocopy SMA motor neuron defects",
        "description": (
            "Given PFN2 is the dominant profilin in MNs (7.6x enriched) and actin dynamics "
            "are critical for MN health, PFN2 loss-of-function should phenocopy aspects of "
            "SMA including NMJ defects, reduced neurite outgrowth, and impaired axonal transport. "
            "This parallels PFN1 mutations causing ALS (PMID 23727170), suggesting the profilin "
            "family is broadly critical for MN survival."
        ),
        "target_symbol": "PFN2",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "GSE287257: PFN2 7.6x enriched in human MNs",
            "PMID 23727170: PFN1 mutations cause familial ALS",
            "PMID 11076947: PFN2 is the neuron-specific profilin",
            "Computational prediction: actin pathway central to MN disease"
        ],
        "evidence_against": [
            "No PFN2 mutations found in SMA or ALS patients",
            "PFN2 knockout mice have not been extensively characterized for MN phenotypes",
            "PFN1 and PFN2 may have sufficient redundancy"
        ],
        "testable_prediction": "PFN2 CRISPR knockout in iPSC-derived MNs should show NMJ and neurite defects similar to SMN knockdown",
        "therapeutic_implication": "Establishes PFN2 as a convergence point between SMA and ALS actin pathology — potential shared therapeutic target",
        "confidence": 0.50,
        "tags": ["profilin", "PFN1", "ALS", "cross-disease", "genetics"]
    },
    {
        "title": "PFN2-PFN1 isoform balance determines motor neuron susceptibility to actin stress",
        "description": (
            "Motor neurons express predominantly PFN2 while glia and muscle express PFN1. "
            "This isoform dependence makes MNs uniquely vulnerable to perturbations in "
            "PFN2 function or its regulatory partners. In SMA, the PFN2 upregulation (+1.22x) "
            "may be insufficient to compensate for the broader actin dysregulation, "
            "while PFN1-dependent cells are protected."
        ),
        "target_symbol": "PFN2",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "GSE287257: PFN2 7.6x enriched in MNs; PFN1 lower",
            "PMID 23727170: PFN1 mutations cause ALS (MN-specific disease)",
            "Tissue-specific profilin expression documented"
        ],
        "evidence_against": [
            "PFN1 is also expressed in neurons, just at lower levels",
            "Isoform-specific roles in MNs not fully characterized",
            "MN vulnerability likely multifactorial beyond profilin balance"
        ],
        "testable_prediction": "PFN2/PFN1 ratio should be highest in vulnerable MN populations and lowest in resistant populations (ocular MNs)",
        "therapeutic_implication": "PFN2 supplementation could specifically protect MNs without affecting other cell types",
        "confidence": 0.45,
        "tags": ["profilin", "isoform", "vulnerability", "motor-neuron", "cell-type-specific"]
    },
    {
        "title": "PFN2 interacts with SMN in the profilin-actin complex required for MN axonal transport",
        "description": (
            "SMN protein has documented interactions with profilin (via the SMN-Gemin complex). "
            "In SMA, reduced SMN disrupts PFN2-containing complexes needed for local actin "
            "polymerization in axons. PFN2 upregulation may partially compensate for lost "
            "SMN-PFN2 interaction by increasing free PFN2 available for actin dynamics."
        ),
        "target_symbol": "PFN2",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "PMID 10523642: SMN interacts with profilin through proline-rich motifs",
            "GSE208629: Pfn2 UP in SMA MNs",
            "PMID 28377503: Actin-dependent axonal transport impaired in SMA"
        ],
        "evidence_against": [
            "SMN-profilin interaction shown primarily for PFN1, not PFN2",
            "Functional relevance of SMN-profilin interaction debated",
            "Axonal transport defects may be actin-independent (microtubule-based)"
        ],
        "testable_prediction": "Co-immunoprecipitation should show SMN-PFN2 complex in MNs; complex should be reduced in SMA iPSC-MNs",
        "therapeutic_implication": "Restoring SMN-PFN2 interaction (via SMN gene therapy or small molecule) could rescue axonal actin dynamics",
        "confidence": 0.42,
        "tags": ["profilin", "SMN", "protein-interaction", "axonal-transport"]
    },
    {
        "title": "PFN2 as a gene therapy payload for SMN-independent SMA treatment",
        "description": (
            "AAV9-mediated PFN2 overexpression in SMA motor neurons could boost actin "
            "polymerization independently of SMN status. As the neuron-enriched profilin, "
            "PFN2 supplementation would be cell-type appropriate and address the actin "
            "polymerization deficit downstream of the ROCK-LIMK2-CFL2 axis."
        ),
        "target_symbol": "PFN2",
        "hypothesis_type": "therapeutic",
        "tier": "C",
        "evidence_for": [
            "GSE287257: PFN2 naturally enriched in MNs — appropriate target",
            "AAV9 efficiently transduces MNs (proven by Zolgensma)",
            "PFN2 promotes actin polymerization — directly addresses SMA actin deficit"
        ],
        "evidence_against": [
            "PFN2 overexpression toxicity not characterized",
            "Gene therapy already available for SMA (Zolgensma delivers SMN1)",
            "Actin polymerization may not be the rate-limiting step in SMA pathology"
        ],
        "testable_prediction": "AAV9-PFN2 should improve motor function in Smn2B/- mice; combination with low-dose Nusinersen should be synergistic",
        "therapeutic_implication": "PFN2 gene therapy could supplement existing SMA treatments for patients with residual motor deficits",
        "confidence": 0.35,
        "tags": ["gene-therapy", "profilin", "AAV9", "SMN-independent", "therapeutic"]
    },
    # ===================================================================
    # ROCK1 — UPSTREAM KINASE (5 hypotheses)
    # ===================================================================
    {
        "title": "ROCK1 upregulation in SMA motor neurons drives the pathological ROCK-LIMK2-CFL2 axis",
        "description": (
            "ROCK1 is upregulated in SMA MNs (GSE208629) and directly phosphorylates LIMK2 "
            "at Thr505, activating its kinase function. This places ROCK1 as the proximal "
            "driver of the entire actin pathology cascade: ROCK1 up leads to LIMK2 activation leads to CFL2 "
            "phosphorylation leads to actin hyperstabilization leads to NMJ failure. ROCK1 is the most "
            "upstream druggable target in this cascade."
        ),
        "target_symbol": "ROCK1",
        "hypothesis_type": "mechanism",
        "tier": "A",
        "evidence_for": [
            "GSE208629: Rock1 UP in SMA MNs",
            "PMID 10783251: ROCK1 directly phosphorylates LIMK at Thr505",
            "PMID 22397316: Fasudil (pan-ROCK inhibitor) rescues SMA",
            "ROCK1 is upstream of the entire LIMK2-CFL2 axis"
        ],
        "evidence_against": [
            "ROCK1 vs ROCK2 contribution not dissected in SMA",
            "Fasudil inhibits both ROCK1 and ROCK2 — individual contributions unknown",
            "ROCK1 has many substrates beyond LIMK2 (MLC, MYPT1, etc.)"
        ],
        "testable_prediction": "ROCK1-selective inhibitor should reduce phospho-LIMK2 and phospho-CFL2 in SMA iPSC-MNs; ROCK2-selective inhibitor may have different effect profile",
        "therapeutic_implication": "ROCK1-selective inhibitors could reduce off-target effects compared to pan-ROCK inhibitors like Fasudil",
        "confidence": 0.75,
        "tags": ["ROCK", "kinase", "upstream", "Fasudil", "ROCK-LIMK2-CFL2"]
    },
    {
        "title": "ROCK1-mediated myosin II activation contributes to SMA growth cone collapse independently of LIMK2",
        "description": (
            "ROCK1 phosphorylates myosin light chain (MLC) and myosin phosphatase (MYPT1), "
            "increasing actomyosin contractility. In SMA MNs, this ROCK1-myosin axis may "
            "cause growth cone collapse and axon retraction through excessive contractile "
            "force, independently of the LIMK2-CFL2 actin stabilization pathway. "
            "Fasudil rescues both branches simultaneously."
        ),
        "target_symbol": "ROCK1",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Rock1 UP in SMA MNs",
            "PMID 10657297: ROCK1 activates myosin II via MLC phosphorylation",
            "PMID 28377503: Growth cone defects early in SMA pathology",
            "PMID 22397316: Fasudil (blocks ROCK-myosin AND ROCK-LIMK) rescues SMA"
        ],
        "evidence_against": [
            "Growth cone collapse mechanism not directly tested in SMA",
            "Myosin II phosphorylation status unknown in SMA MNs",
            "LIMK2 pathway may be the dominant ROCK1 effector in MNs"
        ],
        "testable_prediction": "Blebbistatin (myosin II inhibitor) should partially rescue SMA growth cone morphology; combined with LIMKi3, rescue should match Fasudil effect",
        "therapeutic_implication": "Dual inhibition of ROCK1-LIMK2 and ROCK1-myosin branches may explain Fasudil superiority over selective LIMK2 inhibition",
        "confidence": 0.55,
        "tags": ["ROCK", "myosin", "growth-cone", "actomyosin", "contractility"]
    },
    {
        "title": "ROCK1 activation in SMA is triggered by reduced progranulin-mediated survival signaling",
        "description": (
            "Progranulin (GRN) promotes motor neuron survival by inhibiting RhoA-ROCK signaling. "
            "SMN depletion may reduce progranulin expression or secretion, releasing the brake "
            "on RhoA-ROCK1 activation. This would connect SMN loss to ROCK1 upregulation "
            "through a neurotrophic factor pathway."
        ),
        "target_symbol": "ROCK1",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "PMID 21451020: Progranulin inhibits RhoA/ROCK pathway in neurons",
            "GSE208629: Rock1 UP in SMA MNs",
            "SMN depletion affects multiple signaling pathways"
        ],
        "evidence_against": [
            "Progranulin expression in SMA MNs not characterized",
            "SMN-progranulin connection is speculative",
            "RhoA activation in SMA may be mediated by other mechanisms"
        ],
        "testable_prediction": "Progranulin levels should be reduced in SMA iPSC-MN conditioned media; recombinant progranulin should reduce ROCK1 activity",
        "therapeutic_implication": "Progranulin supplementation could be an upstream approach to normalize the ROCK-LIMK2-CFL2 axis",
        "confidence": 0.32,
        "tags": ["ROCK", "progranulin", "neurotrophic", "signaling", "upstream"]
    },
    {
        "title": "ROCK1 inhibition with low-dose Fasudil as adjunctive therapy for treated SMA patients",
        "description": (
            "Fasudil is FDA-approved in Japan for cerebral vasospasm and has documented "
            "oral bioavailability and CNS penetration. At 30 mg/kg BID, it improved survival "
            "in SMA mice (Bowerman 2012). Repurposing Fasudil as adjunctive therapy for "
            "SMA patients already on Nusinersen/Risdiplam could address residual actin "
            "pathology that SMN restoration alone does not fix."
        ),
        "target_symbol": "ROCK1",
        "hypothesis_type": "therapeutic",
        "tier": "A",
        "evidence_for": [
            "PMID 22397316: Fasudil 30 mg/kg BID improves survival in Smn2B/- mice",
            "Fasudil approved in Japan — safety data available",
            "GSE208629: ROCK1/2 UP in SMA MNs — direct target of Fasudil",
            "SMN-independent mechanism complements existing therapies"
        ],
        "evidence_against": [
            "Fasudil dose for SMA (30 mg/kg) much higher than vasospasm dose — toxicity concerns",
            "Mouse-to-human dose translation challenging for CNS drugs",
            "No SMA clinical trial of Fasudil conducted despite 2012 preclinical data",
            "Fasudil is pan-ROCK — side effects on smooth muscle, immune system"
        ],
        "testable_prediction": "Low-dose Fasudil (3-10 mg/kg) + Risdiplam should show motor function improvement in SMA mice beyond Risdiplam alone",
        "therapeutic_implication": "Could provide an immediately repurposable add-on therapy for SMA patients with residual symptoms despite SMN-enhancing treatment",
        "confidence": 0.68,
        "tags": ["Fasudil", "repurposing", "ROCK", "clinical", "combination", "SMN-independent"]
    },
    {
        "title": "ROCK1 caspase cleavage generates a constitutively active fragment in SMA motor neurons undergoing apoptosis",
        "description": (
            "ROCK1 is cleaved by caspase-3 during apoptosis, generating a constitutively "
            "active kinase fragment (ROCK1-delta1). In SMA MNs undergoing early apoptosis, this "
            "could create a positive feedback loop: MN stress leads to caspase activation leads to ROCK1 "
            "cleavage leads to constitutive ROCK1 activity leads to actin collapse leads to more stress. Breaking "
            "this loop with ROCK inhibitors could widen the therapeutic window."
        ),
        "target_symbol": "ROCK1",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "PMID 11390498: Caspase-3 cleaves ROCK1, generating constitutively active fragment",
            "GSE208629: Rock1 UP in SMA MNs",
            "PMID 25349423: Apoptosis is the final MN death pathway in SMA"
        ],
        "evidence_against": [
            "Caspase-cleaved ROCK1 not detected in SMA tissue",
            "This would be a late-stage event — may not explain early actin defects",
            "ROCK1 transcriptional upregulation (scRNA-seq) distinct from post-translational cleavage"
        ],
        "testable_prediction": "Western blot of SMA spinal cord should show ROCK1-delta1 fragment; caspase inhibitor should reduce active ROCK1 and delay MN loss",
        "therapeutic_implication": "Combined ROCK + caspase inhibition could break the positive feedback loop in degenerating MNs",
        "confidence": 0.35,
        "tags": ["ROCK", "caspase", "apoptosis", "positive-feedback", "mechanism"]
    },
    # ===================================================================
    # ROCK2 — FASUDIL TARGET (5 hypotheses)
    # ===================================================================
    {
        "title": "ROCK2 is the dominant Fasudil target responsible for SMA motor neuron rescue",
        "description": (
            "While Fasudil inhibits both ROCK1 and ROCK2, ROCK2 is more abundantly expressed "
            "in brain and ROCK2 has preferential activity toward LIMK2 (vs. ROCK1 toward LIMK1). "
            "The therapeutic effect of Fasudil in SMA may be primarily mediated through "
            "ROCK2 to LIMK2 inhibition in motor neurons. This would explain why CNS-specific "
            "effects are prominent despite systemic dosing."
        ),
        "target_symbol": "ROCK2",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "PMID 22397316: Fasudil rescues SMA mice (systemic dosing)",
            "PMID 15556950: ROCK2 is the predominant isoform in brain/neurons",
            "GSE208629: Both Rock1 and Rock2 UP in SMA MNs",
            "ROCK2 preferentially signals to LIMK2 in neuronal contexts"
        ],
        "evidence_against": [
            "ROCK1 and ROCK2 substrate specificities overlap significantly",
            "ROCK2-selective effects in SMA not demonstrated",
            "Fasudil IC50 for ROCK1 and ROCK2 are similar — not selective"
        ],
        "testable_prediction": "ROCK2-selective inhibitor (KD025/belumosudil) should phenocopy Fasudil rescue in SMA iPSC-MNs; ROCK1-selective inhibitor should have weaker effect",
        "therapeutic_implication": "ROCK2-selective inhibitors (belumosudil is already FDA-approved for GVHD) could be repurposed for SMA with better specificity than Fasudil",
        "confidence": 0.58,
        "tags": ["ROCK2", "Fasudil", "belumosudil", "selectivity", "repurposing"]
    },
    {
        "title": "Belumosudil (ROCK2-selective) as a clinical candidate for SMA combination therapy",
        "description": (
            "Belumosudil (KD025) is an FDA-approved ROCK2-selective inhibitor for chronic "
            "GVHD. Its established safety profile, oral bioavailability, and ROCK2 selectivity "
            "make it a superior candidate to Fasudil for SMA repurposing. If ROCK2 is the "
            "dominant pathway driver in SMA MNs, belumosudil could provide targeted ROCK2-LIMK2 "
            "axis inhibition with fewer peripheral side effects."
        ),
        "target_symbol": "ROCK2",
        "hypothesis_type": "therapeutic",
        "tier": "B",
        "evidence_for": [
            "Belumosudil FDA-approved (safety data available)",
            "ROCK2 is brain-enriched — selectivity advantageous for CNS disease",
            "GSE208629: Rock2 UP in SMA MNs",
            "PMID 22397316: Pan-ROCK inhibition (Fasudil) rescues SMA — ROCK2 contribution likely"
        ],
        "evidence_against": [
            "Belumosudil CNS penetration not well characterized",
            "ROCK2 selectivity may not be sufficient — ROCK1 contribution unknown",
            "No preclinical SMA data for belumosudil"
        ],
        "testable_prediction": "Belumosudil at 200 mg daily equivalent in SMA mice should improve motor function; blood-brain barrier penetration should be confirmed by CSF drug levels",
        "therapeutic_implication": "Fastest path to clinical trial: FDA-approved drug with known safety, repurposed for SMA with strong mechanistic rationale",
        "confidence": 0.55,
        "tags": ["belumosudil", "repurposing", "ROCK2", "FDA-approved", "clinical"]
    },
    {
        "title": "ROCK2 mediates SMN-independent NMJ maturation defects in SMA through LIMK2-actin signaling",
        "description": (
            "NMJ maturation requires precise actin remodeling. ROCK2 upregulation in SMA MNs "
            "hyperactivates LIMK2, which hyperstabilizes actin at presynaptic terminals, "
            "preventing the dynamic remodeling needed for NMJ maturation from plaque to "
            "pretzel morphology. This explains the immature NMJ phenotype seen in SMA mice."
        ),
        "target_symbol": "ROCK2",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "GSE208629: Rock2 and Limk2 UP in SMA MNs",
            "PMID 26025607: NMJ maturation arrested in SMA mice",
            "PMID 15713940: Actin dynamics required for NMJ maturation (plaque to pretzel transition)"
        ],
        "evidence_against": [
            "NMJ maturation defects could be postsynaptic (muscle-side)",
            "Other actin regulators beyond ROCK2-LIMK2 contribute to NMJ formation",
            "ROCK2 role in NMJ specifically not tested"
        ],
        "testable_prediction": "ROCK2 inhibition during the NMJ maturation window (P0-P14 in mice) should rescue pretzel formation in SMA mice",
        "therapeutic_implication": "Early ROCK2 inhibition could prevent NMJ defects even before SMN-enhancing therapy takes effect",
        "confidence": 0.52,
        "tags": ["ROCK2", "NMJ", "maturation", "actin", "development"]
    },
    {
        "title": "ROCK2 phosphorylation of CRMP2 impairs axonal microtubule dynamics in SMA independently of actin",
        "description": (
            "ROCK2 phosphorylates CRMP2 (collapsin response mediator protein 2), inactivating "
            "its microtubule-stabilizing function. In SMA MNs with upregulated ROCK2, CRMP2 "
            "phosphorylation may impair axonal microtubule dynamics, contributing to axonal "
            "transport deficits independently of the actin-LIMK2-CFL2 pathway. This provides "
            "a second pathological axis downstream of ROCK2."
        ),
        "target_symbol": "ROCK2",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "PMID 16540511: ROCK2 phosphorylates CRMP2 at Thr555, inactivating MT stabilization",
            "GSE208629: Rock2 UP in SMA MNs",
            "PMID 28377503: Axonal transport deficits documented in SMA"
        ],
        "evidence_against": [
            "CRMP2 phosphorylation not measured in SMA",
            "Microtubule defects in SMA may be SMN-dependent (snRNP assembly role)",
            "CRMP2 model is speculative in SMA context"
        ],
        "testable_prediction": "Phospho-CRMP2 (Thr555) should be elevated in SMA MN axons; ROCK2 inhibition should normalize CRMP2 phosphorylation and axonal transport velocity",
        "therapeutic_implication": "ROCK2 inhibition addresses both actin (via LIMK2) and microtubule (via CRMP2) pathology — dual mechanism",
        "confidence": 0.42,
        "tags": ["ROCK2", "CRMP2", "microtubule", "axonal-transport", "dual-mechanism"]
    },
    {
        "title": "ROCK2 haploinsufficiency in SMA mice extends survival without Fasudil treatment",
        "description": (
            "If ROCK2 is a key driver of SMA pathology via the LIMK2-CFL2 axis, then "
            "genetic reduction of ROCK2 (heterozygous knockout) should partially rescue "
            "SMA phenotype without pharmacological intervention. This genetic experiment "
            "would definitively establish ROCK2 as a disease modifier and validate it as "
            "a drug target."
        ),
        "target_symbol": "ROCK2",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "PMID 22397316: Pharmacological ROCK inhibition rescues SMA",
            "GSE208629: Rock2 UP in SMA MNs",
            "Genetic haploinsufficiency is the gold standard for target validation"
        ],
        "evidence_against": [
            "ROCK2 heterozygous mice may compensate with ROCK1 upregulation",
            "Developmental ROCK2 reduction differs from postnatal pharmacological inhibition",
            "ROCK2+/- x SMA cross not yet performed"
        ],
        "testable_prediction": "Smn2B/- ; Rock2+/- mice should show extended survival (>50%) and improved motor function compared to Smn2B/- ; Rock2+/+ littermates",
        "therapeutic_implication": "Positive result would provide genetic validation for ROCK2-selective drug development in SMA",
        "confidence": 0.62,
        "tags": ["ROCK2", "genetics", "haploinsufficiency", "target-validation", "mouse-model"]
    },
    # ===================================================================
    # RAC1 — Rho GTPase (3 hypotheses)
    # ===================================================================
    {
        "title": "RAC1-PAK pathway is suppressed in SMA motor neurons, shifting signaling to RhoA-ROCK-LIMK2",
        "description": (
            "The Rho GTPase family has opposing effects: RAC1 promotes neurite extension "
            "(via PAK to LIMK1) while RhoA causes retraction (via ROCK to LIMK2). In SMA MNs, "
            "RAC1 suppression combined with RhoA activation would shift the balance toward "
            "retraction signaling, explaining both the LIMK1 absence and LIMK2 dominance "
            "observed in single-cell data."
        ),
        "target_symbol": "RAC1",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "GSE208629: LIMK1 absent (RAC1/PAK effector), LIMK2 UP (RhoA/ROCK effector)",
            "PMID 10508858: RAC1 promotes neurite outgrowth; RhoA promotes retraction",
            "PMID 25143584: RhoA activated in SMN-depleted cells"
        ],
        "evidence_against": [
            "RAC1 activity not directly measured in SMA MNs",
            "RAC1 mRNA may be normal — activity regulated post-translationally by GEFs/GAPs",
            "LIMK1 absence may be MN subtype-specific rather than RAC1-dependent"
        ],
        "testable_prediction": "Active RAC1 (GTP-bound) should be reduced in SMA iPSC-MNs; RAC1 activator (CN04) should partially rescue neurite phenotype",
        "therapeutic_implication": "RAC1 activation represents an orthogonal approach to counter RhoA-ROCK hyperactivation in SMA",
        "confidence": 0.52,
        "tags": ["RAC1", "RhoA", "GTPase", "balance", "neurite-outgrowth"]
    },
    {
        "title": "RAC1 activators synergize with ROCK inhibitors by restoring GTPase balance in SMA motor neurons",
        "description": (
            "Therapeutic strategy: simultaneously inhibit RhoA-ROCK (with Fasudil) and "
            "activate RAC1 (with small molecule activators or CDC42 modulation). This dual "
            "approach would normalize the RAC1/RhoA ratio, restoring the dynamic balance "
            "needed for growth cone navigation and synaptic maintenance."
        ),
        "target_symbol": "RAC1",
        "hypothesis_type": "combinatorial",
        "tier": "C",
        "evidence_for": [
            "RAC1 and RhoA are antagonistic — correcting both should have additive effect",
            "PMID 22397316: Fasudil (ROCK inhibitor) rescues SMA",
            "GSE208629: LIMK isoform switch suggests GTPase imbalance"
        ],
        "evidence_against": [
            "RAC1 activators not well developed for CNS use",
            "Dual GTPase modulation may be too complex pharmacologically",
            "RAC1 hyperactivation linked to cancer — safety concerns"
        ],
        "testable_prediction": "Fasudil + RAC1 activator should show greater neurite outgrowth rescue than either alone in SMA iPSC-MNs",
        "therapeutic_implication": "Combination GTPase modulation could provide superior rescue compared to single-pathway approaches",
        "confidence": 0.35,
        "tags": ["RAC1", "ROCK", "combination", "GTPase", "Fasudil"]
    },
    {
        "title": "SMN depletion impairs RAC1 activation by disrupting RAC1-GEF complex formation",
        "description": (
            "SMN protein participates in RNA processing complexes that regulate expression "
            "of guanine nucleotide exchange factors (GEFs) for RAC1. SMN depletion may reduce "
            "specific RAC1-GEFs (e.g., TIAM1, DOCK180), leading to decreased RAC1 activation "
            "and the consequent shift toward RhoA-ROCK dominance in SMA motor neurons."
        ),
        "target_symbol": "RAC1",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "PMID 25143584: RhoA activated in SMN-depleted cells",
            "SMN involved in RNA processing — could affect GEF mRNA splicing",
            "GSE208629: Data consistent with RAC1 hypoactivation"
        ],
        "evidence_against": [
            "SMN-GEF connection not directly demonstrated",
            "RAC1-GEF expression not examined in SMA transcriptomics",
            "Model is highly speculative with multiple assumptions"
        ],
        "testable_prediction": "scRNA-seq should show reduced RAC1-GEF (TIAM1, DOCK180) expression in SMA MNs; GEF overexpression should rescue RAC1 activity",
        "therapeutic_implication": "Identifies specific GEFs as potential therapeutic targets for restoring RAC1 signaling in SMA",
        "confidence": 0.30,
        "tags": ["RAC1", "GEF", "SMN", "RNA-processing", "upstream"]
    },
    # ===================================================================
    # ACTG1 — STRUCTURAL ACTIN (3 hypotheses)
    # ===================================================================
    {
        "title": "ACTG1 (gamma-actin) upregulation contributes to cytoskeletal rigidity in SMA motor neurons",
        "description": (
            "ACTG1 (gamma-1 actin) is upregulated in SMA MNs as part of the broad actin "
            "pathway activation (10/14 genes UP). Unlike beta-actin (ACTB), gamma-actin "
            "forms more stable filaments and is enriched in mature, less dynamic structures. "
            "ACTG1 upregulation may shift the actin cytoskeleton toward rigidity, complementing "
            "LIMK2-mediated cofilin inactivation to create a double hit on actin dynamics."
        ),
        "target_symbol": "ACTG1",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "GSE208629: 10/14 actin genes UP in SMA MNs",
            "PMID 20998684: ACTG1 forms more stable filaments than ACTB",
            "Actin isoform ratio affects cytoskeletal dynamics and cell behavior"
        ],
        "evidence_against": [
            "ACTG1 specific upregulation level not reported individually",
            "Actin isoform ratio effect on MN function not characterized",
            "General actin upregulation may be a non-specific stress response"
        ],
        "testable_prediction": "ACTG1/ACTB ratio should be increased in SMA iPSC-MNs; normalizing the ratio should improve growth cone dynamics",
        "therapeutic_implication": "Actin isoform-switching approaches could complement kinase inhibition strategies",
        "confidence": 0.35,
        "tags": ["actin", "gamma-actin", "cytoskeleton", "rigidity", "isoform"]
    },
    {
        "title": "ACTG1 mutations that reduce filament stability might protect SMA motor neurons",
        "description": (
            "If actin hyperstabilization drives SMA MN pathology, then naturally occurring "
            "ACTG1 variants with reduced polymerization stability could act as disease modifiers. "
            "This is analogous to PLS3 overexpression as an SMA modifier — except working "
            "through structural actin properties rather than bundling."
        ),
        "target_symbol": "ACTG1",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "PMID 19270694: PLS3 as actin-related SMA modifier precedent",
            "GSE208629: Actin pathway broadly dysregulated in SMA MNs",
            "ACTG1 variants affect filament properties in known ways"
        ],
        "evidence_against": [
            "ACTG1 mutations cause hearing loss (DFNA20) — pleiotropic effects",
            "No SMA modifier studies have identified ACTG1 variants",
            "Highly speculative — no supporting genetic data"
        ],
        "testable_prediction": "GWAS of SMA severity modifiers should include ACTG1 locus; specific ACTG1 variants should correlate with milder phenotype",
        "therapeutic_implication": "Understanding actin structural modifiers could inspire small molecules that reduce actin stability",
        "confidence": 0.25,
        "tags": ["actin", "ACTG1", "modifier", "genetics", "filament-stability"]
    },
    {
        "title": "ACTG1 upregulation in SMA motor neurons increases vulnerability to actin-targeting toxins",
        "description": (
            "SMA MNs with broadly upregulated actin pathway (10/14 genes UP) may be more "
            "sensitive to environmental actin-targeting compounds (cytochalasin, latrunculin "
            "analogs, or natural actin-disrupting agents). This could explain why SMA patients "
            "sometimes show unexpected sensitivity to medications or environmental exposures "
            "that affect cytoskeletal dynamics."
        ),
        "target_symbol": "ACTG1",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "GSE208629: 10/14 actin genes UP — hypersensitized pathway",
            "Cells with altered actin dynamics often show increased sensitivity to actin drugs",
            "Clinical observation of variable drug sensitivity in SMA patients"
        ],
        "evidence_against": [
            "No clinical data on actin-targeting compound sensitivity in SMA patients",
            "Upregulated actin could make cells MORE resistant, not more sensitive",
            "Environmental actin toxin exposure is rare"
        ],
        "testable_prediction": "SMA iPSC-MNs should show lower LD50 for cytochalasin D and latrunculin B compared to isogenic controls",
        "therapeutic_implication": "Clinical pharmacology awareness: SMA patients may need dose adjustments for drugs affecting cytoskeletal dynamics",
        "confidence": 0.25,
        "tags": ["actin", "ACTG1", "pharmacology", "sensitivity", "environmental"]
    },
    # ===================================================================
    # PFN1 — ALS GENE, CROSS-DISEASE (5 hypotheses)
    # ===================================================================
    {
        "title": "PFN1 mutations in ALS and PFN2 dysregulation in SMA converge on profilin-actin motor neuron vulnerability",
        "description": (
            "PFN1 mutations cause familial ALS (PMID 23727170) while PFN2 is the "
            "MN-enriched profilin upregulated in SMA. Both diseases affect motor neurons "
            "through profilin-dependent actin dynamics: ALS via loss-of-function mutations "
            "in PFN1, SMA via dysregulation of the broader profilin-actin network including "
            "PFN2. This convergence identifies the profilin-actin axis as a shared MN "
            "vulnerability factor."
        ),
        "target_symbol": "PFN1",
        "hypothesis_type": "mechanism",
        "tier": "A",
        "evidence_for": [
            "PMID 23727170: PFN1 mutations cause familial ALS (4 families)",
            "GSE287257: PFN2 7.6x enriched in human MNs",
            "GSE208629: Pfn2 UP in SMA MNs",
            "Both diseases primarily affect motor neurons"
        ],
        "evidence_against": [
            "PFN1-ALS and SMA have very different etiologies",
            "PFN1 mutations are rare (about 1-2% of familial ALS)",
            "Profilin convergence may be coincidental rather than mechanistically linked"
        ],
        "testable_prediction": "PFN1 mutant iPSC-MNs should show similar actin pathway dysregulation (LIMK/CFL changes) as SMN-depleted iPSC-MNs",
        "therapeutic_implication": "Shared profilin-actin vulnerability could enable cross-disease drug development for both SMA and ALS",
        "confidence": 0.65,
        "tags": ["PFN1", "ALS", "profilin", "cross-disease", "convergence", "motor-neuron"]
    },
    {
        "title": "PFN1-dependent actin polymerization is the rate-limiting step for motor neuron axon maintenance",
        "description": (
            "Motor neurons have the longest axons in the body (up to 1 meter). Maintaining "
            "these axons requires massive actin polymerization supported by profilins. "
            "MNs are uniquely dependent on profilin-actin dynamics because their extreme "
            "length amplifies any deficiency in actin supply. This explains why profilin "
            "mutations (PFN1 in ALS) and actin pathway dysregulation (SMA) selectively "
            "affect MNs."
        ),
        "target_symbol": "PFN1",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "Motor neuron axons are the longest in the body — high actin demand",
            "PMID 23727170: PFN1 loss-of-function causes MN disease (ALS)",
            "GSE208629: Actin pathway massively upregulated in SMA MNs",
            "Computational prediction: axon length correlates with actin dependency"
        ],
        "evidence_against": [
            "Axonal maintenance is primarily microtubule-based, not actin-based",
            "MN vulnerability in SMA relates more to NMJ than axon length",
            "Profilin has actin-independent functions that may be more relevant"
        ],
        "testable_prediction": "MN subtypes with longer axons should degenerate faster in SMA; axon length should correlate with actin pathway gene expression",
        "therapeutic_implication": "Supporting actin polymerization (via PFN supplementation or LIMK2 inhibition) addresses a fundamental MN vulnerability",
        "confidence": 0.48,
        "tags": ["PFN1", "axon", "polymerization", "motor-neuron", "length-dependent"]
    },
    {
        "title": "PFN1 G118V mutation creates toxic actin aggregates similar to those predicted in severe SMA",
        "description": (
            "The PFN1-G118V ALS mutation reduces actin binding and causes protein aggregation. "
            "In severe SMA, the combination of actin hyperstabilization (LIMK2-CFL2 axis) "
            "and PFN2 upregulation may lead to abnormal actin-profilin complexes that form "
            "micro-aggregates in axons. This parallel between genetic (ALS) and acquired (SMA) "
            "profilin-actin dysfunction could share a common toxic intermediate."
        ),
        "target_symbol": "PFN1",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "PMID 23727170: PFN1-G118V causes aggregation in ALS",
            "GSE208629: Both actin and profilin dysregulated in SMA MNs",
            "Protein aggregation is a common theme in MN diseases"
        ],
        "evidence_against": [
            "Actin aggregation not observed in SMA pathology",
            "SMA has no known protein aggregation component (unlike ALS)",
            "Model extrapolates from rare genetic ALS to common SMA — tenuous"
        ],
        "testable_prediction": "Super-resolution imaging of SMA iPSC-MN axons should reveal abnormal actin-profilin clusters not seen in controls",
        "therapeutic_implication": "If confirmed, anti-aggregation strategies from ALS could be applied to SMA",
        "confidence": 0.28,
        "tags": ["PFN1", "aggregation", "ALS", "cross-disease", "pathology"]
    },
    {
        "title": "PFN1 expression level modifies SMA severity by buffering actin polymerization capacity",
        "description": (
            "Natural variation in PFN1 expression could modify SMA severity: higher PFN1 "
            "expression provides more actin polymerization buffer, partially compensating "
            "for the actin dynamics defect in SMA. This would make PFN1 a genetic modifier "
            "of SMA, similar to PLS3 and NCALD."
        ),
        "target_symbol": "PFN1",
        "hypothesis_type": "biomarker",
        "tier": "C",
        "evidence_for": [
            "PMID 19270694: PLS3 (another actin gene) is a documented SMA modifier",
            "Profilin is central to actin homeostasis — variation should affect phenotype",
            "PMID 23475966: Multiple SMA modifiers in actin pathway"
        ],
        "evidence_against": [
            "PFN1 not identified as SMA modifier in GWAS or family studies",
            "PFN1 expression variation in MNs unknown",
            "PFN2 (not PFN1) is the MN-enriched profilin"
        ],
        "testable_prediction": "SMA patient cohort analysis should show correlation between PFN1 copy number/expression eQTLs and motor function scores",
        "therapeutic_implication": "PFN1 supplementation could be a modifier-based therapeutic approach for SMA",
        "confidence": 0.30,
        "tags": ["PFN1", "modifier", "genetics", "SMA-severity", "actin"]
    },
    {
        "title": "Cross-disease profilin screening identifies compounds that rescue both PFN1-ALS and SMA actin phenotypes",
        "description": (
            "A high-throughput screen for compounds that enhance profilin-dependent actin "
            "polymerization could identify drugs effective in both PFN1-ALS (loss of "
            "polymerization) and SMA (dysregulated polymerization/depolymerization). Compounds "
            "that stabilize profilin-actin interaction without blocking dynamics could "
            "address both diseases."
        ),
        "target_symbol": "PFN1",
        "hypothesis_type": "therapeutic",
        "tier": "C",
        "evidence_for": [
            "PMID 23727170: PFN1-ALS has actin polymerization defect",
            "GSE208629: SMA has actin dynamics defect",
            "Cross-disease screening increases commercial viability of drug development"
        ],
        "evidence_against": [
            "SMA and ALS actin defects may require opposite interventions",
            "Profilin-actin interaction is hard to modulate with small molecules",
            "No validated HTS assay for profilin-actin function exists"
        ],
        "testable_prediction": "Dual-readout screen (PFN1-ALS iPSC-MNs + SMA iPSC-MNs) should identify compounds rescuing both phenotypes at >10% hit rate",
        "therapeutic_implication": "Cross-disease drug development for profilin-actin modulators could attract broader pharma interest and funding",
        "confidence": 0.30,
        "tags": ["PFN1", "drug-screen", "cross-disease", "ALS", "SMA", "therapeutic"]
    },
    # ===================================================================
    # CROSS-PATHWAY — COMBINATION THERAPIES (8 hypotheses)
    # ===================================================================
    {
        "title": "Triple therapy Risdiplam + Fasudil + LIMK2i maximally rescues SMA motor neurons through three independent axes",
        "description": (
            "Optimal SMA therapy requires attacking three independent axes: (1) SMN restoration "
            "(Risdiplam), (2) upstream ROCK inhibition (Fasudil, addresses myosin + LIMK2), "
            "and (3) specific LIMK2 inhibition (to fully suppress the LIMK2-CFL2 arm). "
            "This triple combination addresses SMN protein levels, actomyosin contractility, "
            "and actin dynamics simultaneously — the three major pathological axes in SMA MNs."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "combinatorial",
        "tier": "A",
        "evidence_for": [
            "PMID 35587700: Risdiplam improves but does not normalize SMA",
            "PMID 22397316: Fasudil rescues SMA SMN-independently",
            "GSE208629: LIMK2 is the specific actin kinase in SMA MNs",
            "Multi-target approaches superior in complex diseases (oncology precedent)"
        ],
        "evidence_against": [
            "Three-drug combination increases complexity and drug-drug interaction risk",
            "No LIMK2-selective inhibitor in clinical development",
            "Cost and regulatory burden of triple combination therapy"
        ],
        "testable_prediction": "Triple combination should show >90% neurite outgrowth rescue in SMA iPSC-MNs (vs. ~60% for Risdiplam alone, ~40% for Fasudil alone)",
        "therapeutic_implication": "Defines the maximal achievable rescue and guides clinical combination strategy",
        "confidence": 0.55,
        "tags": ["combination", "triple-therapy", "Risdiplam", "Fasudil", "LIMK2", "maximal-rescue"]
    },
    {
        "title": "ROCK-LIMK2-CFL2 axis inhibition rescues NMJ defects that persist after Nusinersen treatment",
        "description": (
            "Nusinersen-treated SMA patients often have persistent NMJ deficits despite "
            "improved SMN levels in MN cell bodies. The ROCK-LIMK2-CFL2 axis operates "
            "locally at presynaptic terminals, and NMJ-specific actin pathology may not "
            "resolve with nuclear SMN restoration alone. Adding ROCK/LIMK2 inhibition "
            "could specifically address residual NMJ dysfunction."
        ),
        "target_symbol": "ROCK1",
        "hypothesis_type": "combinatorial",
        "tier": "B",
        "evidence_for": [
            "Clinical observation: Nusinersen patients plateau in motor function",
            "PMID 26025607: NMJ defects are early and persistent in SMA",
            "GSE208629: ROCK-LIMK2-CFL2 axis active in SMA MNs",
            "Local NMJ actin dynamics independent of nuclear SMN function"
        ],
        "evidence_against": [
            "NMJ recovery may just need more time after SMN restoration",
            "ROCK/LIMK2 pathway contribution to NMJ specifically not demonstrated",
            "Nusinersen + Fasudil drug interaction unknown"
        ],
        "testable_prediction": "Nusinersen-treated SMA mice should show residual NMJ denervation; adding Fasudil should further improve NMJ innervation beyond Nusinersen alone",
        "therapeutic_implication": "Provides rationale for add-on ROCK/LIMK2 therapy in Nusinersen-treated patients with motor function plateau",
        "confidence": 0.58,
        "tags": ["combination", "Nusinersen", "NMJ", "ROCK-LIMK2-CFL2", "residual-disease"]
    },
    {
        "title": "Sequential therapy: Risdiplam first to stabilize, then Fasudil to restore actin dynamics",
        "description": (
            "A sequential treatment strategy where Risdiplam is given first to restore "
            "SMN protein and stabilize MN survival, followed by Fasudil to address residual "
            "actin pathology. This avoids the complexity of simultaneous drug-drug interactions "
            "while still targeting both SMN and actin axes."
        ),
        "target_symbol": "ROCK2",
        "hypothesis_type": "combinatorial",
        "tier": "B",
        "evidence_for": [
            "Sequential therapy reduces drug interaction risk",
            "SMN restoration may be prerequisite for MNs to respond to actin therapy",
            "PMID 22397316: Fasudil effective even without SMN correction"
        ],
        "evidence_against": [
            "Delayed actin therapy may miss critical window",
            "MNs already lost cannot be rescued by sequential approach",
            "No preclinical data on sequential vs. simultaneous combination"
        ],
        "testable_prediction": "In SMA mice: Risdiplam (P0-P7) then Fasudil (P7-P21) should equal simultaneous treatment and be safer",
        "therapeutic_implication": "Simpler clinical trial design: enroll Risdiplam-stabilized patients for Fasudil add-on study",
        "confidence": 0.50,
        "tags": ["combination", "sequential", "Risdiplam", "Fasudil", "clinical-design"]
    },
    {
        "title": "Actin pathway gene signature predicts which SMA patients will benefit from ROCK/LIMK2 inhibition",
        "description": (
            "Not all SMA patients may have equal actin pathway dysregulation. A gene "
            "expression signature based on the 10 upregulated actin genes (LIMK2, CFL2, "
            "PFN2, ROCK1, ROCK2, ACTG1, etc.) measured in accessible tissue (blood, muscle "
            "biopsy) could identify patients most likely to respond to ROCK/LIMK2-targeted "
            "therapy — enabling precision medicine in SMA."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "biomarker",
        "tier": "B",
        "evidence_for": [
            "GSE208629: 10/14 actin genes UP in SMA MNs",
            "Biomarker-guided therapy improves clinical outcomes (oncology precedent)",
            "Gene expression signatures measurable in blood/muscle"
        ],
        "evidence_against": [
            "Blood gene expression may not reflect MN-specific actin changes",
            "SMA patient population too small for biomarker-stratified trials",
            "Actin pathway upregulation may be universal in SMA rather than variable"
        ],
        "testable_prediction": "SMA patient RNA from PBMCs should show variable actin signature; higher signature patients should have lower motor function scores",
        "therapeutic_implication": "Enables patient selection for ROCK/LIMK2 inhibitor clinical trials, improving success probability",
        "confidence": 0.45,
        "tags": ["biomarker", "precision-medicine", "gene-signature", "patient-selection", "clinical"]
    },
    {
        "title": "CORO1C-driven neuroinflammation amplifies motor neuron actin pathology via microglial ROS",
        "description": (
            "CORO1C is NOT motor neuron-specific — it is highest in microglia and endothelial "
            "cells. Microglial CORO1C upregulation may drive neuroinflammation via enhanced "
            "phagocytic activity and ROS production. The resulting oxidative stress could "
            "further dysregulate the ROCK-LIMK2-CFL2 axis in nearby MNs, creating a "
            "non-cell-autonomous amplification loop."
        ),
        "target_symbol": "CORO1C",
        "hypothesis_type": "mechanism",
        "tier": "B",
        "evidence_for": [
            "GSE287257: CORO1C highest in microglia/endothelial, not MNs",
            "PMID 22983542: Coronins regulate immune cell migration and phagocytosis",
            "PMID 30770349: Microglia activated in SMA spinal cord",
            "ROS activates RhoA-ROCK signaling in neurons"
        ],
        "evidence_against": [
            "CORO1C role in microglia-specific neuroinflammation not demonstrated",
            "Our previous MN-focused analysis was wrong about CORO1C — interpretation cautious",
            "Neuroinflammation is secondary in SMA compared to primary MN pathology"
        ],
        "testable_prediction": "Microglial CORO1C knockdown should reduce ROS production and partially rescue MN survival in SMA co-culture models",
        "therapeutic_implication": "Anti-inflammatory strategies targeting microglial CORO1C could complement MN-directed actin therapy",
        "confidence": 0.48,
        "tags": ["CORO1C", "microglia", "neuroinflammation", "ROS", "non-cell-autonomous"]
    },
    {
        "title": "The actin pathway constitutes an SMN-independent therapeutic axis for late-treated SMA patients",
        "description": (
            "Patients treated late (after significant MN loss) benefit less from SMN restoration. "
            "The ROCK-LIMK2-CFL2 actin pathway operates independently of SMN levels and could "
            "protect remaining MNs and improve NMJ function even in late-treated patients. "
            "This population (Type 2/3 SMA diagnosed after infancy) represents the greatest "
            "unmet medical need."
        ),
        "target_symbol": "ROCK1",
        "hypothesis_type": "therapeutic",
        "tier": "A",
        "evidence_for": [
            "PMID 22397316: Fasudil rescues SMA independently of SMN",
            "GSE208629: Actin pathway dysregulated in SMA MNs regardless of SMN status",
            "Late-treated SMA patients have persistent motor deficits despite SMN therapy",
            "Clinical need: thousands of SMA patients diagnosed too late for full SMN benefit"
        ],
        "evidence_against": [
            "Remaining MNs in late-treated patients may be too damaged for rescue",
            "Actin pathway may become irrelevant once MN loss exceeds threshold",
            "No clinical data on actin pathway therapies in any SMA cohort"
        ],
        "testable_prediction": "Fasudil should improve motor function in SMA mice treated after symptom onset (P10-P14), even without SMN restoration",
        "therapeutic_implication": "Actin pathway therapy could serve thousands of SMA patients who missed the window for optimal SMN treatment",
        "confidence": 0.65,
        "tags": ["SMN-independent", "late-treatment", "unmet-need", "clinical", "ROCK-LIMK2-CFL2"]
    },
    {
        "title": "Dual ROCK1/ROCK2 + LIMK2 inhibition prevents resistance to single-pathway inhibitors in SMA",
        "description": (
            "Single-target inhibition often leads to compensatory upregulation of parallel "
            "pathways. ROCK inhibition alone may lead to LIMK2 activation via alternative "
            "kinases (PAK, MRCK). Simultaneous inhibition of ROCK1/2 and LIMK2 would prevent "
            "this escape mechanism, providing durable pathway suppression."
        ),
        "target_symbol": "LIMK2",
        "hypothesis_type": "combinatorial",
        "tier": "C",
        "evidence_for": [
            "Resistance to kinase inhibitors well-documented in oncology",
            "Multiple kinases can activate LIMK2 (ROCK, PAK, MRCK)",
            "GSE208629: Both ROCK and LIMK2 upregulated — both need targeting"
        ],
        "evidence_against": [
            "SMA is not cancer — resistance mechanisms may differ",
            "Dual kinase inhibition increases toxicity risk",
            "No evidence of ROCK inhibitor resistance in SMA models"
        ],
        "testable_prediction": "Long-term Fasudil treatment of SMA iPSC-MNs should show phospho-LIMK2 rebound; adding LIMK2 inhibitor should prevent rebound",
        "therapeutic_implication": "Rational combination prevents resistance and provides sustained actin pathway normalization",
        "confidence": 0.38,
        "tags": ["combination", "resistance", "ROCK", "LIMK2", "durability"]
    },
    {
        "title": "Actin pathway dysregulation as the unifying mechanism for cardiac, bone, and vascular pathology in SMA",
        "description": (
            "SMA is a multisystem disease affecting heart, bone, and vasculature in addition "
            "to motor neurons. The ROCK-LIMK2-CFL2 actin pathway is active in all these "
            "tissues. Actin dysregulation may drive cardiac remodeling (cardiomyocyte actin), "
            "bone loss (osteoclast actin rings), and vascular defects (endothelial actin) in "
            "SMA — making ROCK/LIMK2 inhibition a multisystem therapeutic strategy."
        ),
        "target_symbol": "ROCK1",
        "hypothesis_type": "mechanism",
        "tier": "C",
        "evidence_for": [
            "PMID 28988988: Cardiac defects in SMA patients",
            "PMID 30051899: Bone pathology in SMA mice",
            "ROCK-actin pathway active in cardiomyocytes, osteoclasts, endothelial cells",
            "GSE208629: Actin pathway centrally dysregulated in SMA"
        ],
        "evidence_against": [
            "Multisystem SMA pathology may be SMN-dependent, not actin-dependent",
            "ROCK/LIMK2 pathway regulation differs between tissues",
            "Peripheral actin pathway changes not validated in SMA patients"
        ],
        "testable_prediction": "SMA mouse cardiomyocytes and osteoclasts should show ROCK-LIMK2-CFL2 axis dysregulation; Fasudil should improve cardiac and bone parameters",
        "therapeutic_implication": "ROCK/LIMK2 inhibition could address multisystem SMA with a single therapeutic approach",
        "confidence": 0.40,
        "tags": ["multisystem", "cardiac", "bone", "vascular", "ROCK-LIMK2-CFL2", "actin"]
    },
]

# ---------------------------------------------------------------------------
# Database insertion logic
# ---------------------------------------------------------------------------

# Map our hypothesis types to DB-valid types
# DB CHECK: 'target', 'combination', 'repurposing', 'biomarker', 'mechanism'
TYPE_MAP = {
    "mechanism": "mechanism",
    "mechanistic": "mechanism",
    "therapeutic": "repurposing",
    "biomarker": "biomarker",
    "combinatorial": "combination",
}


async def insert_via_db(hypotheses: list[dict], dry_run: bool = False) -> dict:
    """Insert hypotheses directly into the database."""
    from sma_platform.core.config import settings
    from sma_platform.core.database import close_pool, execute, fetch, fetchrow, init_pool

    await init_pool(settings.database_url)

    # Get existing hypothesis titles to avoid duplicates
    existing = await fetch("SELECT title FROM hypotheses")
    existing_titles = {r["title"] for r in existing}

    success = 0
    skipped = 0
    errors = []

    for h in hypotheses:
        if h["title"] in existing_titles:
            print(f"  SKIP (exists): {h['title'][:70]}...")
            skipped += 1
            continue

        db_type = TYPE_MAP.get(h["hypothesis_type"], "mechanism")
        metadata = json.dumps({
            "target_symbol": h["target_symbol"],
            "tier": h["tier"],
            "evidence_for": h["evidence_for"],
            "evidence_against": h["evidence_against"],
            "testable_prediction": h["testable_prediction"],
            "therapeutic_implication": h["therapeutic_implication"],
            "tags": h["tags"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "actin_pathway_single_cell_validation",
            "datasets": ["GSE208629", "GSE287257"],
        })

        if dry_run:
            print(f"  DRY-RUN: {h['title'][:70]}... (conf={h['confidence']}, type={db_type})")
            success += 1
            continue

        try:
            await execute(
                """INSERT INTO hypotheses
                   (hypothesis_type, title, description, rationale,
                    supporting_evidence, contradicting_evidence,
                    confidence, status, generated_by, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                db_type,
                h["title"],
                h["description"],
                h["description"],  # rationale = description
                [],  # supporting_evidence UUIDs — we don't have claim UUIDs
                [],  # contradicting_evidence UUIDs
                h["confidence"],
                "proposed",
                "actin_pathway_analysis",
                metadata,
            )
            print(f"  OK: {h['title'][:70]}... (conf={h['confidence']})")
            success += 1
        except Exception as e:
            err_msg = f"FAIL: {h['title'][:50]}... — {e}"
            print(f"  {err_msg}")
            errors.append(err_msg)

    await close_pool()

    return {"success": success, "skipped": skipped, "errors": len(errors), "error_details": errors}


async def insert_via_api(hypotheses: list[dict], dry_run: bool = False) -> dict:
    """Insert hypotheses via HTTP POST to the live API."""
    import httpx

    base_url = "https://sma-research.info/api/v2"
    headers = {"x-admin-key": "sma-admin-2026", "Content-Type": "application/json"}

    success = 0
    skipped = 0
    errors = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, get existing hypotheses to check for duplicates
        try:
            resp = await client.get(f"{base_url}/hypotheses", params={"limit": 5000})
            if resp.status_code == 200:
                existing_titles = {h["title"] for h in resp.json()}
            else:
                existing_titles = set()
                print(f"  Warning: Could not fetch existing hypotheses (HTTP {resp.status_code})")
        except Exception as e:
            existing_titles = set()
            print(f"  Warning: Could not connect to API: {e}")

        for h in hypotheses:
            if h["title"] in existing_titles:
                print(f"  SKIP (exists): {h['title'][:70]}...")
                skipped += 1
                continue

            db_type = TYPE_MAP.get(h["hypothesis_type"], "mechanism")
            payload = {
                "hypothesis_type": db_type,
                "title": h["title"],
                "description": h["description"],
                "rationale": h["description"],
                "confidence": h["confidence"],
                "status": "proposed",
                "generated_by": "actin_pathway_analysis",
                "metadata": {
                    "target_symbol": h["target_symbol"],
                    "tier": h["tier"],
                    "evidence_for": h["evidence_for"],
                    "evidence_against": h["evidence_against"],
                    "testable_prediction": h["testable_prediction"],
                    "therapeutic_implication": h["therapeutic_implication"],
                    "tags": h["tags"],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source": "actin_pathway_single_cell_validation",
                    "datasets": ["GSE208629", "GSE287257"],
                },
            }

            if dry_run:
                print(f"  DRY-RUN: {h['title'][:70]}... (conf={h['confidence']})")
                success += 1
                continue

            try:
                resp = await client.post(
                    f"{base_url}/hypotheses",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    print(f"  OK: {h['title'][:70]}... (conf={h['confidence']})")
                    success += 1
                elif resp.status_code == 404:
                    # POST endpoint doesn't exist — fall back to DB mode
                    print("  API POST /hypotheses not available — switching to DB mode")
                    return await insert_via_db(hypotheses, dry_run)
                else:
                    err = f"HTTP {resp.status_code}: {resp.text[:100]}"
                    print(f"  FAIL: {h['title'][:50]}... — {err}")
                    errors.append(err)
            except Exception as e:
                err_msg = f"FAIL: {h['title'][:50]}... — {e}"
                print(f"  {err_msg}")
                errors.append(err_msg)

    return {"success": success, "skipped": skipped, "errors": len(errors), "error_details": errors}


def print_summary(hypotheses: list[dict]) -> None:
    """Print hypothesis count summary by target and tier."""
    from collections import Counter

    print("\n" + "=" * 70)
    print("ACTIN PATHWAY HYPOTHESES — SUMMARY")
    print("=" * 70)

    by_target = Counter(h["target_symbol"] for h in hypotheses)
    by_tier = Counter(h["tier"] for h in hypotheses)
    by_type = Counter(h["hypothesis_type"] for h in hypotheses)

    print(f"\nTotal hypotheses: {len(hypotheses)}")

    print("\nBy target:")
    for target, count in sorted(by_target.items(), key=lambda x: -x[1]):
        print(f"  {target:12s}: {count}")

    print("\nBy tier:")
    for tier in ["A", "B", "C"]:
        print(f"  Tier {tier}: {by_tier.get(tier, 0)}")

    print("\nBy type:")
    for typ, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {typ:15s}: {count}")

    avg_conf = sum(h["confidence"] for h in hypotheses) / len(hypotheses)
    print(f"\nAverage confidence: {avg_conf:.2f}")

    print("\nTier A hypotheses (highest evidence):")
    for h in hypotheses:
        if h["tier"] == "A":
            print(f"  [{h['target_symbol']:6s}] {h['title'][:80]} (conf={h['confidence']})")

    print()


async def main():
    parser = argparse.ArgumentParser(description="Seed SMA actin pathway hypotheses")
    parser.add_argument("--api", action="store_true", help="Use HTTP API instead of direct DB")
    parser.add_argument("--dry-run", action="store_true", help="Print hypotheses without inserting")
    args = parser.parse_args()

    print_summary(HYPOTHESES)

    mode = "API" if args.api else "DB"
    print(f"{'DRY RUN — ' if args.dry_run else ''}Inserting {len(HYPOTHESES)} hypotheses via {mode}...")
    print("-" * 70)

    if args.api:
        result = await insert_via_api(HYPOTHESES, dry_run=args.dry_run)
    else:
        result = await insert_via_db(HYPOTHESES, dry_run=args.dry_run)

    print("-" * 70)
    print(f"Results: {result['success']} inserted, {result['skipped']} skipped, {result['errors']} errors")
    if result.get("error_details"):
        print("Errors:")
        for e in result["error_details"]:
            print(f"  - {e}")


if __name__ == "__main__":
    asyncio.run(main())
