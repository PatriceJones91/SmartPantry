import logging

from fastapi import APIRouter, HTTPException

from config import get_settings, public_error_detail
from pydantic import BaseModel

from models.recommendation_api import (
    RecommendationContractInfoResponse,
    RecommendationGenerateRequestV1,
    RecommendationGenerateResponseV1,
)
from models.schemas import RecommendationActionRequest, RecommendationFeedbackRequest
from services.recommendations import generate_recommendations
from services.recommendations.api_adapter import ENGINE_VERSION, build_api_response
from services.recommendation_tracking import (
    build_action_row,
    persist_generation,
    prepare_generation_records,
)
from services.supabase_service import get_supabase

router = APIRouter()
logger = logging.getLogger("smart_pantry.recommendations")
settings = get_settings()



class GeneralFeedbackRequest(BaseModel):
    user_id: str
    feedback: str


@router.get("/contract", response_model=RecommendationContractInfoResponse)
def recommendation_contract():
    return RecommendationContractInfoResponse(engine_version=ENGINE_VERSION)


@router.post("/generate", response_model=RecommendationGenerateResponseV1)
def generate(payload: RecommendationGenerateRequestV1):
    try:
        supabase = get_supabase()
        pantry_response = supabase.table("sp2_pantry_items").select("*").eq("user_id", payload.user_id).execute()
        actions_response = None
        profile_response = (
            supabase.table("sp2_users")
            .select(
                "id, username, household_size, allergies, dietary_restrictions, "
                "preferred_meal_type, preferred_cuisine, avoid_foods, "
                "quick_meals_preferred, profile_notes"
            )
            .eq("id", payload.user_id)
            .single()
            .execute()
        )
        try:
            actions_response = (supabase.table("sp2_recommendation_actions").select("recipe_id, recipe_name, action, created_at").eq("user_id", payload.user_id).order("created_at", desc=True).limit(250).execute())
        except Exception:
            actions_response = None
    except Exception as exc:
        logger.exception("Could not load recommendation data user_id=%s", payload.user_id)
        raise HTTPException(
            status_code=503,
            detail=public_error_detail("Could not load pantry or profile data", exc, settings),
        ) from exc

    pantry = pantry_response.data or []
    profile = profile_response.data or None
    if not profile:
        raise HTTPException(status_code=404, detail="Participant profile was not found.")

    profile["_behavior_actions"] = (actions_response.data if actions_response else []) or []

    try:
        result = generate_recommendations(
            pantry,
            profile,
            limit=payload.candidate_limit,
            expiry_window_days=payload.expiry_window_days,
            include_nutrition_debug=payload.include_debug,
            meal_types=payload.meal_types,
            cuisine_types=payload.cuisine_types,
        )
        response_model = build_api_response(
            user_id=payload.user_id,
            engine_result=result,
            requested_limit=payload.limit,
            include_debug=payload.include_debug,
        )
        response_payload, session_row, result_rows = prepare_generation_records(
            user_id=payload.user_id,
            request_options={
                "limit": payload.limit,
                "candidate_limit": payload.candidate_limit,
                "expiry_window_days": payload.expiry_window_days,
                "include_debug": payload.include_debug,
                "meal_types": payload.meal_types,
                "cuisine_types": payload.cuisine_types,
            },
            response_payload=response_model.model_dump(mode="json"),
            pantry=pantry,
            profile=profile,
        )
        try:
            persist_generation(supabase, session_row, result_rows)
        except Exception:
            response_payload["metadata"]["tracking_status"] = "failed"
        return RecommendationGenerateResponseV1.model_validate(response_payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Recommendation engine failed user_id=%s", payload.user_id)
        raise HTTPException(
            status_code=500,
            detail=public_error_detail("The recommendation engine failed", exc, settings),
        ) from exc


@router.post("/action")
def save_action(payload: RecommendationActionRequest):
    try:
        row = build_action_row(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response = get_supabase().table("sp2_recommendation_actions").insert(row).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not save recommendation action.")
    return response.data[0]


@router.post("/feedback")
def save_feedback(payload: RecommendationFeedbackRequest):
    if not payload.comments.strip() and payload.rating is None and payload.liked is None:
        raise HTTPException(status_code=400, detail="Feedback requires a comment, rating, or like/dislike value.")
    row = payload.model_dump()
    row["comments"] = payload.comments.strip()
    response = get_supabase().table("sp2_recommendation_feedback").insert(row).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not save recommendation feedback.")
    return response.data[0]


@router.post("/general-feedback")
def save_general_feedback(payload: GeneralFeedbackRequest):
    feedback_text = (payload.feedback or "").strip()
    if not feedback_text:
        raise HTTPException(status_code=400, detail="Feedback message is required.")
    response = (
        get_supabase().table("sp2_recommendation_feedback")
        .insert({"user_id": payload.user_id, "feedback_type": "general", "comments": feedback_text})
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not save general feedback.")
    return {"status": "ok", "message": "Feedback saved. Thank you.", "feedback": response.data[0]}


@router.get("/history/{user_id}")
def history(user_id: str):
    response = (
        get_supabase().table("sp2_recommendation_actions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []
