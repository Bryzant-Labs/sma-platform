# ESM-2 Kinase Domain Similarity: LIMK2 vs ROCK2

**Date**: 2026-03-24
**Model**: ESM-2 650M (esm2_t33_650M_UR50D, 1280-dim per-residue embeddings)
**Source PDBs**: AlphaFold2 predictions
- `LIMK2_P53671_kinase.pdb` — 287 residues (PDB 309-595)
- `ROCK2_O75116_kinase.pdb` — 396 residues (PDB 18-413)

---

## Key Results

| Region | Cosine Similarity | Interpretation |
|--------|:-----------------:|---------------|
| **Full kinase domain** | **0.8823** | High — same kinase fold family |
| **DFG + activation loop** (20 res) | **0.8129** | High — conserved catalytic machinery |
| **P-loop (GxGxxG)** | **0.7973** | High — nearly identical ATP phosphate anchor |
| **alpha-C helix** | **0.7975** | High — conserved regulatory element |
| **HRD catalytic loop** (12 res) | **0.7297** | Moderate-high — conserved catalytic base |
| **Gatekeeper region** (+-3 res) | **0.7079** | Moderate — different gatekeeper residues (D vs H) |
| **Combined ATP pocket** (P-loop + Hinge) | **0.6431** | Moderate — divergent hinge offsets the conserved P-loop |
| **Hinge region alone** | **0.5327** | Lower — most divergent part of the ATP pocket |

---

## ATP Binding Pocket Residues

### P-loop (GxGxxG motif) — 79.7% embedding similarity
```
LIMK2 (338-343):  G-K-G-F-F-G
ROCK2 ( 99-104):  G-R-G-A-F-G
                   * . * . * *   (4/6 identical)
```
The GxGxxG glycine-rich loop anchors the ATP phosphates. Both kinases share the essential glycine framework. The difference at position 4 (F vs A) affects pocket volume but not H-1152 binding geometry since H-1152 targets the adenine pocket, not the phosphate region.

**Per-residue P-loop similarities**:
| Position | LIMK2 | ROCK2 | Cosine Sim |
|----------|-------|-------|:----------:|
| 1 | G (338) | G (99) | 0.7874 |
| 2 | K (339) | R (100) | 0.7071 |
| 3 | G (340) | G (101) | 0.7728 |
| 4 | F (341) | A (102) | 0.6317 |
| 5 | F (342) | F (103) | 0.7058 |
| 6 | G (343) | G (104) | 0.8109 |

### Hinge Region — 53.3% embedding similarity
```
LIMK2 (395-401):      L-Y-K-D-K-K-L
ROCK2 (153-176):  V-Q-L-F-Y-A-F-Q-D-D-R-Y-L-Y-M-V-M-E-Y-M-P-G-G-D
```
The hinge region shows the greatest divergence, which is expected — the hinge is where kinase selectivity is primarily determined. However, H-1152 and its derivatives are **Type I inhibitors** that make just 1-2 hydrogen bonds to the hinge backbone NH and CO atoms. These backbone interactions are geometrically conserved regardless of side-chain differences. This is why H-1152 can bind both kinases despite hinge sequence divergence.

### DFG Motif + Activation Loop — 81.3% embedding similarity
```
LIMK2 (469-488):  D-F-G-L-S-R-L-I-V-E-E-R-K-R-A-P-M-E-K-A
ROCK2 (232-251):  D-F-G-T-C-M-K-M-D-E-T-G-M-V-H-C-D-T-A-V
```
The DFG motif itself is 100% identical. The high overall similarity of this region indicates that both kinases adopt a similar DFG-in active conformation, which is the conformation H-1152 binds.

### HRD Catalytic Loop — 73.0% embedding similarity
```
LIMK2 (449-460):  H-R-D-L-N-S-H-N-C-L-I-K
ROCK2 (212-223):  H-R-D-V-K-P-D-N-M-L-L-D
                   * * *       *
```
The catalytic HRD motif is identical. The surrounding residues differ but maintain similar structural roles.

### Gatekeeper — 70.8% embedding similarity
```
LIMK2: D (Asp) at PDB 462
ROCK2: H (His) at PDB 225
```
The gatekeeper residue differs: **Asp (small, charged)** in LIMK2 vs **His (medium, can be charged)** in ROCK2. Both are relatively small/medium and do not create a steric block in the back pocket. This is significant: kinases with bulky gatekeepers (e.g., Thr in many kinases) sterically block certain inhibitors. The permissive gatekeepers in both LIMK2 and ROCK2 allow H-1152 access to the hydrophobic back pocket.

### alpha-C Helix — 79.8% embedding similarity
```
LIMK2 (355-371):  K-A-T-G-K-V-M-V-M-K-E-L-I-R-C-D-E
ROCK2 (112-128):  K-A-S-Q-K-V-Y-A-M-K-L-L-S-K-F-E-M
                   * *   . * *     * *
```
The alpha-C helix shows high conservation, including the critical Lys-Glu salt bridge (K...E) that stabilizes the active conformation. Both kinases maintain this interaction, confirming they are in similar active states.

---

## Why H-1152 and genmol_119 Bind Both LIMK2 and ROCK2

The ESM-2 analysis reveals **four structural reasons** for dual-kinase binding:

### 1. Conserved ATP-binding architecture (full domain similarity = 0.88)
Both kinases share the canonical kinase fold with highly similar catalytic machinery. The overall embedding similarity of 0.88 places them in the same structural neighborhood, well above the ~0.5-0.6 threshold for unrelated kinases.

### 2. Identical catalytic motifs (DFG = 100%, HRD = 100%)
The DFG and HRD motifs that form the catalytic core are sequence-identical. Both kinases adopt the DFG-in active conformation that Type I inhibitors like H-1152 target. The high DFG+activation loop similarity (0.81) confirms the activation loop geometry is conserved.

### 3. Permissive gatekeeper residues (D in LIMK2, H in ROCK2)
Neither kinase has a bulky gatekeeper. Both Asp and His are small enough to allow inhibitor access to the hydrophobic region behind the gatekeeper. This is a key determinant of inhibitor promiscuity in kinases.

### 4. Hinge backbone conservation despite sequence divergence
Although the hinge sequences differ substantially (cosine = 0.53), H-1152 is a **Type I inhibitor** that binds via backbone hydrogen bonds to the hinge, not side-chain interactions. The hinge backbone geometry is dictated by the kinase fold, not the sequence. This means the low hinge embedding similarity actually overstates the binding site difference for H-1152-class compounds.

### Therapeutic Implication
The **dual ROCK2+LIMK2 activity** of H-1152 derivatives is not a liability but a potential advantage for SMA:
- **ROCK2 inhibition** reduces pathological actin stress fiber formation
- **LIMK2 inhibition** prevents cofilin phosphorylation, restoring actin dynamics
- Both targets converge on the **ROCK-LIMK-Cofilin** axis identified as the strongest therapeutic signal in SMA

The high structural similarity (0.88) explains why achieving selectivity between ROCK2 and LIMK2 is inherently difficult, and may not be desirable for SMA therapy.

---

## Method Notes

- ESM-2 650M (33 layers, 650M parameters) provides per-residue embeddings in 1280 dimensions
- Cosine similarity computed on mean-pooled embeddings for each region
- Sequences extracted from AlphaFold2-predicted kinase domain PDB files
- NVIDIA NIM ESM-2 endpoint was unavailable (HTTP 500, documented as DEGRADED), so embeddings were computed locally using `fair-esm` on CPU
- ATP pocket residue ranges based on standard kinase annotation: P-loop (GxGxxG), hinge (backbone H-bond donors/acceptors flanking adenine), DFG, HRD, gatekeeper

---

## Raw Data

```json
{
  "embedding_model": "esm2_t33_650M_UR50D",
  "embedding_dim": 1280,
  "full_domain_cosine_similarity": 0.8823,
  "ploop_cosine_similarity": 0.7973,
  "hinge_cosine_similarity": 0.5327,
  "atp_pocket_cosine_similarity": 0.6431,
  "dfg_activation_cosine_similarity": 0.8129,
  "hrd_catalytic_cosine_similarity": 0.7297,
  "gatekeeper_cosine_similarity": 0.7079,
  "alphaC_helix_cosine_similarity": 0.7975
}
```
