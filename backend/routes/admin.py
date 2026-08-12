from fastapi import APIRouter
from services.supabase_service import table, rows

router = APIRouter()


@router.get("/summary")
def summary():
    users = rows(table("sp2_users").select("*").execute())
    pantry = rows(table("sp2_pantry_items").select("*").execute())
    surveys = rows(table("sp2_surveys").select("*").execute())
    actions = rows(table("sp2_recommendation_actions").select("*").execute())
    sessions = rows(table("sp2_recommendation_sessions").select("id").execute())
    made = [log for log in actions if log.get("action") == "made"]
    saved = [log for log in actions if log.get("action") == "saved"]
    return {
        "participants": len([u for u in users if u.get("role") == "participant"]),
        "pantry_items": len(pantry),
        "survey_responses": len(surveys),
        "recommendation_sessions": len(sessions),
        "recommendation_actions": len(actions),
        "meals_made": len(made),
        "meals_saved": len(saved),
    }


@router.get("/users")
def users():
    return rows(table("sp2_users").select("id, username, role, created_at").execute())


@router.get("/surveys")
def surveys():
    return rows(table("sp2_surveys").select("*").order("created_at", desc=True).execute())


@router.get("/pantry")
def pantry():
    return rows(table("sp2_pantry_items").select("*").order("created_at", desc=True).execute())


@router.get("/recommendation-logs")
def recommendation_logs():
    return rows(table("sp2_recommendation_actions").select("*").order("created_at", desc=True).execute())


@router.get("/recommendation-sessions")
def recommendation_sessions():
    return rows(table("sp2_recommendation_sessions").select("*").order("generated_at", desc=True).execute())
