"""Patent landscape analysis for SMA therapeutic space.

Analyzes the ~578 SMA patents in the sources table to provide:
- Temporal filing trends (patents per year)
- Mechanism clustering (splicing, gene therapy, antisense, etc.)
- Top assignees / applicants
- Recent competitive intelligence
- Freedom-to-operate assessment for specific compounds
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any

from ..core.database import fetch, fetchrow

logger = logging.getLogger(__name__)

# Mechanism keyword clusters for patent classification
MECHANISM_KEYWORDS: dict[str, list[str]] = {
    "splicing": [
        "splicing", "splice", "exon skipping", "exon inclusion",
        "pre-mrna", "spliceosome", "splice modifier", "splice modulator",
    ],
    "gene_therapy": [
        "gene therapy", "gene transfer", "gene delivery", "aav",
        "adeno-associated", "viral vector", "transgene", "gene replacement",
    ],
    "antisense": [
        "antisense", "oligonucleotide", "aso", "morpholino",
        "locked nucleic", "gapmers", "sirna", "mirna",
    ],
    "small_molecule": [
        "small molecule", "compound", "pharmaceutical composition",
        "oral administration", "tablet", "capsule", "formulation",
    ],
    "crispr": [
        "crispr", "cas9", "cas13", "gene editing", "genome editing",
        "base editing", "prime editing", "guide rna",
    ],
    "biomarker": [
        "biomarker", "diagnostic", "prognostic", "detection",
        "assay", "monitoring", "neurofilament", "smn protein level",
    ],
    "screening": [
        "screening", "high throughput", "hts", "drug discovery",
        "library", "hit identification", "assay development",
    ],
    "delivery": [
        "delivery", "nanoparticle", "lipid nanoparticle", "lnp",
        "intrathecal", "blood-brain barrier", "bbb", "cns delivery",
        "encapsulation", "liposome",
    ],
}

# Known SMA discovery targets for cross-referencing with patents
SMA_DISCOVERY_TARGETS = [
    "SMN1", "SMN2", "PLS3", "NCALD", "STMN2", "UBA1",
    "CORO1C", "AGRN", "DYNC1H1", "4-AP", "4-aminopyridine",
    "dalfampridine", "fampridine", "risdiplam", "nusinersen",
    "branaplam", "onasemnogene", "zolgensma",
]


def _classify_mechanism(title: str, abstract: str) -> list[str]:
    """Classify a patent into mechanism clusters based on title/abstract text."""
    text = f"{title} {abstract}".lower()
    matched = []
    for mechanism, keywords in MECHANISM_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                matched.append(mechanism)
                break
    return matched if matched else ["other"]


def _extract_assignee(metadata: dict | str | None, title: str) -> str | None:
    """Extract assignee/applicant from patent metadata or title heuristics."""
    if metadata:
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        # Common metadata fields for patent assignees
        for field in ("assignee", "applicant", "assignees", "applicants",
                      "patent_assignee", "patent_applicant", "owner"):
            val = metadata.get(field)
            if val:
                if isinstance(val, list):
                    return val[0] if val else None
                return str(val)

    # Heuristic: company names often appear in parentheses in titles
    paren_match = re.search(r'\(([A-Z][^)]{3,})\)', title or "")
    if paren_match:
        return paren_match.group(1).strip()

    return None


def _mentions_compound(title: str, abstract: str, compound: str) -> bool:
    """Check if patent text mentions a specific compound (case-insensitive)."""
    text = f"{title} {abstract}".lower()
    compound_lower = compound.lower()

    # Direct mention
    if compound_lower in text:
        return True

    # Common synonyms for well-known compounds
    synonyms: dict[str, list[str]] = {
        "4-aminopyridine": ["4-ap", "dalfampridine", "fampridine", "aminopyridine"],
        "4-ap": ["4-aminopyridine", "dalfampridine", "fampridine", "aminopyridine"],
        "dalfampridine": ["4-aminopyridine", "4-ap", "fampridine", "aminopyridine"],
        "risdiplam": ["evrysdi", "rg7916"],
        "nusinersen": ["spinraza"],
        "branaplam": ["lmi070", "novartis"],
        "onasemnogene": ["zolgensma", "avxs-101"],
    }

    for syn in synonyms.get(compound_lower, []):
        if syn in text:
            return True

    return False


def _mentions_discovery_targets(title: str, abstract: str) -> list[str]:
    """Check which SMA discovery targets are mentioned in patent text."""
    text = f"{title} {abstract}".lower()
    found = []
    for target in SMA_DISCOVERY_TARGETS:
        if target.lower() in text:
            found.append(target)
    return found


async def get_landscape() -> dict[str, Any]:
    """Analyze the full SMA patent landscape.

    Returns:
        - patents_per_year: filing counts by year
        - mechanism_clusters: patent counts per mechanism type
        - top_assignees: most frequent patent holders
        - recent_filings: patents from the last 2 years
        - total_patents: total count
        - mechanism_details: per-mechanism list of representative patents
    """
    rows = await fetch(
        """SELECT id, external_id, title, abstract, pub_date, metadata
           FROM sources
           WHERE source_type = 'patent'
           ORDER BY pub_date DESC NULLS LAST"""
    )

    if not rows:
        return {
            "total_patents": 0,
            "patents_per_year": {},
            "mechanism_clusters": {},
            "top_assignees": [],
            "recent_filings": [],
            "note": "No patents found in the database.",
        }

    patents = [dict(r) for r in rows]
    total = len(patents)

    # --- Patents per year ---
    year_counts: Counter[int] = Counter()
    for p in patents:
        pd = p.get("pub_date")
        if pd:
            yr = pd.year if isinstance(pd, date) else None
            if yr is None:
                try:
                    yr = int(str(pd)[:4])
                except (ValueError, TypeError):
                    continue
            year_counts[yr] += 1
    patents_per_year = dict(sorted(year_counts.items()))

    # --- Mechanism clustering ---
    mechanism_counts: Counter[str] = Counter()
    mechanism_patents: dict[str, list[dict]] = defaultdict(list)
    for p in patents:
        mechanisms = _classify_mechanism(p.get("title", ""), p.get("abstract", ""))
        for m in mechanisms:
            mechanism_counts[m] += 1
            if len(mechanism_patents[m]) < 5:  # Keep up to 5 examples per cluster
                mechanism_patents[m].append({
                    "external_id": p["external_id"],
                    "title": p.get("title", ""),
                    "pub_date": str(p.get("pub_date", "")),
                })

    # --- Top assignees ---
    assignee_counts: Counter[str] = Counter()
    for p in patents:
        assignee = _extract_assignee(p.get("metadata"), p.get("title", ""))
        if assignee:
            assignee_counts[assignee] += 1
    top_assignees = [
        {"assignee": name, "patent_count": count}
        for name, count in assignee_counts.most_common(20)
    ]

    # --- Recent filings (last 2 years) ---
    cutoff = date.today() - timedelta(days=730)
    recent = []
    for p in patents:
        pd = p.get("pub_date")
        if pd:
            pub = pd if isinstance(pd, date) else None
            if pub is None:
                try:
                    pub = date.fromisoformat(str(pd)[:10])
                except (ValueError, TypeError):
                    continue
            if pub >= cutoff:
                targets_mentioned = _mentions_discovery_targets(
                    p.get("title", ""), p.get("abstract", "")
                )
                recent.append({
                    "external_id": p["external_id"],
                    "title": p.get("title", ""),
                    "pub_date": str(pub),
                    "mechanisms": _classify_mechanism(
                        p.get("title", ""), p.get("abstract", "")
                    ),
                    "assignee": _extract_assignee(
                        p.get("metadata"), p.get("title", "")
                    ),
                    "discovery_targets_mentioned": targets_mentioned,
                })

    # --- Trend analysis ---
    sorted_years = sorted(year_counts.keys())
    trend = "stable"
    if len(sorted_years) >= 3:
        recent_avg = sum(year_counts.get(y, 0) for y in sorted_years[-2:]) / 2
        older_avg = sum(year_counts.get(y, 0) for y in sorted_years[:-2]) / max(len(sorted_years) - 2, 1)
        if older_avg > 0:
            if recent_avg > older_avg * 1.3:
                trend = "increasing"
            elif recent_avg < older_avg * 0.7:
                trend = "decreasing"

    return {
        "total_patents": total,
        "patents_per_year": patents_per_year,
        "filing_trend": trend,
        "mechanism_clusters": {
            m: {"count": c, "examples": mechanism_patents.get(m, [])}
            for m, c in mechanism_counts.most_common()
        },
        "top_assignees": top_assignees,
        "recent_filings_count": len(recent),
        "recent_filings": recent[:50],  # Cap to avoid huge responses
    }


async def freedom_to_operate(compound_name: str) -> dict[str, Any]:
    """Assess freedom-to-operate for a specific compound against SMA patents.

    Searches all patents for mentions of the compound (including known synonyms).
    Returns a risk assessment with relevant patent details.

    Args:
        compound_name: Name of the compound to check (e.g., "4-aminopyridine")

    Returns:
        - risk_level: "clear", "caution", or "blocked"
        - matching_patents: list of patents mentioning this compound
        - total_checked: how many patents were scanned
        - compound: the queried compound name
    """
    if not compound_name or not compound_name.strip():
        return {
            "compound": compound_name,
            "risk_level": "error",
            "error": "Compound name is required.",
            "matching_patents": [],
        }

    rows = await fetch(
        """SELECT id, external_id, title, abstract, pub_date, metadata
           FROM sources
           WHERE source_type = 'patent'
           ORDER BY pub_date DESC NULLS LAST"""
    )

    patents = [dict(r) for r in rows]
    total_checked = len(patents)
    matching: list[dict[str, Any]] = []

    for p in patents:
        title = p.get("title", "") or ""
        abstract = p.get("abstract", "") or ""

        if _mentions_compound(title, abstract, compound_name):
            mechanisms = _classify_mechanism(title, abstract)
            assignee = _extract_assignee(p.get("metadata"), title)

            # Determine relevance level based on how directly the compound is mentioned
            compound_lower = compound_name.lower()
            combined = f"{title} {abstract}".lower()

            # "direct" = compound in the title (strongest signal)
            # "claims_related" = compound in abstract only
            if compound_lower in (title or "").lower():
                relevance = "direct"
            else:
                relevance = "claims_related"

            matching.append({
                "external_id": p["external_id"],
                "title": title,
                "abstract_snippet": (abstract[:300] + "...") if len(abstract) > 300 else abstract,
                "pub_date": str(p.get("pub_date", "")),
                "mechanisms": mechanisms,
                "assignee": assignee,
                "relevance": relevance,
            })

    # Risk assessment logic
    direct_hits = [m for m in matching if m["relevance"] == "direct"]
    related_hits = [m for m in matching if m["relevance"] == "claims_related"]

    if len(direct_hits) >= 2:
        risk_level = "blocked"
        risk_explanation = (
            f"Found {len(direct_hits)} patents with '{compound_name}' directly in the title. "
            f"This compound has significant patent coverage. A detailed FTO opinion from "
            f"a patent attorney is strongly recommended before proceeding."
        )
    elif direct_hits:
        risk_level = "caution"
        risk_explanation = (
            f"Found {len(direct_hits)} patent(s) directly referencing '{compound_name}' "
            f"and {len(related_hits)} with related mentions. Review patent claims carefully "
            f"to determine if your specific use case is covered."
        )
    elif related_hits:
        risk_level = "caution"
        risk_explanation = (
            f"Found {len(related_hits)} patents mentioning '{compound_name}' in their text. "
            f"While no direct title matches, the compound appears in patent contexts. "
            f"Review the specific claims for potential overlap."
        )
    else:
        risk_level = "clear"
        risk_explanation = (
            f"No patents found mentioning '{compound_name}' among {total_checked} SMA patents. "
            f"Note: this covers only patents in our database — a comprehensive FTO analysis "
            f"should also search USPTO, EPO, and WIPO databases directly."
        )

    return {
        "compound": compound_name,
        "risk_level": risk_level,
        "risk_explanation": risk_explanation,
        "total_patents_checked": total_checked,
        "matching_patents_count": len(matching),
        "direct_hits": len(direct_hits),
        "related_hits": len(related_hits),
        "matching_patents": matching,
    }


async def recent_patents(days_back: int = 365) -> list[dict[str, Any]]:
    """Retrieve the most recent patent filings, highlighting discovery target mentions.

    Args:
        days_back: How far back to look (default 365 days)

    Returns:
        List of recent patents with mechanism classification and target annotations.
    """
    # Load our discovery targets from the targets table
    target_rows = await fetch(
        "SELECT symbol FROM targets ORDER BY symbol"
    )
    db_targets = [dict(r)["symbol"] for r in target_rows] if target_rows else []
    # Combine with known SMA targets
    all_targets = list(set(SMA_DISCOVERY_TARGETS + db_targets))

    rows = await fetch(
        """SELECT id, external_id, title, abstract, pub_date, metadata, url
           FROM sources
           WHERE source_type = 'patent'
             AND pub_date >= CURRENT_DATE - $1 * INTERVAL '1 day'
           ORDER BY pub_date DESC""",
        days_back,
    )

    results = []
    for row in rows:
        p = dict(row)
        title = p.get("title", "") or ""
        abstract = p.get("abstract", "") or ""
        text = f"{title} {abstract}".lower()

        # Find which targets are mentioned
        targets_mentioned = [t for t in all_targets if t.lower() in text]

        mechanisms = _classify_mechanism(title, abstract)
        assignee = _extract_assignee(p.get("metadata"), title)

        results.append({
            "external_id": p["external_id"],
            "title": title,
            "pub_date": str(p.get("pub_date", "")),
            "url": p.get("url"),
            "mechanisms": mechanisms,
            "assignee": assignee,
            "discovery_targets_mentioned": targets_mentioned,
            "highlights_our_targets": len(targets_mentioned) > 0,
        })

    return results
