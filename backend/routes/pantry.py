from fastapi import APIRouter, HTTPException
from models.schemas import PantryItemCreate, PantryItemUpdate
from services.supabase_service import table, rows, row

router = APIRouter()

@router.get("/{user_id}")
def get_pantry(user_id: str):
    response = table("sp2_pantry_items").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return rows(response)

@router.post("")
def add_pantry_item(payload: PantryItemCreate):
    response = table("sp2_pantry_items").insert(payload.model_dump()).execute()
    return row(response)

@router.put("/{item_id}")
def update_pantry_item(item_id: str, payload: PantryItemUpdate):
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided.")
    response = table("sp2_pantry_items").update(update_data).eq("id", item_id).execute()
    return row(response)

@router.delete("/{item_id}")
def delete_pantry_item(item_id: str):
    table("sp2_pantry_items").delete().eq("id", item_id).execute()
    return {"deleted": True, "id": item_id}
