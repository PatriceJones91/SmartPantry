import unittest

from services.recommendations.diversity import (
    are_near_duplicates,
    recipe_similarity,
    recipe_signature,
    select_diverse_recommendations,
)


def item(recipe_id, score, ingredients, *, name=None, dish=None, cuisine=None, expiring=False, nutrition=70):
    expiry = [{"days_until_expiration": 1}] if expiring else []
    return {
        "recipe_id": recipe_id,
        "recipe_name": name or recipe_id,
        "main_ingredients": ingredients,
        "dish_types": dish or [],
        "cuisine_types": cuisine or [],
        "meal_types": ["dinner"],
        "smart_score": score,
        "nutrition_fit": {"status": "available", "score_percent": nutrition},
        "expiring_ingredients": expiry,
        "smart_score_details": {
            "breakdown": {"expiration_priority": {"points": 20 if expiring else 0}}
        },
    }


class DiversityPhase8Tests(unittest.TestCase):
    def test_signature_identifies_food_families(self):
        sig = recipe_signature(item("x", 80, ["chicken breast", "penne pasta"], dish=["main course"]))
        self.assertEqual(sig["protein_family"], "chicken")
        self.assertEqual(sig["starch_family"], "pasta")

    def test_near_duplicate_titles_and_ingredients_are_detected(self):
        a = item("a", 90, ["chicken", "rice", "broccoli"], name="Easy Chicken Rice Bowl")
        b = item("b", 89, ["chicken", "rice", "broccoli"], name="Chicken and Rice Bowl")
        self.assertTrue(are_near_duplicates(a, b))
        self.assertGreater(recipe_similarity(a, b), 0.7)

    def test_different_meals_are_not_duplicates(self):
        a = item("a", 90, ["chicken", "rice"], name="Chicken Rice Bowl")
        b = item("b", 89, ["salmon", "potato"], name="Baked Salmon and Potatoes")
        self.assertFalse(are_near_duplicates(a, b))

    def test_highest_smart_score_is_always_preserved(self):
        ranked = [
            item("top", 99, ["chicken", "rice"]),
            item("b", 88, ["salmon", "potato"]),
            item("c", 87, ["tofu", "noodles"]),
        ]
        selected, metadata = select_diverse_recommendations(ranked, limit=2)
        self.assertIn("top", [x["recipe_id"] for x in selected])
        self.assertTrue(metadata["highest_smart_score_preserved"])

    def test_expiry_led_candidate_is_protected(self):
        ranked = [
            item("normal1", 95, ["salmon", "potato"]),
            item("normal2", 94, ["tofu", "rice"]),
            item("expiry", 80, ["chicken", "pasta"], expiring=True),
        ]
        selected, metadata = select_diverse_recommendations(ranked, limit=2)
        self.assertIn("expiry", [x["recipe_id"] for x in selected])
        self.assertEqual(metadata["selected_expiry_led_count"], 1)

    def test_top_nutrition_candidate_is_protected_when_distinct(self):
        ranked = [
            item("top", 98, ["chicken", "rice"], nutrition=70),
            item("middle", 90, ["beef", "pasta"], nutrition=75),
            item("nutrition", 80, ["salmon", "potato"], nutrition=99),
        ]
        selected, _ = select_diverse_recommendations(ranked, limit=2)
        self.assertIn("nutrition", [x["recipe_id"] for x in selected])

    def test_near_duplicate_is_skipped_for_variety(self):
        ranked = [
            item("a", 95, ["chicken", "rice", "broccoli"], name="Chicken Rice Bowl"),
            item("b", 94, ["chicken", "rice", "broccoli"], name="Easy Chicken Rice Bowl"),
            item("c", 90, ["salmon", "potato", "spinach"], name="Baked Salmon"),
        ]
        selected, metadata = select_diverse_recommendations(ranked, limit=2)
        ids = [x["recipe_id"] for x in selected]
        self.assertEqual(ids, ["a", "c"])
        self.assertGreater(metadata["near_duplicates_skipped"], 0)

    def test_final_set_preserves_original_smart_score_order(self):
        ranked = [
            item("a", 95, ["chicken", "rice"]),
            item("b", 92, ["salmon", "potato"]),
            item("c", 89, ["tofu", "noodles"]),
        ]
        selected, _ = select_diverse_recommendations(ranked, limit=3)
        self.assertEqual([x["recipe_id"] for x in selected], ["a", "b", "c"])
        self.assertEqual([x["final_rank"] for x in selected], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
