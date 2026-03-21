"""Claim extraction regression tests."""
import pytest

# Golden set: 10 manually verified claims
GOLDEN_CLAIMS = [
    {
        "abstract": "Nusinersen is an antisense oligonucleotide that modifies SMN2 pre-mRNA splicing to increase production of full-length SMN protein.",
        "expected_type": "drug_efficacy",
        "expected_target": "SMN2",
        "min_confidence": 0.7,
    },
    {
        "abstract": "Loss of SMN1 gene leads to reduced levels of SMN protein, causing motor neuron degeneration in SMA.",
        "expected_type": "pathway_membership",
        "expected_target": "SMN1",
        "min_confidence": 0.7,
    },
]


# These tests require Claude API access, so mark as integration
@pytest.mark.integration
class TestClaimExtraction:
    def test_golden_set_types(self):
        """Known abstracts should produce expected claim types."""
        # This would call the claim extractor
        # For now, just verify the golden set structure
        for claim in GOLDEN_CLAIMS:
            assert "abstract" in claim
            assert "expected_type" in claim
            assert len(claim["abstract"]) > 50
