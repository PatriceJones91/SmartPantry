from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.supabase_service import table
import hashlib
import re

router = APIRouter()


class RegisterPayload(BaseModel):
    username: str
    password: str
    role: str | None = "participant"


class LoginPayload(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


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


@router.post("/register")
def register(payload: RegisterPayload):
    username = validate_username(payload.username)
    password = validate_password(payload.password)
    role = payload.role or "participant"

    existing = find_user(username)

    if existing:
        stored_hash = existing.get("password_hash")
        entered_hash = hash_password(password)

        if stored_hash and stored_hash not in [entered_hash, password]:
            raise HTTPException(status_code=401, detail="Username already exists with a different password.")

        return clean_user(existing)

    new_user = {
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
    }

    try:
        created = table("sp2_users").insert(new_user).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not create user: {str(exc)}")

    if not created.data:
        raise HTTPException(status_code=500, detail="Could not create user.")

    return clean_user(created.data[0])


@router.post("/login")
def login(payload: LoginPayload):
    username = validate_username(payload.username)
    password = validate_password(payload.password)

    user = find_user(username)

    if not user:
        raise HTTPException(status_code=401, detail="User not found. Please create an account first.")

    stored_hash = user.get("password_hash")
    entered_hash = hash_password(password)

    if stored_hash and stored_hash not in [entered_hash, password]:
        raise HTTPException(status_code=401, detail="Incorrect password.")

    return clean_user(user)

# --- ADMIN ACCOUNT TOOLS ---

class AdminPasswordResetPayload(BaseModel):
    admin_username: str
    admin_password: str
    target_username: str
    new_password: str


class AdminDeleteUserPayload(BaseModel):
    admin_username: str
    admin_password: str
    target_username: str
    confirm_text: str


def require_admin_user(admin_username: str, admin_password: str):
    admin_username = validate_username(admin_username)
    admin_password = validate_password(admin_password)

    admin = find_user(admin_username)

    if not admin or admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    stored_hash = admin.get("password_hash")
    entered_hash = hash_password(admin_password)

    if stored_hash and stored_hash not in [entered_hash, admin_password]:
        raise HTTPException(status_code=403, detail="Admin password is incorrect.")

    return admin


@router.post("/admin/reset-password")
def admin_reset_password(payload: AdminPasswordResetPayload):
    require_admin_user(payload.admin_username, payload.admin_password)

    target_username = validate_username(payload.target_username)
    new_password = validate_password(payload.new_password)

    target_user = find_user(target_username)

    if not target_user:
        raise HTTPException(status_code=404, detail="Participant username was not found.")

    if target_user.get("role") == "admin":
        raise HTTPException(status_code=400, detail="Admin accounts cannot be reset here.")

    try:
        table("sp2_users").update({
            "password_hash": hash_password(new_password)
        }).eq("id", target_user["id"]).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not reset password: {str(exc)}")

    return {
        "status": "ok",
        "message": f"Password reset for {target_username}.",
        "target_user": clean_user(target_user),
    }


@router.post("/admin/delete-test-user")
def admin_delete_test_user(payload: AdminDeleteUserPayload):
    require_admin_user(payload.admin_username, payload.admin_password)

    target_username = validate_username(payload.target_username)
    target_user = find_user(target_username)

    if not target_user:
        raise HTTPException(status_code=404, detail="Participant username was not found.")

    if target_user.get("role") == "admin":
        raise HTTPException(status_code=400, detail="Admin accounts cannot be deleted here.")

    required_confirmation = f"DELETE {target_username}"

    if payload.confirm_text != required_confirmation:
        raise HTTPException(
            status_code=400,
            detail=f'Type exactly: {required_confirmation}',
        )

    user_id = target_user.get("id")

    cleanup_steps = [
        ("sp2_history", "user_id", user_id),
        ("sp2_recommendations", "user_id", user_id),
        ("sp2_pantry_items", "user_id", user_id),
        ("sp2_surveys", "user_id", user_id),
    ]

    cleanup_results = []

    for table_name, column, value in cleanup_steps:
        try:
            table(table_name).delete().eq(column, value).execute()
            cleanup_results.append({"table": table_name, "status": "deleted"})
        except Exception as exc:
            cleanup_results.append({"table": table_name, "status": f"skipped: {str(exc)}"})

    try:
        table("sp2_users").delete().eq("id", user_id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not delete user account: {str(exc)}")

    return {
        "status": "ok",
        "message": f"Deleted tester account {target_username}.",
        "deleted_user": target_username,
        "cleanup": cleanup_results,
    }

