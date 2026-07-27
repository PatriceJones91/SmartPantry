"""Translate internal recommendation-engine output into API contract v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from models.recommendation_api import RecommendationGenerateResponseV1

API_CONTRACT_VERSION = "1.0"
ENGINE_VERSION = "phase_17_adaptive_recommendation_learning_v1"


def _strip_debug_fields(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    for recommendation in recommendations:
        item = dict(recommendation)
        nutrition_fit = dict(item.get("nutrition_fit") or {})
        nutrition_fit.pop("feature_inputs", None)
        nutrition_fit.pop("error", None)
        item["nutrition_fit"] = nutrition_fit
        cleaned.append(item)
    return cleaned


def build_api_response(
    *,
    user_id: str,
    engine_result: Dict[str, Any],
    requested_limit: int,
    include_debug: bool,
) -> RecommendationGenerateResponseV1:
    recommendations = list(engine_result.get("recommendations") or [])
    if not include_debug:
        recommendations = _strip_debug_fields(recommendations)

    metadata = dict(engine_result.get("metadata") or {})
    metadata.update(
        {
            "returned_count": len(recommendations),
            "requested_limit": requested_limit,
            "api_contract_version": API_CONTRACT_VERSION,
            "engine_version": ENGINE_VERSION,
            "debug_included": include_debug,
        }
    )
    if not include_debug:
        metadata.pop("nutrition_fit_model_path", None)
        metadata.pop("nutrition_fit_model_load_error", None)
        metadata.pop("nutrition_fit_expected_features", None)

    return RecommendationGenerateResponseV1.model_validate(
        {
            "api_version": API_CONTRACT_VERSION,
            "generated_at": datetime.now(timezone.utc),
            "user_id": user_id,
            "recommendations": recommendations,
            "grocery_suggestions": engine_result.get("grocery_suggestions") or [],
            "metadata": metadata,
        }
    )
