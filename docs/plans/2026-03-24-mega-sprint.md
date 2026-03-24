# 24h Mega Sprint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete Wave 1 (science), Wave 2 (frontend), Wave 3 (presentation) to prepare for Simon meeting (March 30 week).

**Architecture:** Parallel agent execution — Wave 1 tasks are independent (docking, hypotheses, literature, synthesis, screening). Wave 2 tasks modify frontend/index.html (sequential). Wave 3 depends on Wave 1+2 outputs.

**Tech Stack:** FastAPI, asyncpg, NVIDIA NIM DiffDock v2.2, Claude Sonnet 4.6 (hypotheses), vanilla JS frontend, AlphaFold PDB structures

---

## Wave 1: Science Sprint (Parallel)

### Task 1A: Fix DiffDock + Run LIMK2/ROCK2 Docking Campaign

**Problem:** All 14 dockings returned 400 Bad Request. ROCK2 PDB is 11,433 lines (full 1,388 residues) — too large for DiffDock NIM.

**Fix:** Trim PDB to kinase domain only:
- ROCK2: residues 18-413 (kinase domain, UniProt annotation)
- LIMK2: residues 309-595 (kinase domain)

**Files:**
- Modify: `scripts/dock_limk2_rock2_campaign.py` — add PDB trimming function
- Output: `data/docking/limk2_rock2_campaign_2026-03-24.json` (overwrite failed results)
- Output: `data/structures/ROCK2_O75116_kinase.pdb`, `LIMK2_P53671_kinase.pdb`

**Steps:**
1. Add `trim_pdb_to_domain(pdb_text, start_res, end_res)` function
2. Define kinase domains for each target
3. Run campaign with trimmed PDBs
4. If still 400: try base64-encoding PDB (some NIM versions require this)
5. Save results, print summary
6. Import results to DB via screening API

### Task 1B: Generate 50+ Hypotheses

**Targets:** LIMK2, CFL2, PFN2, PFN1, ROCK1, ROCK2, ACTG1, RAC1
**Method:** Use Claude Sonnet 4.6 locally (Max Plan, free) to generate mechanistic hypothesis cards
**Template per hypothesis:**
- title, mechanism, evidence_for, evidence_against, testable_prediction, therapeutic_implication, tier (A/B/C)

**Files:**
- Create: `scripts/generate_hypotheses_wave2.py`
- Output: POST to moltbot `/api/v2/hypotheses` (admin key)

### Task 1C: ROCK Inhibitor Landscape

**Research:** PubMed search for all ROCK inhibitors tested in neurodegenerative disease
**Key compounds:** Fasudil, Y-27632, Ripasudil, H-1152, Netarsudil, Belumosudil, KD025
**Output:** `docs/research/rock-inhibitor-landscape.md`

### Task 1D: Convergence Synthesis Refresh

**Update synthesis cards with:**
- CORO1C reframe: glial marker, not MN target
- LIMK2 > LIMK1 for SMA
- CFL2 as disease-specific biomarker
- 10/14 actin genes UP in SMA MNs
- Triple therapy update: Risdiplam + Fasudil + LIMK2-inhibitor

**Files:**
- Modify: `src/sma_platform/reasoning/convergence_hypothesis.py` if needed
- POST to `/api/v2/synthesis/run` to regenerate

### Task 1E: ChEMBL LIMK2 Candidate Selection

**Pipeline:**
1. From 23,057 enriched ChEMBL compounds
2. Filter: BBB-permeable (4,020), kinase activity, LIMK-related
3. Rank top 20 by: pChEMBL value, selectivity, drug-likeness
4. Prepare SMILES list for DiffDock batch

**Files:**
- Create: `scripts/filter_chembl_limk2.py`
- Output: `data/docking/limk2_candidates_top20.json`

---

## Wave 2: Frontend Polish (Sequential on frontend/index.html)

### Task 2A: Menu Restructuring
Groups: Core Science | Discovery | Analysis | Clinical | Advanced | Meta

### Task 2B: Interactive Advanced Modules
Pattern: fetch API data, render expandable cards with real content

### Task 2C: JS Bug Fixes
Fix SmilesDrawer, NGL 3D viewer, syntax errors

### Task 2D: Homepage Redesign
Discovery pipeline, metrics dashboard, latest findings

---

## Wave 3: Presentation (Depends on Wave 1+2)

### Task 3A: Simon PPTX v4
### Task 3B: 5 News Posts
### Task 3C: Data Quality Audit
### Task 3D: Full Deploy + Smoke Test

---

## Execution Strategy
- Wave 1: 5 parallel agents (background)
- Wave 2: Sequential (shared frontend file)
- Wave 3: After Wave 1+2 complete
- All git handled by lead (Opus) only
