"""Build UCM artifacts (nodes, edges, evidence) from TSV inputs.

Usage:
    from sma_platform.ucm.builder import UCMBuilder
    builder = UCMBuilder("data/raw")
    builder.build_all("data/processed")
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .utils import ensure_dir, normalize_confidence, now_iso, read_tsv, sha256_file

NODE_REQUIRED = ["node_id", "node_type", "label"]
EDGE_REQUIRED = ["src", "dst", "relation", "confidence"]
EVIDENCE_REQUIRED = ["evidence_id", "source_type", "source_ref"]


class UCMBuilder:
    """Builds Parquet artifacts from raw TSV data."""

    def __init__(self, raw_dir: str | Path):
        self.raw_dir = Path(raw_dir)

    def build_nodes(self, out_dir: Path) -> pd.DataFrame:
        ensure_dir(out_dir)
        df = read_tsv(self.raw_dir / "nodes.tsv")
        if df is None:
            df = pd.DataFrame(columns=NODE_REQUIRED + ["synonyms", "namespace", "metadata_json"])
        else:
            for col in NODE_REQUIRED:
                if col not in df.columns:
                    raise ValueError(f"nodes.tsv missing required column: {col}")
            for col in ["synonyms", "namespace", "metadata_json"]:
                if col not in df.columns:
                    df[col] = ""

        out_path = out_dir / "nodes.parquet"
        df.to_parquet(out_path, index=False)
        return df

    def build_edges(self, out_dir: Path) -> pd.DataFrame:
        ensure_dir(out_dir)
        df = read_tsv(self.raw_dir / "edges.tsv")
        if df is None:
            df = pd.DataFrame(columns=EDGE_REQUIRED + ["direction", "effect", "evidence_ids", "metadata_json"])
        else:
            for col in EDGE_REQUIRED:
                if col not in df.columns:
                    raise ValueError(f"edges.tsv missing required column: {col}")
            for col in ["direction", "effect", "evidence_ids", "metadata_json"]:
                if col not in df.columns:
                    df[col] = ""
            df["confidence"] = df["confidence"].apply(normalize_confidence)

        out_path = out_dir / "edges.parquet"
        df.to_parquet(out_path, index=False)
        return df

    def build_evidence(self, out_dir: Path) -> pd.DataFrame:
        ensure_dir(out_dir)
        df = read_tsv(self.raw_dir / "evidence.tsv")
        if df is None:
            df = pd.DataFrame(columns=EVIDENCE_REQUIRED + ["notes", "date", "checksum"])
        else:
            for col in EVIDENCE_REQUIRED:
                if col not in df.columns:
                    raise ValueError(f"evidence.tsv missing required column: {col}")
            for col in ["notes", "date", "checksum"]:
                if col not in df.columns:
                    df[col] = ""
            # Auto-fill dates
            for i, row in df.iterrows():
                if not row.get("date"):
                    df.at[i, "date"] = now_iso()

        out_path = out_dir / "evidence.tsv"
        df.to_csv(out_path, sep="\t", index=False)
        return df

    def build_all(self, out_dir: str | Path) -> dict[str, int]:
        """Build all artifacts. Returns row counts."""
        out = Path(out_dir)
        nodes = self.build_nodes(out)
        edges = self.build_edges(out)
        evidence = self.build_evidence(out)
        return {"nodes": len(nodes), "edges": len(edges), "evidence": len(evidence)}
