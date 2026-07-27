"""Optional participant preference fit for eligible recommendation candidates.

Safety restrictions are handled earlier by profile_safety.py. This module only
measures optional likes and convenience preferences; it never removes a recipe.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple
import re


def _terms(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw = [str(item) for item in value]
    else:
        raw = re.split(r"[,;/|\n]+", str(value))
    result: List[str] = []
    for item in raw:
        cleaned = " ".join(item.lower().strip().split())
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def _label_matches(preferences: Sequence[str], labels: Iterable[str]) -> bool:
    normalized_labels = [" ".join(str(label).lower().split()) for label in labels]
    for preference in preferences:
        if any(preference == label or preference in label or label in preference for label in normalized_labels):
            return True
    return False


def calculate_preference_fit(
    candidate: Mapping[str, Any],
    profile: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Return a transparent 0-10 optional preference score.

    Blank profile fields receive neutral credit instead of penalizing a user who
    chose not to state a preference.
    """
    profile = profile or {}
    preferred_cuisines = _terms(profile.get("preferred_cuisine"))
    preferred_meals = _terms(profile.get("preferred_meal_type"))
    quick_preferred = profile.get("quick_meals_preferred")

    score = 0.0
    reasons: List[str] = []
    details: Dict[str, Any] = {
        "preferred_cuisines": preferred_cuisines,
        "preferred_meal_types": preferred_meals,
        "quick_meals_preferred": quick_preferred,
    }

    if not preferred_cuisines:
        score += 2.0
        details["cuisine_match"] = "neutral_no_preference"
    elif _label_matches(preferred_cuisines, candidate.get("cuisine_types") or []):
        score += 4.0
        details["cuisine_match"] = True
        reasons.append("Matches a preferred cuisine")
    else:
        details["cuisine_match"] = False

    if not preferred_meals:
        score += 2.0
        details["meal_type_match"] = "neutral_no_preference"
    elif _label_matches(preferred_meals, candidate.get("meal_types") or []):
        score += 4.0
        details["meal_type_match"] = True
        reasons.append("Matches a preferred meal type")
    else:
        details["meal_type_match"] = False

    everyday_fit = candidate.get("everyday_fit_score")
    try:
        everyday_fit_value = float(everyday_fit) if everyday_fit is not None else None
    except (TypeError, ValueError):
        everyday_fit_value = None

    if quick_preferred is True:
        if everyday_fit_value is not None and everyday_fit_value >= 70:
            score += 2.0
            details["quick_meal_match"] = True
            reasons.append("Fits the quick-everyday preference")
        else:
            details["quick_meal_match"] = False
    else:
        score += 1.0
        details["quick_meal_match"] = "neutral_not_requested"

    return {
        "score": round(min(score, 10.0), 1),
        "max_score": 10.0,
        "reasons": reasons,
        "details": details,
    }
