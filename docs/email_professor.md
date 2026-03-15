**Betreff:** SMA-Forschungsplattform — schau Dir das mal an, ich brauch Dein Feedback

---

Hi [NAME],

ich hoffe Dir geht's gut! Ich hab in den letzten Monaten an etwas gebaut, das ich Dir unbedingt zeigen wollte — eine Open-Source-Plattform, die die gesamte SMA-Forschungsevidenz automatisiert zusammenträgt, strukturiert und analysiert. Da Du selbst an SMA forschst, bist Du genau der Richtige, um mir zu sagen ob das Ding auch wirklich nützlich ist.

**Kurz was die Plattform macht:**

Die SMA Research Platform (https://sma-research.info) indexiert täglich automatisch neue Publikationen aus PubMed, bioRxiv/medRxiv und ClinicalTrials.gov. Aus den Abstracts extrahiert ein LLM (Claude) strukturierte wissenschaftliche Claims — aktuell über 22.600 Claims aus 4.582 Quellen — und ordnet diese 21 molekularen Targets und 16 Wirkstoffen zu.

Darauf aufbauend generiert die Plattform:

- **Mechanistische Hypothesenkarten** (220+) mit Evidenz-Konvergenz, Widersprüchen und experimentellen Vorschlägen
- **Auto-Discovery Signale** — automatische Erkennung von Claim-Spikes, Hypothesen-Konfirmationen und neuen Targets
- **Splice Variant Predictor** — Vorhersage der Auswirkungen von SMN2-Exon-7-Varianten auf Splicing (regelbasiert) und Proteinfunktion (ESM-2)
- **Computational Screening** — 21.228 gescreente Moleküle aus ChEMBL mit BBB-Permeabilität, CNS MPO, PAINS-Filter

Alles Open Source (MIT License), alle Daten offen auf HuggingFace, die REST-API hat ~155 Endpoints für programmatischen Zugriff.

**Warum ich Dich frage:**

Du weißt besser als ich, welche Fragen in der SMA-Forschung gerade wirklich offen sind. Ich würde mich mega freuen, wenn Du Dir die Plattform mal anschaust und mir sagst:

1. **Welche Datenquellen fehlen?** — Gibt es Datenbanken oder Register, die Du für Deine Arbeit brauchst?
2. **Welche Analysen wären nützlich?** — Z.B. spezifische Pathway-Analysen, Biomarker-Korrelationen, Genotyp-Phänotyp-Mappings?
3. **Welches Format hilft Dir?** — API für eigene Pipelines? CSV-Export? BibTeX? Andere Integrationen?
4. **Was fehlt inhaltlich?** — Gibt es Targets, Mechanismen oder Fragestellungen, die noch nicht abgedeckt sind?

Anbei eine Präsentation mit den technischen Details. Die Plattform ist live unter https://sma-research.info — die API-Docs unter https://sma-research.info/api/v2/docs.

Zeitlich bin ich flexibel — ob kurzer Call, Mail oder GitHub-Kommentar, alles passt.

Beste Grüße,
Christian

---

**Links:**
- Plattform: https://sma-research.info
- API Docs: https://sma-research.info/api/v2/docs
- GitHub: https://github.com/Bryzant-Labs/sma-platform
- HuggingFace: https://huggingface.co/datasets/SMAResearch/sma-evidence-graph
- Präsentation: (als Anhang beigefügt)
