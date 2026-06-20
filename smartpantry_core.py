import streamlit as st
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import ast
import re
import json

try:
    import joblib
except ImportError:
    joblib = None

from database_supabase import (
    init_db,
    register_user,
    login_user,
    update_user_profile,
    get_user_profile,
    add_pantry_item,
    update_pantry_item,
    get_user_pantry,
    reduce_pantry_item_quantity,
    mark_item_used,
    save_recommendation_log,
    get_user_recommendation_logs,
    mark_recommendation_used,
    save_survey,
    has_completed_survey,
    get_all_users,
    get_all_pantry_items,
    get_all_recommendation_logs,
    get_all_ingredient_usage,
    get_all_surveys,
)



st.markdown(
    """
    <style>
    :root {
        --sp-green: #1f7a3f;
        --sp-dark-green: #14532d;
        --sp-orange: #f97316;
        --sp-soft-orange: #fff0df;
        --sp-blue: #2563eb;
        --sp-baby-blue: #d9f2ff;
        --sp-cream: #fffaf2;
        --sp-card: #ffffff;
    }

    .stApp {
        background: linear-gradient(135deg, #eef8ff 0%, #d9f2ff 28%, #f6fff3 68%, #e8ffe8 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #14532d 0%, #1f7a3f 70%, #2563eb 100%);
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    h1, h2, h3 {
        color: var(--sp-dark-green);
    }

    div.stButton > button,
    div.stDownloadButton > button {
        background-color: var(--sp-green);
        color: white;
        border-radius: 12px;
        border: 2px solid var(--sp-green);
        font-weight: 700;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background-color: var(--sp-orange);
        color: white;
        border: 2px solid var(--sp-orange);
    }

    .smart-card {
        background: var(--sp-card);
        border: 1px solid #dcebd6;
        border-left: 7px solid var(--sp-green);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
    }

    .smart-card-orange {
        border-left-color: var(--sp-orange);
    }

    .smart-card-blue {
        border-left-color: var(--sp-blue);
    }

    .alert-red {
        background: #ffe5e5;
        border: 2px solid #dc2626;
        border-left: 10px solid #dc2626;
        color: #7f1d1d;
        border-radius: 16px;
        padding: 14px;
        margin-bottom: 12px;
        font-weight: 700;
    }

    .alert-orange {
        background: #ffedd5;
        border: 2px solid #f97316;
        border-left: 10px solid #f97316;
        color: #7c2d12;
        border-radius: 16px;
        padding: 14px;
        margin-bottom: 12px;
        font-weight: 700;
    }

    .alert-blue {
        background: #d9f2ff;
        border: 2px solid #60a5fa;
        border-left: 10px solid #60a5fa;
        color: #0f3f66;
        border-radius: 16px;
        padding: 14px;
        margin-bottom: 12px;
        font-weight: 700;
    }

    .small-note {
        color: #355c3a;
        font-size: 0.95rem;
    }

    .friendly-note {
        background: #ffffff;
        border: 1px solid #dcebd6;
        border-left: 7px solid var(--sp-green);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
        font-size: 1.05rem;
        line-height: 1.7;
    }

    .page-logo {
        text-align: center;
        margin-bottom: 10px;
    }

    .page-logo img {
        max-width: 260px;
        border-radius: 18px;
    }

    .history-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
        border: 1px solid #e5e7eb;
    }

    .history-green { border-left: 10px solid #22c55e; }
    .history-purple { border-left: 10px solid #a855f7; }
    .history-brown { border-left: 10px solid #a16207; }
    .history-red { border-left: 10px solid #ef4444; }
    .history-blue { border-left: 10px solid #3b82f6; }
    .history-gray { border-left: 10px solid #9ca3af; }

    .history-title {
        font-weight: 800;
        font-size: 1.05rem;
        color: #14532d;
        margin-bottom: 4px;
    }

    .history-item {
        font-size: 0.98rem;
        color: #374151;
    }

    .grocery-list-card {
        background: #ffffff;
        border: 1px solid #dcebd6;
        border-left: 7px solid #1f7a3f;
        border-radius: 18px;
        padding: 18px 22px;
        margin-bottom: 16px;
        box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
    }

    .grocery-list-card h4 {
        margin-top: 0;
        margin-bottom: 8px;
        color: #14532d;
    }

    .grocery-list-card ul {
        margin-top: 6px;
        margin-bottom: 4px;
        padding-left: 24px;
    }

    .grocery-list-card li {
        margin-bottom: 6px;
        font-weight: 650;
        color: #1f2937;
    }

    .grocery-list-high { border-left-color: #ef4444; }
    .grocery-list-medium { border-left-color: #f97316; }
    .grocery-list-low { border-left-color: #2563eb; }
    .grocery-list-manual { border-left-color: #a855f7; }

    .recommendation-legend-board {
        background: #ffffff;
        border: 1px solid #dcebd6;
        border-radius: 18px;
        padding: 16px 18px;
        margin-bottom: 16px;
        box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
    }

    .recommendation-legend-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 10px;
        margin-top: 10px;
    }

    .recommendation-legend-item {
        border-radius: 14px;
        padding: 12px;
        font-weight: 700;
        border: 1px solid #e5e7eb;
    }

    .legend-green { background: #dcfce7; color: #14532d; border-left: 8px solid #22c55e; }
    .legend-blue { background: #dbeafe; color: #1e3a8a; border-left: 8px solid #3b82f6; }
    .legend-orange { background: #ffedd5; color: #7c2d12; border-left: 8px solid #f97316; }
    .legend-purple { background: #f3e8ff; color: #581c87; border-left: 8px solid #a855f7; }

    .recommendation-section-note {
        background: #ffffff;
        border-radius: 16px;
        padding: 14px 16px;
        margin-bottom: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 12px rgba(20, 83, 45, 0.06);
        font-weight: 650;
    }

    .section-green { border-left: 10px solid #22c55e; }
    .section-blue { border-left: 10px solid #3b82f6; }
    .section-orange { border-left: 10px solid #f97316; }
    .section-purple { border-left: 10px solid #a855f7; }
    </style>
    """,
    unsafe_allow_html=True,
)


APP_DIR = Path(__file__).resolve().parent
LOGO_PATHS = [
    APP_DIR / "SmartPantry_logo.png",
    APP_DIR / "assets" / "SmartPantry_logo.png",
    APP_DIR / "data" / "SmartPantry_logo.png",
]
PROJECT_DIR = APP_DIR.parent if APP_DIR.name.lower() == "app" else APP_DIR

DATASET_PATHS = [
    APP_DIR / "data" / "smart_pantry_recipes_clean.csv",
]

BARCODE_LOOKUP_PATHS = [
    APP_DIR / "data" / "barcode_lookup.csv",
    PROJECT_DIR / "app" / "data" / "barcode_lookup.csv",
    PROJECT_DIR / "data" / "barcode_lookup.csv",
]
MODEL_PATHS = [
    APP_DIR / "ml" / "recommendation_model.pkl",
    PROJECT_DIR / "ml" / "recommendation_model.pkl",
    APP_DIR / "recommendation_model.pkl",
    PROJECT_DIR / "recommendation_model.pkl",
]
MAX_RECIPES_FOR_APP = 400


@st.cache_data(ttl=30, show_spinner=False)
def get_user_pantry_cached(user_id):
    return get_user_pantry(user_id)


@st.cache_data(ttl=30, show_spinner=False)
def get_user_profile_cached(user_id):
    return get_user_profile(user_id)


@st.cache_data(ttl=30, show_spinner=False)
def has_completed_survey_cached(user_id, survey_type):
    return has_completed_survey(user_id, survey_type)


@st.cache_data(ttl=30, show_spinner=False)
def get_user_recommendation_logs_cached(user_id):
    return get_user_recommendation_logs(user_id)


@st.cache_data(ttl=60, show_spinner=False)
def load_admin_data_cached():
    return {
        "users": get_all_users(),
        "pantry": get_all_pantry_items(),
        "recommendations": get_all_recommendation_logs(),
        "usage": get_all_ingredient_usage(),
        "surveys": get_all_surveys(),
    }


def clear_user_cache(user_id=None):
    """Clear cached user/admin data after a write so the screen refreshes with current records."""
    cached_functions = [
        get_user_pantry_cached,
        get_user_profile_cached,
        has_completed_survey_cached,
        get_user_recommendation_logs_cached,
        load_admin_data_cached,
    ]
    for cached_function in cached_functions:
        try:
            cached_function.clear()
        except Exception:
            pass


def get_logo_path():
    for path in LOGO_PATHS:
        if path.exists():
            return str(path)
    return None


def show_logo(width=230):
    logo_path = get_logo_path()
    if logo_path:
        st.image(logo_path, width=width)


def show_page_logo():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        show_logo(width=260)


def count_words(text):
    return len(str(text).split())


def validate_250_words(text):
    words = count_words(text)
    if words > 250:
        return False, f"Please keep feedback at 250 words or less. Current count: {words} words."
    return True, f"{words}/250 words"


CATEGORY_DISPLAY = {
    "Grain": "🟣 Grain",
    "Protein": "🔴 Protein",
    "Dairy": "🟡 Dairy",
    "Fruit": "🩷 Fruit",
    "Vegetable": "🔵 Vegetable",
    "Canned Goods": "🟢 Canned Goods",
    "Frozen": "🧊 Frozen",
    "Snack": "🟠 Snack",
    "Condiment": "🟤 Condiment",
    "Tea & Coffee": "⚫ Tea & Coffee",
    "Other": "⚪ Other",
}

CATEGORY_OPTIONS = list(CATEGORY_DISPLAY.keys())
CATEGORY_DISPLAY_OPTIONS = list(CATEGORY_DISPLAY.values())
CATEGORY_REVERSE_DISPLAY = {display: clean for clean, display in CATEGORY_DISPLAY.items()}


def get_category_display(category):
    category = str(category or "Other").strip()
    return CATEGORY_DISPLAY.get(category, f"⚪ {category}")


def clean_category_value(category_value):
    category_value = str(category_value or "Other").strip()
    if category_value in CATEGORY_REVERSE_DISPLAY:
        return CATEGORY_REVERSE_DISPLAY[category_value]
    for clean_category, display_category in CATEGORY_DISPLAY.items():
        if category_value == clean_category or category_value.endswith(clean_category):
            return clean_category
    return category_value.replace("🟣", "").replace("🔴", "").replace("🟡", "").replace("🩷", "").replace("🔵", "").replace("🟢", "").replace("🧊", "").replace("🟠", "").replace("🟤", "").replace("⚫", "").replace("⚪", "").strip() or "Other"


def apply_category_style(df):
    category_colors = {
        "Protein": "background-color: #ffe5e5",
        "Dairy": "background-color: #fff7cc",
        "Grain": "background-color: #eadcff",
        "Fruit": "background-color: #ffd6e7",
        "Vegetable": "background-color: #d9f2ff",
        "Canned Goods": "background-color: #e8ffe8",
        "Frozen": "background-color: #dbeafe",
        "Snack": "background-color: #fff0df",
        "Condiment": "background-color: #fef3c7",
        "Tea & Coffee": "background-color: #eeeeee",
        "Other": "background-color: #f5f5f5",
    }

    def style_row(row):
        color = category_colors.get(clean_category_value(row.get("category", "Other")), "")
        return [color] * len(row)

    return df.style.apply(style_row, axis=1)


def normalize_column_name(name):
    return str(name).strip().lower().replace(" ", "_")


def find_column(columns, possible_names):
    normalized = {normalize_column_name(col): col for col in columns}
    for name in possible_names:
        key = normalize_column_name(name)
        if key in normalized:
            return normalized[key]
    return None


def clean_ingredient_token(value):
    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9\s\-]", "", value)
    value = value.replace("fresh ", "").replace("dried ", "")
    value = value.replace("boneless ", "").replace("skinless ", "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


OPTIONAL_STAPLES = {
    "salt", "pepper", "black pepper", "white pepper", "garlic powder", "onion powder",
    "paprika", "smoked paprika", "cayenne", "red pepper flakes", "chili powder",
    "seasoning", "seasoning salt", "italian seasoning", "taco seasoning",
    "cinnamon", "nutmeg", "oregano", "basil", "thyme", "rosemary", "parsley",
    "cilantro", "cumin", "bay leaf", "bay leaves", "water", "ice", "cooking spray",
    "nonstick spray", "oil", "vegetable oil", "olive oil", "canola oil",
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
    "american", "italian", "mexican", "southern", "mediterranean", "asian", "chinese",
    "japanese", "thai", "indian", "middle eastern", "caribbean", "french"
}

CUISINE_TYPE_OPTIONS = [
    "American", "Italian", "Mexican", "Southern", "Mediterranean", "Asian",
    "Chinese", "Japanese", "Thai", "Indian", "Middle Eastern", "Caribbean",
    "French", "Vegetarian", "Seafood", "No Preference"
]

UNWANTED_DISH_TERMS = {
    "cocktail", "cocktails", "drink", "drinks", "beverage", "sauce", "marinade",
    "dressing", "dip", "condiment", "seasoning", "spice mix", "syrup"
}

BLOG_NAME_PATTERNS = [
    r"^eat for (?:eight|8) bucks:\s*",
    r"^\$?\d+\s*(?:dollar|buck)s?:\s*",
    r"\bgrandma(?:'s)?\b", r"\bgrandmother(?:'s)?\b", r"\bmom(?:'s)?\b",
    r"\bmama(?:'s)?\b", r"\bdad(?:'s)?\b", r"\baunt(?:ie's|'s)?\b",
    r"\bnana(?:'s)?\b", r"\bcopycat\b", r"\bfamous\b", r"\baward winning\b",
    r"\bbest ever\b", r"\bworld's best\b", r"\brestaurant style\b",
]


def normalize_plural_ingredient(value):
    value = clean_ingredient_token(value)
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


def safe_number(value, default=0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def categorize_meal_type(name):
    name = str(name).lower()
    breakfast_terms = ["breakfast", "pancake", "waffle", "oat", "egg", "toast", "smoothie", "muffin"]
    snack_terms = ["snack", "chips", "popcorn", "bar"]
    lunch_terms = ["sandwich", "wrap", "salad", "soup", "bowl", "quesadilla"]

    if any(term in name for term in breakfast_terms):
        return "Breakfast"
    if any(term in name for term in snack_terms):
        return "Snack"
    if any(term in name for term in lunch_terms):
        return "Lunch"
    return "Dinner"


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

    common_count = sum(1 for item in ingredients if item in COMMON_PANTRY_INGREDIENTS or any(item in common or common in item for common in COMMON_PANTRY_INGREDIENTS))
    if ingredient_count:
        common_ratio = common_count / ingredient_count
        score += int(common_ratio * 25)

    if any(cuisine in cuisine_text for cuisine in PRACTICAL_CUISINES):
        score += 8

    if any(term in name or term in meal_text for term in ["pasta", "spaghetti", "rice", "bowl", "sandwich", "wrap", "soup", "salad", "casserole", "taco", "quesadilla", "toast", "skillet", "bake"]):
        score += 8

    if any(term in name or term in meal_text for term in UNWANTED_DISH_TERMS):
        score -= 35

    if len(recipe_name) > 90:
        score -= 8

    if re.search(r"\b(test|mock|unknown)\b", name):
        score -= 20

    return max(0, min(score, 100))



def parse_dataset_list(value):
    """Parse list-like dataset fields, including Python lists, JSON lists, and comma-separated text."""
    if pd.isna(value):
        return []

    text = str(value).strip()
    if not text:
        return []

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)):
            cleaned = []
            for item in parsed:
                if isinstance(item, dict):
                    item = item.get("food") or item.get("text") or item.get("label") or ""
                token = clean_ingredient_token(item)
                if token:
                    cleaned.append(token)
            return cleaned
        if isinstance(parsed, dict):
            return [clean_ingredient_token(v) for v in parsed.values() if clean_ingredient_token(v)]
    except Exception:
        pass

    if text.startswith("c(") and text.endswith(")"):
        text = text[2:-1]

    text = text.replace('"', "").replace("'", "")
    parts = re.split(r",|;|\|", text)
    return [clean_ingredient_token(part) for part in parts if clean_ingredient_token(part)]


def parse_jsonish(value):
    """Parse JSON or Python-dict-looking text safely. Returns dict/list/string."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return ast.literal_eval(text)
    except Exception:
        return None


def simplify_ingredient_text(text):
    """Turn recipe ingredient lines into cleaner pantry-friendly ingredient names."""
    text = str(text).lower().strip()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\b\d+(?:/\d+)?\b", " ", text)
    text = re.sub(r"\b(cup|cups|tablespoon|tablespoons|tbsp|teaspoon|teaspoons|tsp|ounce|ounces|oz|pound|pounds|lb|lbs|gram|grams|g|kg|ml|liter|liters|pinch|dash|can|cans|package|packages|slice|slices|piece|pieces|serving|servings)\b", " ", text)
    text = re.sub(r"\b(chopped|diced|minced|sliced|fresh|dried|boneless|skinless|cooked|uncooked|large|small|medium|optional|divided|to taste)\b", " ", text)
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    if len(words) > 4:
        text = " ".join(words[-4:])
    return clean_ingredient_token(text)


def extract_ingredients_from_row(row, ingredient_lines_col=None, ingredients_col=None, main_ingredients_col=None):
    """Use the best available dataset column to create a clean ingredient list.

    The cleaned Smart Pantry CSV already has a main_ingredients column, so the app should
    use that first. If that column is not available, the app falls back to the original
    ingredients or ingredient_lines fields.
    """
    ingredients = []

    if main_ingredients_col:
        parsed = parse_jsonish(row.get(main_ingredients_col, ""))
        if isinstance(parsed, list):
            ingredients = [clean_ingredient_token(item) for item in parsed if clean_ingredient_token(item)]

    if not ingredients and ingredients_col:
        parsed = parse_jsonish(row.get(ingredients_col, ""))
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    food = item.get("food") or item.get("label") or item.get("text") or ""
                    token = clean_ingredient_token(food)
                    if token:
                        ingredients.append(token)
                else:
                    token = simplify_ingredient_text(item)
                    if token:
                        ingredients.append(token)

    if not ingredients and ingredient_lines_col:
        parsed_lines = parse_dataset_list(row.get(ingredient_lines_col, ""))
        ingredients = [simplify_ingredient_text(line) for line in parsed_lines if simplify_ingredient_text(line)]

    cleaned = []
    seen = set()
    for ingredient in ingredients:
        ingredient = normalize_plural_ingredient(ingredient)
        if ingredient and ingredient not in seen and len(ingredient) > 1:
            cleaned.append(ingredient)
            seen.add(ingredient)
    return cleaned


def extract_nutrient_value(row, simple_col=None, nutrients_col=None, digest_col=None, nutrient_key=""):
    """Pull calories/protein/carbs/fat from simple columns or nested nutrition columns."""
    if simple_col:
        value = safe_number(row.get(simple_col, 0), 0)
        if value:
            return value

    if nutrients_col:
        nutrients = parse_jsonish(row.get(nutrients_col, ""))
        if isinstance(nutrients, dict):
            item = nutrients.get(nutrient_key)
            if isinstance(item, dict):
                return safe_number(item.get("quantity", 0), 0)

    if digest_col:
        digest = parse_jsonish(row.get(digest_col, ""))
        if isinstance(digest, list):
            for item in digest:
                if isinstance(item, dict) and item.get("tag") == nutrient_key:
                    return safe_number(item.get("total", item.get("daily", 0)), 0)

    return 0


def normalize_meal_type_value(value, recipe_name=""):
    parsed = parse_jsonish(value)
    if isinstance(parsed, list) and parsed:
        value = parsed[0]
    value = str(value or "").strip().title()
    if value in ["Breakfast", "Lunch", "Dinner", "Snack"]:
        return value
    if "Snack" in value:
        return "Snack"
    if "Breakfast" in value or "Brunch" in value:
        return "Breakfast"
    if "Lunch" in value:
        return "Lunch"
    if "Dinner" in value or "Main" in value:
        return "Dinner"
    return categorize_meal_type(recipe_name)


def normalize_cook_time(row, cook_col=None, total_time_col=None):
    value = None
    if cook_col and str(row.get(cook_col, "")).strip():
        value = row.get(cook_col)
    elif total_time_col and str(row.get(total_time_col, "")).strip():
        value = row.get(total_time_col)

    if value is None or pd.isna(value):
        return "Not listed"
    try:
        minutes = float(value)
        if minutes <= 0:
            return "Not listed"
        if minutes.is_integer():
            return f"{int(minutes)} minutes"
        return f"{round(minutes, 1)} minutes"
    except Exception:
        return str(value)


def build_instruction_text(row, instruction_col=None, url_col=None):
    if instruction_col:
        raw = row.get(instruction_col, "")
        parsed = parse_jsonish(raw)
        if isinstance(parsed, list):
            steps = [str(step).strip() for step in parsed if str(step).strip()]
            if steps:
                return " ".join(steps[:5])
        if str(raw).strip() and str(raw).strip().lower() != "nan":
            return str(raw).strip()

    if url_col and str(row.get(url_col, "")).strip():
        return f"Instructions are available from the original recipe source: {row.get(url_col)}"

    return "Follow standard cooking steps for this meal."


@st.cache_data(show_spinner=False)
def load_recipes_from_dataset():
    dataset_path = None
    for path in DATASET_PATHS:
        if path.exists():
            dataset_path = path
            break

    if dataset_path is None:
        return None

    try:
        header_df = pd.read_csv(dataset_path, nrows=0)
        columns = list(header_df.columns)
    except Exception as exc:
        st.warning(f"Recipe dataset could not be read: {exc}")
        return None

    name_col = find_column(columns, ["clean_recipe_name", "recipe_name", "name", "Name", "RecipeName"])
    ingredient_lines_col = find_column(columns, ["ingredient_lines", "ingredientLines", "RecipeIngredientParts", "ingredients_list"])
    ingredients_col = find_column(columns, ["ingredients", "recipeingredientparts", "RecipeIngredientParts", "ingredient_parts"])
    main_ingredients_col = find_column(columns, ["main_ingredients", "mainIngredients", "clean_ingredients"])
    instruction_col = find_column(columns, ["instructions", "recipeinstructions", "RecipeInstructions", "directions", "instruction"])
    url_col = find_column(columns, ["url", "source_url", "recipe_url"])
    meal_type_col = find_column(columns, ["meal_type", "meal", "category"])
    dish_type_col = find_column(columns, ["dish_type", "dish"])
    cuisine_col = find_column(columns, ["cuisine_type", "cuisine"])
    calories_col = find_column(columns, ["calories", "Calories"])
    protein_col = find_column(columns, ["protein", "ProteinContent", "protein_content"])
    carbs_col = find_column(columns, ["carbs", "CarbohydrateContent", "carbohydrate_content"])
    fat_col = find_column(columns, ["fat", "FatContent", "fat_content"])
    nutrients_col = find_column(columns, ["total_nutrients", "totalNutrients"])
    digest_col = find_column(columns, ["digest"])
    cook_col = find_column(columns, ["cook_time", "CookTime", "total_time", "TotalTime"])
    servings_col = find_column(columns, ["servings", "yield"])
    health_labels_col = find_column(columns, ["health_labels", "healthLabels"])
    diet_labels_col = find_column(columns, ["diet_labels", "dietLabels"])
    cautions_col = find_column(columns, ["cautions"])

    if name_col is None or (main_ingredients_col is None and ingredient_lines_col is None and ingredients_col is None):
        st.warning("Recipe dataset loaded, but recipe name or ingredient columns were not found. Using built-in sample recipes instead.")
        return None

    usecols = [
        name_col, main_ingredients_col, ingredient_lines_col, ingredients_col, instruction_col, url_col,
        meal_type_col, dish_type_col, cuisine_col, calories_col, protein_col,
        carbs_col, fat_col, nutrients_col, digest_col, cook_col, servings_col,
        health_labels_col, diet_labels_col, cautions_col,
    ]
    usecols = [col for col in usecols if col]

    try:
        df = pd.read_csv(dataset_path, usecols=usecols, nrows=MAX_RECIPES_FOR_APP, low_memory=False)
    except Exception as exc:
        st.warning(f"Recipe dataset could not be loaded: {exc}")
        return None

    recipes = []
    seen_names = set()

    for _, row in df.iterrows():
        original_name = str(row.get(name_col, "Recipe")).strip()
        if not original_name or original_name.lower() == "nan":
            continue

        display_name = clean_recipe_display_name(original_name)
        normalized_name_key = normalize_column_name(display_name)
        if normalized_name_key in seen_names:
            continue

        raw_ingredients = extract_ingredients_from_row(row, ingredient_lines_col, ingredients_col, main_ingredients_col)
        main_ingredients = get_main_recipe_ingredients(raw_ingredients)
        if len(main_ingredients) < 2 or len(main_ingredients) > 10:
            continue

        meal_type_source = row.get(meal_type_col, "") if meal_type_col else row.get(dish_type_col, "") if dish_type_col else ""
        meal_type = normalize_meal_type_value(meal_type_source, display_name)
        dish_type = str(row.get(dish_type_col, "")) if dish_type_col else ""
        cuisine_type = str(row.get(cuisine_col, "Not listed")) if cuisine_col else "Not listed"

        recipe_quality_score = calculate_recipe_quality_score(
            display_name,
            main_ingredients,
            cuisine=cuisine_type,
            meal_type=meal_type,
            dish_type=dish_type,
        )

        # Keep the dataset useful without being too strict. Lower-scoring recipes are still allowed
        # if they have a clear name and a reasonable number of main ingredients.
        if recipe_quality_score < 40:
            continue

        calories_total = safe_number(row.get(calories_col, 0), 0) if calories_col else 0
        protein_total = extract_nutrient_value(row, protein_col, nutrients_col, digest_col, "PROCNT")
        carbs_total = extract_nutrient_value(row, carbs_col, nutrients_col, digest_col, "CHOCDF")
        fat_total = extract_nutrient_value(row, fat_col, nutrients_col, digest_col, "FAT")

        instructions = build_instruction_text(row, instruction_col, url_col)
        cook_time = normalize_cook_time(row, cook_col, None)
        servings = safe_number(row.get(servings_col, 1), 1) if servings_col else 1
        if servings <= 0:
            servings = 1

        calories = calories_total / servings if calories_total else 0
        protein = protein_total / servings if protein_total else 0
        carbs = carbs_total / servings if carbs_total else 0
        fat = fat_total / servings if fat_total else 0

        amounts = {ingredient: 1 for ingredient in main_ingredients}
        units = {ingredient: "serving" for ingredient in main_ingredients}

        recipes.append(
            {
                "name": display_name,
                "original_name": original_name,
                "meal_type": meal_type,
                "ingredients": main_ingredients,
                "full_ingredients": raw_ingredients,
                "amounts": amounts,
                "units": units,
                "calories": int(round(calories)) if calories else 0,
                "protein": round(protein, 1),
                "carbs": round(carbs, 1),
                "fat": round(fat, 1),
                "cook_time": cook_time,
                "instructions": instructions,
                "servings": int(round(servings)),
                "source": dataset_path.name,
                "cuisine_type": cuisine_type,
                "dish_type": dish_type,
                "health_labels": str(row.get(health_labels_col, "")) if health_labels_col else "",
                "diet_labels": str(row.get(diet_labels_col, "")) if diet_labels_col else "",
                "cautions": str(row.get(cautions_col, "")) if cautions_col else "",
                "recipe_quality_score": recipe_quality_score,
            }
        )
        seen_names.add(normalized_name_key)

        if len(recipes) >= MAX_RECIPES_FOR_APP:
            break

    recipes = sorted(recipes, key=lambda item: item.get("recipe_quality_score", 0), reverse=True)
    return recipes or None


@st.cache_resource(show_spinner=False)
def load_recommendation_model():
    if joblib is None:
        return None

    for path in MODEL_PATHS:
        if path.exists():
            try:
                return joblib.load(path)
            except Exception:
                return None
    return None


def get_ml_health_score(recipe):
    model = load_recommendation_model()
    if model is None:
        return None

    feature_df = pd.DataFrame(
        [
            {
                "calories": safe_number(recipe.get("calories", 0), 0),
                "protein": safe_number(recipe.get("protein", 0), 0),
                "carbs": safe_number(recipe.get("carbs", 0), 0),
                "fat": safe_number(recipe.get("fat", 0), 0),
                "ingredient_count": len(recipe.get("ingredients", [])),
            }
        ]
    )

    try:
        prediction = float(model.predict(feature_df)[0])
        return max(0, min(15, round(prediction / 10, 2)))
    except Exception:
        return None


COMMON_INGREDIENTS = [
    "rice", "pasta", "bread", "eggs", "milk", "cheese", "chicken",
    "ground beef", "turkey", "tuna", "salmon", "shrimp", "beans",
    "black beans", "corn", "tomatoes", "lettuce", "spinach",
    "potatoes", "sweet potatoes", "carrots", "broccoli", "peas",
    "oats", "cereal", "peanut butter", "jelly", "yogurt",
    "flour", "sugar", "butter", "olive oil", "tortillas",
    "salsa", "apples", "bananas", "strawberries", "blueberries",
    "crackers", "soup", "chicken broth", "tomato sauce",
    "onion", "mushrooms", "bell pepper", "celery", "zucchini",
    "mayonnaise", "ranch", "mustard", "potato chips", "croutons"
]


@st.cache_data(show_spinner=False)
def get_dataset_dropdown_options():
    """Build participant dropdown options from the cleaned recipe dataset when available."""
    options = {
        "ingredients": [],
        "meal_types": [],
        "cuisine_types": [],
        "dish_types": [],
    }

    dataset_path = None
    for path in DATASET_PATHS:
        if path.exists():
            dataset_path = path
            break

    if dataset_path is None:
        return options

    try:
        header_df = pd.read_csv(dataset_path, nrows=0)
        columns = list(header_df.columns)
        main_ingredients_col = find_column(columns, ["main_ingredients", "ingredients", "ingredient_lines"])
        meal_type_col = find_column(columns, ["meal_type", "meal"])
        cuisine_col = find_column(columns, ["cuisine_type", "cuisine"])
        dish_type_col = find_column(columns, ["dish_type", "dish"])
        usecols = [col for col in [main_ingredients_col, meal_type_col, cuisine_col, dish_type_col] if col]
        if not usecols:
            return options
        df = pd.read_csv(dataset_path, usecols=usecols, nrows=MAX_RECIPES_FOR_APP, low_memory=False)
    except Exception:
        return options

    ingredient_set = set()
    if main_ingredients_col and main_ingredients_col in df.columns:
        for value in df[main_ingredients_col].dropna().head(MAX_RECIPES_FOR_APP):
            for item in parse_dataset_list(value):
                item = normalize_plural_ingredient(item)
                if item and not is_optional_staple(item) and 2 <= len(item) <= 35:
                    ingredient_set.add(item)

    def clean_option(value):
        value = str(value or "").strip()
        if not value or value.lower() == "nan":
            return ""
        parsed = parse_jsonish(value)
        if isinstance(parsed, list) and parsed:
            value = str(parsed[0]).strip()
        return value.title()

    def column_options(column_name):
        if not column_name or column_name not in df.columns:
            return []
        values = []
        for value in df[column_name].dropna().unique():
            cleaned = clean_option(value)
            if cleaned and cleaned not in values:
                values.append(cleaned)
        return sorted(values)[:50]

    options["ingredients"] = sorted(ingredient_set)[:250]
    options["meal_types"] = column_options(meal_type_col)
    options["cuisine_types"] = column_options(cuisine_col)
    options["dish_types"] = column_options(dish_type_col)
    return options


def get_pantry_item_dropdown_options():
    dataset_items = get_dataset_dropdown_options().get("ingredients", [])
    combined = []
    for item in COMMON_INGREDIENTS + dataset_items:
        clean = normalize_text(item)
        if clean and clean not in [normalize_text(existing) for existing in combined]:
            combined.append(item)
    return combined


def get_profile_cuisine_options():
    dataset_cuisines = get_dataset_dropdown_options().get("cuisine_types", [])
    combined = []
    for item in CUISINE_TYPE_OPTIONS + dataset_cuisines:
        if item and item not in combined:
            combined.append(item)
    if "No Preference" not in combined:
        combined.append("No Preference")
    return combined


CONTAINER_TYPES = [
    "carton",
    "loaf",
    "bottle",
    "box",
    "bag",
    "can",
    "pack",
    "jar",
    "container",
    "package",
    "bunch",
    "item",
]


USABLE_UNITS = [
    "servings",
    "serving",
    "eggs",
    "slices",
    "slice",
    "cups",
    "cup",
    "tablespoons",
    "teaspoons",
    "ounces",
    "oz",
    "pounds",
    "lb",
    "gallon",
    "gallons",
    "cartons",
    "carton",
    "loaves",
    "loaf",
    "bottles",
    "bottle",
    "boxes",
    "box",
    "jars",
    "jar",
    "containers",
    "container",
    "packages",
    "package",
    "bunches",
    "bunch",
    "heads",
    "head",
    "cans",
    "can",
    "pieces",
    "piece",
    "bags",
    "bag",
    "packs",
    "pack",
    "items",
    "item",
]


def clean_barcode_value(value):
    """Keep only numbers so participants can type or paste a barcode with spaces/dashes."""
    return re.sub(r"[^0-9]", "", str(value or ""))


@st.cache_data(show_spinner=False)
def load_barcode_lookup():
    """Load the cleaned Open Food Facts barcode lookup CSV.

    The expected file path is app/data/barcode_lookup.csv.
    The app uses item_name as the clean Smart Pantry pantry item name, while
    product_name and brand remain background proof from Open Food Facts.
    """
    barcode_path = None

    for path in BARCODE_LOOKUP_PATHS:
        if path.exists():
            barcode_path = path
            break

    if barcode_path is None:
        return pd.DataFrame()

    try:
        df = pd.read_csv(barcode_path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()

    if "barcode" not in df.columns or "item_name" not in df.columns:
        return pd.DataFrame()

    df["barcode"] = df["barcode"].apply(clean_barcode_value)
    df["item_name"] = df["item_name"].astype(str).str.strip()

    if "product_name" not in df.columns:
        df["product_name"] = ""

    if "brand" not in df.columns:
        df["brand"] = ""

    if "category" not in df.columns:
        df["category"] = "Other"

    if "quantity" not in df.columns:
        df["quantity"] = "1"

    if "unit" not in df.columns:
        df["unit"] = "item"

    if "container_type" not in df.columns:
        df["container_type"] = "package"

    if "source_url" not in df.columns:
        df["source_url"] = ""

    df = df[df["barcode"] != ""].copy()
    df = df[df["item_name"] != ""].copy()
    df = df.drop_duplicates(subset=["barcode"], keep="first")

    return df


def get_barcode_lookup_item(barcode_value):
    barcode_value = clean_barcode_value(barcode_value)
    if not barcode_value:
        return None

    lookup_df = load_barcode_lookup()

    if lookup_df.empty:
        return None

    matches = lookup_df[lookup_df["barcode"] == barcode_value]

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()


RECIPES = [
    {
        "name": "Tuna Pasta Bowl",
        "meal_type": "Lunch",
        "ingredients": ["tuna", "pasta", "tomato sauce", "cheese"],
        "amounts": {
            "tuna": 1,
            "pasta": 1,
            "tomato sauce": 1,
            "cheese": 1,
        },
        "units": {
            "tuna": "can",
            "pasta": "serving",
            "tomato sauce": "serving",
            "cheese": "serving",
        },
        "calories": 520,
        "protein": 34,
        "carbs": 58,
        "fat": 16,
        "cook_time": "20 minutes",
        "instructions": "Boil pasta, warm tomato sauce, mix in tuna, and top with cheese.",
    },
    {
        "name": "Chicken Rice Bowl",
        "meal_type": "Dinner",
        "ingredients": ["chicken", "rice", "broccoli", "carrots"],
        "amounts": {
            "chicken": 1,
            "rice": 1,
            "broccoli": 1,
            "carrots": 1,
        },
        "units": {
            "chicken": "serving",
            "rice": "serving",
            "broccoli": "serving",
            "carrots": "serving",
        },
        "calories": 610,
        "protein": 45,
        "carbs": 64,
        "fat": 18,
        "cook_time": "30 minutes",
        "instructions": "Cook rice, season chicken, steam vegetables, and combine in a bowl.",
    },
    {
        "name": "Egg and Toast Breakfast",
        "meal_type": "Breakfast",
        "ingredients": ["eggs", "bread", "cheese"],
        "amounts": {
            "eggs": 2,
            "bread": 2,
            "cheese": 1,
        },
        "units": {
            "eggs": "eggs",
            "bread": "slices",
            "cheese": "slice",
        },
        "calories": 390,
        "protein": 24,
        "carbs": 32,
        "fat": 18,
        "cook_time": "10 minutes",
        "instructions": "Toast bread, scramble eggs, and add cheese before serving.",
    },
    {
        "name": "Bean and Rice Burrito",
        "meal_type": "Dinner",
        "ingredients": ["beans", "rice", "tortillas", "cheese", "salsa"],
        "amounts": {
            "beans": 1,
            "rice": 1,
            "tortillas": 1,
            "cheese": 1,
            "salsa": 1,
        },
        "units": {
            "beans": "serving",
            "rice": "serving",
            "tortillas": "piece",
            "cheese": "serving",
            "salsa": "serving",
        },
        "calories": 560,
        "protein": 22,
        "carbs": 78,
        "fat": 17,
        "cook_time": "20 minutes",
        "instructions": "Warm beans and rice, place in tortilla, add cheese and salsa, then roll.",
    },
    {
        "name": "Peanut Butter Banana Toast",
        "meal_type": "Breakfast",
        "ingredients": ["bread", "peanut butter", "bananas"],
        "amounts": {
            "bread": 2,
            "peanut butter": 1,
            "bananas": 1,
        },
        "units": {
            "bread": "slices",
            "peanut butter": "serving",
            "bananas": "piece",
        },
        "calories": 430,
        "protein": 15,
        "carbs": 54,
        "fat": 18,
        "cook_time": "5 minutes",
        "instructions": "Toast bread, spread peanut butter, and add sliced bananas.",
    },
    {
        "name": "Chicken Tortilla Wrap",
        "meal_type": "Lunch",
        "ingredients": ["chicken", "tortillas", "lettuce", "cheese", "salsa"],
        "amounts": {
            "chicken": 1,
            "tortillas": 1,
            "lettuce": 1,
            "cheese": 1,
            "salsa": 1,
        },
        "units": {
            "chicken": "serving",
            "tortillas": "piece",
            "lettuce": "serving",
            "cheese": "serving",
            "salsa": "serving",
        },
        "calories": 510,
        "protein": 38,
        "carbs": 42,
        "fat": 20,
        "cook_time": "15 minutes",
        "instructions": "Warm tortilla, add cooked chicken, lettuce, cheese, and salsa.",
    },
    {
        "name": "Salmon Sweet Potato Plate",
        "meal_type": "Dinner",
        "ingredients": ["salmon", "sweet potatoes", "broccoli"],
        "amounts": {
            "salmon": 1,
            "sweet potatoes": 1,
            "broccoli": 1,
        },
        "units": {
            "salmon": "serving",
            "sweet potatoes": "serving",
            "broccoli": "serving",
        },
        "calories": 650,
        "protein": 42,
        "carbs": 52,
        "fat": 25,
        "cook_time": "35 minutes",
        "instructions": "Bake salmon and sweet potatoes, then serve with steamed broccoli.",
    },
    {
        "name": "Yogurt Berry Bowl",
        "meal_type": "Breakfast",
        "ingredients": ["yogurt", "strawberries", "blueberries", "oats"],
        "amounts": {
            "yogurt": 1,
            "strawberries": 1,
            "blueberries": 1,
            "oats": 1,
        },
        "units": {
            "yogurt": "serving",
            "strawberries": "serving",
            "blueberries": "serving",
            "oats": "serving",
        },
        "calories": 360,
        "protein": 18,
        "carbs": 55,
        "fat": 8,
        "cook_time": "5 minutes",
        "instructions": "Add yogurt to a bowl, top with berries and oats.",
    },
    {
        "name": "Turkey Cheese Melt",
        "meal_type": "Lunch",
        "ingredients": ["turkey", "bread", "cheese"],
        "amounts": {
            "turkey": 1,
            "bread": 2,
            "cheese": 1,
        },
        "units": {
            "turkey": "serving",
            "bread": "slices",
            "cheese": "slice",
        },
        "calories": 470,
        "protein": 33,
        "carbs": 38,
        "fat": 19,
        "cook_time": "10 minutes",
        "instructions": "Layer turkey and cheese on bread, then toast until melted.",
    },
    {
        "name": "Vegetable Soup",
        "meal_type": "Dinner",
        "ingredients": ["soup", "carrots", "peas", "corn", "chicken broth"],
        "amounts": {
            "soup": 1,
            "carrots": 1,
            "peas": 1,
            "corn": 1,
            "chicken broth": 1,
        },
        "units": {
            "soup": "can",
            "carrots": "serving",
            "peas": "serving",
            "corn": "serving",
            "chicken broth": "serving",
        },
        "calories": 310,
        "protein": 12,
        "carbs": 48,
        "fat": 7,
        "cook_time": "20 minutes",
        "instructions": "Combine soup, vegetables, and broth in a pot. Simmer until warm.",
    },
    {
        "name": "Apple Peanut Butter Snack",
        "meal_type": "Snack",
        "ingredients": ["apples", "peanut butter"],
        "amounts": {
            "apples": 1,
            "peanut butter": 1,
        },
        "units": {
            "apples": "piece",
            "peanut butter": "serving",
        },
        "calories": 290,
        "protein": 8,
        "carbs": 32,
        "fat": 16,
        "cook_time": "5 minutes",
        "instructions": "Slice apples and serve with peanut butter.",
    },
    {
        "name": "Shrimp Rice Skillet",
        "meal_type": "Dinner",
        "ingredients": ["shrimp", "rice", "peas", "carrots"],
        "amounts": {
            "shrimp": 1,
            "rice": 1,
            "peas": 1,
            "carrots": 1,
        },
        "units": {
            "shrimp": "serving",
            "rice": "serving",
            "peas": "serving",
            "carrots": "serving",
        },
        "calories": 540,
        "protein": 39,
        "carbs": 61,
        "fat": 14,
        "cook_time": "25 minutes",
        "instructions": "Cook shrimp in a skillet, add rice and vegetables, and heat together.",
    },
    {
        "name": "Chicken Salad",
        "meal_type": "Lunch",
        "ingredients": ["chicken", "lettuce", "tomatoes", "onion", "cheese"],
        "amounts": {
            "chicken": 1,
            "lettuce": 1,
            "tomatoes": 1,
            "onion": 1,
            "cheese": 1,
        },
        "units": {
            "chicken": "serving",
            "lettuce": "serving",
            "tomatoes": "serving",
            "onion": "serving",
            "cheese": "serving",
        },
        "calories": 430,
        "protein": 36,
        "carbs": 18,
        "fat": 24,
        "cook_time": "15 minutes",
        "instructions": "Chop lettuce and tomatoes, add cooked chicken, onion, and cheese. Mix and serve.",
    },
    {
        "name": "Shrimp Salad",
        "meal_type": "Lunch",
        "ingredients": ["shrimp", "lettuce", "tomatoes", "onion", "cheese"],
        "amounts": {
            "shrimp": 1,
            "lettuce": 1,
            "tomatoes": 1,
            "onion": 1,
            "cheese": 1,
        },
        "units": {
            "shrimp": "serving",
            "lettuce": "serving",
            "tomatoes": "serving",
            "onion": "serving",
            "cheese": "serving",
        },
        "calories": 390,
        "protein": 32,
        "carbs": 16,
        "fat": 21,
        "cook_time": "15 minutes",
        "instructions": "Cook shrimp if needed, then combine with lettuce, tomatoes, onion, and cheese.",
    },
    {
        "name": "Turkey Rice Bowl",
        "meal_type": "Dinner",
        "ingredients": ["turkey", "rice", "corn", "salsa", "cheese"],
        "amounts": {
            "turkey": 1,
            "rice": 1,
            "corn": 1,
            "salsa": 1,
            "cheese": 1,
        },
        "units": {
            "turkey": "serving",
            "rice": "serving",
            "corn": "serving",
            "salsa": "serving",
            "cheese": "serving",
        },
        "calories": 590,
        "protein": 38,
        "carbs": 63,
        "fat": 19,
        "cook_time": "25 minutes",
        "instructions": "Cook rice, warm turkey and corn, then top with salsa and cheese.",
    },
]


def get_active_recipes():
    dataset_recipes = load_recipes_from_dataset()
    if dataset_recipes:
        return dataset_recipes
    return RECIPES


SUBSTITUTIONS = {
    "chicken": ["shrimp", "turkey", "tuna", "salmon", "beans"],
    "shrimp": ["chicken", "salmon", "tuna"],
    "salmon": ["shrimp", "tuna", "chicken"],
    "tuna": ["chicken", "shrimp", "salmon"],
    "ground beef": ["turkey", "chicken", "beans"],
    "turkey": ["chicken", "ground beef", "beans"],
    "milk": ["yogurt", "water"],
    "cheese": ["yogurt"],
    "bread": ["tortillas", "crackers"],
    "tortillas": ["bread"],
    "rice": ["pasta", "potatoes"],
    "pasta": ["rice", "potatoes"],
    "broccoli": ["spinach", "peas", "carrots"],
    "carrots": ["broccoli", "peas", "corn"],
    "lettuce": ["spinach"],
    "tomato sauce": ["tomatoes", "salsa"],
    "salsa": ["tomato sauce", "tomatoes"],
    "onion": ["bell pepper", "celery", "onion powder"],
    "mushrooms": ["zucchini", "bell pepper", "spinach"],
    "tomatoes": ["salsa", "tomato sauce"],
    "sweet potatoes": ["potatoes", "rice"],
    "peas": ["corn", "carrots"],
    "corn": ["peas", "carrots"],
}


def normalize_text(value):
    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9\s\-]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def format_number(value):
    try:
        value = float(value)
        if value.is_integer():
            return str(int(value))
        return str(round(value, 2))
    except Exception:
        return str(value)


def get_available_pantry_items(pantry_df):
    if pantry_df.empty:
        return []

    return pantry_df["item_name"].apply(normalize_text).tolist()


def get_days_until_expiration(expiration_date):
    try:
        exp_date = datetime.strptime(str(expiration_date), "%Y-%m-%d").date()
        return (exp_date - date.today()).days
    except ValueError:
        return 999


def get_expiration_alert_info(days_left):
    if days_left <= 1:
        return {
            "level": "Use immediately!",
            "class": "alert-red",
            "message": "This item needs attention now so it does not get wasted."
        }

    if 2 <= days_left <= 4:
        return {
            "level": "Warning: Use Soon",
            "class": "alert-orange",
            "message": "Try to use this item soon before it expires."
        }

    if 5 <= days_left <= 10:
        return {
            "level": "Plan ahead",
            "class": "alert-blue",
            "message": "This item is not urgent yet, but it should be planned into a meal soon."
        }

    return None


def get_recipe_requirements(recipe):
    requirements = []

    for ingredient in recipe["ingredients"]:
        ingredient_clean = normalize_text(ingredient)
        amount = recipe.get("amounts", {}).get(ingredient, 1)
        unit = recipe.get("units", {}).get(ingredient, "serving")

        requirements.append(
            {
                "ingredient": ingredient_clean,
                "amount": float(amount),
                "unit": unit,
            }
        )

    return requirements


def get_item_name_variants(value):
    base = normalize_text(value)
    variants = {base}

    if base.endswith("ies") and len(base) > 3:
        variants.add(base[:-3] + "y")

    if base.endswith("es") and len(base) > 2:
        variants.add(base[:-2])

    if base.endswith("s") and len(base) > 1:
        variants.add(base[:-1])

    return {item.strip() for item in variants if item and item.strip()}


def pantry_item_matches(pantry_item_name, target_item_name):
    pantry_variants = get_item_name_variants(pantry_item_name)
    target_variants = get_item_name_variants(target_item_name)

    if pantry_variants.intersection(target_variants):
        return True

    pantry_clean = normalize_text(pantry_item_name)
    target_clean = normalize_text(target_item_name)

    if target_clean in pantry_clean or pantry_clean in target_clean:
        return True

    return False


def find_pantry_row_for_item(pantry_df, item_name):
    item_name = normalize_text(item_name)

    if pantry_df.empty:
        return None

    exact_matches = pantry_df[
        pantry_df["item_name"].apply(normalize_text) == item_name
    ]

    if not exact_matches.empty:
        return exact_matches.iloc[0]

    for _, row in pantry_df.iterrows():
        if pantry_item_matches(row["item_name"], item_name):
            return row

    return None


def pantry_has_enough(pantry_df, item_name, amount_needed):
    row = find_pantry_row_for_item(pantry_df, item_name)

    if row is None:
        return False

    try:
        available_quantity = float(row["quantity"])
    except Exception:
        available_quantity = 0

    return available_quantity >= float(amount_needed)



SMART_SWAP_GROUPS = {
    "chicken": [
        "chicken", "chicken breast", "chicken breasts", "chicken thigh",
        "chicken thighs", "chicken wing", "chicken wings", "rotisserie chicken",
        "canned chicken"
    ],
    "beef": ["beef", "ground beef", "beef strips", "steak", "roast beef"],
    "turkey": ["turkey", "ground turkey", "turkey slices", "turkey breast"],
    "fish": ["fish", "salmon", "tuna", "tilapia", "cod"],
    "egg": ["egg", "eggs"],
    "bread_base": ["bread", "tortilla", "tortillas", "wrap", "buns", "rolls", "crackers"],
    "starch": ["rice", "pasta", "spaghetti", "macaroni", "noodles", "potato", "potatoes"],
    "dairy": ["milk", "cheese", "yogurt", "sour cream", "cream cheese"],
    "greens": ["lettuce", "spinach", "cabbage", "kale"],
    "vegetable_flavor": ["onion", "bell pepper", "celery", "zucchini", "mushroom", "mushrooms"],
    "tomato_base": ["tomato", "tomatoes", "tomato sauce", "salsa", "pasta sauce"],
}


def get_smart_swap_group(ingredient):
    ingredient = normalize_text(ingredient)
    for group_name, group_items in SMART_SWAP_GROUPS.items():
        for group_item in group_items:
            if pantry_item_matches(ingredient, group_item):
                return group_name
    return None


def get_quantity_available(pantry_row):
    if pantry_row is None:
        return 0
    try:
        return float(pantry_row.get("quantity", 0) or 0)
    except Exception:
        return 0


def find_pantry_row_by_group(pantry_df, required_ingredient):
    required_group = get_smart_swap_group(required_ingredient)
    if required_group is None or pantry_df.empty:
        return None

    for _, row in pantry_df.iterrows():
        pantry_group = get_smart_swap_group(row["item_name"])
        if pantry_group == required_group:
            return row

    return None


def find_smart_substitution(required_ingredient, pantry_df, amount_needed=1):
    """Return a realistic Smart Swap without letting substitutions count as exact make-now meals."""
    required_ingredient = normalize_text(required_ingredient)
    amount_needed = float(amount_needed or 1)

    exact_row = find_pantry_row_for_item(pantry_df, required_ingredient)
    if exact_row is not None:
        available_amount = get_quantity_available(exact_row)
        if 0 < available_amount < amount_needed:
            return {
                "missing": required_ingredient,
                "substitute": normalize_text(exact_row["item_name"]),
                "substitution_type": "quantity_adjustment",
                "amount_needed": amount_needed,
                "available_amount": available_amount,
                "message": (
                    f"This recipe calls for {format_number(amount_needed)} {exact_row.get('unit', 'serving')} "
                    f"{required_ingredient}, but you have {format_number(available_amount)}. "
                    f"You can still make a smaller portion."
                ),
            }

    family_row = find_pantry_row_by_group(pantry_df, required_ingredient)
    if family_row is not None:
        available_amount = get_quantity_available(family_row)
        pantry_name = normalize_text(family_row["item_name"])
        if available_amount > 0 and not pantry_item_matches(pantry_name, required_ingredient):
            return {
                "missing": required_ingredient,
                "substitute": pantry_name,
                "substitution_type": "same_food_family",
                "amount_needed": amount_needed,
                "available_amount": available_amount,
                "message": (
                    f"This recipe calls for {required_ingredient}, but you have {family_row['item_name']}. "
                    f"This should still work because it is the same main ingredient family."
                ),
            }

    possible_subs = SUBSTITUTIONS.get(required_ingredient, [])
    for substitute in possible_subs:
        substitute_row = find_pantry_row_for_item(pantry_df, substitute)
        if substitute_row is not None:
            available_amount = get_quantity_available(substitute_row)
            if available_amount <= 0:
                continue

            required_group = get_smart_swap_group(required_ingredient)
            substitute_group = get_smart_swap_group(substitute)
            if required_group == "vegetable_flavor":
                substitution_type = "optional_flavor_substitute"
                message = (
                    f"This recipe calls for {required_ingredient}, but you have {substitute}. "
                    f"This works as a flavor swap, but the taste may change."
                )
            elif required_group and substitute_group and required_group == substitute_group:
                substitution_type = "same_food_family"
                message = (
                    f"This recipe calls for {required_ingredient}, but you have {substitute}. "
                    f"This should still work because it is the same ingredient family."
                )
            else:
                substitution_type = "functional_substitute"
                message = (
                    f"This recipe calls for {required_ingredient}, but you have {substitute}. "
                    f"This may work because it plays a similar role in the meal."
                )

            return {
                "missing": required_ingredient,
                "substitute": substitute,
                "substitution_type": substitution_type,
                "amount_needed": amount_needed,
                "available_amount": available_amount,
                "message": message,
            }

    return None


def get_dish_style(recipe_name, ingredients):
    text = normalize_text(recipe_name + " " + " ".join(ingredients))
    style_terms = {
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
    for style, terms in style_terms.items():
        if any(term in text for term in terms):
            return style
    return "general"


def get_core_recipe_groups(ingredients):
    groups = []
    for ingredient in ingredients:
        group = get_smart_swap_group(ingredient)
        if group and group not in groups:
            groups.append(group)
    return groups


def get_recipe_family_key(recipe):
    recipe_name = recipe.get("name", "")
    ingredients = [normalize_text(item) for item in recipe.get("ingredients", [])]
    dish_style = get_dish_style(recipe_name, ingredients)
    core_groups = get_core_recipe_groups(ingredients)

    protein_groups = [group for group in core_groups if group in ["chicken", "beef", "turkey", "fish", "egg"]]
    base_groups = [group for group in core_groups if group in ["starch", "bread_base", "greens", "tomato_base"]]
    protein_key = "+".join(sorted(protein_groups[:2])) or "no_main_protein"
    base_key = "+".join(sorted(base_groups[:2])) or "no_main_base"
    return f"{protein_key}|{base_key}|{dish_style}"


def get_match_tier(match_percent):
    if match_percent >= 80:
        return "🟢 Great Match"
    if match_percent >= 60:
        return "🟡 Strong Match"
    if match_percent >= 40:
        return "🟠 Partial Match"
    if match_percent >= 20:
        return "🔵 Low Match"
    return "⚪ Very Low Match"


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


def build_why_this_meal(item):
    reasons = []
    exact_percent = item.get("exact_match_percent", item.get("match_percent", 0))
    coverage_percent = item.get("coverage_percent", exact_percent)

    if item["matched_ingredients"]:
        reasons.append(
            f"Exact pantry ingredients found: {len(item['matched_ingredients'])} item(s): "
            + ", ".join(item["matched_ingredients"][:5])
        )

    if item["expiring_ingredients"]:
        reasons.append("Uses ingredient(s) that should be planned soon: " + ", ".join(item["expiring_ingredients"][:5]))

    if item["substitutions"]:
        reasons.append(
            f"This meal is under Smart Swaps because {len(item['substitutions'])} ingredient(s) need a swap, "
            "ingredient-family match, or smaller amount adjustment."
        )

    if item.get("missing_without_substitution"):
        reasons.append("Still missing without a pantry swap: " + ", ".join(item["missing_without_substitution"][:5]))

    if item.get("ml_health_score") is not None:
        reasons.append(f"Random Forest nutrition/practicality support: {item['ml_health_score']}/15.")

    reasons.append(f"Exact pantry match: {exact_percent}%.")
    if coverage_percent != exact_percent:
        reasons.append(f"Coverage with Smart Swaps or amount adjustments: {coverage_percent}%.")
    reasons.append(f"Smart Score: {item['score']}/100.")
    return reasons



def find_substitution(required_ingredient, pantry_df, amount_needed=1):
    smart_sub = find_smart_substitution(required_ingredient, pantry_df, amount_needed)
    if smart_sub:
        return smart_sub.get("substitute")
    return None

def profile_terms_to_set(value):
    terms = []
    for part in re.split(r",|;|\n", str(value)):
        clean = normalize_text(part)
        if clean:
            terms.append(clean)
            if clean.endswith("s"):
                terms.append(clean[:-1])
            else:
                terms.append(clean + "s")
    return set(terms)


def get_profile_warning_items(recipe_ingredients, profile):
    allergies = profile_terms_to_set(profile.get("allergies", ""))
    disliked = profile_terms_to_set(profile.get("disliked_ingredients", ""))

    warning_items = []

    for ingredient in recipe_ingredients:
        ingredient_clean = normalize_text(ingredient)
        ingredient_terms = {ingredient_clean}
        if ingredient_clean.endswith("s"):
            ingredient_terms.add(ingredient_clean[:-1])
        else:
            ingredient_terms.add(ingredient_clean + "s")

        if ingredient_terms & allergies:
            warning_items.append(
                {
                    "ingredient": ingredient,
                    "reason": "allergy",
                    "message": f"This recipe calls for {ingredient}. Your profile lists this as an allergy. Please substitute or remove it.",
                }
            )
        elif ingredient_terms & disliked:
            warning_items.append(
                {
                    "ingredient": ingredient,
                    "reason": "preference",
                    "message": f"This recipe calls for {ingredient}. Your profile lists this as disliked. You may substitute or remove it.",
                }
            )

    return warning_items


def calculate_recommendation_score(recipe, pantry_df, profile):
    recipe_requirements = get_recipe_requirements(recipe)

    exact_matches = []
    substitutions = []
    missing_without_substitution = []
    expiring_ingredients = []

    for requirement in recipe_requirements:
        ingredient = requirement["ingredient"]
        amount_needed = requirement["amount"]

        exact_row = find_pantry_row_for_item(pantry_df, ingredient)

        if exact_row is not None and pantry_has_enough(pantry_df, ingredient, amount_needed):
            exact_matches.append(ingredient)
        else:
            smart_substitution = find_smart_substitution(ingredient, pantry_df, amount_needed)

            if smart_substitution:
                substitutions.append(smart_substitution)
            else:
                missing_without_substitution.append(ingredient)

    total_needed = len(recipe_requirements)
    exact_count = len(exact_matches)
    swap_count = len(substitutions)
    missing_count = len(missing_without_substitution)

    exact_match_percent = round((exact_count / max(total_needed, 1)) * 100)
    coverage_percent = round(((exact_count + swap_count) / max(total_needed, 1)) * 100)

    can_make_meal = total_needed > 0 and exact_count == total_needed and swap_count == 0 and missing_count == 0
    can_make_with_swaps = total_needed > 0 and missing_count == 0 and swap_count > 0

    used_items = exact_matches + [
        normalize_text(sub["substitute"])
        for sub in substitutions
    ]

    for _, row in pantry_df.iterrows():
        item_name = normalize_text(row["item_name"])
        days_left = get_days_until_expiration(row["expiration_date"])

        if item_name in used_items and days_left <= 10:
            expiring_ingredients.append(item_name)

    preferred_meal_types = normalize_text(profile.get("preferred_meal_types", ""))
    preferred_cuisine_types = normalize_text(profile.get("preferred_cuisine_types", ""))
    recipe_cuisine = normalize_text(recipe.get("cuisine_type", ""))

    meal_type_score = 10 if normalize_text(recipe["meal_type"]) in preferred_meal_types else 5
    cuisine_score = 0
    if preferred_cuisine_types and "no preference" not in preferred_cuisine_types:
        preferred_cuisines = [normalize_text(item) for item in re.split(r",|;|\n", preferred_cuisine_types) if normalize_text(item)]
        if any(cuisine and cuisine in recipe_cuisine for cuisine in preferred_cuisines):
            cuisine_score = 8

    preference_score = meal_type_score + cuisine_score

    if exact_count + swap_count > 0:
        ml_health_score = get_ml_health_score(recipe)
    else:
        ml_health_score = None

    nutrition_score = ml_health_score if ml_health_score is not None else 10
    expiration_score = min(len(expiring_ingredients) * 10, 20)

    exact_component = exact_match_percent * 0.35
    coverage_component = coverage_percent * 0.15
    swap_component = 10 if can_make_with_swaps else 0
    quantity_component = 15 if can_make_meal else (8 if can_make_with_swaps else 0)
    preference_component = min(preference_score, 15)
    nutrition_component = min(nutrition_score, 15)
    missing_penalty = missing_count * 8

    final_score = (
        exact_component
        + coverage_component
        + expiration_score
        + swap_component
        + quantity_component
        + preference_component
        + nutrition_component
        - missing_penalty
    )

    if can_make_with_swaps:
        final_score = min(final_score, 94)
    elif missing_count > 0:
        final_score = min(final_score, 79)

    final_score = round(max(0, min(final_score, 100)))

    warning_items = get_profile_warning_items(
        [requirement["ingredient"] for requirement in recipe_requirements],
        profile,
    )

    return {
        "can_make_meal": can_make_meal,
        "can_make_with_swaps": can_make_with_swaps,
        "score": final_score,
        "matched_ingredients": exact_matches,
        "substitutions": substitutions,
        "missing_without_substitution": missing_without_substitution,
        "expiring_ingredients": expiring_ingredients,
        "warning_items": warning_items,
        "requirements": recipe_requirements,
        "ml_health_score": ml_health_score,
        "exact_match_percent": exact_match_percent,
        "coverage_percent": coverage_percent,
        "exact_count": exact_count,
        "swap_count": swap_count,
        "missing_count": missing_count,
    }


def recipe_has_any_pantry_overlap(recipe, pantry_df):
    """Fast pre-check so the app does not score recipes that share nothing useful with the pantry."""
    if pantry_df.empty:
        return False

    pantry_names = [normalize_text(name) for name in pantry_df["item_name"].tolist()]
    recipe_names = [normalize_text(name) for name in recipe.get("ingredients", [])]

    for recipe_item in recipe_names:
        for pantry_item in pantry_names:
            if pantry_item_matches(pantry_item, recipe_item):
                return True

        smart_sub = find_smart_substitution(recipe_item, pantry_df, 1)
        if smart_sub and smart_sub.get("substitution_type") in ["same_food_family", "quantity_adjustment"]:
            return True

    return False

def get_recommendations(pantry_df, profile, meal_type_filter):
    if pantry_df.empty:
        return []

    recommendations = []
    active_recipes = get_active_recipes()

    for recipe in active_recipes:
        if meal_type_filter != "All" and recipe["meal_type"] != meal_type_filter:
            continue

        if not recipe_has_any_pantry_overlap(recipe, pantry_df):
            continue

        score_info = calculate_recommendation_score(recipe, pantry_df, profile)
        exact_match_percent = score_info.get("exact_match_percent", 0)
        coverage_percent = score_info.get("coverage_percent", exact_match_percent)

        if coverage_percent == 0:
            continue

        if score_info["can_make_meal"]:
            category = "Meals You Can Make Now"
            category_label = "Make Now"
        elif score_info.get("can_make_with_swaps", False):
            category = "Smart Swaps / Almost There"
            category_label = "Smart Swap Match"
        else:
            category = "Need More Ingredients"
            category_label = "More Ideas"

        recommendations.append(
            {
                "recipe": recipe,
                "score": score_info["score"],
                "matched_ingredients": score_info["matched_ingredients"],
                "substitutions": score_info["substitutions"],
                "missing_without_substitution": score_info["missing_without_substitution"],
                "expiring_ingredients": score_info["expiring_ingredients"],
                "warning_items": score_info["warning_items"],
                "requirements": score_info["requirements"],
                "ml_health_score": score_info.get("ml_health_score"),
                "can_make_meal": score_info["can_make_meal"],
                "can_make_with_swaps": score_info.get("can_make_with_swaps", False),
                "recommendation_category": category,
                "recommendation_category_label": category_label,
                "match_percent": exact_match_percent,
                "exact_match_percent": exact_match_percent,
                "coverage_percent": coverage_percent,
                "match_tier": get_match_tier(exact_match_percent),
                "recipe_family_key": get_recipe_family_key(recipe),
                "recipe_quality_score": recipe.get("recipe_quality_score", 75),
                "exact_count": score_info.get("exact_count", 0),
                "swap_count": score_info.get("swap_count", 0),
                "missing_count": score_info.get("missing_count", 0),
            }
        )

    recommendations = sorted(
        recommendations,
        key=lambda item: (
            len(item["expiring_ingredients"]) > 0,
            item["can_make_meal"],
            item.get("can_make_with_swaps", False),
            item["score"],
            item.get("exact_match_percent", item.get("match_percent", 0)),
            item.get("coverage_percent", 0),
            item.get("recipe_quality_score", 0),
        ),
        reverse=True,
    )

    return recommendations


def mark_recipe_ingredients_used(user_id, pantry_df, recipe, selected_substitutions, feedback):
    messages = []
    requirements = get_recipe_requirements(recipe)

    for requirement in requirements:
        ingredient = requirement["ingredient"]
        amount_needed = requirement["amount"]
        item_to_use = selected_substitutions.get(ingredient, ingredient)

        pantry_row = find_pantry_row_for_item(pantry_df, item_to_use)

        if pantry_row is None:
            messages.append(f"{item_to_use} was not found in the pantry.")
            continue

        success, message = reduce_pantry_item_quantity(
            user_id,
            pantry_row["id"],
            amount_needed,
            "Used in recommended meal",
            f"Used for {recipe['name']}. {feedback}",
        )

        messages.append(message)

    clear_user_cache(user_id)
    return messages


def mark_selected_ingredients_used(user_id, pantry_df, selected_ingredient_names, usage_type, notes, amount_lookup=None):
    messages = []
    amount_lookup = amount_lookup or {}

    for item_name in selected_ingredient_names:
        pantry_row = find_pantry_row_for_item(pantry_df, item_name)

        if pantry_row is None:
            messages.append(f"{item_name} was not found in the pantry.")
            continue

        amount_to_use = amount_lookup.get(normalize_text(item_name), 1)

        success, message = reduce_pantry_item_quantity(
            user_id,
            pantry_row["id"],
            amount_to_use,
            usage_type,
            notes,
        )

        messages.append(message)

    clear_user_cache(user_id)
    return messages


def mark_selected_pantry_rows_used(user_id, selected_usage_rows, usage_type, notes):
    messages = []

    for usage in selected_usage_rows:
        success, message = reduce_pantry_item_quantity(
            user_id,
            usage["pantry_item_id"],
            usage["amount_used"],
            usage_type,
            notes,
        )
        messages.append(message)

    clear_user_cache(user_id)
    return messages


def discard_selected_pantry_item(user_id, pantry_df, item_name, notes):
    pantry_row = find_pantry_row_for_item(pantry_df, item_name)

    if pantry_row is None:
        return False, f"{item_name} was not found in the pantry."

    success = mark_item_used(
        user_id,
        pantry_row["id"],
        "Expired or discarded",
        notes,
    )

    if success:
        clear_user_cache(user_id)
        return True, f"{item_name} was marked as expired/discarded and removed from the active pantry."

    return False, f"Could not update {item_name}."


def logout():
    st.session_state.clear()
    st.rerun()


def show_login_page():
    login_logo_col1, login_logo_col2, login_logo_col3 = st.columns([1, 2, 1])
    with login_logo_col2:
        show_logo(width=260)

    st.markdown(
        """
        <div class="friendly-note">
            <strong>Welcome to Smart Pantry!!!</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["Login", "Create Participant Account"])

    with tab_login:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            user = login_user(username, password)

            if user:
                st.session_state["user"] = user
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab_register:
        new_username = st.text_input("Create username", key="register_username")
        new_password = st.text_input("Create password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm password", type="password")

        if st.button("Create Account"):
            if not new_username or not new_password:
                st.error("Please enter a username and password.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = register_user(new_username, new_password)

                if success:
                    clear_user_cache()
                    st.success(message)
                    st.info("You can now log in.")
                else:
                    st.error(message)


def show_sidebar():
    user = st.session_state["user"]

    logo_path = get_logo_path()
    if logo_path:
        st.sidebar.image(logo_path, use_container_width=True)

    st.sidebar.write(f"Logged in as: **{user['username']}**")
    st.sidebar.write(f"Role: **{user['role']}**")

    if user["role"] == "admin":
        pages = [
            "Admin Dashboard",
            "Participant View",
            "Logout",
        ]
    else:
        pages = [
            "Home",
            "Profile",
            "Pre-Study Survey",
            "My Pantry",
            "Meal Recommendations",
            "Recommendation History",
            "Post-Study Survey",
            "Logout",
        ]

    selected_page = st.sidebar.radio("Navigation", pages)

    if selected_page == "Logout":
        logout()

    return selected_page



def color_name_for_category(category):
    color_names = {
        "Protein": "Red",
        "Dairy": "Yellow",
        "Grain": "Purple",
        "Fruit": "Pink",
        "Vegetable": "Green",
        "Canned Goods": "Mint",
        "Frozen": "Blue",
        "Snack": "Orange",
        "Condiment": "Brown",
        "Tea & Coffee": "Gray",
        "Other": "Light gray",
    }
    return color_names.get(clean_category_value(category), "Light gray")


def show_pantry_category_pie(pantry_df):
    if pantry_df.empty or "category" not in pantry_df.columns:
        st.info("Add pantry items to see your pantry category breakdown.")
        return

    category_counts = pantry_df["category"].fillna("Other").apply(clean_category_value).value_counts()

    if category_counts.empty:
        st.info("Add pantry items to see your pantry category breakdown.")
        return

    st.subheader("Pantry Category Breakdown")
    st.caption("This shows the mix of pantry items by category.")

    category_colors = {
        "Protein": "#ef4444",
        "Dairy": "#facc15",
        "Grain": "#a855f7",
        "Fruit": "#ec4899",
        "Vegetable": "#22c55e",
        "Canned Goods": "#10b981",
        "Frozen": "#60a5fa",
        "Snack": "#f97316",
        "Condiment": "#92400e",
        "Tea & Coffee": "#6b7280",
        "Other": "#d1d5db",
    }

    try:
        import matplotlib.pyplot as plt

        chart_col, legend_col = st.columns([2, 1])
        colors = [category_colors.get(category, category_colors["Other"]) for category in category_counts.index]

        with chart_col:
            fig, ax = plt.subplots(figsize=(4.6, 4.6))
            ax.pie(
                category_counts.values,
                labels=None,
                autopct="%1.0f%%",
                startangle=90,
                colors=colors,
                textprops={"fontsize": 9},
            )
            ax.axis("equal")
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

        with legend_col:
            st.markdown("**Color Key**")
            for category in category_counts.index:
                color = category_colors.get(category, category_colors["Other"])
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                        <div style="width:14px; height:14px; background:{color}; border-radius:50%; border:1px solid #666;"></div>
                        <span>{color_name_for_category(category)} = {category}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    except Exception:
        summary_df = pd.DataFrame({
            "Category": category_counts.index,
            "Percent": (category_counts / category_counts.sum() * 100).round(1).values,
            "Item Count": category_counts.values,
        })
        st.dataframe(summary_df, use_container_width=True)


def render_expiration_alerts(pantry_df):
    st.subheader("Expiration Alerts")

    if pantry_df.empty:
        st.info("No pantry items added yet.")
        return 0

    alert_count = 0

    for _, row in pantry_df.iterrows():
        days_left = get_days_until_expiration(row["expiration_date"])
        alert_info = get_expiration_alert_info(days_left)

        if alert_info:
            alert_count += 1
            day_word = "day" if days_left == 1 else "days"

            if days_left < 0:
                time_text = f"expired {abs(days_left)} days ago"
            elif days_left == 0:
                time_text = "expires today"
            else:
                time_text = f"expires in {days_left} {day_word}"

            st.markdown(
                f"""
                <div class="{alert_info['class']}">
                    {alert_info['level']}: {row['item_name'].title()} {time_text}<br>
                    Amount left: {format_number(row['quantity'])} {row['unit']} in {row.get('container_type', 'item')}<br>
                    {alert_info['message']}
                </div>
                """,
                unsafe_allow_html=True,
            )

    if alert_count == 0:
        st.success("No pantry items need attention right now.")

    return alert_count



def get_future_grocery_suggestions(pantry_df):
    if pantry_df.empty:
        return []

    pantry_names = {normalize_text(name) for name in pantry_df["item_name"].tolist()}
    pantry_categories = pantry_df["category"].fillna("Other").apply(clean_category_value).tolist()
    category_counts = pd.Series(pantry_categories).value_counts().to_dict()

    suggestions = []
    seen = set()

    def add_suggestion(item, reason, priority, suggestion_type="Add", allow_existing=False):
        key = f"{normalize_text(item)}::{normalize_text(reason)}::{normalize_text(suggestion_type)}"
        item_key = normalize_text(item)
        if not item_key or key in seen:
            return
        if not allow_existing and item_key in pantry_names:
            return
        seen.add(key)
        suggestions.append({
            "Item": str(item).title(),
            "Why It Is Listed": reason,
            "Type": suggestion_type,
            "Priority": priority,
        })

    for _, row in pantry_df.iterrows():
        days_left = get_days_until_expiration(row["expiration_date"])
        item_name = str(row["item_name"]).title()
        quantity = safe_number(row.get("quantity", 0), 0)
        unit = str(row.get("unit", "")).strip()

        if days_left < 0:
            add_suggestion(
                item_name,
                "Expired in pantry. Replace only if this is an item the household still uses.",
                "High",
                "Expired / Replace",
                allow_existing=True,
            )
        elif days_left <= 5:
            add_suggestion(
                item_name,
                f"Expires in {days_left} day(s). Use soon, then replace if needed.",
                "High" if days_left <= 2 else "Medium",
                "Use Soon / Possible Replacement",
                allow_existing=True,
            )

        if 0 < quantity <= 2:
            normalized_name = normalize_text(row.get("item_name", ""))
            common_meal_helpers = {
                "milk", "cheese", "eggs", "egg", "bread", "rice", "pasta", "tortilla", "tortillas",
                "chicken", "beans", "tomato sauce", "salsa", "broccoli", "spinach", "lettuce"
            }
            if normalized_name in common_meal_helpers or any(helper in normalized_name for helper in common_meal_helpers):
                add_suggestion(
                    item_name,
                    f"Only {format_number(quantity)} {unit} left, and this item can help make several meals.",
                    "Medium",
                    "Low Amount / Restock Soon",
                    allow_existing=True,
                )

    category_boosters = {
        "Protein": ["chicken", "eggs", "beans", "tuna"],
        "Grain": ["rice", "pasta", "bread", "tortillas"],
        "Dairy": ["cheese", "milk", "yogurt"],
        "Vegetable": ["broccoli", "spinach", "carrots", "tomatoes"],
        "Fruit": ["apples", "bananas", "berries"],
    }

    for category, items in category_boosters.items():
        if category_counts.get(category, 0) < 2:
            for item in items:
                add_suggestion(item, f"Adds more {category.lower()} options for future meals.", "Medium", "Meal Helper")
                break

    meal_pairings = [
        ("pasta", "tomato sauce", "Completes easy pasta meals."),
        ("pasta", "ground beef", "Adds protein for pasta meals."),
        ("rice", "beans", "Completes rice and bean meals."),
        ("rice", "chicken", "Completes chicken rice bowls."),
        ("bread", "cheese", "Completes sandwiches or melts."),
        ("bread", "eggs", "Completes breakfast meals."),
        ("tortilla", "cheese", "Completes wraps or quesadillas."),
        ("tortillas", "salsa", "Completes tacos or wraps."),
        ("eggs", "bread", "Completes quick breakfast meals."),
        ("cheese", "tortillas", "Completes quesadillas or wraps."),
    ]

    for have_item, needed_item, reason in meal_pairings:
        if have_item in pantry_names and needed_item not in pantry_names:
            add_suggestion(needed_item, reason, "Low", "Meal Helper")

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    suggestions = sorted(suggestions, key=lambda item: priority_order.get(item["Priority"], 9))
    return suggestions[:10]



def show_grocery_item_list(title, items, css_class):
    clean_items = []
    seen = set()

    for item in items:
        item_text = str(item).strip().title()
        item_key = normalize_text(item_text)
        if item_text and item_key not in seen:
            clean_items.append(item_text)
            seen.add(item_key)

    if not clean_items:
        return

    list_items = "".join(f"<li>{item}</li>" for item in clean_items)
    st.markdown(
        f"""
        <div class="grocery-list-card {css_class}">
            <h4>{title}</h4>
            <ul>{list_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_manual_grocery_items(user_id):
    manual_key = f"manual_grocery_items_{user_id}"

    if manual_key not in st.session_state:
        st.session_state[manual_key] = []

    st.markdown("**Add your own grocery items**")

    with st.form(f"manual_grocery_form_{user_id}"):
        manual_entry = st.text_input(
            "Type ingredient or item",
            placeholder="Example: eggs, rice, yogurt",
            key=f"manual_grocery_entry_{user_id}",
        )
        add_manual = st.form_submit_button("Add to Grocery List")

    if add_manual:
        new_items = [item.strip().title() for item in re.split(r",|;|\n", manual_entry) if item.strip()]
        existing_keys = {normalize_text(item) for item in st.session_state[manual_key]}

        for item in new_items:
            item_key = normalize_text(item)
            if item_key and item_key not in existing_keys:
                st.session_state[manual_key].append(item)
                existing_keys.add(item_key)

        if new_items:
            st.success("Item added to your grocery list ideas.")
            st.rerun()
        else:
            st.warning("Please type at least one item before adding.")

    if st.session_state[manual_key]:
        show_grocery_item_list(
            "Your Added Items",
            st.session_state[manual_key],
            "grocery-list-manual",
        )

        col_clear, col_spacer = st.columns([1, 3])
        with col_clear:
            if st.button("Clear Added Items", key=f"clear_manual_grocery_{user_id}"):
                st.session_state[manual_key] = []
                st.rerun()


def show_future_grocery_list(pantry_df):
    st.subheader("Suggested Grocery List")

    user_id = st.session_state["user"]["id"]
    manual_key = f"manual_grocery_items_{user_id}"
    if manual_key not in st.session_state:
        st.session_state[manual_key] = []

    suggestions = get_future_grocery_suggestions(pantry_df)
    table_rows = []
    seen_items = set()

    priority_rank = {"High": 0, "Medium": 1, "Low": 2, "Manual": 3}
    priority_display = {
        "High": "High",
        "Medium": "Medium",
        "Low": "Helpful",
        "Manual": "Added by User",
    }

    for suggestion in suggestions:
        item_name = str(suggestion.get("Item", "")).strip().title()
        item_key = normalize_text(item_name)
        if not item_name or item_key in seen_items:
            continue
        seen_items.add(item_key)
        priority = str(suggestion.get("Priority", "Low")).strip().title()
        suggestion_type = str(suggestion.get("Type", "Suggested")).strip()
        reason = str(suggestion.get("Why It Is Listed", "Suggested based on pantry activity.")).strip()
        table_rows.append(
            {
                "Priority": priority_display.get(priority, priority),
                "Item": item_name,
                "Reason": reason,
                "Category": suggestion_type,
                "Sort": priority_rank.get(priority, 9),
            }
        )

    for manual_item in st.session_state[manual_key]:
        item_name = str(manual_item).strip().title()
        item_key = normalize_text(item_name)
        if not item_name or item_key in seen_items:
            continue
        seen_items.add(item_key)
        table_rows.append(
            {
                "Priority": "Added by User",
                "Item": item_name,
                "Reason": "Manually added to the grocery list.",
                "Category": "Manual",
                "Sort": priority_rank["Manual"],
            }
        )

    if table_rows:
        grocery_df = pd.DataFrame(table_rows).sort_values(["Sort", "Item"])
        grocery_df = grocery_df[["Priority", "Item", "Reason", "Category"]]

        def style_priority(row):
            priority = str(row.get("Priority", ""))
            if priority == "High":
                color = "background-color: #ffe5e5; color: #7f1d1d; font-weight: 700;"
            elif priority == "Medium":
                color = "background-color: #ffedd5; color: #7c2d12; font-weight: 700;"
            elif priority == "Helpful":
                color = "background-color: #d9f2ff; color: #0f3f66; font-weight: 700;"
            elif priority == "Added by User":
                color = "background-color: #f3e8ff; color: #581c87; font-weight: 700;"
            else:
                color = ""
            return [color for _ in row.index]

        st.dataframe(
            grocery_df.style.apply(style_priority, axis=1),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No automatic grocery ideas yet. You can still add your own items below.")

    st.markdown("**Add your own grocery items**")
    with st.form(f"manual_grocery_form_{user_id}"):
        manual_entry = st.text_input(
            "Type ingredient or item",
            placeholder="Example: eggs, rice, yogurt",
            key=f"manual_grocery_entry_{user_id}",
        )
        add_manual = st.form_submit_button("Add to Grocery List")

    if add_manual:
        new_items = [item.strip().title() for item in re.split(r",|;|\n", manual_entry) if item.strip()]
        existing_keys = {normalize_text(item) for item in st.session_state[manual_key]}

        for item in new_items:
            item_key = normalize_text(item)
            if item_key and item_key not in existing_keys:
                st.session_state[manual_key].append(item)
                existing_keys.add(item_key)

        if new_items:
            st.success("Item added to your grocery list.")
            st.rerun()
        else:
            st.warning("Please type at least one item before adding.")

    if st.session_state[manual_key]:
        col_clear, col_spacer = st.columns([1, 3])
        with col_clear:
            if st.button("Clear Added Items", key=f"clear_manual_grocery_{user_id}"):
                st.session_state[manual_key] = []
                st.rerun()

def show_next_best_action(pantry_df):
    st.subheader("Next Best Action")

    if pantry_df.empty:
        st.info("Add at least a few pantry items first. Then Smart Pantry can help you plan meals and grocery needs.")
        return

    expiring_rows = []
    for _, row in pantry_df.iterrows():
        days_left = get_days_until_expiration(row["expiration_date"])
        if days_left <= 4:
            expiring_rows.append((days_left, row))

    if expiring_rows:
        expiring_rows.sort(key=lambda item: item[0])
        days_left, row = expiring_rows[0]
        item_name = str(row["item_name"]).title()
        if days_left < 0:
            st.warning(f"Check {item_name} first. It appears to be expired, so mark it discarded if it cannot be used safely.")
        elif days_left <= 1:
            st.warning(f"Use {item_name} first. It needs attention immediately.")
        else:
            st.info(f"Plan a meal using {item_name}. It expires in {days_left} days.")
        return

    category_counts = pantry_df["category"].fillna("Other").apply(clean_category_value).value_counts()
    if not category_counts.empty:
        lowest_category = category_counts.idxmin()
        st.info(f"Your pantry looks okay right now. To create more meal options, consider adding more {lowest_category.lower()} items next time you shop.")
    else:
        st.info("Your pantry looks okay right now. Keep updating items after cooking so the recommendations stay accurate.")


def show_home():
    st.markdown(
        """
        <div class="friendly-note">
            Let’s see what’s in your pantry today.
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state["user"]["id"]

    pre_done = has_completed_survey_cached(user_id, "Pre-Study")
    post_done = has_completed_survey_cached(user_id, "Post-Study")
    pantry_df = get_user_pantry_cached(user_id)

    total_usable_quantity = 0

    if not pantry_df.empty:
        total_usable_quantity = pantry_df["quantity"].astype(float).sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Pre-Study Survey", "Completed" if pre_done else "Not Completed")

    with col2:
        st.metric("Available Pantry Items", len(pantry_df))

    with col3:
        st.metric("Total Usable Amounts", format_number(total_usable_quantity))

    with col4:
        st.metric("Post-Study Survey", "Completed" if post_done else "Not Completed")

    top_left, top_right = st.columns([1.2, 1])

    with top_left:
        show_pantry_category_pie(pantry_df)

    with top_right:
        render_expiration_alerts(pantry_df)

    show_future_grocery_list(pantry_df)

def show_profile():
    st.title("My Profile and Preferences")

    user_id = st.session_state["user"]["id"]
    profile = get_user_profile_cached(user_id)

    allergies = st.text_area(
        "Allergies",
        value=profile["allergies"],
        placeholder="Example: onions, mushrooms, peanuts",
    )

    disliked_ingredients = st.text_area(
        "Disliked Ingredients",
        value=profile["disliked_ingredients"],
        placeholder="Example: olives, tuna, spinach",
    )

    preferred_meal_types = st.multiselect(
        "Preferred Meal Types",
        ["Breakfast", "Lunch", "Dinner", "Snack"],
        default=[
            meal_type for meal_type in ["Breakfast", "Lunch", "Dinner", "Snack"]
            if meal_type.lower() in profile["preferred_meal_types"].lower()
        ],
    )

    cuisine_options = get_profile_cuisine_options()
    preferred_cuisine_types = st.multiselect(
        "Preferred Cuisine Types",
        cuisine_options,
        default=[
            cuisine for cuisine in cuisine_options
            if cuisine.lower() in profile.get("preferred_cuisine_types", "").lower()
        ] or ["No Preference"],
        help="This helps Smart Pantry rank meals closer to what the participant actually likes. It will not completely block other useful meals."
    )

    if st.button("Save Profile"):
        update_user_profile(
            user_id,
            allergies,
            disliked_ingredients,
            ", ".join(preferred_meal_types),
            ", ".join(preferred_cuisine_types),
        )
        clear_user_cache(user_id)
        st.success("Profile updated.")


SURVEY_QUESTIONS = {
    "Pre-Study": [
        ("pre_pantry_awareness", "I usually know what food items I already have in my pantry, fridge, or cabinets."),
        ("pre_expiration_awareness", "I usually know which food items are getting close to expiring."),
        ("pre_avoid_duplicate_buying", "My current pantry or meal planning method helps me avoid buying food I already have."),
        ("pre_meal_planning_support", "My current method helps me decide what meals I can make with ingredients I already own."),
        ("pre_use_before_expiration", "My current method helps me use food before it expires."),
        ("pre_confidence_planning", "I feel confident planning meals based on what I already have at home."),
        ("pre_use_before_buying", "I usually try to use ingredients I already have before buying more groceries."),
        ("pre_method_easy_updated", "My current pantry tracking or meal planning method is easy for me to keep updated."),
        ("pre_realistic_meal_ideas", "My current method gives me meal ideas that are realistic for my household."),
        ("pre_prior_app_helped", "I have used a pantry tracking, grocery list, or recipe recommendation app before that helped me manage food at home."),
    ],
    "Post-Study": [
        ("post_pantry_awareness", "Smart Pantry helped me better understand what food items I already had."),
        ("post_expiration_awareness", "Smart Pantry helped me notice which items were getting close to expiring."),
        ("post_meal_planning", "Smart Pantry helped me plan meals using ingredients already in my pantry."),
        ("post_recommendation_usefulness", "Smart Pantry gave meal recommendations that felt realistic and useful."),
        ("post_use_before_buying", "Smart Pantry helped me use ingredients before buying more groceries."),
        ("post_reduce_forgetting", "Smart Pantry helped reduce the chance of me forgetting about food I already had."),
        ("post_smart_score_understanding", "The Smart Score helped me understand why a meal was recommended."),
        ("post_substitution_helpfulness", "The substitution options made the meal recommendations more helpful."),
        ("post_easier_than_previous", "Compared to my previous method, Smart Pantry made pantry management easier."),
        ("post_more_ingredient_use", "Compared to my previous method, Smart Pantry helped me use more ingredients I already owned."),
    ],
}

OPEN_ENDED_QUESTIONS = [
    ("open_notice", "What did Smart Pantry help you notice about your pantry, grocery habits, or meal planning?"),
    ("open_feature", "Which Smart Pantry feature was the most useful to you, and why?"),
    ("open_recommendation_used", "Did any meal recommendation help you use an ingredient you may not have used otherwise? Please explain."),
    ("open_compare", "How did Smart Pantry compare to your previous way of tracking groceries, planning meals, or finding recipes?"),
    ("open_improve", "What would make Smart Pantry easier or more useful for you to keep using?"),
]


def show_survey(survey_type):
    st.title(survey_type)

    user_id = st.session_state["user"]["id"]

    if has_completed_survey_cached(user_id, survey_type):
        st.info(f"You have already completed the {survey_type.lower()}.")
        return

    st.write("Rate each statement from 1 to 10.")
    st.caption("1 = Strongly Disagree / Not Useful, 10 = Strongly Agree / Extremely Useful")

    responses = {}
    for key, question in SURVEY_QUESTIONS.get(survey_type, SURVEY_QUESTIONS["Pre-Study"]):
        responses[key] = st.slider(question, 1, 10, 5, key=f"{survey_type}_{key}")

    if survey_type == "Pre-Study":
        current_method = st.selectbox(
            "How do you currently manage your pantry or groceries?",
            [
                "Memory",
                "Handwritten list",
                "Phone notes",
                "Spreadsheet",
                "Grocery list app",
                "Recipe app",
                "SuperCook",
                "Samsung Food",
                "Yummly",
                "Mealime",
                "I do not currently track pantry items",
                "Other",
            ],
        )
        comments = ""
    else:
        current_method = "Post-Study"
        st.subheader("Open-Ended Questions")
        open_responses = {}
        for key, question in OPEN_ENDED_QUESTIONS:
            open_responses[key] = st.text_area(question, key=f"{survey_type}_{key}")
        responses.update(open_responses)
        comments = build_open_ended_comment_summary(open_responses)

    if st.button(f"Submit {survey_type}"):
        save_survey(
            user_id,
            survey_type,
            responses.get("pre_pantry_awareness", responses.get("post_pantry_awareness", 5)),
            responses.get("pre_realistic_meal_ideas", responses.get("post_recommendation_usefulness", 5)),
            responses.get("pre_use_before_buying", responses.get("post_more_ingredient_use", 5)),
            responses.get("pre_method_easy_updated", responses.get("post_easier_than_previous", 5)),
            current_method,
            comments,
            survey_responses=json.dumps(responses, ensure_ascii=False),
        )
        clear_user_cache(user_id)
        st.success(f"{survey_type} submitted.")
        st.rerun()

def show_pantry():
    st.title("My Pantry")
    st.markdown(
        """
        <div class="friendly-note">
            Let’s gather your main ingredients. You do not need to add every spice or seasoning unless you want.
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state["user"]["id"]

    st.subheader("Add Pantry Item")

    st.markdown(
        """
        <div class="smart-card smart-card-orange">
            Add a reasonable usable amount. It does not have to be perfect.
            Count easy items like eggs or slices of bread. For bags, boxes, jars, or packs,
            estimate by servings or pieces. If the package has more than about 15 small pieces,
            use a simple estimate like servings, cups, or "about half left" converted into a number.
        </div>
        """,
        unsafe_allow_html=True,
    )

    barcode_input = st.text_input(
        "Barcode / UPC (optional)",
        placeholder="Type or paste a barcode/UPC, or leave blank and use the dropdown below",
        help="Smart Pantry checks app/data/barcode_lookup.csv. If the barcode is found, it fills the item name and pantry details into the same Add Pantry Item form.",
        key="add_pantry_barcode_input",
    )

    cleaned_barcode = clean_barcode_value(barcode_input)
    barcode_match = get_barcode_lookup_item(cleaned_barcode)

    if cleaned_barcode and barcode_match:
        st.success(f"Barcode found: {barcode_match.get('item_name', '').title()}")
        st.caption(
            f"Product source match: {barcode_match.get('product_name', 'Not listed')}"
            + (f" | Brand: {barcode_match.get('brand', 'Not listed')}" if barcode_match.get('brand') else "")
        )
    elif cleaned_barcode:
        st.warning("Barcode was not found in the lookup file. You can still use the dropdown or type the item manually below.")

    default_item_name = barcode_match.get("item_name", "") if barcode_match else ""
    default_category = clean_category_value(barcode_match.get("category", "Other")) if barcode_match else "Other"
    default_unit = str(barcode_match.get("unit", "item")).strip() if barcode_match else "servings"
    default_container = str(barcode_match.get("container_type", "item")).strip() if barcode_match else "item"

    try:
        default_quantity = float(barcode_match.get("quantity", 1.0)) if barcode_match else 1.0
    except Exception:
        default_quantity = 1.0

    if default_category not in CATEGORY_OPTIONS:
        default_category = "Other"

    if default_unit not in USABLE_UNITS:
        default_unit = "servings"

    if default_container not in CONTAINER_TYPES:
        default_container = "item"

    if barcode_match and st.session_state.get("last_barcode_prefill") != cleaned_barcode:
        st.session_state["add_pantry_custom_item"] = default_item_name
        st.session_state["add_pantry_category"] = default_category
        st.session_state["add_pantry_container_type"] = default_container
        st.session_state["add_pantry_quantity"] = default_quantity
        st.session_state["add_pantry_unit"] = default_unit
        st.session_state["last_barcode_prefill"] = cleaned_barcode

    st.caption("Use one method: enter a barcode/UPC, choose a common item from the dropdown, or type your own item name.")

    with st.form("add_pantry_item_form"):
        selected_item = st.selectbox(
            "Choose common item",
            [""] + get_pantry_item_dropdown_options(),
            key="add_pantry_selected_item",
        )
        custom_item = st.text_input(
            "Or type/edit item name",
            value=st.session_state.get("add_pantry_custom_item", default_item_name),
            key="add_pantry_custom_item",
        )

        category = st.selectbox(
            "Category",
            CATEGORY_OPTIONS,
            index=CATEGORY_OPTIONS.index(st.session_state.get("add_pantry_category", default_category)) if st.session_state.get("add_pantry_category", default_category) in CATEGORY_OPTIONS else CATEGORY_OPTIONS.index("Other"),
            key="add_pantry_category",
        )

        container_type = st.selectbox(
            "Container Type",
            CONTAINER_TYPES,
            index=CONTAINER_TYPES.index(st.session_state.get("add_pantry_container_type", default_container)) if st.session_state.get("add_pantry_container_type", default_container) in CONTAINER_TYPES else CONTAINER_TYPES.index("item"),
            help="Example: carton, loaf, bottle, box, bag, can, pack.",
            key="add_pantry_container_type",
        )

        quantity = st.number_input(
            "How many usable amounts are in this item?",
            min_value=0.0,
            value=float(st.session_state.get("add_pantry_quantity", default_quantity)),
            step=0.5,
            help="Example: eggs = 12, bread slices = 20, milk cups = 8.",
            key="add_pantry_quantity",
        )

        unit = st.selectbox(
            "Usable Unit",
            USABLE_UNITS,
            index=USABLE_UNITS.index(st.session_state.get("add_pantry_unit", default_unit)) if st.session_state.get("add_pantry_unit", default_unit) in USABLE_UNITS else USABLE_UNITS.index("servings"),
            help="Example: eggs, slices, cups, servings, pieces.",
            key="add_pantry_unit",
        )

        expiration_date = st.date_input("Expiration Date", key="add_pantry_expiration_date")

        submitted = st.form_submit_button("Add Item")

        if submitted:
            item_name = custom_item.strip() if custom_item.strip() else selected_item

            if not item_name:
                st.error("Please enter a barcode, choose an item, or type an item name.")
            elif quantity <= 0:
                st.error("Please enter a usable quantity greater than zero.")
            else:
                add_pantry_item(
                    user_id,
                    item_name,
                    category,
                    quantity,
                    unit,
                    expiration_date.isoformat(),
                    container_type,
                )
                clear_user_cache(user_id)

                if cleaned_barcode and barcode_match:
                    st.success(
                        f"{item_name.title()} added from barcode lookup. "
                        f"This {container_type} contains {format_number(quantity)} {unit}."
                    )
                else:
                    st.success(
                        f"{item_name.title()} added to your pantry. "
                        f"This {container_type} contains {format_number(quantity)} {unit}. "
                        f"When a meal uses this item, only the amount used will be removed."
                    )

                for key in [
                    "add_pantry_barcode_input",
                    "add_pantry_custom_item",
                    "add_pantry_selected_item",
                    "last_barcode_prefill",
                ]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    st.subheader("Current Pantry Items")

    pantry_df = get_user_pantry_cached(user_id)

    if pantry_df.empty:
        st.info("No pantry items added yet.")
        return

    st.write(
        "You can correct mistakes directly in the table below. Edit the item name, category, amount, unit, "
        "container type, or expiration date, then click **Save Table Changes**."
    )

    editable_df = pantry_df.copy()
    editable_df["days_left"] = editable_df["expiration_date"].apply(get_days_until_expiration)
    editable_df["pantry_amount"] = editable_df.apply(
        lambda row: f"{format_number(row['quantity'])} {row['unit']} in {row.get('container_type', 'item')}",
        axis=1,
    )

    table_df_with_ids = editable_df[
        [
            "id",
            "item_name",
            "category",
            "quantity",
            "unit",
            "container_type",
            "expiration_date",
            "days_left",
            "pantry_amount",
        ]
    ].copy()

    # Keep the Supabase UUID hidden from participants, but save it in the background
    # so edits still update the correct pantry item.
    hidden_pantry_ids = table_df_with_ids["id"].astype(str).tolist()

    table_df = table_df_with_ids.drop(columns=["id"], errors="ignore")
    table_df["category"] = table_df["category"].apply(get_category_display)

    # Streamlit's DateColumn works best when the column contains real date values,
    # not plain strings from SQLite/Supabase. This keeps the table from failing to populate.
    table_df["expiration_date"] = pd.to_datetime(
        table_df["expiration_date"],
        errors="coerce",
    ).dt.date

    edited_table = st.data_editor(
        table_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="editable_current_pantry_table",
        disabled=["days_left", "pantry_amount"],
        column_config={
            "item_name": st.column_config.TextColumn("Item Name", required=True),
            "category": st.column_config.SelectboxColumn(
                "Category",
                options=CATEGORY_DISPLAY_OPTIONS,
                required=True,
            ),
            "quantity": st.column_config.NumberColumn(
                "Quantity",
                min_value=0.0,
                step=0.5,
                required=True,
            ),
            "unit": st.column_config.SelectboxColumn(
                "Unit",
                options=USABLE_UNITS,
                required=True,
            ),
            "container_type": st.column_config.SelectboxColumn(
                "Container",
                options=CONTAINER_TYPES,
                required=True,
            ),
            "expiration_date": st.column_config.DateColumn(
                "Expiration Date",
                format="YYYY-MM-DD",
                required=True,
            ),
            "days_left": st.column_config.NumberColumn("Days Left", disabled=True),
            "pantry_amount": st.column_config.TextColumn("Pantry Amount", disabled=True),
        },
    )

    if st.button("Save Table Changes"):
        changes_saved = 0

        for row_index, edited_row in edited_table.iterrows():
            pantry_item_id = hidden_pantry_ids[int(row_index)]
            matching_original_rows = pantry_df[pantry_df["id"].astype(str) == str(pantry_item_id)]

            if matching_original_rows.empty:
                st.error("One pantry item could not be matched to its saved record. Please refresh and try again.")
                return

            original_row = matching_original_rows.iloc[0]

            edited_item_name = str(edited_row["item_name"]).strip()
            edited_category = clean_category_value(edited_row["category"])
            edited_quantity = float(edited_row["quantity"])
            edited_unit = str(edited_row["unit"]).strip()
            edited_container_type = str(edited_row["container_type"]).strip()

            raw_expiration_date = edited_row["expiration_date"]
            if pd.isna(raw_expiration_date):
                st.error(f"{edited_item_name.title()} needs a valid expiration date.")
                return

            if isinstance(raw_expiration_date, datetime):
                edited_expiration_date = raw_expiration_date.date().isoformat()
            elif hasattr(raw_expiration_date, "isoformat"):
                edited_expiration_date = raw_expiration_date.isoformat()[:10]
            else:
                edited_expiration_date = str(raw_expiration_date)[:10]

            if not edited_item_name:
                st.error("One pantry item has a blank name. Please fix it before saving.")
                return

            if edited_quantity <= 0:
                st.error(f"{edited_item_name.title()} must have a quantity greater than zero.")
                return

            changed = (
                normalize_text(original_row["item_name"]) != normalize_text(edited_item_name)
                or str(original_row["category"]) != edited_category
                or float(original_row["quantity"]) != edited_quantity
                or str(original_row["unit"]) != edited_unit
                or str(original_row["container_type"]) != edited_container_type
                or str(original_row["expiration_date"])[:10] != edited_expiration_date
            )

            if changed:
                update_pantry_item(
                    user_id,
                    pantry_item_id,
                    edited_item_name,
                    edited_category,
                    edited_quantity,
                    edited_unit,
                    edited_expiration_date,
                    edited_container_type,
                )
                changes_saved += 1

        if changes_saved == 0:
            st.info("No table changes were detected.")
        else:
            clear_user_cache(user_id)
            st.success(f"Saved {changes_saved} pantry item update(s).")
            st.rerun()




def show_recommendation_color_chart(make_now_count=0, smart_swap_count=0, more_ideas_count=0):
    return

def show_recommendations():
    st.title("Meal Recommendations")
    st.markdown(
        """
        <div class="friendly-note">
            Here are meals ideas based on what is already in your pantry. Lets take a look!!!!
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state["user"]["id"]
    pantry_df = get_user_pantry_cached(user_id)
    profile = get_user_profile_cached(user_id)

    if pantry_df.empty:
        st.info("Add pantry items first to receive meal recommendations.")
        return

    meal_type_filter = st.selectbox(
        "Filter by meal type",
        ["All", "Breakfast", "Lunch", "Dinner", "Snack"],
    )

    recommendations = get_recommendations(pantry_df, profile, meal_type_filter)

    with st.expander("➕ Add Your Own Recipe Idea", expanded=False):
        st.write(
            "If you do not see a recommendation you like, you can add the meal you already have in mind. "
            "This saves to your recommendation history so it still counts as pantry planning activity."
        )

        custom_recipe_name = st.text_input(
            "Recipe or meal name",
            placeholder="Example: Chicken Alfredo, Tuna Melt, Egg Fried Rice",
            key="custom_recipe_name",
        )

        custom_meal_type = st.selectbox(
            "Meal type",
            ["Breakfast", "Lunch", "Dinner", "Snack"],
            key="custom_recipe_meal_type",
        )

        custom_ingredients = st.text_area(
            "Ingredients you plan to use",
            placeholder="Example: chicken, pasta, alfredo sauce, broccoli",
            key="custom_recipe_ingredients",
        )

        custom_notes = st.text_area(
            "Notes or reason for adding this recipe — 250 words max",
            placeholder="Example: I already know how to make this and I have most of the ingredients.",
            key="custom_recipe_notes",
        )

        valid_custom_notes, custom_notes_msg = validate_250_words(custom_notes)
        st.caption(custom_notes_msg)

        if st.button("Save My Recipe Idea", key="save_custom_recipe_idea"):
            if not custom_recipe_name.strip():
                st.error("Please enter a recipe or meal name.")
            elif not custom_ingredients.strip():
                st.error("Please enter at least one ingredient.")
            elif not valid_custom_notes:
                st.error(custom_notes_msg)
            else:
                ingredient_list = [
                    normalize_text(item)
                    for item in re.split(r",|;|\n", custom_ingredients)
                    if normalize_text(item)
                ]
                note = (
                    "Participant added their own recipe idea. "
                    f"Ingredients planned: {', '.join(ingredient_list)}. "
                    f"{custom_notes}"
                ).strip()
                save_recommendation_log(
                    user_id,
                    f"Custom Recipe: {custom_recipe_name.strip()}",
                    custom_meal_type,
                    0,
                    ingredient_list,
                    [],
                    feedback=note,
                    used_recommendation="No",
                )
                st.success("Your recipe idea was saved to Recommendation History.")
                st.rerun()

    make_now = [item for item in recommendations if item["recommendation_category"] == "Meals You Can Make Now"]
    almost = [item for item in recommendations if item["recommendation_category"] == "Smart Swaps / Almost There"]
    more_ideas = [item for item in recommendations if item["recommendation_category"] == "Need More Ingredients"]

    ready_options = make_now + almost

    tab_ready, tab_more, tab_elsewhere = st.tabs(
        [
            f"Make Now / Smart Swaps ({len(ready_options)})",
            f"More Ideas ({len(more_ideas)})",
            "Used Elsewhere / Discarded",
        ]
    )

    def build_ingredient_choices(item, selected_substitutions):
        ingredient_choices = []
        recommended_amount_lookup = {}
        unit_lookup = {}
        available_lookup = {}
        label_to_ingredient = {}
        label_to_pantry_id = {}

        aggregated = {}

        for requirement in item["requirements"]:
            original_ingredient = requirement["ingredient"]
            pantry_ingredient = selected_substitutions.get(original_ingredient, original_ingredient)
            pantry_row = find_pantry_row_for_item(pantry_df, pantry_ingredient)

            if pantry_row is None:
                continue

            pantry_id = str(pantry_row["id"])
            pantry_name = normalize_text(pantry_row.get("item_name", pantry_ingredient))
            available_quantity = float(pantry_row.get("quantity", 0) or 0)
            pantry_unit = pantry_row.get("unit", requirement["unit"])
            suggested_amount = float(requirement.get("amount", 1) or 1)

            if pantry_id not in aggregated:
                aggregated[pantry_id] = {
                    "pantry_name": pantry_name,
                    "suggested_amount": 0.0,
                    "available_quantity": available_quantity,
                    "unit": pantry_unit,
                }

            aggregated[pantry_id]["suggested_amount"] += suggested_amount
            aggregated[pantry_id]["available_quantity"] = available_quantity
            aggregated[pantry_id]["unit"] = pantry_unit

        for pantry_id, info in aggregated.items():
            pantry_name = info["pantry_name"]
            suggested_amount = min(info["suggested_amount"], info["available_quantity"])
            label = (
                f"{pantry_name} — suggested {format_number(suggested_amount)} "
                f"{info['unit']}, available {format_number(info['available_quantity'])} {info['unit']}"
            )

            ingredient_choices.append(label)
            recommended_amount_lookup[label] = float(suggested_amount)
            unit_lookup[label] = info["unit"]
            available_lookup[label] = info["available_quantity"]
            label_to_ingredient[label] = pantry_name
            label_to_pantry_id[label] = pantry_id

        return ingredient_choices, recommended_amount_lookup, unit_lookup, available_lookup, label_to_ingredient, label_to_pantry_id


    def render_recommendation_list(items, tab_label):
        if not items:
            st.info(f"No meals in {tab_label.lower()} yet.")
            return

        if "Make Now" in tab_label:
            st.markdown(
                """
                <div class="recommendation-section-note section-green">
                    🟢 These meals use exact pantry ingredients and should be the fastest options to make now.
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif "Smart Swaps" in tab_label:
            st.markdown(
                """
                <div class="recommendation-section-note section-blue">
                    🔵 These meals need a realistic swap or amount adjustment, so review the Smart Swap note first.
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif "More Ideas" in tab_label:
            st.markdown(
                """
                <div class="recommendation-section-note section-orange">
                    🟠 These are still useful ideas, but you may need extra ingredients before making them.
                </div>
                """,
                unsafe_allow_html=True,
            )

        for index, item in enumerate(items):
            recipe = item["recipe"]
            safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", f"{tab_label}_{index}_{recipe['name']}")

            exact_percent = item.get("exact_match_percent", item.get("match_percent", 0))
            coverage_percent = item.get("coverage_percent", exact_percent)
            if item.get("recommendation_category") == "Smart Swaps / Almost There":
                tier_label = "🔵 Smart Swap Match"
            elif item.get("recommendation_category") == "Meals You Can Make Now":
                tier_label = "🟢 Make Now"
            else:
                tier_label = item.get("match_tier", get_match_tier(exact_percent))

            with st.expander(
                f"{recipe['name']} — {tier_label} "
                f"— Smart Score: {item['score']}/100 "
                f"— Exact Match: {exact_percent}% "
                f"— Coverage With Swaps: {coverage_percent}%"
            ):
                st.write(f"**Meal Type:** {recipe['meal_type']}")
                st.write(f"**Cuisine Type:** {recipe.get('cuisine_type', 'Not listed')}")
                st.write(f"**Cook Time:** {recipe['cook_time']}")
                st.write(f"**Calories:** {recipe['calories']}")
                st.write(f"**Protein:** {recipe['protein']}g")
                st.write(f"**Carbs:** {recipe['carbs']}g")
                st.write(f"**Fat:** {recipe['fat']}g")
                if item.get("ml_health_score") is not None:
                    st.write(f"**Nutrition Fit:** {format_number(item['ml_health_score'])}/15")
                if item.get("recipe_quality_score") is not None:
                    st.write(f"**Everyday Recipe Fit:** {item['recipe_quality_score']}/100")

                st.write(f"**Exact Pantry Match:** {exact_percent}%")
                st.write(f"**Coverage With Smart Swaps:** {coverage_percent}%")
                if item.get("recommendation_category") == "Smart Swaps / Almost There":
                    st.info("This is in Smart Swaps because at least one ingredient is not an exact make-now match, even if the meal can still work.")

                st.write("**Ingredients Needed:**")
                for requirement in item["requirements"]:
                    st.write(f"- {format_number(requirement['amount'])} {requirement['unit']} {requirement['ingredient']}")

                st.write("**Exact Ingredients Available in Your Pantry:**")
                st.write(", ".join(item["matched_ingredients"]) if item["matched_ingredients"] else "None")

                selected_substitutions = {}

                if item["substitutions"]:
                    st.subheader("Smart Swap Options")
                    for sub_index, substitution in enumerate(item["substitutions"]):
                        missing = substitution["missing"]
                        substitute = substitution["substitute"]
                        substitution_type = substitution.get("substitution_type", "functional_substitute")
                        message = substitution.get(
                            "message",
                            f"This recipe calls for {missing}. You have {substitute}."
                        )

                        if substitution_type == "same_food_family":
                            st.success(f"🍗 Smart Swap: {message}")
                        elif substitution_type == "quantity_adjustment":
                            st.info(f"🥚 Amount Adjustment: {message}")
                        elif substitution_type == "optional_flavor_substitute":
                            st.warning(f"🧅 Flavor Swap: {message}")
                        else:
                            st.info(f"🔁 Smart Swap: {message}")

                        use_sub = st.checkbox(
                            f"Use {substitute} for {missing}?",
                            value=True,
                            key=f"sub_{safe_key}_{sub_index}",
                        )
                        if use_sub:
                            selected_substitutions[missing] = substitute

                if item.get("missing_without_substitution"):
                    st.info("Still missing: " + ", ".join(item["missing_without_substitution"]))

                if item["warning_items"]:
                    st.subheader("Allergy or Preference Advice")
                    for warning in item["warning_items"]:
                        st.warning(warning["message"])
                        substitute = find_substitution(warning["ingredient"], pantry_df, 1)
                        if substitute:
                            st.info(f"Suggested substitute for {warning['ingredient']}: {substitute}")
                        else:
                            st.info(f"You may remove {warning['ingredient']} or use a safe substitute of your choice.")

                if item["expiring_ingredients"]:
                    st.warning("Expiring soon: " + ", ".join(item["expiring_ingredients"]))

                st.write("**Why this meal?**")
                for reason in build_why_this_meal(item):
                    st.write(f"- {reason}")

                st.write("**Instructions:**")
                st.write(recipe["instructions"])

                st.subheader("Made This Meal")

                matched = item["matched_ingredients"] + [
                    f"{key} -> {value}" for key, value in selected_substitutions.items()
                ]

                (
                    ingredient_choices,
                    recommended_amount_lookup,
                    unit_lookup,
                    available_lookup,
                    label_to_ingredient,
                    label_to_pantry_id,
                ) = build_ingredient_choices(item, selected_substitutions)

                if not ingredient_choices:
                    st.info("No pantry ingredients from this recipe could be matched to exact pantry rows yet.")
                else:
                    st.write(
                        "Select the ingredients you actually used, then enter the real amount used. "
                        "The pantry amount will update after you submit."
                    )

                    used_labels = st.multiselect(
                        "Ingredients used in this meal",
                        ingredient_choices,
                        default=ingredient_choices,
                        key=f"made_used_items_{safe_key}",
                    )

                    actual_amount_lookup = {}

                    if used_labels:
                        st.write("**Actual amounts used**")

                        for used_index, used_label in enumerate(used_labels):
                            ingredient_name = label_to_ingredient[used_label]
                            suggested_amount = recommended_amount_lookup.get(used_label, 1.0)
                            available_amount = available_lookup.get(used_label, suggested_amount)
                            ingredient_unit = unit_lookup.get(used_label, "serving")
                            default_amount = min(suggested_amount, available_amount)

                            safe_used_key = re.sub(
                                r"[^a-zA-Z0-9_]",
                                "_",
                                f"{tab_label}_{index}_{used_index}_{label_to_pantry_id.get(used_label, ingredient_name)}_{ingredient_name}_{used_label}",
                            )

                            actual_amount = st.number_input(
                                f"How much {ingredient_name} did you actually use? ({ingredient_unit})",
                                min_value=0.0,
                                max_value=float(available_amount),
                                value=float(default_amount),
                                step=0.5,
                                key=f"actual_amount_{safe_used_key}",
                            )

                            actual_amount_lookup[used_label] = actual_amount

                    made_feedback = st.text_area(
                        "Feedback",
                        placeholder="Example: I made sandwiches and used 8 slices of bread instead of the suggested 2.",
                        key=f"made_feedback_{safe_key}",
                    )
                    valid_made_feedback, made_feedback_msg = validate_250_words(made_feedback)
                    st.caption(made_feedback_msg)

                    if st.button("Submit Made Meal", key=f"submit_made_meal_{safe_key}"):
                        if not used_labels:
                            st.error("Please select at least one ingredient you used.")
                        elif any(amount <= 0 for amount in actual_amount_lookup.values()):
                            st.error("Every selected ingredient must have an amount greater than zero.")
                        elif not valid_made_feedback:
                            st.error(made_feedback_msg)
                        else:
                            selected_items = [label_to_ingredient[label] for label in used_labels]
                            selected_usage_rows = [
                                {
                                    "pantry_item_id": label_to_pantry_id[label],
                                    "item_name": label_to_ingredient[label],
                                    "amount_used": actual_amount_lookup[label],
                                }
                                for label in used_labels
                            ]
                            amount_note = ", ".join(
                                [
                                    f"{format_number(actual_amount_lookup[label])} {unit_lookup.get(label, '')} {label_to_ingredient[label]}"
                                    for label in used_labels
                                ]
                            )
                            note = (
                                f"Made this recommended meal. Actual amounts used: {amount_note}. "
                                f"{made_feedback}"
                            ).strip()

                            save_recommendation_log(
                                user_id,
                                recipe["name"],
                                recipe["meal_type"],
                                item["score"],
                                selected_items,
                                item["expiring_ingredients"],
                                feedback=note,
                                used_recommendation="Yes",
                            )

                            messages = mark_selected_pantry_rows_used(
                                user_id,
                                selected_usage_rows,
                                "Used in recommended meal",
                                note,
                            )

                            for message in messages:
                                if "not found" in message.lower() or "not enough" in message.lower():
                                    st.error(message)
                                else:
                                    st.success(message)

                            st.success("Meal feedback saved and the exact pantry amounts were updated.")
                            st.rerun()

                with st.expander("Save, dislike, or skip this recommendation", expanded=False):
                    general_feedback = st.text_area(
                        "Optional feedback — 250 words max",
                        placeholder="Example: I saved this for later, I did not like it, or I did not use it.",
                        key=f"general_feedback_{safe_key}",
                    )
                    valid_general_feedback, general_feedback_msg = validate_250_words(general_feedback)
                    st.caption(general_feedback_msg)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("Save for Later", key=f"save_{safe_key}"):
                            if not valid_general_feedback:
                                st.error(general_feedback_msg)
                            else:
                                note = f"Saved recommendation. {general_feedback}".strip()
                                save_recommendation_log(
                                    user_id,
                                    recipe["name"],
                                    recipe["meal_type"],
                                    item["score"],
                                    matched,
                                    item["expiring_ingredients"],
                                    feedback=note,
                                    used_recommendation="No",
                                )
                                clear_user_cache(user_id)
                                st.success("Recommendation saved to your history.")

                    with col2:
                        if st.button("Did Not Use", key=f"did_not_use_{safe_key}"):
                            if not valid_general_feedback:
                                st.error(general_feedback_msg)
                            else:
                                note = f"Did not use this recommendation. {general_feedback}".strip()
                                save_recommendation_log(
                                    user_id,
                                    recipe["name"],
                                    recipe["meal_type"],
                                    item["score"],
                                    matched,
                                    item["expiring_ingredients"],
                                    feedback=note,
                                    used_recommendation="No",
                                )
                                clear_user_cache(user_id)
                                st.success("Feedback saved as not used.")

                    with col3:
                        if st.button("Do Not Like", key=f"dislike_{safe_key}"):
                            if not valid_general_feedback:
                                st.error(general_feedback_msg)
                            else:
                                note = f"Did not like this recommendation. {general_feedback}".strip()
                                save_recommendation_log(
                                    user_id,
                                    recipe["name"],
                                    recipe["meal_type"],
                                    item["score"],
                                    matched,
                                    item["expiring_ingredients"],
                                    feedback=note,
                                    used_recommendation="No",
                                )
                                clear_user_cache(user_id)
                                st.success("Feedback saved. This helps evaluate recommendation usefulness.")

    def render_used_elsewhere_and_discard_tab():
        st.subheader("Used Ingredients Elsewhere")
        st.write(
            "Use this when an ingredient from the pantry was used in a meal that was not one of the recommendations. "
            "This updates the pantry amount and saves the usage for the study data."
        )

        pantry_options = {}
        for _, row in pantry_df.iterrows():
            label = (
                f"{row['item_name']} — {format_number(row['quantity'])} {row['unit']} left, "
                f"expires {row['expiration_date']}"
            )
            pantry_options[label] = {
                "id": str(row["id"]),
                "name": row["item_name"],
                "quantity": float(row["quantity"] or 0),
                "unit": row["unit"],
            }

        if not pantry_options:
            st.info("No pantry items are available right now.")
        else:
            elsewhere_label = st.selectbox(
                "Which pantry ingredient did you use?",
                list(pantry_options.keys()),
                key="global_elsewhere_item",
            )
            selected_elsewhere = pantry_options[elsewhere_label]

            elsewhere_amount = st.number_input(
                f"How much did you use? ({selected_elsewhere['unit']})",
                min_value=0.0,
                max_value=float(selected_elsewhere["quantity"]),
                value=min(1.0, float(selected_elsewhere["quantity"])),
                step=0.5,
                key="global_elsewhere_amount",
            )

            elsewhere_meal = st.text_input(
                "What did you use it for?",
                placeholder="Example: tacos, omelet, sandwich, lunch for kids",
                key="global_elsewhere_meal",
            )

            elsewhere_feedback = st.text_area(
                "Extra notes — 250 words max",
                placeholder="Example: I used the chicken for tacos instead of making one of the recommended meals.",
                key="global_elsewhere_feedback",
            )
            valid_elsewhere_feedback, elsewhere_feedback_msg = validate_250_words(elsewhere_feedback)
            st.caption(elsewhere_feedback_msg)

            if st.button("Submit Used Elsewhere", key="global_submit_elsewhere"):
                if elsewhere_amount <= 0:
                    st.error("Please enter an amount greater than zero.")
                elif not elsewhere_meal.strip():
                    st.error("Please say what you used it for.")
                elif not valid_elsewhere_feedback:
                    st.error(elsewhere_feedback_msg)
                else:
                    note = (
                        f"Used ingredient somewhere else. Ingredient: {selected_elsewhere['name']}. "
                        f"Amount used: {format_number(elsewhere_amount)} {selected_elsewhere['unit']}. "
                        f"Used for: {elsewhere_meal}. {elsewhere_feedback}"
                    ).strip()

                    save_recommendation_log(
                        user_id,
                        "Ingredient Used Elsewhere",
                        "Other",
                        0,
                        [selected_elsewhere["name"]],
                        [],
                        feedback=note,
                        used_recommendation="Yes",
                    )

                    messages = mark_selected_pantry_rows_used(
                        user_id,
                        [
                            {
                                "pantry_item_id": selected_elsewhere["id"],
                                "item_name": selected_elsewhere["name"],
                                "amount_used": elsewhere_amount,
                            }
                        ],
                        "Used outside recommended meal",
                        note,
                    )

                    for message in messages:
                        if "not found" in message.lower() or "not enough" in message.lower():
                            st.error(message)
                        else:
                            st.success(message)

                    clear_user_cache(user_id)
                    st.success("Ingredient use saved and pantry amount was updated.")
                    st.rerun()

        st.divider()
        st.subheader("Expired or Discarded Items")
        st.write(
            "Use this when an item is expired, almost expired, spoiled, or cannot be used. "
            "The item will be removed from the active pantry and saved for the study record."
        )

        discard_options = {}
        for _, row in pantry_df.iterrows():
            days_left = get_days_until_expiration(row["expiration_date"])
            if days_left <= 10:
                if days_left < 0:
                    status_text = f"expired {abs(days_left)} days ago"
                elif days_left == 0:
                    status_text = "expires today"
                else:
                    status_text = f"expires in {days_left} days"

                label = (
                    f"{row['item_name']} — {format_number(row['quantity'])} {row['unit']} left, {status_text}"
                )
                discard_options[label] = row["item_name"]

        if not discard_options:
            st.info("No expired or almost-expired pantry items are in the 0-10 day alert range right now.")
        else:
            discard_label = st.selectbox(
                "Which item needs to be marked expired/discarded?",
                list(discard_options.keys()),
                key="global_discard_item",
            )
            discard_item = discard_options[discard_label]

            discard_reason = st.text_area(
                "Why was it discarded? — 250 words max",
                placeholder="Example: It expired before I could use it, smelled bad, or was no longer safe.",
                key="global_discard_reason",
            )
            valid_discard_feedback, discard_feedback_msg = validate_250_words(discard_reason)
            st.caption(discard_feedback_msg)

            if st.button("Submit Discarded Item", key="global_submit_discard"):
                if not valid_discard_feedback:
                    st.error(discard_feedback_msg)
                else:
                    note = f"Expired/discarded item. Item: {discard_item}. {discard_reason}".strip()

                    save_recommendation_log(
                        user_id,
                        "Expired or Discarded Item",
                        "Other",
                        0,
                        [discard_item],
                        [discard_item],
                        feedback=note,
                        used_recommendation="No",
                    )

                    success, message = discard_selected_pantry_item(user_id, pantry_df, discard_item, note)

                    if success:
                        st.warning(message)
                        st.rerun()
                    else:
                        st.error(message)

    with tab_ready:
        if not recommendations:
            st.warning(
                "No meal matches were found yet. Add a few more pantry items or check that item names are simple, like chicken, rice, eggs, bread, or cheese."
            )
        elif not ready_options:
            st.info("No Make Now or Smart Swap meals are available yet. Check More Ideas for recipes that may need extra ingredients.")
        else:
            render_recommendation_list(ready_options, "Ready Options")

    with tab_more:
        if not recommendations:
            st.warning(
                "No extra meal ideas were found yet. Add a few more pantry items or check your item names."
            )
        else:
            render_recommendation_list(more_ideas, "More Ideas")

    with tab_elsewhere:
        render_used_elsewhere_and_discard_tab()


def show_recommendation_history():
    st.title("Recommendation History")

    user_id = st.session_state["user"]["id"]
    logs_df = get_user_recommendation_logs_cached(user_id)

    if logs_df.empty:
        st.info("No recommendation history yet.")
        return

    st.markdown(
        """
        <div class="friendly-note">
            This page shows your recent Smart Pantry activity in one clean view. It includes meals you made,
            meals made with a substitution, ingredients used somewhere else, and items that were discarded.
        </div>
        """,
        unsafe_allow_html=True,
    )

    def clean_history_value(value):
        value = str(value or "").strip()
        if not value or value.lower() == "nan":
            return ""
        return value

    def get_participant_item(row):
        meal_name = clean_history_value(row.get("meal_name", ""))
        matched = clean_history_value(row.get("matched_ingredients", ""))
        expiring = clean_history_value(row.get("expiring_ingredients", ""))

        if meal_name in ["Ingredient Used Elsewhere", "Expired or Discarded Item"]:
            if matched:
                return matched
            if expiring:
                return expiring
            return "Pantry item"

        return meal_name

    def classify_history_action(row):
        meal_name = clean_history_value(row.get("meal_name", ""))
        feedback = clean_history_value(row.get("feedback", "")).lower()
        matched = clean_history_value(row.get("matched_ingredients", "")).lower()
        used = clean_history_value(row.get("used_recommendation", ""))

        if meal_name == "Ingredient Used Elsewhere":
            return "Used Ingredient Elsewhere", "Used Elsewhere"

        if meal_name == "Expired or Discarded Item":
            return "Expired / Discarded", "Discarded"

        if "->" in matched or "substitute" in feedback or "instead of" in feedback:
            return "Made With Substitution", "Substitution"

        if used == "Yes" or "made this recommended meal" in feedback:
            return "Made Recommended Meal", "Recommended Meal"

        if "saved recommendation" in feedback:
            return "Saved Recommendation", "Saved"

        if "did not like" in feedback or "did not use" in feedback:
            return "Not Used / Feedback", "Feedback"

        return "Pantry Action", "Pantry Action"

    def format_history_date(value):
        try:
            parsed = pd.to_datetime(value)
            if pd.isna(parsed):
                return "Not listed"
            return parsed.strftime("%b %d, %Y")
        except Exception:
            return "Not listed"

    participant_view = logs_df.copy()
    participant_view["Activity"] = participant_view.apply(lambda row: classify_history_action(row)[0], axis=1)
    participant_view["Category"] = participant_view.apply(lambda row: classify_history_action(row)[1], axis=1)
    participant_view["Meal or Ingredient"] = participant_view.apply(get_participant_item, axis=1)

    date_column = "created_at" if "created_at" in participant_view.columns else None
    if date_column:
        participant_view["Date"] = participant_view[date_column].apply(format_history_date)
    else:
        participant_view["Date"] = "Not listed"

    participant_view = participant_view[["Date", "Activity", "Meal or Ingredient", "Category"]]
    participant_view = participant_view.drop_duplicates().reset_index(drop=True)

    made_count = int((participant_view["Category"] == "Recommended Meal").sum())
    substitution_count = int((participant_view["Category"] == "Substitution").sum())
    used_elsewhere_count = int((participant_view["Category"] == "Used Elsewhere").sum())
    discarded_count = int((participant_view["Category"] == "Discarded").sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Recommended Meals Made", made_count)
    with col2:
        st.metric("Made With Swaps", substitution_count)
    with col3:
        st.metric("Used Elsewhere", used_elsewhere_count)
    with col4:
        st.metric("Discarded / Expired", discarded_count)

    st.subheader("Activity Log")

    filter_options = ["All Activity"] + sorted(participant_view["Activity"].dropna().unique().tolist())
    selected_filter = st.selectbox("Filter history", filter_options)

    if selected_filter != "All Activity":
        display_df = participant_view[participant_view["Activity"] == selected_filter].copy()
    else:
        display_df = participant_view.copy()

    if display_df.empty:
        st.info("No history records match this filter yet.")
        return

    st.dataframe(
        display_df[["Date", "Activity", "Meal or Ingredient", "Category"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        <div class="friendly-note">
            This table helps show what happened after recommendations were made. That matters for the study because it connects the app suggestions to real ingredient use.
        </div>
        """,
        unsafe_allow_html=True,
    )

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")


def safe_percent(numerator, denominator):
    try:
        denominator = float(denominator)
        if denominator == 0:
            return 0
        return round((float(numerator) / denominator) * 100, 1)
    except Exception:
        return 0


def parse_survey_response_json(value):
    """Safely read the stored survey JSON so the dashboard does not show raw JSON text."""
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    try:
        text = str(value).strip()
    except Exception:
        return {}

    if not text or text.lower() in ["nan", "none", "null"]:
        return {}

    for parser in [json.loads, ast.literal_eval]:
        try:
            parsed = parser(text)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            continue

    return {}


def build_open_ended_comment_summary(open_responses):
    """Save a readable comments field while still keeping full JSON in survey_responses."""
    if not isinstance(open_responses, dict):
        return ""

    parts = []
    question_lookup = dict(OPEN_ENDED_QUESTIONS)

    for key, question in OPEN_ENDED_QUESTIONS:
        answer = str(open_responses.get(key, "") or "").strip()
        if answer:
            parts.append(f"{question} {answer}")

    if not parts:
        for key, answer in open_responses.items():
            answer = str(answer or "").strip()
            if answer:
                parts.append(f"{question_lookup.get(key, key)} {answer}")

    return "\n\n".join(parts)


def format_survey_comments(comment_value, survey_response_value=""):
    """Turn old JSON comments and new comments into clean text for the admin table."""
    comment_data = parse_survey_response_json(comment_value)
    response_data = parse_survey_response_json(survey_response_value)

    parts = []
    for key, question in OPEN_ENDED_QUESTIONS:
        answer = str(comment_data.get(key, response_data.get(key, "")) or "").strip()
        if answer:
            short_question = question.replace("Smart Pantry", "App")
            parts.append(f"{short_question} {answer}")

    if parts:
        return "\n\n".join(parts)

    raw_comment = str(comment_value or "").strip()
    if raw_comment.lower() in ["nan", "none", "null"]:
        return ""
    if raw_comment.startswith("{") and raw_comment.endswith("}"):
        return ""
    return raw_comment


def survey_key_aliases(question_key, survey_type):
    """Map dashboard outcome names to the actual pre/post survey response keys."""
    aliases = {
        "Pre-Study": {
            "pantry_awareness": ["pre_pantry_awareness"],
            "recommendation_usefulness": ["pre_realistic_meal_ideas"],
            "ingredient_utilization": ["pre_use_before_buying"],
            "ease_of_use": ["pre_method_easy_updated"],
        },
        "Post-Study": {
            "pantry_awareness": ["post_pantry_awareness"],
            "recommendation_usefulness": ["post_recommendation_usefulness"],
            "ingredient_utilization": ["post_more_ingredient_use"],
            "ease_of_use": ["post_easier_than_previous"],
            "compared_awareness": ["post_pantry_awareness"],
            "compared_recommendations": ["post_recommendation_usefulness"],
            "compared_utilization": ["post_more_ingredient_use"],
        },
    }

    return [question_key] + aliases.get(survey_type, {}).get(question_key, [])


def get_survey_numeric_value(row, question_key, survey_type):
    response_data = parse_survey_response_json(row.get("survey_responses", ""))

    for key in survey_key_aliases(question_key, survey_type):
        value = response_data.get(key)
        try:
            if value not in [None, ""]:
                return float(value)
        except Exception:
            pass

    for key in survey_key_aliases(question_key, survey_type):
        if key in row.index:
            try:
                value = row.get(key)
                if value not in [None, ""] and not pd.isna(value):
                    return float(value)
            except Exception:
                pass

    if question_key in row.index:
        try:
            value = row.get(question_key)
            if value not in [None, ""] and not pd.isna(value):
                return float(value)
        except Exception:
            pass

    return None


def survey_question_average(surveys_df, survey_type, question_key):
    if surveys_df.empty:
        return 0

    values = []
    subset = surveys_df[surveys_df["survey_type"] == survey_type]

    for _, row in subset.iterrows():
        value = get_survey_numeric_value(row, question_key, survey_type)
        if value is not None:
            values.append(float(value))

    if not values:
        return 0
    return round(sum(values) / len(values), 2)


def build_readable_survey_results(surveys_df):
    """Create a cleaner admin view without raw JSON columns."""
    if surveys_df.empty:
        return pd.DataFrame()

    rows = []
    for _, row in surveys_df.iterrows():
        survey_type = row.get("survey_type", "")
        readable_row = {
            "username": row.get("username", ""),
            "survey_type": survey_type,
            "current_method": row.get("current_method", ""),
            "pantry_awareness": get_survey_numeric_value(row, "pantry_awareness", survey_type),
            "recommendation_usefulness": get_survey_numeric_value(row, "recommendation_usefulness", survey_type),
            "ingredient_utilization": get_survey_numeric_value(row, "ingredient_utilization", survey_type),
            "ease_of_use": get_survey_numeric_value(row, "ease_of_use", survey_type),
            "comments": format_survey_comments(row.get("comments", ""), row.get("survey_responses", "")),
        }

        rows.append(readable_row)

    display_df = pd.DataFrame(rows)
    return display_df


def show_open_ended_survey_responses(surveys_df):
    """Show long post-study written answers in expandable sections instead of a crowded table."""
    if surveys_df.empty:
        return

    response_rows = []
    for _, row in surveys_df.iterrows():
        survey_type = row.get("survey_type", "")
        response_data = parse_survey_response_json(row.get("survey_responses", ""))
        comment_data = parse_survey_response_json(row.get("comments", ""))

        answers = {}
        for key, question in OPEN_ENDED_QUESTIONS:
            answer = str(comment_data.get(key, response_data.get(key, "")) or "").strip()
            if answer:
                answers[question] = answer

        if answers:
            response_rows.append(
                {
                    "username": row.get("username", "Participant"),
                    "survey_type": survey_type,
                    "answers": answers,
                }
            )

    if not response_rows:
        return

    st.subheader("Open-Ended Survey Responses")
    for item in response_rows:
        with st.expander(f"{item['username']} - {item['survey_type']} written responses"):
            for question, answer in item["answers"].items():
                st.markdown(f"**{question}**")
                st.write(answer)



def show_study_metrics(users_df, pantry_df, recommendation_df, usage_df, surveys_df):
    st.subheader("Study Metrics")
    st.write(
        "These metrics convert pantry activity, recommendation logs, ingredient usage, and survey responses "
        "into evidence for pantry awareness, recommendation usefulness, and ingredient utilization."
    )

    participant_count = len(users_df[users_df["role"] == "participant"]) if not users_df.empty and "role" in users_df.columns else 0
    pre_count = len(surveys_df[surveys_df["survey_type"] == "Pre-Study"]) if not surveys_df.empty else 0
    post_count = len(surveys_df[surveys_df["survey_type"] == "Post-Study"]) if not surveys_df.empty else 0

    pre_awareness = survey_question_average(surveys_df, "Pre-Study", "pantry_awareness")
    post_awareness = survey_question_average(surveys_df, "Post-Study", "pantry_awareness")
    awareness_change = round(post_awareness - pre_awareness, 2) if pre_awareness and post_awareness else 0

    pre_utilization = survey_question_average(surveys_df, "Pre-Study", "ingredient_utilization")
    post_utilization = survey_question_average(surveys_df, "Post-Study", "ingredient_utilization")
    utilization_change = round(post_utilization - pre_utilization, 2) if pre_utilization and post_utilization else 0

    post_recommendation_usefulness = survey_question_average(surveys_df, "Post-Study", "recommendation_usefulness")
    compared_awareness = survey_question_average(surveys_df, "Post-Study", "compared_awareness")
    compared_recommendations = survey_question_average(surveys_df, "Post-Study", "compared_recommendations")
    compared_utilization = survey_question_average(surveys_df, "Post-Study", "compared_utilization")

    total_recommendations = len(recommendation_df)
    meals_made = 0
    if not recommendation_df.empty and "used_recommendation" in recommendation_df.columns:
        meals_made = len(recommendation_df[recommendation_df["used_recommendation"] == "Yes"])

    total_pantry_items = len(pantry_df)
    total_usage_events = len(usage_df)
    total_quantity_used = 0
    used_elsewhere_count = 0
    expired_discarded_count = 0
    if not usage_df.empty:
        if "quantity_used" in usage_df.columns:
            total_quantity_used = round(pd.to_numeric(usage_df["quantity_used"], errors="coerce").fillna(0).sum(), 2)
        if "usage_type" in usage_df.columns:
            usage_type_text = usage_df["usage_type"].astype(str).str.lower()
            used_elsewhere_count = usage_type_text.str.contains("outside|elsewhere", regex=True).sum()
            expired_discarded_count = usage_type_text.str.contains("expired|discard", regex=True).sum()

    acceptance_rate = safe_percent(meals_made, total_recommendations)
    ingredient_utilization_rate = safe_percent(total_usage_events, total_pantry_items)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Participants", participant_count)
        st.metric("Pre-Surveys", pre_count)
    with col2:
        st.metric("Post-Surveys", post_count)
        st.metric("Pantry Items Added", total_pantry_items)
    with col3:
        st.metric("Meals Made", meals_made)
        st.metric("Recommendation Acceptance", f"{acceptance_rate}%")
    with col4:
        st.metric("Usage Events", total_usage_events)
        st.metric("Ingredient Utilization Rate", f"{ingredient_utilization_rate}%")

    st.subheader("Outcome Summary")
    summary_rows = [
        {"Outcome": "Pantry awareness", "Pre Average": pre_awareness, "Post Average": post_awareness, "Change": awareness_change},
        {"Outcome": "Ingredient utilization", "Pre Average": pre_utilization, "Post Average": post_utilization, "Change": utilization_change},
        {"Outcome": "Recommendation usefulness", "Pre Average": 0, "Post Average": post_recommendation_usefulness, "Change": post_recommendation_usefulness},
        {"Outcome": "Compared to previous method - awareness", "Pre Average": 0, "Post Average": compared_awareness, "Change": compared_awareness},
        {"Outcome": "Compared to previous method - recommendations", "Pre Average": 0, "Post Average": compared_recommendations, "Change": compared_recommendations},
        {"Outcome": "Compared to previous method - utilization", "Pre Average": 0, "Post Average": compared_utilization, "Change": compared_utilization},
    ]
    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, use_container_width=True)

    chart_df = summary_df[summary_df["Post Average"] > 0][["Outcome", "Post Average"]].set_index("Outcome")
    if not chart_df.empty:
        st.bar_chart(chart_df)

    st.subheader("Usage and Recommendation Evidence")
    evidence_df = pd.DataFrame([
        {"Metric": "Total recommendations logged", "Value": total_recommendations},
        {"Metric": "Meals marked as made", "Value": meals_made},
        {"Metric": "Ingredients used elsewhere", "Value": used_elsewhere_count},
        {"Metric": "Expired/discarded items", "Value": expired_discarded_count},
        {"Metric": "Total quantity used", "Value": total_quantity_used},
        {"Metric": "Recommendation acceptance rate (%)", "Value": acceptance_rate},
        {"Metric": "Ingredient utilization rate (%)", "Value": ingredient_utilization_rate},
    ])
    st.dataframe(evidence_df, use_container_width=True)



def show_admin_dashboard():
    st.title("Admin Dashboard")

    st.write(
        """
        This dashboard is for the researcher to review participant activity,
        pantry usage, survey results, and recommendation usage.
        """
    )

    with st.spinner("Loading admin data..."):
        admin_data = load_admin_data_cached()

    users_df = admin_data["users"]
    pantry_df = admin_data["pantry"]
    recommendation_df = admin_data["recommendations"]
    usage_df = admin_data["usage"]
    surveys_df = admin_data["surveys"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        participant_count = 0
        if not users_df.empty and "role" in users_df.columns:
            participant_count = len(users_df[users_df["role"] == "participant"])
        st.metric("Participants", participant_count)

    with col2:
        st.metric("Pantry Items", len(pantry_df))

    with col3:
        st.metric("Recommendations Saved", len(recommendation_df))

    with col4:
        used_count = 0
        if not recommendation_df.empty and "used_recommendation" in recommendation_df.columns:
            used_count = len(recommendation_df[recommendation_df["used_recommendation"] == "Yes"])
        st.metric("Recommendations Used", used_count)

    st.caption("Admin data is cached for 60 seconds so the app does not reload every table on every click.")

    admin_section = st.selectbox(
        "Choose admin section",
        [
            "Study Metrics",
            "Users",
            "Pantry Data",
            "Recommendation Logs",
            "Ingredient Usage",
            "Survey Results",
            "Export Data",
        ],
    )

    if st.button("Refresh Admin Data"):
        clear_user_cache()
        st.rerun()

    if admin_section == "Study Metrics":
        show_study_metrics(users_df, pantry_df, recommendation_df, usage_df, surveys_df)

    elif admin_section == "Users":
        st.subheader("Participants and Users")
        st.dataframe(users_df, use_container_width=True)

    elif admin_section == "Pantry Data":
        st.subheader("All Pantry Items")
        st.dataframe(pantry_df, use_container_width=True)

    elif admin_section == "Recommendation Logs":
        st.subheader("All Recommendation Logs")
        st.dataframe(recommendation_df, use_container_width=True)

    elif admin_section == "Ingredient Usage":
        st.subheader("Ingredient Usage Logs")
        st.dataframe(usage_df, use_container_width=True)

    elif admin_section == "Survey Results":
        st.subheader("Survey Results")

        if surveys_df.empty:
            st.info("No survey responses have been submitted yet.")
        else:
            readable_surveys_df = build_readable_survey_results(surveys_df)
            st.dataframe(readable_surveys_df, use_container_width=True, hide_index=True)

            show_open_ended_survey_responses(surveys_df)

            st.subheader("Average Survey Scores by Survey Type")

            score_cols = [
                "pantry_awareness",
                "recommendation_usefulness",
                "ingredient_utilization",
                "ease_of_use",
            ]

            summary_rows = []
            for survey_type_name in sorted(readable_surveys_df["survey_type"].dropna().unique()):
                type_df = readable_surveys_df[readable_surveys_df["survey_type"] == survey_type_name]
                row = {"survey_type": survey_type_name}
                for score_col in score_cols:
                    row[score_col] = round(pd.to_numeric(type_df[score_col], errors="coerce").mean(), 2)
                summary_rows.append(row)

            summary_df = pd.DataFrame(summary_rows)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            with st.expander("Raw survey data for troubleshooting"):
                st.caption("This keeps the database proof available, but it is hidden so comments and full JSON responses do not crowd the main admin view.")
                st.dataframe(surveys_df, use_container_width=True)

    elif admin_section == "Export Data":
        st.subheader("Download CSV Files")

        st.download_button(
            "Download Users CSV",
            data=convert_df_to_csv(users_df),
            file_name="smart_pantry_users.csv",
            mime="text/csv",
        )

        st.download_button(
            "Download Pantry CSV",
            data=convert_df_to_csv(pantry_df),
            file_name="smart_pantry_pantry_items.csv",
            mime="text/csv",
        )

        st.download_button(
            "Download Recommendations CSV",
            data=convert_df_to_csv(recommendation_df),
            file_name="smart_pantry_recommendations.csv",
            mime="text/csv",
        )

        st.download_button(
            "Download Ingredient Usage CSV",
            data=convert_df_to_csv(usage_df),
            file_name="smart_pantry_ingredient_usage.csv",
            mime="text/csv",
        )

        st.download_button(
            "Download Surveys CSV",
            data=convert_df_to_csv(surveys_df),
            file_name="smart_pantry_surveys.csv",
            mime="text/csv",
        )

def show_participant_view_for_admin():
    st.title("Participant View Preview")
    st.info("This lets the researcher preview the regular participant experience.")
    show_home()

# Page rendering functions are called from main.py through app_pages modules.
