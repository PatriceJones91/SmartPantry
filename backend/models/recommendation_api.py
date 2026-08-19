"""Versioned public API models for Smart Pantry recommendations.

These models are the boundary between the rebuilt Python engine and the React
frontend. Internal engine metadata may evolve, but the fields declared here are
stable for API contract version 1.0.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RecommendationGenerateRequestV1(BaseModel):
    user_id: str = Field(..., min_length=1)
    limit: int = Field(default=15, ge=1, le=15)
    candidate_limit: int = Field(default=300, ge=10, le=1000)
    meal_types: List[str] = Field(default_factory=list)
    cuisine_types: List[str] = Field(default_factory=list)
    expiry_window_days: int = Field(default=7, ge=0, le=30)
    include_debug: bool = False


class IngredientMatchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recipe_ingredient: str
    normalized_ingredient: str
    match_type: str
    pantry_item_id: str
    pantry_item_name: str
    expiration_state: str
    expires_on: Optional[str] = None
    days_until_expiration: Optional[int] = None

    # Recipe-native quantity data comes directly from smart_pantry_recipe_dataset.csv.
    # Exposing it here lets the frontend scale ingredient use by the number of
    # servings actually prepared without hard-coding meal-specific amounts.
    recipe_quantity: Optional[float] = None
    recipe_measure: Optional[str] = None
    recipe_weight_grams: Optional[float] = None
    recipe_text: Optional[str] = None


class NutritionSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    servings: Optional[float] = None
    reported_servings: Optional[float] = None
    servings_inferred: bool = False
    per_serving: Dict[str, Optional[float]] = Field(default_factory=dict)
    basis: Optional[str] = None


class NutritionFitResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str
    score_percent: Optional[float] = None
    score_out_of_15: Optional[float] = None
    grade: str
    reasons: List[str] = Field(default_factory=list)
    model_name: Optional[str] = None
    missing_features: List[str] = Field(default_factory=list)
    feature_inputs: Optional[Dict[str, float]] = None
    error: Optional[str] = None


class ScoreComponentResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    points: float
    max_points: float


class SmartScoreDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    score: float
    max_score: float
    version: str
    weights: Dict[str, float]
    breakdown: Dict[str, ScoreComponentResponse]
    reasons: List[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recipe_id: str
    recommendation_result_id: Optional[str] = None
    recipe_name: str
    recipe_url: str = ""
    final_rank: int = Field(..., ge=1)
    eligibility: Literal["complete", "near_complete"]
    eligibility_reason: str
    missing_main_ingredient_count: int = Field(default=0, ge=0, le=2)
    eligibility_tier: int = Field(default=0, ge=0, le=2)
    candidate_group: Literal["expiry_led_complete", "other_complete", "expiry_led_near_complete", "other_near_complete"]
    meal_types: List[str] = Field(default_factory=list)
    cuisine_types: List[str] = Field(default_factory=list)
    dish_types: List[str] = Field(default_factory=list)
    main_ingredients: List[str] = Field(default_factory=list)
    matched_ingredients: List[IngredientMatchResponse] = Field(default_factory=list)
    missing_ingredients: List[str] = Field(default_factory=list)
    smart_swaps: List[Dict[str, Any]] = Field(default_factory=list)
    expiring_ingredients: List[IngredientMatchResponse] = Field(default_factory=list)
    pantry_match_percent: float = Field(..., ge=0, le=100)
    nutrition: NutritionSummaryResponse
    nutrition_fit: NutritionFitResponse
    preference_fit: Dict[str, Any]
    smart_score: float = Field(..., ge=0, le=100)
    smart_score_details: SmartScoreDetailsResponse
    reasons: List[str] = Field(default_factory=list)
    diversity_signature: Dict[str, Any] = Field(default_factory=dict)
    recommendation_explanation: str = ""
    quality_validation: Dict[str, Any] = Field(default_factory=dict)


class RecommendationResponseMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    returned_count: int = Field(..., ge=0)
    requested_limit: int = Field(..., ge=1, le=15)
    api_contract_version: str
    engine_version: str
    debug_included: bool
    session_id: Optional[str] = None
    tracking_status: str = "not_attempted"
    tracking_schema_version: Optional[str] = None


class RecommendationGenerateResponseV1(BaseModel):
    api_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    user_id: str
    recommendations: List[RecommendationResponse]
    grocery_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: RecommendationResponseMetadata


class RecommendationContractInfoResponse(BaseModel):
    api_version: Literal["1.0"] = "1.0"
    engine_version: str
    maximum_recommendations: int = 15
    default_recommendations: int = 15
    default_expiry_window_days: int = 7
    eligibility_states_returned: List[str] = Field(default_factory=lambda: ["complete", "near_complete"])
    candidate_groups: List[str] = Field(
        default_factory=lambda: ["expiry_led_complete", "other_complete", "expiry_led_near_complete", "other_near_complete"]
    )
