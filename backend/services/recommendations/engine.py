"""Phase 17 full-pool, adaptive recommendation orchestration."""
from __future__ import annotations
from datetime import date
from typing import Any, Dict, List, Optional, Sequence
from .candidate_discovery import discover_candidates
from .diversity import are_near_duplicates, select_diverse_recommendations
from .meal_context import matches_active_filters
from .nutrition_fit import enrich_candidates_with_nutrition_fit
from .profile_safety import filter_safe_recipes
from .recommendation_quality import audit_recommendations
from .recipe_realism import filter_realistic_recipe_concepts
from .recipe_repository import load_recipes
from .smart_score import score_and_rank_candidates


def _build_grocery_suggestions(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, Dict[str, Any]] = {}
    for recipe in recommendations[:50]:
        swapped = {str(item.get("needed") or "").strip().lower() for item in recipe.get("smart_swaps") or []}
        for missing in recipe.get("missing_ingredients") or []:
            key = str(missing).strip().lower()
            if not key or key in swapped:
                continue
            row = counts.setdefault(key, {"ingredient": missing, "recipe_count": 0, "recipe_names": []})
            row["recipe_count"] += 1
            if len(row["recipe_names"]) < 3:
                row["recipe_names"].append(recipe.get("recipe_name"))
    return sorted(counts.values(), key=lambda item: (-item["recipe_count"], str(item["ingredient"])))[:10]


def generate_recommendations(
    pantry_items: List[Dict[str, Any]], profile: Dict[str, Any] | None = None, *,
    limit: int = 300, expiry_window_days: int = 7, today: Optional[date] = None,
    include_nutrition_debug: bool = True, meal_types: Sequence[str] | None = None,
    cuisine_types: Sequence[str] | None = None,
) -> Dict[str, Any]:
    recipes = load_recipes()
    safe_recipes, safety_metadata = filter_safe_recipes(recipes, profile)
    discovery = discover_candidates(safe_recipes, pantry_items, today=today, expiry_window_days=expiry_window_days, limit=None)
    all_realistic = discovery.recommendations
    context_filtered = [c for c in all_realistic if matches_active_filters(c, meal_types, cuisine_types)]
    filtered, realism_metadata = filter_realistic_recipe_concepts(context_filtered)
    requested = min(max(1, int(limit)), 1000)
    # Nutrition inference is applied to the filtered realistic pool, then capped only
    # after ranking. This means the visible top results are chosen from the full context.
    nutrition_candidates, nutrition_metadata = enrich_candidates_with_nutrition_fit(filtered, include_debug=include_nutrition_debug)
    ranked, score_metadata = score_and_rank_candidates(nutrition_candidates, profile, limit=len(nutrition_candidates))
    capped_ranked = ranked[:requested]
    # Keep complete meals ahead of near-complete meals, while diversifying each
    # tier independently. This prevents a high-nutrition fallback from hiding
    # meals the participant can already make.
    complete_ranked = [item for item in capped_ranked if item.get("eligibility") == "complete"]
    near_ranked = [item for item in capped_ranked if item.get("eligibility") != "complete"]
    complete_selected, complete_diversity = select_diverse_recommendations(complete_ranked, limit=len(complete_ranked))
    near_selected, near_diversity = select_diverse_recommendations(near_ranked, limit=len(near_ranked))
    # A complete and near-complete version of the same dish must not both appear.
    # Keep the complete version and remove duplicate families from the fallback tier.
    cross_tier_duplicate_count = 0
    globally_unique_near = []
    for item in near_selected:
        if any(are_near_duplicates(item, chosen) for chosen in complete_selected + globally_unique_near):
            cross_tier_duplicate_count += 1
            continue
        globally_unique_near.append(item)
    near_selected = globally_unique_near
    recommendations = complete_selected + near_selected
    recommendations, quality_metadata = audit_recommendations(recommendations)
    diversity_metadata = {
        **near_diversity,
        "complete_diversity_returned_count": len(complete_selected),
        "near_complete_diversity_returned_count": len(near_selected),
        "diversity_candidate_count": len(capped_ranked),
        "diversity_returned_count": len(recommendations),
        "diversity_strategy": "complete_first_global_recipe_family_deduplication_then_progressive_variety",
        "cross_tier_duplicate_count": cross_tier_duplicate_count,
    }
    for rank, item in enumerate(recommendations, 1):
        item["final_rank"] = rank
    return {
        "recommendations": recommendations,
        "grocery_suggestions": _build_grocery_suggestions(recommendations),
        "metadata": {
            **safety_metadata, **discovery.metadata, **realism_metadata, **nutrition_metadata, **score_metadata, **diversity_metadata, **quality_metadata,
            "returned_count": len(recommendations), "requested_limit": requested,
            "total_realistic_candidate_count": len(all_realistic),
            "filtered_candidate_count": len(filtered),
            "results_truncated": len(filtered) > requested,
            "active_meal_filters": list(meal_types or []), "active_cuisine_filters": list(cuisine_types or []),
            "ranking_phase": "phase_18_5_realism_filtered_family_deduped_inventory_balanced_ranking",
            "diversity_phase": "phase_18_4_recipe_family_dedupe_progressive_results",
            "smart_swap_phase": "phase_18_4_strict_same_family_role_and_context_validation",
            "realism_phase": "phase_18_5_conservative_novelty_suppression",
        },
    }
