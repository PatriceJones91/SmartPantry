from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.supabase_service import table

router = APIRouter()


class RegisterPayload(BaseModel):
    username: str
    password: str | None = None
    role: str | None = "participant"


class LoginPayload(BaseModel):
    username: str
    password: str | None = None


def clean_user(user: dict) -> dict:
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "role": user.get("role") or "participant",
    }


@router.post("/register")
def register(payload: RegisterPayload):
    username = (payload.username or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username is required.")

    role = payload.role or "participant"

    existing = table("sp2_users").select("*").eq("username", username).execute()

    if existing.data:
        return clean_user(existing.data[0])

    created = table("sp2_users").insert({
        "username": username,
        "role": role,
    }).execute()

    if not created.data:
        raise HTTPException(status_code=500, detail="Could not create user.")

    return clean_user(created.data[0])


@router.post("/login")
def login(payload: LoginPayload):
    username = (payload.username or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username is required.")

    result = table("sp2_users").select("*").eq("username", username).execute()

    if not result.data:
        raise HTTPException(status_code=401, detail="User not found. Please create an account first.")

    return clean_user(result.data[0])
