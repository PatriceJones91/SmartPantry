from services.recommendation_tracking import build_action_row, prepare_generation_records


def test_prepare_generation_assigns_session_and_result_ids():
    response = {
        "generated_at": "2026-07-21T00:00:00+00:00",
        "metadata": {},
        "recommendations": [
            {
                "recipe_id": "recipe-1",
                "recipe_name": "Pantry Meal",
                "final_rank": 1,
                "candidate_group": "other_complete",
                "smart_score": 88.0,
                "pantry_match_percent": 100.0,
                "nutrition_fit": {"score_percent": 81.0},
                "matched_ingredients": [{"pantry_item_id": "p1"}],
                "expiring_ingredients": [],
            }
        ],
    }
    enriched, session, results = prepare_generation_records(
        user_id="user-1",
        request_options={"limit": 15, "expiry_window_days": 7},
        response_payload=response,
        pantry=[{"id": "p1", "item_name": "Eggs", "quantity": 2}],
        profile={"id": "user-1", "username": "participant", "password_hash": "must-not-copy"},
    )
    assert enriched["metadata"]["session_id"] == session["id"]
    assert enriched["recommendations"][0]["recommendation_result_id"] == results[0]["id"]
    assert results[0]["session_id"] == session["id"]
    assert "password_hash" not in session["profile_snapshot"]


def test_action_row_uses_research_identifiers():
    row = build_action_row(
        {
            "user_id": "user-1",
            "session_id": "session-1",
            "recommendation_result_id": "result-1",
            "recipe_id": "recipe-1",
            "recipe_name": "Meal",
            "action": "saved",
            "smart_score": 90,
        }
    )
    assert row["session_id"] == "session-1"
    assert row["recipe_id"] == "recipe-1"
    assert row["action"] == "saved"
