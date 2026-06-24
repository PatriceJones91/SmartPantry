from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.supabase_service import table
import re

router = APIRouter()


class RegisterPayload(BaseModel):
    username: str
    password: str
    role: str | None = "participant"


class LoginPayload(BaseModel):
    username: str
    password: str


def validate_username(username: str) -> str:
    username = (username or "").strip()

    if len(username) < 3 or len(username) > 32:
        raise HTTPException(status_code=400, detail="Username must be 3 to 32 characters.")

    if not re.match(r"^[A-Za-z0-9_-]+$", username):
        raise HTTPException(
            status_code=400,
            detail="Username can only use letters, numbers, underscores, or dashes.",
        )

    return username


def validate_password(password: str) -> str:
    password = password or ""

    if len(password) < 6 or len(password) > 64:
        raise HTTPException(status_code=400, detail="Password must be 6 to 64 characters.")

    return password


def clean_user(user: dict) -> dict:
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "role": user.get("role") or "participant",
    }


def find_user(username: str):
    try:
        result = table("sp2_users").select("*").eq("username", username).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read user table: {str(exc)}")


def create_user(username: str, password: str, role: str):
    insert_attempts = [
        {"username": username, "password": password, "role": role},
        {"username": username, "role": role},
        {"username": username},
    ]

    last_error = None

    for new_user in insert_attempts:
        try:
            created = table("sp2_users").insert(new_user).execute()
            if created.data:
                return created.data[0]
        except Exception as exc:
            last_error = str(exc)

    raise HTTPException(status_code=500, detail=f"Could not create user: {last_error}")


@router.post("/register")
def register(payload: RegisterPayload):
    username = validate_username(payload.username)
    password = validate_password(payload.password)
    role = payload.role or "participant"

    existing = find_user(username)

    if existing:
        existing_password = existing.get("password")
        if existing_password and existing_password != password:
            raise HTTPException(status_code=401, detail="Username already exists with a different password.")
        return clean_user(existing)

    created_user = create_user(username, password, role)
    return clean_user(created_user)


@router.post("/login")
def login(payload: LoginPayload):
    username = validate_username(payload.username)
    password = validate_password(payload.password)

    user = find_user(username)

    if not user:
        raise HTTPException(status_code=401, detail="User not found. Please create an account first.")

    stored_password = user.get("password")

    if stored_password and stored_password != password:
        raise HTTPException(status_code=401, detail="Incorrect password.")

    return clean_user(user)
