# Hypothesis Auto-Generation Run — 2026-03-22

## Summary

| Metric | Value |
|--------|-------|
| **Claims in DB** | 14,187 |
| **Convergence signals found** | 177 |
| **Already had hypotheses** | 50 (skipped) |
| **New hypotheses generated** | 127 |
| **LLM-synthesized (Claude Sonnet)** | 122 |
| **Fallback (template-based)** | 5 |
| **Total hypotheses in DB** | 1,472 (was 1,285) |
| **Average confidence (new)** | 0.643 |
| **Generation time** | ~55 minutes |

### Parameters
- `days_back=30`, `min_claims=2`, `dry_run=false`
- Model: `claude-sonnet-4-6` via Anthropic API
- Generator: `convergence-hypothesis-agent`

### Notes
- 3 LLM JSON parse failures (empty response or truncated) — fell back to template
- 2 Anthropic API 529 "Overloaded" errors — fell back to template
- All 127 signals successfully persisted to the `hypotheses` table

---

## Top 25 Hypotheses by Confidence (LLM-generated)

### 1. NfL as pharmacodynamic biomarker (conf=0.82, 143 claims)
Neurofilament light chain (NfL) released from degenerating motor neuron axons serves as a quantitative, real-time pharmacodynamic biomarker of SMN-dependent axonal integrity. Restoration of SMN protein via nusinersen or onasemnogene abeparvovec reduces axonal cytoskeletal destabilization, decreasing NfL shedding proportionally to motor neuron rescue.

### 2. Apitegromab / myostatin blockade (conf=0.82, 48 claims)
Apitegromab rescues motor function in later-onset SMA (Types 2/3) by selectively blocking proteolytic activation of latent myostatin in the extracellular matrix, preventing ActRIIB-mediated SMAD2/3 signaling and reversing the atrophy-hypertrophy imbalance.

### 3. ROCK hyperactivation → NMJ collapse (conf=0.82, 29 claims)
ROCK hyperactivation in SMN-deficient motor neurons drives pathological actomyosin contraction via excessive MLC phosphorylation, destabilizing growth cone actin dynamics and NMJ maturation. ROCK inhibition rescues SMA phenotype primarily through peripheral neuromuscular connectivity restoration.

### 4. BCL2L1 (Bcl-xL) apoptotic threshold (conf=0.82, 24 claims)
SMN deficiency leads to transcriptional downregulation of BCL2L1 (Bcl-xL), shifting the Bcl-xL:Bax ratio toward pro-apoptotic signaling at the mitochondrial outer membrane, lowering the threshold for cytochrome c release and caspase activation.

### 5. Senataxin / R-loop accumulation (conf=0.82, 20 claims)
SMN deficiency causes reduced senataxin (SETX) protein levels at transcription-replication conflict sites, leading to pathological R-loop accumulation, replication fork stalling, and DNA double-strand breaks specifically in motor neurons.

### 6. DLK → C1q complement-mediated synapse elimination (conf=0.82, 17 claims)
SMN deficiency triggers DLK-dependent upregulation of C1q expression, which tags vulnerable proprioceptive synapses on motor neuron dendrites for complement-mediated elimination. C1q blockade preserves sensory-motor circuit integrity.

### 7. Stasimon/Tmem41b U12 mis-splicing (conf=0.82, 17 claims)
SMN deficiency causes mis-splicing of U12 intron-containing Stasimon/Tmem41b pre-mRNA, reducing Stasimon protein levels. Loss of Stasimon's ER-resident phospholipid scramblase activity impairs ER membrane homeostasis, triggering p38 MAPK → p53 phosphorylation → synaptic stripping.

### 8. PLS3-CORO1C actin endocytosis failure (conf=0.82, 16 claims)
SMN deficiency impairs F-actin polymerization at motor nerve terminals by reducing PLS3-mediated actin bundling and CORO1C-dependent actin nucleation, collapsing the actin cytoskeleton required for clathrin-mediated and fluid-phase endocytosis, leading to synaptic vesicle recycling failure.

### 9. pNF-H biomarker of axonal integrity (conf=0.82, 14 claims)
Neurofilament heavy chain (pNF-H) and NfL accumulation in biofluids reflects SMN deficiency-driven impairment of axonal cytoskeletal integrity and neurofilament transport.

### 10. p38a MAPK dual mechanism (conf=0.78, 34 claims)
SMN deficiency leads to hyperactivation of p38a MAPK (MAPK14), driving motor neuron degeneration through: (1) destabilization of synaptic AMPA receptor composition promoting excitotoxic calcium influx, and (2) suppression of neurotrophic MEK/ERK survival signaling.

### 11. Myostatin / ActRIIB pathway (conf=0.78, 29 claims)
Myostatin (GDF8) drives progressive skeletal muscle atrophy through hyperactivation of ActRIIB/ALK4-5-SMAD2/3 signaling in denervated muscle fibers. Selective inhibition by apitegromab rescues muscle mass independently of SMN restoration.

### 12. ERK1/2 vs p38 balance (conf=0.78, 28 claims)
Compensatory hyper-activation of ERK1/2 in SMN-deficient motor neurons is survival-promoting; concurrent pathological p38 MAPK activation drives TNF-a-mediated atrophy. Selective p38 inhibition without disrupting ERK1/2 is the optimal strategy.

### 13. p38 MAPKa + MW150 combination (conf=0.78, 28 claims)
Chronic p38 MAPKa hyperactivation drives SMN-independent axonal degeneration. MW150 inhibition synergizes with SMN-restoring therapies (nusinersen/risdiplam) to rescue motor neurons beyond what SMN restoration alone achieves.

### 14. Neurofilament axonal transport rescue (conf=0.78, 13 claims)
Aberrant NF-H phosphorylation and impaired axonal transport cause pathological accumulation within degenerating motor neuron axons. Nusinersen rescues axonal transport fidelity and reduces neurofilament accumulation.

### 15. ZPR1 → snRNP biogenesis (conf=0.78, 8 claims)
ZPR1 downregulation impairs cytoplasmic snRNP biogenesis by reducing SMN-ZPR1 complex-mediated Sm protein delivery, disrupting spliceosomal assembly distinct from but synergistic with primary SMN loss.

### 16. Notch → glial differentiation block (conf=0.78, 8 claims)
Dysregulated Notch signaling maintains glial progenitors in an undifferentiated state, reducing myelination and trophic support to motor neurons.

### 17. FST:MSTN ratio as severity predictor (conf=0.78, 7 claims)
Follistatin upregulation following denervation suppresses myostatin-mediated atrophy. The FST:MSTN ratio determines residual muscle mass preservation and inversely predicts motor severity.

### 18. IGF-1/PI3K-Akt at axonal growth cones (conf=0.76, 32 claims)
SMN deficiency impairs IGF-1/PI3K-Akt signaling by reducing ribosomal biogenesis and local translation of IGF-1R mRNA at axonal growth cones, tipping the Bcl-xL/Bax ratio toward apoptosis.

### 19. HDAC inhibition dual rescue (conf=0.76, 26 claims)
HDAC inhibition rescues by epigenetically derepressing SMN2 exon 7 inclusion AND simultaneously suppressing the intrinsic apoptotic cascade via Bcl-2/Bax rebalancing and JNK/cytochrome-c suppression.

### 20. p53 via impaired MDM2 splicing (conf=0.74, 52 claims)
SMN deficiency causes nuclear p53 accumulation through impaired MDM2 mRNA splicing (via disrupted SMN-DDX20 snRNP complex), activating pro-apoptotic and pro-inflammatory programs independent of canonical DNA damage.

---

## Novel Target Highlights

| Target | Claims | Confidence | Key Mechanism |
|--------|--------|------------|---------------|
| SETX (Senataxin) | 20 | 0.82 | R-loop accumulation → DNA breaks in MNs |
| BCL2L1 (Bcl-xL) | 24 | 0.82 | Pro-apoptotic Bcl-xL:Bax shift |
| TARDBP (TDP-43) | 37 | 0.72 | HK1 glycolytic flux → energy deficit |
| MTOR_PATHWAY | 56 | 0.62 | Staufen1 → PI3K/AKT/mTOR suppression |
| HTRA2/Omi | 26 | 0.62 | UPR-driven apoptosis suppression |
| SARM1 | 8 | 0.62 | NAD+ depletion → Wallerian degeneration |
| UBA1 | 6 | 0.62 | Ubiquitin pathway dysfunction |
| CHRNA1 | 2 | 0.52 | AChR subunit switching at NMJ |

## Pathway Hypotheses

| Pathway | Claims | Confidence | Mechanism |
|---------|--------|------------|-----------|
| MAPK_PATHWAY | 28 | 0.78 | ERK1/2 compensatory vs p38 pathological |
| HDAC_PATHWAY | 26 | 0.76 | Epigenetic SMN2 derepression + Bcl-2 |
| NOTCH_PATHWAY | 8 | 0.78 | Glial differentiation block |
| JNK_PATHWAY | 27 | 0.62 | Stress response impairment |
| WNT_PATHWAY | 8 | 0.52 | Wnt/beta-catenin suppression in MNs |

## Drug/Therapeutic Hypotheses

| Drug/Target | Claims | Confidence | Mechanism |
|-------------|--------|------------|-----------|
| Apitegromab | 48 | 0.82 | Latent myostatin blockade |
| ROCK inhibitors | 29 | 0.82 | Actomyosin/NMJ rescue |
| 4-AP | 25 | 0.74 | Kv channel block → neurotransmitter release |
| VPA (Valproic acid) | 28 | 0.72 | HDAC inhibition → SMN2 derepression |
| MW150 (p38 inhibitor) | 28 | 0.78 | Synergy with SMN-restoring therapies |
| Growth hormone | 81 | 0.52 | IGF-1R/Akt → SMN2 exon 7 inclusion |

---

## Database State After Run

```
Total hypotheses:  1,472
Total claims:      14,187
Total targets:     ~50
Convergence agent: 238 hypotheses (including prior runs)
```

## Errors During Generation
- 3x JSON parse failures (empty or truncated LLM response)
- 2x Anthropic API 529 "Overloaded" errors
- All 5 errors gracefully handled with fallback template hypotheses
