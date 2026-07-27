"""Typed recipe data access for the rebuilt recommendation engine.

This module owns only dataset parsing and stable recipe identity. It contains no
pantry matching, expiration, profile, ranking, or scoring rules.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "smart_pantry_recipe_dataset.csv"


@dataclass(frozen=True)
class RecipeIngredient:
    food: str
    text: str
    weight: Optional[float] = None
    measure: Optional[str] = None
    quantity: Optional[float] = None


@dataclass(frozen=True)
class RecipeRecord:
    recipe_id: str
    recipe_name: str
    clean_recipe_name: str
    meal_types: List[str]
    cuisine_types: List[str]
    dish_types: List[str]
    ingredients: List[RecipeIngredient]
    main_ingredients: List[str]
    calories: Optional[float]
    protein: Optional[float]
    carbs: Optional[float]
    fat: Optional[float]
    servings: Optional[float]
    url: str
    everyday_fit_score: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _display_recipe_name(value: Any) -> str:
    text = _clean_text(value)
    # Dataset titles often carry scraped suffixes that look unpolished in cards.
    text = re.sub(r"^recipe\s*:?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+(?:recipes?|recipe ideas?)\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text).strip(" -|:")
    return text or "Untitled Recipe"


def _optional_float(value: Any) -> Optional[float]:
    text = _clean_text(value)
    if not text:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _parse_list(value: Any) -> List[Any]:
    """Parse dataset list fields stored as JSON or Python literals."""
    if isinstance(value, list):
        return value
    text = _clean_text(value)
    if not text:
        return []
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(text)
            return parsed if isinstance(parsed, list) else []
        except (ValueError, SyntaxError, json.JSONDecodeError):
            continue
    return []


def _parse_string_list(value: Any) -> List[str]:
    result: List[str] = []
    for item in _parse_list(value):
        cleaned = _clean_text(item).lower()
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def _parse_ingredients(value: Any) -> List[RecipeIngredient]:
    ingredients: List[RecipeIngredient] = []
    for raw in _parse_list(value):
        if not isinstance(raw, dict):
            continue
        food = _clean_text(raw.get("food"))
        text = _clean_text(raw.get("text"))
        if not food and not text:
            continue
        ingredients.append(
            RecipeIngredient(
                food=food,
                text=text or food,
                weight=_optional_float(raw.get("weight")),
                measure=_clean_text(raw.get("measure")) or None,
                quantity=_optional_float(raw.get("quantity")),
            )
        )
    return ingredients


def _stable_recipe_id(row: Dict[str, str]) -> str:
    """Return a deterministic ID that stays stable across imports/deployments."""
    identity = "|".join(
        [
            _clean_text(row.get("url")).lower(),
            _clean_text(row.get("clean_recipe_name") or row.get("recipe_name")).lower(),
        ]
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return f"recipe_{digest}"


def parse_recipe_row(row: Dict[str, str]) -> RecipeRecord:
    source_name = _clean_text(row.get("recipe_name"))
    clean_name = _clean_text(row.get("clean_recipe_name")) or source_name
    recipe_name = _display_recipe_name(clean_name or source_name)
    return RecipeRecord(
        recipe_id=_stable_recipe_id(row),
        recipe_name=recipe_name,
        clean_recipe_name=_display_recipe_name(clean_name or recipe_name),
        meal_types=_parse_string_list(row.get("meal_type")),
        cuisine_types=_parse_string_list(row.get("cuisine_type")),
        dish_types=_parse_string_list(row.get("dish_type")),
        ingredients=_parse_ingredients(row.get("ingredients")),
        main_ingredients=_parse_string_list(row.get("main_ingredients")),
        calories=_optional_float(row.get("calories")),
        protein=_optional_float(row.get("protein")),
        carbs=_optional_float(row.get("carbs")),
        fat=_optional_float(row.get("fat")),
        servings=_optional_float(row.get("servings")),
        url=_clean_text(row.get("url")),
        everyday_fit_score=_optional_float(row.get("everyday_fit_score")),
    )


@lru_cache(maxsize=1)
def load_recipe_rows() -> List[Dict[str, str]]:
    """Load raw rows for audits and migration tools."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Recipe dataset not found: {DATASET_PATH}")
    with DATASET_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@lru_cache(maxsize=1)
def load_recipes() -> List[RecipeRecord]:
    """Load parsed recipes with deterministic IDs and typed fields."""
    return [parse_recipe_row(row) for row in load_recipe_rows()]


def dataset_audit() -> Dict[str, Any]:
    """Return a compact quality report without changing recommendation behavior."""
    recipes = load_recipes()
    ids = [recipe.recipe_id for recipe in recipes]
    urls = [recipe.url for recipe in recipes if recipe.url]
    return {
        "dataset_path": str(DATASET_PATH),
        "recipe_count": len(recipes),
        "unique_recipe_ids": len(set(ids)),
        "duplicate_recipe_ids": len(ids) - len(set(ids)),
        "recipes_without_main_ingredients": sum(not r.main_ingredients for r in recipes),
        "recipes_without_ingredient_details": sum(not r.ingredients for r in recipes),
        "recipes_without_url": sum(not r.url for r in recipes),
        "duplicate_urls": len(urls) - len(set(urls)),
        "recipes_without_complete_nutrition": sum(
            any(v is None for v in (r.calories, r.protein, r.carbs, r.fat, r.servings))
            for r in recipes
        ),
    }
