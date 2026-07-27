import unittest
from datetime import date
from models.recommendation_api import RecommendationResponse
from services.recommendations.meal_eligibility import Eligibility, classify_meal_eligibility
from services.recommendations.smart_score import score_and_rank_candidates


def candidate(recipe_id, eligibility, missing, score_hint=80, expiring=False):
    match = {"recipe_ingredient":"egg","normalized_ingredient":"egg","match_type":"exact","pantry_item_id":"p1","pantry_item_name":"Egg","expiration_state":"expiring" if expiring else "fresh","expires_on":"2026-07-22","days_until_expiration":1 if expiring else 20}
    return {
        "recipe_id": recipe_id, "recipe_name": recipe_id, "recipe_url":"", "eligibility":eligibility,
        "eligibility_reason":"test", "eligibility_tier":0 if eligibility=="complete" else len(missing),
        "missing_main_ingredient_count":len(missing),
        "candidate_group": ("expiry_led_" if expiring else "other_") + ("complete" if eligibility=="complete" else "near_complete"),
        "meal_types":[],"cuisine_types":[],"dish_types":[],"main_ingredients":["egg","rice","beans"],
        "matched_ingredients":[match],"missing_ingredients":missing,"expiring_ingredients":[match] if expiring else [],
        "pantry_match_percent":100 if not missing else 66.7,"everyday_fit_score":score_hint,
        "nutrition":{"calories":500,"protein":25,"carbs":50,"fat":15,"servings":2},
        "nutrition_fit":{"status":"available","score_percent":score_hint,"grade":"Good","reasons":[],"score_out_of_15":12,"model_name":"x","missing_features":[]},
    }

class Phase12Tests(unittest.TestCase):
    def test_one_missing_is_near_complete(self):
        d=classify_meal_eligibility(total_main_ingredients=4, matched_main_ingredients=3, missing_main_ingredients=["cheese"])
        self.assertEqual(d.status, Eligibility.NEAR_COMPLETE); self.assertEqual(d.tier,1)

    def test_two_missing_requires_real_pantry_base(self):
        d=classify_meal_eligibility(total_main_ingredients=5, matched_main_ingredients=3, missing_main_ingredients=["cheese","bread"])
        self.assertEqual(d.status, Eligibility.NEAR_COMPLETE); self.assertEqual(d.tier,2)

    def test_complete_always_ranks_above_near_complete(self):
        complete=candidate("complete","complete",[],score_hint=20)
        near=candidate("near","near_complete",["cheese"],score_hint=100,expiring=True)
        ranked,_=score_and_rank_candidates([near,complete],{},limit=2)
        self.assertEqual(ranked[0]["recipe_id"],"complete")

    def test_api_accepts_near_complete(self):
        c=candidate("near","near_complete",["cheese"])
        c.update({"final_rank":1,"preference_fit":{},"smart_score":70,"smart_score_details":{"score":70,"max_score":100,"version":"x","weights":{},"breakdown":{},"reasons":[]},"reasons":[],"diversity_signature":{}})
        parsed=RecommendationResponse.model_validate(c)
        self.assertEqual(parsed.eligibility,"near_complete")

if __name__ == '__main__': unittest.main()
