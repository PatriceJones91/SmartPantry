"""Phase 8 diversity-aware final recommendation selection.

Smart Score establishes quality. This module selects a varied subset without
re-scoring recipes or allowing a weak recipe to leapfrog the whole list.
It protects the strongest overall, expiration-led, and Nutrition Fit candidates,
then fills remaining slots with a deterministic maximum-marginal-relevance pass.
"""

from __future__ import annotations

from collections import Counter
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

_TITLE_STOPWORDS = {
    "a", "an", "and", "easy", "quick", "best", "classic", "simple", "homemade",
    "recipe", "style", "with", "the", "of", "for", "healthy", "delicious",
    "favorite", "famous", "original", "copycat", "almost", "perfect", "ultimate",
    "sherry", "diane", "grandma", "moms", "mom", "restaurant", "kfc",
}

_PROTEIN_GROUPS = {
    "chicken": {"chicken", "poultry"},
    "turkey": {"turkey"},
    "beef": {"beef", "steak", "ground beef", "hamburger", "burger"},
    "lamb": {"lamb", "lamb chop", "mutton"},
    "pork": {"pork", "ham", "bacon", "sausage"},
    "fish": {"salmon", "tuna", "cod", "tilapia", "fish", "trout"},
    "shellfish": {"shrimp", "prawn", "crab", "lobster", "scallop"},
    "egg": {"egg"},
    "tofu_tempeh": {"tofu", "tempeh"},
    "beans_legumes": {"bean", "beans", "lentil", "lentils", "chickpea", "chickpeas"},
}

_STARCH_GROUPS = {
    "pasta": {"pasta", "spaghetti", "penne", "linguine", "noodle", "noodles"},
    "rice": {"rice", "risotto"},
    "potato": {"potato", "potatoes", "sweet potato"},
    "bread": {"bread", "tortilla", "bun", "roll", "pita"},
    "grain": {"quinoa", "barley", "couscous", "oats", "farro"},
}


def _tokens(value: Any) -> Set[str]:
    text = str(value or "").lower().replace("&", " and ")
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text)
        if token and token not in _TITLE_STOPWORDS
    }


def _list_tokens(values: Iterable[Any]) -> Set[str]:
    result: Set[str] = set()
    for value in values or []:
        result.update(_tokens(value))
    return result


def _canonical_title(candidate: Mapping[str, Any]) -> str:
    return " ".join(sorted(_tokens(candidate.get("recipe_name"))))


def _recipe_family(candidate: Mapping[str, Any]) -> str:
    """Return a human-facing recipe family used for strong duplicate control.

    Dataset titles often add owner names or marketing adjectives to the same dish
    (for example, "Homemade Chicken Nuggets" and "Sherry's Homemade Chicken
    Nuggets").  Those should compete for one recommendation slot.
    """
    text = " ".join(sorted(_tokens(candidate.get("recipe_name"))))
    rules = (
        ("chicken_nuggets", ("chicken", "nugget")),
        ("fried_chicken", ("fried", "chicken")),
        ("mashed_potatoes", ("mashed", "potato")),
        ("mac_and_cheese", ("mac", "cheese")),
        ("mac_and_cheese", ("macaroni", "cheese")),
        ("hamburger", ("hamburger",)),
        ("hamburger", ("burger",)),
        ("potato_soup", ("potato", "soup")),
        ("grilled_cheese", ("grilled", "cheese")),
        ("omelet", ("omelet",)),
        ("omelet", ("omelette",)),
        ("chicken_parmesan", ("chicken", "parmesan")),
    )
    tokens = set(text.split())
    for family, required in rules:
        if all(term in tokens for term in required):
            return family
    return ""


def _ingredient_tokens(candidate: Mapping[str, Any]) -> Set[str]:
    return _list_tokens(candidate.get("main_ingredients") or [])


def _first_group(tokens: Set[str], groups: Mapping[str, Set[str]]) -> str:
    joined = " ".join(sorted(tokens))
    for group, terms in groups.items():
        if any(term in tokens or term in joined for term in terms):
            return group
    return "other"


def recipe_signature(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    title_tokens = _tokens(candidate.get("recipe_name"))
    ingredient_tokens = _ingredient_tokens(candidate)
    dish_tokens = _list_tokens(candidate.get("dish_types") or [])
    cuisine_tokens = _list_tokens(candidate.get("cuisine_types") or [])
    meal_tokens = _list_tokens(candidate.get("meal_types") or [])
    all_food_tokens = title_tokens | ingredient_tokens
    return {
        "canonical_title": _canonical_title(candidate),
        "recipe_family": _recipe_family(candidate),
        "title_tokens": title_tokens,
        "ingredient_tokens": ingredient_tokens,
        "dish_family": next(iter(sorted(dish_tokens)), "other"),
        "cuisine_family": next(iter(sorted(cuisine_tokens)), "other"),
        "meal_family": next(iter(sorted(meal_tokens)), "other"),
        "protein_family": _first_group(all_food_tokens, _PROTEIN_GROUPS),
        "starch_family": _first_group(all_food_tokens, _STARCH_GROUPS),
    }


def _jaccard(left: Set[str], right: Set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def recipe_similarity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    """Return a transparent 0-1 similarity estimate for diversity decisions."""
    a = recipe_signature(left)
    b = recipe_signature(right)
    title = _jaccard(a["title_tokens"], b["title_tokens"])
    ingredients = _jaccard(a["ingredient_tokens"], b["ingredient_tokens"])
    categorical = sum(
        a[key] != "other" and a[key] == b[key]
        for key in ("dish_family", "protein_family", "starch_family", "cuisine_family")
    ) / 4.0
    return round((0.30 * title) + (0.50 * ingredients) + (0.20 * categorical), 4)


def are_near_duplicates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    a = recipe_signature(left)
    b = recipe_signature(right)
    if a["canonical_title"] and a["canonical_title"] == b["canonical_title"]:
        return True
    if a.get("recipe_family") and a.get("recipe_family") == b.get("recipe_family"):
        return True
    ingredient_similarity = _jaccard(a["ingredient_tokens"], b["ingredient_tokens"])
    title_similarity = _jaccard(a["title_tokens"], b["title_tokens"])
    # Stronger dataset-level deduplication: same dish with owner/marketing words
    # should not reappear dozens of cards later merely because the title differs.
    return (
        ingredient_similarity >= 0.76
        or (ingredient_similarity >= 0.58 and title_similarity >= 0.50)
        or (title_similarity >= 0.72 and ingredient_similarity >= 0.40)
    )


def _score(candidate: Mapping[str, Any]) -> float:
    try:
        return float(candidate.get("smart_score") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _nutrition(candidate: Mapping[str, Any]) -> float:
    try:
        return float((candidate.get("nutrition_fit") or {}).get("score_percent") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _expiry_points(candidate: Mapping[str, Any]) -> float:
    try:
        return float(
            ((candidate.get("smart_score_details") or {}).get("breakdown") or {})
            .get("expiration_priority", {})
            .get("points", 0.0)
        )
    except (TypeError, ValueError):
        return 0.0


def _can_add(candidate: Mapping[str, Any], selected: Sequence[Mapping[str, Any]]) -> bool:
    return not any(are_near_duplicates(candidate, existing) for existing in selected)


def _anchor_candidates(ranked: Sequence[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Protect quality while ensuring major protein families get early coverage.

    Expiration remains a useful signal, but it may not reserve several anchor
    positions for the same protein. A strong shrimp, beef, or lamb candidate can
    therefore appear before a fourth chicken variation.
    """
    anchors: List[Dict[str, Any]] = []
    if not ranked or not limit:
        return anchors

    anchors.append(ranked[0])
    top_score = _score(ranked[0])

    # Add the strongest realistic candidate from distinct protein families.
    # The score floor prevents diversity from promoting weak or impractical meals.
    protein_target = 0 if limit < 5 else min(6, max(2, limit // 4))
    represented = {recipe_signature(ranked[0])["protein_family"]}
    for item in ranked[1:]:
        if len(anchors) >= limit or len(represented - {"other"}) >= protein_target:
            break
        family = recipe_signature(item)["protein_family"]
        if family == "other" or family in represented:
            continue
        if _score(item) < max(45.0, top_score - 14.0):
            continue
        if _can_add(item, anchors):
            anchors.append(item)
            represented.add(family)

    # Keep at most two expiration-led anchors and avoid repeating a protein when
    # a different expiring-food candidate is available.
    expiry_target = min(2, max(1, limit // 8)) if any(item.get("expiring_ingredients") for item in ranked) else 0
    expiry_ranked = sorted(
        (item for item in ranked if item.get("expiring_ingredients")),
        key=lambda item: (-_expiry_points(item), -_score(item), str(item.get("recipe_id") or "")),
    )
    expiry_added = 0
    for item in expiry_ranked:
        if expiry_added >= expiry_target or len(anchors) >= limit:
            break
        if item in anchors or not _can_add(item, anchors):
            continue
        family = recipe_signature(item)["protein_family"]
        same_family_expiry = any(
            existing.get("expiring_ingredients")
            and recipe_signature(existing)["protein_family"] == family
            for existing in anchors
        )
        if same_family_expiry:
            continue
        anchors.append(item)
        expiry_added += 1

    nutrition_target = min(2, max(1, limit // 8)) if ranked else 0
    nutrition_ranked = sorted(
        ranked,
        key=lambda item: (-_nutrition(item), -_score(item), str(item.get("recipe_id") or "")),
    )
    nutrition_added = 0
    for item in nutrition_ranked:
        if nutrition_added >= nutrition_target or len(anchors) >= limit:
            break
        if item not in anchors and _can_add(item, anchors) and not _exceeds_family_caps(item, anchors):
            anchors.append(item)
            nutrition_added += 1
    return anchors[:limit]


def _meal_category(candidate: Mapping[str, Any]) -> str:
    text = " ".join([str(candidate.get("recipe_name") or ""), *(candidate.get("meal_types") or []), *(candidate.get("dish_types") or [])]).lower()
    if any(term in text for term in ("dessert", "cake", "cupcake", "cookie", "candy", "pudding", "sweet")):
        return "dessert"
    if any(term in text for term in ("breakfast", "brunch", "pancake", "waffle", "scramble")):
        return "breakfast"
    if any(term in text for term in ("snack", "appetizer", "starter")):
        return "snack"
    return "main_meal"


def _exceeds_family_caps(candidate: Mapping[str, Any], selected: Sequence[Mapping[str, Any]]) -> bool:
    """Prevent a 15-card list from being dominated by one protein or dish style."""
    signature = recipe_signature(candidate)
    selected_signatures = [recipe_signature(item) for item in selected]
    protein_count = sum(sig["protein_family"] == signature["protein_family"] for sig in selected_signatures)
    dish_count = sum(sig["dish_family"] == signature["dish_family"] for sig in selected_signatures)
    protein_dish_count = sum(
        sig["protein_family"] == signature["protein_family"]
        and sig["dish_family"] == signature["dish_family"]
        for sig in selected_signatures
    )
    meal_category = _meal_category(candidate)
    meal_category_count = sum(_meal_category(item) == meal_category for item in selected)
    if meal_category == "dessert" and meal_category_count >= 2:
        return True
    if meal_category == "snack" and meal_category_count >= 2:
        return True
    if signature["protein_family"] != "other" and protein_count >= 3:
        return True
    if signature["dish_family"] != "other" and dish_count >= 4:
        return True
    return signature["protein_family"] != "other" and signature["dish_family"] != "other" and protein_dish_count >= 2


def select_diverse_recommendations(
    ranked_candidates: Sequence[Dict[str, Any]],
    *,
    limit: int = 15,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Select a varied final set while keeping Smart Score as the base rank."""
    requested_limit = max(0, int(limit))
    ranked = list(ranked_candidates)
    if not requested_limit or not ranked:
        return [], {
            "diversity_version": "phase_18_4_recipe_family_dedupe_v1",
            "diversity_candidate_count": len(ranked),
            "diversity_returned_count": 0,
            "near_duplicates_skipped": 0,
            "diversity_anchor_count": 0,
        }

    rank_index = {str(item.get("recipe_id")): index for index, item in enumerate(ranked)}
    selected = _anchor_candidates(ranked, requested_limit)
    selected_ids = {str(item.get("recipe_id")) for item in selected}
    duplicate_skips = 0

    family_counts: Dict[str, Counter] = {
        "dish_family": Counter(),
        "protein_family": Counter(),
        "starch_family": Counter(),
        "cuisine_family": Counter(),
    }
    for item in selected:
        signature = recipe_signature(item)
        for key in family_counts:
            family_counts[key][signature[key]] += 1

    while len(selected) < requested_limit:
        best = None
        best_utility = float("-inf")
        for candidate in ranked:
            candidate_id = str(candidate.get("recipe_id"))
            if candidate_id in selected_ids:
                continue
            if not _can_add(candidate, selected):
                duplicate_skips += 1
                continue
            if _exceeds_family_caps(candidate, selected):
                continue

            signature = recipe_signature(candidate)
            max_similarity = max((recipe_similarity(candidate, item) for item in selected), default=0.0)
            family_penalty = 0.0
            family_penalty += max(0, family_counts["dish_family"][signature["dish_family"]] - 1) * 2.0
            family_penalty += max(0, family_counts["protein_family"][signature["protein_family"]] - 2) * 1.5
            family_penalty += max(0, family_counts["starch_family"][signature["starch_family"]] - 2) * 1.0
            family_penalty += max(0, family_counts["cuisine_family"][signature["cuisine_family"]] - 2) * 0.75
            rank_penalty = rank_index.get(candidate_id, len(ranked)) * 0.05
            utility = _score(candidate) - (max_similarity * 18.0) - family_penalty - rank_penalty
            if utility > best_utility:
                best_utility = utility
                best = candidate

        if best is None:
            # Relax family caps only after the varied pool is exhausted, while
            # still refusing near-duplicates. This keeps the requested count.
            remaining = [
                candidate for candidate in ranked
                if str(candidate.get("recipe_id")) not in selected_ids
                and _can_add(candidate, selected)
            ]
            if not remaining:
                break
            best = max(
                remaining,
                key=lambda candidate: (
                    _score(candidate) - max((recipe_similarity(candidate, item) for item in selected), default=0.0) * 22.0,
                    -rank_index.get(str(candidate.get("recipe_id")), len(ranked)),
                ),
            )
        selected.append(best)
        selected_ids.add(str(best.get("recipe_id")))
        signature = recipe_signature(best)
        for key in family_counts:
            family_counts[key][signature[key]] += 1

    # Keep the diversity-selection order. Smart Score remains the base utility,
    # but progressive results must not collapse back into repeated recipe families.
    for final_rank, item in enumerate(selected, start=1):
        item["final_rank"] = final_rank
        signature = recipe_signature(item)
        item["diversity_signature"] = {
            **signature,
            "title_tokens": sorted(signature["title_tokens"]),
            "ingredient_tokens": sorted(signature["ingredient_tokens"]),
        }

    duplicate_candidates_excluded = sum(
        1
        for candidate in ranked
        if str(candidate.get("recipe_id")) not in selected_ids
        and any(are_near_duplicates(candidate, chosen) for chosen in selected)
    )

    metadata = {
        "diversity_version": "phase_18_4_recipe_family_dedupe_v1",
        "diversity_strategy": "quality_first_recipe_family_dedupe_protein_coverage_and_progressive_variety",
        "diversity_candidate_count": len(ranked),
        "diversity_returned_count": len(selected),
        "diversity_requested_limit": requested_limit,
        "diversity_anchor_count": len(_anchor_candidates(ranked, requested_limit)),
        "near_duplicates_skipped": max(duplicate_skips, duplicate_candidates_excluded),
        "near_duplicate_candidates_excluded": duplicate_candidates_excluded,
        "selected_expiry_led_count": sum(bool(item.get("expiring_ingredients")) for item in selected),
        "selected_unique_dish_families": len({recipe_signature(item)["dish_family"] for item in selected}),
        "selected_unique_protein_families": len({recipe_signature(item)["protein_family"] for item in selected}),
        "selected_unique_starch_families": len({recipe_signature(item)["starch_family"] for item in selected}),
        "selected_meal_category_counts": {category: sum(_meal_category(item) == category for item in selected) for category in ("main_meal", "breakfast", "snack", "dessert")},
        "highest_smart_score_preserved": bool(selected and ranked and selected[0].get("recipe_id") == ranked[0].get("recipe_id")),
    }
    return selected, metadata
