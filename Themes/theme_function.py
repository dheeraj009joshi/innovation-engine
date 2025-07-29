from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
from Themes.motivation_themes import run as motivation_theme_run
from Themes.outcome_themes import run as outcome_theme_run
from Themes.situation_themes import run as situation_theme_run
from Themes.technology_themes import run as technology_theme_run
from Themes.benefit_themes import run as benefit_theme_run   
import streamlit as st
import pandas as pd



def run_themes():
    project_description=st.session_state.current_project["description"]

    agents_output = st.session_state.agent_outputs["results"]

    # Dictionary to hold all generated texts
    agents_text = {}

    # Loop through each agent dynamically
    for agent_name, entries in agents_output.items():
        df = pd.DataFrame(entries)
        
        text = ""
        for _, row in df.iterrows():
            entry = "\n".join([
                f"{key}: {row.get(key, '')}" for key in df.columns
            ]) + "\n\n"
            text += entry

        agents_text[agent_name] = text





    # Define agents
    agents = {
        # "IngredientsAgent": (run_ingredients, rnd_text, project_description),
        "TechnologyAgent": (technology_run, agents_text["TechnologyAgent"], project_description),
        "BenefitsAgent": (benefit_run, agents_text["BenefitsAgent"], project_description),
        "SituationsAgent": (situation_run, agents_text["SituationsAgent"], project_description),
        "MotivationsAgent": (motivation_run, agents_text["MotivationsAgent"], project_description),
        "OutcomesAgent": (outcome_run, agents_text["OutcomesAgent"], project_description),
    }
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = {}
    agent_count = len(agents)

    # Create a container for agent status messages
    status_container = st.container()

    # Initialize status messages
    status_messages = {
        agent: status_container.empty() for agent in agents
    }

    # Set initial status
    for agent in agents:
        status_messages[agent].info(f"🟡 Starting...  {agent.replace('Agent', '')} ")

    # Run agents with ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(fn, text,description): agent for agent, (fn, text,description) in agents.items()}
        
        for i, future in enumerate(as_completed(futures)):
            agent = futures[future]
            
            try:
                result = future.result()
                results[agent] = result
                # Update status to success
                status_messages[agent].success(f"✅ {agent.replace('Agent', '')} completed successfully")
                
                # Show quick notification
                st.toast(f"✨ {agent.replace('Agent', ' Themes')} finished!", icon="✅")
            except Exception as e:
                status_messages[agent].error(f"❌ {agent.replace('Agent', '')} failed: {str(e)}")
                st.toast(f"⚠️ {agent.replace('Agent', '')} failed", icon="❌")
            
            # Update progress bar
            progress = int((i + 1) / agent_count * 100)
            progress_bar.progress(progress)
            status_text.info(f"⏳ Progress: {progress}% complete | {i+1}/{agent_count} agents finished")

    # Final completion
    progress_bar.progress(100)


    # Celebration effect
    # st.balloons()
    st.success("Digester analysis complete! Ready to review results.")

    # Save results and move to next step
    if results:
        timestamp2 = datetime.now().isoformat()
        # logging.info(f"{timestamp2}, Digester results saved with {len(str(results))} agents")
        self.auth.save_agent_results(st.session_state.current_project["_id"], results)
        st.session_state.agent_outputs = results
        st.session_state.completed_steps = [1, 2, 3]
        st.session_state.wizard_step = 3
        
        # Auto-rerun after short delay to show results
        time.sleep(2)
        st.rerun()