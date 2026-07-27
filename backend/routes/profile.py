from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.supabase_service import get_supabase

router = APIRouter()


class ProfileUpdate(BaseModel):
    household_size: Optional[int] = 1
    allergies: Optional[str] = ""
    dietary_restrictions: Optional[str] = ""
    preferred_meal_type: Optional[str] = ""
    preferred_cuisine: Optional[str] = ""
    avoid_foods: Optional[str] = ""
    quick_meals_preferred: Optional[bool] = True
    profile_notes: Optional[str] = ""


@router.get("/{user_id}")
def get_profile(user_id: str):
    supabase = get_supabase()

    response = (
        supabase.table("sp2_users")
        .select(
            "id, username, role, household_size, allergies, dietary_restrictions, "
            "preferred_meal_type, preferred_cuisine, avoid_foods, "
            "quick_meals_preferred, profile_notes"
        )
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return response.data


@router.put("/{user_id}")
def update_profile(user_id: str, payload: ProfileUpdate):
    supabase = get_supabase()

    update_data = {
        "household_size": payload.household_size,
        "allergies": payload.allergies or "",
        "dietary_restrictions": payload.dietary_restrictions or "",
        "preferred_meal_type": payload.preferred_meal_type or "",
        "preferred_cuisine": payload.preferred_cuisine or "",
        "avoid_foods": payload.avoid_foods or "",
        "quick_meals_preferred": payload.quick_meals_preferred,
        "profile_notes": payload.profile_notes or "",
    }

    response = (
        supabase.table("sp2_users")
        .update(update_data)
        .eq("id", user_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Profile could not be updated.")

    return response.data[0]
