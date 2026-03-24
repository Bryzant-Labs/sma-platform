"""PubMed adapter using NCBI E-utilities.

Searches PubMed for SMA-related papers and retrieves structured metadata.
Uses Biopython's Entrez module for reliable API access.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any

from Bio import Entrez

from ...core.config import settings

logger = logging.getLogger(__name__)

_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def _normalise_date(year: str, month: str, day: str) -> str | None:
    """Convert PubMed date parts to ISO YYYY-MM-DD, or None if unusable."""
    if not year or not year.isdigit():
        return None
    m = _MONTH_MAP.get(month.lower()[:3], month.zfill(2) if month.isdigit() else "01")
    d = day.zfill(2) if day.isdigit() else "01"
    return f"{year}-{m}-{d}"

# Configure Entrez
Entrez.email = settings.ncbi_email
Entrez.tool = settings.ncbi_tool
if settings.ncbi_api_key:
    Entrez.api_key = settings.ncbi_api_key

# Base SMA search queries
SMA_QUERIES = [
    # --- Original queries ---
    '"spinal muscular atrophy"',
    '"SMN1" OR "SMN2" AND "spinal muscular atrophy"',
    '"STMN2" AND ("motor neuron" OR "SMA")',
    '"nusinersen" OR "Spinraza"',
    '"risdiplam" OR "Evrysdi"',
    '"onasemnogene" OR "Zolgensma"',
    '"spinal muscular atrophy" AND ("gene therapy" OR "antisense oligonucleotide")',

    # --- MeSH-based queries ---
    '"Muscular Atrophy, Spinal"[MeSH]',
    '"Muscular Atrophy, Spinal"[MeSH] AND "Drug Therapy"[MeSH]',
    '"Muscular Atrophy, Spinal"[MeSH] AND "Genetic Therapy"[MeSH]',
    '"Muscular Atrophy, Spinal"[MeSH] AND "Biomarkers"[MeSH]',
    '"Motor Neurons"[MeSH] AND "Spinal Muscular Atrophy"[tiab]',
    '"Survival of Motor Neuron 1 Protein"[MeSH]',
    '"Survival of Motor Neuron 2 Protein"[MeSH]',

    # --- Protein and molecular target queries ---
    '"SMN protein" AND "spinal muscular atrophy"',
    '"SMN2 splicing" OR "SMN2 exon 7"',
    '"plastin 3" AND ("SMA" OR "spinal muscular atrophy")',
    '"STMN2" AND "SMN"',
    '"UBA1" AND ("SMA" OR "spinal muscular atrophy")',
    '"PLS3" AND ("SMA" OR "spinal muscular atrophy")',
    '"NCALD" AND ("SMA" OR "spinal muscular atrophy")',

    # --- Treatment-focused queries ---
    '"antisense oligonucleotide" AND "spinal muscular atrophy"',
    '"splicing modifier" AND "SMN2"',
    '"SMN-C" AND "spinal muscular atrophy"',
    '"branaplam" AND ("SMA" OR "spinal muscular atrophy")',
    '"SRK-015" OR "apitegromab" AND ("SMA" OR "spinal muscular atrophy")',
    '"gene replacement therapy" AND "spinal muscular atrophy"',
    '"AAV9" AND "spinal muscular atrophy"',
    '"exon skipping" AND "spinal muscular atrophy"',
    '"combination therapy" AND "spinal muscular atrophy"',

    # --- Biomarker queries ---
    '"neurofilament" AND ("SMA" OR "spinal muscular atrophy")',
    '"neurofilament light chain" AND "spinal muscular atrophy"',
    '"phosphorylated neurofilament heavy" AND "spinal muscular atrophy"',
    '"biomarker" AND "spinal muscular atrophy"',
    '"compound muscle action potential" AND "spinal muscular atrophy"',

    # --- Clinical and natural history ---
    '"spinal muscular atrophy" AND "natural history"',
    '"spinal muscular atrophy" AND "newborn screening"',
    '"spinal muscular atrophy" AND "presymptomatic"',
    '"spinal muscular atrophy" AND ("SMA type 1" OR "SMA type 2" OR "SMA type 3")',
    '"spinal muscular atrophy" AND "clinical trial"[pt]',
    '"spinal muscular atrophy" AND "outcome measure"',
    '"spinal muscular atrophy" AND "motor function"',
    '"spinal muscular atrophy" AND "CHOP INTEND"',
    '"spinal muscular atrophy" AND "HINE"',

    # --- Mechanism / basic science ---
    '"SMN" AND "axonal transport"',
    '"SMN" AND "mRNA splicing"',
    '"SMN complex" AND "snRNP"',
    '"spinal muscular atrophy" AND "autophagy"',
    '"spinal muscular atrophy" AND "mitochondria"',
    '"spinal muscular atrophy" AND "neuromuscular junction"',
    '"spinal muscular atrophy" AND "mouse model"',

    # --- Additional modifier gene queries ---
    '"CORO1C" AND ("SMA" OR "spinal muscular atrophy")',
    '"coronin" AND ("SMA" OR "spinal muscular atrophy" OR "motor neuron")',
    '"CORO1C" AND "SMN"',
    '"mTOR" AND ("SMA" OR "spinal muscular atrophy")',
    '"mTOR pathway" AND "motor neuron"',
    '"rapamycin" AND ("SMA" OR "spinal muscular atrophy")',
    '"neurocalcin delta" AND ("SMA" OR "motor neuron")',
    '"NCALD" AND "SMN"',

    # --- Epidemiology and registry ---
    '"spinal muscular atrophy" AND "incidence" OR "prevalence"',
    '"spinal muscular atrophy" AND "registry"',
    '"spinal muscular atrophy" AND "quality of life"',
    '"spinal muscular atrophy" AND "caregiver"',

    # --- Discovery targets (TargetDiscovery_A omics convergence) ---
    '"CD44" AND ("SMA" OR "spinal muscular atrophy" OR "motor neuron degeneration")',
    '"CD44" AND ("motor neuron" OR "neuromuscular")',
    '"SULF1" AND ("SMA" OR "spinal muscular atrophy" OR "motor neuron")',
    '"SULF1" AND ("heparan sulfate" AND "neuron")',
    '"DNMT3B" AND ("SMA" OR "spinal muscular atrophy")',
    '"DNMT3B" AND ("SMN2" OR "epigenetic" AND "motor neuron")',
    '"ANK3" AND ("motor neuron" OR "axon" OR "node of Ranvier")',
    '"ankyrin-G" AND ("neuromuscular" OR "motor neuron")',
    '"GALNT6" AND ("SMA" OR "spinal muscular atrophy" OR "motor neuron")',
    '"GALNT6" AND ("glycosylation" AND "neuron")',
    '"LY96" OR "MD-2" AND ("neuroinflammation" OR "motor neuron")',
    '"LY96" AND ("TLR4" AND "neurodegeneration")',
    '"SPATA18" OR "MIEAP" AND ("mitochondria" AND "neuron")',
    '"SPATA18" AND ("mitochondrial quality" OR "motor neuron")',
    '"LDHA" AND ("SMA" OR "spinal muscular atrophy" OR "motor neuron")',
    '"lactate dehydrogenase" AND ("motor neuron" OR "SMA")',
    '"CAST" OR "calpastatin" AND ("SMA" OR "motor neuron" OR "neuroprotection")',
    '"calpain inhibitor" AND ("motor neuron" OR "neurodegeneration")',
    '"NEDD4L" AND ("SMA" OR "spinal muscular atrophy" OR "ubiquitin")',
    '"NEDD4L" AND ("motor neuron" OR "UBA1")',
    '"CTNNA1" OR "alpha-catenin" AND ("motor neuron" OR "neuromuscular")',
    '"CTNNA1" AND ("cytoskeleton" OR "cell adhesion" AND "neuron")',
    # --- Cross-species comparative biology (Querdenker) ---
    # Axolotl / Salamander
    '"axolotl" AND ("motor neuron" OR "spinal cord regeneration")',
    '"axolotl" AND ("SMN" OR "survival motor neuron")',
    '"salamander" AND "neural regeneration" AND "motor"',
    '"ambystoma mexicanum" AND ("neuron" OR "regeneration")',
    # Zebrafish
    '"zebrafish" AND ("motor neuron regeneration" OR "spinal cord repair")',
    '"zebrafish" AND ("SMN" OR "smn1" OR "smn2")',
    '"danio rerio" AND "motor neuron" AND ("regeneration" OR "development")',
    # Naked mole rat
    '"naked mole rat" AND ("neurodegeneration" OR "neuroprotection")',
    '"heterocephalus glaber" AND "neuron"',
    # C. elegans
    '"C. elegans" AND ("smn-1" OR "SMN" OR "motor neuron")',
    '"caenorhabditis elegans" AND "motor neuron" AND "degeneration"',
    # Drosophila
    '"drosophila" AND ("SMN" OR "Smn" OR "motor neuron")',
    '"drosophila" AND "spinal muscular atrophy"',
    # General comparative
    '"motor neuron regeneration" AND "model organism"',
    '"neural regeneration" AND ("comparative" OR "cross-species")',
    '"axon regeneration" AND "motor neuron" AND ("zebrafish" OR "axolotl")',
    # --- Cross-disease learning (Querdenker) ---
    # ALS (motor neuron disease overlap)
    '"amyotrophic lateral sclerosis" AND ("SMN" OR "STMN2" OR "motor neuron degeneration")',
    '"ALS" AND "SMA" AND ("motor neuron" OR "shared pathway")',
    '"TDP-43" AND ("STMN2" OR "motor neuron" OR "splicing")',
    '"SOD1" AND ("motor neuron" OR "neuroprotection") AND "therapy"',
    '"ALS" AND ("drug repurposing" OR "riluzole" OR "edaravone") AND "motor neuron"',
    # DMD (Duchenne — shared NMJ + gene therapy approaches)
    '"duchenne muscular dystrophy" AND ("neuromuscular junction" OR "NMJ")',
    '"DMD" AND ("exon skipping" OR "antisense oligonucleotide") AND "therapy"',
    '"duchenne" AND ("gene therapy" OR "AAV") AND "motor"',
    # SBMA (Kennedy disease — lower motor neuron)
    '"spinal bulbar muscular atrophy" AND "motor neuron"',
    '"Kennedy disease" AND ("motor neuron" OR "androgen receptor")',
    # Myasthenia Gravis (NMJ disease)
    '"myasthenia gravis" AND ("neuromuscular junction" OR "NMJ") AND "therapy"',
    '"myasthenia gravis" AND ("acetylcholine receptor" OR "complement") AND "treatment"',
    # CMT (axonal degeneration)
    '"Charcot-Marie-Tooth" AND ("axonal" OR "motor neuron" OR "neuropathy") AND "therapy"',
    # Friedreich Ataxia (mitochondrial neurodegeneration)
    '"Friedreich ataxia" AND ("mitochondria" OR "frataxin") AND "neurodegeneration"',
    # General cross-disease
    '"motor neuron disease" AND ("drug repurposing" OR "shared mechanism" OR "common pathway")',
    '"neuromuscular disease" AND ("gene therapy" OR "antisense") AND "clinical trial"',
    '"motor neuron" AND ("neuroprotection" OR "neurodegeneration") AND "therapeutic target"',
    # --- Querdenker: Bear Hibernation / Muscle Preservation ---
    '"hibernation" AND ("muscle preservation" OR "muscle atrophy" OR "muscle protection")',
    '"myosin ATPase" AND ("muscle atrophy" OR "disuse" OR "neuropathy")',
    '"torpor" AND ("skeletal muscle" OR "motor neuron" OR "neuroprotection")',
    '"hibernation" AND ("protein homeostasis" OR "proteostasis") AND "muscle"',
    '"bear" AND "muscle" AND ("atrophy resistance" OR "preservation")',
    '"SUMOylation" AND ("muscle" OR "motor neuron" OR "neuroprotection")',
    # --- Querdenker: Bioelectricity / Michael Levin ---
    '"bioelectric" AND ("regeneration" OR "morphogenetic" OR "patterning")',
    '"ion channel" AND ("muscle stem cell" OR "satellite cell" OR "regeneration")',
    '"membrane potential" AND ("regeneration" OR "morphogenesis") AND ("muscle" OR "neuron")',
    '"bioelectricity" AND ("motor neuron" OR "neuromuscular")',
    '"gap junction" AND ("regeneration" OR "motor neuron")',
    '"Vmem" AND ("patterning" OR "regeneration" OR "development")',
    # --- Querdenker: Epigenetic Dimming / dCas9 ---
    '"dCas9" AND ("epigenetic" OR "gene silencing" OR "CRISPRi")',
    '"FSHD" AND "DUX4" AND ("epigenetic silencing" OR "repression")',
    '"epigenetic silencing" AND ("neuromuscular" OR "motor neuron" OR "muscle")',
    '"CRISPRi" AND ("motor neuron" OR "neuromuscular disease")',
    '"chromatin remodeling" AND ("SMN2" OR "spinal muscular atrophy")',
    '"histone modification" AND ("motor neuron" OR "SMA")',
    # --- Querdenker: ECM / Matrix Engineering ---
    '"extracellular matrix" AND "muscle fibrosis" AND ("therapy" OR "reversal")',
    '"fibrosis" AND "muscle regeneration" AND ("treatment" OR "reversal")',
    '"decellularized matrix" AND ("muscle" OR "neuromuscular")',
    '"matrix metalloproteinase" AND ("neuromuscular" OR "motor neuron")',
    '"ECM" AND ("muscle stem cell" OR "satellite cell") AND "regeneration"',
    '"collagen" AND ("neuromuscular junction" OR "NMJ") AND "remodeling"',
    # --- Querdenker: Cross-Species Proteomics / Splicing ---
    '"axolotl" AND "proteomics" AND "regeneration"',
    '"splicing" AND "regeneration" AND ("cross-species" OR "comparative")',
    '"alternative splicing" AND ("axolotl" OR "zebrafish") AND "regeneration"',
    '"spatial transcriptomics" AND ("motor neuron" OR "spinal cord")',
    '"single cell" AND "proteomics" AND ("motor neuron" OR "neuromuscular")',
    '"regeneration" AND "proteome" AND ("salamander" OR "axolotl" OR "zebrafish")',
    # --- Harvard-Level: Spatial Multi-Omics ---
    '"spatial transcriptomics" AND ("skeletal muscle" OR "neuromuscular")',
    '"Slide-seq" AND ("muscle" OR "neuron" OR "regeneration")',
    '"MERFISH" AND ("motor neuron" OR "spinal cord" OR "muscle")',
    '"spatial omics" AND ("drug delivery" OR "tissue niche" OR "muscle")',
    '"spatial gene expression" AND ("neuromuscular junction" OR "motor neuron")',
    '"niche" AND "drug resistance" AND ("muscle" OR "neuromuscular")',
    # --- Harvard-Level: NMJ-on-a-Chip / Organ-on-Chip ---
    '"organ-on-a-chip" AND ("neuromuscular" OR "motor neuron" OR "NMJ")',
    '"microphysiological system" AND ("neuromuscular" OR "motor neuron")',
    '"extracellular vesicle" AND ("neuromuscular junction" OR "motor neuron")',
    '"exosome" AND ("motor neuron" OR "NMJ" OR "spinal muscular atrophy")',
    '"retrograde signaling" AND ("neuromuscular junction" OR "motor neuron")',
    '"muscle-derived" AND ("neuroprotection" OR "motor neuron" OR "trophic factor")',
    '"muscle" AND "nerve" AND "retrograde" AND ("signaling" OR "communication")',
    # --- Harvard-Level: Atrofish / NDRG1 / Survivorship ---
    '"NDRG1" AND ("motor neuron" OR "muscle" OR "stress response")',
    '"NDRG1" AND ("neuroprotection" OR "cell survival" OR "apoptosis")',
    '"zebrafish" AND "muscle atrophy" AND "model"',
    '"atrophy" AND "survival" AND ("motor neuron" OR "muscle cell")',
    '"cell dormancy" AND ("neuroprotection" OR "motor neuron")',
    '"quiescence" AND ("motor neuron" OR "muscle stem cell") AND "survival"',
    # --- Harvard-Level: SMA as Multisystem Disease ---
    '"spinal muscular atrophy" AND ("liver" OR "hepatic" OR "metabolism")',
    '"spinal muscular atrophy" AND ("multisystem" OR "multi-organ" OR "systemic")',
    '"SMN" AND ("liver" OR "hepatocyte" OR "metabolic")',
    '"spinal muscular atrophy" AND ("fatty acid" OR "lipid metabolism")',
    '"SMA" AND ("energy metabolism" OR "mitochondrial dysfunction") AND "systemic"',
    # --- Harvard-Level: Bioelectric Patches / Electroceuticals ---
    '"electroceutical" AND ("muscle" OR "nerve" OR "regeneration")',
    '"electrical stimulation" AND ("satellite cell" OR "muscle stem cell")',
    '"electrical stimulation" AND ("motor neuron" OR "neuromuscular") AND "regeneration"',
    '"bioelectric patch" AND ("muscle" OR "nerve")',
    '"functional electrical stimulation" AND "spinal muscular atrophy"',
    # --- Querdenker: RNA Decoy / Sponge Strategy ---
    '"RNA decoy" AND ("splicing" OR "spliceosome")',
    '"hnRNP A1" AND ("SMN2" OR "exon 7" OR "spinal muscular atrophy")',
    '"splicing factor" AND "decoy" AND ("motor neuron" OR "neuromuscular")',
    '"RNA sponge" AND ("splicing" OR "gene regulation")',
    # --- Querdenker: Mitochondrial Overdrive / PGC-1alpha ---
    '"PGC-1alpha" AND ("motor neuron" OR "neurodegeneration" OR "neuroprotection")',
    '"mitochondrial biogenesis" AND ("motor neuron" OR "spinal muscular atrophy")',
    '"bioenergetic" AND ("motor neuron" OR "neuroprotection" OR "rescue")',
    '"NAD+" AND ("motor neuron" OR "neurodegeneration" OR "neuroprotection")',
    # --- Querdenker: DUBTACs / Protein Stabilization ---
    '"DUBTAC" OR "deubiquitinase targeting chimera"',
    '"protein stabilization" AND ("SMN" OR "survival motor neuron")',
    '"deubiquitinase" AND ("SMN" OR "motor neuron")',
    '"USP" AND ("SMN protein" OR "spinal muscular atrophy")',
    '"PROTAC" AND ("neurodegeneration" OR "motor neuron")',
    # --- Querdenker: Mechanotransduction ---
    '"mechanotransduction" AND ("motor neuron" OR "muscle" OR "neuroprotection")',
    '"vibration" AND ("muscle" OR "motor neuron") AND ("therapy" OR "regeneration")',
    '"mechanical stimulation" AND ("chaperone" OR "HSP" OR "protein stability")',
    # --- Querdenker: Microbiome / Engineered Probiotics ---
    '"microbiome" AND ("motor neuron" OR "neurodegeneration" OR "neuroprotection")',
    '"gut-brain axis" AND ("motor neuron" OR "neuromuscular")',
    '"engineered probiotic" AND ("neurodegeneration" OR "neuroprotection")',
    '"butyrate" AND ("SMN2" OR "HDAC" OR "motor neuron")',
    # --- Querdenker: Naked Mole Rat / HMM-HA ---
    '"naked mole rat" AND ("hyaluronic acid" OR "hyaluronan")',
    '"high molecular weight hyaluronic acid" AND ("neuroprotection" OR "cytoprotection")',
    '"HAS2" AND ("longevity" OR "neuroprotection")',
    # --- Verified: Axolotl Regeneration Molecular Switch ---
    '"c-Fos" AND "JunB" AND ("regeneration" OR "glial scar")',
    '"miR-200a" AND ("regeneration" OR "spinal cord")',
    '"ERK" AND "sustained" AND ("regeneration" OR "reprogramming") AND "muscle"',
    '"ependymoglial" AND ("regeneration" OR "spinal cord")',
    # --- Verified: Spinal Cord Stimulation in SMA (Simon/Capogrosso) ---
    '"spinal cord stimulation" AND "spinal muscular atrophy"',
    '"epidural stimulation" AND ("motor neuron" OR "SMA" OR "spinal muscular atrophy")',
    '"spinal cord stimulation" AND "motor neuron disease"',
    '"proprioception" AND "spinal muscular atrophy"',
    '"sensory motor" AND "spinal muscular atrophy" AND "circuit"',
    '"H-reflex" AND ("SMA" OR "spinal muscular atrophy")',
    '"Capogrosso" AND "spinal cord stimulation"',

    # --- p53 / apoptosis / cell death pathways (Simon feedback, 2026-03-20) ---
    '"p53" AND ("spinal muscular atrophy" OR "SMA") AND "motor neuron"',
    '"TP53" AND "spinal muscular atrophy"',
    '"p53" AND "motor neuron" AND ("apoptosis" OR "cell death")',
    '"apoptosis" AND "spinal muscular atrophy" AND "motor neuron"',
    '"cell death" AND "spinal muscular atrophy"',
    '"caspase" AND ("SMA" OR "spinal muscular atrophy")',
    '"Bax" AND ("motor neuron" OR "spinal muscular atrophy")',
    '"Bcl-2" AND ("motor neuron" OR "spinal muscular atrophy")',

    # --- Broader gap-filling queries (2026-03-20) ---
    '"Schwann cell" AND "spinal muscular atrophy"',
    '"astrocyte" AND "spinal muscular atrophy"',
    '"glia" AND "spinal muscular atrophy" AND "motor neuron"',
    '"muscle pathology" AND "spinal muscular atrophy"',
    '"skeletal muscle" AND "spinal muscular atrophy" AND "atrophy"',
    '"SMA" AND "genotype phenotype correlation"',
    '"spinal muscular atrophy" AND "modifier gene"',

    # --- Simon / Schoeneberg lab papers (2026-03-20) ---
    '"Simon C" AND "spinal muscular atrophy"',
    '"Schoeneberg" AND ("SMA" OR "motor neuron")',

    # --- Actin cytoskeleton targets (2026-03-24, underrepresented) ---
    '"ACTG1" AND "motor neuron"',
    '"ACTR2" AND "neurodegeneration"',
    '"ABI2" AND "actin" AND "neuron"',
    '"cofilin-2" AND "motor neuron"',
    '"CFL2" AND "spinal cord"',
    '"LIMK1" AND "neurodegeneration"',
    '"LIMK inhibitor" AND "neuron"',
    '"profilin-1" AND "ALS"',
    '"PFN1" AND "motor neuron"',
    '"actin rod" AND "neurodegenerative"',
    '"cofilin rod" AND "disease"',

    # --- Selective vulnerability & non-neuronal cells (2026-03-24) ---
    '"proprioceptive" AND "SMA"',
    '"Ia afferent" AND "spinal muscular atrophy"',
    '"selective vulnerability" AND "motor neuron" AND "SMA"',
    '"astrocyte" AND "SMA" AND "spinal muscular atrophy"',
    '"microglia" AND "SMA" AND "motor neuron"',

    # --- ROCK / Fasudil pathway (2026-03-24) ---
    '"ROCK inhibitor" AND "motor neuron disease"',
    '"Fasudil" AND "neurodegeneration"',
    '"ROCK inhibitor" AND "motor neuron"',
    '"fasudil" AND "motor neuron disease"',
    '"fasudil" AND ("ALS" OR "spinal muscular atrophy")',
    '"LIMK2" AND ("kinase" OR "neurodegeneration")',
    '"LIMK2" AND ("motor neuron" OR "spinal muscular atrophy")',
    '"ROCK-LIMK" AND ("actin" OR "SMA" OR "motor neuron")',
    '"ROCK" AND "LIMK" AND "actin" AND "spinal muscular atrophy"',
    '"H-1152" AND ("ROCK" OR "kinase")',
    '"H-1152" AND ("motor neuron" OR "neurodegeneration")',
    '"cofilin phosphorylation" AND "neurodegeneration"',
    '"cofilin phosphorylation" AND ("motor neuron" OR "spinal muscular atrophy")',
    '"actin dynamics" AND "spinal muscular atrophy"',
    '"actin dynamics" AND "motor neuron disease"',
    '"PFN2" AND ("profilin" OR "motor neuron")',
    '"PFN2" AND ("neurodegeneration" OR "spinal muscular atrophy")',
    '"profilin-2" AND ("motor neuron" OR "neurodegeneration")',

    # --- Underlinked modifier targets (2026-03-24) ---
    '"STMN2" AND "stathmin" AND "motor neuron"',
    '"NCALD" AND "neurocalcin" AND "SMA"',
    '"PLS3" AND "plastin" AND "modifier" AND "SMA"',
]


async def _entrez_search(
    query: str,
    max_results: int,
    min_date: str = "",
    max_date: str = "",
) -> list[str]:
    """Run Entrez search in a thread to avoid blocking the event loop."""
    def _search() -> list[str]:
        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "usehistory": "y",
        }
        if min_date:
            params["mindate"] = min_date
            params["maxdate"] = max_date
            params["datetype"] = "pdat"
        handle = Entrez.esearch(**params)
        record = Entrez.read(handle)
        handle.close()
        return record.get("IdList", [])

    return await asyncio.to_thread(_search)


async def _entrez_fetch(pmids: list[str]) -> list:
    """Run Entrez fetch in a thread to avoid blocking the event loop."""
    def _fetch() -> list:
        handle = Entrez.efetch(
            db="pubmed", id=",".join(pmids), rettype="xml", retmode="xml"
        )
        records = Entrez.read(handle)
        handle.close()
        return records.get("PubmedArticle", [])

    return await asyncio.to_thread(_fetch)


async def search_pubmed(
    query: str,
    max_results: int = 100,
    min_date: str | None = None,
    max_date: str | None = None,
) -> list[str]:
    """Search PubMed and return list of PMIDs.

    Args:
        query: PubMed search query
        max_results: Maximum number of results
        min_date: Minimum date (YYYY/MM/DD)
        max_date: Maximum date (YYYY/MM/DD)

    Returns:
        List of PMID strings
    """
    pmids = await _entrez_search(
        query=query,
        max_results=max_results,
        min_date=min_date or "",
        max_date=max_date or "",
    )
    logger.info("PubMed search '%s...' returned %d results", query[:60], len(pmids))
    return pmids


async def fetch_paper_details(pmids: list[str]) -> list[dict[str, Any]]:
    """Fetch detailed metadata for a list of PMIDs.

    Returns list of dicts with: pmid, title, authors, journal, pub_date, doi, abstract
    """
    if not pmids:
        return []

    raw_articles = await _entrez_fetch(pmids)

    papers = []
    for article in raw_articles:
        medline = article.get("MedlineCitation", {})
        art = medline.get("Article", {})

        # Extract PMID
        pmid = str(medline.get("PMID", ""))

        # Extract authors
        author_list = art.get("AuthorList", [])
        authors = []
        for a in author_list:
            last = a.get("LastName", "")
            first = a.get("ForeName", "")
            if last:
                authors.append(f"{last} {first}".strip())

        # Extract pub date
        pub_date_raw = art.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
        year = pub_date_raw.get("Year", "")
        month = pub_date_raw.get("Month", "01")
        day = pub_date_raw.get("Day", "01")

        # Extract DOI
        doi = ""
        for eid in art.get("ELocationID", []):
            if str(eid.attributes.get("EIdType", "")) == "doi":
                doi = str(eid)

        # Extract abstract
        abstract_parts = art.get("Abstract", {}).get("AbstractText", [])
        abstract = " ".join(str(p) for p in abstract_parts)

        papers.append({
            "pmid": pmid,
            "title": str(art.get("ArticleTitle", "")),
            "authors": authors,
            "journal": art.get("Journal", {}).get("Title", ""),
            "pub_date": _normalise_date(year, month, day),
            "doi": doi,
            "abstract": abstract,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })

    logger.info(f"Fetched details for {len(papers)}/{len(pmids)} papers")
    return papers


async def search_recent_sma(days_back: int = 7, max_per_query: int = 50) -> list[dict[str, Any]]:
    """Search all SMA queries for recent papers.

    This is the main daily ingestion entry point.
    """
    today = date.today()
    from datetime import timedelta
    min_date = (today - timedelta(days=days_back)).strftime("%Y/%m/%d")
    max_date = today.strftime("%Y/%m/%d")

    all_pmids: set[str] = set()
    for query in SMA_QUERIES:
        pmids = await search_pubmed(query, max_results=max_per_query, min_date=min_date, max_date=max_date)
        all_pmids.update(pmids)
        # NCBI rate limit: 3 req/sec without API key, 10 req/sec with key
        await asyncio.sleep(0.35)

    logger.info(f"Total unique PMIDs from {len(SMA_QUERIES)} queries: {len(all_pmids)}")

    if not all_pmids:
        return []

    return await fetch_paper_details(list(all_pmids))
