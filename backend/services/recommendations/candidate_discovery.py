"""Eligibility-driven, expiration-first recipe candidate discovery.

This phase intentionally performs no nutrition, preference, or Smart Score
ranking. It establishes a deterministic candidate pool in two groups:

1. Complete meals that use at least one pantry item expiring within the window.
2. Other complete meals that can be made from the usable pantry.

Near-complete recipes missing one or two meaningful main ingredients are retained
as fallback candidates. Complete meals always remain ahead of near-complete meals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .expiry_analyzer import ExpirationAssessment, assess_expiration
from .meal_eligibility import Eligibility, EligibilityDecision, classify_meal_eligibility
from .ingredient_normalizer import ingredients_equivalent, normalize_ingredient
from .pantry_matcher import PantryItem, match_recipe_ingredient, prepare_pantry_items
from .recipe_repository import RecipeRecord
from .smart_swaps import find_smart_swaps
from .meal_context import classify_meal_types, normalize_cuisines


@dataclass(frozen=True)
class PreparedPantryItem:
    item: PantryItem
    expiration: ExpirationAssessment


@dataclass(frozen=True)
class CandidateDiscoveryResult:
    recommendations: List[Dict[str, Any]]
    metadata: Dict[str, Any]



def _has_usable_quantity(item: PantryItem) -> bool:
    # A missing quantity means quantity was not tracked; it is not treated as zero.
    return item.quantity is None or item.quantity > 0


def prepare_usable_pantry(
    raw_pantry_items: Iterable[Dict[str, Any]],
    *,
    today: Optional[date] = None,
    expiry_window_days: int = 7,
) -> Tuple[List[PreparedPantryItem], Dict[str, int]]:
    prepared = prepare_pantry_items(raw_pantry_items)
    usable: List[PreparedPantryItem] = []
    expired_count = 0
    out_of_stock_count = 0

    for item in prepared:
        expiration = assess_expiration(
            item.expiration_date,
            today=today,
            expiry_window_days=expiry_window_days,
        )
        if not _has_usable_quantity(item):
            out_of_stock_count += 1
            continue
        if not expiration.is_usable:
            expired_count += 1
            continue
        usable.append(PreparedPantryItem(item=item, expiration=expiration))

    return usable, {
        "raw_pantry_item_count": len(prepared),
        "usable_pantry_item_count": len(usable),
        "expired_pantry_item_count": expired_count,
        "out_of_stock_pantry_item_count": out_of_stock_count,
        "expiring_pantry_item_count": sum(entry.expiration.is_expiring for entry in usable),
    }


def _ingredient_match_payload(
    recipe_ingredient: str,
    pantry_entry: PreparedPantryItem,
    match_type: str,
    normalized_ingredient: str,
) -> Dict[str, Any]:
    return {
        "recipe_ingredient": recipe_ingredient,
        "normalized_ingredient": normalized_ingredient,
        "match_type": match_type,
        "pantry_item_id": pantry_entry.item.pantry_item_id,
        "pantry_item_name": pantry_entry.item.item_name,
        "display_name": normalized_ingredient or normalize_ingredient(pantry_entry.item.item_name).canonical or pantry_entry.item.item_name,
        "expiration_state": pantry_entry.expiration.state.value,
        "expires_on": pantry_entry.expiration.expiration_date,
        "days_until_expiration": pantry_entry.expiration.days_until_expiration,
    }




def _recipe_detail_for_main_ingredient(recipe: RecipeRecord, main_ingredient: str) -> Dict[str, Any]:
    """Return the dataset quantity/measure record that best represents a main ingredient.

    The recommendation engine ranks on normalized main ingredients, while the recipe dataset
    also stores the original amount, measure, text, and an estimated gram weight. Keeping both
    lets the UI show recipe-native amounts and safely convert them to pantry units later.
    """
    target = normalize_ingredient(main_ingredient).canonical
    exact = []
    equivalent = []
    for ingredient in recipe.ingredients:
        source = ingredient.food or ingredient.text
        canonical = normalize_ingredient(source).canonical
        if canonical and canonical == target:
            exact.append(ingredient)
        elif source and ingredients_equivalent(main_ingredient, source):
            equivalent.append(ingredient)
    selected = (exact or equivalent or [None])[0]
    if selected is None:
        return {
            "recipe_quantity": None,
            "recipe_measure": None,
            "recipe_weight_grams": None,
            "recipe_text": main_ingredient,
        }
    return {
        "recipe_quantity": selected.quantity,
        "recipe_measure": selected.measure,
        "recipe_weight_grams": selected.weight,
        "recipe_text": selected.text or selected.food or main_ingredient,
    }

def _nutrition_payload(recipe: RecipeRecord) -> Dict[str, Any]:
    """Return audited per-serving nutrition with conservative outlier correction.

    Some source rows contain implausibly low serving counts. We preserve the
    reported value and infer only the minimum serving count needed to keep a
    portion within a credible upper range.
    """
    reported = recipe.servings if recipe.servings and recipe.servings > 0 else 1.0
    effective = float(reported)
    inferred = False
    if recipe.calories is not None and recipe.calories / effective > 1200:
        effective = max(effective, min(24.0, float(__import__("math").ceil(recipe.calories / 850.0))))
        inferred = effective != float(reported)
    def portion(value):
        return round(value / effective, 1) if value is not None else None
    return {
        "calories": recipe.calories, "protein": recipe.protein, "carbs": recipe.carbs, "fat": recipe.fat,
        "servings": effective, "reported_servings": recipe.servings,
        "servings_inferred": inferred,
        "per_serving": {"calories": portion(recipe.calories), "protein": portion(recipe.protein), "carbs": portion(recipe.carbs), "fat": portion(recipe.fat)},
        "basis": "per_serving_inferred" if inferred else "per_serving_reported",
    }


def evaluate_recipe_candidate(
    recipe: RecipeRecord,
    pantry_entries: Sequence[PreparedPantryItem],
) -> Tuple[EligibilityDecision, Dict[str, Any]]:
    pantry_items = [entry.item for entry in pantry_entries]
    pantry_by_id = {entry.item.pantry_item_id: entry for entry in pantry_entries}

    matched: List[Dict[str, Any]] = []
    missing: List[str] = []
    for main_ingredient in recipe.main_ingredients:
        result = match_recipe_ingredient(main_ingredient, pantry_items)
        if not result.matched or not result.pantry_item_id:
            missing.append(main_ingredient)
            continue
        pantry_entry = pantry_by_id[result.pantry_item_id]
        match_payload = _ingredient_match_payload(
            main_ingredient,
            pantry_entry,
            result.match_type,
            result.normalized_ingredient,
        )
        match_payload.update(_recipe_detail_for_main_ingredient(recipe, main_ingredient))
        matched.append(match_payload)

    decision = classify_meal_eligibility(
        total_main_ingredients=len(recipe.main_ingredients),
        matched_main_ingredients=len(matched),
        missing_main_ingredients=missing,
    )
    expiring_matches = [item for item in matched if item["expiration_state"] == "expiring"]
    if decision.status is Eligibility.COMPLETE:
        candidate_group = "expiry_led_complete" if expiring_matches else "other_complete"
    elif decision.status is Eligibility.NEAR_COMPLETE:
        candidate_group = "expiry_led_near_complete" if expiring_matches else "other_near_complete"
    else:
        candidate_group = "ineligible"

    payload: Dict[str, Any] = {
        "recipe_id": recipe.recipe_id,
        "recipe_name": recipe.recipe_name,
        "recipe_url": recipe.url,
        "meal_types": classify_meal_types({"recipe_name": recipe.recipe_name, "meal_types": recipe.meal_types, "dish_types": recipe.dish_types, "everyday_fit_score": recipe.everyday_fit_score}),
        "cuisine_types": normalize_cuisines({"recipe_name": recipe.recipe_name, "cuisine_types": recipe.cuisine_types}),
        "dish_types": recipe.dish_types,
        "main_ingredients": recipe.main_ingredients,
        "matched_ingredients": matched,
        "missing_ingredients": missing,
        "smart_swaps": find_smart_swaps(missing, [{"item_name": entry.item.item_name} for entry in pantry_entries], recipe_context={"recipe_name": recipe.recipe_name, "meal_types": recipe.meal_types, "dish_types": recipe.dish_types}),
        "expiring_ingredients": expiring_matches,
        "pantry_match_percent": decision.main_ingredient_coverage,
        "eligibility": decision.status.value,
        "eligibility_reason": decision.reason,
        "missing_main_ingredient_count": decision.missing_main_ingredient_count,
        "eligibility_tier": decision.tier,
        "candidate_group": candidate_group,
        "everyday_fit_score": recipe.everyday_fit_score,
        "nutrition": _nutrition_payload(recipe),
        # These are deliberately absent until later phases calculate them.
        "nutrition_fit": None,
        "preference_fit": None,
        "smart_score": None,
    }
    return decision, payload


def _expiry_sort_key(candidate: Dict[str, Any]) -> tuple:
    expiring = candidate["expiring_ingredients"]
    earliest = min(
        item["days_until_expiration"]
        for item in expiring
        if item["days_until_expiration"] is not None
    )
    return (
        earliest,
        -len(expiring),
        -len(candidate["matched_ingredients"]),
        candidate["recipe_name"].lower(),
        candidate["recipe_id"],
    )


def _other_sort_key(candidate: Dict[str, Any]) -> tuple:
    # There is intentionally no hidden quality score in Phase 4. Prefer recipes
    # that use more pantry main ingredients, then use stable alphabetical order.
    return (
        -len(candidate["matched_ingredients"]),
        candidate["recipe_name"].lower(),
        candidate["recipe_id"],
    )


def discover_candidates(
    recipes: Sequence[RecipeRecord],
    raw_pantry_items: Iterable[Dict[str, Any]],
    *,
    today: Optional[date] = None,
    expiry_window_days: int = 7,
    limit: Optional[int] = 15,
) -> CandidateDiscoveryResult:
    """Return all realistic complete and near-complete candidates before scoring."""
    pantry_entries, pantry_metadata = prepare_usable_pantry(
        raw_pantry_items, today=today, expiry_window_days=expiry_window_days,
    )
    groups = {
        "expiry_led_complete": [], "other_complete": [],
        "expiry_led_near_complete": [], "other_near_complete": [],
    }
    ineligible_count = 0
    near_one = near_two = 0
    for recipe in recipes:
        decision, candidate = evaluate_recipe_candidate(recipe, pantry_entries)
        if decision.status is Eligibility.INELIGIBLE:
            ineligible_count += 1
            continue
        groups[candidate["candidate_group"]].append(candidate)
        if decision.status is Eligibility.NEAR_COMPLETE:
            if decision.missing_main_ingredient_count == 1: near_one += 1
            elif decision.missing_main_ingredient_count == 2: near_two += 1

    groups["expiry_led_complete"].sort(key=_expiry_sort_key)
    groups["other_complete"].sort(key=_other_sort_key)
    groups["expiry_led_near_complete"].sort(key=lambda c: (c["missing_main_ingredient_count"],) + _expiry_sort_key(c))
    groups["other_near_complete"].sort(key=lambda c: (c["missing_main_ingredient_count"], -c["pantry_match_percent"],) + _other_sort_key(c))
    combined = (groups["expiry_led_complete"] + groups["other_complete"] +
                groups["expiry_led_near_complete"] + groups["other_near_complete"])
    requested_limit = None if limit is None else max(int(limit), 0)
    selected = combined if requested_limit is None else combined[:requested_limit]
    metadata = {
        **pantry_metadata, "expiry_window_days": max(int(expiry_window_days),0),
        "recipe_count_evaluated": len(recipes),
        "expiry_led_complete_count": len(groups["expiry_led_complete"]),
        "other_complete_count": len(groups["other_complete"]),
        "expiry_led_near_complete_count": len(groups["expiry_led_near_complete"]),
        "other_near_complete_count": len(groups["other_near_complete"]),
        "near_complete_one_missing_count": near_one,
        "near_complete_two_missing_count": near_two,
        "ineligible_count": ineligible_count,
        "total_eligible_count": len(combined), "returned_count": len(selected),
        "requested_limit": requested_limit, "ranking_phase": "phase_12_candidate_expansion",
    }
    return CandidateDiscoveryResult(recommendations=selected, metadata=metadata)
