from __future__ import annotations

from collections import Counter, defaultdict
import re
from typing import Any, Dict, Iterable, List, Set


def grocery_key(value: str) -> str:
    text = str(value or "").lower().strip()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    words: List[str] = []
    for word in text.split():
        if len(word) > 4 and word.endswith("ies"):
            word = f"{word[:-3]}y"
        elif len(word) > 4 and word.endswith("es") and not word.endswith(("cheese", "molasses")):
            word = word[:-2]
        elif len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us")):
            word = word[:-1]
        words.append(word)
    return " ".join(words)


def display_grocery_name(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(value or "").strip())
    return cleaned[:1].upper() + cleaned[1:] if cleaned else cleaned


def swap_missing_name(swap: Dict[str, Any]) -> str:
    return str(
        swap.get("needed")
        or swap.get("missing")
        or swap.get("missing_ingredient")
        or swap.get("ingredient")
        or ""
    ).strip()


def pantry_covers_name(pantry_keys: Set[str], missing_key: str) -> bool:
    if not missing_key:
        return True

    for pantry_key in pantry_keys:
        if pantry_key == missing_key:
            return True
        if len(pantry_key) >= 4 and len(missing_key) >= 4:
            if pantry_key in missing_key or missing_key in pantry_key:
                return True
    return False


def build_grocery_suggestions(
    result_rows: Iterable[Dict[str, Any]],
    pantry_items: Iterable[Dict[str, Any]],
    *,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    pantry_keys = {
        grocery_key(item.get("item_name"))
        for item in pantry_items
        if grocery_key(item.get("item_name"))
    }

    counts: Counter[str] = Counter()
    display_names: Dict[str, str] = {}
    meals_by_item: Dict[str, List[str]] = defaultdict(list)
    best_rank: Dict[str, int] = {}

    for result in result_rows:
        snapshot = result.get("recommendation_snapshot") or {}
        missing = snapshot.get("missing_ingredients") or []
        swaps = snapshot.get("smart_swaps") or []

        covered_by_swap = {
            grocery_key(swap_missing_name(swap))
            for swap in swaps
            if grocery_key(swap_missing_name(swap))
        }

        recipe_name = str(
            result.get("recipe_name")
            or snapshot.get("recipe_name")
            or "Recommended meal"
        )
        rank = int(result.get("final_rank") or snapshot.get("final_rank") or 9999)

        seen_in_recipe: Set[str] = set()
        for ingredient in missing:
            raw_name = ingredient.get("name") if isinstance(ingredient, dict) else ingredient
            key = grocery_key(raw_name)

            if (
                not key
                or key in seen_in_recipe
                or key in covered_by_swap
                or pantry_covers_name(pantry_keys, key)
            ):
                continue

            seen_in_recipe.add(key)
            counts[key] += 1
            display_names.setdefault(key, display_grocery_name(str(raw_name)))
            if recipe_name not in meals_by_item[key]:
                meals_by_item[key].append(recipe_name)
            best_rank[key] = min(best_rank.get(key, rank), rank)

    ordered_keys = sorted(
        counts,
        key=lambda key: (
            -counts[key],
            best_rank.get(key, 9999),
            display_names[key].lower(),
        ),
    )

    suggestions: List[Dict[str, Any]] = []
    for key in ordered_keys[:limit]:
        meal_count = counts[key]
        suggestions.append(
            {
                "item": display_names[key],
                "meal_count": meal_count,
                "needed_for": meals_by_item[key][:3],
                "label": f"{meal_count} meal" if meal_count == 1 else f"{meal_count} meals",
                "class_name": (
                    "high"
                    if meal_count >= 3
                    else "medium"
                    if meal_count == 2
                    else "suggested"
                ),
                "note": (
                    f"Needed for {meal_count} recommended meal"
                    if meal_count == 1
                    else f"Needed for {meal_count} recommended meals"
                ),
            }
        )

    return suggestions
