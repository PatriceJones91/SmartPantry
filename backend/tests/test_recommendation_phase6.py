import unittest

from services.recommendations.nutrition_fit import (
    EXPECTED_FEATURES,
    build_feature_inputs,
    calculate_nutrition_fit,
    enrich_candidates_with_nutrition_fit,
    load_nutrition_model,
)


class FixedModel:
    def __init__(self, prediction=84.0):
        self.prediction = prediction
        self.rows = []

    def predict(self, rows):
        self.rows.extend(rows)
        return [self.prediction for _ in rows]


def candidate(recipe_id="r1", calories=500, protein=30, carbs=50, fat=18):
    return {
        "recipe_id": recipe_id,
        "recipe_name": "Test Meal",
        "main_ingredients": ["chicken breast", "rice", "broccoli"],
        "nutrition": {
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "servings": 2,
        },
        "candidate_group": "other_complete",
    }


class NutritionFitPhase6Tests(unittest.TestCase):
    def test_model_schema_matches_phase_contract(self):
        model = load_nutrition_model()
        self.assertEqual(tuple(model.feature_names_in_), EXPECTED_FEATURES)
        self.assertEqual(model.n_features_in_, 5)

    def test_feature_inputs_use_exact_training_order(self):
        values, missing = build_feature_inputs(candidate())
        self.assertFalse(missing)
        self.assertEqual(list(values), list(EXPECTED_FEATURES))
        self.assertEqual(values["ingredient_count"], 3.0)

    def test_missing_required_nutrition_is_not_replaced_with_zero(self):
        result = calculate_nutrition_fit(candidate(calories=None), model=FixedModel())
        self.assertEqual(result.status, "unavailable_missing_nutrition")
        self.assertIsNone(result.score_percent)
        self.assertIn("calories", result.missing_features)

    def test_prediction_is_returned_as_percent_and_out_of_15(self):
        model = FixedModel(84.0)
        result = calculate_nutrition_fit(candidate(), model=model)
        self.assertEqual(result.status, "available")
        self.assertEqual(result.score_percent, 84.0)
        self.assertEqual(result.score_out_of_15, 12.6)
        self.assertEqual(result.grade, "Very Good")
        self.assertEqual(model.rows[0], [500.0, 30.0, 50.0, 18.0, 3.0])

    def test_prediction_is_clamped_to_zero_to_one_hundred(self):
        high = calculate_nutrition_fit(candidate(), model=FixedModel(120))
        low = calculate_nutrition_fit(candidate(), model=FixedModel(-10))
        self.assertEqual(high.score_percent, 100.0)
        self.assertEqual(low.score_percent, 0.0)

    def test_enrichment_keeps_original_candidate_order(self):
        candidates = [candidate("first"), candidate("second")]
        enriched, metadata = enrich_candidates_with_nutrition_fit(
            candidates, model=FixedModel(75), include_debug=True
        )
        self.assertEqual([item["recipe_id"] for item in enriched], ["first", "second"])
        self.assertFalse(metadata["nutrition_fit_changed_candidate_order"])
        self.assertIn("feature_inputs", enriched[0]["nutrition_fit"])

    def test_debug_inputs_can_be_omitted_from_public_payload(self):
        enriched, metadata = enrich_candidates_with_nutrition_fit(
            [candidate()], model=FixedModel(75), include_debug=False
        )
        self.assertNotIn("feature_inputs", enriched[0]["nutrition_fit"])
        self.assertFalse(metadata["nutrition_fit_debug_inputs_included"])

    def test_real_model_produces_bounded_prediction(self):
        result = calculate_nutrition_fit(candidate())
        self.assertEqual(result.status, "available")
        self.assertGreaterEqual(result.score_percent, 0)
        self.assertLessEqual(result.score_percent, 100)


if __name__ == "__main__":
    unittest.main()
