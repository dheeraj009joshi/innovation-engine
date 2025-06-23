import streamlit as st
from datetime import datetime
import uuid
# NOTE: get_db kept for existing codebase
from db.mongo import get_db


class ProjectUI:
    def __init__(self, auth_service):
        self.auth = auth_service

    # ------------------------------------------------------------------
    #  Dashboard
    # ------------------------------------------------------------------
    def projects_dashboard(self):
        # ---------- Check for card clicks ---------------------------------
        for key in st.session_state:
            if key.startswith("clicked_project_"):
                project_id = key.replace("clicked_project_", "")
                if st.session_state[key]:
                    # Reset the click state
                    st.session_state[key] = False
                    # Find and load the project
                    doc = self.auth.projects.find_one({"_id": project_id})
                    if doc:
                        self.load_project(doc)
                        st.stop()

        # ---------- toast flag ----------------------------------------
        if st.session_state.get("submitted_project_form"):
            st.success("🎉 Project created successfully!", icon="📁")
            st.session_state.project_name = ""
            st.session_state.project_description = ""
            st.session_state.submitted_project_form = False

        # ---------- global CSS ----------------------------------------
        st.markdown(
            """
<style>
/* grid ----------------------------------------------------------- */
.project-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1.5rem;margin-bottom:2rem;}

/* card ----------------------------------------------------------- */
.project-card{position:relative;background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:1.5rem;
              font-family:'Segoe UI',sans-serif;box-shadow:0 2px 6px rgba(0,0,0,.03);
              transition:box-shadow .25s;cursor:pointer;}
.project-card:hover{box-shadow:0 4px 24px rgba(0,0,0,.12);}
.project-card:hover h4{color:#2563eb;}

/* status pills --------------------------------------------------- */
.status-complete{background:#d1fadf;color:#027a48;font-size:.8rem;font-weight:600;padding:2px 10px;border-radius:8px;margin-left:10px;}
.status-active  {background:#dbeafe;color:#2563eb;font-size:.8rem;font-weight:600;padding:2px 10px;border-radius:8px;margin-left:10px;}

/* description clamp --------------------------------------------- */
.project-desc{margin:.5rem 0 1rem 0;color:#333;font-size:.95rem;line-height:1.4em;
              display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;
              overflow:hidden;text-overflow:ellipsis;max-height:calc(1.4em*4);}

/* progress ------------------------------------------------------- */
.progress-container{border-radius:20px;overflow:hidden;height:10px;margin:6px 0;}
.progress-container.complete{background:#e0fce1;}
.progress-container.active  {background:#e5e7eb;}
.progress-bar-complete{background:#22c55e;height:100%;}
.progress-bar-active  {background:#3b82f6;height:100%;}

/* misc ----------------------------------------------------------- */
.meta{font-size:.85rem;color:#666;margin-top:1rem;}

/* Card titles */
.project-card h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #374151;
}
</style>

<script>
function openProject(projectId) {
    // Find the corresponding button and click it
    const buttons = window.parent.document.querySelectorAll('button[data-testid="baseButton-secondary"]');
    for (let button of buttons) {
        if (button.querySelector && button.querySelector('p') && 
            button.querySelector('p').textContent.includes('Open ' + projectId)) {
            button.click();
            break;
        }
    }
}
</script>
""",
            unsafe_allow_html=True,
        )

        # ---------- title & new-project form --------------------------
        st.title("📂 Project Management")
        with st.expander("🆕 Create New Project", expanded=False):
            with st.form("new_project_form"):
                name = st.text_input("Project Name", key="project_name")
                description = st.text_area("Description", key="project_description")
                if st.form_submit_button("Create Project") and name:
                    self.auth.projects.insert_one(
                        {
                            "_id": str(uuid.uuid4()),
                            "name": name,
                            "description": description,
                            "owner": st.session_state.current_user["username"],
                            "created_at": datetime.now(),
                            "wizard_step": 1,
                            "completed_steps": [],
                            "analyses": [],
                            "file_metadata": {},
                        }
                    )
                    st.session_state.submitted_project_form = True
                    st.rerun()

        # ---------- project grid -------------------------------------
        st.subheader("📦 Your Projects")
        projects = list(
            self.auth.projects.find({"owner": st.session_state.current_user["username"]}).sort("created_at", -1)
        )
        if not projects:
            st.info("🎯 No projects found. Create your first project above!")
            return

        # Build the grid HTML with clickable cards
        grid_html = '<div class="project-grid">'
        for p in projects:
            pct = len(p.get("completed_steps", [])) * 25
            done = pct == 100

            pill_cls = "status-complete" if done else "status-active"
            pill_txt = "completed" if done else "active"

            bar_cls = "progress-bar-complete" if done else "progress-bar-active"
            cont_cls = "progress-container complete" if done else "progress-container active"
            pct_cap = f"✔ {pct}% Complete" if done else f"{pct}% Complete"
            pct_col = "#4caf50" if done else "#555"

            grid_html += f"""
<div class='project-card' onclick='openProject("{p["_id"]}")'>
  <h4>{p['name']} <span class='{pill_cls}'>{pill_txt}</span></h4>
  <div class='project-desc'>{p.get('description','No description')}</div>

  <div class='{cont_cls}'><div class='{bar_cls}' style='width:{pct}%'></div></div>
  <div style='font-size:.8rem;color:{pct_col};margin-top:2px;'>{pct_cap}</div>

  <div class='meta'>📅 {p['created_at'].strftime('%b %d, %Y')}</div>
</div>"""

        grid_html += "</div>"
        st.markdown(grid_html, unsafe_allow_html=True)

        # ---------- Hidden buttons for each project -------------------
        # These buttons will be triggered by the JavaScript
        for p in projects:
            # Initialize click state if not exists
            if f"clicked_project_{p['_id']}" not in st.session_state:
                st.session_state[f"clicked_project_{p['_id']}"] = False
            
            # Hidden button that gets clicked by JavaScript
            if st.button(
                f"Open {p['_id']}", 
                key=f"open_project_{p['_id']}", 
                help="Open project",
                type="secondary"
            ):
                doc = self.auth.projects.find_one({"_id": p["_id"]})
                if doc:
                    self.load_project(doc)

        # ---------- Action buttons section (visible) ------------------
        st.markdown("---")
        st.subheader("Project Actions")
        
        cols = st.columns(len(projects))
        for i, p in enumerate(projects):
            with cols[i]:
                st.write(f"**{p['name']}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_{p['_id']}", help="Edit project"):
                        st.session_state.editing_project = p['_id']
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{p['_id']}", help="Delete project"):
                        # Show confirmation dialog
                        if st.session_state.get(f"confirm_delete_{p['_id']}"):
                            # Perform deletion
                            self.auth.projects.delete_one({"_id": p["_id"]})
                            # Also delete related results
                            self.auth.results.delete_many({"project_id": p["_id"]})
                            st.success(f"Project '{p['name']}' deleted!")
                            st.session_state.pop(f"confirm_delete_{p['_id']}", None)
                            st.rerun()
                        else:
                            # Set confirmation flag
                            st.session_state[f"confirm_delete_{p['_id']}"] = True
                            st.warning(f"Are you sure you want to delete '{p['name']}'? Click delete again to confirm.")
                            st.rerun()

    # ---------- load_project stays unchanged -------------------------
    def load_project(self, project):
        st.session_state.study_step = 10
        st.session_state.pop("study_data", None)
        st.session_state.current_project = project
        st.session_state.wizard_step = project.get("wizard_step", 1)
        st.session_state.completed_steps = project.get("completed_steps", [])
        st.session_state.file_metadata = project.get("file_metadata", {})

        self.auth.users.update_one({"_id": st.session_state.current_user["_id"]},
                                   {"$set": {"current_project": project["_id"]}})

        if (res := self.auth.results.find_one({"project_id": project["_id"]})):
            data = res.get("results", {})
            st.session_state.agent_outputs = data
            if isinstance(data.get("ProductGenerationAgent"), list):
                ideas = data["ProductGenerationAgent"]
                new_pg = {
                    "generations":[{"_id":str(uuid.uuid4()),"created_at":datetime.now(),"ideas":ideas}],
                    "latest":{"_id":str(uuid.uuid4()),"created_at":datetime.now(),"ideas":ideas},
                }
                st.session_state.agent_outputs["ProductGenerationAgent"] = new_pg
                self.auth.results.update_one({"_id":res["_id"]},
                                             {"$set":{"results.ProductGenerationAgent":new_pg}})

        st.session_state.page = "dashboard"
        st.rerun()