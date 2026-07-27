"""Conservative realism screening for participant-facing recommendations.

The source dataset contains a small number of novelty mashups that may be valid
recipes but are poor default suggestions for a pantry assistant.  This module
suppresses only high-confidence gimmick combinations.  Familiar dishes remain
eligible, and uncertain cases are left in the candidate pool rather than being
silently over-filtered.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def _tokens(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", str(value or "").lower()))


# These are title-level combinations, not ingredient bans.  For example,
# ordinary waffles and ordinary pesto pasta remain eligible; only the explicit
# novelty mashup is suppressed.
_BLOCKED_TITLE_COMBINATIONS: Tuple[Tuple[frozenset[str], str], ...] = (
    (frozenset({"pesto", "waffle"}), "novelty_pesto_waffle_mashup"),
    (frozenset({"pesto", "waffles"}), "novelty_pesto_waffle_mashup"),
    (frozenset({"parmesan", "pesto", "waffle"}), "novelty_savory_waffle_mashup"),
    (frozenset({"parmesan", "pesto", "waffles"}), "novelty_savory_waffle_mashup"),
)


def realism_decision(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    """Return an explainable keep/suppress decision for one candidate."""
    title = str(candidate.get("recipe_name") or "").strip()
    title_tokens = _tokens(title)
    for required, reason in _BLOCKED_TITLE_COMBINATIONS:
        if required.issubset(title_tokens):
            return {
                "keep": False,
                "reason": reason,
                "recipe_name": title,
                "realism_version": "phase_18_5_conservative_realism_v1",
            }
    return {
        "keep": True,
        "reason": "no_high_confidence_novelty_pattern",
        "recipe_name": title,
        "realism_version": "phase_18_5_conservative_realism_v1",
    }


def filter_realistic_recipe_concepts(
    candidates: Sequence[Mapping[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Suppress high-confidence novelty mashups and report exactly what changed."""
    kept: List[Dict[str, Any]] = []
    suppressed: List[Dict[str, str]] = []
    for candidate in candidates:
        decision = realism_decision(candidate)
        if decision["keep"]:
            kept.append(dict(candidate))
        else:
            suppressed.append({
                "recipe_name": str(decision["recipe_name"]),
                "reason": str(decision["reason"]),
            })
    return kept, {
        "recipe_realism_version": "phase_18_5_conservative_realism_v1",
        "realism_screened_candidate_count": len(candidates),
        "realism_suppressed_candidate_count": len(suppressed),
        "realism_suppressed_examples": suppressed[:10],
        "realism_strategy": "suppress_only_high_confidence_novelty_title_combinations",
    }
