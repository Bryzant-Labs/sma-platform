-- Spatial Multi-Omics Tables (Migration 012)
-- Migrates hardcoded SPINAL_ZONES and drug penetration data from spatial_omics.py to PostgreSQL.

-- Spinal cord anatomical zones with drug accessibility scores
CREATE TABLE IF NOT EXISTS spatial_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_key TEXT UNIQUE NOT NULL,              -- machine key (e.g. 'ventral_horn')
    zone_name TEXT NOT NULL,                   -- human name (e.g. 'Ventral Horn')
    anatomical_region TEXT NOT NULL,
    cell_types TEXT[] NOT NULL DEFAULT '{}',
    bbb_score FLOAT NOT NULL CHECK (bbb_score BETWEEN 0 AND 1),   -- BBB permeability 0-1
    csf_score FLOAT NOT NULL CHECK (csf_score BETWEEN 0 AND 1),   -- CSF exposure 0-1
    vascular_score FLOAT NOT NULL CHECK (vascular_score BETWEEN 0 AND 1),  -- vascular density 0-1
    sma_relevance FLOAT NOT NULL CHECK (sma_relevance BETWEEN 0 AND 1),
    drug_access TEXT,                          -- qualitative summary
    clinical_relevance TEXT,                   -- description / clinical note
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spatial_zones_key ON spatial_zones(zone_key);
CREATE INDEX IF NOT EXISTS idx_spatial_zones_relevance ON spatial_zones(sma_relevance DESC);

-- Drug penetration profiles per zone (pre-computed or cached)
CREATE TABLE IF NOT EXISTS spatial_drug_penetration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drug_name TEXT NOT NULL,
    route TEXT NOT NULL CHECK (route IN ('intrathecal', 'oral', 'iv', 'aav', 'other')),
    molecular_weight FLOAT,
    logp FLOAT,
    drug_type TEXT,                            -- ASO, small_molecule, gene_therapy, etc.
    zone_scores JSONB NOT NULL DEFAULT '{}',   -- {zone_key: 0.0-1.0}
    best_zone TEXT,
    worst_zone TEXT,
    mechanism TEXT,
    bbb_crossing BOOLEAN GENERATED ALWAYS AS (
        (zone_scores->>'ventral_horn')::FLOAT > 0.4
    ) STORED,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(drug_name, route)
);

CREATE INDEX IF NOT EXISTS idx_spatial_drug_route ON spatial_drug_penetration(route);
CREATE INDEX IF NOT EXISTS idx_spatial_drug_name ON spatial_drug_penetration(drug_name);
CREATE INDEX IF NOT EXISTS idx_spatial_drug_bbb ON spatial_drug_penetration(bbb_crossing);

-- -------------------------------------------------------------------
-- Seed: Spinal Cord Zones
-- -------------------------------------------------------------------
INSERT INTO spatial_zones (zone_key, zone_name, anatomical_region, cell_types, bbb_score, csf_score, vascular_score, sma_relevance, drug_access, clinical_relevance) VALUES
(
    'ventral_horn',
    'Ventral Horn',
    'Gray matter, ventral',
    ARRAY['alpha motor neurons', 'gamma motor neurons', 'interneurons', 'astrocytes', 'microglia'],
    0.35, 0.50, 0.70, 1.0,
    'Moderate BBB barrier; reached well by IT drugs (nusinersen) and oral risdiplam',
    'PRIMARY SMA target zone. Contains alpha motor neurons (the cells that die in SMA). Lamina VIII-IX. Most vulnerable region — motor neuron loss is the hallmark of SMA.'
),
(
    'dorsal_horn',
    'Dorsal Horn',
    'Gray matter, dorsal',
    ARRAY['sensory neurons', 'interneurons', 'astrocytes', 'microglia'],
    0.30, 0.55, 0.60, 0.25,
    'Moderate CSF exposure; accessible to IT delivery',
    'Sensory processing region. Relatively spared in SMA but sensory deficits reported in severe cases. Lamina I-VI.'
),
(
    'central_canal',
    'Central Canal / Ependymal Zone',
    'Central gray matter',
    ARRAY['ependymal cells', 'neural stem cells', 'CSF-contacting neurons'],
    0.20, 1.0, 0.40, 0.30,
    'Highest CSF exposure — primary target for intrathecal delivery',
    'Highest CSF exposure — best reached by intrathecal drugs (nusinersen). Contains neural stem cell niche. Potential for endogenous repair.'
),
(
    'white_matter',
    'White Matter Tracts',
    'Peripheral white matter',
    ARRAY['oligodendrocytes', 'astrocytes', 'myelinated axons'],
    0.25, 0.30, 0.45, 0.40,
    'Poor drug access; therapeutic silent zone for current therapies',
    'Motor axon tracts. Axonal degeneration occurs in SMA. White matter pathology may precede motor neuron death.'
),
(
    'drg',
    'Dorsal Root Ganglia',
    'Peripheral (outside CNS)',
    ARRAY['sensory neurons', 'satellite glia'],
    0.80, 0.15, 0.75, 0.20,
    'Outside BBB — highly accessible to systemic drugs; DRG toxicity concern for AAV9',
    'Outside BBB — accessible to systemic drugs. DRG toxicity is a concern for AAV9 gene therapy (dorsal root ganglion pathology in NHP studies).'
),
(
    'nmj',
    'Neuromuscular Junction',
    'Peripheral (muscle)',
    ARRAY['motor neuron terminal', 'muscle fiber', 'terminal Schwann cells'],
    1.0, 0.0, 0.65, 0.85,
    'No BBB — fully accessible to systemic drugs',
    'CRITICAL SMA zone. NMJ denervation is an early event in SMA, often preceding motor neuron death. Accessible to systemic drugs (no BBB). Agrin/MuSK/rapsyn pathway is disrupted.'
)
ON CONFLICT (zone_key) DO NOTHING;

-- -------------------------------------------------------------------
-- Seed: Drug Penetration (pre-computed from _zone_accessibility logic)
-- -------------------------------------------------------------------
INSERT INTO spatial_drug_penetration (drug_name, route, molecular_weight, logp, drug_type, zone_scores, best_zone, worst_zone, mechanism, notes) VALUES
(
    'Nusinersen (Spinraza)',
    'intrathecal',
    7501,
    -5,
    'ASO',
    '{"ventral_horn": 0.70, "dorsal_horn": 0.74, "central_canal": 1.00, "white_matter": 0.54, "drg": 0.42, "nmj": 0.30}'::JSONB,
    'central_canal',
    'nmj',
    'Antisense oligonucleotide — blocks hnRNPA1 repressor on SMN2 exon 7, restores full-length SMN protein',
    'Intrathecal delivery bypasses BBB. CSF exposure drives zone penetration. Clinical PK: 60-70% motor neuron engagement in ventral horn.'
),
(
    'Risdiplam (Evrysdi)',
    'oral',
    390,
    2.1,
    'small_molecule',
    '{"ventral_horn": 0.35, "dorsal_horn": 0.30, "central_canal": 0.20, "white_matter": 0.25, "drg": 0.80, "nmj": 1.00}'::JSONB,
    'nmj',
    'central_canal',
    'Small molecule SMN2 splicing modifier — distributes systemically including CNS and peripheral tissues',
    'Oral bioavailability. MW 390, logP 2.1 — good BBB penetration. Reaches both CNS and peripheral tissues (NMJ, DRG).'
),
(
    'Zolgensma (AAV9-SMN1)',
    'aav',
    4000000,
    0,
    'gene_therapy',
    '{"ventral_horn": 0.545, "dorsal_horn": 0.51, "central_canal": 0.44, "white_matter": 0.475, "drg": 0.86, "nmj": 1.00}'::JSONB,
    'nmj',
    'central_canal',
    'AAV9 vector delivers functional SMN1 gene — tropism for motor neurons; partially crosses BBB via IV in neonates',
    'AAV9 partially crosses BBB; IV in neonates, intrathecal in older patients. DRG toxicity observed in NHP studies.'
)
ON CONFLICT (drug_name, route) DO NOTHING;
