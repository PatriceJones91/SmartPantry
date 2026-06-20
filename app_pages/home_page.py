import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from smartpantry_core import (
    clean_category_value,
    format_number,
    get_days_until_expiration,
    get_expiration_alert_info,
    has_completed_survey_cached,
    get_user_pantry_cached,
    normalize_text,
    safe_number,
)


CATEGORY_COLORS = {
    "Protein": "#ef4444",
    "Dairy": "#facc15",
    "Grain": "#a855f7",
    "Fruit": "#ec4899",
    "Vegetable": "#22c55e",
    "Canned Goods": "#10b981",
    "Frozen": "#60a5fa",
    "Snack": "#f97316",
    "Condiment": "#92400e",
    "Tea & Coffee": "#6b7280",
    "Other": "#d1d5db",
}


def show_pantry_category_pie(pantry_df):
    st.subheader("Pantry Category Breakdown")
    st.caption("This shows the mix of pantry items by category.")

    if pantry_df.empty or "category" not in pantry_df.columns:
        st.info("Add pantry items to see your pantry category breakdown.")
        return

    category_counts = (
        pantry_df["category"]
        .fillna("Other")
        .apply(clean_category_value)
        .value_counts()
    )

    if category_counts.empty:
        st.info("Add pantry items to see your pantry category breakdown.")
        return

    chart_data = pd.DataFrame(
        {
            "Category": category_counts.index,
            "Count": category_counts.values,
        }
    )

    chart_data["Percent"] = (
        chart_data["Count"] / chart_data["Count"].sum() * 100
    ).round(0).astype(int)

    chart_data["Label"] = chart_data.apply(
        lambda row: f"{row['Category']}<br>{row['Percent']}%",
        axis=1,
    )

    colors = [
        CATEGORY_COLORS.get(category, CATEGORY_COLORS["Other"])
        for category in chart_data["Category"]
    ]

    chart_col, legend_col = st.columns([2, 1])

    with chart_col:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=chart_data["Category"],
                    values=chart_data["Count"],
                    text=chart_data["Label"],
                    textinfo="text",
                    textposition="inside",
                    marker=dict(colors=colors, line=dict(color="white", width=2)),
                    hovertemplate="<b>%{label}</b><br>Items: %{value}<br>Share: %{percent}<extra></extra>",
                    sort=False,
                    direction="clockwise",
                )
            ]
        )

        fig.update_traces(
            textfont=dict(size=14, color="black"),
            insidetextorientation="horizontal",
        )

        fig.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=430,
            paper_bgcolor="white",
            plot_bgcolor="white",
        )

        chart_key = "pantry_category_pie_" + "_".join(
            [
                f"{row.Category}_{row.Count}"
                for row in chart_data.itertuples()
            ]
        )

        st.plotly_chart(fig, width="stretch", key=chart_key)

    with legend_col:
        st.markdown("**Color Key**")

        for category in chart_data["Category"]:
            color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Other"])

            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:9px;">
                    <div style="
                        width:14px;
                        height:14px;
                        background:{color};
                        border-radius:50%;
                        border:1px solid #666;
                    "></div>
                    <span>{category}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_expiration_alerts(pantry_df):
    st.subheader("Expiration Alerts")

    if pantry_df.empty:
        st.info("No pantry items added yet.")
        return 0

    alert_count = 0

    for _, row in pantry_df.iterrows():
        expiration_date = row.get("expiration_date", "")
        days_left = get_days_until_expiration(expiration_date)
        alert_info = get_expiration_alert_info(days_left)

        if alert_info:
            alert_count += 1

            item_name = str(row.get("item_name", "Pantry item")).title()
            quantity = format_number(row.get("quantity", 0))
            unit = str(row.get("unit", "serving"))
            container_type = str(row.get("container_type", "item"))

            day_word = "day" if days_left == 1 else "days"

            if days_left < 0:
                time_text = f"expired {abs(days_left)} days ago"
            elif days_left == 0:
                time_text = "expires today"
            else:
                time_text = f"expires in {days_left} {day_word}"

            st.markdown(
                f"""
                <div class="{alert_info['class']}">
                    {alert_info['level']}: {item_name} {time_text}<br>
                    Amount left: {quantity} {unit} in {container_type}<br>
                    {alert_info['message']}
                </div>
                """,
                unsafe_allow_html=True,
            )

    if alert_count == 0:
        st.success("No pantry items need attention right now.")

    return alert_count


def get_future_grocery_suggestions(pantry_df):
    if pantry_df.empty:
        return []

    pantry_names = {
        normalize_text(name)
        for name in pantry_df.get("item_name", pd.Series(dtype=str)).tolist()
    }

    pantry_categories = (
        pantry_df.get("category", pd.Series(dtype=str))
        .fillna("Other")
        .apply(clean_category_value)
        .tolist()
    )

    category_counts = pd.Series(pantry_categories).value_counts().to_dict()

    suggestions = []
    seen = set()

    def add_suggestion(item, reason, priority, suggestion_type="Add", allow_existing=False):
        item_text = str(item).strip().title()
        item_key = normalize_text(item_text)
        key = f"{item_key}::{normalize_text(reason)}::{normalize_text(suggestion_type)}"

        if not item_key or key in seen:
            return

        if not allow_existing and item_key in pantry_names:
            return

        seen.add(key)

        suggestions.append(
            {
                "Item": item_text,
                "Why It Is Listed": reason,
                "Type": suggestion_type,
                "Priority": priority,
            }
        )

    for _, row in pantry_df.iterrows():
        item_name = str(row.get("item_name", "")).strip().title()
        if not item_name:
            continue

        days_left = get_days_until_expiration(row.get("expiration_date", ""))
        quantity = safe_number(row.get("quantity", 0), 0)
        unit = str(row.get("unit", "")).strip()

        if days_left < 0:
            add_suggestion(
                item_name,
                "Expired in pantry. Replace only if this is an item the household still uses.",
                "High",
                "Expired / Replace",
                allow_existing=True,
            )

        elif days_left <= 5:
            add_suggestion(
                item_name,
                f"Expires in {days_left} day(s). Use soon, then replace if needed.",
                "High" if days_left <= 2 else "Medium",
                "Use Soon / Possible Replacement",
                allow_existing=True,
            )

        if 0 < quantity <= 2:
            normalized_name = normalize_text(item_name)

            common_meal_helpers = {
                "milk",
                "cheese",
                "eggs",
                "egg",
                "bread",
                "rice",
                "pasta",
                "tortilla",
                "tortillas",
                "chicken",
                "beans",
                "tomato sauce",
                "salsa",
                "broccoli",
                "spinach",
                "lettuce",
            }

            if normalized_name in common_meal_helpers or any(
                helper in normalized_name for helper in common_meal_helpers
            ):
                add_suggestion(
                    item_name,
                    f"Only {format_number(quantity)} {unit} left, and this item can help make several meals.",
                    "Medium",
                    "Low Amount / Restock Soon",
                    allow_existing=True,
                )

    category_boosters = {
        "Protein": ["chicken", "eggs", "beans", "tuna"],
        "Grain": ["rice", "pasta", "bread", "tortillas"],
        "Dairy": ["cheese", "milk", "yogurt"],
        "Vegetable": ["broccoli", "spinach", "carrots", "tomatoes"],
        "Fruit": ["apples", "bananas", "berries"],
    }

    for category, items in category_boosters.items():
        if category_counts.get(category, 0) < 2:
            for item in items:
                add_suggestion(
                    item,
                    f"Adds more {category.lower()} options for future meals.",
                    "Medium",
                    "Meal Helper",
                )
                break

    meal_pairings = [
        ("pasta", "tomato sauce", "Completes easy pasta meals."),
        ("pasta", "ground beef", "Adds protein for pasta meals."),
        ("rice", "beans", "Completes rice and bean meals."),
        ("rice", "chicken", "Completes chicken rice bowls."),
        ("bread", "cheese", "Completes sandwiches or melts."),
        ("bread", "eggs", "Completes breakfast meals."),
        ("tortilla", "cheese", "Completes wraps or quesadillas."),
        ("tortillas", "salsa", "Completes tacos or wraps."),
        ("eggs", "bread", "Completes quick breakfast meals."),
        ("cheese", "tortillas", "Completes quesadillas or wraps."),
    ]

    for have_item, needed_item, reason in meal_pairings:
        if have_item in pantry_names and needed_item not in pantry_names:
            add_suggestion(
                needed_item,
                reason,
                "Low",
                "Meal Helper",
            )

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    suggestions = sorted(
        suggestions,
        key=lambda item: priority_order.get(item.get("Priority", "Low"), 9),
    )

    return suggestions[:10]


def show_future_grocery_list(pantry_df):
    st.subheader("Suggested Grocery List")

    user_id = st.session_state["user"]["id"]
    manual_key = f"manual_grocery_items_{user_id}"

    if manual_key not in st.session_state:
        st.session_state[manual_key] = []

    suggestions = get_future_grocery_suggestions(pantry_df)
    table_rows = []
    seen_items = set()

    priority_rank = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
        "Manual": 3,
    }

    priority_display = {
        "High": "High",
        "Medium": "Medium",
        "Low": "Helpful",
        "Manual": "Added by User",
    }

    for suggestion in suggestions:
        item_name = str(suggestion.get("Item", "")).strip().title()
        item_key = normalize_text(item_name)

        if not item_name or item_key in seen_items:
            continue

        seen_items.add(item_key)

        priority = str(suggestion.get("Priority", "Low")).strip().title()
        suggestion_type = str(suggestion.get("Type", "Suggested")).strip()
        reason = str(
            suggestion.get(
                "Why It Is Listed",
                "Suggested based on pantry activity.",
            )
        ).strip()

        table_rows.append(
            {
                "Priority": priority_display.get(priority, priority),
                "Item": item_name,
                "Reason": reason,
                "Category": suggestion_type,
                "Sort": priority_rank.get(priority, 9),
            }
        )

    for manual_item in st.session_state[manual_key]:
        item_name = str(manual_item).strip().title()
        item_key = normalize_text(item_name)

        if not item_name or item_key in seen_items:
            continue

        seen_items.add(item_key)

        table_rows.append(
            {
                "Priority": "Added by User",
                "Item": item_name,
                "Reason": "Manually added to the grocery list.",
                "Category": "Manual",
                "Sort": priority_rank["Manual"],
            }
        )

    if table_rows:
        grocery_df = pd.DataFrame(table_rows).sort_values(["Sort", "Item"])
        grocery_df = grocery_df[["Priority", "Item", "Reason", "Category"]]

        def style_priority(row):
            priority = str(row.get("Priority", ""))

            if priority == "High":
                color = "background-color: #ffe5e5; color: #7f1d1d; font-weight: 700;"
            elif priority == "Medium":
                color = "background-color: #ffedd5; color: #7c2d12; font-weight: 700;"
            elif priority == "Helpful":
                color = "background-color: #d9f2ff; color: #0f3f66; font-weight: 700;"
            elif priority == "Added by User":
                color = "background-color: #f3e8ff; color: #581c87; font-weight: 700;"
            else:
                color = ""

            return [color for _ in row.index]

        st.dataframe(
            grocery_df.style.apply(style_priority, axis=1),
            width="stretch",
            hide_index=True,
        )

    else:
        st.info("No automatic grocery ideas yet. You can still add your own items below.")

    st.markdown("**Add your own grocery items**")

    with st.form(f"manual_grocery_form_{user_id}"):
        manual_entry = st.text_input(
            "Type ingredient or item",
            placeholder="Example: eggs, rice, yogurt",
            key=f"manual_grocery_entry_{user_id}",
        )

        add_manual = st.form_submit_button("Add to Grocery List")

    if add_manual:
        new_items = [
            item.strip().title()
            for item in re.split(r",|;|\n", manual_entry)
            if item.strip()
        ]

        existing_keys = {
            normalize_text(item)
            for item in st.session_state[manual_key]
        }

        for item in new_items:
            item_key = normalize_text(item)

            if item_key and item_key not in existing_keys:
                st.session_state[manual_key].append(item)
                existing_keys.add(item_key)

        if new_items:
            st.success("Item added to your grocery list.")
            st.rerun()
        else:
            st.warning("Please type at least one item before adding.")

    if st.session_state[manual_key]:
        col_clear, col_spacer = st.columns([1, 3])

        with col_clear:
            if st.button("Clear Added Items", key=f"clear_manual_grocery_{user_id}"):
                st.session_state[manual_key] = []
                st.rerun()


def render():
    st.markdown(
        """
        <div class="friendly-note">
            Let’s see what’s in your pantry today.
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state["user"]["id"]

    pre_done = has_completed_survey_cached(user_id, "Pre-Study")
    post_done = has_completed_survey_cached(user_id, "Post-Study")
    pantry_df = get_user_pantry_cached(user_id)

    total_usable_quantity = 0

    if not pantry_df.empty and "quantity" in pantry_df.columns:
        total_usable_quantity = pantry_df["quantity"].astype(float).sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Pre-Study Survey", "Completed" if pre_done else "Not Completed")

    with col2:
        st.metric("Available Pantry Items", len(pantry_df))

    with col3:
        st.metric("Total Usable Amounts", format_number(total_usable_quantity))

    with col4:
        st.metric("Post-Study Survey", "Completed" if post_done else "Not Completed")

    st.write("")

    top_left, top_right = st.columns([1.2, 1])

    with top_left:
        show_pantry_category_pie(pantry_df)

    with top_right:
        render_expiration_alerts(pantry_df)

    st.write("")

    show_future_grocery_list(pantry_df)