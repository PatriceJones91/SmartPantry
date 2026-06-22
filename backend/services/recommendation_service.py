import ast
import csv
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

RECIPE_SOURCES = [
    {
        "path": DATA_DIR / "sample_recipes.csv",
        "source_type": "core",
        "source_label": "Core everyday meals",
        "source_boost": 15,
        "limit": None,
    },
    {
        "path": DATA_DIR / "smart_pantry_recipes_clean.csv",
        "source_type": "expanded",
        "source_label": "Expanded recipe library",
        "source_boost": 0,
        "limit": 1200,
    },
]

STOP_WORDS = {
    "fresh", "frozen", "canned", "can", "package", "pkg", "cup", "cups", "tbsp",
    "tsp", "tablespoon", "tablespoons", "teaspoon", "teaspoons", "chopped", "diced",
    "sliced", "shredded", "grated", "large", "small", "medium", "thin", "thick",
    "optional", "cooked", "uncooked", "boneless", "skinless", "ground", "whole",
    "pieces", "piece", "oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds",
}

LOW_VALUE_MISSING = {
    "salt", "pepper", "water", "ice", "cooking spray", "spray", "seasoning",
    "garlic powder", "onion powder", "paprika", "parsley", "basil", "oregano",
}


METADATA_INGREDIENT_WORDS = {
    "food",
    "text",
    "weight",
    "measure",
    "quantity",
    "unit",
    "units",
    "ingredient",
    "ingredients",
    "name",
    "value",
    "amount",
    "none",
    "nan",
}


def normalize_key(value: str) -> str:
    return (value or "").strip().lower().replace(" ", "_").replace("-", "_")


def get_first(row: Dict[str, Any], possible_names: List[str], default: str = "") -> str:
    normalized = {normalize_key(k): v for k, v in row.items()}

    for name in possible_names:
        key = normalize_key(name)
        if key in normalized and normalized[key] not in [None, ""]:
            return str(normalized[key]).strip()

    return default


def clean_ingredient(value: str) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\b\d+[\/\d\.]*\b", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    words = [
        word.strip()
        for word in text.split()
        if word.strip() and word.strip() not in STOP_WORDS
    ]

    cleaned = " ".join(words).strip()

    if cleaned.endswith("s") and len(cleaned) > 3 and not cleaned.endswith("ss"):
        cleaned = cleaned[:-1]

    return cleaned


def simplify(value: str) -> str:
    return clean_ingredient(value)


def ingredient_tokens(value: str) -> set:
    return {
        token
        for token in simplify(value).split()
        if len(token) > 2 and token not in STOP_WORDS
    }



def is_real_ingredient(value: str) -> bool:
    ingredient = clean_ingredient(value)

    if not ingredient:
        return False

    if ingredient in METADATA_INGREDIENT_WORDS:
        return False

    if len(ingredient) < 2:
        return False

    tokens = ingredient.split()

    if all(token in METADATA_INGREDIENT_WORDS for token in tokens):
        return False

    return True


def extract_ingredient_from_dict(item: Dict[str, Any]) -> str:
    # Prefer the actual food name, not the metadata keys.
    for key in ["food", "name", "ingredient", "ingredient_name", "item", "product"]:
        if key in item and item[key]:
            return str(item[key])

    # If food is missing, text is usually the human-readable ingredient line.
    if "text" in item and item["text"]:
        return str(item["text"])

    return ""

def parse_ingredients(value: Any) -> List[str]:
    if value is None:
        return []

    raw_items = []

    if isinstance(value, list):
        raw_items = value
    else:
        text_value = str(value).strip()

        if not text_value:
            return []

        # First try to read real JSON or Python-style list/dict strings.
        parsed = None

        if text_value.startswith("[") or text_value.startswith("{"):
            try:
                parsed = json.loads(text_value)
            except Exception:
                try:
                    parsed = ast.literal_eval(text_value)
                except Exception:
                    parsed = None

        if isinstance(parsed, list):
            raw_items = parsed
        elif isinstance(parsed, dict):
            if "ingredients" in parsed and isinstance(parsed["ingredients"], list):
                raw_items = parsed["ingredients"]
            else:
                raw_items = [parsed]
        else:
            # Pull food/name values out of dictionary-looking strings before splitting.
            extracted_values = re.findall(
                r"""['"](?:food|name|ingredient|ingredient_name|item|product)['"]\s*:\s*['"]([^'"]+)['"]""",
                text_value,
                flags=re.IGNORECASE,
            )

            if extracted_values:
                raw_items = extracted_values
            else:
                raw_items = re.split(r"[,;|\n]", text_value)

    cleaned = []
    seen = set()

    for raw_item in raw_items:
        if isinstance(raw_item, dict):
            ingredient_text = extract_ingredient_from_dict(raw_item)
        else:
            ingredient_text = str(raw_item)

        ingredient = clean_ingredient(ingredient_text)

        if not is_real_ingredient(ingredient):
            continue

        if ingredient not in seen:
            cleaned.append(ingredient)
            seen.add(ingredient)

    return cleaned


def parse_minutes(value: str) -> Optional[int]:
    if not value:
        return None

    text = str(value).strip().upper()

    if text.startswith("PT"):
        hours = re.search(r"(\d+)H", text)
        minutes = re.search(r"(\d+)M", text)
        total = 0

        if hours:
            total += int(hours.group(1)) * 60

        if minutes:
            total += int(minutes.group(1))

        return total or None

    numbers = re.findall(r"\d+", text)

    if numbers:
        return int(numbers[0])

    return None


def days_until(expiration_date):
    if not expiration_date:
        return None

    try:
        if isinstance(expiration_date, str):
            exp = datetime.strptime(expiration_date[:10], "%Y-%m-%d").date()
        else:
            exp = expiration_date

        return (exp - date.today()).days
    except Exception:
        return None


def infer_meal_type(name: str, category: str = "") -> str:
    text = f"{name} {category}".lower()

    if any(word in text for word in ["breakfast", "egg", "toast", "oat", "cereal", "pancake"]):
        return "Breakfast"

    if any(word in text for word in ["lunch", "wrap", "salad", "sandwich", "soup"]):
        return "Lunch"

    if any(word in text for word in ["dinner", "casserole", "pasta", "rice", "bowl", "chicken", "fish"]):
        return "Dinner"

    return "Meal"


def row_to_recipe(row: Dict[str, Any], source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    name = get_first(row, ["recipe_name", "name", "title", "recipe", "Name"])

    ingredients_value = get_first(
        row,
        [
            "ingredients",
            "ingredients_list",
            "recipe_ingredients",
            "cleaned_ingredients",
            "ingredients_clean",
            "RecipeIngredientParts",
            "NER",
        ],
    )

    ingredients = parse_ingredients(ingredients_value)

    if not name or len(ingredients) < 2 or len(ingredients) > 18:
        return None

    category = get_first(row, ["category", "recipe_category", "RecipeCategory", "dish_type"], "")
    meal_type = get_first(row, ["meal_type", "meal", "course", "MealType"], "") or infer_meal_type(name, category)

    return {
        "recipe_name": name,
        "ingredients_list": ingredients,
        "meal_type": meal_type,
        "cuisine_type": get_first(row, ["cuisine_type", "cuisine", "Cuisine", "region"], "Everyday"),
        "dish_type": get_first(row, ["dish_type", "RecipeCategory", "category"], category or "Meal"),
        "calories": get_first(row, ["calories", "Calories"], ""),
        "protein": get_first(row, ["protein", "ProteinContent", "protein_g"], ""),
        "carbs": get_first(row, ["carbs", "CarbohydrateContent", "carbohydrates", "carbs_g"], ""),
        "fat": get_first(row, ["fat", "FatContent", "fat_g"], ""),
        "cook_time": parse_minutes(get_first(row, ["cook_time", "CookTime", "total_time", "TotalTime", "minutes"])),
        "instructions": get_first(
            row,
            ["instructions", "Instructions", "recipe_instructions", "RecipeInstructions", "directions"],
            "",
        ),
        "source_type": source["source_type"],
        "source_label": source["source_label"],
        "source_boost": source["source_boost"],
    }


def load_recipes() -> List[Dict[str, Any]]:
    recipes = []
    seen_names = set()

    for source in RECIPE_SOURCES:
        path = source["path"]

        if not path.exists():
            continue

        loaded_from_source = 0

        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                recipe = row_to_recipe(row, source)

                if not recipe:
                    continue

                name_key = simplify(recipe["recipe_name"])

                if name_key in seen_names:
                    continue

                recipes.append(recipe)
                seen_names.add(name_key)
                loaded_from_source += 1

                if source["limit"] and loaded_from_source >= source["limit"]:
                    break

    return recipes


def pantry_item_matches_ingredient(pantry_name: str, ingredient: str) -> bool:
    pantry_clean = simplify(pantry_name)
    ingredient_clean = simplify(ingredient)

    if not pantry_clean or not ingredient_clean:
        return False

    if pantry_clean in ingredient_clean or ingredient_clean in pantry_clean:
        return True

    pantry_tokens = ingredient_tokens(pantry_clean)
    ingredient_tokens_set = ingredient_tokens(ingredient_clean)

    return bool(
        pantry_tokens
        and ingredient_tokens_set
        and pantry_tokens.intersection(ingredient_tokens_set)
    )



def split_profile_list(value: Any) -> List[str]:
    if not value:
        return []

    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = re.split(r"[,;|\n]", str(value))

    cleaned = []

    for item in raw_items:
        text = clean_ingredient(item)
        text = text.replace("no ", "").replace("avoid ", "").strip()

        if text and text not in cleaned:
            cleaned.append(text)

    return cleaned


def profile_terms_to_avoid(profile: Optional[Dict[str, Any]]) -> List[str]:
    if not profile:
        return []

    terms = []

    for field in ["allergies", "avoid_foods", "dietary_restrictions"]:
        terms.extend(split_profile_list(profile.get(field, "")))

    # Special case: if the user types "no pork" in restrictions, make sure pork is blocked.
    restrictions = str(profile.get("dietary_restrictions", "")).lower()
    if "pork" in restrictions and "pork" not in terms:
        terms.append("pork")

    return [term for term in terms if term]


def recipe_contains_avoided_food(recipe: Dict[str, Any], profile: Optional[Dict[str, Any]]) -> bool:
    avoid_terms = profile_terms_to_avoid(profile)

    if not avoid_terms:
        return False

    recipe_text = " ".join(
        [
            str(recipe.get("recipe_name", "")),
            str(recipe.get("dish_type", "")),
            str(recipe.get("cuisine_type", "")),
            " ".join(recipe.get("ingredients_list", [])),
        ]
    ).lower()

    for term in avoid_terms:
        clean_term = clean_ingredient(term)

        if clean_term and clean_term in recipe_text:
            return True

    return False


def preference_boost(recipe: Dict[str, Any], profile: Optional[Dict[str, Any]]) -> float:
    if not profile:
        return 0

    boost = 0

    preferred_meal_types = split_profile_list(profile.get("preferred_meal_type", ""))
    preferred_cuisines = split_profile_list(profile.get("preferred_cuisine", ""))

    recipe_meal_type = clean_ingredient(recipe.get("meal_type", ""))
    recipe_cuisine = clean_ingredient(recipe.get("cuisine_type", ""))
    recipe_name = clean_ingredient(recipe.get("recipe_name", ""))
    recipe_dish = clean_ingredient(recipe.get("dish_type", ""))

    for meal_type in preferred_meal_types:
        meal = clean_ingredient(meal_type)

        if meal and (
            meal in recipe_meal_type
            or meal in recipe_name
            or meal in recipe_dish
        ):
            boost += 8
            break

    for cuisine in preferred_cuisines:
        cuisine_clean = clean_ingredient(cuisine)

        if cuisine_clean and (
            cuisine_clean in recipe_cuisine
            or cuisine_clean in recipe_name
            or cuisine_clean in recipe_dish
        ):
            boost += 6
            break

    quick_preferred = profile.get("quick_meals_preferred", True)
    cook_time = recipe.get("cook_time")
    ingredient_count = len(recipe.get("ingredients_list", []))

    if quick_preferred:
        if cook_time is not None and cook_time <= 20:
            boost += 8
        elif ingredient_count <= 5:
            boost += 6

    return min(boost, 18)



def score_recipe(recipe: Dict[str, Any], pantry_items: List[Dict[str, Any]], profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if recipe_contains_avoided_food(recipe, profile):
        return {
            "recipe_name": recipe.get("recipe_name"),
            "meal_type": recipe.get("meal_type"),
            "cuisine_type": recipe.get("cuisine_type"),
            "dish_type": recipe.get("dish_type"),
            "calories": recipe.get("calories"),
            "protein": recipe.get("protein"),
            "carbs": recipe.get("carbs"),
            "fat": recipe.get("fat"),
            "cook_time": recipe.get("cook_time"),
            "instructions": recipe.get("instructions"),
            "score": -1,
            "matched_ingredients": [],
            "missing_ingredients": [],
            "expiring_items": [],
            "source_type": recipe.get("source_type"),
            "source_label": recipe.get("source_label"),
            "why": "Filtered out because it conflicts with saved allergies or foods to avoid.",
            "filtered_out": True,
        }

    recipe_ingredients = recipe.get("ingredients_list", [])
    matched = []
    missing = []
    matched_pantry_items = []

    for ingredient in recipe_ingredients:
        matched_item = None

        for pantry_item in pantry_items:
            pantry_name = pantry_item.get("item_name", "")

            if pantry_item_matches_ingredient(pantry_name, ingredient):
                matched_item = pantry_item
                break

        if matched_item:
            matched.append(ingredient)
            matched_pantry_items.append(matched_item)
        else:
            missing.append(ingredient)

    total_ingredients = max(len(recipe_ingredients), 1)
    match_ratio = len(matched) / total_ingredients

    match_score = match_ratio * 48
    matched_count_bonus = min(len(matched) * 4, 12)

    expiring_bonus = 0
    expiring_items = []

    for item in matched_pantry_items:
        item_days = days_until(item.get("expiration_date"))

        if item_days is None:
            continue

        if item_days <= 0:
            expiring_bonus += 20
            expiring_items.append(item.get("item_name"))
        elif item_days <= 1:
            expiring_bonus += 18
            expiring_items.append(item.get("item_name"))
        elif item_days <= 4:
            expiring_bonus += 12
            expiring_items.append(item.get("item_name"))
        elif item_days <= 10:
            expiring_bonus += 7
            expiring_items.append(item.get("item_name"))

    expiring_bonus = min(expiring_bonus, 30)

    ingredient_count = len(recipe_ingredients)
    simplicity_bonus = 0

    if ingredient_count <= 4:
        simplicity_bonus += 12
    elif ingredient_count <= 6:
        simplicity_bonus += 8
    elif ingredient_count <= 8:
        simplicity_bonus += 4

    cook_time = recipe.get("cook_time")

    if cook_time is not None:
        if cook_time <= 15:
            simplicity_bonus += 8
        elif cook_time <= 30:
            simplicity_bonus += 4

    source_boost = recipe.get("source_boost", 0)
    profile_boost = preference_boost(recipe, profile)
    missing_penalty = len([item for item in missing if item not in LOW_VALUE_MISSING]) * 5
    no_match_penalty = 18 if len(matched) == 0 else 0

    score = (
        10
        + match_score
        + matched_count_bonus
        + expiring_bonus
        + simplicity_bonus
        + source_boost
        + profile_boost
        - missing_penalty
        - no_match_penalty
    )

    score = max(0, min(round(score, 1), 100))

    matched = [item for item in matched if is_real_ingredient(item)]
    missing = [item for item in missing if is_real_ingredient(item)]
    expiring_items = [item for item in expiring_items if item]

    return {
        "recipe_name": recipe.get("recipe_name"),
        "meal_type": recipe.get("meal_type"),
        "cuisine_type": recipe.get("cuisine_type"),
        "dish_type": recipe.get("dish_type"),
        "calories": recipe.get("calories"),
        "protein": recipe.get("protein"),
        "carbs": recipe.get("carbs"),
        "fat": recipe.get("fat"),
        "cook_time": recipe.get("cook_time"),
        "instructions": recipe.get("instructions"),
        "score": score,
        "matched_ingredients": matched,
        "missing_ingredients": missing,
        "expiring_items": list(dict.fromkeys([item for item in expiring_items if item])),
        "source_type": recipe.get("source_type"),
        "source_label": recipe.get("source_label"),
        "why": build_reason(matched, missing, expiring_items, recipe, profile),
    }


def build_reason(matched, missing, expiring_items, recipe, profile=None):
    parts = []

    if recipe.get("source_type") == "core":
        parts.append("This comes from the quick everyday recipe set.")
    else:
        parts.append("This comes from the larger expanded recipe library.")

    if matched:
        parts.append(f"Uses pantry items: {', '.join(matched[:5])}.")

    if expiring_items:
        unique_expiring = list(dict.fromkeys([item for item in expiring_items if item]))
        parts.append(f"Prioritizes items close to expiring: {', '.join(unique_expiring[:5])}.")

    if profile:
        preferred_meals = split_profile_list(profile.get("preferred_meal_type", ""))
        preferred_cuisines = split_profile_list(profile.get("preferred_cuisine", ""))

        if preferred_meals or preferred_cuisines:
            parts.append("Also checked against saved profile preferences.")

    if missing:
        parts.append(f"Missing ingredients: {', '.join(missing[:5])}.")

    return " ".join(parts)


def generate_recommendations(pantry_items: List[Dict[str, Any]], profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    active_pantry = [item for item in pantry_items if item.get("status") != "deleted"]

    scored = [score_recipe(recipe, active_pantry, profile) for recipe in load_recipes()]
    scored = [recipe for recipe in scored if recipe.get("recipe_name") and not recipe.get("filtered_out") and recipe.get("score", 0) >= 0]
    scored.sort(key=lambda item: item["score"], reverse=True)

    selected = []
    selected_names = set()

    for recipe in scored:
        if len(selected) >= 10:
            break

        selected.append(recipe)
        selected_names.add(simplify(recipe["recipe_name"]))

    expanded_added = 0

    for recipe in scored:
        if expanded_added >= 4 or len(selected) >= 14:
            break

        if recipe.get("source_type") != "expanded":
            continue

        name_key = simplify(recipe["recipe_name"])

        if name_key in selected_names:
            continue

        if recipe.get("score", 0) < 25:
            continue

        selected.append(recipe)
        selected_names.add(name_key)
        expanded_added += 1

    return selected


def grocery_suggestions(recommendations: List[Dict[str, Any]]) -> List[str]:
    counts = {}

    for rec in recommendations[:8]:
        for item in rec.get("missing_ingredients", []):
            if item in LOW_VALUE_MISSING:
                continue

            counts[item] = counts.get(item, 0) + 1

    ordered = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    return [item for item, _count in ordered[:8]]
