import unittest

from services.recommendations.meal_eligibility import Eligibility, classify_meal_eligibility
from services.recommendations.recipe_repository import dataset_audit, load_recipes


class RecipeRepositoryTests(unittest.TestCase):
    def test_dataset_loads_with_stable_unique_ids(self):
        recipes = load_recipes()
        self.assertGreater(len(recipes), 0)
        self.assertEqual(len(recipes), len({recipe.recipe_id for recipe in recipes}))
        self.assertTrue(all(recipe.recipe_id.startswith("recipe_") for recipe in recipes))

    def test_audit_count_matches_loaded_count(self):
        self.assertEqual(dataset_audit()["recipe_count"], len(load_recipes()))


class EligibilityTests(unittest.TestCase):
    def test_complete_requires_all_main_ingredients(self):
        result = classify_meal_eligibility(
            total_main_ingredients=4,
            matched_main_ingredients=4,
            missing_main_ingredients=[],
        )
        self.assertEqual(result.status, Eligibility.COMPLETE)

    def test_near_complete_allows_one_missing_at_75_percent(self):
        result = classify_meal_eligibility(
            total_main_ingredients=4,
            matched_main_ingredients=3,
            missing_main_ingredients=["chicken"],
        )
        self.assertEqual(result.status, Eligibility.NEAR_COMPLETE)

    def test_two_missing_can_be_near_complete(self):
        result = classify_meal_eligibility(
            total_main_ingredients=5,
            matched_main_ingredients=3,
            missing_main_ingredients=["chicken", "rice"],
        )
        self.assertEqual(result.status, Eligibility.NEAR_COMPLETE)

    def test_missing_main_ingredient_metadata_is_ineligible(self):
        result = classify_meal_eligibility(
            total_main_ingredients=0,
            matched_main_ingredients=0,
            missing_main_ingredients=[],
        )
        self.assertEqual(result.status, Eligibility.INELIGIBLE)


if __name__ == "__main__":
    unittest.main()
