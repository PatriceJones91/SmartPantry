from services.recommendations.candidate_discovery import evaluate_recipe_candidate, prepare_usable_pantry
from services.recommendations.ingredient_normalizer import normalize_ingredient
from services.recommendations.nutrition_fit import build_feature_inputs
from services.recommendations.recipe_repository import RecipeIngredient, RecipeRecord
from services.recommendations.smart_score import calculate_smart_score


def test_potato_varieties_share_canonical_match():
    assert normalize_ingredient("Yukon gold potatoes").canonical == "potato"
    assert normalize_ingredient("Russet potatoes").canonical == "potato"


def test_nutrition_fit_uses_per_serving_values():
    features, missing = build_feature_inputs({
        "main_ingredients": ["chicken", "rice"],
        "nutrition": {
            "calories": 2400,
            "protein": 240,
            "carbs": 200,
            "fat": 80,
            "servings": 4,
            "per_serving": {"calories": 600, "protein": 60, "carbs": 50, "fat": 20},
        },
    })
    assert not missing
    assert features["calories"] == 600
    assert features["protein"] == 60


def test_candidate_exposes_clean_display_name_and_per_serving_nutrition():
    pantry, _ = prepare_usable_pantry([
        {"id": "p1", "item_name": "Perfect portions boneless skinless chicken breasts", "quantity": 1},
    ])
    recipe = RecipeRecord(
        recipe_id="r1", recipe_name="Chicken", clean_recipe_name="Chicken",
        meal_types=[], cuisine_types=[], dish_types=[], ingredients=[RecipeIngredient(food="chicken breast", text="chicken breast")],
        main_ingredients=["chicken breast"], calories=1200, protein=160, carbs=40, fat=40,
        servings=4, url="", everyday_fit_score=80,
    )
    _, candidate = evaluate_recipe_candidate(recipe, pantry)
    assert candidate["matched_ingredients"][0]["display_name"] == "chicken breast"
    assert candidate["nutrition"]["per_serving"]["calories"] == 300


def test_missing_protein_has_higher_practicality_penalty_than_missing_staple():
    base = {
        "eligibility": "near_complete", "missing_main_ingredient_count": 1,
        "matched_ingredients": [{"recipe_ingredient": "rice"}], "main_ingredients": ["rice", "x"],
        "expiring_ingredients": [], "nutrition_fit": {"status": "available", "score_percent": 80},
        "everyday_fit_score": 80, "meal_types": [], "cuisine_types": [], "dish_types": [],
    }
    staple = calculate_smart_score({**base, "missing_ingredients": ["corn"]}, {})
    protein = calculate_smart_score({**base, "missing_ingredients": ["chicken breast"]}, {})
    assert staple["breakdown"]["practicality"]["points"] > protein["breakdown"]["practicality"]["points"]
