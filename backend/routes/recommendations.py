from fastapi import APIRouter, HTTPException

from models.schemas import RecommendationGenerateRequest, RecommendationActionRequest
from services.supabase_service import get_supabase
from services.recommendation_service import generate_recommendations, grocery_suggestions

router = APIRouter()


@router.post("/generate")
def generate(payload: RecommendationGenerateRequest):
    supabase = get_supabase()

    pantry_response = (
        supabase.table("sp2_pantry_items")
        .select("*")
        .eq("user_id", payload.user_id)
        .execute()
    )

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

    pantry_items = pantry_response.data or []
    profile = profile_response.data or {}

    recommendations = generate_recommendations(pantry_items, profile)

    return {
        "recommendations": recommendations,
        "grocery_suggestions": grocery_suggestions(recommendations),
    }


@router.post("/action")
def save_action(payload: RecommendationActionRequest):
    supabase = get_supabase()

    response = (
        supabase.table("sp2_recommendation_logs")
        .insert(
            {
                "user_id": payload.user_id,
                "recipe_name": payload.recipe_name,
                "action": payload.action,
                "score": payload.score,
                "feedback": payload.feedback or "",
                "used_ingredients": payload.used_ingredients or [],
            }
        )
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=400, detail="Could not save recommendation action.")

    return response.data[0]


@router.get("/history/{user_id}")
def history(user_id: str):
    supabase = get_supabase()

    response = (
        supabase.table("sp2_recommendation_logs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []
