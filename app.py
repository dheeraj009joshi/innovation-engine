# app.py
import streamlit as st

st.set_page_config(
    page_title="Mind Genomics",
    layout="wide",
    page_icon="\U0001F9E0",
    initial_sidebar_state="expanded"
)

from functions import inject_custom_css
from services.auth import AuthService
from ui.analysis import AnalysisUI
from ui.auth import AuthUI
from ui.project import ProjectUI
from streamlit_cookies_manager import EncryptedCookieManager


inject_custom_css()
def init_session_state():
    required_keys = {
        "authenticated": False,
        "current_user": None,
        "current_project": None,
        "extracted_texts":None,
        "agent_outputs": {},
        "theme_outputs": {},
        "wizard_step": 1,
        "completed_steps": [],
        "rnd_files": [],
        "mkt_files": [],
        "file_metadata": {},
        "research_query": "",
        "research_result": "",
        "social_media_search": "",
        "social_media_data": {},
        "study_data":{
                "study_name": "",
                "study_description": "",
                "questions": [],
                "prelim_questions": [],
                "final_thoughts":"",
                "respondent_orientation":""
            },
        "page": "login",
        "last_hashtags": "",
        "selected_agent_for_study":"",
        "selected_agent_data_for_study":{},
        "agent_study_data":{
                "study_name": "",
                "study_description": "",
                "questions": [],
                "prelim_questions": [],
                "final_thoughts":"",
                "respondent_orientation":""
            },
      
    }
    for key, value in required_keys.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "ProductGenerationAgent" not in st.session_state.agent_outputs:
        st.session_state.agent_outputs["ProductGenerationAgent"] = {
            "generations": [],
            "current_generation": None
        }

init_session_state()

def main():

    cookies = EncryptedCookieManager(password="Dheeraj@2006")
    if not cookies.ready():
        st.stop()
    auth_service = AuthService()
    auth_ui = AuthUI(auth_service,cookies)
    project_ui = ProjectUI(auth_service)
    analysis_ui = AnalysisUI(auth_service)

    params = st.query_params
    page = params.get("page", "login")
    token = params.get("token", None)

    if page == "reset" and token:
        auth_ui.reset_password_form(token)
    elif page == "forgot":
        auth_ui.request_reset_form()

    # Restore token
    else:
        if "restored" not in st.session_state:
            token = cookies.get("auth_token")
            if token:
                st.session_state.auth_token = token
            st.session_state.restored = True


        if not st.session_state.authenticated and "auth_token" in st.session_state:
            token = st.session_state.auth_token
            user = auth_service.users.find_one({"_id": token})
            if user:
                st.session_state.authenticated = True
                st.session_state.current_user = user
                st.session_state.page = "projects"
                st.rerun()
            else:
                st.session_state.auth_token = None

        if not st.session_state.authenticated:
            if st.session_state.page == "login":
                auth_ui.login_form()
            elif st.session_state.page == "signup":
                auth_ui.signup_form()
        else:
            with st.sidebar:
                st.markdown(f"## \U0001F9D1\U0001F4BB Welcome, {st.session_state.current_user['username']}")
                if st.session_state.page != "projects":
                    if st.session_state.current_project:
                        project = st.session_state.current_project
                        st.markdown(f"#### \U0001F4C1 {project['name']}")
                        st.caption(project.get('description', 'No description'))
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

                        if 'updated_at' in project:
                            st.caption(f"Last updated: {project['updated_at'].strftime('%Y-%m-%d %H:%M')}")

                    st.markdown("---")
                    if st.button("\U0001F4C2 Switch Project", use_container_width=True):
                        st.session_state.page = "projects"
                        st.rerun()

                    if st.button("\U0001F4E5 Export Results", use_container_width=True):
                        st.info("Export feature coming soon!")

                st.markdown("---")
        
                if st.button("\U0001F6AA Logout", use_container_width=True):
                    auth_service.users.update_one(
                        {"_id": st.session_state.current_user["_id"]},
                        {"$set": {"current_project": None}}
                    )
                    auth_ui.logout()
                   
                  

            if st.session_state.page == "projects":
                project_ui.projects_dashboard()
            elif st.session_state.page == "dashboard":
                st.markdown(f"## \U0001F680 {st.session_state.current_project['name']}")
                analysis_ui.wizard_navigation()
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