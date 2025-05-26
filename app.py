import os
import json
import pdfplumber
import docx2txt
import streamlit as st
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1) Force a light theme
st.set_page_config(
     page_title="Agentic AI Innovation Engine",
     layout="wide",
)

load_dotenv()

# 2) Import each agent’s run function
from agents.ingredients_agent import run as run_ingredients
from agents.technology_agent import run as run_technology
from agents.benefits_agent import run as run_benefits
from agents.situations_agent import run as run_situations
from agents.motivations_agent import run as run_motivations
from agents.outcomes_agent import run as run_outcomes

st.title("🧠 Agentic AI Innovation Engine")

# --- 1) Upload & Extract Text ---
project = "dvh"
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

    # 2) Prepare columns and placeholders
    col_r, col_m = st.columns(2)
    with col_r:
        st.subheader("🔬 R&D Agents")
        rd_placeholders = {
            "IngredientsAgent":  (st.empty(), st.empty()),
            "TechnologyAgent":   (st.empty(), st.empty()),
            "BenefitsAgent":     (st.empty(), st.empty()),
        }
    with col_m:
        st.subheader("📣 Marketing Agents")
        mk_placeholders = {
            "SituationsAgent":   (st.empty(), st.empty()),
            "MotivationsAgent":  (st.empty(), st.empty()),
            "OutcomesAgent":     (st.empty(), st.empty()),
        }

    # 3) Map names → (fn, status_ph, output_ph, text)
    agents = {}
    for name, fn in [
        ("IngredientsAgent", run_ingredients),
        ("TechnologyAgent", run_technology),
        ("BenefitsAgent", run_benefits),
    ]:
        status_ph, output_ph = rd_placeholders[name]
        agents[name] = (fn, status_ph, output_ph, rnd_text)

    for name, fn in [
        ("SituationsAgent", run_situations),
        ("MotivationsAgent", run_motivations),
        ("OutcomesAgent", run_outcomes),
    ]:
        status_ph, output_ph = mk_placeholders[name]
        agents[name] = (fn, status_ph, output_ph, mkt_text)

    # 4) Run all in parallel
    with ThreadPoolExecutor() as executor:
        futures = {}
        for name, (fn, status_ph, _, txt) in agents.items():
            status_ph.info(f"⏳ {name} running…")
            futures[executor.submit(fn, txt)] = name

        for future in as_completed(futures):
            name = futures[future]
            fn, status_ph, output_ph, _ = agents[name]
            try:
                result = future.result()
                # clear status only
                status_ph.empty()

                # Title + JSON or text
                output_ph.subheader(f"{name} Output")
                if isinstance(result, list):
                    output_ph.json(result)
                    # Provide download button
                    json_bytes = json.dumps(result, indent=2).encode("utf-8")
                    output_ph.download_button(
                        label=f"📥 Download {name}JSON",
                        data=json_bytes,
                        file_name=f"{project}_{name}.json",
                        mime="application/json"
                    )
                else:
                    output_ph.text(str(result))

            except Exception as e:
                status_ph.error(f"❌ {name} error: {e}")
