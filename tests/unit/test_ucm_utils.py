"""Tests for UCM utility functions."""

import tempfile
from pathlib import Path

from sma_platform.ucm.utils import normalize_confidence, sha256_file, stable_id


def test_normalize_confidence_valid():
    assert normalize_confidence(0.5) == 0.5
    assert normalize_confidence("0.8") == 0.8
    assert normalize_confidence(0) == 0.0
    assert normalize_confidence(1) == 1.0


def test_normalize_confidence_clamps():
    assert normalize_confidence(-0.5) == 0.0
    assert normalize_confidence(1.5) == 1.0
    assert normalize_confidence(999) == 1.0


def test_normalize_confidence_invalid():
    assert normalize_confidence("invalid") == 0.0
    assert normalize_confidence(None) == 0.0
    assert normalize_confidence("") == 0.0


def test_sha256_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test content")
        f.flush()
        h = sha256_file(f.name)
    assert isinstance(h, str)
    assert len(h) == 64  # SHA-256 hex digest


def test_stable_id():
    id1 = stable_id("TEST:", "a", "b", "c")
    id2 = stable_id("TEST:", "a", "b", "c")
    id3 = stable_id("TEST:", "x", "y", "z")
    assert id1 == id2  # deterministic
    assert id1 != id3  # different inputs
    assert id1.startswith("TEST:")
