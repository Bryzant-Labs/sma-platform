#!/usr/bin/env python3
"""Deliverable #3: Axonal Transport Vulnerability Model.

Simple computational model predicting synapse vulnerability based on
axon length × actin-cofilin rod density.

Tests the "Translational Desert" hypothesis:
- Longer axons (Ia afferents) are more vulnerable to transport blockade
- Actin-cofilin rods physically obstruct mRNA granule and mitochondrial transport
- NMJ is furthest from soma → most dependent on transport → fails first

Output: vulnerability score per axon type, predicting which synapses fail first.
"""

import json
import math
from dataclasses import dataclass


@dataclass
class AxonType:
    """Represents a type of axon with its properties."""
    name: str
    length_um: float  # Axon length in micrometers
    diameter_um: float  # Axon diameter
    myelinated: bool
    function: str  # What this axon does
    transport_demand: float  # Relative demand for cargo delivery (0-1)


@dataclass
class TransportModel:
    """Parameters for the axonal transport simulation."""
    motor_speed_um_per_s: float = 1.0  # Kinesin speed ~1 µm/s
    rod_density_per_100um: float = 2.0  # Actin-cofilin rods per 100µm in SMA
    rod_block_probability: float = 0.3  # Probability a rod blocks a cargo
    cargo_half_life_h: float = 12.0  # Cargo degrades if not delivered
    min_cargo_fraction: float = 0.3  # Below this → synapse dysfunction


# Define axon types in the motor circuit
AXON_TYPES = [
    AxonType("Ia_afferent_lumbar", 1000, 12, True,
             "Proprioceptive sensory from muscle spindle to L4-L5 motor neuron",
             0.9),
    AxonType("Ia_afferent_cervical", 500, 10, True,
             "Proprioceptive sensory from arm muscle spindle to C5-C7",
             0.85),
    AxonType("alpha_motor_neuron_leg", 800, 14, True,
             "Motor neuron from L4-L5 to leg muscle NMJ",
             0.95),
    AxonType("alpha_motor_neuron_arm", 400, 12, True,
             "Motor neuron from C5-C7 to arm muscle NMJ",
             0.9),
    AxonType("local_interneuron", 50, 3, False,
             "Spinal cord interneuron — short local connections",
             0.4),
    AxonType("gamma_motor_neuron", 600, 5, True,
             "Gamma motor neuron to muscle spindle intrafusal fibers",
             0.7),
    AxonType("corticospinal_tract", 500, 10, True,
             "Upper motor neuron from cortex to spinal cord",
             0.8),
]


def calculate_transport_efficiency(axon: AxonType, model: TransportModel) -> dict:
    """Calculate transport efficiency for an axon type.

    Returns dict with:
    - transit_time_h: time for cargo to traverse the full axon
    - rods_encountered: expected number of rods along the axon
    - delivery_probability: probability that cargo reaches the synapse
    - vulnerability_score: 0-1, higher = more vulnerable
    """
    # Transit time
    transit_time_s = axon.length_um / model.motor_speed_um_per_s
    transit_time_h = transit_time_s / 3600

    # Number of rods encountered
    rods = (axon.length_um / 100) * model.rod_density_per_100um

    # Probability of successful delivery (each rod has a chance to block)
    delivery_prob = (1 - model.rod_block_probability) ** rods

    # Time penalty — cargo that's delayed may degrade
    degradation_factor = math.exp(-transit_time_h / model.cargo_half_life_h)

    # Effective cargo fraction at synapse
    effective_cargo = delivery_prob * degradation_factor

    # Is the synapse functional?
    functional = effective_cargo >= model.min_cargo_fraction

    # Vulnerability score (0 = safe, 1 = maximum vulnerability)
    vulnerability = 1.0 - effective_cargo

    return {
        "axon": axon.name,
        "length_um": axon.length_um,
        "function": axon.function,
        "transit_time_h": round(transit_time_h, 2),
        "rods_encountered": round(rods, 1),
        "delivery_probability": round(delivery_prob, 4),
        "degradation_factor": round(degradation_factor, 4),
        "effective_cargo": round(effective_cargo, 4),
        "functional": functional,
        "vulnerability_score": round(vulnerability, 4),
    }


def run_model():
    """Run the transport vulnerability model for all axon types."""

    # Normal condition (healthy — no rods)
    healthy = TransportModel(rod_density_per_100um=0.0, rod_block_probability=0.0)

    # SMA condition — moderate rod formation
    sma_moderate = TransportModel(rod_density_per_100um=2.0, rod_block_probability=0.3)

    # SMA severe — high rod density
    sma_severe = TransportModel(rod_density_per_100um=5.0, rod_block_probability=0.4)

    # SMA + Fasudil — rods reduced
    sma_fasudil = TransportModel(rod_density_per_100um=0.5, rod_block_probability=0.2)

    conditions = {
        "healthy": healthy,
        "sma_moderate": sma_moderate,
        "sma_severe": sma_severe,
        "sma_fasudil": sma_fasudil,
    }

    print("=" * 90)
    print("AXONAL TRANSPORT VULNERABILITY MODEL")
    print("Predicts which synapses fail first based on axon length × rod density")
    print("=" * 90)

    all_results = {}

    for cond_name, model in conditions.items():
        print(f"\n{'─' * 90}")
        print(f"Condition: {cond_name.upper()}")
        print(f"  Rod density: {model.rod_density_per_100um}/100µm | Block prob: {model.rod_block_probability}")
        print(f"{'─' * 90}")
        print(f"{'Axon Type':<30} {'Length':>8} {'Rods':>6} {'Delivery':>10} {'Cargo':>8} {'Vuln':>8} {'Status':>10}")

        results = []
        for axon in AXON_TYPES:
            r = calculate_transport_efficiency(axon, model)
            results.append(r)
            status = "OK" if r["functional"] else "FAILING"
            print(f"{r['axon']:<30} {r['length_um']:>7}µm {r['rods_encountered']:>5.1f} "
                  f"{r['delivery_probability']:>9.1%} {r['effective_cargo']:>7.1%} "
                  f"{r['vulnerability_score']:>7.1%} {status:>10}")

        all_results[cond_name] = results

    # Summary: which axons fail first?
    print(f"\n{'=' * 90}")
    print("PREDICTION: Order of synapse failure in SMA (moderate)")
    print("=" * 90)
    sma_results = sorted(all_results["sma_moderate"], key=lambda x: x["vulnerability_score"], reverse=True)
    for i, r in enumerate(sma_results):
        marker = " ← FAILS FIRST" if i == 0 else " ← FAILS SECOND" if i == 1 else ""
        print(f"  {i+1}. {r['axon']}: vulnerability {r['vulnerability_score']:.1%}{marker}")
        print(f"     {r['function']}")

    # Fasudil rescue prediction
    print(f"\n{'=' * 90}")
    print("PREDICTION: Fasudil rescue effect")
    print("=" * 90)
    for axon_name in [r["axon"] for r in sma_results[:3]]:
        sma_r = next(r for r in all_results["sma_moderate"] if r["axon"] == axon_name)
        fas_r = next(r for r in all_results["sma_fasudil"] if r["axon"] == axon_name)
        improvement = sma_r["vulnerability_score"] - fas_r["vulnerability_score"]
        print(f"  {axon_name}:")
        print(f"    SMA: {sma_r['vulnerability_score']:.1%} vulnerability → "
              f"Fasudil: {fas_r['vulnerability_score']:.1%} (improvement: {improvement:.1%})")

    # Save results
    output = {
        "model_parameters": {
            "healthy": {"rod_density": 0, "block_prob": 0},
            "sma_moderate": {"rod_density": 2, "block_prob": 0.3},
            "sma_severe": {"rod_density": 5, "block_prob": 0.4},
            "sma_fasudil": {"rod_density": 0.5, "block_prob": 0.2},
        },
        "results": all_results,
        "prediction": {
            "first_to_fail": sma_results[0]["axon"],
            "second_to_fail": sma_results[1]["axon"],
            "fasudil_most_benefit": sma_results[0]["axon"],
        },
    }
    with open("data/transport_vulnerability_model.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to data/transport_vulnerability_model.json")


if __name__ == "__main__":
    run_model()
