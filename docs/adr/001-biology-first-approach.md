# ADR-001: Biology-First Approach

**Status**: Accepted
**Date**: 2025-03-14
**Context**: Deciding the overall strategy for the SMA research platform.

## Decision

We follow a biology-first, evidence-based approach:
1. **Phase A**: Build the evidence graph (papers, trials, datasets, targets, claims)
2. **Phase B**: Score and rank targets based on evidence quality
3. **Phase C**: Only then use GPU compute for molecule screening / CRISPR / AAV

## Rationale

- GPU-first approaches waste compute on poorly validated targets
- The existing SMA literature is vast but fragmented — structuring it is the bottleneck
- STMN2 emerged as a validated target through careful literature analysis, not brute-force screening
- Most "moonshot" projects fail because they skip target validation

## Consequences

- We invest heavily in ingestion and evidence extraction first
- GPU/compute work is deferred until we have validated targets
- The platform's value is in the structured data, not raw compute
- All claims must trace back to a source — no unsupported assertions
