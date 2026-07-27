import ast
import csv
import json
import re
import warnings
from difflib import SequenceMatcher
from datetime import date, datetime
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, List, Optional

from services.recommendations.meal_classifier import classify_recipe_meal_types

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
        "source_boost": 3,
        "limit": None,
    },
    {
        "path": DATA_DIR / "smart_pantry_recipe_dataset.csv",
        "source_type": "expanded",
        "source_label": "Expanded recipe library",
        "source_boost": 0,
        "limit": None,
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



INGREDIENT_ALIASES = {
    "chicken breasts": "chicken breast",
    "boneless chicken breast": "chicken breast",
    "skinless chicken breast": "chicken breast",
    "boneless skinless chicken breast": "chicken breast",
    "chicken breasts": "chicken breast",
    "popcorn shrimp": "shrimp",
    "prawns": "shrimp",
    "prawn": "shrimp",
    "angel hair pasta": "angel hair pasta",
    "angel hair": "angel hair pasta",
    "shell pasta": "shell pasta",
    "pasta shells": "shell pasta",
    "brown rice": "brown rice",
    "white rice": "white rice",
    "bell peppers": "bell pepper",
    "green peppers": "bell pepper",
    "red peppers": "bell pepper",
    "lemons": "lemon",
    "apples": "apple",
    "eggs": "egg",
    "asparagu": "asparagus",
}

# Specific terms that must never match merely because one generic word overlaps.
AMBIGUOUS_SINGLE_TOKENS = {
    "sauce", "pepper", "shell", "cream", "cheese", "rice", "pasta", "oil",
    "milk", "bread", "fish", "bean", "beans", "apple", "lemon",
}


@lru_cache(maxsize=50000)
def canonical_ingredient(value: str) -> str:
    """Normalize a pantry or recipe ingredient without erasing useful specificity."""
    cleaned = clean_ingredient(value)
    cleaned = INGREDIENT_ALIASES.get(cleaned, cleaned)

    # Common phrase normalization. Keep distinctions such as pasta sauce versus
    # cheese sauce and bell pepper versus black pepper.
    replacements = [
        (r"\bboneless\s+skinless\s+", ""),
        (r"\bskinless\s+", ""),
        (r"\bboneless\s+", ""),
        (r"\bchicken breast fillet\b", "chicken breast"),
        (r"\bpasta shell\b", "shell pasta"),
        (r"\bmarinara sauce\b", "pasta sauce"),
        (r"\bspaghetti sauce\b", "pasta sauce"),
        # Pantry entries often come from barcode/product names. Reduce harmless
        # package descriptors so the food can satisfy ordinary recipe terms.
        (r"\b(?:finely|freshly|coarsely)\s+shredded\s+", ""),
        (r"\bshredded\s+", ""),
        (r"\b(?:large|medium|small|jumbo)\s+eggs?\b", "egg"),
        (r"\bangus\s+ground\s+beef\s+patties?\b", "ground beef"),
        (r"\bground\s+beef\s+patties?\b", "ground beef"),
        (r"\b(?:original|classic|traditional)\s+", ""),
    ]
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned).strip()

    return INGREDIENT_ALIASES.get(cleaned, cleaned)


def ingredient_identity(value: str) -> tuple[str, str | None]:
    cleaned = canonical_ingredient(value)
    return cleaned, ingredient_swap_role(cleaned)

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
        "asparagus": "asparagus",
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

    cleaned = re.sub(r"\s+recipes?$", "", cleaned, flags=re.I).strip()
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


def calculate_meal_practicality(recipe: Dict[str, Any]) -> float:
    """Estimate whether a recommendation resembles a meal people commonly prepare.

    This is deliberately explainable: established dataset recipes receive a small
    trust advantage, common meal structures score well, and unusual generated
    combinations are allowed but ranked lower instead of being silently removed.
    """
    name = clean_ingredient(recipe.get("recipe_name", ""))
    ingredients = [canonical_ingredient(item) for item in recipe.get("ingredients_list", [])]
    source_type = str(recipe.get("source_type") or "").lower()
    meal_type = str(recipe.get("meal_type") or "").lower()
    dish_type = str(recipe.get("dish_type") or "").lower()
    text = f"{name} {dish_type}"

    score = 68.0 if source_type != "generated" else 58.0

    common_structures = [
        "rice bowl", "stir fry", "pasta", "scramble", "omelet", "soup",
        "stew", "salad", "sandwich", "wrap", "casserole", "taco",
        "quesadilla", "roast", "baked", "skillet", "curry", "toast",
    ]
    if any(term in text for term in common_structures):
        score += 15

    ingredient_text = " ".join(ingredients)
    seafood = any(term in ingredient_text for term in ["shrimp", "salmon", "tuna", "fish", "seafood"])
    pasta = any(term in ingredient_text for term in ["pasta", "spaghetti", "angel hair", "macaroni", "noodle"])
    rice = "rice" in ingredient_text
    lemon = "lemon" in ingredient_text
    asparagus = "asparagus" in ingredient_text
    eggs = any("egg" in item for item in ingredients)
    vegetables = any(term in ingredient_text for term in ["pepper", "asparagus", "broccoli", "spinach", "carrot", "tomato", "onion"])

    if seafood and pasta and lemon:
        score += 16
    if seafood and rice and vegetables:
        score += 14
    if eggs and vegetables and meal_type == "breakfast":
        score += 14
    if asparagus and (seafood or pasta or rice):
        score += 6

    # Keep shrimp mac and cheese possible, but below more natural shrimp meals.
    if seafood and any("cheese sauce" in item or "mac cheese" in item for item in ingredients):
        score -= 18
    if source_type == "generated" and len(ingredients) <= 2 and meal_type not in {"dessert", "snack"}:
        score -= 12
    if meal_type in {"dessert", "snack"}:
        score -= 8

    return round(max(0.0, min(score, 100.0)), 1)


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
    """Build a stable meal-family key that groups renamed versions of the same dish.

    The previous key used broad categories such as ``protein`` and ``grain``. That
    could treat unrelated meals as one family while still allowing renamed copies
    of the same meal through. This key keeps the actual ingredient roles and the
    meaningful title words.
    """
    cleaned_ingredients = [clean_ingredient(item) for item in ingredients if clean_ingredient(item)]
    dish_style = get_dish_style(recipe_name, cleaned_ingredients)

    roles = []
    for ingredient in cleaned_ingredients:
        role = ingredient_swap_role(ingredient) or ingredient_family(ingredient)
        if role and role not in roles:
            roles.append(role)

    filler_words = {
        "easy", "simple", "quick", "best", "homemade", "classic", "healthy",
        "creamy", "crispy", "delicious", "amazing", "favorite", "perfect",
        "with", "and", "the", "a", "an", "recipe", "style", "weeknight",
        "one", "pan", "pot", "skillet",
    }
    title_words = [
        word for word in clean_ingredient(recipe_name).split()
        if word not in filler_words and len(word) > 2
    ]

    # Keep the first meaningful title words in their original order. This makes
    # "Easy Chicken Rice" and "Quick Chicken and Rice" share a family key.
    title_key = "+".join(list(dict.fromkeys(title_words))[:4]) or "meal"
    role_key = "+".join(sorted(roles[:4])) or "general"

    return f"{dish_style}|{role_key}|{title_key}"


def _recommendation_title_tokens(item: Dict[str, Any]) -> set:
    filler_words = {
        "easy", "simple", "quick", "best", "homemade", "classic", "healthy",
        "creamy", "crispy", "baked", "grilled", "fried", "delicious",
        "amazing", "favorite", "perfect", "with", "and", "the", "a", "an",
        "recipe", "style", "weeknight", "one", "pan", "pot", "skillet",
    }
    text = clean_ingredient(item.get("recipe_name", ""))
    return {word for word in text.split() if word not in filler_words and len(word) > 2}


def _recommendation_ingredient_set(item: Dict[str, Any]) -> set:
    values = list(item.get("matched_ingredients", [])) + list(item.get("missing_ingredients", []))
    return {
        clean_ingredient(value)
        for value in values
        if clean_ingredient(value) and not is_low_value_missing(value)
    }


def recommendations_are_too_similar(candidate: Dict[str, Any], existing: Dict[str, Any]) -> bool:
    """Return True when two displayed cards are essentially the same meal."""
    if candidate.get("recipe_family_key") and candidate.get("recipe_family_key") == existing.get("recipe_family_key"):
        return True

    candidate_name = clean_ingredient(candidate.get("recipe_name", ""))
    existing_name = clean_ingredient(existing.get("recipe_name", ""))
    title_similarity = SequenceMatcher(None, candidate_name, existing_name).ratio()

    candidate_tokens = _recommendation_title_tokens(candidate)
    existing_tokens = _recommendation_title_tokens(existing)
    title_overlap = (
        len(candidate_tokens & existing_tokens) / max(1, len(candidate_tokens | existing_tokens))
        if candidate_tokens and existing_tokens else 0
    )

    candidate_ingredients = _recommendation_ingredient_set(candidate)
    existing_ingredients = _recommendation_ingredient_set(existing)
    ingredient_overlap = (
        len(candidate_ingredients & existing_ingredients)
        / max(1, len(candidate_ingredients | existing_ingredients))
        if candidate_ingredients and existing_ingredients else 0
    )

    # Strong title match plus similar ingredients, or near-identical meaningful
    # title words, means the participant would perceive these as the same meal.
    if title_similarity >= 0.84 and ingredient_overlap >= 0.50:
        return True
    if title_overlap >= 0.75 and ingredient_overlap >= 0.55:
        return True

    return False


def prioritize_recommendation_diversity(recommendations):
    unique = []
    for item in recommendations:
        if any(recommendations_are_too_similar(item, existing) for existing in unique):
            continue
        unique.append(item)
    return unique


def normalize_key(value: str) -> str:
    return (value or "").strip().lower().replace(" ", "_").replace("-", "_")


def get_first(row: Dict[str, Any], possible_names: List[str], default: str = "") -> str:
    normalized = {normalize_key(k): v for k, v in row.items()}

    for name in possible_names:
        key = normalize_key(name)
        if key in normalized and normalized[key] not in [None, ""]:
            return str(normalized[key]).strip()

    return default


@lru_cache(maxsize=50000)
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


@lru_cache(maxsize=50000)
def ingredient_tokens(value: str) -> frozenset:
    return frozenset({
        token
        for token in simplify(value).split()
        if len(token) > 2 and token not in STOP_WORDS
    })



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


def infer_meal_type(name: str, category: str = "", cook_time: Optional[int] = None) -> str:
    text = f"{name} {category}".lower()

    if any(word in text for word in ["cake", "cookie", "brownie", "pie", "dessert", "pudding", "cobbler", "baked apple"]):
        return "Dessert"
    if any(word in text for word in ["breakfast", "omelet", "omelette", "pancake", "waffle", "oatmeal", "cereal", "french toast"]):
        return "Breakfast"
    if any(word in text for word in ["lunch", "wrap", "salad", "sandwich", "soup"]):
        return "Lunch"
    if cook_time is not None and cook_time <= 20:
        return "Quick Meal"
    if any(word in text for word in ["dinner", "casserole", "pasta", "rice", "bowl", "chicken", "fish", "shrimp", "beef"]):
        return "Dinner"
    return "Meal"



def clean_instruction_display(value: Any, recipe_name: str, ingredients: List[str]) -> str:
    """
    Keeps recipe instructions readable for the participant. Some datasets store
    instructions as JSON/Python lists or leave them blank, so this creates a
    clean display string without showing raw brackets or metadata.
    """
    raw = str(value or "").strip()
    steps = []

    if raw:
        parsed = None
        if raw.startswith("[") or raw.startswith("{"):
            try:
                parsed = json.loads(raw)
            except Exception:
                try:
                    parsed = ast.literal_eval(raw)
                except Exception:
                    parsed = None

        if isinstance(parsed, list):
            steps = [str(item).strip() for item in parsed if str(item).strip()]
        elif isinstance(parsed, dict):
            possible = parsed.get("instructions") or parsed.get("steps") or parsed.get("directions")
            if isinstance(possible, list):
                steps = [str(item).strip() for item in possible if str(item).strip()]
            elif possible:
                steps = [str(possible).strip()]
        else:
            steps = [raw]

    cleaned_steps = []
    for step in steps:
        step = re.sub(r"\\s+", " ", str(step)).strip(" []'\".,")
        if step and step.lower() not in {"nan", "none", "null"}:
            cleaned_steps.append(step)

    if cleaned_steps:
        return " ".join(
            f"{index + 1}. {step}" if not re.match(r"^\\d+[.)]", step) else step
            for index, step in enumerate(cleaned_steps[:8])
        )[:1800]

    main_items = ", ".join(ingredients[:6]) if ingredients else "the listed ingredients"
    return (
        f"1. Gather the ingredients for {recipe_name}, including {main_items}. "
        "2. Wash, cut, and prepare the ingredients as needed. "
        "3. Cook or assemble the main ingredients until they are safely prepared and heated through. "
        "4. Taste, adjust seasoning if needed, and serve."
    )

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
    cook_time = parse_minutes(get_first(row, ["cook_time", "CookTime", "total_time", "TotalTime", "minutes"]))
    dataset_meal_type = get_first(row, ["meal_type", "meal", "course", "MealType"], "")
    cuisine_type = get_first(row, ["cuisine_type", "cuisine", "Cuisine", "region"], "Everyday")
    dish_type = get_first(row, ["dish_type", "RecipeCategory", "category"], category or "Meal")

    classification = classify_recipe_meal_types({
        "recipe_name": display_name,
        "ingredients_list": ingredients,
        "meal_type": dataset_meal_type,
        "dish_type": dish_type,
        "cook_time": cook_time,
    })
    meal_type = classification["smart_primary_meal_type"]

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
        "dataset_meal_type": dataset_meal_type,
        **classification,
        "calories": get_first(row, ["calories", "Calories"], ""),
        "protein": get_first(row, ["protein", "ProteinContent", "protein_g"], ""),
        "carbs": get_first(row, ["carbs", "CarbohydrateContent", "carbohydrates", "carbs_g"], ""),
        "fat": get_first(row, ["fat", "FatContent", "fat_g"], ""),
        "cook_time": cook_time,
        "instructions": clean_instruction_display(
            get_first(
                row,
                ["instructions", "Instructions", "recipe_instructions", "RecipeInstructions", "directions"],
                "",
            ),
            display_name,
            ingredients,
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
    """Meaningful ingredient matching for recipe feasibility.

    Exact/canonical phrase matches are preferred. A shared generic word is not
    enough: bell pepper does not satisfy black pepper, pasta sauce does not
    satisfy cheese sauce, and shell pasta does not satisfy taco shells.
    """
    pantry_clean = canonical_ingredient(pantry_name)
    ingredient_clean = canonical_ingredient(ingredient)

    if not pantry_clean or not ingredient_clean:
        return False

    if pantry_clean == ingredient_clean:
        return True

    # Product-name compatibility after descriptive words/packaging terms have
    # been cleaned. Keep sauces separate from ordinary cheese.
    if ingredient_clean == "cheese" and pantry_clean.endswith("cheese") and "sauce" not in pantry_clean:
        return True
    if pantry_clean == "cheese" and ingredient_clean.endswith("cheese") and "sauce" not in ingredient_clean:
        return True
    if ingredient_clean in {"beef", "ground beef"} and "beef" in pantry_clean and "pattie" in pantry_clean:
        return True
    if pantry_clean in {"beef", "ground beef"} and "beef" in ingredient_clean and "pattie" in ingredient_clean:
        return True

    # Safe specific-to-general matches.
    safe_generalizations = {
        "pasta": {"angel hair pasta", "shell pasta", "spaghetti", "macaroni", "noodle", "noodles"},
        "rice": {"brown rice", "white rice", "jasmine rice", "basmati rice"},
        "chicken": {"chicken breast", "chicken thigh", "chicken wing", "chicken tender"},
        "shrimp": {"popcorn shrimp"},
        "egg": {"eggs", "large egg", "large eggs"},
        "cheese": {"shredded cheese", "finely shredded cheese", "cheddar cheese", "mozzarella cheese", "monterey jack cheese", "colby jack cheese"},
        "beef": {"ground beef", "beef patty", "beef patties"},
        "ground beef": {"beef patty", "beef patties", "angus ground beef patty", "angus ground beef patties"},
        "bell pepper": {"green bell pepper", "red bell pepper", "yellow bell pepper"},
    }
    for general, specifics in safe_generalizations.items():
        if ingredient_clean == general and pantry_clean in specifics:
            return True
        if pantry_clean == general and ingredient_clean in specifics:
            return True

    pantry_tokens = ingredient_tokens(pantry_clean)
    recipe_tokens = ingredient_tokens(ingredient_clean)
    shared = pantry_tokens & recipe_tokens

    if not shared:
        return False

    # Never accept a single ambiguous token by itself.
    if len(shared) == 1 and next(iter(shared)) in AMBIGUOUS_SINGLE_TOKENS:
        return False

    # Multi-word ingredients need strong token agreement, not one accidental word.
    overlap = len(shared) / max(1, min(len(pantry_tokens), len(recipe_tokens)))
    if overlap >= 0.75 and len(shared) >= 2:
        return True

    return False



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


def _contains_any(clean_name: str, terms: List[str]) -> bool:
    return any(term in clean_name for term in terms)


@lru_cache(maxsize=50000)
def ingredient_swap_role(name: str) -> str | None:
    """
    Uses stricter ingredient roles for Smart Swaps than the broader recipe-family logic.
    This avoids bad swaps like rice for oats, milk for baking chips, or peppers for tomatoes.
    """
    clean_name = clean_ingredient(name)

    if not clean_name:
        return None

    if _contains_any(clean_name, ["butterscotch chip", "chocolate chip", "white chocolate chip", "baking chip"]):
        return "baking_chip"
    if _contains_any(clean_name, ["flour", "cornstarch", "bread crumb", "breadcrumb", "panko"]):
        return "coating_or_flour"
    if _contains_any(clean_name, ["oat", "oatmeal"]):
        return "oats"
    if _contains_any(clean_name, ["rice", "quinoa"]):
        return "rice_grain"
    if _contains_any(clean_name, ["pasta", "spaghetti", "macaroni", "noodle"]):
        return "pasta"
    if _contains_any(clean_name, ["bread", "bun", "roll", "bagel", "toast"]):
        return "bread"
    if _contains_any(clean_name, ["tortilla", "wrap", "flatbread"]):
        return "wrap"
    if _contains_any(clean_name, ["potato"]):
        return "potato"

    if _contains_any(clean_name, ["chicken", "turkey"]):
        return "poultry"
    if _contains_any(clean_name, ["beef", "steak", "lamb"]):
        return "red_meat"
    if _contains_any(clean_name, ["tuna", "salmon", "fish", "shrimp"]):
        return "seafood"
    if _contains_any(clean_name, ["bean", "lentil", "chickpea", "tofu"]):
        return "plant_protein"
    if _contains_any(clean_name, ["egg"]):
        return "egg"

    if _contains_any(clean_name, ["tomato", "tomatoes"]):
        return "tomato"
    if _contains_any(clean_name, ["bell pepper", "green pepper", "red pepper", "pepper"]):
        return "pepper"
    if _contains_any(clean_name, ["lettuce", "spinach", "kale", "greens"]):
        return "leafy_green"
    if _contains_any(clean_name, ["broccoli", "cauliflower"]):
        return "cruciferous"
    if _contains_any(clean_name, ["corn"]):
        return "corn"
    if _contains_any(clean_name, ["carrot"]):
        return "carrot"
    if _contains_any(clean_name, ["onion"]):
        # Onions are often omitted for allergy/preference reasons instead of replaced.
        return None

    if _contains_any(clean_name, ["cheese", "cheddar", "mozzarella", "parmesan"]):
        return "cheese"
    if _contains_any(clean_name, ["milk", "cream", "half and half", "yogurt"]):
        return "milk_or_cream"
    if _contains_any(clean_name, ["butter", "margarine"]):
        return "butter"
    if _contains_any(clean_name, ["oil", "olive oil", "vegetable oil", "canola oil"]):
        return "oil"

    if _contains_any(clean_name, ["sugar", "brown sugar", "honey", "syrup"]):
        return "sweetener"

    return None


def smart_swap_reason(role: str) -> str:
    reasons = {
        "poultry": "This is another poultry option and is usually a practical protein swap.",
        "red_meat": "This is another red-meat option and may work as a protein swap.",
        "seafood": "This is another seafood option and may work as a protein swap.",
        "plant_protein": "This is another plant-based protein option.",
        "tomato": "This is another tomato-based ingredient and is a close recipe swap.",
        "pepper": "This is another pepper ingredient and is a close recipe swap.",
        "leafy_green": "This is another leafy green and is a close produce swap.",
        "cheese": "This is another cheese option and should work in many similar recipes.",
        "milk_or_cream": "This is another milk or cream option and may work in the same recipe role.",
        "butter": "This is another butter-style option and may work for the same recipe role.",
        "oil": "This is another cooking oil option and may work for the same recipe role.",
        "rice_grain": "This is another rice or grain option and should only be used for bowl or side-dish style recipes.",
        "pasta": "This is another pasta or noodle option.",
        "bread": "This is another bread option and may work for toast or sandwiches.",
        "wrap": "This is another wrap or tortilla option.",
        "oats": "This is another oat ingredient and should stay close to the recipe purpose.",
        "coating_or_flour": "This is another coating or flour-style ingredient.",
        "baking_chip": "This is another baking chip or mix-in option.",
        "sweetener": "This is another sweetener option and may work in small amounts.",
    }
    return reasons.get(role, "This is a close pantry replacement for the missing ingredient.")


def find_smart_swaps(missing: List[str], active_pantry: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """
    Creates only practical Smart Swap options. A swap is shown only when the
    missing ingredient and pantry item share the same functional recipe role.
    This prevents weak suggestions such as rice for oats, milk for chips, or
    peppers for tomatoes.
    """
    pantry_names = []

    for item in active_pantry:
        item_name = get_pantry_item_name(item).strip()
        if item_name:
            pantry_names.append(item_name)

    swaps = []
    used_pairs = set()

    allowed_roles = {
        "poultry", "red_meat", "seafood", "plant_protein",
        "tomato", "pepper", "leafy_green", "cruciferous", "corn", "carrot",
        "cheese", "milk_or_cream", "butter", "oil",
        "pasta", "bread", "wrap", "oats", "coating_or_flour",
        "baking_chip", "sweetener",
    }

    for needed in missing:
        needed_clean = clean_ingredient(needed)

        if is_low_value_missing(needed_clean):
            continue

        needed_role = ingredient_swap_role(needed)

        if not needed_role or needed_role not in allowed_roles:
            continue

        for pantry_item in pantry_names:
            pantry_clean = clean_ingredient(pantry_item)

            if pantry_clean == needed_clean:
                continue

            pantry_role = ingredient_swap_role(pantry_item)

            if pantry_role != needed_role:
                continue

            # Avoid replacing specialty baking items with general liquids or grains.
            if needed_role in {"oats", "baking_chip", "coating_or_flour"}:
                if pantry_role != needed_role:
                    continue

            pair_key = (needed_clean, pantry_clean)

            if pair_key in used_pairs:
                continue

            used_pairs.add(pair_key)

            swaps.append({
                "needed": needed,
                "use_instead": pantry_item,
                "family": needed_role,
                "confidence": "Suggested",
                "reason": smart_swap_reason(needed_role),
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



def build_expiring_details(matched_pantry_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Builds readable expiration evidence for the frontend.
    These details help explain why a meal was ranked higher.
    """
    details = []
    seen = set()

    for item in matched_pantry_items:
        item_name = item.get("item_name") or item.get("name") or ""
        if not item_name or item_name in seen:
            continue

        item_days = days_until(item.get("expiration_date"))

        if item_days is None or item_days > 10:
            continue

        if item_days <= 0:
            urgency = "expired"
            label = f"{abs(item_days)} day(s) expired"
        elif item_days <= 1:
            urgency = "use_now"
            label = f"{item_days} day(s) left"
        elif item_days <= 4:
            urgency = "use_soon"
            label = f"{item_days} day(s) left"
        else:
            urgency = "plan_ahead"
            label = f"{item_days} day(s) left"

        details.append({
            "item_name": item_name,
            "days": item_days,
            "urgency": urgency,
            "label": label,
        })
        seen.add(item_name)

    details.sort(key=lambda item: item["days"])
    return details



def title_required_protein_role(recipe_name: str) -> str | None:
    text = canonical_ingredient(recipe_name)
    checks = [
        ("shrimp", "seafood"), ("salmon", "seafood"), ("tuna", "seafood"),
        ("fish", "seafood"), ("chicken", "poultry"), ("turkey", "poultry"),
        ("beef", "red_meat"), ("steak", "red_meat"), ("lamb", "red_meat"),
        ("pork", "red_meat"), ("sausage", "red_meat"),
        ("tofu", "plant_protein"), ("lentil", "plant_protein"),
        ("bean", "plant_protein"), ("egg", "egg"), ("omelet", "egg"),
        ("frittata", "egg"),
    ]
    for term, role in checks:
        if re.search(rf"\b{re.escape(term)}\b", text):
            return role
    return None


def pantry_quantity_value(item: Dict[str, Any]) -> float:
    """Return a numeric pantry quantity; blank/invalid values count as available (1)."""
    raw = item.get("quantity")
    if raw in (None, ""):
        return 1.0
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return 1.0


def pantry_item_is_available(item: Dict[str, Any]) -> bool:
    """An item may remain in history, but zero/negative quantities cannot satisfy a recipe."""
    status = str(item.get("status") or "").strip().lower()
    return status != "deleted" and pantry_quantity_value(item) > 0


def pantry_urgency_value(item: Dict[str, Any]) -> float:
    days = days_until(item.get("expiration_date"))
    if days is None:
        return 0.0
    if days <= 0:
        return 14.0
    if days <= 1:
        return 12.0
    if days <= 4:
        return 8.0
    if days <= 10:
        return 3.0
    return 0.0


def build_pantry_meal_templates(active_pantry: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a small number of compatible pantry meals, not every possible template permutation."""
    available = [item for item in active_pantry if pantry_item_is_available(item)]
    names = [get_pantry_item_name(item).strip() for item in available if get_pantry_item_name(item).strip()]
    item_by_name = {get_pantry_item_name(item).strip(): item for item in available}

    def first_matching(*terms):
        for name in names:
            clean = canonical_ingredient(name)
            if any(term in clean for term in terms):
                return name
        return None

    proteins = []
    for name in names:
        clean = canonical_ingredient(name)
        role = ingredient_swap_role(name)
        # Processed meats can appear in real recipes, but should not be used to generate
        # artificial lemon-pasta or rice-bowl combinations.
        if role in {"poultry", "seafood", "red_meat", "plant_protein"} and not any(
            term in clean for term in ["bacon", "sausage", "hot dog"]
        ):
            proteins.append(name)
    proteins.sort(key=lambda name: -pantry_urgency_value(item_by_name.get(name, {})))

    rice = first_matching("brown rice", "white rice", "rice")
    pasta = next((
        name for name in names
        if any(term in canonical_ingredient(name) for term in [
            "angel hair pasta", "shell pasta", "pasta", "spaghetti", "macaroni", "noodle"
        ]) and "cheese sauce" not in canonical_ingredient(name)
    ), None)
    composite_mac = first_matching("pasta cheese sauce", "shell pasta cheese sauce", "mac cheese", "macaroni cheese")
    vegetables = []
    for name in names:
        role = ingredient_swap_role(name)
        if role in {"pepper", "leafy_green", "cruciferous", "corn", "carrot", "tomato"} or "asparagus" in canonical_ingredient(name):
            vegetables.append(name)
    vegetables.sort(key=lambda name: -pantry_urgency_value(item_by_name.get(name, {})))

    egg = first_matching("egg")
    milk = first_matching("milk")
    butter = first_matching("butter")
    lemon = first_matching("lemon")
    apple = first_matching("apple")
    pasta_sauce = first_matching("pasta sauce", "marinara")
    templates = []

    def add(name, ingredients, meal_type, dish_type, minutes, instructions, family):
        ingredients = list(dict.fromkeys([item for item in ingredients if item]))
        if len(ingredients) < 2:
            return
        templates.append({
            "recipe_name": name, "recipe_family_key": family, "recipe_quality_score": 92,
            "ingredients_list": ingredients, "meal_type": meal_type, "cuisine_type": "Everyday",
            "dish_type": dish_type, "calories": "", "protein": "", "carbs": "", "fat": "",
            "cook_time": minutes, "instructions": instructions, "source_type": "generated",
            "source_label": "Pantry-built meal", "source_boost": 1,
        })

    # Generate only one bowl and one pasta meal, using the most urgent compatible protein.
    primary_protein = proteins[0] if proteins else None
    urgent_veg = vegetables[0] if vegetables else None
    asparagus = next((v for v in vegetables if "asparagus" in canonical_ingredient(v)), None)

    if primary_protein and rice:
        label = clean_recipe_display_name(primary_protein)
        veg = asparagus or urgent_veg
        veg_label = f", {clean_recipe_display_name(veg)}" if veg else ""
        add(
            f"{label}{veg_label} and {clean_recipe_display_name(rice)} Bowl",
            [primary_protein, rice, veg, butter], "Dinner", "Rice Bowl", 25,
            f"1. Cook or reheat the {rice}. 2. Prepare the {primary_protein} until safely cooked. "
            f"3. Cook the {veg or 'vegetable'} with a small amount of {butter or 'oil'}. 4. Serve together as a bowl.",
            "pantry_bowl|primary|rice",
        )

    if primary_protein and pasta:
        label = clean_recipe_display_name(primary_protein)
        veg = asparagus or urgent_veg
        title_parts = ["Lemon" if lemon else "", label, clean_recipe_display_name(veg) if veg else "", "Pasta"]
        add(
            " ".join(part for part in title_parts if part), [primary_protein, pasta, veg, lemon, butter, pasta_sauce],
            "Dinner", "Pasta", 30,
            f"1. Cook the {pasta}. 2. Prepare the {primary_protein} until safely cooked. "
            f"3. Cook the {veg or 'vegetable'} in {butter or 'oil'}. 4. Toss together"
            f"{', with ' + lemon if lemon else ''}{' and ' + pasta_sauce if pasta_sauce else ''}.",
            "pantry_pasta|primary|pasta",
        )

    if composite_mac and primary_protein:
        label = clean_recipe_display_name(primary_protein)
        add(
            f"{label} Mac and Cheese", [composite_mac, primary_protein, milk, butter],
            "Quick Meal", "Pasta", 20,
            f"1. Prepare the {composite_mac} according to its package directions. "
            f"2. Heat the {primary_protein} until safely cooked. 3. Fold together and serve.",
            "pantry_mac|primary|pasta",
        )

    if egg and vegetables:
        veg = urgent_veg
        add(
            f"{clean_recipe_display_name(veg)} and Egg Scramble", [egg, veg, milk, butter],
            "Breakfast", "Breakfast", 15,
            f"1. Lightly cook the {veg} in {butter or 'oil'}. 2. Whisk the {egg}"
            f"{' with ' + milk if milk else ''}. 3. Add the eggs and cook until set.",
            "pantry_scramble|egg|vegetable",
        )

    if apple and butter:
        add(
            "Warm Buttered Apples", [apple, butter], "Dessert", "Dessert", 15,
            f"1. Slice the {apple}. 2. Cook gently with the {butter} until softened. 3. Serve warm.",
            "pantry_dessert|apple|skillet",
        )
    return templates

def classify_recommendation_phase(
    matched: List[str],
    missing: List[str],
    expiring_details: List[Dict[str, Any]],
    exact_match_percent: float,
    coverage_with_swaps: float,
    recipe: Dict[str, Any],
    primary_protein_matched: bool = True,
) -> Dict[str, Any]:
    """Assign only useful, participant-understandable recommendation phases."""
    matched_count = len(matched)
    urgent_expiring_details = [item for item in expiring_details if item.get("days", 99) <= 4]
    meaningful_missing = [item for item in missing if not is_low_value_missing(item)]
    missing_count = len(meaningful_missing)
    total_count = max(matched_count + missing_count, 1)
    pantry_ratio = matched_count / total_count

    title_role = title_required_protein_role(recipe.get("recipe_name", ""))
    matched_roles = {ingredient_swap_role(item) for item in matched}
    if title_role and title_role not in matched_roles:
        primary_protein_matched = False

    if not primary_protein_matched:
        return {
            "recommendation_phase": "Lower Match",
            "phase_rank": 9,
            "phase_reason": "The recipe's main protein is not available in the pantry.",
        }

    # A complete recipe is always ready to make. Expiration affects its ranking,
    # but does not change the truth that all ingredients are present.
    if missing_count == 0 and matched_count >= 2 and exact_match_percent >= 99:
        if urgent_expiring_details:
            return {
                "recommendation_phase": "Expiring First",
                "phase_rank": 1,
                "phase_reason": "This ready-to-make meal uses pantry items that need attention soon.",
            }
        return {
            "recommendation_phase": "Pantry Match",
            "phase_rank": 2,
            "phase_reason": "This meal can be made with the pantry ingredients already entered.",
        }

    # Use First must still be feasible. Expiration can prioritize a good match;
    # it cannot rescue an unrelated recipe.
    if (
        urgent_expiring_details
        and matched_count >= 2
        and missing_count <= 2
        and pantry_ratio >= 0.70
        and coverage_with_swaps >= 75
    ):
        return {
            "recommendation_phase": "Expiring First",
            "phase_rank": 1,
            "phase_reason": "This feasible meal uses expiring food while requiring very little else.",
        }

    # Almost There means genuinely close, not a recipe with one random match.
    if (
        matched_count >= 2
        and 1 <= missing_count <= 3
        and (pantry_ratio >= 0.60 or coverage_with_swaps >= 70)
    ):
        return {
            "recommendation_phase": "Almost There",
            "phase_rank": 3,
            "phase_reason": "Most of this meal is already in the pantry; only a few meaningful ingredients are missing.",
        }

    return {
        "recommendation_phase": "Lower Match",
        "phase_rank": 9,
        "phase_reason": "This recipe is not feasible enough for the main recommendation list.",
    }


def build_recommendation_explanation(
    matched: List[str],
    missing: List[str],
    expiring_details: List[Dict[str, Any]],
    recipe: Dict[str, Any],
    profile: Optional[Dict[str, Any]],
    phase: Dict[str, Any],
    exact_match_percent: float,
    coverage_with_swaps: float,
    nutrition_fit: Dict[str, Any],
) -> List[str]:
    bullets = []

    if expiring_details:
        expiring_text = ", ".join(
            f"{item['item_name']} ({item['label']})"
            for item in expiring_details[:4]
        )
        bullets.append(f"Uses expiring pantry item(s): {expiring_text}.")

    if matched:
        bullets.append(
            f"Matches {len(matched)} pantry ingredient(s): {', '.join(matched[:6])}."
        )

    if missing:
        bullets.append(
            f"Missing {len(missing)} main ingredient(s): {', '.join(missing[:5])}."
        )
    else:
        bullets.append("No major missing ingredients were found for this recipe.")

    bullets.append(
        f"Pantry match is {exact_match_percent}% and coverage with possible swaps is {coverage_with_swaps}%."
    )

    if nutrition_fit.get("ml_nutrition_fit") is not None:
        bullets.append(
            f"Nutrition Fit contributes {nutrition_fit.get('ml_nutrition_fit')}/15 to the recommendation evidence."
        )
    else:
        bullets.append("Nutrition Fit evidence is shown when enough nutrition data is available.")

    if profile:
        preferred_meals = split_profile_list(profile.get("preferred_meal_type", ""))
        preferred_cuisines = split_profile_list(profile.get("preferred_cuisine", ""))

        if preferred_meals or preferred_cuisines:
            bullets.append("Profile preferences were checked before ranking this meal.")

    bullets.append(phase.get("phase_reason", "This meal was ranked by the Smart Pantry scoring system."))

    return bullets


def build_reason(
    matched,
    missing,
    expiring_items,
    recipe,
    profile=None,
    phase=None,
    exact_match_percent=None,
    coverage_with_swaps_percent=None,
):
    parts = []

    phase_name = (phase or {}).get("recommendation_phase")
    if phase_name:
        parts.append(f"{phase_name}:")
    elif recipe.get("source_type") == "core":
        parts.append("Quick everyday meal:")
    else:
        parts.append("Expanded recipe option:")

    if expiring_items:
        unique_expiring = list(dict.fromkeys([item for item in expiring_items if item]))
        parts.append(f"uses close-to-expiring item(s) first: {', '.join(unique_expiring[:5])}.")

    if matched:
        parts.append(f"matches pantry item(s): {', '.join(matched[:5])}.")

    if missing:
        parts.append(f"missing: {', '.join(missing[:4])}.")
    else:
        parts.append("no major missing ingredients.")

    if exact_match_percent is not None:
        parts.append(f"Pantry match: {exact_match_percent}%.")

    if coverage_with_swaps_percent is not None:
        parts.append(f"Coverage with swaps: {coverage_with_swaps_percent}%.")

    return " ".join(parts)


def score_recipe(recipe: Dict[str, Any], pantry_items: List[Dict[str, Any]], profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Reclassify every candidate (including generated templates) using recipe
    # context instead of trusting raw dataset meal labels.
    classification = classify_recipe_meal_types(recipe)
    recipe = {**recipe, **classification, "meal_type": classification["smart_primary_meal_type"]}
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
            "expiring_details": [],
            "recommendation_phase": "Filtered Out",
            "phase_rank": 99,
            "phase_reason": "Filtered out because it conflicts with saved allergies or foods to avoid.",
            "recommendation_explanation": ["Filtered out because it conflicts with saved allergies or foods to avoid."],
            "source_type": recipe.get("source_type"),
            "source_label": recipe.get("source_label"),
            "why": "Filtered out because it conflicts with saved allergies or foods to avoid.",
            "filtered_out": True,
        }

    recipe_ingredients = recipe.get("ingredients_list", [])
    matched = []
    missing = []
    matched_pantry_items = []

    used_pantry_indexes = set()
    for ingredient in recipe_ingredients:
        matched_item = None
        matched_index = None

        for pantry_index, pantry_item in enumerate(pantry_items):
            if pantry_index in used_pantry_indexes:
                continue
            pantry_name = pantry_item.get("item_name", "")

            if pantry_item_matches_ingredient(pantry_name, ingredient):
                matched_item = pantry_item
                matched_index = pantry_index
                break

        if matched_item:
            matched.append(ingredient)
            matched_pantry_items.append(matched_item)
            used_pantry_indexes.add(matched_index)
        else:
            missing.append(ingredient)

    missing = [item for item in missing if is_real_ingredient(item) and not is_low_value_missing(item)]
    matched = [item for item in matched if is_real_ingredient(item) and not is_low_value_missing(item)]
    recipe_ingredients = [item for item in recipe_ingredients if is_real_ingredient(item) and not is_low_value_missing(item)]

    recipe_protein_roles = {
        ingredient_swap_role(item)
        for item in recipe_ingredients
        if ingredient_swap_role(item) in {"poultry", "red_meat", "seafood", "plant_protein", "egg"}
    }
    matched_protein_roles = {
        ingredient_swap_role(item)
        for item in matched
        if ingredient_swap_role(item) in {"poultry", "red_meat", "seafood", "plant_protein", "egg"}
    }
    primary_protein_matched = not recipe_protein_roles or bool(recipe_protein_roles & matched_protein_roles)

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

    expiring_details = build_expiring_details(matched_pantry_items)
    expiring_items = [item["item_name"] for item in expiring_details]

    everyday_recipe_fit = calculate_everyday_recipe_fit(recipe)
    nutrition_fit = calculate_ml_nutrition_fit(recipe)
    meal_practicality = calculate_meal_practicality(recipe)

    # Smart Score is intentionally separate from pantry-match percentage.
    # A pantry-complete dessert and a pantry-complete urgent dinner should not both equal 100.
    match_score = match_ratio * 36
    matched_count_bonus = min(len(matched) * 2.0, 8)

    expiring_bonus = 0
    for detail in expiring_details:
        item_days = detail.get("days", 99)
        if item_days <= 0:
            expiring_bonus += 12
        elif item_days <= 1:
            expiring_bonus += 10
        elif item_days <= 4:
            expiring_bonus += 6
        elif item_days <= 10:
            expiring_bonus += 2
    expiring_bonus = min(expiring_bonus, 24)

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
        elif cook_time > 60:
            simplicity_bonus -= 6

    source_boost = recipe.get("source_boost", 0)
    profile_boost = preference_boost(recipe, profile)
    missing_penalty = len([item for item in missing if not is_low_value_missing(item)]) * 12
    no_match_penalty = 40 if len(matched) == 0 else 0

    ml_percent = nutrition_fit.get("ml_nutrition_fit_percent")
    nutrition_bonus = round((float(ml_percent) / 100.0) * 8.0, 1) if ml_percent is not None else 0.0

    meal_type = str(recipe.get("meal_type") or "").lower()
    meal_completeness_bonus = 7 if meal_type in {"dinner", "lunch", "breakfast", "quick meal"} else 0
    breakfast_complete_bonus = 3 if meal_type == "breakfast" and len(missing) == 0 else 0
    dessert_main_penalty = 12 if meal_type in {"dessert", "snack"} else 0
    practicality_bonus = round(((meal_practicality - 50.0) / 50.0) * 12.0, 1)
    source_trust_bonus = 4.0 if str(recipe.get("source_type") or "").lower() != "generated" else 0.0

    simplicity_bonus = round(simplicity_bonus * 0.5, 1)
    source_boost = min(float(source_boost or 0), 3.0)
    profile_boost = min(float(profile_boost or 0), 6.0)

    score = (
        match_score + matched_count_bonus + expiring_bonus + simplicity_bonus
        + source_boost + source_trust_bonus + profile_boost + nutrition_bonus
        + meal_completeness_bonus + breakfast_complete_bonus + practicality_bonus
        - missing_penalty - no_match_penalty - dessert_main_penalty
    )

    score = max(0, min(round(score, 1), 100))

    phase = classify_recommendation_phase(
        matched=matched,
        missing=missing,
        expiring_details=expiring_details,
        exact_match_percent=exact_pantry_match_percent,
        coverage_with_swaps=coverage_with_smart_swaps_percent,
        recipe=recipe,
        primary_protein_matched=primary_protein_matched,
    )

    score_breakdown = {
        "pantry_match": round(match_score + matched_count_bonus, 1),
        "expiration_priority": round(expiring_bonus, 1),
        "simplicity": round(simplicity_bonus, 1),
        "data_source": round(source_boost, 1),
        "profile_fit": round(profile_boost, 1),
        "nutrition_fit": round(nutrition_bonus, 1),
        "meal_completeness": round(meal_completeness_bonus + breakfast_complete_bonus, 1),
        "meal_practicality": round(practicality_bonus, 1),
        "source_trust": round(source_trust_bonus, 1),
        "dessert_main_penalty": round(dessert_main_penalty, 1),
        "missing_penalty": round(missing_penalty, 1),
        "no_match_penalty": round(no_match_penalty, 1),
    }

    meaningful_missing_count = len([item for item in missing if not is_low_value_missing(item)])
    feasibility_passed = phase.get("phase_rank", 99) < 9
    feasibility_reason = phase.get("phase_reason")

    explanation = build_recommendation_explanation(
        matched=matched,
        missing=missing,
        expiring_details=expiring_details,
        recipe=recipe,
        profile=profile,
        phase=phase,
        exact_match_percent=exact_pantry_match_percent,
        coverage_with_swaps=coverage_with_smart_swaps_percent,
        nutrition_fit=nutrition_fit,
    )

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
        "meal_practicality_score": meal_practicality,
        "score_breakdown": score_breakdown,
        "matched_ingredients": list(dict.fromkeys(matched)),
        "missing_ingredients": list(dict.fromkeys(missing)),
        "expiring_items": list(dict.fromkeys(expiring_items)),
        "expiring_details": expiring_details,
        "recommendation_phase": phase.get("recommendation_phase"),
        "phase_rank": phase.get("phase_rank"),
        "phase_reason": phase.get("phase_reason"),
        "recommendation_explanation": explanation,
        "source_type": recipe.get("source_type"),
        "source_label": recipe.get("source_label"),
        "recipe_family_key": recipe.get("recipe_family_key"),
        "recipe_quality_score": recipe.get("recipe_quality_score"),
        "meaningful_missing_count": meaningful_missing_count,
        "feasibility_passed": feasibility_passed,
        "feasibility_reason": feasibility_reason,
        "primary_protein_matched": primary_protein_matched,
        "why": build_reason(
            matched,
            missing,
            expiring_items,
            recipe,
            profile,
            phase,
            exact_pantry_match_percent,
            coverage_with_smart_swaps_percent,
        ),
    }


def recommendation_sort_key(item: Dict[str, Any]):
    return (
        item.get("phase_rank", 99),
        -_expiration_priority(item),
        -len(item.get("expiring_items", [])),
        -float(item.get("score", 0) or 0),
        -float(item.get("exact_pantry_match_percent", 0) or 0),
        -float(item.get("coverage_with_smart_swaps_percent", 0) or 0),
    )


def _meal_signature(item: Dict[str, Any]) -> tuple[str, str, str]:
    """Protein + starch + dish style signature for user-perceived variety."""
    ingredients = _recommendation_ingredient_set(item)
    proteins = []
    starches = []
    for ingredient in ingredients:
        role = ingredient_swap_role(ingredient)
        if role in {"poultry", "red_meat", "seafood", "plant_protein", "egg"}:
            proteins.append(role)
        if role in {"rice_grain", "pasta", "bread", "wrap", "potato", "oats"}:
            starches.append(role)
    return (
        sorted(proteins)[0] if proteins else "no_protein",
        sorted(starches)[0] if starches else "no_starch",
        get_dish_style(item.get("recipe_name", ""), list(ingredients)),
    )


def _expiration_priority(item: Dict[str, Any]) -> float:
    value = 0.0
    for detail in item.get("expiring_details", []):
        days = detail.get("days", 99)
        if days <= 0:
            value += 12
        elif days <= 1:
            value += 10
        elif days <= 4:
            value += 6
        elif days <= 10:
            value += 2
    return value


def generate_recommendations(pantry_items: List[Dict[str, Any]], profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Return useful, feasible, varied recommendations instead of a recipe dump."""
    active_pantry = [item for item in pantry_items if pantry_item_is_available(item)]
    if not active_pantry:
        return []

    # Cheap feasibility prefilter before Random Forest scoring. This keeps the
    # full recipe library available without running the ML model thousands of
    # times for recipes that clearly do not fit the pantry.
    pantry_names = [get_pantry_item_name(item) for item in active_pantry]
    candidates = []
    recipe_pool = build_pantry_meal_templates(active_pantry) + load_recipes()
    for recipe in recipe_pool:
        if recipe_contains_avoided_food(recipe, profile):
            continue
        main_ingredients = recipe.get("ingredients_list", [])
        rough_matches = sum(
            1 for ingredient in main_ingredients
            if any(pantry_item_matches_ingredient(name, ingredient) for name in pantry_names)
        )
        rough_total = max(len(main_ingredients), 1)
        rough_ratio = rough_matches / rough_total
        if rough_matches >= 2 and rough_ratio >= 0.50:
            candidates.append((rough_matches, rough_ratio, recipe))

    # Match count comes before ratio. This prevents tiny two-ingredient recipes
    # from crowding out fuller meals such as 6-of-7 ingredient dinners.
    candidates.sort(key=lambda value: (
        -value[0],
        -value[1],
        0 if str(value[2].get("source_type") or "").lower() != "generated" else 1,
        -float(value[2].get("recipe_quality_score", 0) or 0),
    ))

    # Score a broader pool so newly added pantry items can unlock different
    # complete and almost-complete recipes instead of leaving the page unchanged.
    candidate_cap = 700
    scored = [score_recipe(recipe, active_pantry, profile) for _matches, _ratio, recipe in candidates[:candidate_cap]]
    scored = [
        recipe for recipe in scored
        if recipe.get("recipe_name")
        and not recipe.get("filtered_out")
        and recipe.get("feasibility_passed")
        and recipe.get("phase_rank", 99) < 9
        and len(recipe.get("matched_ingredients", [])) >= 2
        and float(recipe.get("exact_pantry_match_percent", 0) or 0) >= 60
    ]

    # Within each useful category, prioritize feasibility, expiration usage, then
    # the transparent Smart Score and recipe quality.
    scored.sort(key=lambda item: (
        item.get("phase_rank", 99),
        -_expiration_priority(item),
        -len(item.get("expiring_items", [])),
        -float(item.get("exact_pantry_match_percent", 0) or 0),
        int(item.get("meaningful_missing_count", 99) or 99),
        -float(item.get("score", 0) or 0),
        0 if str(item.get("source_type") or "").lower() != "generated" else 1,
        -float(item.get("meal_practicality_score", 0) or 0),
        -float(item.get("recipe_quality_score", 0) or 0),
    ))

    scored = prioritize_recommendation_diversity(scored)

    # Build a diverse lead set, then add more distinct feasible choices. The
    # first five stay tightly varied; later results may reuse a protein/starch
    # pattern when the actual recipe is meaningfully different.
    phase_limits = {1: 7, 2: 7, 3: 7}
    phase_counts = {1: 0, 2: 0, 3: 0}
    signature_counts: Dict[tuple[str, str, str], int] = {}
    protein_starch_counts: Dict[tuple[str, str], int] = {}
    style_counts: Dict[str, int] = {}
    meal_type_counts: Dict[str, int] = {}
    selected = []
    result_limit = 15

    for recipe in scored:
        phase = recipe.get("phase_rank", 99)
        if phase not in phase_limits or phase_counts[phase] >= phase_limits[phase]:
            continue

        signature = _meal_signature(recipe)
        protein_starch = signature[:2]
        style = signature[2]
        meal_type = str(recipe.get("meal_type") or "Meal")
        in_lead_set = len(selected) < 5

        if signature_counts.get(signature, 0) >= (1 if in_lead_set else 2):
            continue
        if protein_starch_counts.get(protein_starch, 0) >= (1 if in_lead_set else 3):
            continue
        if in_lead_set and style_counts.get(style, 0) >= 1:
            continue
        if meal_type.lower() in {"dessert", "snack"} and meal_type_counts.get("dessert", 0) >= 2:
            continue
        if any(recommendations_are_too_similar(recipe, existing) for existing in selected):
            continue

        selected.append(recipe)
        phase_counts[phase] += 1
        signature_counts[signature] = signature_counts.get(signature, 0) + 1
        protein_starch_counts[protein_starch] = protein_starch_counts.get(protein_starch, 0) + 1
        style_counts[style] = style_counts.get(style, 0) + 1
        key = "dessert" if meal_type.lower() in {"dessert", "snack"} else meal_type
        meal_type_counts[key] = meal_type_counts.get(key, 0) + 1

        if len(selected) >= result_limit:
            break

    # Fill a short page with the strongest remaining feasible recipes while
    # still blocking true duplicate recipe families.
    if len(selected) < 10:
        for recipe in scored:
            if recipe in selected:
                continue
            phase = recipe.get("phase_rank", 99)
            if phase not in phase_limits or phase_counts[phase] >= phase_limits[phase]:
                continue
            meal_type = str(recipe.get("meal_type") or "Meal")
            if meal_type.lower() in {"dessert", "snack"} and meal_type_counts.get("dessert", 0) >= 2:
                continue
            if any(
                recipe.get("recipe_family_key")
                and recipe.get("recipe_family_key") == existing.get("recipe_family_key")
                for existing in selected
            ):
                continue
            selected.append(recipe)
            phase_counts[phase] += 1
            key = "dessert" if meal_type.lower() in {"dessert", "snack"} else meal_type
            meal_type_counts[key] = meal_type_counts.get(key, 0) + 1
            if len(selected) >= result_limit:
                break

    selected.sort(key=recommendation_sort_key)
    for index, recipe in enumerate(selected):
        urgent = [d for d in recipe.get("expiring_details", []) if d.get("days", 99) <= 4]
        reasons = []
        if urgent:
            reasons.append(f"Uses {len(urgent)} ingredient{'s' if len(urgent) != 1 else ''} expiring soon")
        if not recipe.get("missing_ingredients"):
            reasons.append("No shopping required")
        matched_count = len(recipe.get("matched_ingredients", []))
        if matched_count:
            reasons.append(f"Uses {matched_count} pantry ingredients")
        if recipe.get("cook_time"):
            reasons.append(f"Ready in about {recipe.get('cook_time')} minutes")
        recipe["best_meal_reasons"] = reasons[:4]
        recipe["is_top_recommendation"] = index == 0
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
