# ROCK2 Protein Binder Design — 2026-03-22

## Pipeline

**RFdiffusion** (backbone generation) -> **ProteinMPNN** (sequence design) -> **ESMfold** (structure validation)

All three steps run via NVIDIA NIM cloud APIs (build.nvidia.com).

## Target

- **Protein**: ROCK2 (Rho-associated protein kinase 2)
- **UniProt**: O75116
- **Structure**: PDB 2F2U — X-ray crystal structure of the ROCK2 kinase domain (chain A, residues 27-417)
- **Rationale**: ROCK2 is a key regulator of actin dynamics in the RhoA-ROCK-LIMK-Cofilin pathway. Inhibiting ROCK2 kinase activity could rescue actin cytoskeletal defects in SMA motor neurons.

## RFdiffusion Parameters

| Parameter | Value |
|-----------|-------|
| Target PDB | 2F2U chain A (ROCK2 kinase domain) |
| Contig specification | `80/0 A27-388` |
| Binder length | 80 residues |
| Number of designs | 5 |
| Avg generation time | ~50 seconds per backbone |

Note: Residues 389-393 are missing from the crystal structure (disordered loop), so the contig avoids that region.

## ProteinMPNN Parameters

| Parameter | Value |
|-----------|-------|
| Input | RFdiffusion backbone (full complex) |
| API format | `{"input_pdb": <pdb_content>}` (minimal — extra params rejected by NVIDIA API) |
| Generation time | ~0.4 seconds per design |

## ESMfold Validation

| Parameter | Value |
|-----------|-------|
| Input | 80-residue binder sequences |
| Endpoint | `nvidia/esmfold` (NOT `/predict` suffix) |
| Generation time | ~1-2 seconds per structure |

## Results (Ranked by pLDDT)

### Design 4 — Best Overall
- **MPNN Score**: 0.7603 (best)
- **ESMfold pLDDT**: 85.0 (range: 68.9-89.8)
- **Sequence** (80 aa):
```
MEKKYEEYLKKKKEELSKAFEELLEEILENIEKLKEVAEELKEKLEELKDKFSEVEIKKMKKAIEETEKLLEKIKKVLEE
```

### Design 5 — Co-Best pLDDT
- **MPNN Score**: 0.7768
- **ESMfold pLDDT**: 85.0 (range: 70.8-91.6)
- **Sequence** (80 aa):
```
MKFEKYEKMLEIFAEEMEEYVEEIKEAFELCKKAIEAAKKLKKEKGNKELLEELIEYIKELKKLSDIIKKVLEKVLKKLE
```

### Design 1
- **MPNN Score**: 0.7986
- **ESMfold pLDDT**: 82.1 (range: 67.0-87.7)
- **Sequence** (80 aa):
```
MEFIEKKVEEFKEEVKDAVKEMIFKNSKEIMEVCERTIEILKEIEKEEELSEEELREREYEREEMEKTMKMIKEIEELLK
```

### Design 2
- **MPNN Score**: 0.7604
- **ESMfold pLDDT**: 81.2 (range: 66.0-88.4)
- **Sequence** (80 aa):
```
TKLEKLKKLEEVLAEEVKDHEDVVKLLIESSKKLKEMKVKVEKDKSFEEEYKEKSIEIAEELKKHLDEILKILKKVVEEN
```

### Design 3 — Lowest Confidence
- **MPNN Score**: 0.7630
- **ESMfold pLDDT**: 71.6 (range: 46.1-84.6)
- **Sequence** (80 aa):
```
DEEYEKIKELAKKGDIKKEEENKAWLPITKKFVLKNIEEFLKVSKKAIKVFKELGRKKSDIEKLEKAEKKYEEILKLKEK
```

## Interpretation

- **pLDDT > 80**: Designs 4, 5, 1, and 2 all have high predicted structural confidence. These binders are predicted to fold into well-defined structures.
- **MPNN Score ~0.76**: Lower is better for ProteinMPNN. All designs score in a similar range, indicating the backbone is designable.
- **Design 4** is the top candidate: best MPNN score (0.7603) AND joint-best pLDDT (85.0).
- **Design 3** has lower pLDDT (71.6) with a minimum of 46.1 — some regions may be disordered. Deprioritize.
- All sequences are highly charged (many K, E, D residues) — typical for computationally designed helical binders.

## Caveats

1. **No binding affinity prediction**: RFdiffusion designs backbones geometrically but does not predict binding energy. AlphaFold2-Multimer or Rosetta interface scoring needed.
2. **No experimental validation**: These are computational designs only. Experimental testing (SPR, ITC, or co-crystallization) would be required.
3. **Hotspot selection**: The current design targets the kinase domain broadly (contig `80/0 A27-388`). More specific hotspot targeting of the ATP-binding pocket or substrate groove could yield more potent inhibitory binders.
4. **Sequence diversity**: ProteinMPNN was called with minimal parameters (NVIDIA API rejected `chains_to_design`, `temperature`, `num_sequences`). Running with the self-hosted ProteinMPNN container would allow more control.

## Files on Server (moltbot)

```
/home/bryzant/sma-platform/data/binder_designs/
  rock2_backbone_{1-5}.pdb          — RFdiffusion backbone structures (complex)
  rock2_mpnn_{1-5}.json             — ProteinMPNN sequence design results
  rock2_binder_{1-5}_esmfold.pdb    — ESMfold-predicted binder structures
  rock2_binder_final.json           — Summary results
```

```
/home/bryzant/sma-platform/data/pdb/
  ROCK2_O75116.cif                  — AlphaFold full-length ROCK2 (CIF format)
  ROCK2_2F2U.pdb                    — Experimental kinase domain (X-ray)
```

## Next Steps

1. **AlphaFold2-Multimer**: Predict complex structures of top binders (Design 4, 5) with ROCK2 kinase domain to assess interface quality
2. **Rosetta InterfaceAnalyzer**: Score binding energy (ddG) for each design
3. **Hotspot-focused redesign**: Target specific residues in the ATP pocket (K121, E139, D176, D232)
4. **Fix platform NIM adapter**: Update `design_binder()` to use correct NVIDIA API format (no `hotspot_residues`/`num_designs` at top level), fix AlphaFold URL for large proteins (use CIF or experimental PDB), fix ESMfold URL (no `/predict` suffix)

## API Format Discoveries

During this session, we discovered that the NVIDIA NIM APIs have stricter schemas than documented:

| API | Accepted Fields | Rejected Fields |
|-----|----------------|-----------------|
| RFdiffusion | `input_pdb`, `contigs` | `hotspot_residues`, `num_designs`, `target_pdb` |
| ProteinMPNN | `input_pdb` | `chains_to_design`, `temperature`, `num_sequences`, `pdb` |
| ESMfold | `sequence` (at `/nvidia/esmfold`) | Any request to `/predict` suffix (404) |
