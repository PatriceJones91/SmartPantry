"""Supabase persistence for recommendation research events.

The recommendation engine remains deterministic and database-independent. This
module records what was generated and how participants interacted with it.
Tracking failures never alter ranking or eligibility decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4

from services.recommendations.api_adapter import API_CONTRACT_VERSION, ENGINE_VERSION

NUTRITION_MODEL_VERSION = "random_forest_nutrition_fit_v1"
TRACKING_SCHEMA_VERSION = "1.0"
ALLOWED_ACTIONS = {"viewed", "opened_recipe", "saved", "made", "used_elsewhere", "not_used", "custom_meal", "skipped", "dismissed"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _snapshot_pantry(pantry: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    allowed = {
        "id", "item_name", "category", "quantity", "unit", "container_type",
        "expiration_date", "status", "barcode", "brand", "source", "notes",
    }
    return [{key: item.get(key) for key in allowed if key in item} for item in pantry]


def _snapshot_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {
        "id", "username", "household_size", "allergies", "dietary_restrictions",
        "preferred_meal_type", "preferred_cuisine", "avoid_foods",
        "quick_meals_preferred", "profile_notes",
    }
    return {key: profile.get(key) for key in allowed if key in profile}


def prepare_generation_records(
    *,
    user_id: str,
    request_options: Dict[str, Any],
    response_payload: Dict[str, Any],
    pantry: List[Dict[str, Any]],
    profile: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """Add stable tracking IDs and create rows for sessions/results."""
    enriched = dict(response_payload)
    enriched["metadata"] = dict(enriched.get("metadata") or {})
    recommendations = [dict(item) for item in enriched.get("recommendations") or []]

    session_id = str(uuid4())
    created_at = utc_now_iso()
    enriched["metadata"].update(
        {
            "session_id": session_id,
            "tracking_status": "recorded",
            "tracking_schema_version": TRACKING_SCHEMA_VERSION,
        }
    )

    session_row = {
        "id": session_id,
        "user_id": user_id,
        "generated_at": enriched.get("generated_at") or created_at,
        "requested_limit": request_options.get("limit", 15),
        "expiry_window_days": request_options.get("expiry_window_days", 7),
        "returned_count": len(recommendations),
        "engine_version": ENGINE_VERSION,
        "api_contract_version": API_CONTRACT_VERSION,
        "nutrition_model_version": NUTRITION_MODEL_VERSION,
        "tracking_schema_version": TRACKING_SCHEMA_VERSION,
        "pantry_snapshot": _snapshot_pantry(pantry),
        "profile_snapshot": _snapshot_profile(profile),
        "request_options": request_options,
        "generation_metadata": enriched.get("metadata") or {},
    }

    result_rows: List[Dict[str, Any]] = []
    for recommendation in recommendations:
        result_id = str(uuid4())
        recommendation["recommendation_result_id"] = result_id
        nutrition_fit = recommendation.get("nutrition_fit") or {}
        result_rows.append(
            {
                "id": result_id,
                "session_id": session_id,
                "user_id": user_id,
                "recipe_id": recommendation.get("recipe_id"),
                "recipe_name": recommendation.get("recipe_name"),
                "final_rank": recommendation.get("final_rank"),
                "candidate_group": recommendation.get("candidate_group"),
                "smart_score": recommendation.get("smart_score"),
                "nutrition_fit_score": nutrition_fit.get("score_percent"),
                "pantry_match_percent": recommendation.get("pantry_match_percent"),
                "uses_expiring_ingredients": bool(recommendation.get("expiring_ingredients")),
                "expiring_ingredient_count": len(recommendation.get("expiring_ingredients") or []),
                "matched_ingredient_count": len(recommendation.get("matched_ingredients") or []),
                "recommendation_snapshot": recommendation,
                "shown_at": created_at,
            }
        )

    enriched["recommendations"] = recommendations
    return enriched, session_row, result_rows


def persist_generation(supabase: Any, session_row: Dict[str, Any], result_rows: List[Dict[str, Any]]) -> None:
    session_response = supabase.table("sp2_recommendation_sessions").insert(session_row).execute()
    if not session_response.data:
        raise RuntimeError("Recommendation session was not recorded.")
    if result_rows:
        result_response = supabase.table("sp2_recommendation_results").insert(result_rows).execute()
        if len(result_response.data or []) != len(result_rows):
            raise RuntimeError("Not all recommendation results were recorded.")


def build_action_row(payload: Dict[str, Any]) -> Dict[str, Any]:
    action = str(payload.get("action") or "").strip().lower()
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"Unsupported recommendation action: {action}")
    return {
        "user_id": payload["user_id"],
        "session_id": payload["session_id"],
        "recommendation_result_id": payload.get("recommendation_result_id"),
        "recipe_id": payload["recipe_id"],
        "recipe_name": payload["recipe_name"],
        "action": action,
        "smart_score": payload.get("smart_score"),
        "metadata": payload.get("metadata") or {},
    }
