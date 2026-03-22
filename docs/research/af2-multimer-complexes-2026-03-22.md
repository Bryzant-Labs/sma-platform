# AlphaFold2-Multimer Complex Structure Predictions for SMA

**Date**: 2026-03-22
**Platform**: SMA Research Platform (`/api/v2/nims/alphafold2-multimer`)
**Server**: moltbot (217.154.10.79)

---

## Executive Summary

Attempted AF2-Multimer NIM predictions for 6 key SMA-related protein complexes. **The NVIDIA API key returned 403 Forbidden** on all BioNeMo NIM endpoints (DiffDock, AlphaFold2, AlphaFold2-Multimer, ESMfold, RFdiffusion). The key needs to be re-generated at [build.nvidia.com](https://build.nvidia.com) with each NIM individually activated.

**Fallback**: Downloaded experimental PDB structures (where available) and AlphaFold v6 single-chain structures for all 11 proteins. Performed interface residue analysis on all experimental complexes.

### Key Findings

| Complex | Experimental PDB | AF2-Multimer Needed? | Interface Hotspots |
|---------|-----------------|---------------------|-------------------|
| SMN + PFN1 | **None** (co-IP only, PMID:21920940) | **YES - HIGH PRIORITY** | Unknown |
| SMN + Gemin2 | 5XJL (cryo-EM) | Low priority | Chain 2-A: 11+16 residues |
| ROCK2 + LIMK1 | **None** (functional only) | **YES - HIGH PRIORITY** | Unknown |
| LIMK1 + CFL2 | 5HVK, 5L6W (crystal) | Low priority | A:19 + B:17 residues |
| C1QA+C1QB+C1QC | 1PK6 (crystal) | Low priority | A:28, B:25, C:31 residues |
| MDM2 + TP53 | 1YCR (crystal, classic) | Low priority | A:24 + B:11 residues |

**Two complexes (SMN+PFN1 and ROCK2+LIMK1) have NO experimental structures and are the highest-priority targets for AF2-Multimer prediction.**

---

## NVIDIA API Key Issue

```
POST https://health.api.nvidia.com/v1/biology/deepmind/alphafold2-multimer
-> 403 Forbidden: "Authorization failed"
```

The current NVIDIA API key (`nvapi-wEj_...`) does not have access to BioNeMo NIMs. All biology endpoints return 403:
- DiffDock: 403
- AlphaFold2: 403
- AlphaFold2-Multimer: 403
- ESMfold: 403
- RFdiffusion: 403
- GenMol: 404

### Fix Required
1. Go to [build.nvidia.com](https://build.nvidia.com)
2. Navigate to each NIM endpoint page (AlphaFold2-Multimer, DiffDock, etc.)
3. Click "Get API Key" or "Try it" to activate access
4. Generate a new API key with BioNeMo permissions
5. Update `NVIDIA_API_KEY` in `~/.bashrc` on moltbot and restart sma-api

---

## Protein Sequences (from UniProt)

All sequences fetched and saved to `/home/bryzant/sma-platform/data/af2_multimer_complexes/sequences.json`

| Protein | UniProt | Length | Gene |
|---------|---------|--------|------|
| SMN1 | Q16637 | 294 aa | SMN1 |
| PFN1 (Profilin-1) | P07737 | 140 aa | PFN1 |
| Gemin2 | O14893 | 280 aa | GEMIN2 |
| ROCK2 | O75116 | 1388 aa | ROCK2 |
| LIMK1 | P53667 | 647 aa | LIMK1 |
| CFL2 (Cofilin-2) | Q9Y281 | 166 aa | CFL2 |
| C1QA | P02745 | 245 aa | C1QA |
| C1QB | P02746 | 253 aa | C1QB |
| C1QC | P02747 | 245 aa | C1QC |
| MDM2 | Q00987 | 491 aa | MDM2 |
| TP53 | P04637 | 393 aa | TP53 |

---

## Complex 1: SMN + PFN1 (Profilin-1)

**Status**: NO EXPERIMENTAL STRUCTURE -- AF2-Multimer prediction critical

**Biological relevance**: SMN directly interacts with Profilin (PMID:21920940). This interaction is central to the actin pathway dysfunction in SMA. Profilin binds actin monomers and proline-rich proteins. SMN contains proline-rich regions (residues 195-240) that likely mediate PFN1 binding.

- **SMN**: 294 aa (Q16637) -- largely disordered, Tudor domain (residues 91-151) well-structured
- **PFN1**: 140 aa (P07737) -- compact, well-structured

**AlphaFold v6 single-chain structures**: Downloaded
- `AF_SMN1_Q16637.pdb` (187 KB)
- `AF_PFN1_P07737.pdb` (90 KB)

**Predicted binding interface** (from literature):
- SMN proline-rich region (residues ~195-240) likely contacts PFN1 poly-proline binding groove
- PFN1 residues involved in PLP binding: W3, H133, Y139 (aromatic cradle)

**When AF2-Multimer becomes available**: Submit both full-length sequences. Expected interface at SMN proline-rich region + PFN1 PLP groove.

---

## Complex 2: SMN + Gemin2

**Status**: Experimental structure available (PDB: 5XJL)

**PDB 5XJL**: SMN + Gemin2 complex (cryo-EM/crystal hybrid)

### Chain Assignment
| Chain | Residues | Identity |
|-------|----------|----------|
| 2 | 204 (22-278) | Gemin2 |
| A | 81 (1-81) | SMN (N-terminal) |
| B | 85 (22-117) | SMN (Gemin2-binding domain) |
| E | 77 (14-90) | SMN oligomerization |
| F | 74 (3-76) | SMN |
| G | 63 (8-72) | SmD3 |
| M | 17 (35-51) | peptide |

### Interface Residues (5A cutoff)

**Gemin2(Chain 2) -- SMN(Chain A):**
- Gemin2: 11 residues [22, 187, 188, 189, 223, 224, 225, 226, 227, 228, 273]
- SMN: 16 residues [1, 16, 18, 22, 24, 25, 26, 44, 45, 46, 47, 48, 49, 51, 52, 72]

**Gemin2(Chain 2) -- SMN(Chain B):**
- Gemin2: 24 residues [22, 24, 66, 68, 80-87, 226-232, 235, 239, 271-274]
- SMN: 27 residues [23, 26-28, 43, 50, 61-62, 69, 71-76, 91+]

**Binder design hotspots**: Gemin2 residues 223-228 and SMN residues 44-52 form the core binding interface.

**Files**:
- `5XJL.pdb` (452 KB)
- `AF_GEMIN2_O14893.pdb` (185 KB)

---

## Complex 3: ROCK2 + LIMK1

**Status**: NO EXPERIMENTAL STRUCTURE -- AF2-Multimer prediction critical

**Biological relevance**: ROCK2 phosphorylates LIMK1 at Thr508 in the activation loop, activating LIMK1's kinase activity. This is the key signaling step in the ROCK-LIMK-Cofilin actin pathway that is dysregulated in SMA.

- **ROCK2**: 1388 aa (O75116) -- very large kinase. Kinase domain: residues 71-379
- **LIMK1**: 647 aa (P53667) -- kinase domain: residues 331-631

**Note**: ROCK2+LIMK1 together = 2035 residues. May need truncation for AF2-Multimer (max ~2500 residues). Submit ROCK2 kinase domain (71-379, 309 aa) + LIMK1 kinase domain (331-631, 301 aa) = 610 aa total.

**AlphaFold v6 single-chain structures**: Downloaded
- `AF_ROCK2_O75116.pdb` (926 KB)
- `AF_LIMK1_P53667.pdb` (420 KB)

**Predicted binding interface** (from literature):
- ROCK2 kinase domain substrate-binding cleft
- LIMK1 activation loop around Thr508

**When AF2-Multimer becomes available**: Submit ROCK2(71-379) + LIMK1(331-631) as truncated domains. Interface residues will reveal druggable hotspots for disrupting ROCK2-LIMK1 signaling.

---

## Complex 4: LIMK1 + CFL2 (Cofilin-2)

**Status**: Experimental structures available (PDB: 5HVK, 5L6W)

**PDB 5HVK**: LIMK1 D460N mutant + full-length Cofilin-1 (closest available to CFL2)
**PDB 5L6W**: LIMK1 + ATPgammaS + CFL1

### Interface Residues (5A cutoff, from 5HVK)

**LIMK1(Chain A, kinase domain 324-634) -- Cofilin(Chain B, 2-166):**
- LIMK1: 19 residues [348, 349, 375, 376, 509, 510, 511, 512, 513, 514, 516, 521, 549, 550, 551, 555, 556, 557, 559]
- Cofilin: 17 residues [2, 4, 44, 45, 109, 111, 112, 114, 115, 116, 118, 119, 122, 123, 126, 127, 129]

### Cross-validated with 5L6W

**LIMK1(Chain L) -- Cofilin(Chain C):**
- LIMK1: 18 residues [348, 349, 350, 460, 481, 509, 512, 513, 514, 516, 521, 549, 550, 551, 555, 556, 557, 559]
- Cofilin: 10 residues [2, 3, 111, 112, 114, 115, 116, 118, 119, 122]

### Conserved Interface Core (present in both structures)
- **LIMK1**: 348, 349, 509, 512, 513, 514, 516, 521, 549, 550, 551, 555, 556, 557, 559
- **Cofilin**: 111, 112, 114, 115, 116, 118, 119, 122

**Key hotspot**: LIMK1 residues 509-521 (activation segment) and 549-559 (substrate-binding region) + Cofilin residues 111-127 (includes Ser3 phosphorylation site region).

**Note**: CFL2 (Cofilin-2, Q9Y281, 166 aa) shares ~80% identity with CFL1. The interface should be highly conserved. AF2-Multimer with actual CFL2 sequence would confirm.

**Files**:
- `5HVK.pdb` (663 KB)
- `5L6W.pdb` (327 KB)
- `AF_CFL2_Q9Y281.pdb` (112 KB)

---

## Complex 5: C1QA + C1QB + C1QC (Complement C1q Trimer)

**Status**: Experimental structure available (PDB: 1PK6)

**PDB 1PK6**: Complement C1q globular domain heterotrimeric complex

### Chain Assignment
| Chain | Residues | Identity |
|-------|----------|----------|
| A (C1QA) | 133 (90-222) | Globular head domain |
| B (C1QB) | 132 (92-223) | Globular head domain |
| C (C1QC) | 129 (89-217) | Globular head domain |

### Interface Residues (5A cutoff)

**A-B interface:**
- C1QA: 28 residues [90-96, 98, 100, 115-116, 118, 140, 142, 144, 150, 161-167, 217, 219-220]
- C1QB: 25 residues [140, 142, 159, 167-175, 179, 181-188, 218, 220-223]

**A-C interface:**
- C1QA: 23 residues [136, 138, 140, 150, 164-171, 177, 179-184, 201, 217, 219-220]
- C1QC: 31 residues [89, 91-95, 97, 116-117, 119-120, 139, 141, 143, 145+16 more]

**B-C interface:**
- C1QB: 30 residues [93-98, 100, 119-120, 122, 142, 144, 146, 148, 177+15 more]
- C1QC: 28 residues [137, 139, 141, 143, 151, 160-168, 174+13 more]

**SMA relevance**: Complement pathway activation is implicated in motor neuron degeneration. C1q marks synapses for elimination -- elevated in SMA models. Understanding the trimer interface could guide therapeutic strategies to block complement-mediated NMJ destruction.

**Files**:
- `1PK6.pdb` (307 KB)
- `AF_C1QA_P02745.pdb` (154 KB)
- `AF_C1QB_P02746.pdb` (157 KB)
- `AF_C1QC_P02747.pdb` (153 KB)

---

## Complex 6: MDM2 + TP53

**Status**: Experimental structure available (PDB: 1YCR -- classic structure)

**PDB 1YCR**: MDM2 bound to p53 transactivation domain (Kussie et al., Science 1996)

### Chain Assignment
| Chain | Residues | Identity |
|-------|----------|----------|
| A (MDM2) | 85 (25-109) | N-terminal p53-binding domain |
| B (TP53) | 13 (17-29) | Transactivation domain peptide |

### Interface Residues (5A cutoff)

**MDM2(Chain A) -- p53(Chain B):**
- MDM2: 24 residues [25, 26, 50, 51, 54, 55, 57, 58, 61, 62, 67, 70, 71, 72, 73, 75, 91, 93, 94, 96, 99, 100, 103, 104]
- p53: 11 residues [17, 18, 19, 20, 22, 23, 25, 26, 27, 28, 29]

### Key Hotspot Residues
- **MDM2 deep pocket**: Residues 54, 58, 61, 67, 72, 96, 100 form the hydrophobic cleft
- **p53 anchor residues**: F19, W23, L26 (the classic "FWL triad") insert into the MDM2 pocket
- All MDM2 inhibitors (nutlins, idasanutlin, navtemadlin) target this exact interface

**SMA relevance**: p53 pathway activation contributes to motor neuron death in SMA. MDM2 is the primary negative regulator of p53. Understanding this interface informs potential neuroprotective strategies.

**Files**:
- `1YCR.pdb` (94 KB)
- `AF_MDM2_Q00987.pdb` (320 KB)
- `AF_TP53_P04637.pdb` (254 KB)

---

## Files Inventory (on moltbot)

### Experimental PDB Structures
```
/home/bryzant/sma-platform/data/af2_multimer_complexes/
  5XJL.pdb      (452 KB)  SMN + Gemin2
  5HVK.pdb      (663 KB)  LIMK1 + Cofilin-1
  5L6W.pdb      (327 KB)  LIMK1 + CFL1 + ATPgammaS
  1YCR.pdb       (94 KB)  MDM2 + p53
  1PK6.pdb      (307 KB)  C1q trimer (A+B+C)
  5WSG.pdb    (7,088 KB)  Spliceosome (contains SMN subunits, not SMN-PFN1)
```

### AlphaFold v6 Single-Chain Structures
```
  AF_SMN1_Q16637.pdb    (187 KB)
  AF_PFN1_P07737.pdb     (90 KB)
  AF_GEMIN2_O14893.pdb  (185 KB)
  AF_ROCK2_O75116.pdb   (926 KB)
  AF_LIMK1_P53667.pdb   (420 KB)
  AF_CFL2_Q9Y281.pdb    (112 KB)
  AF_C1QA_P02745.pdb    (154 KB)
  AF_C1QB_P02746.pdb    (157 KB)
  AF_C1QC_P02747.pdb    (153 KB)
  AF_MDM2_Q00987.pdb    (320 KB)
  AF_TP53_P04637.pdb    (254 KB)
```

### Analysis Files
```
  sequences.json           (5 KB)   All UniProt sequences
  interface_analysis.json  (11 KB)  Interface residue data
```

---

## Action Items

### Immediate (API Key Fix)
1. Re-generate NVIDIA API key at [build.nvidia.com](https://build.nvidia.com) with BioNeMo NIM access
2. Activate each NIM individually: AlphaFold2-Multimer, DiffDock, AlphaFold2, ESMfold, RFdiffusion
3. Update key on moltbot: `export NVIDIA_API_KEY=<new-key>` in `~/.bashrc` and restart `pm2 restart sma-api`

### After Key Fix -- Priority AF2-Multimer Predictions
1. **SMN + PFN1** (294 + 140 = 434 residues) -- No experimental structure exists. Critical for actin pathway.
2. **ROCK2(71-379) + LIMK1(331-631)** (309 + 301 = 610 residues) -- No experimental structure. Key kinase cascade.
3. **LIMK1 + CFL2** (647 + 166 = 813 residues) -- Validate against 5HVK/5L6W with actual CFL2 sequence.

### Binder Design Pipeline (after complex structures obtained)
For each AF2-Multimer result:
1. Extract interface residues as hotspots
2. Feed to RFdiffusion (`/api/v2/nims/design-binder`) for de novo binder design
3. Design sequences with ProteinMPNN (`/api/v2/nims/design-sequence`)
4. Validate binding with DiffDock

---

## API Endpoint Reference

```bash
# AF2-Multimer prediction
POST /api/v2/nims/alphafold2-multimer
Header: X-Admin-Key: sma-admin-2026
Body: {
  "sequences": ["<seq1>", "<seq2>"],
  "algorithm": "jackhmmer",
  "relax_prediction": true
}

# Example: SMN + PFN1 (ready to run once API key is fixed)
curl -X POST http://127.0.0.1:8090/api/v2/nims/alphafold2-multimer \
  -H "X-Admin-Key: sma-admin-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "sequences": [
      "MAMSSGGSGGGVPEQEDSVLFRRGTGQSDDSDIWDDTALIKAYDKAVASFKHALKNGDICETSGKPKTTPKRKPAKKNKSQKKNTAASLQQWKVGDKCSAIWSEDGCIYPATIASIDFKRETCVVVYTGYGNREEQNLSDLLSPICEVANNIEQNAQENENESQVSTDESENSRSPGNKSDNIKPKSAPWNSFLPPPPPMPGPRLGPGKPGLKFNGPPPPPPPPPPHLLSCWLPPFPSGPPIIPPPPPICPDSLDDADALGSMLISWYMSGYHTGYYMGFRQNQKEGRCSHSLN",
      "MAGWNAYIDNLMADGTCQDAAIVGYKDSPSVWAAVPGKTFVNITPAEVGVLVGKDRSSSFYVNGLTLGGQKCSVIRDSLLQDGEFSMDLRTKSTGGAPTFNVTVTKTDKTLVLLMGKEGVHGGELINKVCYEMASHLRRSQY"
    ],
    "algorithm": "jackhmmer",
    "relax_prediction": true
  }'
```
