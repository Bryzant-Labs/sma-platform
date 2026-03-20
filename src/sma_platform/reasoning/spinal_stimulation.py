"""Spinal Cord Stimulation for SMA — Capogrosso/Simon approach.

Epidural spinal cord stimulation targeting proprioceptive circuits
to reactivate dormant motor neurons. Pilot results 'spectacular'
per Prof. Simon (Leipzig).
"""

from __future__ import annotations

SPINAL_STIMULATION = {
    "name": "Epidural Spinal Cord Stimulation for SMA",
    "researcher": "Marco Capogrosso (University of Pittsburgh)",
    "collaborators": ["ESPACE Europe consortium", "Christian Simon (Leipzig)"],
    "mechanism": (
        "Proprioceptive Ia afferents form monosynaptic connections on spinal motor neurons. "
        "In SMA, these synapses are lost early (Mentis 2011). Epidural stimulation at sub-motor "
        "threshold activates the proprioceptive circuit, which then reactivates motor neurons "
        "that have been dormant (not dead). After 1 month of 2h/day stimulation, patients show "
        "improved motor function because the proprioceptive-motor circuit is re-established."
    ),
    "key_innovation": "Stimulation below motor threshold — activates proprioception, NOT direct motor activation",
    "pilot_results": "Spectacular improvement in motor function after 1 month (Simon's description)",
    "clinical_status": "Pilot studies ongoing, planning larger trials",
    "advantages": [
        "Can help adult patients (not just infants)",
        "Complements SMN-targeting therapies",
        "Targets proprioceptive circuit — a novel axis",
        "Epidural implants are established technology",
        "Non-destructive — can be removed",
    ],
    "challenges": [
        "Invasive procedure (epidural implant)",
        "Requires daily stimulation sessions",
        "Individual parameter optimization needed",
        "Long-term effects unknown",
    ],
    "relevance_to_platform": [
        "Our proprioceptive pathway analysis directly supports this approach",
        "4-AP (our CORO1C hit) enhances nerve conduction — potential synergy",
        "Spinal cord segment mapping helps target stimulation correctly",
        "Evidence convergence scoring can quantify support for this approach",
    ],
    "references": [
        {"title": "Proprioceptive synaptic dysfunction in SMA", "pmid": "21482353", "author": "Mentis et al."},
        {"title": "Spinal cord stimulation restores motor function", "pmid": None, "author": "Capogrosso et al."},
    ],
}


def get_stimulation_info():
    """Return curated knowledge about spinal cord stimulation for SMA."""
    return SPINAL_STIMULATION
