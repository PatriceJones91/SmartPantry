from collections import Counter
from datetime import datetime

SIMPLE_MEALS = {

    "Sandwich": [

        "bread",
        "lunchmeat"
    ],

    "Grilled Cheese": [

        "bread",
        "cheese"
    ],

    "Cheeseburger": [

        "bread",
        "ground beef",
        "cheese"
    ],

    "Hamburger": [

        "bread",
        "ground beef"
    ],

    "Shrimp Quesadilla": [

        "shrimp",
        "tortilla",
        "cheese"
    ],

    "Chicken Alfredo": [

        "pasta",
        "chicken",
        "alfredo sauce"
    ],

    "Spaghetti": [

        "pasta",
        "ground beef",
        "pasta sauce"
    ],

    "Fried Rice": [

        "rice",
        "egg",
        "onion"
    ],

    "Chicken Wrap": [

        "tortilla",
        "chicken",
        "cheese"
    ],

    "Tacos": [

        "tortilla",
        "ground beef",
        "cheese"
    ]
}

def normalize_ingredient(text):

    return str(text).lower().strip()

def calculate_waste_risk(expiration_date):

    try:

        today = datetime.today().date()

        expiration = datetime.strptime(

            str(expiration_date),
            "%Y-%m-%d"

        ).date()

        days_left = (
            expiration - today
        ).days

        if days_left <= 2:

            return "High"

        elif days_left <= 5:

            return "Medium"

        return "Low"

    except:

        return "Unknown"

def get_meals_you_can_make(pantry_items):

    pantry_items = [

        normalize_ingredient(i)

        for i in pantry_items
    ]

    meals = []

    for meal_name, ingredients in SIMPLE_MEALS.items():

        matched = []

        for ingredient in ingredients:

            ingredient = normalize_ingredient(
                ingredient
            )

            for pantry_item in pantry_items:

                if ingredient in pantry_item or pantry_item in ingredient:

                    matched.append(
                        ingredient
                    )

                    break

        score = round(

            len(matched) / len(ingredients),

            2
        )

        if score >= 1.0:

            meals.append({

                "meal": meal_name,

                "matched": matched,

                "score": score
            })

    return meals

def generate_grocery_suggestions(meals):

    grocery_counter = Counter()

    for meal in meals:

        if meal["meal"] == "Hamburger":

            grocery_counter[
                "bacon"
            ] += 1

            grocery_counter[
                "lettuce"
            ] += 1

        if meal["meal"] == "Shrimp Quesadilla":

            grocery_counter[
                "sour cream"
            ] += 1

            grocery_counter[
                "peppers"
            ] += 1

    return grocery_counter.most_common(5)