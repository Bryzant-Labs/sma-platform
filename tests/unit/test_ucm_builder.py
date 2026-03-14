"""Tests for UCM builder."""

import tempfile
from pathlib import Path

import pandas as pd

from sma_platform.ucm.builder import UCMBuilder


def _write_tsv(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def test_build_nodes_from_tsv():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw = Path(tmpdir) / "raw"
        raw.mkdir()
        out = Path(tmpdir) / "out"

        _write_tsv(raw / "nodes.tsv", "node_id\tnode_type\tlabel\nHGNC:11117\tgene\tSMN1\n")
        builder = UCMBuilder(raw)
        df = builder.build_nodes(out)

        assert len(df) == 1
        assert df.iloc[0]["node_id"] == "HGNC:11117"
        assert (out / "nodes.parquet").exists()


def test_build_nodes_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw = Path(tmpdir) / "raw"
        raw.mkdir()
        out = Path(tmpdir) / "out"

        builder = UCMBuilder(raw)
        df = builder.build_nodes(out)
        assert len(df) == 0


def test_build_edges_normalizes_confidence():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw = Path(tmpdir) / "raw"
        raw.mkdir()
        out = Path(tmpdir) / "out"

        _write_tsv(raw / "edges.tsv", "src\tdst\trelation\tconfidence\nA\tB\tregulates\t1.5\n")
        builder = UCMBuilder(raw)
        df = builder.build_edges(out)

        assert df.iloc[0]["confidence"] == 1.0  # clamped


def test_build_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw = Path(tmpdir) / "raw"
        raw.mkdir()
        out = Path(tmpdir) / "out"

        _write_tsv(raw / "nodes.tsv", "node_id\tnode_type\tlabel\nA\tgene\tGeneA\n")
        _write_tsv(raw / "edges.tsv", "src\tdst\trelation\tconfidence\nA\tB\tregulates\t0.8\n")
        _write_tsv(raw / "evidence.tsv", "evidence_id\tsource_type\tsource_ref\nEV1\tpaper\tPMID:123\n")

        builder = UCMBuilder(raw)
        counts = builder.build_all(out)

        assert counts == {"nodes": 1, "edges": 1, "evidence": 1}
