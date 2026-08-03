from services.dashboard_grocery import (
    build_grocery_suggestions,
    grocery_key,
    pantry_covers_name,
)


def test_grocery_key_normalizes_plural_names():
    assert grocery_key("Tomatoes") == grocery_key("tomato")


def test_existing_pantry_item_is_not_suggested():
    rows = [
        {
            "recipe_name": "Tomato Soup",
            "final_rank": 1,
            "recommendation_snapshot": {
                "missing_ingredients": ["tomatoes"],
                "smart_swaps": [],
            },
        }
    ]
    assert build_grocery_suggestions(rows, [{"item_name": "Fresh tomato"}]) == []


def test_smart_swap_covered_ingredient_is_not_suggested():
    rows = [
        {
            "recipe_name": "Crunchy Chicken",
            "final_rank": 1,
            "recommendation_snapshot": {
                "missing_ingredients": ["breadcrumbs"],
                "smart_swaps": [
                    {"needed": "breadcrumbs", "use_instead": "corn flakes"}
                ],
            },
        }
    ]
    assert build_grocery_suggestions(rows, []) == []


def test_items_are_ranked_by_number_of_meals_unlocked():
    rows = [
        {
            "recipe_name": "Meal One",
            "final_rank": 1,
            "recommendation_snapshot": {
                "missing_ingredients": ["chicken broth", "tomatoes"],
                "smart_swaps": [],
            },
        },
        {
            "recipe_name": "Meal Two",
            "final_rank": 2,
            "recommendation_snapshot": {
                "missing_ingredients": ["chicken broth"],
                "smart_swaps": [],
            },
        },
    ]

    suggestions = build_grocery_suggestions(rows, [])
    assert suggestions[0]["item"] == "Chicken broth"
    assert suggestions[0]["meal_count"] == 2
    assert suggestions[1]["item"] == "Tomatoes"
