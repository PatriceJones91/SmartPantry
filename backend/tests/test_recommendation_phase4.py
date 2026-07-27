import unittest
from datetime import date

from services.recommendations.candidate_discovery import (
    discover_candidates,
    evaluate_recipe_candidate,
    prepare_usable_pantry,
)
from services.recommendations.expiry_analyzer import ExpirationState, assess_expiration
from services.recommendations.meal_eligibility import Eligibility
from services.recommendations.recipe_repository import RecipeIngredient, RecipeRecord


def recipe(recipe_id, name, main_ingredients):
    return RecipeRecord(
        recipe_id=recipe_id,
        recipe_name=name,
        clean_recipe_name=name,
        meal_types=["dinner"],
        cuisine_types=[],
        dish_types=["main course"],
        ingredients=[RecipeIngredient(food=item, text=item) for item in main_ingredients],
        main_ingredients=main_ingredients,
        calories=500,
        protein=30,
        carbs=50,
        fat=15,
        servings=2,
        url=f"https://example.com/{recipe_id}",
        everyday_fit_score=None,
    )


class ExpirationAnalyzerTests(unittest.TestCase):
    def test_expiring_window_is_inclusive(self):
        result = assess_expiration("2026-07-27", today=date(2026, 7, 20), expiry_window_days=7)
        self.assertEqual(result.state, ExpirationState.EXPIRING)
        self.assertEqual(result.days_until_expiration, 7)

    def test_expired_item_is_not_usable(self):
        result = assess_expiration("2026-07-19", today=date(2026, 7, 20))
        self.assertEqual(result.state, ExpirationState.EXPIRED)
        self.assertFalse(result.is_usable)


class CandidateDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 7, 20)
        self.pantry = [
            {"id": "p1", "item_name": "Chicken Breasts", "quantity": 2, "expiration_date": "2026-07-21"},
            {"id": "p2", "item_name": "Rice", "quantity": 2, "expiration_date": "2027-01-01"},
            {"id": "p3", "item_name": "Eggs", "quantity": 6, "expiration_date": "2026-08-01"},
            {"id": "p4", "item_name": "Spinach", "quantity": 1, "expiration_date": "2026-07-19"},
            {"id": "p5", "item_name": "Bread", "quantity": 0, "expiration_date": "2026-07-22"},
        ]

    def test_complete_expiry_recipe_is_first_group(self):
        recipes = [
            recipe("r1", "Chicken Rice", ["chicken breast", "rice"]),
            recipe("r2", "Egg Rice", ["egg", "rice"]),
        ]
        result = discover_candidates(recipes, self.pantry, today=self.today, limit=15)
        self.assertEqual([item["recipe_id"] for item in result.recommendations], ["r1", "r2"])
        self.assertEqual(result.recommendations[0]["candidate_group"], "expiry_led_complete")
        self.assertEqual(result.recommendations[1]["candidate_group"], "other_complete")

    def test_expiration_does_not_make_incomplete_recipe_eligible(self):
        entries, _ = prepare_usable_pantry(self.pantry, today=self.today)
        decision, candidate = evaluate_recipe_candidate(
            recipe("r3", "Chicken Pasta", ["chicken breast", "pasta"]), entries
        )
        self.assertEqual(decision.status, Eligibility.INELIGIBLE)
        self.assertEqual(candidate["eligibility"], "ineligible")

    def test_non_expiring_complete_meal_is_still_returned(self):
        recipes = [recipe("r2", "Egg Rice", ["egg", "rice"])]
        result = discover_candidates(recipes, self.pantry, today=self.today)
        self.assertEqual(result.metadata["other_complete_count"], 1)
        self.assertEqual(result.recommendations[0]["recipe_id"], "r2")

    def test_expired_and_zero_quantity_items_are_excluded(self):
        recipes = [
            recipe("r4", "Spinach Eggs", ["spinach", "egg"]),
            recipe("r5", "Egg Sandwich", ["egg", "bread"]),
        ]
        result = discover_candidates(recipes, self.pantry, today=self.today)
        self.assertEqual(result.recommendations, [])
        self.assertEqual(result.metadata["expired_pantry_item_count"], 1)
        self.assertEqual(result.metadata["out_of_stock_pantry_item_count"], 1)

    def test_phase_has_no_smart_score(self):
        result = discover_candidates(
            [recipe("r1", "Chicken Rice", ["chicken breast", "rice"])],
            self.pantry,
            today=self.today,
        )
        self.assertIsNone(result.recommendations[0]["smart_score"])
        self.assertEqual(result.metadata["ranking_phase"], "phase_12_candidate_expansion")


if __name__ == "__main__":
    unittest.main()
