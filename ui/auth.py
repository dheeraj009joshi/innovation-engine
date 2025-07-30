
import datetime
import time
from functions import send_reset_email
import streamlit as st
import re
from streamlit_cookies_manager import EncryptedCookieManager
from automation.account_creation import main as create_account
import asyncio
from config import countries


class AuthUI:
    def __init__(self, auth_service,cookies):
        self.auth = auth_service
        self.cookies=cookies

    def logout(self):
        # Clear session state
        if "authenticated" in st.session_state:
            del st.session_state.authenticated
        if "current_user" in st.session_state:
            del st.session_state.current_user
        if "auth_token" in st.session_state:
            del st.session_state.auth_token

        # Clear cookies
        if "auth_token" in self.cookies:
            del self.cookies["auth_token"]

        # Optionally rerun or redirect
        st.success("You have been logged out.")
        st.session_state.page = "login"
        st.rerun()



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
                identifier = st.text_input("Username or Email")
                col1, col2 = st.columns([4, 1])
                password = st.text_input("Password", type="password")

                st.markdown('<a href="?page=forgot">Forgot Password?</a>', unsafe_allow_html=True)

                submitted = st.form_submit_button("Sign In")

                if submitted:
                    user = self.auth.users.find_one({
                        "$or": [
                            {"username": identifier},
                            {"email": identifier}
                        ]
                    })

                    if not user:
                        st.error("❌ User not found. Please check your username or email.")
                    elif user["password"] != self.auth.hash_password(password):
                        st.error("❌ Incorrect password. Please try again.")
                    else:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.session_state.auth_token = str(user["_id"])
                        self.cookies["auth_token"] = st.session_state.auth_token

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
                name = st.text_input("Full Name")
                username = st.text_input("Username (min 4 characters)")
                email = st.text_input("Email")
                country = st.selectbox("Country", options=countries, index=countries.index("United States"))
                gender = st.selectbox("Gender", options=["male", "female", "other"])
                dob = st.date_input("Date of Birth",min_value=datetime.date(1800, 1, 1),max_value=datetime.date.today())
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
                    if len(name) < 3:
                        st.error("Name must be at least 3 characters")
                        error = True
                    if password != confirm_password:
                        st.error("Passwords don't match")
                        error = True
                    if not name.strip():
                        st.error("Name is required")
                        error = True
                    if not dob:
                        st.error("Date of Birth is required")
                        error = True

    
                    if not error:
                        result = self.auth.create_user(username, email, password, name, country, gender, dob)
                        if isinstance(result, tuple) and result[0]:  # success
                            hashed_password = result[1]
                            with st.spinner("Creating account..."):
                                st.info("This may take a few seconds, please wait...")
                                # Run account creation automation
                                asyncio.run(create_account({
                                    "name": name,
                                    "email": email,
                                    "password": hashed_password,  # Pass the hashed password here
                                    "country": country,
                                    "gender": gender
                                }))
                                st.info("Account initialization complete! Please check your email to verify your account.")
                                time.sleep(10)

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
