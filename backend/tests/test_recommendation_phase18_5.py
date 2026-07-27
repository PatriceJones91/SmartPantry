from services.recommendations.recipe_realism import (
    filter_realistic_recipe_concepts,
    realism_decision,
)


def _recipe(name):
    return {"recipe_id": name.lower().replace(" ", "-"), "recipe_name": name}


def test_parmesan_pesto_waffles_are_suppressed():
    decision = realism_decision(_recipe("Parmesan Pesto Waffles"))
    assert decision["keep"] is False
    assert "waffle" in decision["reason"]


def test_normal_waffles_remain_available():
    assert realism_decision(_recipe("Classic Buttermilk Waffles"))["keep"] is True


def test_normal_pesto_meal_remains_available():
    assert realism_decision(_recipe("Chicken Pesto Pasta"))["keep"] is True


def test_filter_reports_suppressed_recipe():
    kept, metadata = filter_realistic_recipe_concepts([
        _recipe("Parmesan Pesto Waffles"),
        _recipe("Classic Buttermilk Waffles"),
    ])
    assert [item["recipe_name"] for item in kept] == ["Classic Buttermilk Waffles"]
    assert metadata["realism_suppressed_candidate_count"] == 1
    assert metadata["realism_suppressed_examples"][0]["recipe_name"] == "Parmesan Pesto Waffles"
