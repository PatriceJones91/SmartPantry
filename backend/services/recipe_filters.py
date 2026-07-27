import re
from difflib import SequenceMatcher

BASIC_PANTRY_ITEMS = {
    "salt", "sea salt", "kosher salt", "table salt", "truffle salt",
    "black pepper", "white pepper", "pepper", "ground pepper",
    "cayenne", "cayenne pepper", "paprika", "smoked paprika",
    "garlic powder", "onion powder", "chili powder", "red pepper flakes",
    "italian seasoning", "seasoning", "seasonings",
    "oil", "olive oil", "vegetable oil", "canola oil", "cooking oil",
    "butter", "water", "ice water",
    "sugar", "brown sugar", "white sugar",
    "flour", "all purpose flour", "cornstarch",
    "baking soda", "baking powder",
    "vanilla", "vanilla extract",
    "vinegar", "white vinegar", "apple cider vinegar",
    "soy sauce", "hot sauce", "mustard", "ketchup", "mayonnaise",
}

CONDIMENT_WORDS = {
    "salt", "pepper", "seasoning", "spice", "spices", "powder",
    "sauce", "oil", "vinegar", "mustard", "ketchup", "mayo",
    "mayonnaise", "marinade", "dressing", "rub", "paste"
}

BAD_RECIPE_WORDS = {
    "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten",
    "pet", "pets", "bird", "hamster", "horse", "treats for dogs",
    "dog food", "cat food", "kibble",
    "slime", "playdough", "soap", "lotion", "shampoo",
    "cleaner", "detergent", "paint", "glue",
}

BAD_TITLE_PATTERNS = [
    r"\bdog\b",
    r"\bdogs\b",
    r"\bpuppy\b",
    r"\bcat\b",
    r"\bpet\b",
    r"\bkibble\b",
    r"\btreats?\s+for\s+dogs?\b",
    r"\bhomemade\s+dog\s+food\b",
    r"\bcat\s+food\b",
]

DUPLICATE_FILLER_WORDS = {
    "easy", "simple", "quick", "best", "homemade", "classic", "healthy",
    "creamy", "crispy", "baked", "grilled", "fried", "slow", "cooker",
    "instant", "pot", "one", "pan", "skillet", "copycat", "ultimate",
    "perfect", "delicious", "amazing", "favorite", "style", "with",
    "and", "the", "a", "an", "recipe"
}

MEAL_WORDS = {
    "chicken", "beef", "turkey", "fish", "salmon", "tuna", "shrimp",
    "pasta", "rice", "soup", "stew", "casserole", "salad", "sandwich",
    "wrap", "quesadilla", "taco", "burrito", "bowl", "omelet", "eggs",
    "potato", "beans", "chili", "meatloaf", "burger", "noodles",
    "stir fry", "roast", "bake", "dinner", "lunch", "breakfast"
}


def clean_text(value):
    return str(value or "").strip().lower()


def split_ingredients(value):
    if value is None:
        return []

    if isinstance(value, list):
        raw_items = value
    else:
        text = str(value)
        raw_items = re.split(r",|\||;|\n", text)

    cleaned = []
    for item in raw_items:
        item = clean_text(item)
        item = re.sub(r"\([^)]*\)", " ", item)
        item = re.sub(r"[^a-z0-9\s-]", " ", item)
        item = re.sub(r"\s+", " ", item).strip()

        if item:
            cleaned.append(item)

    return cleaned


def normalize_ingredient_name(value):
    text = clean_text(value)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\b\d+(\.\d+)?\b", " ", text)
    text = re.sub(
        r"\b(cups?|tbsp|tablespoons?|tsp|teaspoons?|oz|ounces?|lb|lbs|pounds?|grams?|g|kg|ml|liters?|cloves?|pieces?|slices?)\b",
        " ",
        text,
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_basic_pantry_item(value):
    item = normalize_ingredient_name(value)

    if not item:
        return False

    if item in BASIC_PANTRY_ITEMS:
        return True

    words = set(item.split())

    if item in BASIC_PANTRY_ITEMS:
        return True

    if words and words.issubset(BASIC_PANTRY_ITEMS):
        return True

    for basic in BASIC_PANTRY_ITEMS:
        if item == basic:
            return True

    return False


def remove_basic_pantry_from_missing(missing_items):
    cleaned = []
    for item in missing_items or []:
        if not is_basic_pantry_item(item):
            cleaned.append(item)
    return cleaned


def title_is_bad(title):
    text = clean_text(title)

    if not text:
        return True

    if len(text) < 4:
        return True

    if len(text) > 90:
        return True

    for pattern in BAD_TITLE_PATTERNS:
        if re.search(pattern, text):
            return True

    if any(word in text for word in BAD_RECIPE_WORDS):
        return True

    # Block recipes that are only condiment/sauce/seasoning items.
    title_words = set(re.sub(r"[^a-z0-9\s]", " ", text).split())
    if title_words and title_words.issubset(CONDIMENT_WORDS):
        return True

    # Block titles like "Truffle Salt", "Garlic Powder", "Pepper Sauce"
    if len(title_words) <= 3 and title_words.intersection(CONDIMENT_WORDS):
        if not title_words.intersection(MEAL_WORDS):
            return True

    # Keep real meals, block weird non-meal records.
    has_meal_word = any(word in text for word in MEAL_WORDS)
    if not has_meal_word and len(title_words) <= 2:
        return True

    return False


def title_fingerprint(title):
    text = clean_text(title)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = [w for w in text.split() if w not in DUPLICATE_FILLER_WORDS]

    # Sort words so "Chicken Shrimp Quesadilla" and
    # "Quesadilla with Chicken and Shrimp" group together.
    return " ".join(sorted(words))


def ingredient_signature(ingredients):
    items = []
    for item in split_ingredients(ingredients):
        normalized = normalize_ingredient_name(item)
        if normalized and not is_basic_pantry_item(normalized):
            items.append(normalized)

    return set(items)


def recipes_are_duplicates(recipe_a, recipe_b):
    title_a = recipe_a.get("title") or recipe_a.get("meal_name") or recipe_a.get("name") or ""
    title_b = recipe_b.get("title") or recipe_b.get("meal_name") or recipe_b.get("name") or ""

    fp_a = title_fingerprint(title_a)
    fp_b = title_fingerprint(title_b)

    if fp_a and fp_b and fp_a == fp_b:
        return True

    title_similarity = SequenceMatcher(None, clean_text(title_a), clean_text(title_b)).ratio()

    ingredients_a = ingredient_signature(recipe_a.get("ingredients"))
    ingredients_b = ingredient_signature(recipe_b.get("ingredients"))

    if ingredients_a and ingredients_b:
        overlap = len(ingredients_a.intersection(ingredients_b)) / max(1, len(ingredients_a.union(ingredients_b)))
    else:
        overlap = 0

    return title_similarity >= 0.82 and overlap >= 0.65


def filter_recipe_candidates(recipes, max_results=40):
    filtered = []

    for recipe in recipes or []:
        title = recipe.get("title") or recipe.get("meal_name") or recipe.get("name") or ""

        if title_is_bad(title):
            continue

        ingredients = split_ingredients(recipe.get("ingredients"))
        real_ingredients = [i for i in ingredients if not is_basic_pantry_item(i)]

        # Do not keep recipes that are basically only condiments.
        if len(real_ingredients) < 2:
            continue

        duplicate = False
        for existing in filtered:
            if recipes_are_duplicates(recipe, existing):
                duplicate = True
                break

        if duplicate:
            continue

        filtered.append(recipe)

        if len(filtered) >= max_results:
            break

    return filtered
