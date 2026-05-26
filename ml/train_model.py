import ast
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

recipes_df = pd.read_csv(
    "data/recipes.csv"
)

nutrition_df = pd.read_csv(
    "data/Food_Nutrition_Dataset.csv"
)

def normalize_ingredient(name):

    return (
        str(name)
        .lower()
        .strip()
        .replace("-", " ")
        .replace("fresh ", "")
        .replace("dried ", "")
        .replace("extra virgin ", "")
        .replace("low fat ", "")
        .replace("boneless ", "")
        .replace("skinless ", "")
    )

nutrition_lookup = {}

for _, row in nutrition_df.iterrows():

    ingredient = normalize_ingredient(
        row["food_name"]
    )

    nutrition_lookup[ingredient] = {
        "calories": row["calories"],
        "protein": row["protein"],
        "carbs": row["carbs"],
        "fat": row["fat"]
    }

training_data = []

for _, recipe in recipes_df.iterrows():

    try:

        recipe_ingredients = [
            normalize_ingredient(i)
            for i in ast.literal_eval(
                recipe["ingredients"]
            )
        ]

    except:

        continue

    calories = 0
    protein = 0
    carbs = 0
    fat = 0

    matched_ingredients = 0

    for ingredient in recipe_ingredients:

        matched_nutrition = None

        for nutrition_key in nutrition_lookup:

            if (
                ingredient in nutrition_key
                or
                nutrition_key in ingredient
            ):

                matched_nutrition = nutrition_lookup[
                    nutrition_key
                ]

                break

        if matched_nutrition:

            matched_ingredients += 1

            nutrition = matched_nutrition

            calories += nutrition["calories"]
            protein += nutrition["protein"]
            carbs += nutrition["carbs"]
            fat += nutrition["fat"]

    if matched_ingredients == 0:
        continue

    health_score = max(
        1,
        (
            (protein * 3)
            + 50
            - fat
            - (calories / 30)
        )
    )

    training_data.append({
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "ingredient_count": len(recipe_ingredients),
        "health_score": health_score
    })

ml_df = pd.DataFrame(training_data)

print("Training rows:", len(ml_df))

X = ml_df[
    [
        "calories",
        "protein",
        "carbs",
        "fat",
        "ingredient_count"
    ]
]

y = ml_df["health_score"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(
    X_train,
    y_train
)

predictions = model.predict(X_test)

mae = mean_absolute_error(
    y_test,
    predictions
)

print(f"Model MAE: {mae}")

joblib.dump(
    model,
    "ml/recommendation_model.pkl"
)

print("Model saved successfully!")