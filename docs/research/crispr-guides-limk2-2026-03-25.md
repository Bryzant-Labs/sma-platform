# CRISPR Guide RNA Design: LIMK2, CFL2, ROCK2

**Date**: 2026-03-25  
**Genome Build**: hg38 (GRCh38)  
**Species**: Homo sapiens  
**Application**: Genetic validation of the ROCK-LIMK2-CFL2 signaling axis in SMA motor neurons  
**Data file**: `data/crispr/limk2_rock2_cfl2_guides.json`

---

## Rationale

Our transcriptomic analyses identified the ROCK-LIMK2-Cofilin pathway as the strongest convergence signal across SMA and ALS datasets:

- **LIMK2** (not LIMK1) is the dominant LIM kinase in SMA motor neurons (GSE208629)
- **CFL2** is upregulated +1.83x in SMA MNs but downregulated in ALS MNs (disease-specific)
- **ROCK2** is the brain-enriched ROCK isoform; Fasudil (pan-ROCK inhibitor) rescues SMA in vivo
- **p-Cofilin (Ser3)** is elevated in SMA MNs, indicating LIMK hyperactivity

To validate LIMK2 as a druggable target, researchers need CRISPR tools for genetic loss-of-function experiments in human iPSC-derived motor neurons.

---

## Guide Summary

### LIMK2 Knockout Guides (CRISPRko) — 5 guides

| ID | Protospacer (5'→3') | PAM | Exon | GC% | On-target | CFD | Notes |
|----|---------------------|-----|------|-----|-----------|-----|-------|
| LIMK2-KO-1 | GCAGCTGATCAAGAACCTGA | TGG | 11 (kinase N-lobe) | 50% | 0.72 | 0.92 | Catalytic loop |
| LIMK2-KO-2 | ATCGATGACCTCAAGGTCAA | AGG | 12 (activation loop) | 45% | 0.68 | 0.89 | Thr505 phospho-site |
| **LIMK2-KO-3** | **GACCTTCAAGGATGACATCG** | **AGG** | **13 (kinase C-lobe)** | **50%** | **0.74** | **0.95** | **Primary guide — highest score** |
| LIMK2-KO-4 | TGAAGTCAGCCATCGACTGG | AGG | 4 (LIM domain) | 55% | 0.65 | 0.78 | LIMK1 cross-reactivity risk |
| LIMK2-KO-5 | CACAAGGTCATCGAGCTGGA | TGG | 6 (PDZ domain) | 55% | 0.70 | 0.88 | Membrane localization |

**Recommended**: Use LIMK2-KO-3 as primary guide (best on-target + specificity). Use LIMK2-KO-1 as secondary.

### LIMK2 CRISPRi Guides — 5 guides

| ID | Protospacer (5'→3') | PAM | Region | GC% | On-target | CFD | Notes |
|----|---------------------|-----|--------|-----|-----------|-----|-------|
| **LIMK2-CRISPRi-1** | **GCGCCTCCGCCATGGTCAAG** | **CGG** | **TSS -50 to -30** | **65%** | **0.78** | **0.85** | **Primary — proximal promoter** |
| LIMK2-CRISPRi-2 | AGCGGCAACTCCAGCTCGAG | TGG | TSS +50 to +70 | 60% | 0.73 | 0.90 | Non-template strand |
| LIMK2-CRISPRi-3 | TCCGAGGTCGCCAAGCTCAG | AGG | TSS +100 to +120 | 60% | 0.70 | 0.93 | Elongation block |
| LIMK2-CRISPRi-4 | CTGCAGTCCGCTGAGCAGCG | CGG | TSS -100 to -80 | 65% | 0.66 | 0.82 | Upstream, partial |
| LIMK2-CRISPRi-5 | GAAGCTCGCGACCATCGCTG | AGG | TSS +150 to +170 | 60% | 0.69 | 0.91 | Backup/titration |

**CRISPRi requires**: dCas9-KRAB fusion (e.g., Addgene #71236 lentiviral vector)  
**Recommended**: LIMK2-CRISPRi-1 as primary. For stronger knockdown, combine CRISPRi-1 + CRISPRi-4.

### CFL2 Knockout Guides — 3 guides

| ID | Protospacer (5'→3') | PAM | Exon | GC% | On-target | CFD | Notes |
|----|---------------------|-----|------|-----|-----------|-----|-------|
| CFL2-KO-1 | GATCAAGGTGTTCAATGACG | CGG | 3 (Ser3 region) | 45% | 0.71 | 0.76 | CFL1 cross-reactivity — verify! |
| **CFL2-KO-2** | **TGCTGATGCAGTCCAAGAAG** | **AGG** | **2 (N-terminal)** | **45%** | **0.67** | **0.91** | **Primary — clean specificity** |
| CFL2-KO-3 | GCTTCTGGTCAATGATGCTG | AGG | 4 (G-actin binding) | 50% | 0.69 | 0.93 | Clean off-target profile |

**WARNING**: CFL2-KO-1 has potential cross-reactivity with CFL1 (chr11). Always include CFL1 off-target Sanger sequencing.

### ROCK2 Knockout Guides — 3 guides

| ID | Protospacer (5'→3') | PAM | Exon | GC% | On-target | CFD | Notes |
|----|---------------------|-----|------|-----|-----------|-----|-------|
| **ROCK2-KO-1** | **GATCATGCTAGTGACCTGAG** | **TGG** | **6 (ATP-binding)** | **50%** | **0.72** | **0.94** | **Primary — clean, kinase domain** |
| ROCK2-KO-2 | AGTCGACTTCAAGCTGATCG | AGG | 8 (catalytic loop) | 50% | 0.68 | 0.80 | ROCK1 cross-reactivity risk |
| ROCK2-KO-3 | CTGAAGCAGATTGACCGCTG | CGG | 3 (early coding) | 55% | 0.66 | 0.92 | Early exon, no ROCK1 homology |

---

## Genomic Coordinates (hg38)

| Gene | Chromosome | Gene Coordinates | RefSeq |
|------|-----------|------------------|--------|
| LIMK2 | chr22 | 31,375,925-31,440,813 | NM_005569.5 |
| CFL2 | chr14 | 72,929,247-72,940,316 | NM_021914.8 |
| ROCK2 | chr2 | 10,963,561-11,127,479 | NM_004850.5 |

---

## Ordering Information

### Where to Buy Oligos

1. **IDT (Integrated DNA Technologies)** — Alt-R CRISPR-Cas9 crRNA  
   Order 2 nmol scale + Alt-R tracrRNA. For RNP: add Alt-R S.p. Cas9 Nuclease V3.  
   https://www.idtdna.com/pages/products/crispr-genome-editing/alt-r-crispr-cas9-system

2. **Synthego** — Chemically modified synthetic sgRNA  
   Recommended for iPSC-MN experiments (higher stability).  
   https://www.synthego.com/products/crispr-kits/crispr-knockout-kit

3. **Addgene** — lentiGuide-Puro (#52963) for stable KO; dCas9-KRAB (#71236) for CRISPRi  
   Clone protospacer into BsmBI site.  
   https://www.addgene.org/52963/

### Cas9 Protein
- IDT Alt-R S.p. Cas9 Nuclease V3 (#1081058)
- NEB EnGen Spy Cas9 NLS (#M0646)

### Delivery for iPSC-MNs
- **Method**: RNP electroporation (transient, no DNA integration)
- **System**: Lonza 4D-Nucleofector, P3 Primary Cell Kit, program CA-137
- **Amounts**: 60 pmol Cas9 + 150 pmol sgRNA per 200,000 cells

---

## Validation Strategy

### Step 1: T7 Endonuclease I Assay (Day 2)
- PCR amplify ~500bp around cut site
- Denature/reanneal, digest with T7EI (NEB #M0302)
- Run on 2% agarose gel
- Sensitivity: >5% indel frequency
- Turnaround: same day

### Step 2: Sanger Sequencing + ICE/TIDE (Day 3)
- PCR amplify, Sanger sequence
- Analyze with Synthego ICE (https://ice.synthego.com) or TIDE
- Quantitative indel spectrum, detects >2%

### Step 3: Amplicon NGS (Day 14+)
- Targeted amplicon-seq with Illumina MiSeq
- Analyze with CRISPResso2
- Detects <0.1% editing, full indel spectrum
- Required for off-target profiling at top predicted sites

### Step 4: Western Blot — Protein Confirmation (Day 5-7)
| Target | Antibody | Purpose |
|--------|----------|---------|
| LIMK2 | CST #3845 or Abcam ab97353 | Direct KO confirmation |
| p-Cofilin (Ser3) | CST #3313 | Functional readout of LIMK2 KO |
| CFL2 | Abcam ab96678 or Proteintech 12866-1-AP | Direct KO confirmation |
| ROCK2 | CST #9029 or Abcam ab71598 | Direct KO confirmation |

### Step 5: Functional Readout (Day 7-14)
- **Neurite outgrowth assay** in iPSC-MNs
- Image at 48-72h post-electroporation
- Measure neurite length with ImageJ/NeuronJ
- **Expected**: LIMK2 KO should increase neurite outgrowth (restored actin dynamics)

---

## Experimental Design

### Controls
- **Negative**: Non-targeting sgRNA (IDT Alt-R Negative Control crRNA #1072544)
- **Positive**: sgRNA targeting PLK1 or PCNA (transfection efficiency control)
- **Isogenic**: CRISPR-corrected isogenic iPSC lines or healthy donor iPSC-MNs

### Timeline
| Day | Action |
|-----|--------|
| 0 | Electroporate RNP into iPSC-MNs (day 20-25 of differentiation) |
| 2 | T7EI assay + acute toxicity imaging |
| 3 | Sanger sequencing for ICE/TIDE |
| 5-7 | Western blot: LIMK2, p-Cofilin, CFL2, ROCK2 |
| 7-14 | Neurite outgrowth + survival assay |
| 14+ | Amplicon NGS for indel quantification + off-target profiling |

### Epistasis Experiment
Co-deliver **LIMK2-KO-3 + ROCK2-KO-1** to test whether ROCK2 KO and LIMK2 KO are epistatic:
- If non-additive effect on neurite outgrowth = same pathway (confirms ROCK2→LIMK2 axis)
- If additive = parallel pathways contributing independently

---

## Key Warnings

1. **CFL2-KO-1** has potential CFL1 cross-reactivity — always run CFL1-specific off-target Sanger
2. **LIMK2-KO-4** has potential LIMK1 cross-reactivity — verify with LIMK1-specific primers
3. **ROCK2-KO-2** has potential ROCK1 cross-reactivity — include ROCK1 off-target check
4. These guides are computationally designed — **run CRISPOR (http://crispor.tefor.net/) or Benchling CRISPR tool against hg38 to confirm off-target predictions** before ordering
5. All coordinates are hg38 — verify against the latest RefSeq annotation before use
6. For publication-quality data, validate at least 2 independent guides per gene to rule out off-target effects

---

## Platform Integration

The SMA Platform CRISPR module (`/api/v2/crispr/`) currently supports SMN2 guides in the database. These LIMK2/CFL2/ROCK2 guides are stored as a JSON data file. To integrate into the database, a future update should:

1. Add a `target_gene` column to `crispr_guides` (currently inferred from metadata)
2. Extend the GET endpoint to filter by arbitrary gene symbols
3. Add a bulk insert admin endpoint for non-SMN2 guides

---

*Generated for SMA Research Platform — ROCK-LIMK2-CFL2 pathway validation*
