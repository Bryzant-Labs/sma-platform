"""Sample claims for gold-standard validation.

Usage: python tests/gold_standard/sample_claims.py > tests/gold_standard/claims_to_validate.json
"""
import asyncio
import asyncpg
import json
import random
import sys


async def sample_claims():
    conn = await asyncpg.connect(
        "postgresql://sma:sma-research-2026@localhost:5432/sma_platform"
    )

    # Get claim type distribution
    types = await conn.fetch(
        "SELECT claim_type, COUNT(*) as cnt FROM claims GROUP BY claim_type ORDER BY cnt DESC"
    )
    print("Claim type distribution:", file=sys.stderr)
    for t in types:
        print(f"  {t['claim_type']}: {t['cnt']}", file=sys.stderr)

    # Sample proportionally from each type
    samples = []
    for t in types:
        claim_type = t["claim_type"]
        count = min(t["cnt"], 5)  # 5 per type for initial set
        rows = await conn.fetch(
            "SELECT c.id, c.claim_type, c.predicate, c.confidence, c.subject_id, c.object_id, "
            "s.title as source_title, s.external_id as pmid, s.abstract "
            "FROM claims c LEFT JOIN evidence e ON e.claim_id = c.id "
            "LEFT JOIN sources s ON s.id = e.source_id "
            "WHERE c.claim_type = $1 AND s.abstract IS NOT NULL "
            "ORDER BY random() LIMIT $2",
            claim_type,
            count,
        )
        for r in rows:
            samples.append(
                {
                    "claim_id": str(r["id"]),
                    "claim_type": r["claim_type"],
                    "predicate": r["predicate"],
                    "confidence": float(r["confidence"]) if r["confidence"] else None,
                    "source_title": r["source_title"],
                    "pmid": r["pmid"],
                    "abstract_preview": (
                        r["abstract"][:300] if r["abstract"] else None
                    ),
                    # Human validation fields (to be filled manually)
                    "human_judgment": {
                        "factually_correct": None,  # yes/partial/no/unverifiable
                        "type_correct": None,  # yes/no
                        "suggested_type": None,
                        "target_correct": None,  # yes/no
                        "confidence_assessment": None,  # overconfident/correct/underconfident
                        "error_category": None,  # false_positive/wrong_type/wrong_target/overstated/hallucination/none
                        "notes": "",
                    },
                }
            )

    await conn.close()
    return samples


if __name__ == "__main__":
    samples = asyncio.run(sample_claims())
    print(json.dumps(samples, indent=2, default=str))
