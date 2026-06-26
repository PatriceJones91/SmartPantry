import ast
import csv
import json
import re
import warnings
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import joblib
except Exception:
    joblib = None

try:
    import pandas as pd
except Exception:
    pd = None

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ML_MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "random_forest_nutrition_fit_model.pkl"
_ML_MODEL = None
_ML_MODEL_CHECKED = False
ML_FEATURE_NAMES = ["calories", "protein", "carbs", "fat", "ingredient_count"]

RECIPE_SOURCES = [
    {
        "path": DATA_DIR / "sample_recipe_seed_data.csv",
        "source_type": "core",
        "source_label": "Core everyday meals",
        "source_boost": 15,
        "limit": None,
    },
    {
        "path": DATA_DIR / "smart_pantry_recipe_dataset.csv",
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
    "salt", "sea salt", "kosher salt", "table salt", "truffle salt",
    "pepper", "black pepper", "white pepper", "ground pepper",
    "water", "ice", "ice water", "cooking spray", "spray", "nonstick spray",
    "seasoning", "seasoning salt", "italian seasoning", "taco seasoning",
    "garlic powder", "onion powder", "paprika", "smoked paprika",
    "cayenne", "cayenne pepper", "red pepper flakes", "chili powder",
    "parsley", "basil", "oregano", "thyme", "rosemary", "cilantro", "cumin",
    "oil", "cooking oil", "vegetable oil", "olive oil", "canola oil",
    "vinegar", "white vinegar", "apple cider vinegar",
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


# Ported from the original Smart Pantry recommendation quality filters.
OPTIONAL_STAPLES = {
    "salt", "sea salt", "kosher salt", "table salt", "truffle salt",
    "pepper", "black pepper", "white pepper", "ground pepper",
    "garlic powder", "onion powder", "paprika", "smoked paprika",
    "cayenne", "cayenne pepper", "red pepper flakes", "chili powder",
    "seasoning", "seasoning salt", "italian seasoning", "taco seasoning",
    "cinnamon", "nutmeg", "oregano", "basil", "thyme", "rosemary",
    "parsley", "cilantro", "cumin", "bay leaf", "bay leaves",
    "water", "ice", "ice water", "cooking spray", "nonstick spray",
    "oil", "cooking oil", "vegetable oil", "olive oil", "canola oil",
    "vinegar", "white vinegar", "apple cider vinegar",
}

COMMON_PANTRY_INGREDIENTS = {
    "rice", "pasta", "spaghetti", "macaroni", "bread", "tortilla", "tortillas",
    "eggs", "egg", "milk", "cheese", "butter", "yogurt", "sour cream",
    "chicken", "turkey", "ground beef", "beef", "tuna", "salmon", "shrimp", "fish",
    "beans", "black beans", "pinto beans", "kidney beans", "chickpeas", "lentils",
    "potatoes", "sweet potatoes", "tomatoes", "tomato", "tomato sauce", "salsa",
    "lettuce", "spinach", "broccoli", "carrots", "peas", "corn", "onion", "onions",
    "bell pepper", "peppers", "celery", "zucchini", "cabbage", "cucumber",
    "apples", "apple", "bananas", "banana", "strawberries", "blueberries", "berries",
    "oats", "cereal", "flour", "sugar", "peanut butter", "jelly", "jam",
    "crackers", "soup", "chicken broth", "broth", "sausage", "bacon", "tofu",
}

PRACTICAL_CUISINES = {
    "american", "italian", "mexican", "southern", "mediterranean", "asian",
    "chinese", "japanese", "thai", "indian", "middle eastern", "caribbean", "french",
}

UNWANTED_DISH_TERMS = {
    "cocktail", "cocktails", "drink", "drinks", "beverage", "sauce", "marinade",
    "dressing", "dip", "condiment", "seasoning", "spice mix", "syrup",
}

BAD_RECIPE_TERMS = {
    "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "pet", "pets",
    "kibble", "hamster", "horse", "bird", "slime", "playdough", "soap", "lotion",
    "shampoo", "cleaner", "detergent", "paint", "glue",
}

BLOG_NAME_PATTERNS = [
    r"^eat for (?:eight|8) bucks:\s*",
    r"^\$?\d+\s*(?:dollar|buck)s?:\s*",
    r"\bgrandma(?:'s)?\b",
    r"\bgrandmother(?:'s)?\b",
    r"\bmom(?:'s)?\b",
    r"\bmama(?:'s)?\b",
    r"\bdad(?:'s)?\b",
    r"\baunt(?:ie's|'s)?\b",
    r"\bnana(?:'s)?\b",
    r"\bcopycat\b",
    r"\bfamous\b",
    r"\baward winning\b",
    r"\bbest ever\b",
    r"\bworld's best\b",
    r"\brestaurant style\b",
]

DISH_STYLE_TERMS = {
    "casserole": ["casserole", "bake", "baked"],
    "salad": ["salad"],
    "sandwich": ["sandwich", "melt", "toast"],
    "wrap": ["wrap", "tortilla", "burrito", "quesadilla", "taco"],
    "soup": ["soup", "stew", "chili"],
    "pasta": ["pasta", "spaghetti", "macaroni", "noodle", "noodles"],
    "rice_bowl": ["rice", "bowl", "fried rice"],
    "breakfast": ["egg", "toast", "oat", "pancake", "waffle", "breakfast"],
    "skillet": ["skillet", "stir fry", "stir-fry"],
}


def normalize_plural_ingredient(value):
    value = clean_ingredient(value)

    irregular = {
        "tomatoes": "tomato",
        "potatoes": "potato",
        "mushrooms": "mushroom",
        "strawberries": "strawberry",
        "blueberries": "blueberry",
        "tortillas": "tortilla",
        "eggs": "egg",
        "slices": "slice",
    }

    if value in irregular:
        return irregular[value]

    if len(value) > 4 and value.endswith("ies"):
        return value[:-3] + "y"

    if len(value) > 3 and value.endswith("es"):
        return value[:-2]

    if len(value) > 3 and value.endswith("s") and not value.endswith("ss"):
        return value[:-1]

    return value


def clean_recipe_display_name(name):
    cleaned = str(name or "Recipe").strip()

    if ":" in cleaned:
        prefix, rest = cleaned.split(":", 1)
        if re.search(r"buck|dollar|budget|eat for|quick tip|recipe", prefix, re.I):
            cleaned = rest.strip()

    for pattern in BLOG_NAME_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.I).strip()

    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip(" -_.,:;'")

    if not cleaned:
        cleaned = str(name or "Recipe").strip()

    return cleaned[:80].title()


def is_optional_staple(ingredient):
    ingredient = normalize_plural_ingredient(ingredient)

    if ingredient in OPTIONAL_STAPLES:
        return True

    return any(staple in ingredient for staple in OPTIONAL_STAPLES if len(staple.split()) > 1)


def is_low_value_missing(ingredient):
    return is_optional_staple(ingredient)


def get_main_recipe_ingredients(ingredients):
    cleaned = []
    seen = set()

    for ingredient in ingredients:
        ingredient = normalize_plural_ingredient(ingredient)

        if not ingredient or ingredient in seen:
            continue

        if is_optional_staple(ingredient):
            continue

        if len(ingredient) <= 1:
            continue

        cleaned.append(ingredient)
        seen.add(ingredient)

    return cleaned


def recipe_has_bad_title(recipe_name):
    name = str(recipe_name or "").lower()
    words = set(re.sub(r"[^a-z0-9\s]", " ", name).split())

    if not name.strip():
        return True

    if len(name) > 95:
        return True

    if words.intersection(BAD_RECIPE_TERMS):
        # Allow "hot dog" as human food, but block dog food/pet records.
        if "hot" not in words:
            return True

    if re.search(r"\bdog\s+food\b|\bdog\s+treats?\b|\btreats?\s+for\s+dogs?\b|\bcat\s+food\b|\bpet\s+food\b|\bkibble\b", name):
        return True

    return False


def calculate_recipe_quality_score(recipe_name, ingredients, cuisine="", meal_type="", dish_type=""):
    name = str(recipe_name or "").lower()
    cuisine_text = str(cuisine or "").lower()
    meal_text = f"{meal_type} {dish_type}".lower()
    ingredient_count = len(ingredients)

    score = 50

    if 3 <= ingredient_count <= 8:
        score += 20
    elif ingredient_count == 2 or 9 <= ingredient_count <= 10:
        score += 10
    elif ingredient_count > 10:
        score -= min((ingredient_count - 10) * 5, 30)
    else:
        score -= 20

    common_count = sum(
        1
        for item in ingredients
        if item in COMMON_PANTRY_INGREDIENTS
        or any(item in common or common in item for common in COMMON_PANTRY_INGREDIENTS)
    )

    if ingredient_count:
        common_ratio = common_count / ingredient_count
        score += int(common_ratio * 25)

    if any(cuisine in cuisine_text for cuisine in PRACTICAL_CUISINES):
        score += 8

    if any(
        term in name or term in meal_text
        for term in [
            "pasta", "spaghetti", "rice", "bowl", "sandwich", "wrap", "soup",
            "salad", "casserole", "taco", "quesadilla", "toast", "skillet", "bake",
        ]
    ):
        score += 8

    if any(term in name or term in meal_text for term in UNWANTED_DISH_TERMS):
        score -= 35

    if recipe_has_bad_title(recipe_name):
        score -= 60

    if len(str(recipe_name)) > 90:
        score -= 8

    if re.search(r"\b(test|mock|unknown)\b", name):
        score -= 20

    return max(0, min(score, 100))


def get_dish_style(recipe_name, ingredients):
    text = clean_ingredient(str(recipe_name) + " " + " ".join(ingredients))

    for style, terms in DISH_STYLE_TERMS.items():
        if any(term in text for term in terms):
            return style

    return "general"


def get_core_recipe_groups(ingredients):
    groups = []

    for ingredient in ingredients:
        group = ingredient_family(ingredient)

        if group and group not in groups:
            groups.append(group)

    return groups


def get_recipe_family_key_from_values(recipe_name, ingredients):
    ingredients = [clean_ingredient(item) for item in ingredients]
    dish_style = get_dish_style(recipe_name, ingredients)
    core_groups = get_core_recipe_groups(ingredients)

    protein_groups = [
        group for group in core_groups
        if group in ["protein"]
    ]

    base_groups = [
        group for group in core_groups
        if group in ["grain", "vegetable", "sauce_or_liquid"]
    ]

    protein_key = "+".join(sorted(protein_groups[:2])) or "no_main_protein"
    base_key = "+".join(sorted(base_groups[:2])) or "no_main_base"

    title_words = [
        word for word in clean_ingredient(recipe_name).split()
        if word not in {"easy", "simple", "quick", "best", "homemade", "classic", "with", "and", "the", "recipe"}
    ]

    title_key = "+".join(sorted(title_words[:5]))

    return f"{protein_key}|{base_key}|{dish_style}|{title_key}"


def prioritize_recommendation_diversity(recommendations):
    first_best_by_family = []
    duplicate_family_backups = []
    seen_families = set()

    for item in recommendations:
        family_key = item.get("recipe_family_key", "")

        if family_key not in seen_families:
            first_best_by_family.append(item)
            seen_families.add(family_key)
        else:
            duplicate_family_backups.append(item)

    return first_best_by_family + duplicate_family_backups


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

    display_name = clean_recipe_display_name(name)
    ingredients = parse_ingredients(ingredients_value)
    ingredients = get_main_recipe_ingredients(ingredients)

    if not display_name or len(ingredients) < 2 or len(ingredients) > 10:
        return None

    category = get_first(row, ["category", "recipe_category", "RecipeCategory", "dish_type"], "")
    meal_type = get_first(row, ["meal_type", "meal", "course", "MealType"], "") or infer_meal_type(display_name, category)
    cuisine_type = get_first(row, ["cuisine_type", "cuisine", "Cuisine", "region"], "Everyday")
    dish_type = get_first(row, ["dish_type", "RecipeCategory", "category"], category or "Meal")

    recipe_quality_score = calculate_recipe_quality_score(
        display_name,
        ingredients,
        cuisine=cuisine_type,
        meal_type=meal_type,
        dish_type=dish_type,
    )

    if recipe_quality_score < 40:
        return None

    return {
        "recipe_name": display_name,
        "recipe_family_key": get_recipe_family_key_from_values(display_name, ingredients),
        "recipe_quality_score": recipe_quality_score,
        "ingredients_list": ingredients,
        "meal_type": meal_type,
        "cuisine_type": cuisine_type,
        "dish_type": dish_type,
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

                name_key = recipe.get("recipe_family_key") or simplify(recipe["recipe_name"])

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




def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in [None, ""]:
            return default

        cleaned = str(value).replace("g", "").replace("cal", "").replace(",", "").strip()
        return float(cleaned)
    except Exception:
        return default


def load_ml_model():
    global _ML_MODEL, _ML_MODEL_CHECKED

    if _ML_MODEL_CHECKED:
        return _ML_MODEL

    _ML_MODEL_CHECKED = True

    if joblib is None:
        return None

    if not ML_MODEL_PATH.exists():
        return None

    try:
        _ML_MODEL = joblib.load(ML_MODEL_PATH)
        return _ML_MODEL
    except Exception:
        _ML_MODEL = None
        return None


def calculate_ml_nutrition_fit(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Random Forest nutrition fit for Smart Pantry.

    The model was trained with:
    calories, protein, carbs, fat, ingredient_count

    The raw model prediction is treated as a 0-100 nutrition fit output.
    For the project interface, it is also displayed as a 0-15 ML Nutrition Fit
    because the original Smart Pantry prototype used Nutrition Fit out of 15.
    """
    calories = safe_float(recipe.get("calories"))
    protein = safe_float(recipe.get("protein"))
    carbs = safe_float(recipe.get("carbs"))
    fat = safe_float(recipe.get("fat"))
    ingredient_count = len(recipe.get("ingredients_list", []))

    model = load_ml_model()

    if model is None:
        return {
            "ml_nutrition_fit": None,
            "ml_nutrition_fit_percent": None,
            "ml_model_used": "RandomForest model unavailable",
            "ml_feature_inputs": {
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "ingredient_count": ingredient_count,
            },
        }

    try:
        feature_values = {
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "ingredient_count": ingredient_count,
        }

        if pd is not None:
            features = pd.DataFrame([feature_values], columns=ML_FEATURE_NAMES)
        else:
            features = [[calories, protein, carbs, fat, ingredient_count]]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            prediction = float(model.predict(features)[0])
        prediction = max(0.0, min(100.0, prediction))

        return {
            "ml_nutrition_fit": round((prediction / 100.0) * 15.0, 1),
            "ml_nutrition_fit_percent": round(prediction, 1),
            "ml_model_used": type(model).__name__,
            "ml_feature_inputs": {
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "ingredient_count": ingredient_count,
            },
        }
    except Exception:
        return {
            "ml_nutrition_fit": None,
            "ml_nutrition_fit_percent": None,
            "ml_model_used": "RandomForest prediction failed",
            "ml_feature_inputs": {
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "ingredient_count": ingredient_count,
            },
        }


def calculate_everyday_recipe_fit(recipe: Dict[str, Any]) -> float:
    """
    Measures whether a recipe is realistic for everyday pantry use.
    This is separate from the ML Nutrition Fit.
    """
    fit = 70.0

    ingredient_count = len(recipe.get("ingredients_list", []))
    cook_time = recipe.get("cook_time")

    if recipe.get("source_type") == "core":
        fit += 15
    elif recipe.get("source_type") == "expanded":
        fit += 5

    if ingredient_count <= 5:
        fit += 10
    elif ingredient_count <= 8:
        fit += 5
    elif ingredient_count > 12:
        fit -= 8

    if cook_time is not None:
        if cook_time <= 20:
            fit += 8
        elif cook_time <= 35:
            fit += 4
        elif cook_time > 60:
            fit -= 8

    return round(max(0, min(fit, 100)), 1)




SMART_SWAP_FAMILIES = {
    "protein": ["chicken", "turkey", "beef", "lamb", "fish", "salmon", "tuna", "shrimp", "egg", "eggs", "tofu", "beans", "lentils", "sausage"],
    "grain": ["rice", "pasta", "noodle", "noodles", "bread", "tortilla", "flour", "oats", "quinoa", "cereal", "corn", "potato", "potatoes"],
    "dairy": ["milk", "cheese", "cheddar", "mozzarella", "parmesan", "cream", "yogurt", "butter", "sour cream", "cottage cheese"],
    "vegetable": ["broccoli", "cauliflower", "carrot", "pepper", "bell pepper", "onion", "spinach", "lettuce", "tomato", "tomatoes", "celery", "corn", "peas"],
    "sauce_or_liquid": ["tomato sauce", "marinara", "salsa", "broth", "stock", "soup", "gravy", "dressing", "sauce"],
    "fat_or_oil": ["oil", "olive oil", "vegetable oil", "canola oil", "butter"],
    "seasoning": ["salt", "pepper", "garlic powder", "onion powder", "paprika", "seasoning", "italian seasoning"],
    "sweetener": ["sugar", "honey", "syrup", "brown sugar"],
}


def get_pantry_item_name(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("item_name") or item.get("name") or item.get("ingredient") or item.get("food") or "")
    return str(item or "")


def ingredient_family(name: str) -> str | None:
    clean_name = clean_ingredient(name)

    for family, terms in SMART_SWAP_FAMILIES.items():
        for term in terms:
            clean_term = clean_ingredient(term)
            if clean_name == clean_term or clean_term in clean_name or clean_name in clean_term:
                return family

    return None


def find_smart_swaps(missing: List[str], active_pantry: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    pantry_names = []

    for item in active_pantry:
        item_name = get_pantry_item_name(item).strip()
        if item_name:
            pantry_names.append(item_name)

    swaps = []
    used_pairs = set()

    for needed in missing:
        needed_clean = clean_ingredient(needed)

        if is_low_value_missing(needed_clean):
            continue

        needed_family = ingredient_family(needed)

        if not needed_family:
            continue

        for pantry_item in pantry_names:
            pantry_clean = clean_ingredient(pantry_item)

            if pantry_clean == needed_clean:
                continue

            pantry_family = ingredient_family(pantry_item)

            if pantry_family != needed_family:
                continue

            pair_key = (needed_clean, pantry_clean)

            if pair_key in used_pairs:
                continue

            used_pairs.add(pair_key)

            swaps.append({
                "needed": needed,
                "use_instead": pantry_item,
                "family": needed_family,
                "confidence": "Possible",
                "reason": "This pantry item is in the same ingredient family, so it may work as a practical swap depending on the recipe.",
            })

            break

        if len(swaps) >= limit:
            break

    return swaps

def estimate_coverage_with_smart_swaps(
    matched: List[str],
    missing: List[str],
    total_ingredients: int,
    smart_swaps: Optional[List[Dict[str, Any]]] = None,
) -> float:
    """
    Estimates recipe coverage after allowing minor pantry substitutions.
    """
    total = max(total_ingredients, 1)

    easy_missing = [
        item for item in missing
        if is_low_value_missing(item)
    ]

    swap_count = len(smart_swaps or [])

    coverage = ((len(matched) + len(easy_missing) + swap_count) / total) * 100

    return round(max(0, min(coverage, 100)), 1)


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
            "exact_pantry_match_percent": 0,
            "coverage_with_smart_swaps_percent": 0,
            "smart_swaps": [],
            "everyday_recipe_fit": 0,
            "score_breakdown": {},
            "matched_ingredients": [],
            "missing_ingredients": [],
            "expiring_items": [],
            "source_type": recipe.get("source_type"),
            "source_label": recipe.get("source_label"),
            "why": "Filtered out because it conflicts with saved allergies or foods to avoid.",
            "filtered_out": True,
        }

    nutrition_fit = calculate_ml_nutrition_fit(recipe)

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

    missing = [item for item in missing if not is_low_value_missing(item)]
    matched = [item for item in matched if not is_low_value_missing(item)]
    recipe_ingredients = [item for item in recipe_ingredients if not is_low_value_missing(item)]

    total_ingredients = max(len(recipe_ingredients), 1)
    match_ratio = len(matched) / total_ingredients
    exact_pantry_match_percent = round(match_ratio * 100, 1)
    try:
        smart_swaps = find_smart_swaps(missing, pantry_items)
    except Exception:
        smart_swaps = []

    try:
        coverage_with_smart_swaps_percent = estimate_coverage_with_smart_swaps(
            matched,
            missing,
            total_ingredients,
            smart_swaps,
        )
    except Exception:
        coverage_with_smart_swaps_percent = exact_pantry_match_percent
    everyday_recipe_fit = calculate_everyday_recipe_fit(recipe)

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
    missing_penalty = len([item for item in missing if not is_low_value_missing(item)]) * 5
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

    score_breakdown = {
        "pantry_match": round(match_score + matched_count_bonus, 1),
        "expiration_priority": round(expiring_bonus, 1),
        "simplicity": round(simplicity_bonus, 1),
        "data_source": round(source_boost, 1),
        "profile_fit": round(profile_boost, 1),
        "missing_penalty": round(missing_penalty, 1),
        "no_match_penalty": round(no_match_penalty, 1),
    }

    matched = [item for item in matched if is_real_ingredient(item) and not is_low_value_missing(item)]
    missing = [item for item in missing if is_real_ingredient(item) and not is_low_value_missing(item)]
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
        "ml_nutrition_fit": nutrition_fit.get("ml_nutrition_fit"),
        "ml_nutrition_fit_percent": nutrition_fit.get("ml_nutrition_fit_percent"),
        "ml_model_used": nutrition_fit.get("ml_model_used"),
        "ml_feature_inputs": nutrition_fit.get("ml_feature_inputs"),
        "cook_time": recipe.get("cook_time"),
        "instructions": recipe.get("instructions"),
        "score": score,
        "exact_pantry_match_percent": exact_pantry_match_percent,
        "coverage_with_smart_swaps_percent": coverage_with_smart_swaps_percent,
        "smart_swaps": smart_swaps,
        "everyday_recipe_fit": everyday_recipe_fit,
        "score_breakdown": score_breakdown,
        "matched_ingredients": matched,
        "missing_ingredients": missing,
        "expiring_items": list(dict.fromkeys([item for item in expiring_items if item])),
        "source_type": recipe.get("source_type"),
        "source_label": recipe.get("source_label"),
        "recipe_family_key": recipe.get("recipe_family_key"),
        "recipe_quality_score": recipe.get("recipe_quality_score"),
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

    scored = prioritize_recommendation_diversity(scored)

    selected = []
    selected_names = set()
    selected_families = set()

    for recipe in scored:
        if len(selected) >= 10:
            break

        name_key = simplify(recipe["recipe_name"])
        family_key = recipe.get("recipe_family_key") or name_key

        if name_key in selected_names or family_key in selected_families:
            continue

        selected.append(recipe)
        selected_names.add(name_key)
        selected_families.add(family_key)

    expanded_added = 0

    for recipe in scored:
        if expanded_added >= 4 or len(selected) >= 14:
            break

        if recipe.get("source_type") != "expanded":
            continue

        name_key = simplify(recipe["recipe_name"])
        family_key = recipe.get("recipe_family_key") or name_key

        if name_key in selected_names or family_key in selected_families:
            continue

        if recipe.get("score", 0) < 25:
            continue

        selected.append(recipe)
        selected_names.add(name_key)
        selected_families.add(family_key)
        expanded_added += 1

    return selected


def grocery_suggestions(recommendations: List[Dict[str, Any]]) -> List[str]:
    counts = {}

    for rec in recommendations[:8]:
        for item in rec.get("missing_ingredients", []):
            if is_low_value_missing(item):
                continue

            counts[item] = counts.get(item, 0) + 1

    ordered = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    return [item for item, _count in ordered[:8]]
