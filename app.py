import os
import json
import time
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
from bson import ObjectId
from pandas import json_normalize

# -- Import your agents --
from agents.ingredients_agent import run as run_ingredients
from agents.technology_agent import run as run_technology
from agents.benefits_agent import run as run_benefits
from agents.situations_agent import run as run_situations
from agents.motivations_agent import run as run_motivations
from agents.outcomes_agent import run as run_outcomes
from agents.product_generation_agent import run as run_product_generation

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
        .project-card {
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            transition: transform 0.2s;
        }
        .project-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .wizard-step {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            background: #f0f5f9;
            border: 1px solid #dee2e6;
        }
        .step-completed {
            background: #e8f5e9;
            border-color: #4caf50;
        }
        .step-current {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        .progress-bar {
            height: 8px;
            border-radius: 4px;
            background: #e0e0e0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: #4caf50;
            transition: width 0.3s ease;
        }
        .project-icon {
            font-size: 1.8rem;
            margin-right: 1rem;
        }
        .project-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            background: #e3f2fd;
            color: #2196f3;
        }
        .digester-box {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: white;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# Database Setup
def get_db():
    try:
        client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
        client.server_info()
        return client["innovation_engine"]
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        st.stop()

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
            "last_login": None,
            "current_project": None
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

    def save_agent_results(self, project_id, results):
        try:
            # Create or update results document
            self.results.update_one(
                {"project_id": ObjectId(project_id)},
                {"$set": {
                    "results": results,
                    "updated_at": datetime.now()
                }},
                upsert=True
            )
            
            # Update project progress
            self.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {
                    "wizard_step": 3,
                    "completed_steps": [1, 2, 3],
                    "updated_at": datetime.now()
                }}
            )
            return True
        except Exception as e:
            st.error(f"Error saving results: {str(e)}")
            return False
        
    def save_product_results(self, project_id, product_ideas):
        """Save product generation results to database"""
        try:
            # Save product ideas to existing results document
            self.results.update_one(
                {"project_id": ObjectId(project_id)},
                {"$set": {"results.ProductGenerationAgent": product_ideas}},
                upsert=True
            )
            
            # Update project progress
            self.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {
                    "wizard_step": 4,
                    "completed_steps": [1, 2, 3, 4],
                    "updated_at": datetime.now()
                }}
            )
            return True
        except Exception as e:
            st.error(f"Error saving product ideas: {str(e)}")
            return False

# Session State Management
def init_session_state():
    required_keys = {
        "authenticated": False,
        "current_user": None,
        "current_project": None,
        "agent_outputs": {},
        "wizard_step": 1,
        "completed_steps": [],
        "rnd_files": [],
        "mkt_files": [],
        "research_query": "",
        "research_result": "",
        "page": "login"
    }
    for key, value in required_keys.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

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
                        if user.get("current_project"):
                            project = self.auth.projects.find_one({"_id": user["current_project"]})
                            if project:
                                st.session_state.current_project = project
                                st.session_state.wizard_step = project.get("wizard_step", 1)
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
        with st.expander("🆕 Create New Project", expanded=False):
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
                            "wizard_step": 1,
                            "completed_steps": [],
                            "analyses": []
                        }
                        self.auth.projects.insert_one(project)
                        st.rerun()
        
        # Display projects
        st.subheader("📦 Your Projects")
        projects = list(self.auth.projects.find({
            "owner": st.session_state.current_user["username"]
        }).sort("created_at", -1))

        if not projects:
            st.info("🎯 No projects found. Create your first project above!")
            return

        for project in projects:
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span class="project-icon">📁</span>
                        <h3>{project['name']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption(f"Created: {project['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                with col2:
                    progress = len(project.get('completed_steps', [])) / 4
                    st.markdown(f"""
                    <div style="margin-bottom: 0.5rem;">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {progress * 100}%"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                            <span class="project-badge">{f"{int(progress * 100)}% Complete"}</span>
                            <span style="color: #666;">Steps completed: {len(project.get('completed_steps', []))}/4</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Open Project", key=f"open_{project['_id']}"):
                        self.load_project(project)
                
                st.markdown("---")

    def load_project(self, project):
        st.session_state.current_project = project
        st.session_state.wizard_step = project.get("wizard_step", 1)
        st.session_state.completed_steps = project.get("completed_steps", [])
        
        self.auth.users.update_one(
            {"_id": st.session_state.current_user["_id"]},
            {"$set": {"current_project": project["_id"]}}
        )
        
        results = self.auth.results.find_one({"project_id": project["_id"]})
        if results:
            st.session_state.agent_outputs = results.get("results", {})
        
        st.session_state.page = "dashboard"
        st.rerun()

class AnalysisUI:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.agents = {
            "IngredientsAgent": run_ingredients,
            "TechnologyAgent": run_technology,
            "BenefitsAgent": run_benefits,
            "SituationsAgent": run_situations,
            "MotivationsAgent": run_motivations,
            "OutcomesAgent": run_outcomes
        }

    def wizard_navigation(self):
        steps = ["What we know", "Digester", "View Results", "Generate Products"]
        cols = st.columns(len(steps))
        for i, step in enumerate(steps):
            with cols[i]:
                is_completed = (i+1) in st.session_state.completed_steps
                is_current = (i+1) == st.session_state.wizard_step
                status = "✓" if is_completed else "➤" if is_current else "•"
                color = "#4CAF50" if is_completed else "#2196F3" if is_current else "#666"
                
                st.markdown(f"""
                <div class="wizard-step {'step-completed' if is_completed else 'step-current' if is_current else ''}">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: {color}; font-size: 1.2rem; margin-right: 0.5rem;">{status}</span>
                        <h4>Step {i+1}</h4>
                    </div>
                    <p>{step}</p>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("---")

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

    def show_step1_content(self):
        """Reorganized Step 1 with new sections"""
        st.subheader("🔍 What We Know")
        
        # Technical Documents Section
        with st.expander("📚 In my possession - Technical Documents", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Private Technical**")
                private_tech = st.file_uploader(
                    "Upload private technical documents",
                    type=["pdf", "docx", "txt"],
                    accept_multiple_files=True,
                    key="private_tech",
                    label_visibility="collapsed"
                )
            with col2:
                st.markdown("**Public Technical**")
                public_tech = st.file_uploader(
                    "Upload public technical documents",
                    type=["pdf", "docx", "txt"],
                    accept_multiple_files=True,
                    key="public_tech",
                    label_visibility="collapsed"
                )
            st.session_state.rnd_files = private_tech + public_tech

        # Marketing Documents Section
        with st.expander("📊 In my possession - Marketing Documents", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Private Marketing**")
                private_mkt = st.file_uploader(
                    "Upload private marketing documents",
                    type=["pdf", "docx", "txt"],
                    accept_multiple_files=True,
                    key="private_mkt",
                    label_visibility="collapsed"
                )
            with col2:
                st.markdown("**Public Marketing**")
                public_mkt = st.file_uploader(
                    "Upload public marketing documents",
                    type=["pdf", "docx", "txt"],
                    accept_multiple_files=True,
                    key="public_mkt",
                    label_visibility="collapsed"
                )
            st.session_state.mkt_files = private_mkt + public_mkt

        # Deep Research Section
        with st.expander("🔬 Do my research for me", expanded=True):
            st.session_state.research_query = st.text_area(
                "What would you like to find out? Write a 3-sentence paragraph:",
                height=150,
                placeholder="e.g., 'Investigate emerging technologies in biodegradable materials for food packaging. Focus on recent scientific breakthroughs and commercial applications. Identify key players and market adoption challenges.'"
            )
            if st.button("🧠 Run Deep Research", use_container_width=True):
                with st.spinner("Researching with Gemini..."):
                    # Placeholder - would integrate with Gemini API in real implementation
                    # time.sleep(2)
                    st.session_state.research_result = f"Research results for: {st.session_state.research_query}"
                    st.success("The Research Agent is currently under development. Our team is actively working on adding this feature and it will be available soon.")

    def run_agents(self):
        st.subheader("⚙️ Analysis Progress")
        
        rnd_text = self.process_files(st.session_state.rnd_files)
        mkt_text = self.process_files(st.session_state.mkt_files)
        
        # Add research content to analysis
        if st.session_state.get('research_result'):
            rnd_text += "\n\nRESEARCH FINDINGS:\n" + st.session_state.research_result
        
        if not rnd_text and not mkt_text:
            st.error("No valid text extracted from files")
            return

        agents = {
            "IngredientsAgent": (run_ingredients, rnd_text),
            "TechnologyAgent": (run_technology, rnd_text),
            "BenefitsAgent": (run_benefits, rnd_text),
            "SituationsAgent": (run_situations, mkt_text),
            "MotivationsAgent": (run_motivations, mkt_text),
            "OutcomesAgent": (run_outcomes, mkt_text)
        }

        progress_bar = st.progress(0)
        results = {}
        
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(fn, text): name for name, (fn, text) in agents.items()}
            for i, future in enumerate(as_completed(futures)):
                name = futures[future]
                try:
                    result = future.result()
                    results[name] = result
                    st.success(f"✅ {name} completed")
                except Exception as e:
                    st.error(f"❌ {name} failed: {str(e)}")
                progress_bar.progress((i + 1) / len(agents))
        
        if results:
            self.auth.save_agent_results(st.session_state.current_project["_id"], results)
            st.session_state.agent_outputs = results
            st.session_state.completed_steps = [1, 2, 3]
            st.session_state.wizard_step = 3
            st.rerun()

    def normalize_agent_data(self, data):
        if isinstance(data, dict):
            for key in list(data.keys()):
                if key in ['Evidence_Snippets', 'Keywords', 'BenefitsAgent', 'TechnologyAgent']:
                    if not isinstance(data[key], list):
                        data[key] = [data[key]] if data[key] else []
                elif isinstance(data[key], dict):
                    data[key] = self.normalize_agent_data(data[key])
                elif isinstance(data[key], list):
                    data[key] = [self.normalize_agent_data(item) if isinstance(item, dict) else item 
                               for item in data[key]]
        return data

    def format_dataframe(self, data):
        try:
            clean_data = self.normalize_agent_data(data)
            if isinstance(clean_data, dict):
                df = json_normalize(clean_data, sep='_', errors='ignore')
            elif isinstance(clean_data, list):
                df = json_normalize(clean_data, sep='_', errors='ignore')
            else:
                df = pd.DataFrame([clean_data])
            
            return df.astype(str).replace({
                'nan': '', 'None': '', 'NaT': '', '[]': '[]', '{}': '{}'
            })
        except Exception as e:
            st.error(f"📊 Formatting error: {str(e)}")
            return pd.DataFrame({"Raw Data": [str(clean_data)]})

    # def show_results(self):
    #     st.markdown("<div class='emoji-header'>📊 Analysis Results</div>", unsafe_allow_html=True)
    #     if not st.session_state.agent_outputs:
    #         st.warning("📭 No results found")
    #         return

    #     # Create tabs for each digester
    #     tabs = st.tabs([f"{name.replace('Agent', ' Digester')}" for name in st.session_state.agent_outputs.keys()])
    #     for tab, (agent_name, agent_data) in zip(tabs, st.session_state.agent_outputs.items()):
    #         with tab:
    #             # Create a container with border
    #             st.markdown(
    #                 f'<div style="border: 1px solid #dee2e6; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">',
    #                 unsafe_allow_html=True
    #             )
                
    #             # Display key insights in a condensed format
    #             if agent_name == "IngredientsAgent":
    #                 if "Key_Ingredients" in agent_data:
    #                     st.markdown("**Key Ingredients:**")
    #                     st.write(agent_data["Key_Ingredients"])
    #                 if "Functionality" in agent_data:
    #                     st.markdown("**Functionality:**")
    #                     st.write(agent_data["Functionality"])
    #                 if "Sources" in agent_data:
    #                     st.markdown("**Sources:**")
    #                     st.write(agent_data["Sources"])
                
    #             elif agent_name == "TechnologyAgent":
    #                 if "Core_Technology" in agent_data:
    #                     st.markdown("**Core Technology:**")
    #                     st.write(agent_data["Core_Technology"])
    #                 if "Innovation_Level" in agent_data:
    #                     st.markdown("**Innovation Level:**")
    #                     st.write(agent_data["Innovation_Level"])
    #                 if "Evidence" in agent_data:
    #                     st.markdown("**Evidence:**")
    #                     st.write(agent_data["Evidence"])
                
    #             elif agent_name == "BenefitsAgent":
    #                 if "Primary_Benefits" in agent_data:
    #                     st.markdown("**Primary Benefits:**")
    #                     st.write(agent_data["Primary_Benefits"])
    #                 if "Benefit_Type" in agent_data:
    #                     st.markdown("**Benefit Type:**")
    #                     st.write(agent_data["Benefit_Type"])
    #                 if "Evidence" in agent_data:
    #                     st.markdown("**Evidence:**")
    #                     st.write(agent_data["Evidence"])
                
    #             elif agent_name == "SituationsAgent":
    #                 if "Key_Situations" in agent_data:
    #                     st.markdown("**Key Situations:**")
    #                     st.write(agent_data["Key_Situations"])
    #                 if "Consumer_Segments" in agent_data:
    #                     st.markdown("**Consumer Segments:**")
    #                     st.write(agent_data["Consumer_Segments"])
    #                 if "Sources" in agent_data:
    #                     st.markdown("**Sources:**")
    #                     st.write(agent_data["Sources"])
                
    #             elif agent_name == "MotivationsAgent":
    #                 if "Primary_Motivations" in agent_data:
    #                     st.markdown("**Primary Motivations:**")
    #                     st.write(agent_data["Primary_Motivations"])
    #                 if "Motivation_Types" in agent_data:
    #                     st.markdown("**Motivation Types:**")
    #                     st.write(agent_data["Motivation_Types"])
    #                 if "Evidence" in agent_data:
    #                     st.markdown("**Evidence:**")
    #                     st.write(agent_data["Evidence"])
                
    #             elif agent_name == "OutcomesAgent":
    #                 if "Desired_Outcomes" in agent_data:
    #                     st.markdown("**Desired Outcomes:**")
    #                     st.write(agent_data["Desired_Outcomes"])
    #                 if "Outcome_Types" in agent_data:
    #                     st.markdown("**Outcome Types:**")
    #                     st.write(agent_data["Outcome_Types"])
    #                 if "Evidence" in agent_data:
    #                     st.markdown("**Evidence:**")
    #                     st.write(agent_data["Evidence"])
                
    #             st.markdown('</div>', unsafe_allow_html=True)
                
    #             # Show raw data in expander
    #             with st.expander("View Detailed Analysis"):
    #                 df = self.format_dataframe(agent_data)
    #                 st.dataframe(df, use_container_width=True)
    #                 with st.expander("📄 Raw JSON Output"):
    #                     st.json(agent_data)
        
    #     # Add navigation buttons
    #     col1, col2, col3 = st.columns([1,1,2])
    #     with col1:
    #         if st.button("← Back to File Upload", key="back_to_step1"):
    #             st.session_state.wizard_step = 1
    #             st.rerun()
    #     with col2:
    #         st.button("Regenerate Analysis", key="regenerate_analysis", 
    #                  help="Re-run the analysis agents")
    #     with col3:
    #         if st.button("Generate Product Ideas →", key="generate_products"):
    #             st.session_state.wizard_step = 4
    #             st.rerun()
    def show_results(self):
        st.markdown("<div class='emoji-header'>📊 Analysis Results</div>", unsafe_allow_html=True)
        if not st.session_state.agent_outputs:
            st.warning("📭 No results found")
            return

        tabs = st.tabs([f"{name} Agent" for name in st.session_state.agent_outputs.keys()])
        for tab, (agent_name, agent_data) in zip(tabs, st.session_state.agent_outputs.items()):
            with tab:
                df = self.format_dataframe(agent_data)
                st.dataframe(df, use_container_width=True)
                with st.expander("📄 Raw JSON Output"):
                    st.json(agent_data)

        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("← Back to Results", key="back_to_results"):
                st.session_state.wizard_step = 3
                st.rerun()
        with col2:
            if st.button("🔄 Generate Products", key="Generate_products"):
                with st.spinner("Generating product ideas..."):
                    if self.generate_products():
                        st.rerun()
    def generate_products(self):
        """Run product generation with guaranteed UI display"""
        st.subheader("🚀 Generating Product Ideas")
        
        # Get all agent outputs
        all_agent_outputs = st.session_state.agent_outputs
        
        if not all_agent_outputs:
            st.error("No analysis results found. Please run analysis first.")
            return False

        # Create progress container
        progress_container = st.container()
        progress_bar = progress_container.progress(0)
        status_text = progress_container.empty()
        
        def progress_callback(percent, message):
            progress_bar.progress(percent)
            status_text.text(message)
        
        try:
            # Run product generation agent
            product_ideas = run_product_generation(all_agent_outputs, progress_callback=progress_callback)
            
            # Store the results
            st.session_state.agent_outputs["ProductGenerationAgent"] = product_ideas
            
            # Save to database
            self.auth.save_product_results(
                st.session_state.current_project["_id"],
                product_ideas
            )
            
            # Update UI state
            st.session_state.completed_steps = [1, 2, 3, 4]
            st.session_state.wizard_step = 4
            
            # Refresh the UI
            st.rerun()
            return True
            
        except Exception as e:
            progress_callback(100, f"Error: {str(e)}")
            time.sleep(2)
            return False
        finally:
            # Clear progress after delay
            time.sleep(1)
            progress_container.empty()    

    def show_product_ideas(self):
        """Display generated product ideas in a structured format"""
        st.subheader("💡 Generated Product Ideas")
        
        # Check if we have product ideas
        if "ProductGenerationAgent" not in st.session_state.agent_outputs:
            st.warning("No product ideas generated yet")
            return

        ideas = st.session_state.agent_outputs["ProductGenerationAgent"]
        
        # If we have a string, try to parse it as JSON
        if isinstance(ideas, str):
            try:
                ideas = json.loads(ideas)
            except json.JSONDecodeError:
                st.error("Could not parse product ideas as JSON")
                st.text_area("Raw Output", ideas, height=400)
                return
        
        # Display each product idea in a structured format
        if isinstance(ideas, list) and ideas:
            for idx, idea in enumerate(ideas, 1):
                with st.expander(f"Idea #{idx}: {idea.get('product_name', 'Unnamed Product')}", expanded=False):
                    # Product header
                    st.markdown(f"### {idea.get('product_name', 'Unnamed Product')}")
                    
                    # Technical Explanation
                    st.markdown("#### Technical Explanation")
                    st.write(idea.get("technical_explanation", "No technical explanation available"))
                    
                    # Consumer Pitch
                    st.markdown("#### Consumer Pitch")
                    st.write(idea.get("consumer_pitch", "No consumer pitch available"))
                    
                    # Competitor Reaction
                    st.markdown("#### Competitor Reaction")
                    st.write(idea.get("competitor_reaction", "No competitor reaction available"))
                    
                    # 5-Year Projection
                    st.markdown("#### 5-Year Projection (2030)")
                    st.write(idea.get("five_year_projection", "No projection available"))
                    
                    # Consumer Discussion
                    st.markdown("#### Consumer Discussion (Town Hall Meeting)")
                    st.write(idea.get("consumer_discussion", "No consumer discussion available"))
                    
                    # Presentation
                    st.markdown("#### Professional Presentation")
                    presentation = idea.get("presentation", [])
                    if isinstance(presentation, list) and len(presentation) > 0:
                        for i, sentence in enumerate(presentation, 1):
                            st.markdown(f"{i}. {sentence}")
                    else:
                        st.write("No presentation available")
                    
                    # Consumer Q&A
                    st.markdown("#### Consumer Q&A")
                    qa = idea.get("consumer_qa", [])
                    if isinstance(qa, list) and len(qa) > 0:
                        for i, qa_item in enumerate(qa, 1):
                            st.markdown(f"**Q{i}:** {qa_item.get('question', '')}")
                            answers = qa_item.get('answers', [])
                            if answers:
                                for j, ans in enumerate(answers, 1):
                                    st.markdown(f"{j}. {ans}")
                            else:
                                st.markdown("No answers available")
                    else:
                        st.write("No Q&A available")
                    
                    # Investor Evaluation
                    st.markdown("#### Investor Evaluation")
                    st.write(idea.get("investor_evaluation", "No investor evaluation available"))
                    
                    # Advertiser Slogans
                    st.markdown("#### Advertiser Slogans")
                    slogans = idea.get("advertisor_slogans", [])
                    if isinstance(slogans, list) and len(slogans) > 0:
                        for slogan in slogans:
                            st.markdown(f"**Slogan:** {slogan.get('slogan', '')}")
                            st.markdown(f"**Mindset Description:** {slogan.get('mindset_description', '')}")
                            st.markdown("---")
                    else:
                        st.write("No slogans available")
                    
                    # AI Report Card
                    st.markdown("#### AI Report Card")
                    report_card = idea.get("ai_report_card", {})
                    if report_card:
                        report_data = {
                            "Metric": ["Originality", "Usefulness", "Social Media Talk", 
                                    "Memorability", "Friend Talk", "Purchase Ease", 
                                    "Excitement", "Boredom Likelihood"],
                            "Score": [
                                report_card.get("originality", 0),
                                report_card.get("usefulness", 0),
                                report_card.get("social_media_talk", 0),
                                report_card.get("memorability", 0),
                                report_card.get("friend_talk", 0),
                                report_card.get("purchase_ease", 0),
                                report_card.get("excitement", 0),
                                report_card.get("boredom_likelihood", 0)
                            ]
                        }
                        st.dataframe(report_data)
                    else:
                        st.write("No AI report card available")
                    
                    st.markdown("---")
            
            # Add JSON viewer at the bottom
            with st.expander("View Raw JSON Output", expanded=False):
                st.json(ideas)
        
        # Add navigation buttons
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("← Back to Results", key="back_to_results"):
                st.session_state.wizard_step = 3
                st.rerun()
        with col2:
            if st.button("🔄 Regenerate Products", key="regenerate_products"):
                with st.spinner("Regenerating product ideas..."):
                    if self.generate_products():
                        st.rerun()
        
    # Main App
def main():
    auth_service = AuthService()
    auth_ui = AuthUI(auth_service)
    project_ui = ProjectUI(auth_service)
    analysis_ui = AnalysisUI(auth_service)

    # Sidebar
    if st.session_state.authenticated:
        with st.sidebar:
            st.markdown(f"## 🧑💻 Welcome, {st.session_state.current_user['username']}")
            st.markdown("---")
            
            if st.session_state.page == "dashboard":
                if st.button("← Back to Projects"):
                    st.session_state.page = "projects"
                    st.rerun()
            
            if st.button("🚪 Logout"):
                auth_service.users.update_one(
                    {"_id": st.session_state.current_user["_id"]},
                    {"$set": {"current_project": None}}
                )
                st.session_state.clear()
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
                analysis_ui.show_step1_content()
                
                # Check if any files or research queries exist
                any_files = (len(st.session_state.get('rnd_files', []))) > 0 or \
                            (len(st.session_state.get('mkt_files', []))) > 0
                any_research = st.session_state.get('research_query') or \
                               st.session_state.get('research_result')
                
                if st.button("Next →", disabled=not (any_files or any_research)):
                    st.session_state.wizard_step = 2
                    st.session_state.completed_steps.append(1)
                    st.rerun()
            
            elif st.session_state.wizard_step == 2:
                analysis_ui.run_agents()
            
            elif st.session_state.wizard_step == 3:
                analysis_ui.show_results()
               
            
            elif st.session_state.wizard_step == 4:
                analysis_ui.show_product_ideas()
                    
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.button("Reload App", on_click=lambda: st.rerun())