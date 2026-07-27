"""Pantry-to-recipe matching built on the shared ingredient normalizer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .ingredient_normalizer import ingredients_equivalent, normalize_ingredient


@dataclass(frozen=True)
class PantryItem:
    pantry_item_id: str
    item_name: str
    normalized_name: str
    quantity: Optional[float]
    unit: str
    expiration_date: Optional[str]


@dataclass(frozen=True)
class IngredientMatchResult:
    recipe_ingredient: str
    normalized_ingredient: str
    matched: bool
    match_type: str
    pantry_item_id: Optional[str] = None
    pantry_item_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipe_ingredient": self.recipe_ingredient,
            "normalized_ingredient": self.normalized_ingredient,
            "matched": self.matched,
            "match_type": self.match_type,
            "pantry_item_id": self.pantry_item_id,
            "pantry_item_name": self.pantry_item_name,
        }


def _optional_float(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


def prepare_pantry_items(raw_items: Iterable[Dict[str, Any]]) -> List[PantryItem]:
    """Convert Supabase pantry rows into stable matcher records."""
    prepared: List[PantryItem] = []
    for raw in raw_items:
        item_name = " ".join(str(raw.get("item_name") or "").strip().split())
        normalized = normalize_ingredient(item_name).canonical
        if not item_name or not normalized:
            continue
        prepared.append(
            PantryItem(
                pantry_item_id=str(raw.get("id") or ""),
                item_name=item_name,
                normalized_name=normalized,
                quantity=_optional_float(raw.get("quantity")),
                unit=str(raw.get("unit") or "").strip(),
                expiration_date=(str(raw.get("expiration_date")) if raw.get("expiration_date") else None),
            )
        )
    return prepared


def match_recipe_ingredient(
    recipe_ingredient: str,
    pantry_items: Sequence[PantryItem],
) -> IngredientMatchResult:
    target = normalize_ingredient(recipe_ingredient)
    if not target.canonical:
        return IngredientMatchResult(recipe_ingredient, "", False, "none")

    # Canonical equality is preferred and deterministic.
    for item in pantry_items:
        if target.canonical == item.normalized_name:
            return IngredientMatchResult(
                recipe_ingredient=recipe_ingredient,
                normalized_ingredient=target.canonical,
                matched=True,
                match_type="exact" if recipe_ingredient.strip().lower() == item.item_name.strip().lower() else "alias",
                pantry_item_id=item.pantry_item_id,
                pantry_item_name=item.item_name,
            )

    for item in pantry_items:
        if ingredients_equivalent(recipe_ingredient, item.item_name):
            return IngredientMatchResult(
                recipe_ingredient=recipe_ingredient,
                normalized_ingredient=target.canonical,
                matched=True,
                match_type="equivalent",
                pantry_item_id=item.pantry_item_id,
                pantry_item_name=item.item_name,
            )

    return IngredientMatchResult(
        recipe_ingredient=recipe_ingredient,
        normalized_ingredient=target.canonical,
        matched=False,
        match_type="none",
    )


def match_recipe_ingredients(
    recipe_ingredients: Iterable[str],
    raw_pantry_items: Iterable[Dict[str, Any]],
) -> List[IngredientMatchResult]:
    pantry_items = prepare_pantry_items(raw_pantry_items)
    return [match_recipe_ingredient(name, pantry_items) for name in recipe_ingredients]
