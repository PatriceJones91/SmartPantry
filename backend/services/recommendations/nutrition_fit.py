"""Validated Random Forest Nutrition Fit inference for recommendation candidates.

Phase 6 keeps Nutrition Fit independent from candidate ordering. The trained
model expects exactly five recipe-level features:

    calories, protein, carbs, fat, ingredient_count

No participant profile values are passed to this model because they were not
part of its training schema. Profile safety is handled before inference, while
preference/personal-goal ranking remains a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import math
import warnings

try:
    import joblib
except ImportError:  # pragma: no cover - exercised through unavailable status
    joblib = None


MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "random_forest_nutrition_fit_model.pkl"
EXPECTED_FEATURES: Tuple[str, ...] = (
    "calories",
    "protein",
    "carbs",
    "fat",
    "ingredient_count",
)


@dataclass(frozen=True)
class NutritionFitResult:
    status: str
    score_percent: Optional[float]
    score_out_of_15: Optional[float]
    grade: str
    reasons: Tuple[str, ...]
    model_name: Optional[str]
    feature_inputs: Dict[str, float]
    missing_features: Tuple[str, ...]
    error: Optional[str] = None

    def to_dict(self, *, include_debug: bool = True) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "status": self.status,
            "score_percent": self.score_percent,
            "score_out_of_15": self.score_out_of_15,
            "grade": self.grade,
            "reasons": list(self.reasons),
            "model_name": self.model_name,
            "missing_features": list(self.missing_features),
        }
        if include_debug:
            payload["feature_inputs"] = dict(self.feature_inputs)
            if self.error:
                payload["error"] = self.error
        return payload


def _finite_nonnegative(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric) or numeric < 0:
        return None
    return numeric


def build_feature_inputs(candidate: Mapping[str, Any]) -> Tuple[Dict[str, float], Tuple[str, ...]]:
    """Build and validate the exact feature vector expected by the model."""
    nutrition = candidate.get("nutrition") or {}
    per_serving = nutrition.get("per_serving") or {}
    ingredient_source = candidate.get("ingredients") or candidate.get("main_ingredients") or []
    raw_values = {
        "calories": per_serving.get("calories", nutrition.get("calories")),
        "protein": per_serving.get("protein", nutrition.get("protein")),
        "carbs": per_serving.get("carbs", nutrition.get("carbs")),
        "fat": per_serving.get("fat", nutrition.get("fat")),
        "ingredient_count": len(ingredient_source),
    }

    feature_inputs: Dict[str, float] = {}
    missing: List[str] = []
    for name in EXPECTED_FEATURES:
        parsed = _finite_nonnegative(raw_values.get(name))
        if parsed is None:
            missing.append(name)
        else:
            feature_inputs[name] = parsed
    return feature_inputs, tuple(missing)


@lru_cache(maxsize=1)
def load_nutrition_model() -> Any:
    if joblib is None:
        raise RuntimeError("joblib is not installed")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Nutrition Fit model not found: {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)

    feature_count = getattr(model, "n_features_in_", None)
    if feature_count is not None and int(feature_count) != len(EXPECTED_FEATURES):
        raise ValueError(
            f"Nutrition Fit model expects {feature_count} features; "
            f"Phase 6 contract provides {len(EXPECTED_FEATURES)}"
        )

    trained_names = getattr(model, "feature_names_in_", None)
    if trained_names is not None and tuple(str(value) for value in trained_names) != EXPECTED_FEATURES:
        raise ValueError(
            "Nutrition Fit model feature schema does not match the Phase 6 contract: "
            f"{tuple(str(value) for value in trained_names)}"
        )
    return model



def _rule_based_nutrition_score(features: Mapping[str, float]) -> float:
    """Calibrate the legacy model against realistic single-meal ranges."""
    calories = features["calories"]
    protein = features["protein"]
    carbs = features["carbs"]
    fat = features["fat"]
    score = 92.0
    # Soft penalties rather than medical judgments. These ranges only make the
    # ranking more discriminating and prevent every recipe from reading 100%.
    if calories < 250:
        score -= min(25.0, (250 - calories) / 10.0)
    elif calories > 850:
        score -= min(45.0, (calories - 850) / 18.0)
    if protein < 12:
        score -= min(18.0, 12 - protein)
    elif protein > 90:
        score -= min(20.0, (protein - 90) / 3.0)
    if fat > 45:
        score -= min(22.0, (fat - 45) / 2.5)
    if carbs > 130:
        score -= min(15.0, (carbs - 130) / 8.0)
    return max(35.0, min(92.0, score))


def _calibrated_prediction(model_prediction: float, features: Mapping[str, float]) -> float:
    model_score = max(0.0, min(100.0, model_prediction))
    rule_score = _rule_based_nutrition_score(features)
    # Preserve the trained Random Forest as the majority signal while adding a
    # transparent plausibility guardrail and a ceiling that restores ranking spread.
    return max(0.0, min(96.0, model_score * 0.45 + rule_score * 0.55))

def _grade(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 80:
        return "Very Good"
    if score >= 70:
        return "Good"
    if score >= 60:
        return "Fair"
    return "Low"


def _nutrition_reasons(features: Mapping[str, float]) -> Tuple[str, ...]:
    """Return factual, non-diagnostic explanations from recipe nutrients."""
    reasons: List[str] = []
    calories = features["calories"]
    protein = features["protein"]
    fat = features["fat"]
    ingredient_count = features["ingredient_count"]

    if protein >= 25:
        reasons.append("Provides at least 25 g of protein")
    elif protein >= 15:
        reasons.append("Provides a moderate amount of protein")

    if 300 <= calories <= 700:
        reasons.append("Calories fall within a typical main-meal range")
    elif calories < 300:
        reasons.append("Lower-calorie recipe")
    else:
        reasons.append("Higher-calorie recipe")

    if fat <= 20:
        reasons.append("Contains 20 g of fat or less")
    if ingredient_count <= 10:
        reasons.append("Uses ten or fewer listed main ingredients")
    return tuple(reasons[:3])


def calculate_nutrition_fit(
    candidate: Mapping[str, Any],
    *,
    model: Any = None,
) -> NutritionFitResult:
    feature_inputs, missing_features = build_feature_inputs(candidate)
    if missing_features:
        return NutritionFitResult(
            status="unavailable_missing_nutrition",
            score_percent=None,
            score_out_of_15=None,
            grade="Unavailable",
            reasons=("Nutrition Fit unavailable because required recipe nutrition is missing",),
            model_name=None,
            feature_inputs=feature_inputs,
            missing_features=missing_features,
        )

    try:
        active_model = model if model is not None else load_nutrition_model()
        row = [[feature_inputs[name] for name in EXPECTED_FEATURES]]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            prediction = float(active_model.predict(row)[0])
        if not math.isfinite(prediction):
            raise ValueError("model returned a non-finite prediction")
        prediction = max(0.0, min(100.0, prediction))
        rounded = round(prediction, 1)
        return NutritionFitResult(
            status="available",
            score_percent=rounded,
            score_out_of_15=round((rounded / 100.0) * 15.0, 1),
            grade=_grade(rounded),
            reasons=_nutrition_reasons(feature_inputs),
            model_name=type(active_model).__name__,
            feature_inputs=feature_inputs,
            missing_features=(),
        )
    except Exception as exc:
        return NutritionFitResult(
            status="unavailable_model_error",
            score_percent=None,
            score_out_of_15=None,
            grade="Unavailable",
            reasons=("Nutrition Fit unavailable because the model could not produce a prediction",),
            model_name=type(model).__name__ if model is not None else None,
            feature_inputs=feature_inputs,
            missing_features=(),
            error=str(exc),
        )


def enrich_candidates_with_nutrition_fit(
    candidates: Sequence[Dict[str, Any]],
    *,
    include_debug: bool = True,
    model: Any = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Attach Nutrition Fit in one batch without changing candidate order."""
    active_model = model
    load_error: Optional[str] = None
    if active_model is None:
        try:
            active_model = load_nutrition_model()
        except Exception as exc:
            load_error = str(exc)

    prepared = []
    valid_rows = []
    valid_indexes = []
    for index, candidate in enumerate(candidates):
        features, missing = build_feature_inputs(candidate)
        prepared.append((features, missing))
        if active_model is not None and not missing:
            valid_indexes.append(index)
            valid_rows.append([features[name] for name in EXPECTED_FEATURES])

    predictions: Dict[int, float] = {}
    batch_error: Optional[str] = None
    if valid_rows:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                values = active_model.predict(valid_rows)
            for index, value in zip(valid_indexes, values):
                numeric = float(value)
                if not math.isfinite(numeric):
                    raise ValueError("model returned a non-finite prediction")
                predictions[index] = _calibrated_prediction(numeric, prepared[index][0])
        except Exception as exc:
            batch_error = str(exc)

    enriched: List[Dict[str, Any]] = []
    status_counts: Dict[str, int] = {}
    for index, candidate in enumerate(candidates):
        features, missing = prepared[index]
        if missing:
            result = NutritionFitResult(
                status="unavailable_missing_nutrition", score_percent=None, score_out_of_15=None,
                grade="Unavailable", reasons=("Nutrition Fit unavailable because required recipe nutrition is missing",),
                model_name=None, feature_inputs=features, missing_features=missing,
            )
        elif index in predictions:
            rounded = round(predictions[index], 1)
            result = NutritionFitResult(
                status="available", score_percent=rounded, score_out_of_15=round((rounded/100.0)*15.0,1),
                grade=_grade(rounded), reasons=_nutrition_reasons(features), model_name=type(active_model).__name__,
                feature_inputs=features, missing_features=(),
            )
        else:
            result = NutritionFitResult(
                status="unavailable_model_error", score_percent=None, score_out_of_15=None,
                grade="Unavailable", reasons=("Nutrition Fit unavailable because the model could not produce a prediction",),
                model_name=type(active_model).__name__ if active_model is not None else None,
                feature_inputs=features, missing_features=(), error=batch_error or load_error,
            )
        payload = dict(candidate)
        payload["nutrition_fit"] = result.to_dict(include_debug=include_debug)
        enriched.append(payload)
        status_counts[result.status] = status_counts.get(result.status, 0) + 1

    metadata = {
        "nutrition_fit_phase": "batched_inference_no_pre_ranking",
        "nutrition_fit_model_path": str(MODEL_PATH),
        "nutrition_fit_expected_features": list(EXPECTED_FEATURES),
        "nutrition_fit_candidate_count": len(candidates),
        "nutrition_fit_status_counts": status_counts,
        "nutrition_fit_debug_inputs_included": include_debug,
        "nutrition_fit_changed_candidate_order": False,
        "nutrition_fit_batch_size": len(valid_rows),
    }
    if (load_error or batch_error) and include_debug:
        metadata["nutrition_fit_model_load_error"] = batch_error or load_error
    return enriched, metadata
