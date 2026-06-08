from pathlib import Path
import ast
import json
import re

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

APP_DIR = Path(__file__).resolve().parent
DATASET_PATHS = [
    APP_DIR / "data" / "smart_pantry_recipes_clean.csv",
]
MODEL_DIR = APP_DIR / "ml"
MODEL_PATH = MODEL_DIR / "recommendation_model.pkl"
METRICS_PATH = MODEL_DIR / "recommendation_model_metrics.txt"


def find_dataset():
    for path in DATASET_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not find data/smart_pantry_recipes_clean.csv inside the app folder."
    )


def safe_number(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        if isinstance(value, str):
            value = value.replace("g", "").replace("kcal", "").replace(",", "").strip()
        return float(value)
    except Exception:
        return default


def parse_list(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return value
    text = str(value).strip()
    if not text:
        return []
    for parser in (ast.literal_eval, json.loads):
        try:
            parsed = parser(text)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    return [part.strip() for part in re.split(r",|;|\n", text) if part.strip()]


def build_training_dataframe(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    rows = []

    for _, row in df.iterrows():
        ingredients = parse_list(row.get("main_ingredients", row.get("ingredients", "")))
        ingredient_count = len(ingredients)
        if ingredient_count < 2 or ingredient_count > 12:
            continue

        calories = safe_number(row.get("calories", 0))
        protein = safe_number(row.get("protein", 0))
        carbs = safe_number(row.get("carbs", 0))
        fat = safe_number(row.get("fat", 0))
        everyday_fit_score = safe_number(row.get("everyday_fit_score", 50), 50)

        if calories <= 0:
            continue

        practicality = min(max(everyday_fit_score, 1), 100)
        nutrition_balance = 0
        if protein > 0:
            nutrition_balance += min(protein * 2, 25)
        if 250 <= calories <= 750:
            nutrition_balance += 15
        elif calories < 250:
            nutrition_balance += 5
        if fat <= 35:
            nutrition_balance += 10
        if carbs <= 100:
            nutrition_balance += 5

        target_score = max(
            1,
            min(100, (practicality * 0.65) + nutrition_balance - max(0, ingredient_count - 8) * 3),
        )

        rows.append(
            {
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "ingredient_count": ingredient_count,
                "health_score": target_score,
            }
        )

    return pd.DataFrame(rows)


def main():
    csv_path = find_dataset()
    print(f"Using dataset: {csv_path}")

    training_df = build_training_dataframe(csv_path)
    print(f"Training rows: {len(training_df)}")

    if training_df.empty or len(training_df) < 50:
        raise ValueError("Not enough usable rows to train the model. Check the clean CSV.")

    X = training_df[["calories", "protein", "carbs", "fat", "ingredient_count"]]
    y = training_df["health_score"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=150,
        random_state=42,
        n_jobs=-1,
        max_depth=12,
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    metrics_text = (
        f"Training rows: {len(training_df)}\n"
        f"Features: calories, protein, carbs, fat, ingredient_count\n"
        f"Target: nutrition/practicality support score\n"
        f"MAE: {mae:.4f}\n"
        f"R2: {r2:.4f}\n"
        f"Model path: {MODEL_PATH}\n"
    )
    METRICS_PATH.write_text(metrics_text)

    print(metrics_text)
    print("Model saved successfully.")


if __name__ == "__main__":
    main()
