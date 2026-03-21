# Next Milestones — March/April 2026

## Immediate (This Week)

### M-NOW-1: Send Simon Email
- Email is ready in `docs/emails/email_simon_followup.md`
- Meeting prep in `docs/meeting-prep-simon-march30.md`
- Presentation in `docs/presentation-simon-march30.html`
- **Action: Review and send**

### M-NOW-2: Validate 60 Gold-Standard Claims Manually
- File: `tests/gold_standard/auto_validated_claims.json`
- Auto-validation showed 98.3% lenient accuracy but only 28.3% strict
- Need human expert review of at least 20 claims
- Run: `python tests/gold_standard/evaluate.py tests/gold_standard/auto_validated_claims.json`

### M-NOW-3: Run Reproducibility Check on Moltbot
- Script: `scripts/reproduce.sh`
- Verifies schema, stats, claims, convergence, calibration, hypotheses
- First run establishes baseline

## Short-Term (April 2026)

### M-APR-1: CORO1C Intron Retention — Definitive Proof
- Download SRA raw data (SRP093754, 101 FASTQ runs)
- Install STAR + rMATS on Vast.ai A100
- Run splice junction analysis on CORO1C exon2-intron2-exon3
- Would be FIRST direct evidence of CORO1C intron retention in SMA
- Estimated GPU time: 2-4 hours, ~$10

### M-APR-2: CORO1C Expression After HDAC Treatment
- IF Simon/collaborator can provide SMA fibroblasts:
  - Treat with LBH589 (panobinostat) 10-100 nM, 48-72h
  - qRT-PCR for CORO1C mRNA
  - Western blot for CORO1C protein
- This is THE key experiment nobody has done

### M-APR-3: Riluzole SPR Binding Validation
- Commission SPR assay at Leipzig or CRO
- Riluzole vs recombinant SMN2 protein
- Go/No-Go: Kd < 50 micromolar

### M-APR-4: bioRxiv Preprint Submission
- Draft is at `docs/preprint_draft.md` (corrected version)
- Update with CORO1C double-hit model
- Update with 20-pose validation methodology
- Submit to bioRxiv biology section

## Medium-Term (May-June 2026)

### M-MAY-1: Anti-miR-133a-3p Design + Synthesis
- LNA-modified antagomir (design in `docs/mir133a-coro1c-therapeutic.md`)
- Order from IDT or Exiqon
- Test in iPSC-MN for CORO1C de-repression

### M-MAY-2: Combinatorial Screening (in silico)
- Risdiplam + VPA + 4-AP computational modeling
- Drug-drug interaction prediction
- Pathway overlap analysis

### M-MAY-3: Cure SMA Grant Application
- LOI typically due March-May
- Based on CORO1C activation hypothesis
- Use platform data as preliminary results

## Long-Term (Q3-Q4 2026)

### M-Q3-1: Mouse Model Validation
- If HDAC → CORO1C confirmed in cells
- SMA-delta-7 mice, LBH589 treatment
- CORO1C IHC in L1 vs L5

### M-Q3-2: Prospective Backtesting Validation
- Run temporal backtests as data accumulates over months
- Prove platform predictions improve over time

### M-Q3-3: Investigator-Initiated Trial Design
- If all preclinical gates pass
- Risdiplam + VPA combinatorial in SMA patients
- Existing safety profiles accelerate timeline

## Platform Maintenance (Ongoing)

- Daily pipeline at 3 AM UTC (PubMed + bioRxiv + trials)
- Weekly convergence re-computation
- Monthly gold-standard claim validation expansion (60 → 500)
- Quarterly HuggingFace dataset update
