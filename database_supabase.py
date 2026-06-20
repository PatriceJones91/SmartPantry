from datetime import datetime, timezone
import hashlib
import json

import pandas as pd
import streamlit as st
from supabase import create_client


@st.cache_resource(show_spinner=False)
def get_supabase_client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "Supabase secrets are missing. Check .streamlit/secrets.toml for SUPABASE_URL and SUPABASE_KEY."
        )

    return create_client(url, key)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def hash_password(password):
    return hashlib.sha256(str(password).encode("utf-8")).hexdigest()


def to_dataframe(data):
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def normalize_bool(value):
    if isinstance(value, bool):
        return value
    if str(value).lower() in ["yes", "true", "1", "made", "used"]:
        return True
    return False


def init_db():
    supabase = get_supabase_client()

    existing_admin = (
        supabase.table("users")
        .select("*")
        .eq("username", "admin")
        .limit(1)
        .execute()
        .data
    )

    if not existing_admin:
        supabase.table("users").insert(
            {
                "username": "admin",
                "password_hash": hash_password("admin123"),
                "role": "admin",
                "allergies": "",
                "disliked_ingredients": "",
                "preferred_meal_types": "",
                "preferred_cuisine_types": "",
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
        ).execute()


def register_user(username, password):
    supabase = get_supabase_client()
    username = str(username).strip()

    if not username or not password:
        return False, "Please enter a username and password."

    existing_user = (
        supabase.table("users")
        .select("id")
        .eq("username", username)
        .limit(1)
        .execute()
        .data
    )

    if existing_user:
        return False, "That username already exists. Please choose another one."

    try:
        supabase.table("users").insert(
            {
                "username": username,
                "password_hash": hash_password(password),
                "role": "participant",
                "allergies": "",
                "disliked_ingredients": "",
                "preferred_meal_types": "",
                "preferred_cuisine_types": "",
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
        ).execute()
        return True, "Account created successfully."
    except Exception as exc:
        return False, f"Account could not be created: {exc}"


def login_user(username, password):
    supabase = get_supabase_client()
    username = str(username).strip()

    result = (
        supabase.table("users")
        .select("*")
        .eq("username", username)
        .eq("password_hash", hash_password(password))
        .limit(1)
        .execute()
        .data
    )

    if not result:
        return None

    user = result[0]
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "role": user.get("role", "participant"),
        "allergies": user.get("allergies", ""),
        "disliked_ingredients": user.get("disliked_ingredients", ""),
        "preferred_meal_types": user.get("preferred_meal_types", ""),
        "preferred_cuisine_types": user.get("preferred_cuisine_types", ""),
    }


def update_user_profile(
    user_id,
    allergies,
    disliked_ingredients,
    preferred_meal_types,
    preferred_cuisine_types="",
):
    supabase = get_supabase_client()

    supabase.table("users").update(
        {
            "allergies": allergies or "",
            "disliked_ingredients": disliked_ingredients or "",
            "preferred_meal_types": preferred_meal_types or "",
            "preferred_cuisine_types": preferred_cuisine_types or "",
            "updated_at": now_iso(),
        }
    ).eq("id", user_id).execute()


def get_user_profile(user_id):
    supabase = get_supabase_client()

    result = (
        supabase.table("users")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
        .data
    )

    if not result:
        return {
            "allergies": "",
            "disliked_ingredients": "",
            "preferred_meal_types": "",
            "preferred_cuisine_types": "",
        }

    user = result[0]
    return {
        "allergies": user.get("allergies") or "",
        "disliked_ingredients": user.get("disliked_ingredients") or "",
        "preferred_meal_types": user.get("preferred_meal_types") or "",
        "preferred_cuisine_types": user.get("preferred_cuisine_types") or "",
    }


def add_pantry_item(
    user_id,
    item_name,
    category,
    quantity,
    unit,
    expiration_date,
    container_type="item",
):
    supabase = get_supabase_client()

    supabase.table("pantry_items").insert(
        {
            "user_id": user_id,
            "item_name": str(item_name).strip(),
            "category": category,
            "quantity": float(quantity or 0),
            "unit": unit,
            "container_type": container_type,
            "expiration_date": str(expiration_date),
            "status": "active",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
    ).execute()


def update_pantry_item(
    user_id,
    pantry_item_id,
    item_name,
    category,
    quantity,
    unit,
    expiration_date,
    container_type="item",
):
    supabase = get_supabase_client()

    status = "active"
    try:
        if float(quantity or 0) <= 0:
            status = "used"
    except Exception:
        status = "active"

    supabase.table("pantry_items").update(
        {
            "item_name": str(item_name).strip(),
            "category": category,
            "quantity": float(quantity or 0),
            "unit": unit,
            "container_type": container_type,
            "expiration_date": str(expiration_date),
            "status": status,
            "updated_at": now_iso(),
        }
    ).eq("id", pantry_item_id).eq("user_id", user_id).execute()


def get_user_pantry(user_id):
    supabase = get_supabase_client()

    data = (
        supabase.table("pantry_items")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "active")
        .order("expiration_date")
        .execute()
        .data
    )

    df = to_dataframe(data)

    if df.empty:
        return df

    for column in [
        "id",
        "user_id",
        "item_name",
        "category",
        "quantity",
        "unit",
        "container_type",
        "expiration_date",
        "status",
        "created_at",
        "updated_at",
    ]:
        if column not in df.columns:
            df[column] = ""

    return df



def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _list_to_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        cleaned = []
        for item in value:
            if isinstance(item, dict):
                cleaned.append(
                    str(
                        item.get("ingredient")
                        or item.get("item_name")
                        or item.get("pantry_item")
                        or item.get("name")
                        or item
                    )
                )
            else:
                cleaned.append(str(item))
        return ", ".join([item for item in cleaned if item.strip()])

    return str(value)


def reduce_pantry_item_quantity(
    user_id,
    pantry_item_id,
    quantity_used,
    usage_type="used_in_meal",
    notes="Used in recommended meal",
):
    """Reduce one pantry item and write one ingredient usage log.

    This function is still used by Used Elsewhere/Discarded and older page helpers.
    The Submit Made Meal button should use submit_made_meal() instead because that
    function fetches selected pantry rows once and writes usage logs in a batch.
    """
    supabase = get_supabase_client()

    result = (
        supabase.table("pantry_items")
        .select("*")
        .eq("id", pantry_item_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
        .data
    )

    if not result:
        return False, "Pantry item was not found."

    item = result[0]
    current_quantity = _safe_float(item.get("quantity"), 0)
    quantity_used = _safe_float(quantity_used, 0)

    if quantity_used <= 0:
        return False, f"Amount used for {item.get('item_name', 'this item')} must be greater than zero."

    if quantity_used > current_quantity:
        return False, (
            f"Not enough {item.get('item_name', 'item')} available. "
            f"Available: {current_quantity}, requested: {quantity_used}."
        )

    remaining_quantity = max(current_quantity - quantity_used, 0)
    status = "used" if remaining_quantity <= 0 else "active"

    supabase.table("pantry_items").update(
        {
            "quantity": remaining_quantity,
            "status": status,
            "updated_at": now_iso(),
        }
    ).eq("id", pantry_item_id).eq("user_id", user_id).execute()

    supabase.table("ingredient_usage_logs").insert(
        {
            "user_id": user_id,
            "pantry_item_id": pantry_item_id,
            "item_name": item.get("item_name", ""),
            "usage_type": usage_type or "used_in_meal",
            "quantity_used": quantity_used,
            "unit": item.get("unit", ""),
            "remaining_quantity": remaining_quantity,
            "notes": notes or "",
            "created_at": now_iso(),
        }
    ).execute()

    return True, f"{item.get('item_name', 'Item')} updated. Remaining amount: {remaining_quantity}."


def mark_item_used(user_id, pantry_item_id, usage_type="used_elsewhere", notes=""):
    supabase = get_supabase_client()

    result = (
        supabase.table("pantry_items")
        .select("*")
        .eq("id", pantry_item_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
        .data
    )

    if not result:
        return False

    item = result[0]
    current_quantity = _safe_float(item.get("quantity"), 0)

    supabase.table("pantry_items").update(
        {
            "quantity": 0,
            "status": "used",
            "updated_at": now_iso(),
        }
    ).eq("id", pantry_item_id).eq("user_id", user_id).execute()

    supabase.table("ingredient_usage_logs").insert(
        {
            "user_id": user_id,
            "pantry_item_id": pantry_item_id,
            "item_name": item.get("item_name", ""),
            "usage_type": usage_type,
            "quantity_used": current_quantity,
            "unit": item.get("unit", ""),
            "remaining_quantity": 0,
            "notes": notes,
            "created_at": now_iso(),
        }
    ).execute()

    return True


def save_recommendation_log(
    user_id,
    meal_name,
    meal_type,
    score,
    matched_ingredients,
    expiring_ingredients,
    feedback="",
    used_recommendation=False,
):
    supabase = get_supabase_client()

    matched_ingredients = _list_to_text(matched_ingredients)
    expiring_ingredients = _list_to_text(expiring_ingredients)
    used_recommendation = normalize_bool(used_recommendation)

    result = supabase.table("meal_recommendation_logs").insert(
        {
            "user_id": user_id,
            "meal_name": meal_name,
            "meal_type": meal_type,
            "score": float(score or 0),
            "matched_ingredients": matched_ingredients or "",
            "expiring_ingredients": expiring_ingredients or "",
            "used_recommendation": used_recommendation,
            "feedback": feedback or "",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
    ).execute()

    inserted_id = None
    try:
        if result.data:
            inserted_id = result.data[0].get("id")
    except Exception:
        inserted_id = None

    return True, "Recommendation log saved.", inserted_id


def submit_made_meal(
    user_id,
    meal_name,
    meal_type,
    score,
    matched_ingredients,
    expiring_ingredients,
    selected_usage_rows,
    feedback="",
):
    """Save a made meal and update selected pantry rows with fewer Supabase reads.

    Expected selected_usage_rows format:
    [
        {"pantry_item_id": <id>, "item_name": "bread", "amount_used": 2},
        ...
    ]

    This replaces the slower pattern of selecting, updating, and logging each ingredient
    one at a time from main.py.
    """
    supabase = get_supabase_client()
    selected_usage_rows = selected_usage_rows or []

    if not selected_usage_rows:
        return False, "Please select at least one pantry item to update."

    cleaned_rows = []
    pantry_ids = []

    for row in selected_usage_rows:
        pantry_item_id = row.get("pantry_item_id")
        amount_used = _safe_float(row.get("amount_used"), 0)

        if not pantry_item_id:
            return False, "One selected ingredient is missing its pantry item ID."

        if amount_used <= 0:
            item_name = row.get("item_name") or "one selected ingredient"
            return False, f"The amount used for {item_name} must be greater than zero."

        pantry_ids.append(pantry_item_id)
        cleaned_rows.append(
            {
                "pantry_item_id": pantry_item_id,
                "item_name": row.get("item_name", ""),
                "amount_used": amount_used,
            }
        )

    pantry_ids = list(dict.fromkeys(pantry_ids))

    pantry_data = (
        supabase.table("pantry_items")
        .select("*")
        .eq("user_id", user_id)
        .in_("id", pantry_ids)
        .execute()
        .data
    )

    pantry_by_id = {str(item.get("id")): item for item in pantry_data}
    validation_errors = []

    for usage in cleaned_rows:
        pantry_item_id = str(usage["pantry_item_id"])
        pantry_item = pantry_by_id.get(pantry_item_id)

        if pantry_item is None:
            validation_errors.append(f"{usage.get('item_name') or 'A selected item'} was not found in the pantry.")
            continue

        current_quantity = _safe_float(pantry_item.get("quantity"), 0)
        amount_used = _safe_float(usage.get("amount_used"), 0)

        if amount_used > current_quantity:
            validation_errors.append(
                f"Not enough {pantry_item.get('item_name', usage.get('item_name', 'item'))}. "
                f"Available: {current_quantity}, requested: {amount_used}."
            )

    if validation_errors:
        return False, " ".join(validation_errors)

    matched_text = _list_to_text(matched_ingredients)
    expiring_text = _list_to_text(expiring_ingredients)
    created_at = now_iso()

    log_result = supabase.table("meal_recommendation_logs").insert(
        {
            "user_id": user_id,
            "meal_name": meal_name,
            "meal_type": meal_type,
            "score": float(score or 0),
            "matched_ingredients": matched_text,
            "expiring_ingredients": expiring_text,
            "used_recommendation": True,
            "feedback": feedback or "Made this recommended meal.",
            "created_at": created_at,
            "updated_at": created_at,
        }
    ).execute()

    usage_logs = []

    for usage in cleaned_rows:
        pantry_item_id = str(usage["pantry_item_id"])
        pantry_item = pantry_by_id[pantry_item_id]
        current_quantity = _safe_float(pantry_item.get("quantity"), 0)
        amount_used = _safe_float(usage.get("amount_used"), 0)
        remaining_quantity = max(current_quantity - amount_used, 0)
        status = "used" if remaining_quantity <= 0 else "active"
        updated_at = now_iso()

        supabase.table("pantry_items").update(
            {
                "quantity": remaining_quantity,
                "status": status,
                "updated_at": updated_at,
            }
        ).eq("id", pantry_item_id).eq("user_id", user_id).execute()

        usage_logs.append(
            {
                "user_id": user_id,
                "pantry_item_id": pantry_item_id,
                "item_name": pantry_item.get("item_name", usage.get("item_name", "")),
                "usage_type": "used_in_recommended_meal",
                "quantity_used": amount_used,
                "unit": pantry_item.get("unit", ""),
                "remaining_quantity": remaining_quantity,
                "notes": feedback or f"Used for {meal_name}.",
                "created_at": updated_at,
            }
        )

    if usage_logs:
        supabase.table("ingredient_usage_logs").insert(usage_logs).execute()

    updated_count = len(usage_logs)
    return True, f"Meal saved and {updated_count} pantry item(s) updated."


def get_user_recommendation_logs(user_id):
    supabase = get_supabase_client()

    data = (
        supabase.table("meal_recommendation_logs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    df = to_dataframe(data)

    if df.empty:
        return df

    for column in [
        "id",
        "meal_name",
        "meal_type",
        "score",
        "matched_ingredients",
        "expiring_ingredients",
        "used_recommendation",
        "feedback",
        "created_at",
    ]:
        if column not in df.columns:
            df[column] = ""

    return df


def mark_recommendation_used(user_id, recommendation_id, feedback=""):
    supabase = get_supabase_client()

    supabase.table("meal_recommendation_logs").update(
        {
            "used_recommendation": True,
            "feedback": feedback or "",
            "updated_at": now_iso(),
        }
    ).eq("id", recommendation_id).eq("user_id", user_id).execute()


def save_survey(
    user_id,
    survey_type,
    pantry_awareness=0,
    recommendation_usefulness=0,
    ingredient_utilization=0,
    ease_of_use=0,
    current_method="",
    comments="",
    survey_responses="",
):
    supabase = get_supabase_client()

    if isinstance(survey_responses, str):
        try:
            parsed_responses = json.loads(survey_responses) if survey_responses else {}
        except Exception:
            parsed_responses = {"raw_response": survey_responses}
    elif isinstance(survey_responses, dict):
        parsed_responses = survey_responses
    else:
        parsed_responses = {}

    parsed_responses["summary_scores"] = {
        "pantry_awareness": pantry_awareness,
        "recommendation_usefulness": recommendation_usefulness,
        "ingredient_utilization": ingredient_utilization,
        "ease_of_use": ease_of_use,
        "current_method": current_method,
        "comments": comments,
    }

    supabase.table("surveys").insert(
        {
            "user_id": user_id,
            "survey_type": survey_type,
            "survey_responses": parsed_responses,
            "created_at": now_iso(),
        }
    ).execute()


def has_completed_survey(user_id, survey_type):
    supabase = get_supabase_client()

    result = (
        supabase.table("surveys")
        .select("id")
        .eq("user_id", user_id)
        .eq("survey_type", survey_type)
        .limit(1)
        .execute()
        .data
    )

    return bool(result)


def get_all_users():
    supabase = get_supabase_client()

    data = (
        supabase.table("users")
        .select("id, username, role, created_at")
        .order("created_at", desc=True)
        .execute()
        .data
    )

    return to_dataframe(data)


def get_all_pantry_items():
    supabase = get_supabase_client()

    pantry_data = (
        supabase.table("pantry_items")
        .select("*")
        .order("expiration_date")
        .execute()
        .data
    )

    users_data = (
        supabase.table("users")
        .select("id, username")
        .execute()
        .data
    )

    pantry_df = to_dataframe(pantry_data)
    users_df = to_dataframe(users_data)

    if pantry_df.empty:
        return pantry_df

    if not users_df.empty:
        pantry_df = pantry_df.merge(
            users_df,
            left_on="user_id",
            right_on="id",
            how="left",
            suffixes=("", "_user"),
        )
    else:
        pantry_df["username"] = ""

    wanted_columns = [
        "username",
        "item_name",
        "category",
        "quantity",
        "unit",
        "container_type",
        "expiration_date",
        "status",
        "created_at",
        "updated_at",
    ]

    for column in wanted_columns:
        if column not in pantry_df.columns:
            pantry_df[column] = ""

    return pantry_df[wanted_columns]


def get_all_recommendation_logs():
    supabase = get_supabase_client()

    logs_data = (
        supabase.table("meal_recommendation_logs")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
    )

    users_data = (
        supabase.table("users")
        .select("id, username")
        .execute()
        .data
    )

    logs_df = to_dataframe(logs_data)
    users_df = to_dataframe(users_data)

    if logs_df.empty:
        return logs_df

    if not users_df.empty:
        logs_df = logs_df.merge(
            users_df,
            left_on="user_id",
            right_on="id",
            how="left",
            suffixes=("", "_user"),
        )
    else:
        logs_df["username"] = ""

    wanted_columns = [
        "username",
        "meal_name",
        "meal_type",
        "score",
        "matched_ingredients",
        "expiring_ingredients",
        "used_recommendation",
        "feedback",
        "created_at",
    ]

    for column in wanted_columns:
        if column not in logs_df.columns:
            logs_df[column] = ""

    return logs_df[wanted_columns]


def get_all_ingredient_usage():
    supabase = get_supabase_client()

    usage_data = (
        supabase.table("ingredient_usage_logs")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
    )

    users_data = (
        supabase.table("users")
        .select("id, username")
        .execute()
        .data
    )

    usage_df = to_dataframe(usage_data)
    users_df = to_dataframe(users_data)

    if usage_df.empty:
        return usage_df

    if not users_df.empty:
        usage_df = usage_df.merge(
            users_df,
            left_on="user_id",
            right_on="id",
            how="left",
            suffixes=("", "_user"),
        )
    else:
        usage_df["username"] = ""

    wanted_columns = [
        "username",
        "item_name",
        "usage_type",
        "quantity_used",
        "unit",
        "remaining_quantity",
        "notes",
        "created_at",
    ]

    for column in wanted_columns:
        if column not in usage_df.columns:
            usage_df[column] = ""

    return usage_df[wanted_columns]


def get_all_surveys():
    supabase = get_supabase_client()

    surveys_data = (
        supabase.table("surveys")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
    )

    users_data = (
        supabase.table("users")
        .select("id, username")
        .execute()
        .data
    )

    surveys_df = to_dataframe(surveys_data)
    users_df = to_dataframe(users_data)

    if surveys_df.empty:
        return surveys_df

    if not users_df.empty:
        surveys_df = surveys_df.merge(
            users_df,
            left_on="user_id",
            right_on="id",
            how="left",
            suffixes=("", "_user"),
        )
    else:
        surveys_df["username"] = ""

    if "survey_responses" not in surveys_df.columns:
        surveys_df["survey_responses"] = {}

    surveys_df["pantry_awareness"] = surveys_df["survey_responses"].apply(
        lambda value: value.get("summary_scores", {}).get("pantry_awareness", "") if isinstance(value, dict) else ""
    )
    surveys_df["recommendation_usefulness"] = surveys_df["survey_responses"].apply(
        lambda value: value.get("summary_scores", {}).get("recommendation_usefulness", "") if isinstance(value, dict) else ""
    )
    surveys_df["ingredient_utilization"] = surveys_df["survey_responses"].apply(
        lambda value: value.get("summary_scores", {}).get("ingredient_utilization", "") if isinstance(value, dict) else ""
    )
    surveys_df["ease_of_use"] = surveys_df["survey_responses"].apply(
        lambda value: value.get("summary_scores", {}).get("ease_of_use", "") if isinstance(value, dict) else ""
    )
    surveys_df["current_method"] = surveys_df["survey_responses"].apply(
        lambda value: value.get("summary_scores", {}).get("current_method", "") if isinstance(value, dict) else ""
    )
    surveys_df["comments"] = surveys_df["survey_responses"].apply(
        lambda value: value.get("summary_scores", {}).get("comments", "") if isinstance(value, dict) else ""
    )

    wanted_columns = [
        "username",
        "survey_type",
        "pantry_awareness",
        "recommendation_usefulness",
        "ingredient_utilization",
        "ease_of_use",
        "current_method",
        "comments",
        "survey_responses",
        "created_at",
    ]

    for column in wanted_columns:
        if column not in surveys_df.columns:
            surveys_df[column] = ""

    return surveys_df[wanted_columns]