import unittest
from datetime import datetime

from pydantic import ValidationError

from models.recommendation_api import RecommendationGenerateRequestV1
from services.recommendations.api_adapter import build_api_response


def sample_recommendation():
    match = {
        "recipe_ingredient": "chicken breast",
        "normalized_ingredient": "chicken breast",
        "match_type": "exact",
        "pantry_item_id": "pantry-1",
        "pantry_item_name": "Chicken Breast",
        "expiration_state": "expiring",
        "expires_on": "2026-07-22",
        "days_until_expiration": 1,
    }
    breakdown = {
        name: {"points": points, "max_points": maximum}
        for name, points, maximum in [
            ("pantry_usefulness", 30, 30),
            ("expiration_priority", 20, 25),
            ("nutrition_fit", 22, 25),
            ("preference_fit", 8, 10),
            ("practicality", 9, 10),
        ]
    }
    return {
        "recipe_id": "recipe-1",
        "recipe_name": "Chicken Dinner",
        "recipe_url": "https://example.com/recipe-1",
        "final_rank": 1,
        "eligibility": "complete",
        "eligibility_reason": "All main ingredients matched",
        "candidate_group": "expiry_led_complete",
        "meal_types": ["dinner"],
        "cuisine_types": ["american"],
        "dish_types": ["main course"],
        "main_ingredients": ["chicken breast"],
        "matched_ingredients": [match],
        "missing_ingredients": [],
        "expiring_ingredients": [match],
        "pantry_match_percent": 100,
        "nutrition": {"calories": 500, "protein": 35, "carbs": 40, "fat": 18, "servings": 4},
        "nutrition_fit": {
            "status": "available",
            "score_percent": 88,
            "score_out_of_15": 13.2,
            "grade": "Very Good",
            "reasons": ["High protein"],
            "model_name": "RandomForestRegressor",
            "missing_features": [],
            "feature_inputs": {"calories": 500, "protein": 35, "carbs": 40, "fat": 18, "ingredient_count": 1},
            "error": "debug-only",
        },
        "preference_fit": {"points": 8, "max_points": 10, "score": 8, "reasons": []},
        "smart_score": 89,
        "smart_score_details": {
            "score": 89,
            "max_score": 100,
            "version": "phase_07_v1",
            "weights": {
                "pantry_usefulness": 30,
                "expiration_priority": 25,
                "nutrition_fit": 25,
                "preference_fit": 10,
                "practicality": 10,
            },
            "breakdown": breakdown,
            "reasons": ["Complete meal"],
        },
        "reasons": ["Complete meal"],
        "diversity_signature": {"dish_family": "main", "protein_family": "chicken"},
    }


class RecommendationApiPhase9Tests(unittest.TestCase):
    def test_request_defaults_are_stable(self):
        request = RecommendationGenerateRequestV1(user_id="user-1")
        self.assertEqual(request.limit, 15)
        self.assertEqual(request.expiry_window_days, 7)
        self.assertFalse(request.include_debug)

    def test_request_limit_cannot_exceed_fifteen(self):
        with self.assertRaises(ValidationError):
            RecommendationGenerateRequestV1(user_id="user-1", limit=16)

    def test_response_has_version_timestamp_and_user(self):
        response = build_api_response(
            user_id="user-1",
            engine_result={"recommendations": [sample_recommendation()], "metadata": {}},
            requested_limit=15,
            include_debug=False,
        )
        self.assertEqual(response.api_version, "1.0")
        self.assertEqual(response.user_id, "user-1")
        self.assertIsInstance(response.generated_at, datetime)
        self.assertEqual(response.metadata.api_contract_version, "1.0")

    def test_debug_fields_are_hidden_by_default(self):
        response = build_api_response(
            user_id="user-1",
            engine_result={
                "recommendations": [sample_recommendation()],
                "metadata": {"nutrition_fit_model_path": "/private/model.pkl"},
            },
            requested_limit=15,
            include_debug=False,
        )
        nutrition_fit = response.recommendations[0].nutrition_fit
        self.assertIsNone(nutrition_fit.feature_inputs)
        self.assertIsNone(nutrition_fit.error)
        self.assertNotIn("nutrition_fit_model_path", response.metadata.model_extra or {})

    def test_debug_fields_can_be_requested(self):
        response = build_api_response(
            user_id="user-1",
            engine_result={"recommendations": [sample_recommendation()], "metadata": {}},
            requested_limit=15,
            include_debug=True,
        )
        self.assertIsNotNone(response.recommendations[0].nutrition_fit.feature_inputs)
        self.assertEqual(response.recommendations[0].nutrition_fit.error, "debug-only")
        self.assertTrue(response.metadata.debug_included)

    def test_contract_accepts_near_complete_meals(self):
        recipe = sample_recommendation()
        recipe["eligibility"] = "near_complete"
        recipe["missing_main_ingredient_count"] = 1
        recipe["eligibility_tier"] = 1
        recipe["candidate_group"] = "other_near_complete"
        response = build_api_response(
            user_id="user-1",
            engine_result={"recommendations": [recipe], "metadata": {}},
            requested_limit=15,
            include_debug=False,
        )
        self.assertEqual(response.recommendations[0].eligibility, "near_complete")

    def test_returned_count_is_derived_from_payload(self):
        response = build_api_response(
            user_id="user-1",
            engine_result={
                "recommendations": [sample_recommendation()],
                "metadata": {"returned_count": 999},
            },
            requested_limit=10,
            include_debug=False,
        )
        self.assertEqual(response.metadata.returned_count, 1)
        self.assertEqual(response.metadata.requested_limit, 10)


if __name__ == "__main__":
    unittest.main()
