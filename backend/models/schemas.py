from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)
    role: str = "participant"


class LoginRequest(BaseModel):
    username: str
    password: str


class PantryItemCreate(BaseModel):
    user_id: str
    item_name: str
    category: str = "Other"
    quantity: float = 1
    unit: str = "item"
    container_type: Optional[str] = ""
    expiration_date: Optional[str] = None
    barcode: str = ""
    brand: str = ""
    source: str = ""
    notes: str = ""


class PantryItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    container_type: Optional[str] = None
    expiration_date: Optional[str] = None
    status: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    used_amount: Optional[float] = None
    last_action: Optional[str] = None


class SurveySubmit(BaseModel):
    user_id: str
    survey_type: str
    responses: Dict[str, Any]
    comments: Optional[str] = ""


class RecommendationGenerateRequest(BaseModel):
    user_id: str


class RecommendationActionRequest(BaseModel):
    user_id: str
    recipe_name: str
    action: str
    score: Optional[float] = None
    feedback: Optional[str] = ""
    used_ingredients: Optional[List[str]] = []
