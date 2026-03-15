"""Multisystem SMA Module (Phase 7.4).

Models SMA as a multisystem disease beyond motor neuron degeneration.
Tracks liver, cardiac, metabolic, and vascular pathology that emerges
especially in severe SMA types and young patients.

References:
- Hamilton & Bhatt, Front Biosci 2013 (SMA multisystem pathology)
- Deguise & Bhatt, Rare Diseases 2021 (SMA hepatic & metabolic)
- Nery et al., Eur J Paed Neurol 2021 (cardiac involvement in SMA)
- Bowerman et al., Disease Models 2012 (metabolic defects in SMA)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Organ systems affected in SMA
# ---------------------------------------------------------------------------

@dataclass
class OrganSystem:
    """An organ system affected in SMA beyond motor neurons."""
    name: str
    organ: str
    sma_type_affected: str      # SMA1, SMA1-2, all, severe
    prevalence: float           # 0-1 fraction of patients affected
    severity: float             # 0-1 clinical impact
    smn_dependent: bool         # is the pathology SMN-dependent?
    biomarkers: list[str]
    mechanisms: list[str]
    clinical_features: list[str]
    therapeutic_implications: str


ORGAN_SYSTEMS = [
    OrganSystem(
        name="Hepatic Dysfunction",
        organ="Liver",
        sma_type_affected="SMA1",
        prevalence=0.70,
        severity=0.65,
        smn_dependent=True,
        biomarkers=["ALT", "AST", "fatty acid oxidation panel", "bile acids", "albumin"],
        mechanisms=[
            "Hepatic steatosis from impaired fatty acid oxidation",
            "Reduced hepatocyte SMN → aberrant RNA splicing in liver",
            "Glycogen storage defect (fasting hypoglycemia)",
            "Mitochondrial dysfunction in hepatocytes",
        ],
        clinical_features=[
            "Fasting hypoglycemia (can be severe, life-threatening)",
            "Hepatomegaly",
            "Fatty liver (steatosis on ultrasound)",
            "Metabolic acidosis during illness",
        ],
        therapeutic_implications="Systemic SMN restoration (risdiplam, Zolgensma) addresses liver. "
                                "Nusinersen (intrathecal) does NOT reach liver — metabolic monitoring essential.",
    ),
    OrganSystem(
        name="Cardiac Pathology",
        organ="Heart",
        sma_type_affected="SMA1",
        prevalence=0.60,
        severity=0.55,
        smn_dependent=True,
        biomarkers=["Troponin I", "BNP", "echocardiography", "ECG (bradycardia)"],
        mechanisms=[
            "Cardiac autonomic dysfunction (sympathetic denervation)",
            "Structural heart defects (septal defects in severe SMA1)",
            "Cardiomyocyte SMN deficiency → splicing defects",
            "Bradycardia from autonomic imbalance",
        ],
        clinical_features=[
            "Bradycardia (most common cardiac finding)",
            "Septal defects (ASD/VSD in severe SMA1)",
            "Reduced cardiac output",
            "Autonomic dysregulation",
        ],
        therapeutic_implications="Cardiac monitoring recommended in SMA1. Gene therapy (systemic AAV9) "
                                "transduces cardiomyocytes. Risdiplam oral also reaches heart.",
    ),
    OrganSystem(
        name="Metabolic Dysregulation",
        organ="Systemic metabolism",
        sma_type_affected="all",
        prevalence=0.55,
        severity=0.50,
        smn_dependent=True,
        biomarkers=["Glucose", "Insulin", "Lipid panel", "Acylcarnitines", "Lactate"],
        mechanisms=[
            "Impaired fatty acid beta-oxidation (mitochondrial)",
            "Dyslipidemia (abnormal cholesterol metabolism)",
            "Insulin resistance (even in non-obese SMA patients)",
            "Increased energy expenditure relative to muscle mass",
            "Altered amino acid metabolism",
        ],
        clinical_features=[
            "Dyslipidemia (elevated triglycerides, low HDL)",
            "Insulin resistance",
            "Fasting intolerance",
            "Abnormal body composition (high fat, low lean mass)",
            "Metabolic acidosis in acute illness",
        ],
        therapeutic_implications="Metabolic support alongside SMN therapy. Potential for metformin "
                                "(insulin sensitizer + AMPK activator). Dietary management critical.",
    ),
    OrganSystem(
        name="Pancreatic Defects",
        organ="Pancreas",
        sma_type_affected="SMA1-2",
        prevalence=0.40,
        severity=0.45,
        smn_dependent=True,
        biomarkers=["Insulin", "C-peptide", "Glucose tolerance test"],
        mechanisms=[
            "Beta-cell dysfunction (impaired insulin secretion)",
            "SMN deficiency in pancreatic progenitors",
            "Reduced islet mass in SMA mouse models",
        ],
        clinical_features=[
            "Glucose intolerance",
            "Reduced insulin secretion",
            "Potential progression to diabetes-like state",
        ],
        therapeutic_implications="Beta-cell support may be needed in treated SMA patients who survive "
                                "longer. GLP-1 agonists or insulin supplementation in severe cases.",
    ),
    OrganSystem(
        name="Vascular Defects",
        organ="Vasculature",
        sma_type_affected="SMA1",
        prevalence=0.35,
        severity=0.40,
        smn_dependent=True,
        biomarkers=["Digital necrosis (clinical)", "Capillary density", "VEGF levels"],
        mechanisms=[
            "Distal digital necrosis (finger/toe ischemia in SMA1)",
            "Reduced VEGF signaling in endothelium",
            "SMN-dependent vascular patterning defect",
            "Microvascular rarefaction",
        ],
        clinical_features=[
            "Digital necrosis (rare but pathognomonic for severe SMA)",
            "Poor peripheral perfusion",
            "Reduced capillary density in muscle",
        ],
        therapeutic_implications="Vascular pathology confirms SMA is systemic. Systemic SMN delivery "
                                "essential for these patients. VEGF support may help.",
    ),
    OrganSystem(
        name="Bone and Skeletal",
        organ="Skeleton",
        sma_type_affected="all",
        prevalence=0.80,
        severity=0.60,
        smn_dependent=False,
        biomarkers=["DEXA scan", "Vitamin D", "PTH", "Bone turnover markers"],
        mechanisms=[
            "Disuse osteoporosis from immobility",
            "Scoliosis from paraspinal muscle weakness",
            "Fractures from minimal trauma",
            "Possible SMN-independent osteoblast dysfunction",
        ],
        clinical_features=[
            "Scoliosis (progressive, often requiring surgery)",
            "Osteoporosis/osteopenia",
            "Pathological fractures",
            "Joint contractures",
        ],
        therapeutic_implications="Not directly addressed by SMN therapy. Requires orthopedic management, "
                                "bisphosphonates, vitamin D, physical therapy. Scoliosis surgery timing "
                                "important in treated SMA patients.",
    ),
    OrganSystem(
        name="Gastrointestinal",
        organ="GI tract",
        sma_type_affected="SMA1-2",
        prevalence=0.65,
        severity=0.50,
        smn_dependent=True,
        biomarkers=["Gastric emptying study", "pH probe", "Nutritional status"],
        mechanisms=[
            "Bulbar muscle weakness (swallowing difficulty)",
            "Gastric dysmotility (delayed emptying)",
            "Constipation from smooth muscle and autonomic dysfunction",
            "GERD from reduced esophageal motility",
        ],
        clinical_features=[
            "Dysphagia (swallowing difficulty)",
            "GERD (gastroesophageal reflux)",
            "Constipation",
            "Failure to thrive",
            "Aspiration risk",
        ],
        therapeutic_implications="Nutritional support critical. G-tube feeding common in SMA1. "
                                "Proton pump inhibitors for GERD. Prokinetics for gastric dysmotility.",
    ),
]


# ---------------------------------------------------------------------------
# Combination therapy model
# ---------------------------------------------------------------------------

@dataclass
class CombinationTherapy:
    """A combination therapy addressing both neuronal and systemic SMA."""
    name: str
    neuro_component: str
    systemic_component: str
    target_organs: list[str]
    rationale: str
    feasibility: float          # 0-1
    clinical_status: str


COMBINATION_THERAPIES = [
    CombinationTherapy(
        name="Risdiplam + Metformin",
        neuro_component="Risdiplam (oral SMN2 splicing modifier)",
        systemic_component="Metformin (AMPK activator, insulin sensitizer)",
        target_organs=["CNS", "Liver", "Pancreas", "Muscle"],
        rationale="Risdiplam restores SMN systemically. Metformin addresses metabolic dysfunction "
                 "(insulin resistance, mitochondrial deficiency) that persists even with SMN restoration.",
        feasibility=0.85,
        clinical_status="Conceptual — both drugs individually approved, combination not tested in SMA",
    ),
    CombinationTherapy(
        name="Nusinersen + Risdiplam (dual SMN)",
        neuro_component="Nusinersen (intrathecal ASO, high CNS levels)",
        systemic_component="Risdiplam (oral, systemic distribution)",
        target_organs=["CNS", "Liver", "Heart", "Pancreas", "Vasculature"],
        rationale="Nusinersen achieves high CNS/spinal cord SMN levels. Risdiplam covers peripheral "
                 "organs that intrathecal delivery cannot reach. Together: full-body SMN restoration.",
        feasibility=0.70,
        clinical_status="JEWELFISH study showed safety — combination use growing in clinical practice",
    ),
    CombinationTherapy(
        name="SMN therapy + Apitegromab + Exercise",
        neuro_component="Any approved SMN therapy",
        systemic_component="Apitegromab (anti-myostatin) + structured exercise",
        target_organs=["Motor neurons", "Muscle", "NMJ", "Bone"],
        rationale="SMN therapy halts neurodegeneration. Apitegromab promotes muscle growth. "
                 "Exercise provides activity-dependent NMJ maintenance and retrograde signaling.",
        feasibility=0.80,
        clinical_status="Apitegromab in Phase 3 (SAPPHIRE). Exercise trials ongoing.",
    ),
    CombinationTherapy(
        name="Zolgensma + Metabolic support",
        neuro_component="Zolgensma (one-time gene replacement)",
        systemic_component="NAD+ precursor (NMN/NR) + CoQ10 + dietary management",
        target_organs=["All (gene therapy is systemic)", "Mitochondria"],
        rationale="Zolgensma transduces many organs but doesn't fix established metabolic dysfunction. "
                 "Mitochondrial support addresses persistent bioenergetic deficits.",
        feasibility=0.75,
        clinical_status="Conceptual — nutraceutical support not formally studied in SMA",
    ),
]


# ---------------------------------------------------------------------------
# Energy budget model
# ---------------------------------------------------------------------------

def _energy_budget() -> dict[str, Any]:
    """Model the energy budget imbalance in SMA."""
    return {
        "normal_motor_neuron": {
            "atp_demand": "High (synaptic transmission, axonal transport)",
            "energy_source": "Glucose oxidation + fatty acid oxidation",
            "mitochondrial_function": "Normal",
            "supply_demand_ratio": 1.0,
        },
        "sma_motor_neuron": {
            "atp_demand": "High (unchanged — still trying to maintain NMJ)",
            "energy_source": "Impaired (reduced FAO, glycolytic shift)",
            "mitochondrial_function": "Compromised (fragmented, reduced complex I/III)",
            "supply_demand_ratio": 0.60,
        },
        "treated_sma_motor_neuron": {
            "atp_demand": "Moderate (partially restored function)",
            "energy_source": "Partially restored (SMN improves mito function)",
            "mitochondrial_function": "Improved but not normal",
            "supply_demand_ratio": 0.80,
        },
        "therapeutic_gap": "Even with SMN restoration, a 20% energy deficit persists. "
                          "This gap may explain why treated SMA patients plateau rather than "
                          "fully recover. Mitochondrial boosters could close this gap.",
        "actionable_compounds": [
            {"name": "NMN/NR", "mechanism": "NAD+ precursor → Complex I support", "availability": "Supplement"},
            {"name": "Bezafibrate", "mechanism": "PPARalpha agonist → FAO enhancement", "availability": "Prescription"},
            {"name": "CoQ10", "mechanism": "Electron carrier → Complex III support", "availability": "Supplement"},
            {"name": "Metformin", "mechanism": "AMPK activation → mitochondrial biogenesis", "availability": "Prescription"},
            {"name": "Urolithin A", "mechanism": "Mitophagy inducer → removes damaged mitochondria", "availability": "Supplement"},
        ],
    }


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def get_organ_systems() -> dict[str, Any]:
    """Return all organ systems affected in SMA."""
    smn_dependent = [o for o in ORGAN_SYSTEMS if o.smn_dependent]
    smn_independent = [o for o in ORGAN_SYSTEMS if not o.smn_dependent]

    return {
        "total_systems": len(ORGAN_SYSTEMS),
        "systems": [asdict(o) for o in ORGAN_SYSTEMS],
        "smn_dependent_count": len(smn_dependent),
        "smn_independent_count": len(smn_independent),
        "most_severe": asdict(max(ORGAN_SYSTEMS, key=lambda x: x.severity)),
        "most_prevalent": asdict(max(ORGAN_SYSTEMS, key=lambda x: x.prevalence)),
        "insight": "SMA affects 7 organ systems beyond motor neurons. 6/7 are SMN-dependent, "
                   "meaning they share the root cause. Intrathecal nusinersen does NOT address "
                   "peripheral pathology — systemic SMN delivery (risdiplam, Zolgensma) is essential "
                   "for multisystem disease management.",
    }


def get_combination_therapies() -> dict[str, Any]:
    """Return combination therapy strategies for multisystem SMA."""
    return {
        "total_strategies": len(COMBINATION_THERAPIES),
        "strategies": [asdict(c) for c in COMBINATION_THERAPIES],
        "most_feasible": asdict(max(COMBINATION_THERAPIES, key=lambda x: x.feasibility)),
        "insight": "Risdiplam + Metformin is the most feasible combination — both are oral, "
                   "approved, and target complementary pathways. The dual SMN approach "
                   "(nusinersen + risdiplam) is already emerging in clinical practice.",
    }


def get_energy_budget() -> dict[str, Any]:
    """Return the energy budget analysis for SMA motor neurons."""
    return _energy_budget()


def analyze_multisystem_sma() -> dict[str, Any]:
    """Full multisystem SMA analysis with organ systems, combinations, and energy budget."""
    return {
        "organ_systems": get_organ_systems(),
        "combination_therapies": get_combination_therapies(),
        "energy_budget": get_energy_budget(),
        "key_message": "SMA is NOT just a motor neuron disease. Treating the whole patient requires "
                       "addressing liver metabolism, cardiac function, bone health, and energy balance "
                       "alongside neurological SMN restoration.",
    }
