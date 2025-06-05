
import streamlit as st
# from dotenv import load_dotenv

from functions import inject_custom_css
from services.auth import AuthService
from ui.analysis import AnalysisUI
from ui.auth import AuthUI
from ui.project import ProjectUI


# -- Import your agents --

# Initialize configuration
st.set_page_config(
    page_title="AI Innovation Engine",
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="expanded"
)
# load_dotenv()

# Custom CSS

inject_custom_css()


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
        "file_metadata": {},
        "research_query": "",
        "research_result": "",
        "social_media_search": "",
        "social_media_data": {},
        "page": "login",
        "last_hashtags":""
    }
    for key, value in required_keys.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
    # Ensure ProductGenerationAgent has proper structure
    if "ProductGenerationAgent" not in st.session_state.agent_outputs:
        st.session_state.agent_outputs["ProductGenerationAgent"] = {
            "generations": [],
            "current_generation": None
        }

init_session_state()



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
            if st.session_state.page != "projects":
                if st.session_state.current_project:
                    project = st.session_state.current_project
                    st.markdown(f"#### 📁 {project['name']}")
                    st.caption(project.get('description', 'No description'))
                    
                    # Project progress
                    progress = len(st.session_state.get('completed_steps', [])) / 4
                    st.markdown(f"""
                    <div style="margin: 1rem 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Project Progress</span>
                            <span>{int(progress * 100)}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {progress * 100}%"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Last updated
                    if 'updated_at' in project:
                        st.caption(f"Last updated: {project['updated_at'].strftime('%Y-%m-%d %H:%M')}")
                
                st.markdown("---")
            
            # Project actions
            
                if st.button("📂 Switch Project", use_container_width=True):
                    st.session_state.page = "projects"
                    st.rerun()
                    
                
                if st.button("📥 Export Results", use_container_width=True):
                    st.info("Export feature coming soon!")
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
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
            st.markdown(f"## 🚀 {st.session_state.current_project['name']}")
            analysis_ui.wizard_navigation()
            
            # Wrap each step in a styled container
            with st.container():
                st.markdown("<div class='step-container'>", unsafe_allow_html=True)
                
                if st.session_state.wizard_step == 1:
                    analysis_ui.show_step1_content()
                    
                elif st.session_state.wizard_step == 2:
                    analysis_ui.run_agents()
                    
                elif st.session_state.wizard_step == 3:
                    analysis_ui.show_results()
                    
                elif st.session_state.wizard_step == 4:
                    analysis_ui.show_product_ideas()
                
                st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.button("Reload App", on_click=lambda: st.rerun())