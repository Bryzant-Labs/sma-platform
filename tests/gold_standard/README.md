# Gold-Standard Claim Validation Set

## Purpose
Manually verified claims to benchmark the LLM claim extraction pipeline.
Without this, we cannot prove that our 30,000+ claims are accurate.

## Status: SKELETON — needs manual curation

## Process
1. Sample 500 claims from the database (stratified by claim_type and confidence)
2. For each claim, a human reads the source abstract and judges:
   - Is the claim factually correct? (yes/partial/no/unverifiable)
   - Is the claim_type label correct? (yes/no, suggest correct type)
   - Is the target linking correct? (yes/no, suggest correct target)
   - Is the confidence reasonable? (overconfident/correct/underconfident)
3. Store judgments in gold_standard_claims.json
4. Run automated comparison: LLM output vs human judgment
5. Report: precision, recall, F1 by claim_type

## Error Categories
- **False positive**: Claim extracted but not actually stated in abstract
- **False negative**: Important assertion in abstract not extracted as claim
- **Wrong type**: Claim exists but labeled with wrong claim_type
- **Wrong target**: Claim linked to wrong target gene/protein
- **Overstated causality**: Correlation stated as causation
- **Hallucination**: Claim content not present in source text at all
