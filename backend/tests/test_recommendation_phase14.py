from services.recommendations.smart_swaps import find_smart_swaps
from services.recommendations.nutrition_fit import _calibrated_prediction


def test_smart_swap_rejects_bouillon_for_chicken_breast():
    swaps = find_smart_swaps(["chicken bouillon"], [{"item_name": "chicken breast"}])
    assert swaps == []


def test_smart_swap_allows_close_cheese_substitution():
    swaps = find_smart_swaps(["mozzarella cheese"], [{"item_name": "cheddar cheese"}])
    assert swaps and swaps[0]["role"] == "cheese"


def test_calibration_prevents_automatic_perfect_score():
    features = {"calories": 550.0, "protein": 30.0, "carbs": 50.0, "fat": 18.0, "ingredient_count": 8.0}
    assert _calibrated_prediction(100.0, features) < 100.0
