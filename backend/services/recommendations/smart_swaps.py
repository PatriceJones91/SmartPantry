"""Context-safe Smart Swaps using food family + culinary role + recipe context."""
from __future__ import annotations
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Mapping, Sequence
from .ingredient_normalizer import ingredients_equivalent, normalize_ingredient


def _clean(value: Any) -> str:
    return normalize_ingredient(str(value or "")).canonical

@lru_cache(maxsize=8192)
def ingredient_profile(value: str) -> tuple[str | None, str | None]:
    raw = " ".join(str(value or "").lower().replace("-", " ").split())
    name = _clean(value)
    text = f"{raw} {name}"
    if any(t in text for t in ("stock", "broth", "bouillon", "extract", "sauce", "paste")):
        return None, None
    # Cereals and crunchy coatings MUST be resolved before generic rice/grain.
    if any(t in text for t in ("rice crisp", "rice krisp", "corn flake", "cornflake", "breakfast cereal")):
        return "cereal", "crunchy_coating_or_cereal"
    if any(t in text for t in ("panko", "breadcrumb", "bread crumb", "cracker crumb", "crushed cracker")):
        return "dry_coating", "crunchy_coating"
    # Green beans are vegetables, not a generic bean-based protein.
    if any(t in text for t in ("green bean", "string bean", "snap bean")):
        return "green_vegetable", "produce"
    if "flour" in text or "cornstarch" in text:
        return "starch", "thickener_or_dredge"
    rules = [
        # Culinary fats must be classified before a meat word such as "beef".
        ("fat", "cooking_fat", ("beef fat", "duck fat", "lard", "shortening", "butter", "margarine", "olive oil", "vegetable oil", "canola oil")),
        ("poultry", "lean_main_protein", ("chicken", "turkey")),
        ("red_meat", "main_protein", ("beef", "steak", "lamb", "pork", "bacon")),
        ("seafood", "main_protein", ("salmon", "tuna", "shrimp", "fish", "crab")),
        ("plant_protein", "main_protein", ("tofu", "tempeh", "lentil", "chickpea", "bean")),
        ("egg", "binder_or_protein", ("egg",)),
        ("dairy", "creamy_liquid", ("milk", "cream", "yogurt")),
        ("cheese", "melting_or_finishing_cheese", ("cheese", "cheddar", "mozzarella", "parmesan", "gouda")),
        ("pasta", "cooked_starch", ("pasta", "spaghetti", "macaroni", "noodle")),
        ("rice_grain", "cooked_starch", ("brown rice", "white rice", "rice", "quinoa")),
        ("bread", "bread_base", ("bread", "bun", "roll", "bagel", "toast")),
        ("wrap", "wrap_base", ("tortilla", "wrap", "flatbread")),
        ("potato", "starchy_vegetable", ("potato",)),
        ("tomato", "produce", ("tomato",)),
        ("pepper", "produce", ("bell pepper", "red pepper", "green pepper", "yellow pepper")),
        ("leafy_green", "produce", ("spinach", "kale", "lettuce", "collard")),
        ("sweetener", "sweetener", ("sugar", "honey", "maple syrup")),
    ]
    for family, role, terms in rules:
        if any(term in text for term in terms):
            return family, role
    return None, None


def _compatible(needed: tuple[str|None,str|None], pantry: tuple[str|None,str|None]) -> tuple[bool,str]:
    nf, nr = needed; pf, pr = pantry
    if not nf or not nr or not pf or not pr:
        return False, "none"
    if nf == pf and nr == pr:
        return True, "strong"
    # Explicit cross-family culinary-role substitutions.
    if nr == "crunchy_coating_or_cereal" and pr == "crunchy_coating":
        return True, "reasonable"
    if nr == "crunchy_coating" and pr == "crunchy_coating_or_cereal":
        return True, "reasonable"
    if nr == "cooking_fat" and pr == "cooking_fat":
        return True, "reasonable"
    # Main proteins are not interchangeable merely because both contain protein.
    # Keep swaps inside the same culinary family; otherwise prefer no swap.
    if nr == "main_protein" and pr == "main_protein" and nf == pf:
        return True, "strong"
    return False, "none"


def _context_allows_swap(needed: str, replacement: str, recipe_context: Mapping[str, Any] | None) -> bool:
    n = _clean(needed)
    r = _clean(replacement)
    title = str((recipe_context or {}).get("recipe_name") or "").lower()
    # Pasta shape matters in structure-dependent dishes such as macaroni and cheese.
    pasta_shapes = {"macaroni", "elbow macaroni", "angel hair pasta", "spaghetti", "penne", "linguine", "fettuccine"}
    if n in pasta_shapes and r in pasta_shapes and n != r:
        return False
    # Whole eggs are not a transparent one-for-one substitute for separated components.
    if {n, r} & {"egg white", "egg yolk"} and n != r:
        return False
    # Cereal/coating swaps are only suitable when the recipe reads like a coating or cereal use.
    nf, nr = ingredient_profile(needed)
    if nr == "crunchy_coating_or_cereal":
        context = " ".join([title, *(recipe_context or {}).get("dish_types", [])]).lower()
        if not any(term in context for term in ("fried", "crusted", "coated", "cereal", "bar", "treat")):
            return False
    return True


def find_smart_swaps(missing: Sequence[str], pantry_items: Iterable[Mapping[str, Any]], limit: int = 3, recipe_context: Mapping[str, Any] | None = None) -> List[Dict[str, Any]]:
    pantry_names = [str(i.get("item_name") or i.get("name") or i.get("ingredient") or "").strip() for i in pantry_items]
    swaps: List[Dict[str, Any]] = []
    used: set[str] = set()
    for needed in missing:
        needed_profile = ingredient_profile(needed)
        needed_clean = _clean(needed)
        for pantry_name in pantry_names:
            pantry_clean = _clean(pantry_name)
            # A Smart Swap must be a genuinely different ingredient. Generic and
            # specific names such as "flour" and "all-purpose flour" are matches,
            # not substitutions.
            if (
                not pantry_clean
                or pantry_clean == needed_clean
                or ingredients_equivalent(needed, pantry_name)
                or pantry_clean in used
            ):
                continue
            ok, confidence = _compatible(needed_profile, ingredient_profile(pantry_name))
            if not ok or not _context_allows_swap(needed, pantry_name, recipe_context):
                continue
            family, role = needed_profile
            reason = f"Compatible {role.replace('_', ' ')} for this recipe; texture or seasoning may need a small adjustment."
            swaps.append({"needed": needed, "use_instead": pantry_clean or pantry_name, "pantry_item_name": pantry_name, "food_family": family, "culinary_role": role, "role": family, "confidence": confidence, "reason": reason})
            used.add(pantry_clean)
            break
        if len(swaps) >= max(0, int(limit)):
            break
    return swaps
