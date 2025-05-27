import os
import json
import pdfplumber
import docx2txt
import streamlit as st
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient
import hashlib
from datetime import datetime
import pandas as pd
import re


# -- Import your agents --
from agents.ingredients_agent   import run as run_ingredients
from agents.technology_agent    import run as run_technology
from agents.benefits_agent      import run as run_benefits
from agents.situations_agent    import run as run_situations
from agents.motivations_agent   import run as run_motivations
from agents.outcomes_agent      import run as run_outcomes
# Initialize configuration
st.set_page_config(
    page_title="AI Innovation Engine",
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="expanded"
)
load_dotenv()

# Custom CSS
def inject_custom_css():
    st.markdown("""
    <style>
        .main {
            max-width: 1200px;
            padding: 2rem;
        }
        .auth-container {
            max-width: 400px;
            margin: 2rem auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .stButton>button {
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        .project-card {
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
        }
        .wizard-step {
            padding: 1rem;
            border-radius: 8px;
            background: #f8f9fa;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# Database Setup
def get_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["innovation_engine"]
    return db

# Authentication Service
class AuthService:
    def __init__(self):
        self.db = get_db()
        self.users = self.db["users"]
        self.projects = self.db["projects"]
        self.results = self.db["agent_results"]

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, email, password):
        if self.users.find_one({"$or": [{"username": username}, {"email": email}]}):
            return False
        self.users.insert_one({
            "username": username,
            "email": email,
            "password": self.hash_password(password),
            "created_at": datetime.now(),
            "last_login": None
        })
        return True

    def verify_user(self, username, password):
        user = self.users.find_one({"username": username})
        if user and user["password"] == self.hash_password(password):
            self.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now()}}
            )
            return user
        return None

# Session State Management
def init_session_state():
    required_keys = {
        "authenticated": False,
        "current_user": None,
        "current_project": None,
        "agent_outputs": {},
        "wizard_step": 1,
        "rnd_files": [],
        "mkt_files": [],
        "page": "login"
    }
    for key, value in required_keys.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Import agents (mock imports - replace with your actual agents)
# from agents import *

# UI Components
class AuthUI:
    def __init__(self, auth_service):
        self.auth = auth_service

    def login_form(self):
        with st.container():
            st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
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
                        st.session_state.page = "projects"
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            
            st.markdown("</div>", unsafe_allow_html=True)
            cols = st.columns([1,2,1])
            with cols[1]:
                if st.button("Create New Account", key="signup_btn"):
                    st.session_state.page = "signup"
                    st.rerun()

    def signup_form(self):
        with st.container():
            st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
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

class ProjectUI:
    def __init__(self, auth_service):
        self.auth = auth_service

    def projects_dashboard(self):
        st.title("📂 Project Management")
        
        # Create new project
        with st.expander("➕ Create New Project", expanded=False):
            with st.form("new_project_form"):
                name = st.text_input("Project Name")
                description = st.text_area("Description")
                if st.form_submit_button("Create Project"):
                    if name:
                        project = {
                            "name": name,
                            "description": description,
                            "owner": st.session_state.current_user["username"],
                            "created_at": datetime.now(),
                            "files": {"rnd": [], "mkt": []}
                        }
                        self.auth.projects.insert_one(project)
                        st.rerun()
        
        # Display projects
        st.subheader("Your Projects")
        projects = list(self.auth.projects.find({
            "owner": st.session_state.current_user["username"]
        }).sort("created_at", -1))

        if not projects:
            st.info("No projects found. Create your first project above!")
            return

        for project in projects:
            with st.container():
                st.markdown(f"""
                <div class="project-card">
                    <h3>{project['name']}</h3>
                    <p>{project.get('description', '')}</p>
                    <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                        <button onclick="window.openProject('{project['_id']}')">Open</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Open", key=f"open_{project['_id']}"):
                    st.session_state.current_project = project
                    st.session_state.page = "dashboard"
                    st.session_state.wizard_step = 1
                    st.rerun()

class AnalysisUI:
    def __init__(self):
        self.agents = {
            "IngredientsAgent": run_ingredients,
            "TechnologyAgent": run_technology,
            "BenefitsAgent": run_benefits,
            "SituationsAgent": run_situations,
            "MotivationsAgent": run_motivations,
            "OutcomesAgent": run_outcomes
        }

    def wizard_navigation(self):
        steps = ["Upload Files", "Run Analysis", "View Results"]
        cols = st.columns(len(steps))
        for i, step in enumerate(steps):
            with cols[i]:
                st.markdown(f"""
                <div class="wizard-step">
                    <h4>Step {i+1}</h4>
                    <p>{step}</p>
                    {"➤" if st.session_state.wizard_step == i+1 else "✓"}
                </div>
                """, unsafe_allow_html=True)
        st.markdown("---")

    def file_upload_step(self):
        st.subheader("📤 Upload Documents")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.rnd_files = st.file_uploader(
                "R&D Documents",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                key="rnd_upload"
            )
        
        with col2:
            st.session_state.mkt_files = st.file_uploader(
                "Marketing Documents",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                key="mkt_upload"
            )
        
        if st.button("Next →", key="upload_next"):
            if st.session_state.rnd_files or st.session_state.mkt_files:
                st.session_state.wizard_step = 2
                st.rerun()
            else:
                st.error("Please upload at least one file")

    def run_analysis(self):
        st.subheader("⚙️ Analysis Progress")
        
        # Extract text
        rnd_text = self.process_files(st.session_state.rnd_files)
        mkt_text = self.process_files(st.session_state.mkt_files)
        
        if not rnd_text and not mkt_text:
            st.error("No valid text extracted from files")
            return

        # Prepare agents
        agents = {
            "IngredientsAgent": (run_ingredients, rnd_text),
            "TechnologyAgent": (run_technology, rnd_text),
            "BenefitsAgent": (run_benefits, rnd_text),
            "SituationsAgent": (run_situations, mkt_text),
            "MotivationsAgent": (run_motivations, mkt_text),
            "OutcomesAgent": (run_outcomes, mkt_text)
        }

        # Execute agents
        progress_bar = st.progress(0)
        results = {}
        
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(fn, text): name for name, (fn, text) in agents.items()}
            for i, future in enumerate(as_completed(futures)):
                name = futures[future]
                try:
                    results[name] = future.result()
                    st.success(f"✅ {name} completed")
                except Exception as e:
                    st.error(f"❌ {name} failed: {str(e)}")
                progress_bar.progress((i + 1) / len(agents))
        
        st.session_state.agent_outputs = results
        st.session_state.wizard_step = 3
        st.rerun()

    def process_files(self, files):
        text = ""
        for f in files:
            try:
                if f.name.endswith(".pdf"):
                    with pdfplumber.open(f) as pdf:
                        text += "\n".join(p.extract_text() or "" for p in pdf.pages)
                elif f.name.endswith(".docx"):
                    text += docx2txt.process(f)
                else:
                    text += f.read().decode("utf-8")
            except Exception as e:
                st.error(f"Error processing {f.name}: {str(e)}")
        return text

    def show_results(self):
        st.subheader("📊 Analysis Results")
        
        tabs = st.tabs(list(st.session_state.agent_outputs.keys()))
        for tab, (agent, result) in zip(tabs, st.session_state.agent_outputs.items()):
            with tab:
                if isinstance(result, dict):
                    st.dataframe(pd.DataFrame.from_dict(result, orient="index"))
                elif isinstance(result, list):
                    st.dataframe(pd.DataFrame(result))
                else:
                    st.json(result)
        
        if st.button("🔄 Start New Analysis"):
            st.session_state.wizard_step = 1
            st.session_state.agent_outputs = {}
            st.rerun()

# Main App
def main():
    auth_service = AuthService()
    auth_ui = AuthUI(auth_service)
    project_ui = ProjectUI(auth_service)
    analysis_ui = AnalysisUI()

    # Sidebar
    if st.session_state.authenticated:
        with st.sidebar:
            st.image("https://via.placeholder.com/200x50?text=AI+Engine", width=200)
            st.markdown(f"### Welcome, {st.session_state.current_user['username']}")
            
            if st.session_state.page == "dashboard":
                if st.button("← Back to Projects"):
                    st.session_state.page = "projects"
                    st.rerun()
            
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.current_project = None
                st.rerun()

    # Page Routing
    if not st.session_state.authenticated:
        if st.session_state.page == "login":
            auth_ui.login_form()
        elif st.session_state.page == "signup":
            auth_ui.signup_form()
    else:
        if st.session_state.page == "projects":
            project_ui.projects_dashboard()
        elif st.session_state.page == "dashboard":
            analysis_ui.wizard_navigation()
            if st.session_state.wizard_step == 1:
                analysis_ui.file_upload_step()
            elif st.session_state.wizard_step == 2:
                analysis_ui.run_analysis()
            elif st.session_state.wizard_step == 3:
                analysis_ui.show_results()

if __name__ == "__main__":
    main()