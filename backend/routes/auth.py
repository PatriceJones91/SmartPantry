import hashlib
from fastapi import APIRouter, HTTPException
from models.schemas import RegisterRequest, LoginRequest
from services.supabase_service import table, row

router = APIRouter()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@router.post("/register")
def register(payload: RegisterRequest):
    existing = table("sp2_users").select("*").eq("username", payload.username).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Username already exists.")
    role = payload.role if payload.role in ["participant", "admin"] else "participant"
    created = table("sp2_users").insert({
        "username": payload.username,
        "password_hash": hash_password(payload.password),
        "role": role,
    }).execute()
    user = row(created)
    return {"id": user["id"], "username": user["username"], "role": user["role"]}

@router.post("/login")
def login(payload: LoginRequest):
    found = table("sp2_users").select("*").eq("username", payload.username).execute()
    user = row(found)
    if not user or user["password_hash"] != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"id": user["id"], "username": user["username"], "role": user["role"]}
