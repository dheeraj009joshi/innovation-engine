
import streamlit as st
from datetime import datetime
import hashlib
import uuid
from db.mongo import get_db



class ProjectUI:
    def __init__(self, auth_service):
        self.auth = auth_service

    def projects_dashboard(self):


        if "submitted_project_form" not in st.session_state:
            st.session_state.submitted_project_form = False

        # ✅ Show success toast after rerun
        if st.session_state.submitted_project_form:
            st.success("🎉 Project created successfully!", icon="📁")
            st.session_state.project_name = ""
            st.session_state.project_description = ""
            st.session_state.submitted_project_form = False


        st.title("📂 Project Management")
        
        # Create new project
        with st.expander("🆕 Create New Project", expanded=False):
            with st.form("new_project_form"):
                name = st.text_input("Project Name", key="project_name")
                description = st.text_area("Description", key="project_description")
                if st.form_submit_button("Create Project"):
                    if name:
                        project = {
                            "_id":str(uuid.uuid4()),
                            "name": name,
                            "description": description,
                            "owner": st.session_state.current_user["username"],
                            "created_at": datetime.now(),
                            "wizard_step": 1,
                            "completed_steps": [],
                            "analyses": [],
                            "file_metadata": {}
                        }
                        result = self.auth.projects.insert_one(project)
                        # ✅ Clear input fields
                        st.session_state.submitted_project_form = True
                        st.rerun()
        
        # Display projects
        st.subheader("📦 Your Projects")
        st.markdown("____")
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
                    
                    # Create two columns for buttons
                    btn_col1, btn_col2 = st.columns([1, 1])
                    with btn_col1:
                        if st.button("Open Project", key=f"open_{project['_id']}"):
                            self.load_project(project)
                    with btn_col2:
                        if st.button("🗑️", key=f"delete_{project['_id']}", 
                                    help="Delete this project permanently"):
                            # Show confirmation dialog
                            if st.session_state.get(f"confirm_delete_{project['_id']}"):
                                # Perform deletion
                                self.auth.projects.delete_one({"_id": project["_id"]})
                                # Also delete related results
                                self.auth.results.delete_many({"project_id": project["_id"]})
                                st.success(f"Project '{project['name']}' deleted!")
                                st.rerun()
                            else:
                                # Set confirmation flag
                                st.session_state[f"confirm_delete_{project['_id']}"] = True
                                st.warning(f"Are you sure you want to delete '{project['name']}'? Press delete again to confirm.")
                    
                st.markdown("---")

    def load_project(self, project):
        # clearing study state so that the study data won't come across the different projects 
        # print(st.session_state)
        st.session_state.study_step = 10
        st.session_state.agent_study_step = 10
        st.session_state.pop("study_data")
        st.session_state.pop("agent_study_data")
        st.session_state.pop("theme_outputs")
        st.session_state.current_project = project
        st.session_state.wizard_step = project.get("wizard_step", 1)
        st.session_state.completed_steps = project.get("completed_steps", [])
        st.session_state.file_metadata = project.get("file_metadata", {})
        st.session_state.hashtags_list = []
        st.session_state.social_media_data={}
        
        self.auth.users.update_one(
            {"_id": st.session_state.current_user["_id"]},
            {"$set": {"current_project": project["_id"]}}
        )
        
        results = self.auth.results.find_one({"project_id": project["_id"]})
        if results:
            results_data = results.get("results", {})
            st.session_state.agent_outputs = results_data
            
            # Handle product generation data conversion
            if "ProductGenerationAgent" in results_data:
                pg_data = results_data["ProductGenerationAgent"]
                
                # Convert old array format to new structure
                if isinstance(pg_data, list):
                    # Create new structure with old ideas as first generation
                    new_pg_data = {
                        "generations": [{
                            "_id":  str(uuid.uuid4()),
                            "created_at": datetime.now(),
                            "ideas": pg_data
                        }],
                        "latest": {
                            "_id":  str(uuid.uuid4()),
                            "created_at": datetime.now(),
                            "ideas": pg_data
                        }
                    }
                    
                    # Update session state
                    st.session_state.agent_outputs["ProductGenerationAgent"] = new_pg_data
                    
                    # Update database to new format
                    self.auth.results.update_one(
                        {"_id": results["_id"]},
                        {"$set": {"results.ProductGenerationAgent": new_pg_data}}
                    )


        theme_results = self.auth.theme_results.find_one({"project_id": project["_id"]})
        if theme_results:
            theme_data = theme_results.get("results", {})
            st.session_state.theme_outputs = theme_data    





        st.session_state.page = "dashboard"
        st.rerun()
