from services.recommendations.ingredient_normalizer import ingredients_equivalent
from services.recommendations.smart_swaps import find_smart_swaps
from services.recommendations.diversity import select_diverse_recommendations


def _candidate(recipe_id, name, score, ingredients, expiring=False):
    return {
        "recipe_id": recipe_id,
        "recipe_name": name,
        "smart_score": score,
        "main_ingredients": ingredients,
        "meal_types": ["dinner"],
        "dish_types": ["main course"],
        "cuisine_types": ["american"],
        "expiring_ingredients": [{"days_until_expiration": 2}] if expiring else [],
        "smart_score_details": {"breakdown": {"expiration_priority": {"points": 18 if expiring else 0}}},
    }


def test_generic_flour_matches_all_purpose_flour():
    assert ingredients_equivalent("flour", "all-purpose flour")


def test_smart_swap_never_offers_all_purpose_flour_for_flour():
    swaps = find_smart_swaps(["flour"], [{"item_name": "all-purpose flour"}])
    assert swaps == []


def test_diversity_surfaces_strong_available_protein_families_before_more_chicken():
    candidates = [
        _candidate("c1", "Chicken Dinner One", 90, ["chicken breast", "potato"], True),
        _candidate("c2", "Chicken Dinner Two", 89, ["chicken breast", "rice"], True),
        _candidate("c3", "Chicken Dinner Three", 88, ["chicken breast", "pasta"], True),
        _candidate("c4", "Chicken Dinner Four", 87, ["chicken breast", "bread"], True),
        _candidate("s1", "Garlic Shrimp", 84, ["shrimp", "garlic"]),
        _candidate("b1", "Ground Beef Burger", 83, ["ground beef", "hamburger bun"]),
        _candidate("l1", "Herb Lamb Chops", 82, ["lamb chops", "herbs"]),
    ]
    selected, _ = select_diverse_recommendations(candidates, limit=7)
    first_five = " ".join(item["recipe_name"].lower() for item in selected[:5])
    assert "shrimp" in first_five
    assert "beef" in first_five or "burger" in first_five
    assert "lamb" in first_five
