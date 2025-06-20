from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import json
import queue
import time
import docx2txt
from pandas import json_normalize
import pdfplumber
import streamlit as st
from datetime import datetime
import uuid
from docx import Document
from datetime import datetime
import pandas as pd
import io
import queue
import time
from threading import Thread
import pandas as pd
from agents.ingredients_agent import run as run_ingredients
from agents.technology_agent import run as run_technology
from agents.benefits_agent import run as run_benefits
from agents.situations_agent import run as run_situations
from agents.motivations_agent import run as run_motivations
from agents.outcomes_agent import run as run_outcomes
from agents.product_generation_agent import run as run_product_generation
from functions import upload_to_azure, get_scraper_data


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
        steps = [
            {"title": "What We Know", "icon": "🔍"},
            {"title": "Digester", "icon": "⚙️"},
            {"title": "Results", "icon": "📊"},
            {"title": "Product Ideas", "icon": "💡"}
        ]
        
        st.markdown("<div class='wizard-navigation'>", unsafe_allow_html=True)
        cols = st.columns(len(steps))
        
        for i, step in enumerate(steps):
            with cols[i]:
                step_num = i + 1
                is_completed = step_num in st.session_state.completed_steps
                is_current = step_num == st.session_state.wizard_step
                
                # Status indicator
                status_icon = "✓" if is_completed else "➤" if is_current else "•"
                status_color = "#4CAF50" if is_completed else "#2196F3" if is_current else "#9E9E9E"
                bg_color = "#e8f5e9" if is_completed else "#e3f2fd" if is_current else "#f5f5f5"
                border_color = "#4CAF50" if is_completed else "#2196F3" if is_current else "#e0e0e0"
                
                # Make clickable if completed
                
                
                st.markdown(f"""
                <div class="wizard-step" style="border-color: {border_color}; background: {bg_color};">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: {status_color}; font-size: 1.5rem; margin-right: 0.5rem;">{status_icon}</span>
                        <h4 style="margin-bottom: 0;">Step {step_num}</h4>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.2rem;">{step['icon']}</span>
                        <p style="margin-bottom: 0;">{step['title']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if is_completed:
                    if st.button(
                        f"Go to Step :-{step_num}",
                        key=f"wizard_step_{step_num}",
                        help=f"Go to {step['title']}",
                        use_container_width=True
                    ):
                        st.session_state.wizard_step = step_num
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



    def save_files_to_azure(self, files, file_type):
        """Save files to Azure and return metadata"""
        file_metadata = []
        for file in files:
            file_url = upload_to_azure(file)
            if file_url:
                file_metadata.append({
                    "name": file.name,
                    "type": file_type,
                    "url": file_url,
                    "uploaded_at": datetime.now().isoformat()
                })
        return file_metadata



    def show_step1_content(self):
        st.subheader("🔍 What We Know")
        
        # Initialize session state if not exists
        if 'file_metadata' not in st.session_state:
            project_data = self.auth.get_project(st.session_state.current_project["_id"])
            st.session_state.file_metadata = project_data.get("file_metadata", {
                "technical": [],
                "marketing": []
            })
            st.session_state.social_media_data = project_data.get("social_media_data", None)
            st.session_state.research_result = project_data.get("research_result", "")
            st.session_state.last_hashtags = project_data.get("last_hashtags", [])
            st.session_state.rnd_files = []
            st.session_state.mkt_files = []

        # Function to validate file sizes immediately
        def validate_files(uploaded_files, file_type=""):
            if not uploaded_files:
                return True
            
            MAX_SINGLE_FILE = 7 * 1024 * 1024  # 2MB
            MAX_TOTAL_SIZE = 17 * 1024 * 1024  # 10MB
            
            # Check individual file sizes
            for file in uploaded_files:
                if file.size > MAX_SINGLE_FILE:
                    st.error(f"❌ {file_type} file '{file.name}' exceeds 2MB limit ({file.size/1024/1024:.2f}MB)")
                    return False
            
            # Check total size
            total_size = sum(file.size for file in uploaded_files)
            if total_size > MAX_TOTAL_SIZE:
                st.error(f"❌ Total {file_type} size exceeds 10MB limit ({total_size/1024/1024:.2f}MB)")
                return False
                
            return True

        # Technical Documents Section
        with st.expander("📚 In my possession - Technical Documents", expanded=True):
            # Display existing files
            if st.session_state.file_metadata.get("technical"):
                st.markdown("### Uploaded Technical Documents")
                for file in st.session_state.file_metadata["technical"]:
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.markdown(f"📄 **{file['name']}**")
                        st.caption(f"Uploaded: {datetime.fromisoformat(file['uploaded_at']).strftime('%Y-%m-%d %H:%M')}")
                    with col2:
                        st.markdown(
                            f"""
                            <a href="{file['url']}" download target="_blank">
                                <button style="background-color: #f0f0f0; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">
                                    ⬇️ {file['name']}
                                </button>
                            </a>
                            """,
                            unsafe_allow_html=True
                        )
            
            col1, col2 = st.columns(2)
            with col2:
                st.markdown("**Private Technical**")
                private_tech = st.file_uploader(
                    "Upload confidential R&D documents",
                    type=["pdf", "docx", "txt"],
                    accept_multiple_files=True,
                    key="private_tech",
                    label_visibility="collapsed",
                    on_change=lambda: validate_files(st.session_state.private_tech, "private technical")
                )
            with col1:
                st.markdown("**Public Technical**")
                public_tech = st.file_uploader(
                    "Upload published technical documents",
                    type=["pdf", "docx", "txt"],
                    accept_multiple_files=True,
                    key="public_tech",
                    label_visibility="collapsed",
                    on_change=lambda: validate_files(st.session_state.public_tech, "public technical")
                )
            
            # Validate and store files
            tech_files = []
            if private_tech and validate_files(private_tech, "private technical"):
                tech_files.extend(private_tech)
            if public_tech and validate_files(public_tech, "public technical"):
                tech_files.extend(public_tech)
            st.session_state.rnd_files = tech_files

        # Marketing Documents Section
        with st.expander("📊 In my possession - Marketing Documents", expanded=True):
            # Display existing files
            if st.session_state.file_metadata.get("marketing"):
                st.markdown("### Uploaded Marketing Documents")
                for file in st.session_state.file_metadata["marketing"]:
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.markdown(f"📄 **{file['name']}**")
                        st.caption(f"Uploaded: {datetime.fromisoformat(file['uploaded_at']).strftime('%Y-%m-%d %H:%M')}")
                    with col2:
                        st.markdown(
                            f"""
                            <a href="{file['url']}" download target="_blank">
                                <button style="background-color: #f0f0f0; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">
                                    ⬇️ {file['name']}
                                </button>
                            </a>
                            """,
                            unsafe_allow_html=True
                        )
            
            col1, col2 = st.columns(2)
            with col2:
                st.markdown("**Private Marketing**")
                private_mkt = st.file_uploader(
                    "Upload internal marketing materials",
                    type=["pdf", "docx", "txt"],
                    accept_multiple_files=True,
                    key="private_mkt",
                    label_visibility="collapsed",
                    on_change=lambda: validate_files(st.session_state.private_mkt, "private marketing")
                )
            with col1:
                st.markdown("**Public Marketing**")
                public_mkt = st.file_uploader(
                    "Upload public marketing materials",
                    type=["pdf", "docx", "txt"],
                    accept_multiple_files=True,
                    key="public_mkt",
                    label_visibility="collapsed",
                    on_change=lambda: validate_files(st.session_state.public_mkt, "public marketing")
                )
            
            # Validate and store files
            mkt_files = []
            if private_mkt and validate_files(private_mkt, "private marketing"):
                mkt_files.extend(private_mkt)
            if public_mkt and validate_files(public_mkt, "public marketing"):
                mkt_files.extend(public_mkt)
            st.session_state.mkt_files = mkt_files

        # Social Media Scraper Section
        with st.expander("📱 Social Media Scraper", expanded=True):
            hashtags = st.text_input(
                "Enter a single word to scrape:",
                placeholder="cleanbeauty",
                key="hashtag_input"
            )
            hashtags_list = hashtags.split(" ")
            if len(hashtags_list) > 1:
                st.error(f"Please enter a single hashtag. You entered: {hashtags_list}")

            hashtags = hashtags.replace("#", "")
            if st.button("🌐 Scrape 🎵 TikTok", key="scrape_button"):
                if not hashtags.strip():
                    st.error("Please enter at least one hashtag")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    update_queue = queue.Queue()

                    def run_scraper():
                        return get_scraper_data(hashtags, update_queue)

                    with st.spinner(f"🎵 Scraping posts for {hashtags} from TikTok"):
                        st.info("This may take a few minutes. Please don't close your browser.")
                        
                        # Run scraper in background thread
                        result_holder = {}
                        scraper_thread = Thread(target=lambda: result_holder.update({"data": run_scraper()}))
                        scraper_thread.start()

                        # Main thread: Listen to queue and update UI
                        while scraper_thread.is_alive():
                            try:
                                idx, total = update_queue.get(timeout=0.1)
                                pct = int((idx / total) * 100)
                                progress_bar.progress(pct)
                                status_text.info(f"Extracting comments for posts {idx} of {total}")
                            except queue.Empty:
                                time.sleep(0.1)

                        scraper_thread.join()
                        scraped_data = result_holder["data"]
                        st.session_state.social_media_data = scraped_data
                        st.session_state.last_hashtags = hashtags
                        
                        # Save to MongoDB
                        try:
                            self.auth.update_project(
                                st.session_state.current_project["_id"],
                                {
                                    "social_media_data": scraped_data,
                                    "last_hashtags": st.session_state.last_hashtags
                                }
                            )
                            st.success(f"Scraped {idx} posts successfully!")
                        except Exception as e:
                            st.error(f"Failed to save scraped data: {str(e)}")

            if st.session_state.get('social_media_data') or st.session_state.current_project.get('social_media_data'):
                st.markdown("### Scraped Data Preview")
                st.markdown(f"#### Last Hashtag {st.session_state.current_project.get('last_hashtags') or st.session_state.last_hashtags}")

                try:
                    data = st.session_state.current_project.get('social_media_data').copy() 
                except:
                    data = st.session_state.get('social_media_data').copy()

                # Process data for display
                for item in data:
                    if isinstance(item.get("comments"), list):
                        item["comments"] = " | ".join(
                            c.get("text", "") for c in item["comments"] if isinstance(c, dict))
                
                df = pd.json_normalize(data)
                st.dataframe(df, use_container_width=True)

                # CSV download
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_buffer.getvalue(),
                    file_name="scraped_social_data.csv",
                    mime="text/csv"
                )

        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back to Projects", key="back_to_projects"):
                st.session_state.page = "projects"
                st.rerun()
        
        if 1 not in st.session_state.completed_steps:
            with col2:
                try:
                    st.session_state.social_media_data = st.session_state.current_project["social_media_data"]
                except:
                    pass
                
                if st.button("Start Digester →", key="start_Digester", 
                            disabled=not (st.session_state.rnd_files or st.session_state.mkt_files or 
                                        st.session_state.research_result or st.session_state.social_media_data)):
                    # Save files to Azure and update metadata
                    with st.spinner("Saving files to system..."):
                        tech_metadata = self.save_files_to_azure(st.session_state.rnd_files, "technical")
                        mkt_metadata = self.save_files_to_azure(st.session_state.mkt_files, "marketing")
                        
                        # Update file metadata in session and database
                        st.session_state.file_metadata = {
                            "technical": tech_metadata,
                            "marketing": mkt_metadata
                        }
                        self.auth.save_file_metadata(st.session_state.current_project["_id"], st.session_state.file_metadata)
                    
                    # Move to next step
                    st.session_state.completed_steps.append(1)
                    st.session_state.wizard_step = 2
                    st.rerun()



    def run_agents(self):
        st.subheader("⚙️ Running Digester")
        st.info("This may take a few minutes. Please don't close your browser.")
        
        rnd_text = self.process_files(st.session_state.rnd_files)
        mkt_text = self.process_files(st.session_state.mkt_files)
        
        # Add research content to Digester
        if st.session_state.get('research_result'):
            rnd_text += "\n\nRESEARCH FINDINGS:\n" + str(st.session_state.research_result)
        if st.session_state.get("social_media_data"):
            mkt_text += "\n\nSOCIAL MEDIA CONTENT:\n" + str(st.session_state.social_media_data)
            rnd_text += "\n\nSOCIAL MEDIA CONTENT:\n" + str(st.session_state.social_media_data)
        if not rnd_text and not mkt_text:
            st.error("No valid text extracted from files")
            return
        # # # text combining 
        # text="Rnd text : "+rnd_text+" marketing text : "+mkt_text
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
    #     st.subheader("📊 Digester Results")
        
    #     if not st.session_state.agent_outputs:
    #         st.warning("No Digester results found")
    #         return

    #     # Initialize selected_agent_outputs if it doesn't exist
    #     if "selected_agent_outputs" not in st.session_state:
    #         st.session_state.selected_agent_outputs = {}

    #     # Display each agent's results in expandable sections
    #     for agent_name, agent_data in st.session_state.agent_outputs.items():
    #         if agent_name == "ProductGenerationAgent":
    #             continue

    #         df = self.format_dataframe(agent_data)
            
    #         # Add _selected column if it doesn't exist
    #         if "_selected" not in df.columns:
    #             df["_selected"] = False
                
    #         # Only show expander if DataFrame is not empty
    #         if not df.empty:
    #             with st.expander(f"🔎 {agent_name.replace('Agent', ' Digester')}", expanded=False):
    #                 # Create a unique key for the dataframe
    #                 dataframe_key = f"df_{agent_name}"
                    
    #                 # Display editable dataframe
    #                 edited_df = st.data_editor(
    #                     df,
    #                     use_container_width=True,
    #                     key=dataframe_key,
    #                     num_rows="dynamic",
    #                     disabled=[col for col in df.columns if col != "_selected"]  # Only allow selecting
    #                 )
                    
    #                 # Get the selected rows from session state
    #                 if f"df_{agent_name}" in st.session_state:
    #                     selected_rows = st.session_state[f"df_{agent_name}"]["edited_rows"]
                        
    #                     # Filter the dataframe to only include selected rows
    #                     selected_indices = [i for i, val in selected_rows.items() if val.get("_selected", False)]
    #                     if selected_indices:
    #                         selected_data = edited_df.iloc[selected_indices]
    #                         print(selected_data)
    #                         st.session_state.selected_agent_outputs[agent_name] = selected_data.to_dict('records')
    #                     else:
    #                         # Remove agent from selection if nothing is selected
    #                         if agent_name in st.session_state.selected_agent_outputs:
    #                             del st.session_state.selected_agent_outputs[agent_name]

    #                 # Checkbox to show raw JSON
    #                 show_raw = st.checkbox(f"Show raw JSON for {agent_name}", key=f"raw_{agent_name}")
    #                 if show_raw:
    #                     st.json(agent_data)

    #     # Show generate study button if there are selected outputs (OUTSIDE THE LOOP)
    #     if st.session_state.selected_agent_outputs:
    #         print("inside selected ")
    #         col1, col2 = st.columns(2)
    #         with col1:
    #             if st.button("🚀 Generate Study from Selected Results", type="primary"):
    #                 # Here you would call whatever function generates the study
    #                 st.success("Generating study from selected results...")
    #                 # You can access the selected outputs via st.session_state.selected_agent_outputs
    #                 st.json(st.session_state.selected_agent_outputs)  # Just for demonstration
            
    #         with col2:
    #             if st.button("🔄 Clear Selections"):
    #                 st.session_state.selected_agent_outputs = {}
    #                 st.rerun()

    #     # Navigation buttons
    #     col1, col2 = st.columns([1,1])
    #     with col1:
    #         if st.button("← Back to File Upload", key="back_to_step1"):
    #             st.session_state.wizard_step = 1
    #             st.rerun()

    #     with col2:
    #         # Check if product ideas exist
    #         has_products = "ProductGenerationAgent" in st.session_state.agent_outputs
    #         has_generations = has_products and st.session_state.agent_outputs["ProductGenerationAgent"].get("generations")
            
    #         if has_generations:
    #             if st.button("View Product Ideas →", key="view_products"):
    #                 st.session_state.wizard_step = 4
    #                 st.rerun()
    #         else:
    #             if st.button("Generate Product Ideas →", key="generate_products"):
    #                 with st.spinner("Generating product ideas..."):
    #                     if self.generate_products():
    #                         st.rerun()
    
   

  

    def show_results(self):
        st.subheader("📊 Digester Results")
        
        if not st.session_state.agent_outputs:
            st.warning("No Digester results found")
            return

        # Initialize session state
        if "selected_rows" not in st.session_state:
            st.session_state.selected_rows = {}
        if "select_all_states" not in st.session_state:
            st.session_state.select_all_states = {}

        # Track current selections
        current_selections_exist = False

        for agent_name, agent_data in st.session_state.agent_outputs.items():
            if agent_name == "ProductGenerationAgent":
                continue

            df = self.format_dataframe(agent_data)
            
            if not df.empty:
                # Initialize agent's select all state
                if agent_name not in st.session_state.select_all_states:
                    st.session_state.select_all_states[agent_name] = False
                
                # Add Select column initialized with select all state
                df.insert(0, "Select", st.session_state.select_all_states[agent_name])
                
                with st.expander(f"🔎 {agent_name.replace('Agent', ' Digester')}", expanded=False):
                    # Select all checkbox with synchronization
                    select_all = st.checkbox(
                        "Select all",
                        value=st.session_state.select_all_states[agent_name],
                        key=f"select_all_{agent_name}",
                        on_change=lambda a=agent_name: self._handle_select_all(a)
                    )
                    
                    # Display the dataframe
                    edited_df = st.data_editor(
                        df,
                        key=f"editor_{agent_name}",
                        use_container_width=True,
                        disabled=df.columns[1:],  # Only allow editing Select column
                        hide_index=True
                    )
                    
                    # Update selection states
                    selected_rows = edited_df[edited_df["Select"]]
                    if not selected_rows.empty:
                        st.session_state.selected_rows[agent_name] = selected_rows.to_dict('records')
                        current_selections_exist = True
                        # Update select all state if all rows are selected
                        if len(selected_rows) == len(df):
                            st.session_state.select_all_states[agent_name] = True
                        else:
                            st.session_state.select_all_states[agent_name] = False
                    elif agent_name in st.session_state.selected_rows:
                        del st.session_state.selected_rows[agent_name]
                        st.session_state.select_all_states[agent_name] = False

                    # Show raw JSON option
                    if st.checkbox(f"Show raw JSON for {agent_name}", key=f"raw_{agent_name}"):
                        st.json(agent_data)

        
        st.info("You can select the specific raws from the above tables to proceed with the study from results directly")
        # Navigation buttons
        st.markdown("---")
         # Navigation buttons
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("← Back to File Upload", key="back_to_step1"):
                st.session_state.wizard_step = 1
                st.rerun()

        with col2:
            # Check if product ideas exist
            has_products = "ProductGenerationAgent" in st.session_state.agent_outputs
            has_generations = has_products and st.session_state.agent_outputs["ProductGenerationAgent"].get("generations")
            
            if has_generations:
                if st.button("View Product Ideas →", key="view_products"):
                    st.session_state.wizard_step = 4
                    st.rerun()
            else:
                if st.button("Generate Product Ideas →", key="generate_products"):
                    with st.spinner("Generating product ideas..."):
                        if self.generate_products():
                            st.rerun()
    
        # Clear selections handler
        if "clear_clicked" not in st.session_state:
            st.session_state.clear_clicked = False

        # Show action buttons only if we have current selections
        if current_selections_exist or (st.session_state.selected_rows and not st.session_state.clear_clicked):
            st.markdown("---")
            st.info(f"You have selected rows from the following digesters :- {', '.join([k.replace('Agent', ' Digester') for k in list(st.session_state.selected_rows.keys())])}")
            col1, col2 = st.columns(2)
            with col1:
                
                if st.button("📚 Generate Study", type="primary", key=f"gen-study"):
                    st.info("We are working of this functionality...")
                            # st.session_state["study_step"] = 0
                            # st.session_state["selected_idea_idx"] =  1  # store 0-based index

            with col2:
                if st.button("❌ Clear Selections"):
                    st.session_state.selected_rows = {}
                    st.session_state.select_all_states = {k: False for k in st.session_state.select_all_states}
                    st.session_state.clear_clicked = True
                    st.rerun()
            # Now handle study generation AFTER loop (full-width)
            if st.session_state.get("study_step", 0) >= 0:
                # selected_idx = st.session_state.get("selected_idea_idx", 0)
                selected_idea = st.session_state.selected_rows
                from .study import StudyGenerationProcess
                study_gen = StudyGenerationProcess(self.auth, selected_idea,type="results")
                study_gen.run()
        # Reset clear flag after render
        if st.session_state.clear_clicked:
            st.session_state.clear_clicked = False
    def _handle_select_all(self, agent_name):
        """Handle select all checkbox changes"""
        # Toggle the select all state
        st.session_state.select_all_states[agent_name] = not st.session_state.select_all_states.get(agent_name, False)
        
        # Update the dataframe editor state
        if f"editor_{agent_name}" in st.session_state:
            edited_data = st.session_state[f"editor_{agent_name}"]["edited_rows"]
            for row_idx in edited_data:
                edited_data[row_idx]["Select"] = st.session_state.select_all_states[agent_name]




    def generate_product_docx(self, product_data):
        """Generate a Word document for a product idea"""
        doc = Document()
        
        # Add title
        doc.add_heading(product_data.get('product_name', 'Product Idea'), level=1)
        
        # Add sections
        sections = [
            ('Technical Explanation', product_data.get('technical_explanation')),
            ('Consumer Pitch', product_data.get('consumer_pitch')),
            ('Competitor Reaction', product_data.get('competitor_reaction')),
            ('5-Year Projection', product_data.get('five_year_projection')),
            ('Consumer Discussion', product_data.get('consumer_discussion')),
            ('Professional Presentation', '\n'.join([
                f"{i+1}. {item}" for i, item in enumerate(product_data.get('presentation', []))
            ])),
            ('Investor Evaluation', product_data.get('investor_evaluation'))
        ]
        
        for title, content in sections:
            if content:
                doc.add_heading(title, level=2)
                doc.add_paragraph(content)
        
        # Add Q&A
        qa = product_data.get('consumer_qa', [])
        if qa:
            doc.add_heading('Consumer Q&A', level=2)
            for i, item in enumerate(qa, 1):
                doc.add_paragraph(f"Q{i}: {item.get('question', '')}", style='Heading3')
                for j, answer in enumerate(item.get('answers', []), 1):
                    doc.add_paragraph(f"{j}. {answer}")
        
        # Add slogans
        slogans = product_data.get('advertisor_slogans', [])
        if slogans:
            doc.add_heading('Advertiser Slogans', level=2)
            for slogan in slogans:
                doc.add_paragraph(f"Slogan: {slogan.get('slogan', '')}")
                doc.add_paragraph(f"Mindset: {slogan.get('mindset_description', '')}")
        
        # Create in-memory file
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        
        return file_stream


    def generate_products(self):
        """Run product generation with version history"""
        st.subheader("🚀 Generating Product Ideas")
        
        # Get all agent outputs
        all_agent_outputs = st.session_state.agent_outputs
        
        if not all_agent_outputs:
            st.error("No Digester results found. Please run Digester first.")
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
            
            # Store the results in session
            if "ProductGenerationAgent" not in st.session_state.agent_outputs:
                st.session_state.agent_outputs["ProductGenerationAgent"] = {
                    "generations": [],
                    "current_generation": None
                }
            
            # Create new generation
            new_gen = {
                "_id":  str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "ideas": product_ideas
            }
            
            # Add to history
            st.session_state.agent_outputs["ProductGenerationAgent"]["generations"].append(new_gen)
            st.session_state.agent_outputs["ProductGenerationAgent"]["current_generation"] = new_gen
            
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
        st.subheader("💡 Generated Product Ideas")
        
        # Check if we have product ideas
        if "ProductGenerationAgent" not in st.session_state.agent_outputs:
            st.warning("No product ideas generated yet")
            return

        product_data = st.session_state.agent_outputs["ProductGenerationAgent"]
        
        # Handle old format
        if isinstance(product_data, list):
            generations = [{
                "_id":  str(uuid.uuid4()),
                "created_at": datetime.now().isoformat(),
                "ideas": product_data
            }]
            current_generation = 0
        else:
            generations = product_data.get("generations", [])
            current_generation = product_data.get("current_generation")
        
        if not generations:
            st.warning("No product ideas generated yet")
            return
        
        # Generation selector
        st.markdown("### Product Generation Versions")
        gen_options = []
        for i, gen in enumerate(generations):
            # Handle different timestamp formats
            created_at = gen.get("created_at")
            if isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    time_str = created_at
            elif isinstance(created_at, datetime):
                time_str = created_at.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = "Unknown time"
                
            gen_options.append(f"Generation #{i+1} ")
        
        # Add "Create New" option
        gen_options.append("➕ Create New Generation")
        
        # Default to latest generation
        default_idx = len(generations) - 1
        
        # Create selector
        selected_idx = st.selectbox(
            "Select product generation:",
            options=range(len(gen_options)),
            index=default_idx,
            format_func=lambda i: gen_options[i]
        )
        
        # Handle "Create New" selection
        if selected_idx == len(generations):
            if st.button("🔄 Generate New Product Set", use_container_width=True):
                with st.spinner("Generating new product ideas..."):
                    if self.generate_products():
                        st.rerun()
            return
        
        # Get selected generation data
        selected_gen = generations[selected_idx]
        ideas = selected_gen["ideas"]
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
                cols = st.columns([0.85, 0.15]) 
                with cols[0]:
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
                    with cols[1]:
                        if st.button("📚 Generate Study", type="primary", key=f"gen-study-{idx}"):
                            st.session_state["study_step"] = 0
                            st.session_state["selected_idea_idx"] = idx - 1  # store 0-based index

        # Now handle study generation AFTER loop (full-width)
        if st.session_state.get("study_step", 0) >= 0:
            selected_idx = st.session_state.get("selected_idea_idx", 0)
            selected_idea = ideas[selected_idx]
            from .study import StudyGenerationProcess
            study_gen = StudyGenerationProcess(self.auth, selected_idea)
            study_gen.run()
                

            # Add JSON viewer at the bottom
            # with st.expander("View Raw JSON Output", expanded=False):
            #     st.json(ideas)

            
        # Navigation buttons
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