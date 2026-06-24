from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.supabase_service import table

router = APIRouter()


class RegisterPayload(BaseModel):
    username: str
    password: str | None = None
    role: str = "participant"


class LoginPayload(BaseModel):
    username: str
    password: str | None = None


def clean_user(user: dict) -> dict:
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "role": user.get("role", "participant"),
    }


@router.post("/register")
def register(payload: RegisterPayload):
    username = payload.username.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username is required.")

    existing = table("sp2_users").select("*").eq("username", username).execute()

    if existing.data:
        return clean_user(existing.data[0])

    new_user = {
        "username": username,
        "role": payload.role or "participant",
    }

    created = table("sp2_users").insert(new_user).execute()

    if not created.data:
        raise HTTPException(status_code=500, detail="Could not create user.")

    return clean_user(created.data[0])


@router.post("/login")
def login(payload: LoginPayload):
    username = payload.username.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username is required.")

    result = table("sp2_users").select("*").eq("username", username).execute()

    if not result.data:
        raise HTTPException(status_code=401, detail="User not found. Please create an account first.")

    user = result.data[0]
    return clean_user(user)
