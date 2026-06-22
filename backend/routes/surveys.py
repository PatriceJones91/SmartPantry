from fastapi import APIRouter, HTTPException
from models.schemas import SurveySubmit
from services.supabase_service import table, rows, row

router = APIRouter()

@router.post("")
def submit_survey(payload: SurveySubmit):
    if payload.survey_type not in ["pre", "post"]:
        raise HTTPException(status_code=400, detail="survey_type must be pre or post.")
    existing = table("sp2_surveys").select("*").eq("user_id", payload.user_id).eq("survey_type", payload.survey_type).execute()
    data = {"user_id": payload.user_id, "survey_type": payload.survey_type, "responses": payload.responses, "comments": payload.comments or ""}
    if existing.data:
        survey_id = existing.data[0]["id"]
        response = table("sp2_surveys").update(data).eq("id", survey_id).execute()
    else:
        response = table("sp2_surveys").insert(data).execute()
    return row(response)

@router.get("/status/{user_id}")
def survey_status(user_id: str):
    response = table("sp2_surveys").select("*").eq("user_id", user_id).execute()
    surveys = rows(response)
    completed = {item["survey_type"]: True for item in surveys}
    return {"pre": completed.get("pre", False), "post": completed.get("post", False)}

@router.get("/{user_id}")
def get_user_surveys(user_id: str):
    response = table("sp2_surveys").select("*").eq("user_id", user_id).execute()
    return rows(response)
