"""Daily auto-validation of prediction cards against new evidence.

Run after daily PubMed ingestion (e.g. 06:30 UTC via cron).
Re-computes convergence scores and updates prediction card status.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.sma_platform.core.database import init_pool, close_pool, execute, fetch, fetchrow
from src.sma_platform.reasoning.convergence_engine import compute_target_convergence

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SCORE_CHANGE_THRESHOLD = 0.1


async def validate_predictions():
    """Re-validate all active prediction cards."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        logger.error("DATABASE_URL not set")
        return

    await init_pool(dsn)

    try:
        cards = await fetch(
            """SELECT * FROM prediction_cards
               WHERE status IN ('validated', 'monitoring')
               ORDER BY convergence_score DESC"""
        )

        if not cards:
            logger.info("No active predictions to validate")
            return

        updated = 0
        for card in cards:
            card = dict(card)
            target_id = str(card["target_id"])

            result = await compute_target_convergence(target_id)
            if not result:
                continue

            new_score = result["composite_score"]
            old_score = float(card["convergence_score"])
            delta = round(new_score - old_score, 3)

            if abs(delta) < 0.001:
                continue

            last_validated = card.get("last_validated_at") or card["created_at"]
            new_claims_row = await fetchrow(
                """SELECT COUNT(*) AS cnt FROM claims
                   WHERE subject_id = $1 AND created_at > $2""",
                target_id, last_validated,
            )
            new_claims = new_claims_row["cnt"] if new_claims_row else 0

            history = card.get("score_history") or []
            if isinstance(history, str):
                history = json.loads(history)

            history.append({
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "score": new_score,
                "previous_score": old_score,
                "delta": delta,
                "new_claims_count": new_claims,
            })

            new_status = card["status"]
            if delta > SCORE_CHANGE_THRESHOLD:
                new_status = "strengthened"
            elif delta < -SCORE_CHANGE_THRESHOLD:
                new_status = "weakened"

            await execute(
                """UPDATE prediction_cards SET
                    convergence_score = $1,
                    confidence_level = $2,
                    score_history = $3,
                    status = $4,
                    last_validated_at = NOW(),
                    updated_at = NOW()
                   WHERE id = $5""",
                new_score,
                result["confidence_level"],
                json.dumps(history),
                new_status,
                card["id"],
            )
            updated += 1
            logger.info(
                "Updated %s: %.3f -> %.3f (delta %.3f) -> %s",
                card["target_label"], old_score, new_score, delta, new_status,
            )

        logger.info("Validation complete: %d/%d cards updated", updated, len(cards))

    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(validate_predictions())
