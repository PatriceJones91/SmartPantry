from services.recommendations.recommendation_quality import audit_candidate
from services.recommendations.smart_swaps import find_smart_swaps


def _candidate(**overrides):
    base = {
        "recipe_id": "r1",
        "recipe_name": "Test Dinner",
        "eligibility": "near_complete",
        "candidate_group": "other_near_complete",
        "main_ingredients": ["chicken breast", "rice crisp cereal"],
        "missing_ingredients": ["rice crisp cereal"],
        "matched_ingredients": [{"recipe_ingredient": "chicken breast"}],
        "smart_swaps": [],
        "expiring_ingredients": [],
        "nutrition_fit": {"score_percent": 82},
        "smart_score": 74,
    }
    base.update(overrides)
    return base


def test_macaroni_does_not_swap_to_angel_hair():
    swaps = find_smart_swaps(
        ["elbow macaroni"],
        [{"item_name": "angel hair pasta"}],
        recipe_context={"recipe_name": "Homemade Macaroni and Cheese", "dish_types": ["main dish"]},
    )
    assert swaps == []


def test_cereal_does_not_swap_to_brown_rice():
    swaps = find_smart_swaps(
        ["rice crisp cereal"],
        [{"item_name": "brown rice"}],
        recipe_context={"recipe_name": "Oven-Fried Chicken", "dish_types": ["main dish"]},
    )
    assert swaps == []


def test_context_safe_crunchy_swap_is_allowed():
    swaps = find_smart_swaps(
        ["rice crisp cereal"],
        [{"item_name": "panko breadcrumbs"}],
        recipe_context={"recipe_name": "Oven-Fried Chicken", "dish_types": ["main dish"]},
    )
    assert swaps
    assert swaps[0]["confidence"] == "reasonable"


def test_quality_audit_corrects_false_complete_claim():
    result = audit_candidate(_candidate(eligibility="complete", missing_ingredients=["rice crisp cereal"]))
    assert result["eligibility"] == "near_complete"
    assert result["missing_main_ingredient_count"] == 1
    assert result["quality_validation"]["eligibility_corrected"] is True


def test_quality_audit_adds_explanation_and_confidence():
    result = audit_candidate(_candidate())
    assert "Uses 1 pantry ingredient" in result["recommendation_explanation"]
    assert result["quality_validation"]["confidence"] in {"medium", "exploratory"}
