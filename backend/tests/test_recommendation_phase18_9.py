from services.recommendations.candidate_discovery import evaluate_recipe_candidate, prepare_usable_pantry
from services.recommendations.recipe_repository import RecipeIngredient, RecipeRecord


def test_matched_ingredient_carries_recipe_native_quantity_metadata():
    recipe = RecipeRecord(
        recipe_id="recipe_test_flour",
        recipe_name="Test Flour Recipe",
        clean_recipe_name="Test Flour Recipe",
        meal_types=["breakfast"],
        cuisine_types=["american"],
        dish_types=["main course"],
        ingredients=[
            RecipeIngredient(
                food="all-purpose flour",
                text="2 tablespoons all-purpose flour",
                weight=15.0,
                measure="tablespoon",
                quantity=2.0,
            )
        ],
        main_ingredients=["flour"],
        calories=100,
        protein=3,
        carbs=20,
        fat=1,
        servings=2,
        url="",
        everyday_fit_score=1,
    )
    pantry, _ = prepare_usable_pantry([
        {"id": "pantry_flour", "item_name": "All Purpose Flour", "quantity": 6, "unit": "lb"}
    ])
    decision, candidate = evaluate_recipe_candidate(recipe, pantry)
    assert decision.status.value == "complete"
    match = candidate["matched_ingredients"][0]
    assert match["recipe_quantity"] == 2.0
    assert match["recipe_measure"] == "tablespoon"
    assert match["recipe_weight_grams"] == 15.0
    assert match["recipe_text"] == "2 tablespoons all-purpose flour"
