import streamlit as st
from google.cloud import storage
import requests

st.title("Customer Support - Admin Portal")

# Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        response = requests.post("http://localhost:8000/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.logged_in = True
            st.session_state.role = data["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

if st.session_state.role != "admin":
    st.error("Access denied")
    st.stop()

st.header("Upload Files")

uploaded_file = st.file_uploader("Choose a file", type=["pdf", "xlsx", "eml"])
if uploaded_file is not None:
    # For demo, just show success without GCS
    st.success("File uploaded successfully. Processing will be triggered.")
    # In production, upload to GCS here

# Chat interface (same as user)
st.header("Chat with Support")
# Similar to user_ui, but perhaps admin can view all or something. For now, same.