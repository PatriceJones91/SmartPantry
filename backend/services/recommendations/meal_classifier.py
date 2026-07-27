from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple


MEAL_TYPES = ("Breakfast", "Lunch", "Dinner", "Snack", "Quick Meal", "Brunch", "Dessert")


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def _has_phrase(text: str, phrase: str) -> bool:
    # Word-boundary aware matching avoids false positives such as "cake" in
    # "pancakes" or "pie" inside another word.
    pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(_has_phrase(text, phrase) for phrase in phrases)


def _token_count(text: str, phrases: Iterable[str]) -> int:
    return sum(1 for phrase in phrases if _has_phrase(text, phrase))


DESSERT_WORDS = {
    "cake", "cupcake", "cookie", "cookies", "brownie", "brownies", "pie", "tart",
    "cheesecake", "pudding", "cobbler", "frosting", "icing", "dessert", "truffle",
    "candy", "fudge", "mousse", "parfait", "sweet roll", "cinnamon roll", "donut", "doughnut",
}
BREAKFAST_WORDS = {
    "breakfast", "omelet", "omelette", "scramble", "scrambled egg", "pancake", "pancakes", "waffle", "waffles",
    "oatmeal", "cereal", "french toast", "hash brown", "breakfast burrito", "breakfast sandwich",
    "egg sandwich", "eggs benedict", "frittata", "quiche", "biscuits and gravy",
}
SNACK_WORDS = {
    "snack", "dip", "chips", "popcorn", "trail mix", "bites", "finger food", "appetizer",
    "deviled eggs", "nachos", "croquette", "pinwheel", "cracker", "party mix",
}
LUNCH_WORDS = {
    "lunch", "sandwich", "wrap", "panini", "sub", "hoagie", "salad", "soup", "chowder",
    "burger", "hamburger", "taco", "quesadilla", "burrito", "rice bowl", "grain bowl",
    "pita", "flatbread", "sloppy joe", "grilled cheese",
}
DINNER_WORDS = {
    "dinner", "casserole", "lasagna", "pasta", "spaghetti", "mac and cheese", "stew", "roast",
    "meatloaf", "pot roast", "curry", "stir fry", "stir-fry", "enchilada", "chili", "skillet",
    "baked chicken", "grilled chicken", "chicken parmesan", "chicken francese", "shrimp", "salmon",
    "catfish", "steak", "lamb chop", "pork chop", "shepherd", "pot pie", "risotto",
}
BRUNCH_WORDS = {
    "brunch", "quiche", "frittata", "eggs benedict", "breakfast casserole", "breakfast strata",
    "avocado toast", "breakfast sandwich",
}

SWEET_INGREDIENTS = {
    "powdered sugar", "confectioners sugar", "frosting", "icing", "chocolate chips", "marshmallow",
    "cake mix", "brownie mix", "caramel", "sprinkles", "cocoa powder",
}
MAIN_PROTEINS = {
    "chicken", "turkey", "beef", "ground beef", "steak", "pork", "ham", "lamb", "shrimp", "salmon",
    "tuna", "fish", "catfish", "cod", "tilapia", "tofu", "beans", "lentils", "chickpeas",
}
STARCHES = {
    "rice", "pasta", "spaghetti", "macaroni", "noodles", "potato", "potatoes", "bread", "tortilla",
    "quinoa", "couscous", "grits",
}


def classify_recipe_meal_types(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Classify a recipe with a second, independent meal-context layer.

    Dataset meal/cuisine/dish labels are treated as weak evidence, not truth. The
    returned fields are safe for UI filtering:
      smart_primary_meal_type
      smart_meal_types
      smart_meal_type_confidence
      smart_meal_type_reason
    """
    name = _text(recipe.get("recipe_name") or recipe.get("name"))
    dataset_meal = _text(recipe.get("meal_type"))
    dish_type = _text(recipe.get("dish_type"))
    ingredients = [_text(v) for v in (recipe.get("ingredients_list") or []) if _text(v)]
    ingredient_text = " ".join(ingredients)
    title_context = name
    metadata_context = f"{dish_type} {dataset_meal}".strip()
    combined = f"{name} {dish_type} {dataset_meal}".strip()
    cook_time = recipe.get("cook_time")
    try:
        cook_minutes = int(float(cook_time)) if cook_time not in (None, "") else None
    except (TypeError, ValueError):
        cook_minutes = None

    scores = {meal: 0.0 for meal in MEAL_TYPES}
    reasons: List[str] = []

    # Strong semantic rules first. These override noisy dataset labels.
    # Strong signals come from the recipe title. Dataset labels are handled
    # separately as weak evidence because they are often noisy.
    dessert_hits = _token_count(title_context, DESSERT_WORDS)
    breakfast_hits = _token_count(title_context, BREAKFAST_WORDS)
    snack_hits = _token_count(title_context, SNACK_WORDS)
    lunch_hits = _token_count(title_context, LUNCH_WORDS)
    dinner_hits = _token_count(title_context, DINNER_WORDS)
    brunch_hits = _token_count(title_context, BRUNCH_WORDS)

    if dessert_hits:
        scores["Dessert"] += 0.86 + min(0.10, dessert_hits * 0.03)
        reasons.append("dessert title/dish signals")
    if breakfast_hits:
        scores["Breakfast"] += 0.80 + min(0.12, breakfast_hits * 0.03)
        scores["Brunch"] += 0.60 if _contains_any(title_context, BRUNCH_WORDS | {"omelet", "omelette", "frittata", "quiche"}) else 0.30
        reasons.append("breakfast title/dish signals")
    if snack_hits:
        scores["Snack"] += 0.72 + min(0.14, snack_hits * 0.03)
        reasons.append("snack/appetizer title/dish signals")
    if lunch_hits:
        scores["Lunch"] += 0.66 + min(0.18, lunch_hits * 0.03)
        reasons.append("lunch-style dish signals")
    if dinner_hits:
        scores["Dinner"] += 0.66 + min(0.18, dinner_hits * 0.03)
        reasons.append("dinner/entrée dish signals")
    if brunch_hits:
        scores["Brunch"] += 0.72 + min(0.12, brunch_hits * 0.03)
        reasons.append("brunch crossover signals")

    # Ingredients add context when titles are generic.
    protein_hits = sum(1 for token in MAIN_PROTEINS if _has_phrase(ingredient_text, token))
    starch_hits = sum(1 for token in STARCHES if _has_phrase(ingredient_text, token))
    sweet_hits = sum(1 for token in SWEET_INGREDIENTS if _has_phrase(ingredient_text, token))

    if protein_hits and starch_hits:
        scores["Lunch"] += 0.24
        scores["Dinner"] += 0.34
        reasons.append("protein + starch meal structure")
    elif protein_hits:
        scores["Lunch"] += 0.14
        scores["Dinner"] += 0.18

    if sweet_hits >= 2:
        scores["Dessert"] += 0.34
        scores["Lunch"] -= 0.18
        scores["Dinner"] -= 0.18
    if "egg" in ingredient_text and not dessert_hits:
        scores["Breakfast"] += 0.13
        scores["Brunch"] += 0.10

    # Dataset metadata is deliberately weak evidence.
    dataset_map = {
        "breakfast": "Breakfast",
        "brunch": "Brunch",
        "lunch": "Lunch",
        "dinner": "Dinner",
        "supper": "Dinner",
        "snack": "Snack",
        "appetizer": "Snack",
        "dessert": "Dessert",
    }
    for key, canonical in dataset_map.items():
        if key in dataset_meal or key in dish_type:
            scores[canonical] += 0.16

    # Quick Meal is an attribute-like meal type; it can overlap with lunch/dinner.
    if cook_minutes is not None and cook_minutes <= 30:
        scores["Quick Meal"] += 0.72 if cook_minutes <= 20 else 0.62
    if _contains_any(combined, {"quick", "easy", "15 minute", "20 minute", "30 minute"}):
        scores["Quick Meal"] += 0.18

    # Hard conflict guards: do not let dessert/snack/breakfast leak into Lunch just
    # because a raw dataset happened to label them that way.
    if dessert_hits or sweet_hits >= 2:
        scores["Lunch"] = min(scores["Lunch"], 0.18)
        scores["Dinner"] = min(scores["Dinner"], 0.18)
        if not breakfast_hits:
            scores["Breakfast"] = min(scores["Breakfast"], 0.30)
    if snack_hits and not lunch_hits and not dinner_hits:
        scores["Lunch"] = min(scores["Lunch"], 0.25)
        scores["Dinner"] = min(scores["Dinner"], 0.20)
    if breakfast_hits and not lunch_hits and not dinner_hits:
        scores["Lunch"] = min(scores["Lunch"], 0.28)
        scores["Dinner"] = min(scores["Dinner"], 0.20)

    # A recognizable lunch/dinner entrée may legitimately belong to both.
    if scores["Lunch"] >= 0.60 and scores["Dinner"] >= 0.60:
        reasons.append("valid lunch/dinner crossover")

    # Clamp and select types using stricter thresholds for contextual filters.
    scores = {key: round(max(0.0, min(1.0, value)), 3) for key, value in scores.items()}
    thresholds = {
        "Breakfast": 0.58,
        "Lunch": 0.58,
        "Dinner": 0.58,
        "Snack": 0.62,
        "Quick Meal": 0.58,
        "Brunch": 0.58,
        "Dessert": 0.62,
    }
    selected = [meal for meal in MEAL_TYPES if scores[meal] >= thresholds[meal]]

    if not selected:
        # Generic savory meals should still land somewhere useful.
        if protein_hits or starch_hits:
            selected = ["Dinner"]
            scores["Dinner"] = max(scores["Dinner"], 0.58)
            reasons.append("generic savory main-meal fallback")
        elif cook_minutes is not None and cook_minutes <= 30:
            selected = ["Quick Meal"]
            scores["Quick Meal"] = max(scores["Quick Meal"], 0.58)
        else:
            selected = ["Dinner"]
            scores["Dinner"] = max(scores["Dinner"], 0.50)

    primary = max(selected, key=lambda meal: scores.get(meal, 0.0))
    return {
        "smart_primary_meal_type": primary,
        "smart_meal_types": selected,
        "smart_meal_type_confidence": scores,
        "smart_meal_type_reason": "; ".join(dict.fromkeys(reasons)) or "recipe context classification",
    }


def recipe_matches_meal_filter(recipe: Dict[str, Any], requested: str) -> bool:
    requested_clean = _text(requested)
    if not requested_clean or requested_clean in {"all", "all meals"}:
        return True

    canonical = {
        "quick": "Quick Meal",
        "quick meal": "Quick Meal",
        "quick meals": "Quick Meal",
        "breakfast": "Breakfast",
        "lunch": "Lunch",
        "dinner": "Dinner",
        "snack": "Snack",
        "snacks": "Snack",
        "brunch": "Brunch",
        "dessert": "Dessert",
        "desserts": "Dessert",
    }.get(requested_clean, requested.title())

    classified = recipe.get("smart_meal_types")
    if not classified:
        classified = classify_recipe_meal_types(recipe)["smart_meal_types"]
    return canonical in classified
