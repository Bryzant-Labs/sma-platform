"""Disease-specific configuration. Set DISEASE env var to switch."""
import os
from typing import Any

DISEASE = os.environ.get("DISEASE", "sma")

# Disease registry - import configs from diseases/ subfolder
_REGISTRY: dict[str, dict[str, Any]] = {}


def _load_registry():
    from sma_platform.diseases import sma as sma_config
    _REGISTRY["sma"] = sma_config.CONFIG
    try:
        from sma_platform.diseases import idh1_icca as idh1_config
        _REGISTRY["idh1_icca"] = idh1_config.CONFIG
    except ImportError:
        pass


def get_disease_config() -> dict[str, Any]:
    if not _REGISTRY:
        _load_registry()
    if DISEASE not in _REGISTRY:
        raise ValueError(f"Unknown disease: {DISEASE}. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[DISEASE]


def get_disease_id() -> str:
    return DISEASE


def get_disease_name() -> str:
    return get_disease_config()["name"]


def get_disease_short_name() -> str:
    return get_disease_config()["short_name"]


def get_disease_targets() -> list[dict]:
    return get_disease_config()["targets"]


def get_disease_drugs() -> list[dict]:
    return get_disease_config()["drugs"]


def get_disease_pubmed_queries() -> list[str]:
    return get_disease_config()["pubmed_queries"]


def get_disease_trial_queries() -> list[str]:
    return get_disease_config()["trial_queries"]


def get_disease_aliases() -> dict[str, list[str]]:
    return get_disease_config().get("alias_patterns", {})


def get_disease_accent_color() -> str:
    return get_disease_config().get("accent_color", "#4361ee")


def get_disease_description() -> str:
    return get_disease_config().get("description", "")
