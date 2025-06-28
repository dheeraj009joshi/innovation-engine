import os
import json
import uuid
from typing import List, Dict
from dotenv import load_dotenv
from functions import combine_blobs
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from concurrent.futures import ThreadPoolExecutor,as_completed
from config import aii
import streamlit as st


# load_dotenv()
llm = ChatOpenAI(
    model="gpt-4.1-nano",  # 🔥 specify nano model
    temperature=0.7,
    max_tokens=2000,          # optional
    openai_api_key=aii # or use env variable
)

#  Background :{description}
PROMPT = PromptTemplate(
    template="""


 
The specific underlying mechanism (e.g., biochemical, physical, chemical, computational, procedural) by which an intervention, substance, material, process, or system produces a specific effect, achieves a desired outcome, or solves a defined problem. This is the "how it works" at a fundamental or applied level.
Technology: A novel or established application of scientific knowledge, engineering principles, methods, materials, apparatus, or systems designed to achieve a practical purpose or solve a specific problem. This can include new manufacturing processes, analytical techniques, material compositions, software algorithms, or system architectures.
Core Task: For each document in the corpus, identify and extract all distinct MoAs and Technologies described.
Information to Extract for each identified MoA/Technology:
MoA_Technology_Name: A concise, descriptive name or title for the MoA or Technology (e.g., "CRISPR-Cas9 Gene Editing," "Nanoparticle Encapsulation for Drug Delivery," "Quantum Annealing for Optimization," "Photocatalytic Oxidation Process").
Type: Categorize as "Mode of Action" or "Technology."
Description: A brief explanation (1-3 sentences) of what it is and how it fundamentally works or what it enables, based on the text.
Associated_Benefit_Or_Outcome_Achieved: What specific benefit, outcome, or problem does this MoA/Technology directly enable, improve, or solve as described in the context of the paper? (e.g., "Increased drug bioavailability," "Precise genetic modification," "Reduced manufacturing cost," "Enhanced material strength," "Faster problem solving").
Problem_Domain_Or_Application_Context: The specific scientific field, industry, or application area where this MoA/Technology is being discussed or applied in the document (e.g., "Oncology Drug Development," "Water Purification," "Materials Science – Polymers," "Machine Learning – Image Recognition").
Key_Enabling_Factors_Or_Components: List any critical materials, substances, equipment, software components, or scientific principles explicitly mentioned as essential for this MoA/Technology to function (e.g., "Cas9 nuclease & guide RNA," "Liposomes," "Titanium Dioxide nanoparticles," "Specific catalyst type," "Convolutional Neural Networks").
Source_Document_Reference: The filename or unique identifier of the document from which this information was extracted.
Evidence_Snippets: 1-3 direct quotes (verbatim excerpts) from the document that best describe or provide evidence for the MoA/Technology and its function. Include page numbers if possible.
Novelty_Indication (if discernible): Does the paper suggest this MoA/Technology is novel, an improvement, or a new application? (e.g., "Presented as novel," "Improvement over existing methods," "Established but applied to new area," "Not specified").
Keywords: A list of 3-5 relevant keywords associated with this MoA/Technology extracted from the text.
Instructions for Processing:
Thoroughness: Scan each document comprehensively. MoAs/Technologies may be described in various sections including Abstract, Introduction (for context/problem), Methods/Methodology, Results, Discussion, and sometimes even in Figure/Table captions.
Specificity: Focus on the core mechanism or technological innovation, not just generic experimental procedures or standard equipment unless that equipment is the novel technology or central to a specific MoA.
Distinction: Differentiate between an intended outcome and the MoA/Technology that achieves it. Extract both.
Multiple Instances: If a document describes multiple distinct MoAs or Technologies, extract each one as a separate record.
Contextual Understanding: Interpret the information within the context of the document.
Avoid Generalities: Do not extract overly broad statements unless they clearly define a specific, bounded MoA or Technology.
Handle Ambiguity: If an MoA/Technology is not clearly defined or lacks sufficient detail for all fields, fill what you can and note any ambiguities in the Description or a separate Notes field (optional).
Output Format: Provide the extracted information as a list of JSON objects. Each JSON object should represent one uniquely identified MoA or Technology.

TEXT:
{input_text}


""",
    input_variables=["description", "input_text"]
)
chain = LLMChain(llm=llm, prompt=PROMPT)

def chunk_text(text: str, max_chars=2000, overlap=200) -> List[str]:
    chunks, i = [], 0
    while i < len(text):

        chunks.append(text[i : i + max_chars])
        i += max_chars - overlap
    return chunks


def run(text: str,
        description:str,
        max_chars: int = 20000,
        overlap: int = 200,
        max_workers: int = 10
) -> List[Dict]:
    # chunking
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i: i+max_chars])
        i += max_chars - overlap

    # parallel calls
    raw_items: List[Dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(chain.invoke, {"input_text": c,"description": description}): c for c in chunks}
        for f in as_completed(futures):

            out = f.result()['text']
            raw_items.append(out)
        return combine_blobs(raw_items)
