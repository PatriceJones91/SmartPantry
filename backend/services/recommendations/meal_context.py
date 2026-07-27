"""Meal/cuisine context classification and active filter helpers for Phase 15."""
from __future__ import annotations
from typing import Any, Iterable, Mapping, Sequence

MEAL_FILTERS = ["breakfast", "lunch", "dinner", "snack", "quick meal", "brunch"]
CUISINE_FILTERS = ["american", "mexican", "italian", "asian", "mediterranean", "everyday", "southern", "comfort food", "seafood"]


def _text(candidate: Mapping[str, Any]) -> str:
    values = [candidate.get("recipe_name", ""), *(candidate.get("meal_types") or []), *(candidate.get("dish_types") or [])]
    return " ".join(str(v).lower().replace("-", " ") for v in values)


def classify_meal_types(candidate: Mapping[str, Any]) -> list[str]:
    text = _text(candidate)
    labels = {str(v).lower().strip() for v in candidate.get("meal_types") or [] if str(v).strip()}
    found: list[str] = []
    rules = {
        "breakfast": ("breakfast", "oatmeal", "pancake", "waffle", "cereal", "morning"),
        "brunch": ("brunch", "frittata", "quiche", "benedict", "crepe"),
        "snack": ("snack", "appetizer", "dip", "bite", "popcorn", "trail mix"),
        "lunch": ("lunch", "sandwich", "wrap", "salad", "soup"),
        "dinner": ("dinner", "main course", "main dish", "entree", "casserole", "stew", "pasta", "roast", "skillet"),
    }
    dessert_terms = ("dessert", "cake", "cupcake", "cookie", "candy", "pudding", "frosting", "brownie", "pie", "sweet")
    is_dessert = any(term in text for term in dessert_terms)
    for label in MEAL_FILTERS:
        if label in labels or any(term in text for term in rules.get(label, ())):
            found.append(label)
    everyday = candidate.get("everyday_fit_score")
    try:
        quick = float(everyday) >= 70
    except (TypeError, ValueError):
        quick = False
    if quick or any(term in text for term in ("quick", "easy", "15 minute", "20 minute", "30 minute")):
        found.append("quick meal")
    if not found and not is_dessert:
        found.extend(["lunch", "dinner"])
    # Dessert remains discoverable in All, but it is not mislabeled as lunch/dinner.
    if is_dessert:
        found = [x for x in found if x in {"snack", "quick meal", "brunch"}]
        found.append("dessert")
    return list(dict.fromkeys(found))


def normalize_cuisines(candidate: Mapping[str, Any]) -> list[str]:
    raw = [str(v).lower().strip() for v in candidate.get("cuisine_types") or [] if str(v).strip()]
    text = " ".join(raw + [str(candidate.get("recipe_name") or "").lower()])
    out = list(raw)
    mapping = {
        "asian": ("asian", "chinese", "japanese", "thai", "korean", "vietnamese", "indian"),
        "mediterranean": ("mediterranean", "greek", "levant", "middle eastern"),
        "mexican": ("mexican", "tex mex", "taco", "enchilada"),
        "italian": ("italian", "pasta", "risotto", "parmesan"),
        "american": ("american",),
        "southern": ("southern", "cajun", "creole"),
        "comfort food": ("comfort", "casserole", "mac and cheese"),
        "seafood": ("seafood", "shrimp", "salmon", "tuna", "fish", "crab"),
    }
    for label, terms in mapping.items():
        if any(term in text for term in terms):
            out.append(label)
    if not out:
        out.append("everyday")
    return list(dict.fromkeys(out))


def matches_active_filters(candidate: Mapping[str, Any], meal_types: Sequence[str] | None, cuisine_types: Sequence[str] | None) -> bool:
    requested_meals = {str(v).lower().strip() for v in meal_types or [] if str(v).strip() and str(v).lower().strip() != "all"}
    requested_cuisines = {str(v).lower().strip() for v in cuisine_types or [] if str(v).strip() and str(v).lower().strip() != "all"}
    candidate_meals = set(classify_meal_types(candidate))
    candidate_cuisines = set(normalize_cuisines(candidate))
    return (not requested_meals or bool(requested_meals & candidate_meals)) and (not requested_cuisines or bool(requested_cuisines & candidate_cuisines))
