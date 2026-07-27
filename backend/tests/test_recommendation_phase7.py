import unittest

from services.recommendations.smart_score import (
    SMART_SCORE_WEIGHTS,
    calculate_smart_score,
    score_and_rank_candidates,
)


def candidate(
    recipe_id="r1",
    *,
    matched=3,
    expiring_days=None,
    nutrition=80,
    cuisine=None,
    meal_type=None,
    everyday=80,
):
    expiring_days = expiring_days or []
    matched_items = [
        {
            "pantry_item_id": f"p{i}",
            "pantry_item_name": f"item {i}",
            "days_until_expiration": None,
        }
        for i in range(matched)
    ]
    expiring_items = []
    for index, days in enumerate(expiring_days):
        item = dict(matched_items[index])
        item["days_until_expiration"] = days
        item["expiration_state"] = "expiring"
        expiring_items.append(item)
    return {
        "recipe_id": recipe_id,
        "recipe_name": recipe_id,
        "eligibility": "complete",
        "main_ingredients": [f"item {i}" for i in range(matched)],
        "matched_ingredients": matched_items,
        "missing_ingredients": [],
        "expiring_ingredients": expiring_items,
        "cuisine_types": cuisine or [],
        "meal_types": meal_type or [],
        "everyday_fit_score": everyday,
        "nutrition_fit": {
            "status": "available" if nutrition is not None else "unavailable_model_error",
            "score_percent": nutrition,
        },
    }


class SmartScorePhase7Tests(unittest.TestCase):
    def test_weights_total_one_hundred(self):
        self.assertEqual(sum(SMART_SCORE_WEIGHTS.values()), 100.0)

    def test_score_is_bounded_and_has_full_breakdown(self):
        result = calculate_smart_score(candidate(expiring_days=[1]), {})
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertEqual(
            set(result["breakdown"]),
            {"pantry_usefulness", "expiration_priority", "nutrition_fit", "preference_fit", "practicality"},
        )

    def test_expiring_complete_meal_receives_material_priority(self):
        normal = calculate_smart_score(candidate("normal", expiring_days=[]), {})
        expiring = calculate_smart_score(candidate("expiring", expiring_days=[1]), {})
        self.assertGreater(expiring["score"], normal["score"])
        self.assertGreaterEqual(expiring["breakdown"]["expiration_priority"]["points"], 15)

    def test_expiration_never_changes_eligibility(self):
        item = candidate(expiring_days=[0])
        item["eligibility"] = "near_complete"
        result = calculate_smart_score(item, {})
        self.assertEqual(result["breakdown"]["pantry_usefulness"]["complete_meal_points"], 0)

    def test_nutrition_fit_is_twenty_five_percent_of_score(self):
        high = calculate_smart_score(candidate("high", nutrition=100), {})
        low = calculate_smart_score(candidate("low", nutrition=0), {})
        difference = high["breakdown"]["nutrition_fit"]["points"] - low["breakdown"]["nutrition_fit"]["points"]
        self.assertEqual(difference, 25.0)

    def test_more_pantry_ingredients_increase_usefulness(self):
        small = calculate_smart_score(candidate("small", matched=2), {})
        larger = calculate_smart_score(candidate("larger", matched=5), {})
        self.assertGreater(
            larger["breakdown"]["pantry_usefulness"]["points"],
            small["breakdown"]["pantry_usefulness"]["points"],
        )

    def test_preferences_are_optional_ranking_inputs_not_filters(self):
        profile = {
            "preferred_cuisine": "Italian",
            "preferred_meal_type": "Dinner",
            "quick_meals_preferred": True,
        }
        matching = calculate_smart_score(
            candidate(cuisine=["italian"], meal_type=["dinner"], everyday=90), profile
        )
        nonmatching = calculate_smart_score(candidate(cuisine=["mexican"], meal_type=["breakfast"]), profile)
        self.assertGreater(
            matching["breakdown"]["preference_fit"]["points"],
            nonmatching["breakdown"]["preference_fit"]["points"],
        )

    def test_unavailable_nutrition_uses_explicit_neutral_fallback(self):
        result = calculate_smart_score(candidate(nutrition=None), {})
        component = result["breakdown"]["nutrition_fit"]
        self.assertEqual(component["points"], 12.5)
        self.assertTrue(component["fallback_used"])

    def test_ranking_uses_smart_score_before_limit(self):
        weak = candidate("weak", matched=2, nutrition=20)
        strong = candidate("strong", matched=5, expiring_days=[0], nutrition=95)
        ranked, metadata = score_and_rank_candidates([weak, strong], {}, limit=1)
        self.assertEqual(ranked[0]["recipe_id"], "strong")
        self.assertEqual(metadata["smart_score_candidate_count"], 2)
        self.assertEqual(metadata["smart_score_returned_count"], 1)


if __name__ == "__main__":
    unittest.main()
