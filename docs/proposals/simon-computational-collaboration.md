# Computational Collaboration Proposal for Simon CM
# Extending Proprioceptive Synaptic Dysfunction in SMA

> **For**: Christian Simon, Carl-Ludwig-Institute, Leipzig
> **From**: SMA Research Platform (Christian Fischer / Bryzant Labs)
> **Date**: 2026-03-21
> **Reference**: Simon CM et al., Brain 2025 (PMID 39982868)

---

## What We Can Offer

The SMA Research Platform provides computational analysis capabilities that could
extend your proprioceptive synaptic dysfunction findings. We have 30,800 evidence
claims from 6,240 sources, cross-paper synthesis, and GPU compute access.

## Proposed Analyses (5 concrete deliverables)

### 1. Proprioceptive Gene Signature Mining from Public RNA-seq
**Effort**: 2-3 weeks | **Cost**: $0 (public data + existing compute)

Re-analyze GSE87281 (n=101, spinal cord) with focus on proprioceptive markers:
- GSEA for Ia afferent / proprioceptive gene sets (Piezo2, EphA4, Ret, Pvalb)
- WGCNA to find co-expression modules correlating with proprioceptive dysfunction
- Differential expression filtered to DRG neuron / proprioceptor-enriched genes
- Compare with GSE69175 (iPSC-MN) for cross-model consistency

**Deliverable**: List of dysregulated proprioceptive-associated genes in SMA,
ranked by significance and biological coherence.

### 2. Cross-Paper Synthesis: Proprioception × Actin Pathway
**Effort**: 1 week | **Cost**: $0

Our platform's cross-paper synthesis engine can find non-obvious connections between
proprioceptive synapse biology and the actin cytoskeleton pathway:
- Transitive bridges: Gene A mentioned in proprioception paper + Gene A mentioned
  in actin dynamics paper → potential mechanistic connection
- Co-occurrence: Which targets appear in BOTH proprioception AND actin literature?
- Evidence convergence: Where do multiple independent papers point to the same
  proprioceptive-actin connection?

**Deliverable**: Network diagram of proprioception-actin pathway connections with
supporting evidence from 30,800 claims.

### 3. Axonal Transport Vulnerability Model
**Effort**: 3-4 weeks | **Cost**: ~$50 GPU compute

Test the "Translational Desert" hypothesis computationally:
- Model axonal transport with actin-cofilin rod obstruction
- Parameters: axon length, motor protein speed, rod formation rate
- Prediction: longer axons (Ia afferents) are more vulnerable to rod-induced
  transport blockade than shorter axons (local interneurons)
- This could explain WHY proprioceptive synapses fail first

**Deliverable**: Computational model predicting synapse vulnerability based on
axon length × rod density. Testable prediction for your experimental system.

### 4. Single-Cell RNA-seq Proprioceptive Subtype Analysis
**Effort**: 3-4 weeks | **Cost**: $0 (public data)

If suitable scRNA-seq datasets exist from SMA spinal cord:
- Identify proprioceptive neuron clusters using Pvalb, Piezo2, EphA4 markers
- Compare gene expression in proprioceptive vs other neurons in SMA vs control
- Identify which proprioceptive subtypes are most vulnerable
- Look for actin/cofilin pathway genes specifically in vulnerable subtypes

**Deliverable**: Cell-type-resolved gene expression changes in SMA proprioceptive
neurons. Figure-ready for a manuscript.

### 5. Fasudil × Proprioception Hypothesis
**Effort**: Literature synthesis (1 week) + wet lab experiment (7-12 weeks)

Novel hypothesis: ROCK inhibition (Fasudil) clears actin-cofilin rods →
restores mRNA transport → improves proprioceptive synapse function.

Your system could test this:
- SMA motor neuron cultures (your expertise)
- Fasudil treatment (10-30 µM, 72h)
- Measure: proprioceptive synapse markers, p-cofilin, actin rods
- Compare with your existing proprioceptive dysfunction readouts

**Deliverable**: First evidence that ROCK inhibition affects proprioceptive
synapse function in SMA. Potentially high-impact paper.

---

## What We Need From You

1. **Guidance**: Which of these 5 analyses would be most useful for your research?
2. **Data**: Any unpublished scRNA-seq or proprioceptive marker datasets?
3. **Validation**: Can your experimental system test our computational predictions?
4. **Connection**: Introduction to Capogrosso (SCS) or Mentis (circuit) if relevant
5. **Feedback**: What would make this platform genuinely useful for your daily work?

## Platform Access

- **Web**: https://sma-research.info (21 research directions, 58 targets)
- **API**: https://sma-research.info/api/v2/docs
- **MCP**: Natural language queries via Claude Desktop
- **GitHub**: https://github.com/Bryzant-Labs/sma-platform
- **Your papers**: Already ingested (6 papers, PMID 39982868 + 5 others)
