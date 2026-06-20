import json
import pandas as pd
import streamlit as st

from database_supabase import (
    get_all_users,
    get_all_pantry_items,
    get_all_recommendation_logs,
    get_all_ingredient_usage,
    get_all_surveys,
)


OPEN_ENDED_LABELS = {
    "open_notice": "What did App help you notice about your pantry, grocery habits, or meal planning?",
    "open_feature": "Which App feature was the most useful to you, and why?",
    "open_recommendation_help": "Did any meal recommendation help you use an ingredient you may not have used otherwise?",
    "open_compare": "How did App compare to your previous way of tracking groceries, planning meals, or finding recipes?",
    "open_easier": "What would make App easier or more useful for you to keep using?",
}


@st.cache_data(ttl=60, show_spinner=False)
def load_admin_data_cached():
    return {
        "users": get_all_users(),
        "pantry": get_all_pantry_items(),
        "recommendations": get_all_recommendation_logs(),
        "usage": get_all_ingredient_usage(),
        "surveys": get_all_surveys(),
    }


def convert_df_to_csv(df):
    if df is None or df.empty:
        return "".encode("utf-8")
    return df.to_csv(index=False).encode("utf-8")


def parse_json_text(value):
    if value is None:
        return {}

    try:
        if pd.isna(value):
            return {}
    except Exception:
        pass

    text = str(value).strip()

    if not text or text.lower() in ["nan", "none", "null"]:
        return {}

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    return {}


def clean_short_text(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    text = str(value).strip()

    if text.lower() in ["nan", "none", "null"]:
        return ""

    return text


def get_open_ended_answers(row):
    answers = {}

    comments_data = parse_json_text(row.get("comments", ""))
    survey_data = parse_json_text(row.get("survey_responses", ""))

    for key, label in OPEN_ENDED_LABELS.items():
        answer = clean_short_text(comments_data.get(key, ""))

        if not answer:
            answer = clean_short_text(survey_data.get(key, ""))

        if answer:
            answers[label] = answer

    raw_comments = clean_short_text(row.get("comments", ""))

    if not answers and raw_comments and not raw_comments.startswith("{"):
        answers["Comments"] = raw_comments

    return answers


def show_clean_survey_results(surveys_df):
    st.subheader("Survey Results")

    if surveys_df.empty:
        st.info("No survey results have been submitted yet.")
        return

    display_df = surveys_df.copy()

    preferred_columns = [
        "username",
        "survey_type",
        "current_method",
        "pantry_awareness",
        "recommendation_usefulness",
        "ingredient_utilization",
        "ease_of_use",
    ]

    existing_columns = [
        column for column in preferred_columns
        if column in display_df.columns
    ]

    if existing_columns:
        clean_display_df = display_df[existing_columns].copy()
    else:
        clean_display_df = display_df.copy()

    if "comments" in clean_display_df.columns:
        clean_display_df = clean_display_df.drop(columns=["comments"])

    if "survey_responses" in clean_display_df.columns:
        clean_display_df = clean_display_df.drop(columns=["survey_responses"])

    st.dataframe(
        clean_display_df,
        width="stretch",
        hide_index=True,
    )

    st.subheader("Open-Ended Survey Responses")

    open_response_count = 0

    for _, row in surveys_df.iterrows():
        answers = get_open_ended_answers(row)

        if not answers:
            continue

        open_response_count += 1

        username = clean_short_text(row.get("username", "Unknown user"))
        survey_type = clean_short_text(row.get("survey_type", "Survey"))

        with st.expander(f"{username} - {survey_type} written responses"):
            for question, answer in answers.items():
                st.markdown(f"**{question}**")
                st.write(answer)

    if open_response_count == 0:
        st.info("No open-ended survey responses have been submitted yet.")

    score_cols = [
        "pantry_awareness",
        "recommendation_usefulness",
        "ingredient_utilization",
        "ease_of_use",
    ]

    available_score_cols = [
        column for column in score_cols
        if column in surveys_df.columns
    ]

    if available_score_cols and "survey_type" in surveys_df.columns:
        st.subheader("Average Survey Scores by Survey Type")

        numeric_df = surveys_df.copy()

        for column in available_score_cols:
            numeric_df[column] = pd.to_numeric(
                numeric_df[column],
                errors="coerce",
            )

        summary_df = (
            numeric_df
            .groupby("survey_type")[available_score_cols]
            .mean()
            .round(2)
            .reset_index()
        )

        st.dataframe(
            summary_df,
            width="stretch",
            hide_index=True,
        )

    with st.expander("Raw survey data for troubleshooting"):
        st.dataframe(
            surveys_df,
            width="stretch",
            hide_index=True,
        )


def show_study_metrics(users_df, pantry_df, recommendation_df, usage_df, surveys_df):
    st.subheader("Study Metrics")

    total_users = len(users_df) if not users_df.empty else 0
    total_pantry = len(pantry_df) if not pantry_df.empty else 0
    total_recommendations = len(recommendation_df) if not recommendation_df.empty else 0
    total_usage = len(usage_df) if not usage_df.empty else 0
    total_surveys = len(surveys_df) if not surveys_df.empty else 0

    metrics_df = pd.DataFrame(
        [
            {"Metric": "Total users", "Value": total_users},
            {"Metric": "Total pantry items", "Value": total_pantry},
            {"Metric": "Total recommendation logs", "Value": total_recommendations},
            {"Metric": "Total ingredient usage logs", "Value": total_usage},
            {"Metric": "Total survey submissions", "Value": total_surveys},
        ]
    )

    st.dataframe(
        metrics_df,
        width="stretch",
        hide_index=True,
    )

    if not recommendation_df.empty and "used_recommendation" in recommendation_df.columns:
        made_count = len(
            recommendation_df[
                recommendation_df["used_recommendation"].astype(str).str.lower().isin(
                    ["yes", "made", "true", "1"]
                )
            ]
        )

        acceptance_rate = round(
            (made_count / len(recommendation_df)) * 100,
            1,
        ) if len(recommendation_df) else 0

        st.metric("Recommendation Acceptance Rate", f"{acceptance_rate}%")


def show_users(users_df):
    st.subheader("Participants and Users")

    if users_df.empty:
        st.info("No users found.")
        return

    display_df = users_df.copy()

    sensitive_columns = [
        "password",
        "password_hash",
    ]

    display_df = display_df.drop(
        columns=[column for column in sensitive_columns if column in display_df.columns],
        errors="ignore",
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
    )


def show_pantry_data(pantry_df):
    st.subheader("All Pantry Items")

    if pantry_df.empty:
        st.info("No pantry items found.")
        return

    st.dataframe(
        pantry_df,
        width="stretch",
        hide_index=True,
    )


def show_recommendation_logs(recommendation_df):
    st.subheader("Recommendation Logs")

    if recommendation_df.empty:
        st.info("No recommendation logs found.")
        return

    st.dataframe(
        recommendation_df,
        width="stretch",
        hide_index=True,
    )


def show_ingredient_usage(usage_df):
    st.subheader("Ingredient Usage Logs")

    if usage_df.empty:
        st.info("No ingredient usage logs found.")
        return

    st.dataframe(
        usage_df,
        width="stretch",
        hide_index=True,
    )


def show_exports(users_df, pantry_df, recommendation_df, usage_df, surveys_df):
    st.subheader("Export Data")

    st.download_button(
        "Download Users CSV",
        data=convert_df_to_csv(users_df),
        file_name="smart_pantry_users.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download Pantry CSV",
        data=convert_df_to_csv(pantry_df),
        file_name="smart_pantry_pantry_items.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download Recommendations CSV",
        data=convert_df_to_csv(recommendation_df),
        file_name="smart_pantry_recommendations.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download Ingredient Usage CSV",
        data=convert_df_to_csv(usage_df),
        file_name="smart_pantry_ingredient_usage.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download Surveys CSV",
        data=convert_df_to_csv(surveys_df),
        file_name="smart_pantry_surveys.csv",
        mime="text/csv",
    )


def render_admin():
    st.title("Admin Dashboard")

    st.write(
        """
        This dashboard is for the researcher to review participant activity,
        pantry usage, survey results, and recommendation usage.
        """
    )

    admin_data = load_admin_data_cached()

    users_df = admin_data["users"]
    pantry_df = admin_data["pantry"]
    recommendation_df = admin_data["recommendations"]
    usage_df = admin_data["usage"]
    surveys_df = admin_data["surveys"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        participant_count = 0

        if not users_df.empty and "role" in users_df.columns:
            participant_count = len(
                users_df[
                    users_df["role"].astype(str).str.lower() == "participant"
                ]
            )

        st.metric("Participants", participant_count)

    with col2:
        st.metric("Pantry Items", len(pantry_df) if not pantry_df.empty else 0)

    with col3:
        st.metric(
            "Recommendations Saved",
            len(recommendation_df) if not recommendation_df.empty else 0,
        )

    with col4:
        used_count = 0

        if not recommendation_df.empty and "used_recommendation" in recommendation_df.columns:
            used_count = len(
                recommendation_df[
                    recommendation_df["used_recommendation"].astype(str).str.lower().isin(
                        ["yes", "made", "true", "1"]
                    )
                ]
            )

        st.metric("Recommendations Used", used_count)

    st.caption(
        "Admin data is cached for 60 seconds so the app does not reload every table on every click."
    )

    section = st.selectbox(
        "Choose admin section",
        [
            "Survey Results",
            "Study Metrics",
            "Users",
            "Pantry Data",
            "Recommendation Logs",
            "Ingredient Usage",
            "Export Data",
        ],
    )

    if st.button("Refresh Admin Data"):
        load_admin_data_cached.clear()
        st.rerun()

    if section == "Survey Results":
        show_clean_survey_results(surveys_df)

    elif section == "Study Metrics":
        show_study_metrics(
            users_df,
            pantry_df,
            recommendation_df,
            usage_df,
            surveys_df,
        )

    elif section == "Users":
        show_users(users_df)

    elif section == "Pantry Data":
        show_pantry_data(pantry_df)

    elif section == "Recommendation Logs":
        show_recommendation_logs(recommendation_df)

    elif section == "Ingredient Usage":
        show_ingredient_usage(usage_df)

    elif section == "Export Data":
        show_exports(
            users_df,
            pantry_df,
            recommendation_df,
            usage_df,
            surveys_df,
        )


def render_participant_preview():
    st.title("Participant View Preview")
    st.info(
        "Use a participant login to view the full participant experience. "
        "The admin account is only meant for study review and data export."
    )