-- Personal Digital Twin: patient profiles for admin-only personalized analysis
-- PRIVATE: Patient data — admin-only access, never expose publicly

CREATE TABLE IF NOT EXISTS patient_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_name TEXT NOT NULL DEFAULT 'default',
    sma_type TEXT,
    smn2_copies INTEGER,
    age_years INTEGER,
    age_at_diagnosis_months INTEGER,
    current_therapies JSONB DEFAULT '[]',
    therapy_history JSONB DEFAULT '[]',
    functional_scores JSONB DEFAULT '{}',
    biomarkers JSONB DEFAULT '{}',
    genetic_modifiers JSONB DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_patient_profiles_name ON patient_profiles(profile_name);
