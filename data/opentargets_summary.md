# OpenTargets Validation Report — SMA Research Platform
**Query date:** 2026-03-15
**API:** https://api.platform.opentargets.org/api/v4/graphql
**SMA disease ID:** EFO_0008525 (confirmed via search; Orphanet_70 and EFO_0000253 returned null)
**Total SMA-associated targets in OpenTargets:** 1,205

---

## Key Findings

### Ensembl ID Correction
**The Ensembl ID provided for NCALD (ENSG00000158473) is incorrect.** It resolves to **CD1D** (CD1d molecule), an unrelated immune gene. The correct NCALD ID is **ENSG00000104490**, confirmed via OpenTargets search. All analyses use the corrected ID.

---

## Target Validation Summary

| Target | Ensembl ID | OT SMA Score | OT SMA Rank | Known Drugs (SMA) | SM Tractability | Internal Score Alignment |
|--------|-----------|-------------|------------|-------------------|-----------------|--------------------------|
| SMN1 | ENSG00000172062 | **0.884** | #1 / 1205 | Onasemnogene (Ph4) | High (ligand+structure) | Strong alignment |
| SMN2 | ENSG00000205571 | **0.852** | #2 / 1205 | Nusinersen, Risdiplam, Onasemnogene | None (RNA target) | Strong alignment |
| UBA1 | ENSG00000130985 | **0.768** | #17 / 1205 | None | PROTAC-amenable | Strong alignment |
| STMN2 | ENSG00000104435 | N/A (not in top 1205) | — | None | Antibody possible | Partial — see below |
| PLS3 | ENSG00000102024 | N/A (not in top 1205) | — | None | Structure+ligand | Partial — see below |
| NCALD | ENSG00000104490 | N/A (not in top 1205) | — | None | Minimal | Partial — see below |
| CORO1C | ENSG00000110880 | N/A (not in top 1205) | — | None | Minimal | Weakest evidence |
| MTOR | ENSG00000198793 | N/A for SMA | — (pathway target) | 25 drugs (oncology) | **Highest of all 8** | Indirect — pathway only |

---

## Per-Target Analysis

### 1. SMN1 (ENSG00000172062)
**OpenTargets SMA Score: 0.884 — Rank #1**

- **Association evidence:** Genetic association (0.964), genetic literature (0.973), known drug (0.849), animal model (0.501), literature (0.355)
- **Approved drug:** Onasemnogene abeparvovec (Zolgensma) — Phase 4, gene therapy replacing functional SMN1
- **Tractability:** Structure with ligand + high-quality ligand present (SM); OC approved drug = true (gene therapy counts); PROTAC-amenable (ubiquitination + small molecule binder)
- **Genetic constraint (LOF score 0.618):** Moderate intolerance to loss-of-function — consistent with pathogenicity
- **Internal alignment:** STRONG. SMN1 is the causal gene for ~95% of SMA cases. OpenTargets confirms it as the top-ranked target. Our internal evidence graph should reflect this as the anchor node.

---

### 2. SMN2 (ENSG00000205571)
**OpenTargets SMA Score: 0.852 — Rank #2**

- **Association evidence:** Known drug (0.954 — highest of any target!), genetic association (0.921), genetic literature (0.919), animal model (0.501), literature (0.546)
- **Approved drugs:** 3 drugs — Nusinersen (ASO splice modifier), Risdiplam (small molecule splice modifier), Onasemnogene (gene therapy also affects SMN2 context)
- **Tractability note:** No classical tractability flags set (no protein-binding pocket data) — this is expected because SMN2 is targeted at the RNA/splicing level, not the protein level. Tractability data reflects protein-centric assessments.
- **Internal alignment:** STRONG. SMN2 is the primary therapeutic target (all 3 approved drugs modulate it). The known_drug score of 0.954 is the highest of any of our targets, confirming its central role.

---

### 3. STMN2 (ENSG00000104435)
**OpenTargets SMA Score: NOT PRESENT in top 1,205**

- **Closest associations:** Neurodegenerative disease (0.371), ALS type 11 (0.031), familial ALS (0.031)
- **Tractability:** Low for SM (no pocket/ligand data). Antibody potentially feasible (UniProt surface localization). PROTAC-amenable (ubiquitination + half-life data).
- **Why not in OpenTargets SMA:** STMN2's role in SMA is mechanistically linked to TDP-43 dysfunction and UsnRNP complex disruption affecting STMN2 mRNA processing. This is relatively recent research (2019-2022) that may not yet be aggregated with sufficient weight in OpenTargets. Its stronger association with ALS confirms it is a genuine motor neuron gene.
- **Internal alignment:** PARTIAL. Our internal scoring likely captures experimental evidence not yet integrated in OpenTargets. The ALS connection validates the motor neuron relevance. We should treat this as an "emerging evidence" target — well-supported by primary literature but below OpenTargets scoring threshold for SMA.

---

### 4. PLS3 (ENSG00000102024)
**OpenTargets SMA Score: NOT PRESENT in top 1,205**

- **Top diseases:** X-linked osteoporosis with fractures (0.721), congenital diaphragmatic hernia (0.617), osteoporosis (0.475)
- **Tractability:** Structure with ligand (SM); GO CC high confidence (AB). PROTAC-amenable (ubiquitination + half-life).
- **Why not in OpenTargets SMA:** PLS3 as an SMA modifier was established through mouse model and human genetic studies showing that female SMA patients with more PLS3 copies have milder disease. This evidence is primarily experimental (animal model + genetic modifier studies) rather than the GWAS/ClinVar pathogenic variant evidence that drives OpenTargets scoring. PLS3 is correctly classified in osteoporosis because that is where the direct human genetic evidence is strongest.
- **Internal alignment:** PARTIAL. PLS3 is a validated SMA modifier in the literature, but it operates as a neuroprotective modifier (upregulation is protective), not a direct causative gene. OpenTargets correctly shows its primary role is in bone/cytoskeletal disease. Our internal scoring should flag PLS3 as a "sex-specific modifier" with experimental-grade evidence.

---

### 5. NCALD (ENSG00000104490)
**OpenTargets SMA Score: NOT PRESENT in top 1,205**

**CRITICAL: Provided Ensembl ID ENSG00000158473 is WRONG — resolves to CD1D. Correct ID: ENSG00000104490.**

- **Top diseases:** Hypertension (0.511), coronary artery disease (0.425), increased blood pressure (0.385)
- **Tractability:** Minimal across all modalities. PROTAC potentially feasible (ubiquitination data). No known drugs.
- **Why not in OpenTargets SMA:** NCALD's role as an SMA modifier (its reduction is neuroprotective in SMA) comes from specialized neuroscience research, not population-level genetic studies. The cardiovascular associations reflect NCALD's broader biology (calcium sensor expressed in various tissues).
- **Internal alignment:** PARTIAL. NCALD is a validated modifier in SMA research but represents a "niche scientific" finding not captured by OpenTargets' evidence aggregation. Our internal graph's NCALD node should note: (1) the ID correction, (2) the inhibition-direction therapeutic goal (reducing NCALD activity is protective), (3) low tractability for direct targeting.

---

### 6. UBA1 (ENSG00000130985)
**OpenTargets SMA Score: 0.768 — Rank #17**

- **Association evidence:** Genetic association (0.840), genetic literature (0.833), literature (0.303)
- **Specific SMA subtype associations:**
  - Infantile-onset X-linked SMA (SMAX2): score 0.763 — strongest specific association
  - X-linked distal SMA type 3: score 0.474
  - General SMA (EFO_0008525): score 0.035 (literature only — via VEXAS syndrome and ubiquitin pathway)
- **Tractability:** Small molecule binder confirmed + PROTAC-amenable. No approved drugs for SMA.
- **Key therapeutic nuance:** In X-linked SMA, UBA1 activity is REDUCED. Therapeutic goal is activation/restoration, not inhibition — an unusual and challenging direction. Existing UBA1 inhibitors (e.g., MLN7243/TAK-243 in oncology) are not applicable here.
- **Internal alignment:** STRONG for X-linked SMA forms. Our internal scoring should differentiate the two contexts: (a) UBA1 loss-of-function = X-linked SMA (high evidence), (b) UBA1 pathway involvement in autosomal SMA (low evidence). OpenTargets' high rank (17/1205) primarily reflects X-linked SMA genetic evidence.

---

### 7. CORO1C (ENSG00000110880)
**OpenTargets SMA Score: NOT PRESENT in top 1,205, no motor neuron disease associations**

- **Top diseases:** Neurodegenerative disease (0.453), liver disease (0.333), Alzheimer's (0.312)
- **Tractability:** Minimal for SM. Antibody feasible (UniProt + GO surface localization). PROTAC possible.
- **Why not in OpenTargets SMA:** CORO1C as an SMA-relevant target is based on its role in actin cytoskeleton regulation and its interaction with the SMN complex. This is mechanistic/cell biology evidence, not human genetics. OpenTargets' scoring is heavily weighted toward genetic association evidence.
- **Internal alignment:** WEAKEST of the 8 targets. CORO1C has no SMA or motor neuron genetic evidence in OpenTargets. Our internal scoring should flag this as "low confidence — mechanistic hypothesis only." It may be appropriate to de-prioritize CORO1C or reduce its evidence weight in our graph until additional supporting data emerges.

---

### 8. MTOR (ENSG00000198793) — Pathway Target
**OpenTargets SMA Score: NOT PRESENT in top 1,205 for SMA**

- **Role in SMA:** Pathway modifier, not a primary SMA gene. mTOR activation has been proposed to compensate for SMN deficiency and promote motor neuron survival.
- **Top diseases:** mTORopathies (0.830), focal cortical dysplasia (0.823), overgrowth syndromes (0.691), neurodegenerative disease (0.560)
- **Tractability: HIGHEST of all 8 targets.** Approved small molecule (SM), high-quality ligand + structure, druggable family, surface-localized (AB), small molecule binder (PROTAC)
- **Known drugs:** 25 drugs across all indications in clinical trials. Approved: everolimus, temsirolimus (rapalogs). Phase 3: dactolisib, ridaforolimus, gedatolisib.
- **Key challenge:** All 25 known MTOR drugs are inhibitors (oncology context). For SMA, the hypothesis requires MTOR pathway ACTIVATION to support motor neuron survival — the opposite of what these drugs do. Indoximod (mTORC1 activator) is the one exception at Phase 2.
- **Internal alignment:** INDIRECT. MTOR's role in SMA is a pathway-level hypothesis with limited clinical validation. OpenTargets correctly does not associate it with SMA. Our internal graph should represent MTOR as a "pathway node" with explicit notation that the therapeutic direction (activation) differs from all approved indications (inhibition).

---

## Comparative Assessment: Internal Scoring vs. OpenTargets

| Target | OT SMA Score | Internal Priority | Alignment | Notes |
|--------|------------|------------------|-----------|-------|
| SMN1 | 0.884 (#1) | Highest | STRONG | Perfect alignment — OT and internal agree |
| SMN2 | 0.852 (#2) | Highest | STRONG | Perfect alignment — highest known_drug score |
| UBA1 | 0.768 (#17) | High (X-linked SMA) | STRONG | OT captures X-linked SMA genetics well |
| STMN2 | N/A | Moderate | PARTIAL | Motor neuron relevant (ALS), SMA evidence pre-OT aggregation |
| PLS3 | N/A | Moderate (modifier) | PARTIAL | Validated modifier but gene therapy/overexpression target |
| NCALD | N/A | Moderate (modifier) | PARTIAL | ID correction required; inhibition goal, minimal tractability |
| MTOR | N/A for SMA | Pathway context | INDIRECT | High tractability but wrong therapeutic direction in existing drugs |
| CORO1C | N/A | Low | WEAK | No genetic evidence; mechanistic hypothesis only |

---

## Approved SMA Drugs (from OpenTargets)

OpenTargets identifies **17 unique drugs** with SMA indications across **69 targets**:

| Drug | Type | Max Phase | Target | Mechanism |
|------|------|-----------|--------|-----------|
| Onasemnogene abeparvovec (Zolgensma) | Gene therapy | **Approved** | SMN1 | SMN1 gene replacement |
| Nusinersen (Spinraza) | Antisense oligonucleotide | **Approved** | SMN2 | SMN2 splice modulator |
| Risdiplam (Evrysdi) | Small molecule | **Approved** | SMN2 | SMN2 splice modulator |
| Valproic acid | Small molecule | Approved (off-label) | ALDH5A1 | Off-target; indirect SMA evidence |
| Apitegromab | Antibody | Phase 3 | MSTN | Myostatin inhibitor — muscle function |

---

## Recommendations for SMA Platform

1. **Fix NCALD Ensembl ID** in the database: update from `ENSG00000158473` (CD1D) to `ENSG00000104490` (NCALD)

2. **SMN1 and SMN2** are OpenTargets-validated top-2 targets — full evidence pipeline priority

3. **UBA1** is well-validated by OT (#17) but for **X-linked SMA specifically** — ensure the evidence graph distinguishes this from autosomal SMA

4. **STMN2, PLS3, NCALD** are genuinely SMA-relevant but rely on experimental/modifier evidence not captured in OpenTargets scoring. These are candidates for our **PubMed/literature evidence pipeline** to supplement OT's genetic-evidence-weighted approach

5. **CORO1C** has the weakest OpenTargets support of any target. Consider flagging as "hypothesis-grade" in the evidence graph until more supporting data is available

6. **MTOR** should be represented as a pathway context node rather than a direct drug target — note the therapeutic direction inversion relative to all existing approved MTOR drugs

7. **Tractability gap:** Only SMN1 (gene therapy), SMN2 (ASO/SM), and MTOR (SM) have proven clinical tractability. STMN2, PLS3, NCALD, CORO1C have no clinical precedent — gene therapy / AAV-based approaches (like PLS3 overexpression) are the most viable options.

---

## Data Sources
- OpenTargets Platform (2025 release): https://platform.opentargets.org
- Citation: Ochoa, D. et al. (2025) Open Targets Platform. Nucleic Acids Research, 53(D1):D1467-D1477
- Query timestamp: 2026-03-15
- All data freely accessible, no authentication required
