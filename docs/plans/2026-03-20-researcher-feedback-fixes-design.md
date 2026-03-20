# Researcher Feedback Fixes — Design Document

> First external feedback from Christian Simon, PhD (Leipzig University, Carl-Ludwig-Institute for Physiology).
> Deadline: Week of March 30, 2026 (F2F meeting with Simon + Prof. Schöneberg).
> Approved: 2026-03-20

---

## Context

Christian Simon reviewed sma-research.info and reported 5 issues:

1. **p53/SMA literature missing** — his own research area (p53-induced motor neuron death) not found despite ~10+ publications
2. **Mouse (Mus musculus) absent** from species comparison — 90% of SMA animal research
3. **Claim IDs cryptic** — UUIDs like `#8c6da6be-...` meaningless to researchers
4. **AI search opaque** — no explanation of model or methodology
5. **No conversational follow-up** — wants chat-like interaction, not one-shot queries

Additionally, we identified:
6. **Broader ingestion gaps** — if p53 is missing, other pathways likely are too

---

## Fix 1: Ingest p53/SMA Literature

### Problem
PubMed has 37 papers for "p53 spinal muscular atrophy motor neuron" — zero ingested.

### Solution
- Add 4 new PubMed queries to ingestion pipeline:
  - `"p53 spinal muscular atrophy motor neuron"`
  - `"TP53 spinal muscular atrophy"`
  - `"apoptosis motor neuron spinal muscular atrophy"`
  - `"cell death pathway SMA motor neuron"`
- Run ingestion + claim extraction on moltbot
- Add **p53/TP53** as discovery target if sufficient evidence
- Verify: search for "p53 motor neuron" returns Simon's papers

### Files Changed
- `scripts/daily_ingest.py` or ingestion config (add queries)
- Database: new sources + claims rows

---

## Fix 2: Add Mouse + Rat to Species Comparison

### Problem
Species list designed for regenerative biology only. Missing primary SMA model organisms.

### Solution
- Add **Mus musculus** (NCBI taxon 10090) — key trait: "Primary SMA disease model"
- Add **Rattus norvegicus** (NCBI taxon 10116) — key trait: "Pharmacokinetic/toxicology studies"
- Update 3 locations:
  1. `src/sma_platform/api/routes/comparative.py` (SPECIES dict, lines 22-33)
  2. `src/sma_platform/ingestion/adapters/orthologs.py` (MODEL_ORGANISMS + DEFAULT_SPECIES, lines 23-33)
  3. `frontend/index.html` (SPECIES_INFO, lines 4028-4034)
- Run ortholog ingestion for new species
- Mouse should show near-complete conservation across all 21 targets

### Files Changed
- `src/sma_platform/api/routes/comparative.py`
- `src/sma_platform/ingestion/adapters/orthologs.py`
- `frontend/index.html`

---

## Fix 3: Human-Readable Claim Display

### Problem
Claims display as `#8c6da6be-b4ec-e55d-b6c6-076b3ea81c67` — meaningless to researchers.

### Solution
- Add `claim_number SERIAL` column to `claims` table
- Backfill existing 25,109 claims with sequential numbers (ordered by created_at)
- Display format: **`CLAIM-00001`** (zero-padded 5 digits)
- Search results show: claim text (bold) → source paper + PMID → claim type badge → CLAIM-XXXXX small
- RAG assistant cites as `[CLAIM-12345]` instead of UUID fragments
- UUID remains internal API identifier

### Files Changed
- `db/schema.sql` (add column)
- Migration script for backfill
- `src/sma_platform/api/routes/search.py` (include claim_number in results)
- `src/sma_platform/api/routes/evidence.py` (include claim_number)
- `src/sma_platform/reasoning/research_assistant.py` (update citation format)
- `frontend/index.html` (render claim_number instead of UUID)

---

## Fix 4: AI Search Transparency

### Problem
No explanation of how search works or what model powers AI answers.

### Solution
- Info panel below search bar:
  > "Hybrid semantic + keyword search across 25,000+ evidence claims and 5,200+ sources. AI answers powered by Claude (Anthropic)."
- Expandable "How it works" section: embedding model, FAISS index, hybrid scoring
- Surface model name in AI answer responses
- Link to METHODOLOGY.md

### Files Changed
- `frontend/index.html` (search section UI)

---

## Fix 5: Conversational AI Chat — `/chat` Page

### Problem
AI search is one-shot, no follow-up questions. Researcher wants conversation.

### Design

#### Backend
- New `POST /api/v2/chat` endpoint
  - Input: `{ message, conversation_id?, history: [{role, content}] }`
  - Output: `{ answer, sources_used: [], claims_cited: [], conversation_id, model }`
- Stateless server — conversation history sent from client each request
- Same hybrid search RAG pipeline as `/ask`
- LLM prompt includes last 5 exchanges for continuity
- Max 10 exchanges per conversation (cost guard)

#### Frontend
- New `/chat` section in SPA navigation (prominent position)
- Layout:
  - Main area: chat message stream (user bubbles + AI response cards)
  - Right sidebar: "Sources & Claims" panel for current answer
  - Bottom: input box with "Ask a follow-up question..." placeholder
- AI responses show inline `[CLAIM-12345]` citations, clickable to expand
- Each answer card shows: text, source count, model attribution
- Session-only persistence (localStorage for page refresh)
- "New conversation" button clears history

#### Route File
- New `src/sma_platform/api/routes/chat.py`

### Files Changed
- `src/sma_platform/api/routes/chat.py` (new)
- `src/sma_platform/reasoning/research_assistant.py` (add chat method with history)
- `src/sma_platform/api/app.py` (register chat router)
- `frontend/index.html` (new /chat section + navigation)

---

## Fix 6: Broader Ingestion Gap Audit

### Problem
If p53 is missing, other important SMA pathways likely are too.

### Solution
- Add queries for underrepresented topics:
  - `"apoptosis spinal muscular atrophy"`
  - `"autophagy SMA motor neuron"`
  - `"mitochondrial dysfunction spinal muscular atrophy"`
  - `"muscle pathology spinal muscular atrophy"` (peripheral, not just motor neuron)
  - `"neurofilament biomarker spinal muscular atrophy"`
  - `"SMA type phenotype genotype correlation"`
  - `"Schwann cell spinal muscular atrophy"`
  - `"astrocyte glia spinal muscular atrophy"`
- Cross-check Simon's + Schöneberg's PubMed publication lists
- Run full ingestion + claim extraction

### Files Changed
- `scripts/daily_ingest.py` or ingestion config
- Database: new sources + claims

---

## Implementation Order

1. **Fix 2** (Mouse + Rat) — smallest change, immediate visible impact
2. **Fix 1 + Fix 6** (Ingestion) — run in parallel on moltbot, takes time for claim extraction
3. **Fix 3** (Claim numbers) — DB migration + display changes
4. **Fix 4** (Search transparency) — quick frontend text
5. **Fix 5** (Chat page) — largest feature, build last

## Risks
- Claim extraction for 50+ new papers takes ~1-2 hours on moltbot (Claude Haiku API)
- Mouse ortholog ingestion depends on NCBI API availability
- Chat feature token costs — mitigated by exchange limit
