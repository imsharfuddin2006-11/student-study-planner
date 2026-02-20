import streamlit as st
import sqlite3
import pandas as pd
import random
import matplotlib.pyplot as plt
from database import create_tables
from utils import hash_password, check_password, bootstrap

create_tables()

st.set_page_config(layout="wide")

# Inject Bootstrap
st.markdown(bootstrap(), unsafe_allow_html=True)

# DB
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

if "user" not in st.session_state:
    st.session_state.user = None

# Sidebar
st.sidebar.title("🎓 Study Planner")

mode = st.sidebar.selectbox("Theme", ["Light", "Dark"])

quotes = [
    "Push yourself, because no one else will.",
    "Stay consistent.",
    "Dream big. Work hard.",
    "Your future is created today."
]
st.sidebar.success(random.choice(quotes))

# AUTH
menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Signup":
    st.subheader("Create Account")
    user = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Signup"):
        hashed = hash_password(password)
        try:
            c.execute("INSERT INTO users(username,password) VALUES (?,?)", (user, hashed))
            conn.commit()
            st.success("Account Created!")
        except:
            st.error("Username exists!")

if choice == "Login":
    st.subheader("Login")
    user = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        c.execute("SELECT password FROM users WHERE username=?", (user,))
        data = c.fetchone()
        if data and check_password(password, data[0]):
            st.session_state.user = user
            st.success("Login Successful!")
        else:
            st.error("Invalid Credentials")

# DASHBOARD
if st.session_state.user:

    st.title("📚 Student Study Planner Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        subject = st.text_input("Subject")
        task = st.text_input("Task")
        deadline = st.date_input("Deadline")

        if st.button("Add Task"):
            c.execute("INSERT INTO tasks(username,subject,task,deadline,status) VALUES (?,?,?,?,?)",
                      (st.session_state.user, subject, task, str(deadline), "Pending"))
            conn.commit()
            st.success("Task Added!")

    # Show tasks
    c.execute("SELECT * FROM tasks WHERE username=?", (st.session_state.user,))
    data = c.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["ID","Username","Subject","Task","Deadline","Status"])
        st.dataframe(df)

        # Progress
        total = len(df)
        completed = len(df[df["Status"]=="Completed"])
        progress = completed / total if total > 0 else 0

        st.progress(progress)
        st.write(f"Completed: {completed}/{total}")

        # Chart
        fig, ax = plt.subplots()
        ax.bar(["Completed","Pending"], [completed, total-completed])
        st.pyplot(fig)

        # Complete
        task_id = st.number_input("Task ID to Complete", min_value=1)
        if st.button("Mark Complete"):
            c.execute("UPDATE tasks SET status='Completed' WHERE id=?", (task_id,))
            conn.commit()
            st.success("Updated!")

        # Delete
        delete_id = st.number_input("Task ID to Delete", min_value=1, key="delete")
        if st.button("Delete Task"):
            c.execute("DELETE FROM tasks WHERE id=?", (delete_id,))
            conn.commit()
            st.success("Deleted!")

        # Reminder Alert
        today = pd.Timestamp.today().date()
        due_tasks = df[df["Deadline"] == str(today)]
        if not due_tasks.empty:
            st.warning("⚠️ You have tasks due today!")
