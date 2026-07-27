"""Phase 17 recommendation validation and explanation helpers.

This layer does not invent new candidates. It audits the result of matching,
Smart Swaps, scoring, and ranking so the API never describes a recommendation
more confidently than the evidence supports.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .ingredient_normalizer import ingredients_equivalent, normalize_ingredient


def _canonical(value: Any) -> str:
    return normalize_ingredient(str(value or "")).canonical


def _dedupe(values: Iterable[str]) -> List[str]:
    output: List[str] = []
    seen: set[str] = set()
    for value in values:
        clean = str(value or "").strip()
        key = _canonical(clean) or clean.lower()
        if clean and key not in seen:
            output.append(clean)
            seen.add(key)
    return output


def _swap_is_consistent(swap: Mapping[str, Any], missing: Sequence[str]) -> bool:
    needed = str(swap.get("needed") or "").strip()
    replacement = str(swap.get("use_instead") or "").strip()
    confidence = str(swap.get("confidence") or "").lower()
    if not needed or not replacement or confidence not in {"strong", "reasonable"}:
        return False
    if not any(ingredients_equivalent(needed, item) or _canonical(needed) == _canonical(item) for item in missing):
        return False
    if ingredients_equivalent(needed, replacement):
        return False
    return True


def audit_candidate(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a validated copy with confidence and a participant-facing explanation."""
    item = dict(candidate)
    main = _dedupe(item.get("main_ingredients") or [])
    missing = _dedupe(item.get("missing_ingredients") or [])
    matched = list(item.get("matched_ingredients") or [])
    original_swap_count = len(item.get("smart_swaps") or [])
    valid_swaps = [
        dict(swap) for swap in (item.get("smart_swaps") or [])
        if _swap_is_consistent(swap, missing)
    ]

    # Eligibility is re-derived from the actual evidence carried in the result.
    # This catches contract drift without falsely marking a recipe complete.
    uncovered = len(missing)
    expected_eligibility = "complete" if uncovered == 0 else "near_complete"
    eligibility_corrected = item.get("eligibility") != expected_eligibility
    item["eligibility"] = expected_eligibility
    uses_expiring = bool(item.get("expiring_ingredients"))
    item["candidate_group"] = ("expiry_led_" if uses_expiring else "other_") + ("complete" if expected_eligibility == "complete" else "near_complete")
    item["missing_main_ingredient_count"] = uncovered
    item["eligibility_tier"] = min(2, uncovered)
    item["missing_ingredients"] = missing
    item["main_ingredients"] = main
    item["smart_swaps"] = valid_swaps

    matched_count = len({_canonical(row.get("recipe_ingredient")) for row in matched if row.get("recipe_ingredient")})
    total = max(1, len(main))
    item["pantry_match_percent"] = round(min(100.0, max(0.0, matched_count / total * 100.0)), 1)

    score = float(item.get("smart_score") or 0.0)
    fit = (item.get("nutrition_fit") or {}).get("score_percent")
    expiring_count = len(item.get("expiring_ingredients") or [])
    swap_count = len(valid_swaps)
    used_count = len(matched)

    if expected_eligibility == "complete":
        lead = f"You can make this with the pantry ingredients currently available."
    elif swap_count == uncovered and uncovered:
        lead = f"You are missing {uncovered} ingredient{'s' if uncovered != 1 else ''}, but compatible pantry swaps are available."
    else:
        lead = f"This is realistic with {uncovered} additional ingredient{'s' if uncovered != 1 else ''}."

    details = [f"Uses {used_count} pantry ingredient{'s' if used_count != 1 else ''}"]
    if expiring_count:
        details.append(f"uses {expiring_count} item{'s' if expiring_count != 1 else ''} expiring soon")
    behavior = (((item.get("smart_score_details") or {}).get("breakdown") or {}).get("behavior_learning") or {})
    behavior_notes = behavior.get("explanations") or []
    if behavior_notes and behavior_notes[0] != "No strong behavior signal yet":
        details.append(str(behavior_notes[0]).lower())
    if fit is not None:
        details.append(f"Nutrition Fit {round(float(fit))}%")
    details.append(f"Smart Score {round(score)}")
    explanation = lead + " " + "; ".join(details) + "."

    confidence = "high" if expected_eligibility == "complete" else "medium" if uncovered == 1 or swap_count == uncovered else "exploratory"
    item["recommendation_explanation"] = explanation
    item["quality_validation"] = {
        "status": "validated",
        "confidence": confidence,
        "eligibility_corrected": eligibility_corrected,
        "valid_swap_count": swap_count,
        "removed_swap_count": max(0, original_swap_count - swap_count),
        "matched_main_ingredient_count": matched_count,
        "main_ingredient_count": len(main),
    }
    return item


def audit_recommendations(recommendations: Sequence[Mapping[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    audited = [audit_candidate(item) for item in recommendations]
    complete_count = sum(item.get("eligibility") == "complete" for item in audited)
    near_count = len(audited) - complete_count
    confidence_counts = {"high": 0, "medium": 0, "exploratory": 0}
    for item in audited:
        value = (item.get("quality_validation") or {}).get("confidence")
        if value in confidence_counts:
            confidence_counts[value] += 1
    return audited, {
        "quality_validation_version": "phase_17_v1",
        "validated_recommendation_count": len(audited),
        "validated_complete_count": complete_count,
        "validated_near_complete_count": near_count,
        "recommendation_confidence_counts": confidence_counts,
    }
