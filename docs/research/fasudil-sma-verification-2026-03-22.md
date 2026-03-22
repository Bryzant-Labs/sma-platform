# Fasudil + SMA Claim Verification Report

**Date**: 2026-03-22
**Claim under review**: "Fasudil significantly improves survival of SMA mice"
**Extractor confidence**: 1.00
**Verdict**: VERIFIED TRUE

---

## 1. Primary Claim (PMID 22397316) — VERIFIED

| Field | Value |
|-------|-------|
| **PMID** | [22397316](https://pubmed.ncbi.nlm.nih.gov/22397316/) |
| **Title** | Fasudil improves survival and promotes skeletal muscle development in a mouse model of spinal muscular atrophy |
| **Authors** | Melissa Bowerman et al. (Ottawa Hospital Research Institute) |
| **Journal** | BMC Medicine, vol. 10, article 24 |
| **Year** | 2012 (published March 7) |
| **DOI** | 10.1186/1741-7015-10-24 |
| **PubMed verified** | YES — paper exists and title matches exactly |

### Study Details
- **Disease**: Spinal Muscular Atrophy (SMA) — NOT ALS
- **Mouse model**: Smn2B/- mice (severe SMA model)
- **Study type**: In vivo (mouse lifespan study), NOT just in vitro
- **Dosing**: Fasudil 30 mg/kg twice daily by oral gavage, postnatal day 3-21
- **Primary endpoint**: Survival (lifespan)

### Key Results
1. Fasudil **significantly improves survival** of SMA mice (p-value significant)
2. Significant increase in **muscle fiber size** and **postsynaptic endplate size**
3. Restores normal expression of **skeletal muscle development markers**
4. Effect is **NOT mediated by SMN protein upregulation**
5. Effect is **NOT mediated by motor neuron preservation**
6. Mechanism appears to be **muscle-specific** (direct skeletal muscle benefit)

### Critical Assessment
- **Is this a hallucination?** NO — PMID exists on PubMed, title matches exactly
- **Is this about ALS, not SMA?** NO — explicitly uses Smn2B/- SMA mouse model
- **Is "survival" cell survival or mouse lifespan?** MOUSE LIFESPAN (in vivo, oral dosing P3-P21)
- **Is this about ROCK inhibitors generally?** NO — specifically tests Fasudil (a ROCK inhibitor) in SMA mice

---

## 2. Supporting SMA Claim (PMID 28916199) — VERIFIED

| Field | Value |
|-------|-------|
| **PMID** | [28916199](https://pubmed.ncbi.nlm.nih.gov/28916199/) |
| **Title** | ERK and ROCK functionally interact in a signaling network that is compensationally upregulated in Spinal Muscular Atrophy |
| **Journal** | Neurobiology of Disease |
| **Year** | 2017 |

### Key Findings
- ROCK and ERK pathways are bi-directionally linked in SMA
- Fasudil (ROCK inhibitor) and selumetinib (ERK inhibitor) tested in severe SMA mice, separately and combined
- ROCK inhibition ameliorated phenotype of selumetinib-treated SMA mice
- Demonstrates ROCK-to-ERK crosstalk is relevant for SMA pathophysiology
- Supports combinatorial targeting of both pathways

---

## 3. ALS Claims — Correctly Attributed (NOT misattributed to SMA)

The database also contains 17 fasudil claims from ALS papers. These are correctly labeled:

| PMID | Paper | Disease | Status |
|------|-------|---------|--------|
| [23763343](https://pubmed.ncbi.nlm.nih.gov/23763343/) | Fasudil limits motor neuron loss in ALS models | ALS (SOD1-G93A) | Correctly labeled ALS |
| [24311453](https://pubmed.ncbi.nlm.nih.gov/24311453/) | ROCK inhibition modulates microglia in ALS model | ALS (SOD1-G93A) | Correctly labeled ALS |
| [32231638](https://pubmed.ncbi.nlm.nih.gov/32231638/) | Compassionate use of Fasudil in 3 ALS patients | ALS (human) | Correctly labeled ALS |
| [40950480](https://pubmed.ncbi.nlm.nih.gov/40950480/) | ROCK-ALS trial post-hoc analysis | ALS (human trial) | Correctly labeled ALS |

**No misattribution detected.** The claim extractor correctly distinguished SMA from ALS sources.

---

## 4. Database Claim Summary

### SMA-Specific Fasudil Claims (from PMID 22397316, confidence 1.00):
1. "Fasudil significantly improves survival of SMA mice" — **VERIFIED**
2. "Fasudil administration results in a significant increase in muscle fiber and postsynaptic endplate size" — **VERIFIED**
3. "Fasudil administration restores normal expression of markers of skeletal muscle development" — **VERIFIED**

### SMA Pathway Claim (from PMID 28916199, confidence 0.99):
4. "Fasudil is a ROCK inhibitor" — **VERIFIED** (trivially true)

---

## 5. Scientific Significance for SMA Research

This is a **high-value finding** for the SMA platform because:

1. **Fasudil is clinically approved** (in Japan/China for cerebral vasospasm) — repurposing potential
2. **Oral bioavailability** — administered by oral gavage, not injection
3. **SMN-independent mechanism** — works via muscle, not by increasing SMN protein
4. This makes Fasudil a **complementary therapy** candidate alongside SMN-restoring drugs (nusinersen, risdiplam, onasemnogene)
5. The ROCK pathway is a **validated SMA target** with multiple supporting papers
6. **ALS convergence**: Fasudil also shows benefit in ALS models (SOD1-G93A mice and human compassionate use), suggesting shared ROCK pathway dysfunction across motor neuron diseases

### Limitations
- Only one SMA mouse study (Bowerman 2012) — no replication by independent group found
- Mouse model (Smn2B/-) may not fully predict human SMA response
- No SMA clinical trial of Fasudil has been conducted (as of 2026)
- Survival benefit mechanism bypasses motor neurons entirely — unusual and needs more investigation

---

## 6. Conclusion

**CLAIM STATUS: VERIFIED TRUE**

The claim "Fasudil improves survival in SMA mice" is **NOT a hallucination**. It is supported by a peer-reviewed publication (Bowerman et al., BMC Medicine 2012, PMID 22397316) that:
- Uses a genuine SMA mouse model (Smn2B/-)
- Measures actual mouse lifespan (not just cell survival)
- Shows statistically significant survival improvement
- Is correctly attributed in our database

The claim extractor performed correctly here. The confidence score of 1.00 is justified given that the paper title itself contains the exact claim.

---

## Sources
- [Bowerman et al. 2012 — PubMed](https://pubmed.ncbi.nlm.nih.gov/22397316/)
- [Bowerman et al. 2012 — Full Text (BMC Medicine)](https://bmcmedicine.biomedcentral.com/articles/10.1186/1741-7015-10-24)
- [Bowerman et al. 2012 — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3310724/)
- [Hensel et al. 2017 (ERK-ROCK) — PubMed](https://pubmed.ncbi.nlm.nih.gov/28916199/)
- [ROCK-ALS Trial post-hoc — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12424921/)
