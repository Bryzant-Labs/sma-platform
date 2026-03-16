# Researcher Outreach Emails — DRAFT

> Status: DRAFT — Review before sending. Personalize placeholders marked with [BRACKETS].
> Last updated: 2026-03-16


---

## Email 1: Columbia University — Patent JP2015512409A (4-AP for SMA)

**Target:** Corresponding PI behind patent JP2015512409A (4-Aminopyridine for SMA therapy, Columbia University)

**Subject:** Computational evidence for direct 4-AP/SMN2 binding — complementary to your patent work

---

Dear [Professor / Dr. LAST NAME],

I am writing regarding your patent (JP2015512409A) proposing 4-Aminopyridine as a therapeutic agent for Spinal Muscular Atrophy, filed through Columbia University. Your work identified 4-AP's potential in SMA based on its potassium channel blocking activity. I am reaching out because our computational analysis has produced a finding that may be relevant to the mechanism you described.

I maintain an open-source SMA research platform (https://sma-research.info) that aggregates and cross-references published SMA literature, patents, and clinical trial data. As part of a virtual screening campaign, we ran DiffDock molecular docking of 4-AP against the SMN2 protein structure and observed a positive binding confidence score (+0.100). To our knowledge, direct 4-AP binding to SMN2 has not been previously reported in the literature. This would suggest a potential additional mechanism beyond potassium channel modulation — one that was not yet known when your patent was filed.

I should be transparent about the limitations: this is a computational prediction from a single docking tool, and it requires experimental validation before any biological conclusion can be drawn. It is also worth noting that the Phase II clinical trial NCT01645787 (testing 4-AP in SMA) did not meet its primary endpoint, though that trial was designed around the potassium channel hypothesis rather than a direct SMN2 interaction. If a direct binding mechanism exists, it could inform a re-evaluation of dosing, patient selection, or combination approaches.

I am a person living with SMA myself, and this platform is a personal research effort — non-commercial, licensed under AGPL-3.0. I would welcome the opportunity to share our computational data with your group. Specifically, I would be grateful for your assessment of whether this finding warrants experimental follow-up, and whether a binding assay (such as SPR or thermal shift) would be feasible in your laboratory.

The full docking results and evidence graph are publicly available at the link above, and the codebase is on GitHub (https://github.com/Bryzant-Labs/sma-platform). I am happy to provide the raw DiffDock output files or any additional data that would be useful for your review.

Thank you for your time and your foundational work on 4-AP in SMA.

Respectfully,

Christian Fischer
SMA Research Platform — https://sma-research.info
GitHub: https://github.com/Bryzant-Labs/sma-platform
[EMAIL ADDRESS]
[PHONE / LOCATION — Germany]


---

## Email 2: Cure SMA Foundation

**Target:** Research Team at Cure SMA (https://www.curesma.org)

**Subject:** Open-source AI research platform for SMA — built by a researcher with SMA

---

Dear Cure SMA Research Team,

I am writing to introduce an open-source research platform I have built for the SMA community. I have SMA myself, and this project grew out of a personal need to make sense of the rapidly expanding body of SMA research literature in a systematic, evidence-grounded way.

The SMA Research Platform (https://sma-research.info) is an AI-driven evidence synthesis tool that currently indexes over 24,500 structured claims extracted from 5,216 sources — including PubMed articles, 578 SMA patents, and 449 clinical trials from ClinicalTrials.gov. The platform generates cross-paper hypotheses by identifying non-obvious connections across papers that no single researcher would typically read together. It tracks 21 therapeutic targets, 16 drug candidates, and maintains a structured knowledge graph with 428 relationship edges across 34 relationship types. All data is traceable to its original source; every claim links back to the publication it was extracted from.

A recent virtual screening campaign using DiffDock molecular docking produced a lead finding: 4-Aminopyridine (an approved drug for multiple sclerosis) showed positive binding confidence to the SMN2 protein (+0.100). This potential direct SMN2 interaction has not been previously described in the literature — the prior clinical trial (NCT01645787) tested 4-AP in SMA based on its potassium channel mechanism, not protein binding. This is a computational prediction that needs experimental validation, but it illustrates the kind of novel hypothesis the platform can surface by systematically combining literature analysis with structural computation.

The platform is also available as an MCP server (Model Context Protocol) with 24 tools, meaning any researcher using an AI assistant can query our entire SMA knowledge base in natural language — for example, asking "What is the current evidence for PLS3 as a severity modifier in Type 2 patients?" and receiving a structured, source-linked answer drawn from thousands of papers. The full codebase is open-source under AGPL-3.0 on GitHub, and the evidence dataset is published on HuggingFace (SMAResearch/sma-evidence-graph).

I would appreciate the opportunity to bring this platform to Cure SMA's attention for three purposes: (1) awareness within your research network, so that SMA researchers can use the tool; (2) potential collaboration in connecting our computational findings — particularly the 4-AP/SMN2 lead — with wet-lab researchers who could perform experimental validation (e.g., surface plasmon resonance binding assay, splicing reporter assay); and (3) feedback from your scientific advisory team on how the platform could be most useful to the research community.

Thank you for the extraordinary work Cure SMA does for our community. I look forward to hearing from you.

Sincerely,

Christian Fischer
SMA Research Platform — https://sma-research.info
GitHub: https://github.com/Bryzant-Labs/sma-platform
HuggingFace: https://huggingface.co/SMAResearch
[EMAIL ADDRESS]
[PHONE / LOCATION — Germany]


---

## Email 3: European SMA Research Lab

**Target:** Institut de Myologie, Paris (Centre de Recherche en Myologie, Sorbonne Universite / INSERM) — or alternatively: Hannover Medical School (MHH), Institute of Neurogenetics (Prof. Peter Claus, SMA motor neuron biology group)

**Subject:** Open-source SMA evidence platform and a computational drug-target lead requiring experimental validation

---

Dear [Professor / Dr. LAST NAME],

I am writing from Germany to introduce an open-source SMA research platform and to explore the possibility of collaboration on experimental validation of a computational finding.

I have Spinal Muscular Atrophy myself, which is the personal motivation behind this project. The SMA Research Platform (https://sma-research.info) is a non-commercial, evidence-first tool that systematically synthesizes published SMA literature using AI. It currently contains over 24,500 structured claims extracted from 5,216 sources (PubMed, patents, and clinical trials), 468 generated hypotheses, and a knowledge graph spanning 21 therapeutic targets and 34 relationship types. The platform is open-source (AGPL-3.0) and the full evidence dataset is published on HuggingFace.

As part of a GPU-accelerated virtual screening campaign, we performed DiffDock molecular docking of 20 compounds against the SMN2 protein structure. One result stood out: 4-Aminopyridine (4-AP), an approved drug for multiple sclerosis, showed a positive binding confidence to SMN2 (+0.100). To our knowledge, direct 4-AP/SMN2 protein binding has not been reported in the literature. The previous Phase II trial of 4-AP in SMA (NCT01645787) was designed around potassium channel modulation and did not meet its primary endpoint — but direct SMN2 binding was not the hypothesized mechanism at that time. This is a computational prediction with clear limitations (single docking tool, no experimental confirmation), but the novelty of the finding and the fact that 4-AP is already an approved drug with a known safety profile make it worth investigating further.

The experiments that would be most informative for validating or refuting this prediction are: (1) a surface plasmon resonance (SPR) binding assay to confirm or rule out direct 4-AP/SMN2 physical interaction, and (2) an SMN2 splicing reporter assay to determine whether 4-AP affects exon 7 inclusion at concentrations consistent with the docked binding mode. [Your group's / The Institut de Myologie's] expertise in [SMA molecular biology / neuromuscular disease modeling / SMN2 splicing] would be ideally suited for this type of validation work. I would be glad to provide all computational data, docking output files, and full access to the platform's API and evidence graph.

I am not seeking funding or commercial partnership — only scientific collaboration to determine whether this computational lead has biological relevance. If there is interest, I would welcome a brief call or video meeting to discuss the data in more detail.

Thank you for your consideration and for your [group's] contributions to SMA research.

With best regards,

Christian Fischer
SMA Research Platform — https://sma-research.info
GitHub: https://github.com/Bryzant-Labs/sma-platform
HuggingFace: https://huggingface.co/SMAResearch
[EMAIL ADDRESS]
[LOCATION — Germany]


---

## Notes for Sending

- **Columbia (Email 1):** The patent JP2015512409A lists Columbia University as assignee. To identify the specific PI, search the patent's inventor list or check Columbia's Motor Neuron Center / Department of Neurology faculty pages. The patent may be associated with the groups of Darryl De Vivo or Umrao Monani, who have published on SMA therapeutics at Columbia.
- **Cure SMA (Email 2):** Send to research@curesma.org or via the contact form on curesma.org. Consider also reaching out to their Chief Scientific Officer directly if contact info is available.
- **European Lab (Email 3):** Two strong options:
  - **Institut de Myologie, Paris** — Largest European neuromuscular research center. Groups working on SMA gene therapy and molecular mechanisms.
  - **Hannover Medical School (MHH)** — Prof. Peter Claus leads a well-established SMA group focused on SMN protein biology and motor neuron development. Geographic proximity (also Germany) could simplify collaboration logistics.
  - **Alternative:** University of Edinburgh (SMA mouse models), University of Oxford (neuromuscular group), or Leiden University Medical Center (SMA clinical research).
- **Attachments to consider:** A one-page PDF summary of the platform + the 4-AP docking result (screenshot of DiffDock output, confidence score table) would strengthen all three emails.
- **Follow-up:** If no response within 2 weeks, send a brief follow-up referencing the original email.
