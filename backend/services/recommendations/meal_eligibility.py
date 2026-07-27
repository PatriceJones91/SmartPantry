"""Meal eligibility rules for complete and realistic near-complete recipes."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List

class Eligibility(str, Enum):
    COMPLETE = "complete"
    NEAR_COMPLETE = "near_complete"
    INELIGIBLE = "ineligible"

@dataclass(frozen=True)
class EligibilityDecision:
    status: Eligibility
    main_ingredient_coverage: float
    missing_main_ingredients: List[str]
    missing_main_ingredient_count: int
    tier: int
    reason: str
    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self); payload["status"] = self.status.value; return payload

def classify_meal_eligibility(*, total_main_ingredients:int, matched_main_ingredients:int, missing_main_ingredients:List[str]) -> EligibilityDecision:
    total=max(int(total_main_ingredients),0); matched=min(max(int(matched_main_ingredients),0),total)
    missing=[str(x).strip() for x in missing_main_ingredients if str(x).strip()]
    coverage=round((matched/total)*100,2) if total else 0.0
    if total==0:
        return EligibilityDecision(Eligibility.INELIGIBLE,coverage,missing,len(missing),99,"Recipe has no defined main ingredients in the dataset.")
    if matched==total and not missing:
        return EligibilityDecision(Eligibility.COMPLETE,coverage,[],0,0,"All main ingredients are available in the pantry.")
    if len(missing)==1 and coverage>=60.0:
        return EligibilityDecision(Eligibility.NEAR_COMPLETE,coverage,missing,1,1,"Near-complete meal: one main ingredient is needed.")
    if len(missing)==2 and coverage>=60.0 and matched>=2:
        return EligibilityDecision(Eligibility.NEAR_COMPLETE,coverage,missing,2,2,"Near-complete meal: two main ingredients are needed.")
    return EligibilityDecision(Eligibility.INELIGIBLE,coverage,missing,len(missing),99,"The recipe is missing too many main ingredients to be realistically makeable.")
