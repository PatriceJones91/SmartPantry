from services.recommendations.diversity import are_near_duplicates, select_diverse_recommendations
from services.recommendations.smart_swaps import find_smart_swaps


def _recipe(name, ingredients, score=70):
    return {
        "recipe_id": name.lower().replace(" ", "-"),
        "recipe_name": name,
        "main_ingredients": ingredients,
        "dish_types": ["main dish"],
        "meal_types": ["lunch", "dinner"],
        "cuisine_types": ["american"],
        "smart_score": score,
        "nutrition_fit": {"score_percent": 90},
    }


def test_named_chicken_nugget_variants_are_one_recipe_family():
    a = _recipe("Homemade Chicken Nuggets", ["chicken breast", "egg", "flour", "milk"])
    b = _recipe("Sherry's Homemade Chicken Nuggets", ["chicken breast", "egg", "flour", "milk"])
    assert are_near_duplicates(a, b)
    selected, metadata = select_diverse_recommendations([a, b], limit=10)
    assert len(selected) == 1
    assert metadata["near_duplicate_candidates_excluded"] >= 1


def test_green_beans_do_not_swap_to_shrimp():
    swaps = find_smart_swaps(
        ["green beans"],
        [{"item_name": "shrimp"}],
        recipe_context={"recipe_name": "Green Bean Casserole", "dish_types": ["side dish"]},
    )
    assert swaps == []


def test_catfish_does_not_swap_to_black_beans():
    swaps = find_smart_swaps(
        ["catfish"],
        [{"item_name": "black beans"}],
        recipe_context={"recipe_name": "Baked Catfish", "dish_types": ["main dish"]},
    )
    assert swaps == []
