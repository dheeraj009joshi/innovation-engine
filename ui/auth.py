
import streamlit as st
from datetime import datetime
import hashlib
import uuid
from db.mongo import get_db
import re

from functions import save_token


class AuthUI:
    def __init__(self, auth_service):
        self.auth = auth_service

    
    def login_form(self):
        with st.container():
            st.markdown(
        "<div style='text-align: center;'>"
        "<h2 style='margin-bottom: 0;'>🧠 Mind Genomics Inventor</h2>"
        "<p style='margin-top: 0; color: gray;'>The fastest way to discover, generate, and test ideas on the planet</p>"
        "</div>",
        unsafe_allow_html=True
    )
            st.title("🔐 Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In")

                if submitted:
                    user = self.auth.verify_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user

                        # Save to localStorage
                        save_token(str(user["_id"]))

                        # Restore project
                        if user.get("current_project"):
                            project = self.auth.projects.find_one({"_id": user["current_project"]})
                            if project:
                                st.session_state.current_project = project
                                st.session_state.wizard_step = project.get("wizard_step", 1)
                                st.session_state.completed_steps = project.get("completed_steps", [])
                                st.session_state.file_metadata = self.auth.get_file_metadata(project["_id"])

                                results = self.auth.results.find_one({"project_id": project["_id"]})
                                if results:
                                    st.session_state.agent_outputs = results.get("results", {})

                        st.session_state.page = "projects"
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

            st.markdown("</div>", unsafe_allow_html=True)
            if st.button("Create New Account"):
                st.session_state.page = "signup"
                st.rerun()


    def signup_form(self):
        with st.container():
            st.markdown(
        "<div style='text-align: center;'>"
        "<h2 style='margin-bottom: 0;'>🧠 Mind Genomics Inventor</h2>"
        "<p style='margin-top: 0; color: gray;'>The fastest way to discover, generate, and test ideas on the planet</p>"
        "</div>",
        unsafe_allow_html=True
    )
            st.title("🚀 Get Started")
            with st.form("signup_form"):
                username = st.text_input("Username (min 4 characters)")
                email = st.text_input("Email")
                password = st.text_input("Password (min 8 characters)", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Create Account")

                if submitted:
                    error = False
                    if len(username) < 4:
                        st.error("Username must be at least 4 characters")
                        error = True
                    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                        st.error("Invalid email format")
                        error = True
                    if len(password) < 8:
                        st.error("Password must be at least 8 characters")
                        error = True
                    if password != confirm_password:
                        st.error("Passwords don't match")
                        error = True
                    
                    if not error:
                        if self.auth.create_user(username, email, password):
                            st.success("Account created! Please login.")
                            st.session_state.page = "login"
                            st.rerun()
                        else:
                            st.error("Username or email already exists")
            
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button("← Back to Login"):
                st.session_state.page = "login"
                st.rerun()
                
