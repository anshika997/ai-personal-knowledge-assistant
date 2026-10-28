import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.helpers import fetch, flash, show_flash
from utils.styles import page_header

page_header("Goals and Progress", "Set learning goals and track your tasks")
show_flash()

# ---------------- New goal ----------------
with st.expander("Create a new goal"):
    with st.form("new_goal_form", clear_on_submit=True):
        title = st.text_input("Goal title", max_chars=200)
        description = st.text_area("Description (optional)", max_chars=2000)
        use_date = st.checkbox("Set a target date")
        target = st.date_input("Target date")
        created = st.form_submit_button("Create goal", type="primary")
    if created:
        if not title.strip():
            st.warning("Please enter a goal title.")
        else:
            try:
                api_client.create_goal(
                    title.strip(), description.strip(),
                    target.isoformat() if use_date else None,
                )
                flash("Goal created.")
                st.rerun()
            except ApiError as error:
                st.error(str(error))

# ---------------- Goal list ----------------
goals = fetch(api_client.list_goals, default=None)
if goals is None:
    st.stop()
if not goals:
    st.info("No goals yet. Create your first goal above.")

for goal in goals:
    tasks = goal["tasks"]
    done = sum(1 for t in tasks if t["is_completed"])
    icon = "✅" if goal["status"] == "completed" else "🎯"
    label = f"{icon} {goal['title']} ({done}/{len(tasks)} tasks)"

    with st.expander(label, expanded=goal["status"] == "active"):
        if goal["description"]:
            st.write(goal["description"])
        if goal["target_date"]:
            st.caption(f"Target date: {goal['target_date']}")
        st.progress(done / len(tasks) if tasks else 0.0)

        for task in tasks:
            col_a, col_b = st.columns([6, 1])
            checked = col_a.checkbox(
                task["title"], value=task["is_completed"], key=f"task_{task['id']}"
            )
            if checked != task["is_completed"]:
                try:
                    api_client.update_task(task["id"], is_completed=checked)
                    st.rerun()
                except ApiError as error:
                    st.error(str(error))
            if col_b.button("🗑", key=f"deltask_{task['id']}", help="Delete task"):
                try:
                    api_client.delete_task(task["id"])
                    st.rerun()
                except ApiError as error:
                    st.error(str(error))

        with st.form(f"add_task_{goal['id']}", clear_on_submit=True):
            task_title = st.text_input("New task", max_chars=300, key=f"newtask_{goal['id']}")
            add = st.form_submit_button("Add task")
        if add:
            if task_title.strip():
                try:
                    api_client.add_task(goal["id"], task_title.strip())
                    st.rerun()
                except ApiError as error:
                    st.error(str(error))
            else:
                st.warning("Please type a task.")

        b1, b2 = st.columns(2)
        if goal["status"] == "active":
            if b1.button("Mark goal completed", key=f"done_{goal['id']}"):
                try:
                    api_client.update_goal(goal["id"], status="completed")
                    st.rerun()
                except ApiError as error:
                    st.error(str(error))
        else:
            if b1.button("Reopen goal", key=f"reopen_{goal['id']}"):
                try:
                    api_client.update_goal(goal["id"], status="active")
                    st.rerun()
                except ApiError as error:
                    st.error(str(error))

        confirm = b2.checkbox("Confirm delete", key=f"confirm_goal_{goal['id']}")
        if b2.button("Delete goal", disabled=not confirm, key=f"delgoal_{goal['id']}"):
            try:
                api_client.delete_goal(goal["id"])
                flash("Goal deleted.")
                st.rerun()
            except ApiError as error:
                st.error(str(error))

# ---------------- AI recommendations ----------------
st.divider()
st.subheader("AI recommendations")
st.caption(
    "Based on your profile, active goals, and the names of your saved files and notes. "
    "Your document text is not sent."
)
if st.button("Get recommendations"):
    with st.spinner("Thinking..."):
        try:
            st.session_state["recommendations"] = api_client.recommendations()["recommendations"]
        except ApiError as error:
            st.error(str(error))
            st.page_link("views/profile.py", label="Fill in your profile", icon="👤")

if st.session_state.get("recommendations"):
    with st.container(border=True):
        st.markdown(st.session_state["recommendations"])