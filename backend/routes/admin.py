from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.supabase_service import get_supabase, table, rows

router = APIRouter()

STUDY_STATUS_LABELS = {
    "in_progress": "Study In Progress",
    "processing": "Results Being Processed",
    "completed": "Study Completed",
}


class StudyStatusUpdate(BaseModel):
    status: str


def _read_study_status():
    try:
        result = (
            table("sp2_study_settings")
            .select("status, updated_at")
            .eq("setting_key", "study_status")
            .limit(1)
            .execute()
        )
        saved_rows = rows(result)
    except Exception:
        return {
            "status": "in_progress",
            "label": STUDY_STATUS_LABELS["in_progress"],
            "updatedAt": None,
            "storageReady": False,
        }

    saved = saved_rows[0] if saved_rows else {}
    status = saved.get("status") or "in_progress"

    if status not in STUDY_STATUS_LABELS:
        status = "in_progress"

    return {
        "status": status,
        "label": STUDY_STATUS_LABELS[status],
        "updatedAt": saved.get("updated_at"),
        "storageReady": True,
    }


@router.get("/study-status")
def study_status():
    return _read_study_status()


@router.put("/study-status")
def update_study_status(payload: StudyStatusUpdate):
    status = str(payload.status or "").strip().lower()

    if status not in STUDY_STATUS_LABELS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Choose Study In Progress, Results Being Processed, "
                "or Study Completed."
            ),
        )

    updated_at = datetime.now(timezone.utc).isoformat()

    try:
        table("sp2_study_settings").upsert(
            {
                "setting_key": "study_status",
                "status": status,
                "updated_at": updated_at,
            },
            on_conflict="setting_key",
        ).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not save the study status. Run the study-status "
                "database migration in Supabase, then try again."
            ),
        ) from exc

    return {
        "status": status,
        "label": STUDY_STATUS_LABELS[status],
        "updatedAt": updated_at,
        "storageReady": True,
    }


@router.get("/summary")
def summary():
    users = rows(
        table("sp2_users")
        .select("*")
        .execute()
    )

    pantry = rows(
        table("sp2_pantry_items")
        .select("*")
        .execute()
    )

    surveys = rows(
        table("sp2_surveys")
        .select("*")
        .execute()
    )

    actions = rows(
        table("sp2_recommendation_actions")
        .select("*")
        .execute()
    )

    sessions = rows(
        table("sp2_recommendation_sessions")
        .select("id")
        .execute()
    )

    made = [
        log
        for log in actions
        if log.get("action") == "made"
    ]

    saved = [
        log
        for log in actions
        if log.get("action") == "saved"
    ]

    return {
        "participants": len(
            [
                user
                for user in users
                if user.get("role") == "participant"
            ]
        ),
        "pantry_items": len(pantry),
        "survey_responses": len(surveys),
        "recommendation_sessions": len(sessions),
        "recommendation_actions": len(actions),
        "meals_made": len(made),
        "meals_saved": len(saved),
    }


@router.get("/users")
def users():
    return rows(
        table("sp2_users")
        .select("id, username, role, household_size")
        .order("username")
        .order("id")
        .execute()
    )


def _participant_key(value):
    return str(value or "").strip().lower()


def _normalized_action(value):
    if value == "used_elsewhere":
        return "custom_meal"

    return value


@router.get("/committee-evidence")
def committee_evidence():
    """
    Return participant-level research evidence without exposing participant
    usernames or account identifiers in the response.
    """

    participant_users = [
        user
        for user in rows(
            table("sp2_users")
            .select("id, username, role, household_size")
            .order("username")
            .order("id")
            .execute()
        )
        if user.get("role") == "participant"
    ]

    pantry_items = rows(
        table("sp2_pantry_items")
        .select("user_id, status")
        .execute()
    )

    recommendation_logs = rows(
        table("sp2_recommendation_actions")
        .select("user_id, action")
        .execute()
    )

    task1_rows = rows(
        get_supabase()
        .rpc("activity1_admin_rows", {})
        .execute()
    )

    evidence = []

    for index, user in enumerate(participant_users, start=1):
        user_id = user.get("id")
        username_key = _participant_key(user.get("username"))

        user_pantry = [
            item
            for item in pantry_items
            if item.get("user_id") == user_id
            and item.get("status") != "deleted"
        ]

        user_logs = [
            log
            for log in recommendation_logs
            if log.get("user_id") == user_id
            and log.get("action") != "general_feedback"
        ]

        user_task1_rows = [
            row
            for row in task1_rows
            if username_key
            in {
                _participant_key(row.get("username")),
                _participant_key(row.get("participant_id")),
            }
        ]

        actions = [
            _normalized_action(log.get("action"))
            for log in user_logs
        ]

        made = actions.count("made")
        custom = actions.count("custom_meal")

        evidence.append(
            {
                "participantNumber": index,
                "participant": f"Participant {index}",
                "household": user.get("household_size") or "N/A",
                "task1Items": len(user_task1_rows),
                "task3Items": len(user_pantry),
                "recommendationActions": len(user_logs),
                "made": made,
                "custom": custom,
                "utilization": made + custom,
                "saved": actions.count("saved"),
                "notUsed": actions.count("not_used"),
            }
        )

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "participants": evidence,
        "privacy": (
            "Participant usernames and account identifiers are not included."
        ),
        "studyStatus": _read_study_status(),
    }


@router.get("/surveys")
def surveys():
    return rows(
        table("sp2_surveys")
        .select("*")
        .execute()
    )


@router.get("/pantry")
def pantry():
    return rows(
        table("sp2_pantry_items")
        .select("*")
        .order("expiration_date")
        .execute()
    )


@router.get("/recommendation-logs")
def recommendation_logs():
    return rows(
        table("sp2_recommendation_actions")
        .select("*")
        .execute()
    )


@router.get("/recommendation-sessions")
def recommendation_sessions():
    return rows(
        table("sp2_recommendation_sessions")
        .select("*")
        .order("generated_at", desc=True)
        .execute()
    )