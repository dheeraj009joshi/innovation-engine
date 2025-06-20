
import time
from functions import send_reset_email
import streamlit as st
import re
from streamlit_cookies_manager import EncryptedCookieManager




class AuthUI:
    def __init__(self, auth_service,cookies):
        self.auth = auth_service
        self.cookies=cookies

    
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
                col1, col2 = st.columns([4, 1])
                password = st.text_input("Password", type="password")

                st.markdown('<a href="?page=forgot">Forgot Password?</a>', unsafe_allow_html=True)


                submitted = st.form_submit_button("Sign In")

                if submitted:
                    user = self.auth.verify_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user


                        # After user successfully logs in:
                        st.session_state.auth_token = str(user["_id"])
                        self.cookies["auth_token"] = st.session_state.auth_token


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
                
   
    def request_reset_form(self):
        st.title("🔑 Forgot Password")
        with st.form("reset_request"):
            email = st.text_input("Enter your registered email")
            submitted = st.form_submit_button("Send Reset Link")

            if submitted:
                token = self.auth.create_reset_token(email)
                if token:
                    reset_link = f"https://mindgenome.org/?page=reset&token={token}"
                    send_reset_email(email, reset_link)
                    st.success("Password reset link sent.")
                else:
                    st.error("Email not found.")

    def reset_password_form(self, token):
        st.title("🔐 Set New Password")
        with st.form("reset_form"):
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Reset Password")

            if submitted:
                if new_pw != confirm_pw:
                    st.error("Passwords do not match")
                elif len(new_pw) < 8:
                    st.error("Password must be at least 8 characters")
                else:
                    if self.auth.reset_password(token, new_pw):
                        st.success("Password reset successful. Please login.")
                    else:
                        st.error("Invalid or expired token")
        if st.button("🔐 Go to Login"):
                            # Clear token from URL and state
                            st.session_state.page = "login"
                            st.query_params.clear()  # Clears URL params
                            st.rerun()
