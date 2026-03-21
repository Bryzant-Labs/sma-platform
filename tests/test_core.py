"""Core platform tests — minimum viable test suite."""
import pytest
import httpx

API = "https://sma-research.info/api/v2"


class TestAPIHealth:
    """Basic API health and consistency checks."""

    def test_stats_endpoint_returns_all_fields(self):
        r = httpx.get(f"{API}/stats", timeout=10)
        assert r.status_code == 200
        data = r.json()
        required = ["sources", "targets", "drugs", "trials", "claims", "hypotheses"]
        for field in required:
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], int), f"{field} should be int"
            assert data[field] > 0, f"{field} should be > 0"

    def test_targets_returns_21(self):
        r = httpx.get(f"{API}/targets", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 21

    def test_hypotheses_prioritized_has_tiers(self):
        r = httpx.get(f"{API}/hypotheses/prioritized", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "tier_a" in data
        assert "tier_b" in data
        assert "tier_c" in data
        assert data["total"] > 0

    def test_calibration_returns_grade(self):
        r = httpx.get(f"{API}/calibration/bayesian/report", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "grade" in data
        assert data["grade"] in ["A", "B", "C", "D"]

    def test_convergence_scores_all_targets(self):
        r = httpx.get(f"{API}/convergence/scores", timeout=30)
        assert r.status_code == 200
        data = r.json()
        targets = data.get("targets", [])
        assert len(targets) >= 20
