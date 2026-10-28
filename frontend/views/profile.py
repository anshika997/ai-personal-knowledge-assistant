import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.helpers import fetch, flash, fmt_time, show_flash
from utils.styles import page_header


def split_list(text: str) -> list[str]:
    """'AI, Python' -> ['AI', 'Python']"""
    return [item.strip() for item in text.split(",") if item.strip()]


page_header("Personal Profile", "Your interests and goals help personalize AI suggestions")
show_flash()

profile = fetch(api_client.get_profile)
if profile is None:
    st.stop()

with st.form("profile_form"):
    full_name = st.text_input("Full name", value=profile["full_name"], max_chars=120)
    bio = st.text_area("About you", value=profile["bio"], max_chars=2000)
    interests = st.text_input(
        "Interests (separate with commas)", value=", ".join(profile["interests"])
    )
    skills = st.text_input(
        "Skills (separate with commas)", value=", ".join(profile["skills"])
    )
    preferences = st.text_area(
        "Learning preferences", value=profile["learning_preferences"], max_chars=1000
    )
    personal_goals = st.text_area(
        "Personal goals", value=profile["personal_goals"], max_chars=2000
    )
    saved = st.form_submit_button("Save profile", type="primary")

if saved:
    try:
        api_client.update_profile(
            {
                "full_name": full_name,
                "bio": bio,
                "interests": split_list(interests),
                "skills": split_list(skills),
                "learning_preferences": preferences,
                "personal_goals": personal_goals,
            }
        )
        flash("Profile saved.")
        st.rerun()
    except ApiError as error:
        st.error(str(error))

st.caption(f"Last updated: {fmt_time(profile['updated_at'])}")
st.info(
    "Privacy: for recommendations, only your interests, skills, preferences and goals "
    "are sent to the AI provider. Your name and bio are not sent."
)

with st.expander("Danger zone"):
    confirm = st.checkbox("I want to clear all my profile information")
    if st.button("Clear profile", disabled=not confirm):
        try:
            api_client.reset_profile()
            flash("Profile cleared.")
            st.rerun()
        except ApiError as error:
            st.error(str(error))