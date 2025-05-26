import os
import json
import pdfplumber
import docx2txt
import streamlit as st
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Agentic AI Innovation Engine", layout="wide")
load_dotenv()

# -- Import your agents --
from agents.ingredients_agent   import run as run_ingredients
from agents.technology_agent    import run as run_technology
from agents.benefits_agent      import run as run_benefits
from agents.situations_agent    import run as run_situations
from agents.motivations_agent   import run as run_motivations
from agents.outcomes_agent      import run as run_outcomes

st.title("🧠 Agentic AI Innovation Engine")

# Initialize storage for outputs
if "agent_outputs" not in st.session_state:
    st.session_state.agent_outputs = {}

# --- UI for file upload + project ID ---
project = "fe"
rnd_files = st.file_uploader("Upload R&D Files", type=["pdf","docx","txt"], accept_multiple_files=True)
mkt_files = st.file_uploader("Upload Marketing Files", type=["pdf","docx","txt"], accept_multiple_files=True)

if st.button("Extract & Run All Agents"):
    if not project or (not rnd_files and not mkt_files):
        st.error("Please enter a project ID and upload at least one file.")
        st.stop()

    # 1) Extract text
    rnd_text = ""
    for f in rnd_files or []:
        st.write(f"▶ Extracting R&D file {f.name}…")
        if f.name.endswith(".pdf"):
            with pdfplumber.open(f) as pdf:
                rnd_text += "\n".join(p.extract_text() or "" for p in pdf.pages)
        elif f.name.endswith(".docx"):
            rnd_text += docx2txt.process(f)
        else:
            rnd_text += f.read().decode("utf-8")

    mkt_text = ""
    for f in mkt_files or []:
        st.write(f"▶ Extracting Marketing file {f.name}…")
        if f.name.endswith(".pdf"):
            with pdfplumber.open(f) as pdf:
                mkt_text += "\n".join(p.extract_text() or "" for p in pdf.pages)
        elif f.name.endswith(".docx"):
            mkt_text += docx2txt.process(f)
        else:
            mkt_text += f.read().decode("utf-8")

    st.success("✅ Text extracted.")

    # 2) Define agents and placeholders
    col_r, col_m = st.columns(2)
    with col_r:
        st.subheader("🔬 R&D Agents")
        placeholders = {
            "IngredientsAgent": st.empty(),
            "TechnologyAgent":  st.empty(),
            "BenefitsAgent":    st.empty(),
        }
    with col_m:
        st.subheader("📣 Marketing Agents")
        placeholders.update({
            "SituationsAgent":  st.empty(),
            "MotivationsAgent": st.empty(),
            "OutcomesAgent":    st.empty(),
        })

    agents = {
        "IngredientsAgent":  (run_ingredients,  rnd_text),
        "TechnologyAgent":   (run_technology,   rnd_text),
        "BenefitsAgent":     (run_benefits,     rnd_text),
        "SituationsAgent":   (run_situations,   mkt_text),
        "MotivationsAgent":  (run_motivations,  mkt_text),
        "OutcomesAgent":     (run_outcomes,     mkt_text),
    }

    # 3) Execute in parallel
    with ThreadPoolExecutor() as exe:
        futures = {exe.submit(fn, txt): name for name, (fn, txt) in agents.items()}
        for future in as_completed(futures):
            name = futures[future]
            ph = placeholders[name]
            try:
                ph.info(f"⏳ {name} running…")
                result = future.result()
                # store & display
                st.session_state.agent_outputs[name] = result
                ph.subheader(f"{name} Output")
                ph.json(result)
            except Exception as e:
                ph.error(f"❌ {name} error: {e}")

# 4) On rerun, show cached outputs
if st.session_state.agent_outputs:
    st.markdown("---")
    st.header("🔄 Previous Agent Outputs")
    for name, output in st.session_state.agent_outputs.items():
        st.subheader(f"{name} Output")
        st.json(output)
