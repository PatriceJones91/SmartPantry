import ast
import json
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

from database.database import (
    add_pantry_item,
    create_tables,
    delete_pantry_items,
    get_pantry_items,
    update_pantry_item,
)

from recommendation_engine.engine import calculate_waste_risk

create_tables()

st.set_page_config(
    page_title="SmartPantry AI",
    layout="wide"
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f7f2;
    }

    .metric-card {
        background-color: white;
        padding: 14px;
        border-radius: 16px;
        border: 1px solid #dce5d7;
        text-align: center;
    }

    .meal-card {
        background-color: white;
        padding: 14px;
        border-radius: 16px;
        border: 1px solid #dce5d7;
        margin-bottom: 16px;
        min-height: 470px;
        font-size: 14px;
    }

    .section-title {
        font-size: 32px;
        font-weight: bold;
        color: #1d4729;
        margin-bottom: 20px;
    }

    .meal-title {
        color: #1d4729;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_path = "app/SmartPantry_logo.png"

if os.path.exists(logo_path):
    st.sidebar.image(
        logo_path,
        width=220
    )
else:
    st.sidebar.markdown("## 🥗 SmartPantry AI")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Pantry",
        "Recommendations",
    ],
)

DATASET_PATH = "data/recipes-with-nutrition.csv"

PANTRY_STAPLES = {
    "salt",
    "pepper",
    "water",
    "oil",
    "olive oil",
    "vegetable oil",
    "extra virgin olive oil",
    "seasoning",
    "garlic powder",
    "onion powder",
}

BLOCKED_DISH_KEYWORDS = [
    "sauce",
    "condiment",
    "ketchup",
    "mayonnaise",
    "mayo",
    "dressing",
    "marinade",
    "syrup",
    "spread",
    "jam",
    "gravy",
]

ALLOWED_DIP_KEYWORDS = [
    "artichoke dip",
    "spinach dip",
    "bean dip",
    "cheese dip",
    "buffalo chicken dip",
    "guacamole",
    "hummus",
    "salsa",
]

INGREDIENT_ALIASES = {
    "lunch meat": "lunchmeat",
    "turkey lunchmeat": "lunchmeat",
    "ham lunchmeat": "lunchmeat",
    "deli meat": "lunchmeat",
    "turkey breast": "lunchmeat",
    "ham": "lunchmeat",
    "wheat bread": "bread",
    "white bread": "bread",
    "sandwich bread": "bread",
    "hamburger buns": "bread",
    "hamburger bun": "bread",
    "buns": "bread",
    "bun": "bread",
    "toast": "bread",
    "cheddar cheese": "cheese",
    "american cheese": "cheese",
    "mozzarella cheese": "cheese",
    "swiss cheese": "cheese",
    "shredded cheese": "cheese",
    "sliced cheese": "cheese",
    "parmesan cheese": "cheese",
    "parmigiano reggiano cheese": "cheese",
    "ground beef": "ground beef",
    "beef": "ground beef",
    "burger meat": "ground beef",
    "hamburger meat": "ground beef",
    "taco shell": "tortilla",
    "taco shells": "tortilla",
    "wrap": "tortilla",
    "wraps": "tortilla",
    "flour tortilla": "tortilla",
    "corn tortilla": "tortilla",
    "roma tomato": "tomato",
    "cherry tomato": "tomato",
    "fresh tomato": "tomato",
    "tomatoes": "tomato",
    "iceberg lettuce": "lettuce",
    "romaine lettuce": "lettuce",
    "bell pepper": "pepper",
    "green pepper": "pepper",
    "red pepper": "pepper",
    "sweet peppers": "pepper",
    "spaghetti noodles": "pasta",
    "noodles": "pasta",
    "sweet onion": "onion",
    "yellow onion": "onion",
    "red onion": "onion",
    "eggs": "egg",
}

STARTER_RECIPES = [
    {
        "name": "Sandwich",
        "ingredients": ["bread", "lunchmeat", "lettuce", "tomato"],
        "ingredient_lines": ["Bread", "Lunchmeat", "Lettuce", "Tomato"],
        "calories": 390,
        "protein": 18,
        "carbs": 28,
        "fat": 12,
        "cook_time": 5,
        "meal_type": "Lunch",
        "cuisine_type": "American",
        "dish_type": "Sandwich",
        "instructions": "Layer lunchmeat, lettuce, and tomato between bread slices.",
        "source": "SmartPantry Template",
    },
    {
        "name": "Hamburger",
        "ingredients": ["bread", "ground beef", "lettuce", "tomato"],
        "ingredient_lines": ["Bread or hamburger bun", "Ground beef", "Lettuce", "Tomato"],
        "calories": 550,
        "protein": 30,
        "carbs": 38,
        "fat": 28,
        "cook_time": 18,
        "meal_type": "Dinner",
        "cuisine_type": "American",
        "dish_type": "Burger",
        "instructions": "Cook beef patty and assemble with bread, lettuce, and tomato.",
        "source": "SmartPantry Template",
    },
    {
        "name": "Cheeseburger",
        "ingredients": ["bread", "ground beef", "cheese", "lettuce", "tomato"],
        "ingredient_lines": ["Bread or hamburger bun", "Ground beef", "Cheese", "Lettuce", "Tomato"],
        "calories": 650,
        "protein": 35,
        "carbs": 40,
        "fat": 32,
        "cook_time": 20,
        "meal_type": "Dinner",
        "cuisine_type": "American",
        "dish_type": "Burger",
        "instructions": "Cook beef patty, add cheese, lettuce, and tomato.",
        "source": "SmartPantry Template",
    },
    {
        "name": "Grilled Cheese",
        "ingredients": ["bread", "cheese", "butter"],
        "ingredient_lines": ["Bread", "Cheese", "Butter"],
        "calories": 420,
        "protein": 12,
        "carbs": 30,
        "fat": 20,
        "cook_time": 10,
        "meal_type": "Lunch",
        "cuisine_type": "American",
        "dish_type": "Sandwich",
        "instructions": "Butter bread, add cheese, and toast both sides.",
        "source": "SmartPantry Template",
    },
    {
        "name": "Shrimp Quesadilla",
        "ingredients": ["shrimp", "tortilla", "cheese"],
        "ingredient_lines": ["Shrimp", "Tortilla", "Cheese"],
        "calories": 590,
        "protein": 32,
        "carbs": 36,
        "fat": 22,
        "cook_time": 15,
        "meal_type": "Dinner",
        "cuisine_type": "Mexican",
        "dish_type": "Quesadilla",
        "instructions": "Cook shrimp, add cheese to tortilla, and grill both sides.",
        "source": "SmartPantry Template",
    },
    {
        "name": "Fried Rice",
        "ingredients": ["rice", "egg", "onion"],
        "ingredient_lines": ["Rice", "Egg", "Onion"],
        "calories": 480,
        "protein": 14,
        "carbs": 52,
        "fat": 18,
        "cook_time": 15,
        "meal_type": "Dinner",
        "cuisine_type": "Asian",
        "dish_type": "Rice Dish",
        "instructions": "Cook rice with eggs and onions in a skillet.",
        "source": "SmartPantry Template",
    },
]


def clean_text(value):
    return (
        str(value)
        .lower()
        .strip()
        .replace("-", " ")
        .replace("_", " ")
        .replace(",", " ")
        .replace("/", " ")
        .replace("  ", " ")
    )


def normalize_ingredient(ingredient):
    ingredient = clean_text(ingredient)

    if ingredient in INGREDIENT_ALIASES:
        return INGREDIENT_ALIASES[ingredient]

    return ingredient


def detect_category(ingredient):
    ingredient = normalize_ingredient(ingredient)

    if any(word in ingredient for word in ["beef", "chicken", "shrimp", "egg", "salmon", "turkey", "lunchmeat", "fish", "pork"]):
        return "Protein"

    if any(word in ingredient for word in ["milk", "cheese", "yogurt", "butter"]):
        return "Dairy"

    if any(word in ingredient for word in ["bread", "rice", "pasta", "tortilla", "oats", "cereal"]):
        return "Grains"

    if any(word in ingredient for word in ["apple", "banana", "orange", "grape", "strawberry", "blueberry"]):
        return "Fruit"

    if any(word in ingredient for word in ["lettuce", "onion", "tomato", "pepper", "spinach", "potato", "corn", "broccoli", "carrot"]):
        return "Vegetable"

    return "Other"


def clean_dataset_item(item):
    if isinstance(item, dict):
        for key in ["food", "text", "label", "name"]:
            if key in item and str(item[key]).strip():
                return str(item[key])

        return " ".join(
            str(value)
            for value in item.values()
            if str(value).strip()
        )

    return str(item)


def parse_list_value(value):
    if isinstance(value, list):
        return [
            clean_dataset_item(item)
            for item in value
            if clean_dataset_item(item).strip()
        ]

    if pd.isna(value):
        return []

    text = str(value).strip()

    if not text:
        return []

    for parser in [ast.literal_eval, json.loads]:
        try:
            parsed = parser(text)

            if isinstance(parsed, list):
                return [
                    clean_dataset_item(item)
                    for item in parsed
                    if clean_dataset_item(item).strip()
                ]

            if isinstance(parsed, dict):
                cleaned_item = clean_dataset_item(parsed)

                if cleaned_item.strip():
                    return [cleaned_item]

                return [str(key) for key in parsed.keys()]

        except Exception:
            pass

    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]


def parse_dict_value(value):
    if isinstance(value, dict):
        return value

    if pd.isna(value):
        return {}

    text = str(value).strip()

    if not text:
        return {}

    for parser in [ast.literal_eval, json.loads]:
        try:
            parsed = parser(text)

            if isinstance(parsed, dict):
                return parsed

        except Exception:
            pass

    return {}


def extract_nutrient(total_nutrients, key):
    nutrients = parse_dict_value(total_nutrients)

    if key not in nutrients:
        return "N/A"

    value = nutrients[key]

    if isinstance(value, dict):
        amount = value.get("quantity", "N/A")
    else:
        amount = value

    try:
        return round(float(amount), 1)
    except Exception:
        return "N/A"


def safe_title(value):
    text = str(value).strip()

    if text == "" or text.lower() == "nan":
        return None

    return text.title()


def format_category_value(value):
    parsed = parse_list_value(value)

    if not parsed:
        text = str(value).strip()
        return "N/A" if text == "" or text.lower() == "nan" else text.title()

    return ", ".join(
        str(item).title()
        for item in parsed[:3]
    )


def build_dataset_instructions(row):
    if "instructions" in row and str(row["instructions"]).strip().lower() != "nan":
        return str(row["instructions"])

    if "steps" in row and str(row["steps"]).strip().lower() != "nan":
        steps = parse_list_value(row["steps"])

        if steps:
            return " ".join(
                f"{index}. {step}"
                for index, step in enumerate(steps[:6], start=1)
            )

    ingredient_lines = parse_list_value(row.get("ingredient_lines", ""))

    if ingredient_lines:
        return "Use the listed ingredients together. Ingredient list: " + "; ".join(ingredient_lines[:8])

    return "Recipe instructions were not included in the dataset."


def should_skip_recipe(name, dish_type):
    combined_text = f"{name} {dish_type}".lower()

    allowed_dip = any(
        keyword in combined_text
        for keyword in ALLOWED_DIP_KEYWORDS
    )

    blocked_recipe = any(
        keyword in combined_text
        for keyword in BLOCKED_DISH_KEYWORDS
    )

    return blocked_recipe and not allowed_dip


@st.cache_data
def load_dataset_recipes():
    if not os.path.exists(DATASET_PATH):
        return []

    try:
        recipes_df = pd.read_csv(DATASET_PATH)
    except Exception:
        return []

    required_columns = [
        "recipe_name",
        "ingredients",
        "ingredient_lines",
        "total_nutrients",
        "meal_type",
        "cuisine_type",
        "dish_type",
    ]

    if any(column not in recipes_df.columns for column in required_columns):
        return []

    recipes_df = recipes_df.dropna(subset=["recipe_name", "ingredients"])
    recipes_df = recipes_df.head(6000)

    dataset_recipes = []

    for _, row in recipes_df.iterrows():
        name = safe_title(row["recipe_name"])

        if name is None:
            continue

        meal_type = format_category_value(row["meal_type"])
        cuisine_type = format_category_value(row["cuisine_type"])
        dish_type = format_category_value(row["dish_type"])

        if should_skip_recipe(name, dish_type):
            continue

        raw_ingredients = parse_list_value(row["ingredients"])
        normalized_ingredients = []

        for item in raw_ingredients:
            normalized_item = normalize_ingredient(item)

            if normalized_item not in PANTRY_STAPLES and normalized_item:
                normalized_ingredients.append(normalized_item)

        normalized_ingredients = list(dict.fromkeys(normalized_ingredients))

        if len(normalized_ingredients) < 2:
            continue

        ingredient_lines = parse_list_value(row["ingredient_lines"])
        calories = row.get("calories", "N/A")

        try:
            calories = round(float(calories), 1)
        except Exception:
            calories = extract_nutrient(row["total_nutrients"], "ENERC_KCAL")

        dataset_recipes.append(
            {
                "name": name,
                "ingredients": normalized_ingredients[:14],
                "ingredient_lines": ingredient_lines[:10],
                "calories": calories,
                "protein": extract_nutrient(row["total_nutrients"], "PROCNT"),
                "carbs": extract_nutrient(row["total_nutrients"], "CHOCDF"),
                "fat": extract_nutrient(row["total_nutrients"], "FAT"),
                "cook_time": 30,
                "meal_type": meal_type,
                "cuisine_type": cuisine_type,
                "dish_type": dish_type,
                "instructions": build_dataset_instructions(row),
                "source": "Recipes With Nutrition Dataset",
            }
        )

    return dataset_recipes


def get_recipe_matches(recipe, pantry_items):
    normalized_pantry = set(
        normalize_ingredient(item)
        for item in pantry_items
    )

    recipe_ingredients = [
        normalize_ingredient(item)
        for item in recipe["ingredients"]
        if normalize_ingredient(item) not in PANTRY_STAPLES
    ]

    recipe_ingredients = list(dict.fromkeys(recipe_ingredients))

    matched = []
    missing = []

    for ingredient in recipe_ingredients:
        if ingredient in normalized_pantry:
            matched.append(ingredient)
        else:
            missing.append(ingredient)

    return matched, missing, recipe_ingredients


def calculate_recipe_score(recipe, pantry_items, expiring_items):
    matched, missing, recipe_ingredients = get_recipe_matches(recipe, pantry_items)

    if not recipe_ingredients:
        return 0

    match_percent = len(matched) / len(recipe_ingredients)
    score = match_percent * 70

    try:
        protein = float(recipe.get("protein", 0))
        if protein >= 20:
            score += 10
    except Exception:
        pass

    try:
        calories = float(recipe.get("calories", 9999))
        if calories <= 700:
            score += 8
    except Exception:
        pass

    normalized_expiring = set(
        normalize_ingredient(item)
        for item in expiring_items
    )

    for ingredient in matched:
        if ingredient in normalized_expiring:
            score += 15

    if len(missing) == 0:
        score += 25
    elif len(missing) == 1:
        score += 12

    return round(score, 2)


def build_meals_you_can_make(pantry_items, expiring_items):
    all_recipes = STARTER_RECIPES + load_dataset_recipes()
    recommendations = []

    for recipe in all_recipes:
        matched, missing, recipe_ingredients = get_recipe_matches(recipe, pantry_items)

        if not recipe_ingredients:
            continue

        if len(missing) != 0:
            continue

        score = calculate_recipe_score(recipe, pantry_items, expiring_items)

        recommendations.append(
            {
                "name": recipe["name"],
                "score": score,
                "matched": matched,
                "missing": missing,
                "match_percent": 100,
                "data": recipe,
            }
        )

    recommendations = sorted(
        recommendations,
        key=lambda item: item["score"],
        reverse=True,
    )

    seen = set()
    unique_recommendations = []

    for recipe in recommendations:
        key = clean_text(recipe["name"])

        if key not in seen:
            seen.add(key)
            unique_recommendations.append(recipe)

    return unique_recommendations[:16]


def build_grocery_unlocks(pantry_items):
    all_recipes = STARTER_RECIPES + load_dataset_recipes()
    unlocks = {}

    for recipe in all_recipes:
        matched, missing, recipe_ingredients = get_recipe_matches(recipe, pantry_items)

        if not recipe_ingredients:
            continue

        if len(missing) == 1 and len(matched) >= 2:
            ingredient = missing[0]

            if ingredient not in unlocks:
                unlocks[ingredient] = []

            unlocks[ingredient].append(recipe["name"])

    sorted_unlocks = sorted(
        unlocks.items(),
        key=lambda item: len(item[1]),
        reverse=True,
    )

    return sorted_unlocks[:8]


pantry_df = get_pantry_items()
pantry_items = pantry_df["Ingredient"].tolist() if not pantry_df.empty else []

expiring_items = []
expiring_details = []

for _, row in pantry_df.iterrows():
    risk = calculate_waste_risk(row["Expiration"])

    if risk in ["High", "Medium"]:
        expiring_items.append(row["Ingredient"])
        expiring_details.append(
            {
                "ingredient": row["Ingredient"],
                "expiration": row["Expiration"],
                "risk": risk,
            }
        )

meals_you_can_make = build_meals_you_can_make(pantry_items, expiring_items)
grocery_unlocks = build_grocery_unlocks(pantry_items)

if page == "Dashboard":
    st.markdown(
        "<div class='section-title'>📊 Smart Pantry Dashboard</div>",
        unsafe_allow_html=True,
    )

    total_items = len(pantry_df)
    category_counts = {}

    for _, row in pantry_df.iterrows():
        category = row["Category"]
        category_counts[category] = category_counts.get(category, 0) + 1

    pantry_health = max(100 - (len(expiring_items) * 5), 0)

    top1, top2, top3 = st.columns(3)

    with top1:
        st.markdown(
            f"""
            <div class='metric-card'>
            <h1>{total_items}</h1>
            <p>Total Pantry Items</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top2:
        st.markdown(
            f"""
            <div class='metric-card'>
            <h1>{pantry_health}%</h1>
            <p>Pantry Health Score</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top3:
        st.markdown(
            f"""
            <div class='metric-card'>
            <h1>{len(expiring_items)}</h1>
            <p>Expiring Soon</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("⚠️ Expiring Ingredients")

        if not expiring_details:
            st.success("No ingredients expiring soon.")

        for item in expiring_details:
            st.warning(
                f"{item['ingredient']} expires on {item['expiration']} ({item['risk']} risk)"
            )

    with right_col:
        st.subheader("🥗 Pantry Breakdown")

        if category_counts:
            chart_df = pd.DataFrame(
                {
                    "Category": list(category_counts.keys()),
                    "Count": list(category_counts.values()),
                }
            )

            fig = px.pie(
                chart_df,
                names="Category",
                values="Count",
            )

            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Add pantry items to see pantry analytics.")

    st.divider()
    st.subheader("🛒 Smart Grocery Suggestions")

    if not grocery_unlocks:
        st.info("No grocery unlock suggestions yet. Add more pantry items to generate smarter suggestions.")

    for ingredient, meals in grocery_unlocks:
        st.info(f"Buy {ingredient} to unlock: {', '.join(meals[:5])}")

elif page == "Pantry":
    st.markdown(
        "<div class='section-title'>📦 Pantry Inventory</div>",
        unsafe_allow_html=True,
    )

    display_df = pantry_df.copy()

    if not display_df.empty:
        display_df.insert(0, "Select", False)

        edited_df = st.data_editor(
            display_df,
            width="stretch",
            hide_index=True,
        )

        selected_items = edited_df[edited_df["Select"] == True]
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Delete Selected"):
                if len(selected_items) > 0:
                    delete_pantry_items(selected_items["id"].tolist())
                    st.rerun()

        with col2:
            if st.button("Save Changes"):
                for _, row in edited_df.iterrows():
                    update_pantry_item(
                        row["id"],
                        row["Ingredient"],
                        row["Quantity"],
                        row["Expiration"],
                        row["Category"],
                    )

                st.rerun()
    else:
        st.info("No pantry items added yet.")

    st.divider()
    st.subheader("➕ Add Pantry Item")

    with st.form("add_item_form"):
        ingredient = st.text_input("Ingredient")
        quantity = st.text_input("Quantity")
        expiration = st.date_input("Expiration Date")
        category = detect_category(ingredient)

        st.write(f"Detected Category: {category}")

        submit = st.form_submit_button("Add Item")

        if submit:
            if ingredient.strip() == "":
                st.error("Please enter an ingredient.")
            else:
                add_pantry_item(
                    ingredient,
                    quantity,
                    str(expiration),
                    category,
                )

                st.success(f"{ingredient} added!")
                st.rerun()

elif page == "Recommendations":
    st.markdown(
        "<div class='section-title'>🍽️ Smart Recommendations</div>",
        unsafe_allow_html=True,
    )
    
    st.subheader("✅ Meals You Can Make Now")

    if not meals_you_can_make:
        st.warning("No complete meals found with the current pantry items.")

    cols = st.columns(4)

    for index, meal in enumerate(meals_you_can_make):
        meal_data = meal["data"]

        with cols[index % 4]:
            st.markdown(
                f"""
                <div class='meal-card'>

                <div class='meal-title'>{meal['name']}</div>

                <b>AI Match Score:</b> {meal['score']}<br><br>
                <b>Match:</b> {meal['match_percent']}%<br><br>

                <b>Meal Type:</b> {meal_data['meal_type']}<br>
                <b>Cuisine:</b> {meal_data['cuisine_type']}<br>
                <b>Dish Type:</b> {meal_data['dish_type']}<br><br>

                <b>Using:</b><br>
                {', '.join(meal['matched'])}<br><br>

                <b>Missing:</b><br>
                Nothing<br><br>

                🔥 {meal_data['calories']} cal<br>
                💪 {meal_data['protein']} protein<br>
                🍞 {meal_data['carbs']} carbs<br>
                🧈 {meal_data['fat']} fat<br><br>

                <b>Source:</b> {meal_data['source']}<br><br>

                <b>Ingredients:</b><br>
                {'; '.join(meal_data['ingredient_lines'][:5]) if meal_data['ingredient_lines'] else ', '.join(meal_data['ingredients'][:6])}<br><br>

                📖 <b>Recipe:</b><br>
                {meal_data['instructions']}

                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("🛒 Grocery Unlock Suggestions")

    if not grocery_unlocks:
        st.info("No one-item grocery unlocks found yet.")

    for ingredient, meals in grocery_unlocks:
        st.info(f"Buy {ingredient} to unlock: {', '.join(meals[:5])}")