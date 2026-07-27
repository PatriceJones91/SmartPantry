import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "services" / "recommendations" / "meal_classifier.py"
spec = importlib.util.spec_from_file_location("meal_classifier", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
classify_recipe_meal_types = module.classify_recipe_meal_types
recipe_matches_meal_filter = module.recipe_matches_meal_filter


def classify(name, ingredients=None, meal_type="", dish_type="", cook_time=None):
    return classify_recipe_meal_types({
        "recipe_name": name,
        "ingredients_list": ingredients or [],
        "meal_type": meal_type,
        "dish_type": dish_type,
        "cook_time": cook_time,
    })


def test_pancakes_do_not_leak_into_lunch_from_bad_dataset_label():
    result = classify(
        "Blueberry Pancakes",
        ["flour", "milk", "egg", "blueberries"],
        meal_type="Lunch",
        dish_type="Breakfast",
        cook_time=20,
    )
    assert "Breakfast" in result["smart_meal_types"]
    assert "Lunch" not in result["smart_meal_types"]


def test_cookies_are_dessert_not_lunch():
    result = classify(
        "Chocolate Chip Cookies",
        ["flour", "sugar", "butter", "chocolate chips"],
        meal_type="Lunch",
        dish_type="Dessert",
    )
    assert "Dessert" in result["smart_meal_types"]
    assert "Lunch" not in result["smart_meal_types"]


def test_dip_is_snack_not_lunch_when_dataset_is_wrong():
    result = classify(
        "Creamy Spinach Dip",
        ["spinach", "cream cheese", "sour cream"],
        meal_type="Lunch",
        dish_type="Appetizer",
    )
    assert "Snack" in result["smart_meal_types"]
    assert "Lunch" not in result["smart_meal_types"]


def test_sandwich_can_be_lunch_and_quick():
    result = classify(
        "Turkey Club Sandwich",
        ["turkey", "bread", "lettuce", "tomato"],
        dish_type="Main Course",
        cook_time=15,
    )
    assert "Lunch" in result["smart_meal_types"]
    assert "Quick Meal" in result["smart_meal_types"]


def test_casserole_is_dinner_not_breakfast_from_bad_label():
    result = classify(
        "Chicken Broccoli Rice Casserole",
        ["chicken", "rice", "broccoli", "cheddar"],
        meal_type="Breakfast",
        dish_type="Main Course",
        cook_time=50,
    )
    assert "Dinner" in result["smart_meal_types"]
    assert "Breakfast" not in result["smart_meal_types"]


def test_omelet_is_breakfast_and_brunch_but_not_lunch():
    result = classify(
        "Vegetable Omelet",
        ["egg", "bell pepper", "cheese", "spinach"],
        meal_type="Lunch",
        cook_time=15,
    )
    assert "Breakfast" in result["smart_meal_types"]
    assert "Brunch" in result["smart_meal_types"]
    assert "Lunch" not in result["smart_meal_types"]


def test_recipe_filter_uses_smart_classification():
    recipe = {
        "recipe_name": "Apple Cinnamon Cake",
        "ingredients_list": ["apple", "flour", "sugar", "butter"],
        "meal_type": "Lunch",
        "dish_type": "Dessert",
    }
    assert recipe_matches_meal_filter(recipe, "dessert") is True
    assert recipe_matches_meal_filter(recipe, "lunch") is False
