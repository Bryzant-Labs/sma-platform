# Researcher Feedback Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all 6 issues reported by Christian Simon (Leipzig University) before F2F meeting week of March 30.

**Architecture:** Backend changes to FastAPI routes + reasoning modules, DB migration for claim numbering, new chat endpoint with multi-turn RAG, frontend updates to the SPA index.html, and PubMed ingestion gap fixes run on moltbot.

**Tech Stack:** FastAPI, asyncpg, PostgreSQL, Anthropic Claude API, sentence-transformers, FAISS, Biopython, vanilla JS frontend

**Project root:** `/mnt/c/Users/bryza/Dropbox/Christian fischer/SMA/sma-platform/`

**Important:** Do NOT use `isolation: "worktree"` for SMA platform — path spaces break worktrees. Use general-purpose agents with `mode: "auto"`.

---

## Task 1: Add Mouse + Rat to Species Comparison

**Files:**
- Modify: `src/sma_platform/api/routes/comparative.py:22-33`
- Modify: `src/sma_platform/ingestion/adapters/orthologs.py:23-33`
- Modify: `frontend/index.html:4028-4034`

**Step 1: Add Mouse + Rat to backend species list**

In `src/sma_platform/api/routes/comparative.py`, replace lines 22-33:

```python
SPECIES_INFO = [
    {"id": "10090", "name": "Mouse", "scientific": "Mus musculus",
     "key_trait": "Primary SMA disease model, 90% of preclinical research"},
    {"id": "10116", "name": "Rat", "scientific": "Rattus norvegicus",
     "key_trait": "Pharmacokinetic and toxicology studies"},
    {"id": "8296", "name": "Axolotl", "scientific": "Ambystoma mexicanum",
     "key_trait": "Full spinal cord regeneration"},
    {"id": "7955", "name": "Zebrafish", "scientific": "Danio rerio",
     "key_trait": "Motor neuron regeneration"},
    {"id": "10181", "name": "Naked Mole Rat", "scientific": "Heterocephalus glaber",
     "key_trait": "Neurodegeneration resistance"},
    {"id": "6239", "name": "C. elegans", "scientific": "Caenorhabditis elegans",
     "key_trait": "SMN ortholog studies"},
    {"id": "7227", "name": "Drosophila", "scientific": "Drosophila melanogaster",
     "key_trait": "SMN loss-of-function models"},
]
```

**Step 2: Add Mouse + Rat to orthologs adapter**

In `src/sma_platform/ingestion/adapters/orthologs.py`, replace lines 23-33:

```python
MODEL_ORGANISMS = {
    "9606": "Homo sapiens",
    "10090": "Mus musculus",
    "10116": "Rattus norvegicus",
    "8296": "Ambystoma mexicanum",
    "7955": "Danio rerio",
    "10181": "Heterocephalus glaber",
    "6239": "Caenorhabditis elegans",
    "7227": "Drosophila melanogaster",
}

# Default species to search (excluding human)
DEFAULT_SPECIES = ["10090", "10116", "8296", "7955", "10181", "6239", "7227"]
```

**Step 3: Add Mouse + Rat to frontend SPECIES_INFO**

In `frontend/index.html`, find the SPECIES_INFO object (~line 4028) and add Mouse + Rat entries:

```javascript
var SPECIES_INFO = {
    'Mus musculus': {common: 'Mouse', desc: 'Primary SMA disease model'},
    'Rattus norvegicus': {common: 'Rat', desc: 'Pharmacokinetic studies'},
    'Ambystoma mexicanum': {common: 'Axolotl', desc: 'Spinal cord regeneration'},
    'Danio rerio': {common: 'Zebrafish', desc: 'Motor neuron regeneration'},
    'Heterocephalus glaber': {common: 'Naked Mole Rat', desc: 'Neurodegeneration resistance'},
    'Caenorhabditis elegans': {common: 'C. elegans', desc: 'SMN ortholog studies'},
    'Drosophila melanogaster': {common: 'Fruit Fly', desc: 'SMN loss-of-function models'}
};
```

**Step 4: Commit**

```bash
git add src/sma_platform/api/routes/comparative.py src/sma_platform/ingestion/adapters/orthologs.py frontend/index.html
git commit -m "feat: add Mouse + Rat to species comparison — fixes critical gap reported by researcher"
```

---

## Task 2: Add p53/SMA + Broader Ingestion Queries (Fixes 1 + 6)

**Files:**
- Modify: `src/sma_platform/ingestion/adapters/pubmed.py:42-160` (SMA_QUERIES list)

**Step 1: Add new PubMed queries**

In `src/sma_platform/ingestion/adapters/pubmed.py`, add these queries to the SMA_QUERIES list (after the existing cross-species section, before the list closes):

```python
    # --- p53 / apoptosis / cell death pathways (Christian Simon feedback) ---
    '"p53" AND ("spinal muscular atrophy" OR "SMA") AND "motor neuron"',
    '"TP53" AND "spinal muscular atrophy"',
    '"p53" AND "motor neuron" AND ("apoptosis" OR "cell death")',
    '"apoptosis" AND "spinal muscular atrophy" AND "motor neuron"',
    '"cell death" AND "spinal muscular atrophy"',
    '"caspase" AND ("SMA" OR "spinal muscular atrophy")',
    '"Bax" AND ("motor neuron" OR "spinal muscular atrophy")',
    '"Bcl-2" AND ("motor neuron" OR "spinal muscular atrophy")',

    # --- Broader gap-filling queries ---
    '"Schwann cell" AND "spinal muscular atrophy"',
    '"astrocyte" AND "spinal muscular atrophy"',
    '"glia" AND "spinal muscular atrophy" AND "motor neuron"',
    '"muscle pathology" AND "spinal muscular atrophy"',
    '"skeletal muscle" AND "spinal muscular atrophy" AND "atrophy"',
    '"SMA" AND "genotype phenotype correlation"',
    '"spinal muscular atrophy" AND "modifier gene"',

    # --- Simon / Schoeneberg lab papers ---
    '"Simon C" AND "spinal muscular atrophy"',
    '"Schoeneberg" AND ("SMA" OR "motor neuron")',
```

**Step 2: Commit**

```bash
git add src/sma_platform/ingestion/adapters/pubmed.py
git commit -m "feat: add p53/apoptosis, glial, muscle, and researcher-specific PubMed queries"
```

**Step 3: Run full historical ingestion on moltbot**

After deploying, SSH into moltbot and run a one-time backfill ingestion with a large days_back value to catch all historical papers. Run the new queries only (last 17 entries of SMA_QUERIES).

**Step 4: Run claim extraction on new papers**

On moltbot, run claim extraction for unprocessed sources (screen session, ~1-2 hours).

**Step 5: Verify p53 search works**

```bash
curl -s "http://localhost:8090/api/v2/search?q=p53+motor+neuron+death+SMA" | python3 -m json.tool | head -30
```

Expected: Results containing p53-related claims from Simon's research area.

---

## Task 3: Human-Readable Claim Numbers

**Files:**
- Create: `scripts/migrate_claim_numbers.py`
- Modify: `db/schema.sql:135-155` (add claim_number column)
- Modify: `src/sma_platform/api/routes/search.py:48-68` (include claim_number in enrichment)
- Modify: `src/sma_platform/api/routes/evidence.py:29-40` (include claim_number)
- Modify: `src/sma_platform/reasoning/research_assistant.py:106-122` (use CLAIM-XXXXX format)
- Modify: `frontend/index.html:4294-4327` (render claim_number)

**Step 1: Create migration script**

Create `scripts/migrate_claim_numbers.py`:

```python
"""Add claim_number SERIAL column to claims table and backfill existing rows."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute, fetch, init_pool


async def migrate():
    await init_pool(settings.database_url)

    # Step 1: Add the column (nullable first to avoid issues)
    print("Adding claim_number column...")
    await execute("""
        ALTER TABLE claims
        ADD COLUMN IF NOT EXISTS claim_number SERIAL
    """)

    # Step 2: Backfill sequential numbers ordered by created_at
    print("Backfilling claim numbers ordered by created_at...")
    await execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) AS rn
            FROM claims
        )
        UPDATE claims SET claim_number = numbered.rn
        FROM numbered WHERE claims.id = numbered.id
    """)

    # Step 3: Add unique constraint
    print("Adding unique constraint...")
    await execute("""
        ALTER TABLE claims
        ADD CONSTRAINT claims_claim_number_unique UNIQUE (claim_number)
    """)

    # Step 4: Update the sequence to start after the highest number
    row = await fetch("SELECT MAX(claim_number) AS max_num FROM claims")
    max_num = row[0]["max_num"] if row and row[0]["max_num"] else 0
    print(f"Max claim_number: {max_num}")
    await execute(f"SELECT setval(pg_get_serial_sequence('claims', 'claim_number'), {max_num})")

    # Step 5: Create index
    print("Creating index...")
    await execute("CREATE INDEX IF NOT EXISTS idx_claims_number ON claims(claim_number)")

    print("Migration complete!")
    await close_pool()


if __name__ == "__main__":
    asyncio.run(migrate())
```

**Step 2: Update schema.sql**

In `db/schema.sql`, add `claim_number` to the claims CREATE TABLE (line ~142):

```sql
    claim_number    SERIAL UNIQUE,               -- Human-readable ID (CLAIM-00001)
```

**Step 3: Update search enrichment to include claim_number**

In `src/sma_platform/api/routes/search.py`, update the claim query (~line 50-51) to SELECT claim_number and include it in the item dict.

**Step 4: Update evidence route to include claim_number**

In `src/sma_platform/api/routes/evidence.py`, add `c.claim_number` to the SELECT in `list_evidence`.

**Step 5: Update RAG assistant to use CLAIM-XXXXX format**

In `src/sma_platform/reasoning/research_assistant.py`:
- Update claim retrieval query to include `c.claim_number`
- Update `_format_context` to use `CLAIM-{claim_number:05d}` format instead of UUID
- Update SYSTEM_PROMPT to reference CLAIM-XXXXX format

**Step 6: Update frontend search results**

In `frontend/index.html`, add claim number display in search result cards. After the type badge, show `CLAIM-XXXXX` in monospace. Add CSS for `.sr-claim-id`.

**Step 7: Commit**

```bash
git add scripts/migrate_claim_numbers.py db/schema.sql src/sma_platform/api/routes/search.py src/sma_platform/api/routes/evidence.py src/sma_platform/reasoning/research_assistant.py frontend/index.html
git commit -m "feat: human-readable claim numbers (CLAIM-00001) replacing cryptic UUIDs"
```

**Step 8: Run migration on moltbot**

```bash
ssh moltbot "cd /home/bryzant/sma-platform && source venv/bin/activate && python3 scripts/migrate_claim_numbers.py"
```

---

## Task 4: AI Search Transparency

**Files:**
- Modify: `frontend/index.html:1483-1499` (search section)
- Modify: `frontend/index.html:1501-1522` (ask section)

**Step 1: Add methodology info to Search section**

In `frontend/index.html`, update the search section description (~line 1485) to include a `<details>` expandable with methodology explanation: hybrid search, sentence-transformers model, FAISS, data sources.

**Step 2: Add model attribution to Ask AI section**

In `frontend/index.html`, update the ask section description (~line 1503) to mention Claude Sonnet (Anthropic) and RAG.

**Step 3: Commit**

```bash
git add frontend/index.html
git commit -m "feat: add search methodology explanation and model attribution"
```

---

## Task 5: Conversational AI Chat Page

**Files:**
- Create: `src/sma_platform/api/routes/chat.py`
- Modify: `src/sma_platform/reasoning/research_assistant.py` (add `chat` function)
- Modify: `src/sma_platform/api/app.py:16,104` (import + register chat router)
- Modify: `src/sma_platform/api/app.py:193-204` (add "chat" to SECTION_SLUGS)
- Modify: `frontend/index.html` (add /chat nav link + section + JS)

### Step 1: Create chat route

Create `src/sma_platform/api/routes/chat.py` with:
- `POST /chat` endpoint accepting `{message, conversation_id?, history: [{role, content}]}`
- Pydantic models for request validation
- History limited to 10 exchanges
- Auto-generated conversation_id

### Step 2: Add chat function to research_assistant.py

Add `chat()` function after existing `ask()` function:
- Accepts message + history array
- Builds search query from current message + recent user context
- Retrieves evidence via hybrid search (same as ask)
- Constructs messages array with history + current message with evidence context
- Uses Claude Sonnet with CHAT_SYSTEM_PROMPT (includes rule 7: "This is a conversation — you can reference your previous answers")
- Extracts cited claim numbers and PMIDs from answer using regex
- Returns answer + conversation metadata

### Step 3: Register chat router in app.py

- Import `chat` in the routes import line
- Add `app.include_router(chat.router, prefix="/api/v2", tags=["chat"])`
- Add `"chat"` to SECTION_SLUGS set

### Step 4: Add chat section to frontend

**A. Nav link:** Add `/chat` link with `nav-highlight` class (move highlight from Ask AI)

**B. HTML section:** Full chat interface with:
- Messages area with welcome screen + suggestion buttons
- Input area with send button
- Status bar with exchange counter + "New conversation" button
- Suggestions: p53 in SMA, compare therapies, PLS3 modifier, NCALD role, emerging targets

**C. CSS:** Chat container (600px height), message bubbles (user=accent, AI=panel), input area styling

**D. JavaScript:**
- `loadChat()` — event listeners for send button, enter key, suggestion buttons
- `resetChat()` — clear history, reset UI
- `doChat()` — POST to /chat with message + history, render response
- Response rendering: bold text via regex, CLAIM-XXXXX as `<code>`, PMID as PubMed links
- **IMPORTANT: All dynamic HTML must be sanitized with DOMPurify before insertion**
- Exchange limit (10) with status display

### Step 5: Commit

```bash
git add src/sma_platform/api/routes/chat.py src/sma_platform/reasoning/research_assistant.py src/sma_platform/api/app.py frontend/index.html
git commit -m "feat: conversational AI chat page with multi-turn RAG — /chat section"
```

---

## Task 6: Deploy All Changes to Moltbot

**Step 1: Deploy code**

```bash
rsync -avz --exclude='venv' --exclude='__pycache__' --exclude='.git' --exclude='data' \
  src/ moltbot:/home/bryzant/sma-platform/src/
rsync -avz scripts/ moltbot:/home/bryzant/sma-platform/scripts/
rsync frontend/index.html moltbot:/var/www/sma-research.info/index.html
```

**Step 2: Run claim_number migration**

```bash
ssh moltbot "cd /home/bryzant/sma-platform && source venv/bin/activate && python3 scripts/migrate_claim_numbers.py"
```

**Step 3: Run p53/new query ingestion + claim extraction**

See Task 2, Steps 3-4 for the backfill commands.

**Step 4: Run ortholog ingestion for Mouse + Rat**

```bash
curl -s -X POST "http://localhost:8090/api/v2/comparative/ingest/orthologs" \
  -H "X-Admin-Key: sma-admin-2026"
```

**Step 5: Rebuild search index** (to include new claims)

```bash
curl -s -X POST "http://localhost:8090/api/v2/search/reindex" \
  -H "X-Admin-Key: sma-admin-2026"
```

**Step 6: Restart API**

```bash
ssh moltbot "pm2 restart sma-api"
```

**Step 7: Verify all fixes**

```bash
# p53 search works
curl -s "http://localhost:8090/api/v2/search?q=p53+motor+neuron+SMA"

# Mouse in species
curl -s "http://localhost:8090/api/v2/comparative/species"

# Claim numbers present
curl -s "http://localhost:8090/api/v2/search?q=SMN2+splicing&top_k=3"

# Chat endpoint works
curl -s -X POST "http://localhost:8090/api/v2/chat" -H "Content-Type: application/json" -d '{"message":"What is the role of p53 in SMA?"}'

# Site is up
curl -s -o /dev/null -w '%{http_code}' https://sma-research.info/
```

**Step 8: Final commit + push**

```bash
git push origin master
```
