"""Shared response contracts for the rebuilt recommendation engine."""

from typing import Any, Dict, List, Optional, TypedDict


class IngredientMatch(TypedDict, total=False):
    pantry_item_id: str
    pantry_name: str
    recipe_ingredient: str
    normalized_ingredient: str
    match_type: str
    expires_on: Optional[str]
    days_until_expiration: Optional[int]


class RecommendationResult(TypedDict, total=False):
    recipe_id: str
    recipe_name: str
    recipe_url: str
    matched_ingredients: List[IngredientMatch]
    missing_ingredients: List[str]
    expiring_ingredients: List[IngredientMatch]
    pantry_match_percent: float
    nutrition_fit: Optional[float]
    preference_fit: float
    smart_score: float
    eligibility: str
    reasons: List[str]
    metadata: Dict[str, Any]
