from services.recommendation_tracking import build_action_row

def _base(action: str):
    return {
        "user_id": "user-1",
        "session_id": "session-1",
        "recommendation_result_id": "result-1",
        "recipe_id": "recipe-1",
        "recipe_name": "Test Meal",
        "action": action,
        "smart_score": 82.5,
        "metadata": {"used_ingredients": [{"item_name": "flour", "amount_used": 0.5}]},
    }

def test_made_action_contract():
    row = build_action_row(_base("made"))
    assert row["action"] == "made"
    assert row["session_id"] == "session-1"

def test_used_elsewhere_action_contract():
    row = build_action_row(_base("used_elsewhere"))
    assert row["action"] == "used_elsewhere"

def test_not_used_action_contract():
    row = build_action_row(_base("not_used"))
    assert row["action"] == "not_used"

def test_custom_meal_action_contract():
    payload = _base("custom_meal")
    payload["recommendation_result_id"] = None
    payload["recipe_id"] = "custom:omelet"
    row = build_action_row(payload)
    assert row["action"] == "custom_meal"
    assert row["recipe_id"] == "custom:omelet"
