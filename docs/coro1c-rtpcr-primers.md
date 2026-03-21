# CORO1C Intron Retention RT-PCR Primer Design

**Purpose:** Detect intron retention between exons 9 and 10 of CORO1C in SMA patient-derived cells.
**Cost:** ~$50 (primers + reagents for gel-based RT-PCR)
**Turnaround:** 1 day bench time, results same day

## Gene Information

| Field | Value |
|-------|-------|
| Gene | CORO1C (Coronin 1C) |
| RefSeq mRNA | NM_014325.4 |
| Chromosome | 12 (minus strand) |
| Genome Build | GRCh38 / hg38 |
| Exon 8 | chr12:108,652,417-108,652,272 (146 bp) |
| **Exon 9** | **chr12:108,649,020-108,648,963 (58 bp microexon)** |
| **Intron 9/10** | **chr12:108,648,962-108,648,851 (112 bp, GT-AG canonical)** |
| **Exon 10** | **chr12:108,648,850-108,648,605 (246 bp)** |

### Critical Region Sequences (5' to 3', sense strand)

```
Exon 9 (58 bp):
  ATTCTTCAAACTTCATGAGAGAAAGTGTGAACCTATTATTATGACTGTTCCCAGGAAG

Intron 9/10 (112 bp):
  GTGAGTGCTGAGTTTTCTAGACAATCCATATTTTAAACAAATGTAAAAATAAAATTCA
  AAAATCCCAGGCCTTTCTTCTTCCTTACCCACGGGTGCCAAATGTCTCTTGTAG
  ^^ GT (donor)                                           ^^ AG (acceptor)

Exon 10 first 80 bp:
  TCTGACCTTTTCCAAGATGACCTGTATCCTGACACAGCGGGGCCAGAGGCCGCGCTGGA
  GGCAGAAGAGTGGTTCGAAGG
```

## Rationale

The 58 bp microexon (exon 9) is a predicted SMN-dependent splicing target. The flanking
112 bp intron has canonical GT-AG splice sites. In SMA cells with reduced SMN protein,
this intron may be partially retained, producing an aberrant mRNA. RT-PCR with flanking
primers will show two bands on a gel if intron retention is occurring: one at the normal
spliced size and one ~112 bp larger.

---

## Primer Sequences

### Primer 1: Forward (CORO1C-E8F)

| Property | Value |
|----------|-------|
| **Sequence** | `5'-CATTCAGCAGCAAGGAGCCT-3'` |
| Length | 20 nt |
| Tm | 59.0 C |
| GC content | 55.0% |
| Location | Exon 8, position 65-84 of 146 bp |

### Primer 2: Reverse (CORO1C-E10R)

| Property | Value |
|----------|-------|
| **Sequence** | `5'-GAACCACTCTTCTGCCTCCAG-3'` |
| Length | 21 nt |
| Tm | 58.5 C |
| GC content | 57.1% |
| Location | Exon 10, position 55-75 of 246 bp |

### Primer 3: Intron-Specific Forward (CORO1C-INT-F)

| Property | Value |
|----------|-------|
| **Sequence** | `5'-AATCCCAGGCCTTTCTTCTTCC-3'` |
| Length | 22 nt |
| Tm | 58.2 C |
| GC content | 50.0% |
| Location | Intron 9/10, position 61-82 of 112 bp |

### Primer 4: Junction Forward (CORO1C-JCT-F)

| Property | Value |
|----------|-------|
| **Sequence** | `5'-CTGTTCCCAGGAAGTCTGACC-3'` |
| Length | 21 nt |
| Tm | 58.1 C |
| GC content | 57.1% |
| Location | Spans exon 9/10 junction (14 bp exon 9 + 7 bp exon 10) |

### Primer Properties Summary

| Primer | Sequence (5'-3') | Nt | Tm (C) | GC (%) |
|--------|------------------|-----|--------|--------|
| CORO1C-E8F | CATTCAGCAGCAAGGAGCCT | 20 | 59.0 | 55.0 |
| CORO1C-E10R | GAACCACTCTTCTGCCTCCAG | 21 | 58.5 | 57.1 |
| CORO1C-INT-F | AATCCCAGGCCTTTCTTCTTCC | 22 | 58.2 | 50.0 |
| CORO1C-JCT-F | CTGTTCCCAGGAAGTCTGACC | 21 | 58.1 | 57.1 |

**Tm range:** 58.1-59.0 C (max difference 0.9 C -- excellent match)
**Tm method:** Nearest-neighbor (50 mM Na+, 250 nM primer concentration)

---

## PCR Reactions and Expected Products

### Reaction 1: Flanking RT-PCR (E8F + E10R) -- PRIMARY ASSAY

Detects both spliced and intron-retained isoforms simultaneously on a single gel.

| Condition | Band(s) | Size |
|-----------|---------|------|
| Normal / carrier cells | Single band | **215 bp** (exon 8-9-10, properly spliced) |
| SMA cells (low SMN) | **Two bands** | **215 bp** (spliced) + **327 bp** (intron retained) |

The 112 bp size difference is easily resolved on a 2% agarose gel.

```
                    SMA    Normal   Ladder
                    ___     ___
  327 bp -------> | * |   |   |    --- 400
                  |   |   |   |    --- 300
  215 bp -------> | * |   | * |    --- 200
                  |___|   |___|    --- 100
```

### Reaction 2: Intron-Specific RT-PCR (INT-F + E10R) -- CONFIRMATION

Only amplifies if the intron is retained in the mRNA. No product from properly spliced mRNA.

| Condition | Band | Size |
|-----------|------|------|
| Normal cells | **No band** | -- (intron is spliced out, primer binding site absent) |
| SMA cells | **Single band** | **127 bp** (confirms intron retention) |

### Reaction 3: Spliced-Only Control (JCT-F + E10R) -- POSITIVE CONTROL

Only amplifies properly spliced mRNA. The junction primer spans the exon 9/10 boundary
and cannot bind to pre-mRNA with retained intron.

| Condition | Band | Size |
|-----------|------|------|
| Normal cells | **Strong band** | **89 bp** |
| SMA cells | **Weaker band** | **89 bp** (reduced due to splicing defect) |

### Summary of All Reactions

| Reaction | Primers | Normal | SMA | Detects |
|----------|---------|--------|-----|---------|
| 1 (Flanking) | E8F + E10R | 215 bp | 215 + 327 bp | Both isoforms |
| 2 (Intron) | INT-F + E10R | No band | 127 bp | Retention only |
| 3 (Junction) | JCT-F + E10R | 89 bp | 89 bp (weak) | Spliced only |

---

## Specificity Verification

All primers were computationally verified:

- Forward primer (E8F): matches exon 8 of NM_014325.4 -- confirmed
- Reverse primer (E10R): matches exon 10 of NM_014325.4 -- confirmed
- Intron primer (INT-F): matches intron sequence, does NOT match spliced mRNA -- confirmed
- Junction primer (JCT-F): matches spliced mRNA, does NOT match pre-mRNA with retained intron -- confirmed

**BLAST verification recommended** before ordering (against human genome + transcriptome).

---

## Ordering Information

### IDT (Integrated DNA Technologies)

Order at: https://www.idtdna.com/pages/products/custom-dna-rna/dna-oligos

| Parameter | Value |
|-----------|-------|
| Scale | 25 nmol (standard, sufficient for ~1000 reactions) |
| Purification | Standard desalting |
| Format | Dry (lyophilized) |
| Estimated cost | ~$3-5 per primer |
| **Total for 4 primers** | **~$12-20** |
| Shipping | 1-2 business days (standard) |

### Primer Order Table (copy-paste for IDT)

```
Name                Sequence (5' to 3')            Scale    Purification
CORO1C-E8F          CATTCAGCAGCAAGGAGCCT           25nmol   Desalt
CORO1C-E10R         GAACCACTCTTCTGCCTCCAG          25nmol   Desalt
CORO1C-INT-F        AATCCCAGGCCTTTCTTCTTCC         25nmol   Desalt
CORO1C-JCT-F        CTGTTCCCAGGAAGTCTGACC          25nmol   Desalt
```

### Alternative Suppliers

- **Eurofins Genomics** (Europe): https://eurofinsgenomics.com -- faster EU delivery
- **Sigma-Aldrich/Merck**: https://www.sigmaaldrich.com/oligos
- **Thermo Fisher**: https://www.thermofisher.com/oligos

---

## Protocol

### Materials Required

| Item | Catalog Example | Est. Cost |
|------|----------------|-----------|
| 4 custom primers (IDT, 25 nmol) | Custom order | $12-20 |
| RNA extraction kit | Qiagen RNeasy Mini (74104) | ~$5/sample |
| Reverse transcriptase | SuperScript IV (Invitrogen 18091050) or M-MLV | ~$3/reaction |
| Taq polymerase + dNTPs | GoTaq Green Master Mix (Promega M7122) | ~$1/reaction |
| Agarose | Standard molecular biology grade | ~$1/gel |
| DNA ladder | 100 bp ladder (NEB N3231) | ~$1/gel |
| SYBR Safe or EtBr | Gel staining | ~$1/gel |
| **Total per experiment** | | **~$25-50** |

### Step-by-Step Protocol

#### Day 0: Cell Preparation
- Culture cells to 70-80% confluence
- Recommended cell lines:
  - **SMA:** SMA type I fibroblasts (e.g., GM03813, Coriell) or iPSC-derived motor neurons
  - **Control:** Carrier fibroblasts (e.g., GM03814) or healthy donor cells
  - **Rescue control:** SMA cells treated with nusinersen/risdiplam (if available)

#### Step 1: RNA Extraction (45 min)

1. Harvest cells (0.5-1 x 10^6 cells)
2. Extract total RNA using TRIzol or RNeasy Mini Kit
3. DNase I treatment (critical -- removes genomic DNA contamination)
4. Measure RNA concentration and quality (A260/A280 > 1.8)
5. Use 0.5-1 ug total RNA for RT

**Critical:** Include a no-RT control (RNA + water instead of reverse transcriptase)
to confirm amplification is from mRNA, not genomic DNA.

#### Step 2: Reverse Transcription (1 hour)

```
Component                    Volume
RNA (0.5-1 ug)              11 uL
Oligo(dT)18 primer (50 uM)  1 uL
----------------------------------
Denature: 65 C, 5 min, then ice 1 min

Add:
5x RT buffer                 4 uL
dNTPs (10 mM each)          1 uL
RNase inhibitor              1 uL
Reverse transcriptase        1 uL
Nuclease-free water          1 uL
----------------------------------
Total                        20 uL

Incubate: 50 C for 30 min (SuperScript IV) or 42 C for 60 min (M-MLV)
Inactivate: 80 C for 10 min
```

Alternatively, use random hexamers (for better intron coverage if intron-retained
transcripts have disrupted poly-A processing).

#### Step 3: PCR Amplification (2 hours)

Set up 3 reactions per sample (or start with Reaction 1 only):

```
Component                    Volume (per reaction)
cDNA template (from Step 2)  2 uL
GoTaq Green Master Mix 2x    12.5 uL
Forward primer (10 uM)       1 uL
Reverse primer (10 uM)       1 uL
Nuclease-free water           8.5 uL
-----------------------------------
Total                        25 uL
```

**Reaction Setup:**

| Tube | Forward Primer | Reverse Primer | Detects |
|------|---------------|----------------|---------|
| 1 | CORO1C-E8F | CORO1C-E10R | Both isoforms |
| 2 | CORO1C-INT-F | CORO1C-E10R | Intron retention only |
| 3 | CORO1C-JCT-F | CORO1C-E10R | Spliced only (control) |

**Thermocycler Program:**

```
Step                Temperature    Time        Cycles
Initial denaturation   95 C        3 min       1x
Denaturation           95 C        30 sec      |
Annealing              56 C        30 sec      | 30-35x
Extension              72 C        30 sec      |
Final extension        72 C        5 min       1x
Hold                    4 C        forever
```

**Annealing temperature:** 56 C (recommended). Run gradient PCR 54-59 C on first attempt
to optimize.

**Cycle number:** Start with 30 cycles. If bands are faint, increase to 35.
For semi-quantitative comparison, keep cycle number in the linear amplification range.

#### Step 4: Gel Electrophoresis (1 hour)

1. Prepare 2% agarose gel in 1x TAE buffer
2. Add SYBR Safe (1:10,000) or ethidium bromide
3. Load 10 uL of each PCR product + 5 uL 100 bp DNA ladder
4. Run at 100V for 45-60 minutes
5. Image under UV or blue light

**Expected band pattern:**

```
Lane:   1     2     3     4     5     6     7     8     9     L
       Rxn1  Rxn2  Rxn3  Rxn1  Rxn2  Rxn3  Rxn1  Rxn2  Rxn3
       ----SMA----  ----Normal---  ----No RT----
400 -                                                          ---
327 -> [**]
300 -                                                          ---
200 -                                                          ---
215 -> [**]               [**]
127 ->       [**]
100 -                                                          ---
 89 ->             [*]                [**]
```

#### Step 5: Interpretation

| Result | Interpretation |
|--------|---------------|
| Reaction 1 shows TWO bands (215 + 327 bp) in SMA but ONE band (215 bp) in normal | **Intron retention confirmed in SMA cells** |
| Reaction 2 shows band (127 bp) in SMA but none in normal | **Direct confirmation of intron retention** |
| Reaction 3 shows weaker band in SMA vs normal | **Reduced splicing efficiency in SMA** |
| No bands in no-RT control | **No genomic DNA contamination (experiment is valid)** |
| Reaction 1 shows single band (215 bp) in both SMA and normal | **No intron retention detected (null result)** |

---

## Controls

| Control | Purpose |
|---------|---------|
| No-RT control | Confirms signal is from mRNA, not genomic DNA |
| Normal/carrier cells | Negative control for intron retention |
| GAPDH or ACTB RT-PCR | Confirms RNA quality and RT success |
| Water (no-template) | Confirms no primer contamination |
| Genomic DNA template | Expected to give large product (confirms primers work on DNA) |

---

## Quantitative Follow-Up (Optional)

If intron retention is detected by gel, quantify the ratio using:

1. **RT-qPCR:** Use INT-F + E10R (intron-retained) vs JCT-F + E10R (spliced) primer pairs.
   Calculate retention ratio as 2^(-deltaCt).

2. **Densitometry:** Quantify gel band intensities from Reaction 1 using ImageJ.
   Report as: Retention Index = Intensity(327bp) / [Intensity(215bp) + Intensity(327bp)]

3. **Sanger sequencing:** Gel-extract both bands from Reaction 1 and sequence to confirm
   the 327 bp band contains the full 112 bp intron sequence.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No bands at all | Check RNA quality (run on gel), increase template, increase cycles to 35 |
| Bands in no-RT control | Genomic DNA contamination -- repeat DNase treatment |
| Smear instead of bands | Reduce template amount, check primer specificity by BLAST |
| Only one band in Rxn 1 | May be null result (no retention) or PCR bias toward shorter product. Try reducing extension time to 20 sec to favor shorter products |
| Extra unexpected bands | Non-specific amplification -- increase annealing temp to 58 C |
| Weak bands | Increase cDNA input or cycle number; verify RNA concentration |

---

## Source Data

- mRNA RefSeq: [NM_014325.4](https://www.ncbi.nlm.nih.gov/nuccore/NM_014325.4)
- Gene ID: [23603](https://www.ncbi.nlm.nih.gov/gene/23603)
- Genome: NC_000012.12 (GRCh38/hg38)
- Primer design: Biopython MeltingTemp (nearest-neighbor method)
- Sequences verified: Exon/intron boundaries confirmed by alignment of mRNA to genomic DNA
- Splice sites verified: GT (donor) and AG (acceptor) canonical dinucleotides confirmed

---

## Citation

If this assay produces publishable results, cite:

> CORO1C intron 9/10 retention was detected by RT-PCR using primers flanking the 112 bp
> intron between exons 9 and 10 (NM_014325.4). Primers were designed using Biopython
> nearest-neighbor Tm calculation and verified against NCBI RefSeq sequences.
> SMA Research Platform (https://sma-research.info).

---

*Generated: 2026-03-21*
*Platform: SMA Research Platform on moltbot (Biopython + NCBI Entrez)*
*All sequences verified against NCBI NM_014325.4 and NC_000012.12 (GRCh38)*
