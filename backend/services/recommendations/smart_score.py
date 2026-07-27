"""Phase 17 adaptive and explainable Smart Score."""
from __future__ import annotations
from typing import Any, Dict, Mapping, Sequence, Tuple
import math

from .behavior_learning import score_behavior
from .preference_fit import calculate_preference_fit

SMART_SCORE_WEIGHTS = {
    "pantry_usefulness": 30.0,
    "expiration_priority": 20.0,
    "nutrition_fit": 25.0,
    "preference_fit": 5.0,
    "practicality": 20.0,
}

HIGH_BURDEN = {"chicken","beef","pork","turkey","shrimp","salmon","fish","lamb","tofu","tempeh","steak","sausage"}
LOW_BURDEN = {"salt","pepper","oil","water","flour","sugar","corn","breadcrumb","panko","rice","pasta","potato","onion","garlic","milk"}


def _pantry_utilization(candidate: Mapping[str, Any]) -> Tuple[float, Dict[str, Any]]:
    matched_rows = candidate.get("matched_ingredients") or []
    matched = len(matched_rows)
    total = max(1, len(candidate.get("main_ingredients") or []))
    coverage = max(0.0, min(1.0, matched / total))
    unique_pantry = len({str(row.get("pantry_item_id") or row.get("pantry_item_name") or "") for row in matched_rows})
    expiring = len(candidate.get("expiring_ingredients") or [])
    complete_points = 6.0 if candidate.get("eligibility") == "complete" else 0.0
    coverage_points = coverage * 14.0
    breadth_points = min(7.0, unique_pantry * 1.4)
    waste_points = min(3.0, expiring * 1.5)
    points = min(30.0, complete_points + coverage_points + breadth_points + waste_points)
    return round(points, 1), {
        "complete_meal_points": complete_points,
        "matched_count": matched,
        "unique_pantry_items_used": unique_pantry,
        "main_ingredient_count": total,
        "coverage_percent": round(coverage * 100, 1),
        "coverage_points": round(coverage_points, 1),
        "pantry_breadth_points": round(breadth_points, 1),
        "waste_reduction_points": round(waste_points, 1),
    }


def _nutrition(candidate):
    fit = candidate.get("nutrition_fit") or {}
    value = fit.get("score_percent")
    if value is None:
        return 12.5, {"status": fit.get("status") or "unavailable", "fallback_used": True}
    value = max(0.0, min(100.0, float(value)))
    return round(value * .25, 1), {"status": "available", "nutrition_fit_percent": round(value, 1), "fallback_used": False}


def _expiry(candidate):
    items = candidate.get("expiring_ingredients") or []
    days = [int(i["days_until_expiration"]) for i in items if i.get("days_until_expiration") is not None]
    if not days:
        return 0.0, {"uses_expiring_ingredients": False, "expiring_ingredient_count": 0, "earliest_days_until_expiration": None}
    earliest = max(0, min(days))
    urgency = max(4.0, 15.0 - earliest)
    breadth = min(5.0, len(items) * 2.5)
    return round(min(20.0, urgency + breadth), 1), {"uses_expiring_ingredients": True, "expiring_ingredient_count": len(items), "earliest_days_until_expiration": earliest}


def _missing_burden(candidate):
    swaps = {str(s.get("needed", "")) for s in candidate.get("smart_swaps") or []}
    total = 0.0
    detail = []
    for raw in candidate.get("missing_ingredients") or []:
        text = str(raw).lower()
        if raw in swaps:
            penalty, level = 0.75, "swap_available"
        elif any(t in text for t in HIGH_BURDEN):
            penalty, level = 5.0, "high"
        elif any(t in text for t in LOW_BURDEN):
            penalty, level = 1.25, "low"
        else:
            penalty, level = 2.75, "medium"
        total += penalty
        detail.append({"ingredient": raw, "burden": level, "penalty": penalty})
    return min(10.0, total), detail


def _practicality(candidate):
    count = len(candidate.get("main_ingredients") or [])
    simplicity = 9.0 if count <= 5 else 7.5 if count <= 8 else 6.0 if count <= 11 else 4.0
    everyday = candidate.get("everyday_fit_score")
    try:
        everyday_points = max(0, min(100, float(everyday))) * .10 if everyday is not None else 5.0
    except (TypeError, ValueError):
        everyday_points = 5.0
    burden, detail = _missing_burden(candidate)
    context = " ".join(candidate.get("meal_types") or []) + " " + " ".join(candidate.get("dish_types") or []) + " " + str(candidate.get("recipe_name") or "")
    dessert = any(x in context.lower() for x in ["dessert", "cake", "cupcake", "candy", "cookie", "pudding"])
    category_penalty = 3.0 if dessert else 0.0
    points = max(0.0, min(20.0, simplicity + everyday_points - burden - category_penalty))
    return round(points, 1), {"main_ingredient_count": count, "simplicity_points": simplicity, "everyday_points": round(everyday_points, 1), "missing_penalty": round(burden, 1), "missing_burden": detail, "smart_swap_count": len(candidate.get("smart_swaps") or []), "dessert_or_sweet_penalty": category_penalty}


def calculate_smart_score(candidate: Mapping[str, Any], profile=None):
    pantry_points, pantry_detail = _pantry_utilization(candidate)
    nutrition_points, nutrition_detail = _nutrition(candidate)
    expiry_points, expiry_detail = _expiry(candidate)
    practicality_points, practicality_detail = _practicality(candidate)
    behavior_points, behavior_detail = score_behavior(candidate, profile)
    preference = calculate_preference_fit(candidate, profile)
    preference_raw = float(preference.get("score") or 0)
    base_preference_points = preference_raw * .5
    # Convert the neutral-centered behavior score (5) into a conservative
    # adjustment of at most +/-2 points inside the existing preference bucket.
    behavior_adjustment = max(-2.0, min(2.0, (behavior_points - 5.0) * 0.5))
    preference_points = round(max(0.0, min(5.0, base_preference_points + behavior_adjustment)), 1)
    preference["behavior_learning"] = behavior_detail
    preference["behavior_adjustment"] = round(behavior_adjustment, 1)

    total = round(min(100.0, pantry_points + nutrition_points + expiry_points + practicality_points + preference_points), 1)
    missing = len(candidate.get("missing_ingredients") or [])
    reasons = ["Complete meal from available pantry ingredients" if candidate.get("eligibility") == "complete" else f"Near-complete meal needing {missing} additional ingredient{'s' if missing != 1 else ''}"]
    reasons.append(f"Uses {len(candidate.get('matched_ingredients') or [])} pantry ingredients")
    if expiry_detail["uses_expiring_ingredients"]:
        reasons.append(f"Uses {expiry_detail['expiring_ingredient_count']} ingredient{'s' if expiry_detail['expiring_ingredient_count'] != 1 else ''} expiring soon")
    if behavior_detail["explanations"][0] != "No strong behavior signal yet":
        reasons.append(behavior_detail["explanations"][0])
    if candidate.get("smart_swaps"):
        reasons.append(f"Context-safe Smart Swap available for {len(candidate['smart_swaps'])} missing ingredient{'s' if len(candidate['smart_swaps']) != 1 else ''}")

    return {
        "score": total,
        "max_score": 100.0,
        "version": "phase_17_adaptive_v1",
        "weights": dict(SMART_SCORE_WEIGHTS),
        "breakdown": {
            "pantry_usefulness": {"points": pantry_points, "max_points": 30.0, **pantry_detail},
            "expiration_priority": {"points": expiry_points, "max_points": 20.0, **expiry_detail},
            "nutrition_fit": {"points": nutrition_points, "max_points": 25.0, **nutrition_detail},
            "preference_fit": {"points": preference_points, "max_points": 5.0, **preference},
            "practicality": {"points": practicality_points, "max_points": 20.0, **practicality_detail},
        },
        "reasons": reasons[:5],
    }


def _ranking_key(candidate):
    score = float(candidate.get("smart_score") or 0)
    expiring = candidate.get("expiring_ingredients") or []
    days = [x.get("days_until_expiration") for x in expiring if x.get("days_until_expiration") is not None]
    preference = ((candidate.get("smart_score_details") or {}).get("breakdown") or {}).get("preference_fit") or {}
    behavior = preference.get("behavior_learning") or {}
    fatigue = float(behavior.get("fatigue_penalty") or 0)
    return (
        0 if candidate.get("eligibility") == "complete" else 1,
        -score,
        fatigue,
        len(candidate.get("missing_ingredients") or []),
        -len(candidate.get("matched_ingredients") or []),
        min(days) if days else math.inf,
        str(candidate.get("recipe_name") or "").lower(),
    )


def score_and_rank_candidates(candidates: Sequence[Dict[str, Any]], profile=None, *, limit=15):
    scored = []
    for candidate in candidates:
        score = calculate_smart_score(candidate, profile)
        item = dict(candidate)
        item["preference_fit"] = score["breakdown"]["preference_fit"]
        item["smart_score"] = score["score"]
        item["smart_score_details"] = score
        item["reasons"] = score["reasons"]
        scored.append(item)
    scored.sort(key=_ranking_key)
    requested = max(0, int(limit))
    selected = scored[:requested] if requested else []
    return selected, {
        "smart_score_version": "phase_17_adaptive_v1",
        "smart_score_weights": dict(SMART_SCORE_WEIGHTS),
        "smart_score_candidate_count": len(scored),
        "smart_score_returned_count": len(selected),
        "smart_score_requested_limit": requested,
        "smart_score_sorting": "complete_first_then_adaptive_score_utilization_fatigue_and_expiration",
        "behavior_action_count": len((profile or {}).get("_behavior_actions") or []),
    }
