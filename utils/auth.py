# utils/auth.py

import streamlit as st

def login():
    """
    A trivial example of a login helper.  In practice
    you’d hook this up to real user-database logic.
    """
    if "user" not in st.session_state:
        st.session_state.user = None

    username = st.sidebar.text_input("Username")
    pwd      = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Log in"):
        # TODO: replace with real validation
        if username == "admin" and pwd == "secret":
            st.session_state.user = username
            st.sidebar.success(f"Welcome, {username}!")
        else:
            st.sidebar.error("❌ Invalid creds")
