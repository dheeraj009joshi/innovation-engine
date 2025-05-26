import os
import json
import pdfplumber
import docx2txt
import streamlit as st
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

# Import each agent’s run function
from agents.ingredients_agent import run as run_ingredients
from agents.technology_agent import run as run_technology
from agents.benefits_agent import run as run_benefits
from agents.situations_agent import run as run_situations
from agents.motivations_agent import run as run_motivations
from agents.outcomes_agent import run as run_outcomes

st.set_page_config(layout="wide")
st.title("🧠 Agentic AI Innovation Engine")

# --- 1) Upload & Extract Text ---
project = "kfjdbds"
rnd_files = st.file_uploader("Upload R&D Files", type=["pdf","docx","txt"], accept_multiple_files=True)
mkt_files = st.file_uploader("Upload Marketing Files", type=["pdf","docx","txt"], accept_multiple_files=True)

if st.button("Extract & Run All Agents"):
    if not project or (not rnd_files and not mkt_files):
        st.error("Please enter a project ID and upload at least one file.")
        st.stop()

    # Extract R&D text
    rnd_text = ""
    for f in rnd_files or []:
        st.write(f"▶ Extracting R&D file {f.name}…")
        if f.name.endswith(".pdf"):
            txt = ""
            with pdfplumber.open(f) as pdf:
                for p in pdf.pages:
                    txt += p.extract_text() or ""
        elif f.name.endswith(".docx"):
            txt = docx2txt.process(f)
        else:
            txt = f.read().decode("utf-8")
        rnd_text += f"\n\n--- {f.name} ---\n\n{txt}"

    # Extract Marketing text
    mkt_text = ""
    for f in mkt_files or []:
        st.write(f"▶ Extracting Marketing file {f.name}…")
        if f.name.endswith(".pdf"):
            txt = ""
            with pdfplumber.open(f) as pdf:
                for p in pdf.pages:
                    txt += p.extract_text() or ""
        elif f.name.endswith(".docx"):
            txt = docx2txt.process(f)
        else:
            txt = f.read().decode("utf-8")
        mkt_text += f"\n\n--- {f.name} ---\n\n{txt}"

    st.success("✅ Text extracted.")

    # Prepare placeholders
    col_r, col_m = st.columns(2)
    with col_r:
        st.subheader("🔬 R&D Agents")
        ph_ing = st.empty()
        ph_tech = st.empty()
        ph_ben = st.empty()
    with col_m:
        st.subheader("📣 Marketing Agents")
        ph_sit = st.empty()
        ph_mot = st.empty()
        ph_out = st.empty()

    # Map R&D agents → (fn, placeholder, input_text)
    rd_agents = {
        "IngredientsAgent": (run_ingredients, ph_ing, rnd_text),
        "TechnologyAgent":  (run_technology,  ph_tech, rnd_text),
        "BenefitsAgent":    (run_benefits,    ph_ben, rnd_text),
    }
    # Map Marketing agents → (fn, placeholder, input_text)
    mk_agents = {
        "SituationsAgent":  (run_situations,   ph_sit, mkt_text),
        "MotivationsAgent": (run_motivations,  ph_mot, mkt_text),
        "OutcomesAgent":    (run_outcomes,     ph_out, mkt_text),
    }

    # Combine maps
    all_agents = {**rd_agents, **mk_agents}

    # Run all in parallel
    with ThreadPoolExecutor() as executor:
        futures = {}
        # submit each
        for name, (fn, ph, txt) in all_agents.items():
            ph.info(f"⏳ {name} running…")
            futures[executor.submit(fn, txt)] = name

        # collect results
        for future in as_completed(futures):
            name = futures[future]
            fn, ph, _ = all_agents[name]
            try:
                output = future.result()
                ph.success(f"✅ {name} done")
                if isinstance(output, list):
                    ph.json(output)
                else:
                    ph.text(str(output))
            except Exception as e:
                ph.error(f"❌ {name} error: {e}")
