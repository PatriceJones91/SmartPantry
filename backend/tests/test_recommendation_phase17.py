from datetime import datetime, timedelta, timezone

from services.recommendations.behavior_learning import score_behavior
from services.recommendations.smart_score import calculate_smart_score


def candidate(name="Chicken Soup", recipe_id="r1"):
    return {
        "recipe_id": recipe_id,
        "recipe_name": name,
        "eligibility": "complete",
        "main_ingredients": ["chicken", "carrot", "onion", "broth"],
        "matched_ingredients": [
            {"pantry_item_id": "1", "pantry_item_name": "chicken"},
            {"pantry_item_id": "2", "pantry_item_name": "carrot"},
            {"pantry_item_id": "3", "pantry_item_name": "onion"},
            {"pantry_item_id": "4", "pantry_item_name": "broth"},
        ],
        "missing_ingredients": [],
        "smart_swaps": [],
        "expiring_ingredients": [],
        "nutrition_fit": {"status": "available", "score_percent": 80},
        "meal_types": ["dinner"],
        "dish_types": ["soup"],
        "cuisine_types": ["everyday"],
    }


def test_saved_recipe_gets_positive_behavior_signal():
    profile = {"_behavior_actions": [{"recipe_id": "r1", "recipe_name": "Chicken Soup", "action": "saved"}]}
    points, detail = score_behavior(candidate(), profile)
    assert points > 5
    assert detail["exact_signal"] > 0


def test_recently_made_recipe_gets_fatigue_penalty():
    recent = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    profile = {"_behavior_actions": [{"recipe_id": "r1", "recipe_name": "Chicken Soup", "action": "made", "created_at": recent}]}
    points, detail = score_behavior(candidate(), profile)
    assert detail["fatigue_penalty"] == 4.0
    assert detail["days_since_last_made"] <= 2


def test_skipped_similar_recipe_reduces_signal():
    profile = {"_behavior_actions": [{"recipe_id": "other", "recipe_name": "Creamy Chicken Soup", "action": "skipped"}]}
    points, detail = score_behavior(candidate(), profile)
    assert points < 5
    assert detail["similar_recipe_signal"] < 0


def test_smart_score_has_adaptive_components():
    score = calculate_smart_score(candidate(), {"_behavior_actions": []})
    assert score["version"] == "phase_17_adaptive_v1"
    assert "pantry_usefulness" in score["breakdown"]
    assert "behavior_learning" in score["breakdown"]["preference_fit"]
    assert sum(score["weights"].values()) == 100
