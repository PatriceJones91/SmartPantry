import streamlit as st
from database_supabase import init_db

st.set_page_config(
    page_title="Smart Pantry",
    page_icon="🥫",
    layout="wide",
)
from utils.ui_helpers import apply_smart_pantry_theme

apply_smart_pantry_theme()

@st.cache_resource(show_spinner=False)
def setup_database():
    init_db()


setup_database()

from smartpantry_core import show_login_page, show_sidebar
from app_pages.home_page import render as render_home
from app_pages.profile_page import render as render_profile
from app_pages.pantry_page import render as render_pantry
from app_pages.recommendation_page import render as render_recommendations
from app_pages.history_page import render as render_history
from app_pages.survey_page import render_pre_study, render_post_study
from app_pages.admin_page import render_admin, render_participant_preview


def main():
    if "user" not in st.session_state:
        show_login_page()
        return

    page = show_sidebar()

    if page == "Home":
        render_home()
    elif page == "Profile":
        render_profile()
    elif page == "Pre-Study Survey":
        render_pre_study()
    elif page == "My Pantry":
        render_pantry()
    elif page == "Meal Recommendations":
        render_recommendations()
    elif page == "Recommendation History":
        render_history()
    elif page == "Post-Study Survey":
        render_post_study()
    elif page == "Admin Dashboard":
        render_admin()
    elif page == "Participant View":
        render_participant_preview()


if __name__ == "__main__":
    main()