import unittest

from services.recommendations.ingredient_normalizer import (
    ingredients_equivalent,
    normalize_ingredient,
)
from services.recommendations.pantry_matcher import (
    match_recipe_ingredient,
    prepare_pantry_items,
)


class IngredientNormalizerTests(unittest.TestCase):
    def test_removes_quantity_unit_and_preparation(self):
        result = normalize_ingredient("2 cups finely chopped fresh tomatoes")
        self.assertEqual(result.canonical, "tomato")

    def test_controlled_chicken_aliases(self):
        self.assertEqual(
            normalize_ingredient("boneless skinless chicken breasts, diced").canonical,
            "chicken breast",
        )
        self.assertTrue(ingredients_equivalent("chicken breast fillet", "Chicken Breasts"))

    def test_common_aliases(self):
        self.assertEqual(normalize_ingredient("garbanzo beans").canonical, "chickpea")
        self.assertEqual(normalize_ingredient("scallions").canonical, "green onion")

    def test_false_matches_are_rejected(self):
        self.assertFalse(ingredients_equivalent("chicken stock", "chicken breast"))
        self.assertFalse(ingredients_equivalent("coconut milk", "whole milk"))
        self.assertFalse(ingredients_equivalent("peanut oil", "peanuts"))
        self.assertFalse(ingredients_equivalent("tomato sauce", "tomato"))


class PantryMatcherTests(unittest.TestCase):
    def setUp(self):
        self.pantry = prepare_pantry_items(
            [
                {
                    "id": "p1",
                    "item_name": "Chicken Breasts",
                    "quantity": 2,
                    "unit": "lb",
                    "expiration_date": "2026-07-20",
                },
                {"id": "p2", "item_name": "Garbanzo Beans", "quantity": 1, "unit": "can"},
            ]
        )

    def test_returns_stable_pantry_id(self):
        result = match_recipe_ingredient("2 boneless chicken breasts, diced", self.pantry)
        self.assertTrue(result.matched)
        self.assertEqual(result.pantry_item_id, "p1")
        self.assertEqual(result.normalized_ingredient, "chicken breast")
        self.assertEqual(result.match_type, "alias")

    def test_unmatched_result_is_explicit(self):
        result = match_recipe_ingredient("tomato sauce", self.pantry)
        self.assertFalse(result.matched)
        self.assertEqual(result.match_type, "none")
        self.assertIsNone(result.pantry_item_id)


if __name__ == "__main__":
    unittest.main()
