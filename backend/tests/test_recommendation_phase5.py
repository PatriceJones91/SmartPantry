import unittest
from datetime import date

from services.recommendations.candidate_discovery import discover_candidates
from services.recommendations.profile_safety import (
    build_profile_safety_rules,
    evaluate_recipe_safety,
    filter_safe_recipes,
)
from services.recommendations.recipe_repository import RecipeIngredient, RecipeRecord


def recipe(recipe_id, name, ingredients):
    return RecipeRecord(
        recipe_id=recipe_id,
        recipe_name=name,
        clean_recipe_name=name,
        meal_types=["dinner"],
        cuisine_types=[],
        dish_types=["main course"],
        ingredients=[RecipeIngredient(food=item, text=item) for item in ingredients],
        main_ingredients=ingredients,
        calories=500,
        protein=30,
        carbs=50,
        fat=15,
        servings=2,
        url=f"https://example.com/{recipe_id}",
        everyday_fit_score=None,
    )


class ProfileSafetyTests(unittest.TestCase):
    def test_profile_terms_are_parsed_and_normalized(self):
        rules = build_profile_safety_rules({
            "allergies": "Peanuts; Shellfish",
            "avoid_foods": "mushrooms, olives",
            "dietary_restrictions": "Gluten-Free, no pork",
        })
        self.assertEqual(rules.allergies, ("peanuts", "shellfish"))
        self.assertEqual(rules.avoided_foods, ("mushrooms", "olives"))
        self.assertEqual(rules.restrictions, ("gluten_free", "pork_free"))

    def test_declared_allergy_excludes_recipe(self):
        decision = evaluate_recipe_safety(
            recipe("r1", "Peanut Noodles", ["noodles", "peanut butter"]),
            build_profile_safety_rules({"allergies": "peanut"}),
        )
        self.assertFalse(decision.safe)
        self.assertIn("peanut", decision.matched_terms)

    def test_avoided_food_excludes_recipe(self):
        decision = evaluate_recipe_safety(
            recipe("r2", "Mushroom Rice", ["mushroom", "rice"]),
            build_profile_safety_rules({"avoid_foods": "mushrooms"}),
        )
        self.assertFalse(decision.safe)

    def test_vegetarian_blocks_meat_but_not_eggs(self):
        rules = build_profile_safety_rules({"dietary_restrictions": "vegetarian"})
        self.assertFalse(evaluate_recipe_safety(recipe("r3", "Chicken Rice", ["chicken breast", "rice"]), rules).safe)
        self.assertTrue(evaluate_recipe_safety(recipe("r4", "Egg Rice", ["egg", "rice"]), rules).safe)

    def test_vegan_blocks_dairy_and_eggs(self):
        rules = build_profile_safety_rules({"dietary_restrictions": "vegan"})
        self.assertFalse(evaluate_recipe_safety(recipe("r5", "Cheese Pasta", ["pasta", "cheddar"]), rules).safe)
        self.assertFalse(evaluate_recipe_safety(recipe("r6", "Egg Rice", ["egg", "rice"]), rules).safe)
        self.assertTrue(evaluate_recipe_safety(recipe("r7", "Bean Rice", ["black bean", "rice"]), rules).safe)

    def test_pescatarian_allows_fish_but_blocks_chicken(self):
        rules = build_profile_safety_rules({"dietary_restrictions": "pescatarian"})
        self.assertTrue(evaluate_recipe_safety(recipe("r8", "Salmon Rice", ["salmon", "rice"]), rules).safe)
        self.assertFalse(evaluate_recipe_safety(recipe("r9", "Chicken Rice", ["chicken breast", "rice"]), rules).safe)

    def test_gluten_free_and_dairy_free_are_hard_filters(self):
        gf = build_profile_safety_rules({"dietary_restrictions": "gluten free"})
        df = build_profile_safety_rules({"dietary_restrictions": "dairy free"})
        self.assertFalse(evaluate_recipe_safety(recipe("r10", "Toast", ["bread", "egg"]), gf).safe)
        self.assertFalse(evaluate_recipe_safety(recipe("r11", "Cream Soup", ["cream", "potato"]), df).safe)

    def test_no_substring_false_positive_for_ham_in_yam(self):
        rules = build_profile_safety_rules({"dietary_restrictions": "pork free"})
        self.assertTrue(evaluate_recipe_safety(recipe("r12", "Baked Yam", ["yam"]), rules).safe)

    def test_safety_filter_runs_before_expiration_discovery(self):
        recipes = [
            recipe("unsafe", "Chicken Rice", ["chicken breast", "rice"]),
            recipe("safe", "Bean Rice", ["black bean", "rice"]),
        ]
        safe_recipes, metadata = filter_safe_recipes(
            recipes, {"dietary_restrictions": "vegetarian"}
        )
        pantry = [
            {"id": "p1", "item_name": "Chicken Breast", "quantity": 1, "expiration_date": "2026-07-21"},
            {"id": "p2", "item_name": "Black Beans", "quantity": 1, "expiration_date": "2026-07-21"},
            {"id": "p3", "item_name": "Rice", "quantity": 1, "expiration_date": "2026-08-01"},
        ]
        result = discover_candidates(safe_recipes, pantry, today=date(2026, 7, 20))
        self.assertEqual([item["recipe_id"] for item in result.recommendations], ["safe"])
        self.assertEqual(metadata["recipes_excluded_by_safety"], 1)


if __name__ == "__main__":
    unittest.main()
