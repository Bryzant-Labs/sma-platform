"""Evaluate claim extraction against gold standard.

Usage: python tests/gold_standard/evaluate.py tests/gold_standard/validated_claims.json
"""
import json
import sys
from collections import Counter


def evaluate(validated_path):
    with open(validated_path) as f:
        claims = json.load(f)

    total = len(claims)
    judged = [
        c for c in claims if c["human_judgment"]["factually_correct"] is not None
    ]

    if not judged:
        print(
            "No claims have been judged yet. Please fill in human_judgment fields."
        )
        return

    # Accuracy metrics
    correct = sum(
        1 for c in judged if c["human_judgment"]["factually_correct"] == "yes"
    )
    partial = sum(
        1 for c in judged if c["human_judgment"]["factually_correct"] == "partial"
    )
    wrong = sum(
        1 for c in judged if c["human_judgment"]["factually_correct"] == "no"
    )

    type_correct = sum(
        1 for c in judged if c["human_judgment"]["type_correct"] == "yes"
    )
    target_correct = sum(
        1 for c in judged if c["human_judgment"]["target_correct"] == "yes"
    )

    errors = Counter(
        c["human_judgment"]["error_category"]
        for c in judged
        if c["human_judgment"]["error_category"]
    )

    print(f"Gold Standard Evaluation Report")
    print(f"{'=' * 50}")
    print(f"Total claims: {total}")
    print(f"Judged: {len(judged)}")
    print(f"")
    print(
        f"Factual accuracy: {correct}/{len(judged)} ({100*correct/len(judged):.1f}%)"
    )
    print(f"Partial: {partial}/{len(judged)} ({100*partial/len(judged):.1f}%)")
    print(f"Wrong: {wrong}/{len(judged)} ({100*wrong/len(judged):.1f}%)")
    print(
        f"Type correct: {type_correct}/{len(judged)} ({100*type_correct/len(judged):.1f}%)"
    )
    print(
        f"Target correct: {target_correct}/{len(judged)} ({100*target_correct/len(judged):.1f}%)"
    )
    print(f"")
    print(f"Error distribution:")
    for err, cnt in errors.most_common():
        print(f"  {err}: {cnt}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <validated_claims.json>")
        sys.exit(1)
    evaluate(sys.argv[1])
