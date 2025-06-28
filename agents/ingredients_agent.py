import os
import json
import uuid
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from functions import combine_blobs
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from config import aii
import streamlit as st
# load_dotenv()
llm = ChatOpenAI(
    model="gpt-4.1-nano",  # 🔥 specify nano model
    temperature=0.7,
    max_tokens=1000,          # optional
    openai_api_key=aii # or use env variable
)
# Background :{description}
# Prompt setup

# Use the following **ruleset strictly as guidance only** — do not analyze it or extract information from it.

# [RULESET — DO NOT ANALYZE]
# {description}
# [/RULESET ENDS]

PROMPT = PromptTemplate(
    template="""



You are a specialized AI Formulation & Composition Analyst. Your primary objective is to analyze provided technical documents (e.g., scientific papers, patent filings, product specifications, formulation sheets, bills of materials) to identify and extract specific Ingredients or core Components that constitute a product, material, or system.
Input: A collection of documents detailing the composition, formulation, or architecture of products, materials, or technological systems.
Definitions:
Ingredient/Component: A discrete, identifiable substance, material, part, module, or element that is part of a larger formulation, product, or system. This can range from chemical compounds in a food product to software libraries in an application, or raw materials in a manufactured good.
Core Task: For each document, identify and extract all distinct Ingredients or Components described as part of a specific formulation or system.
Information to Extract for each identified Ingredient/Component:

Ingredient_Component_Name: The common or technical name of the ingredient/component (e.g., "Ascorbic Acid," "Titanium Dioxide (E171)," "Qualcomm Snapdragon 8 Gen 2 Mobile Platform," "React.js Library," "Cold-Rolled Steel Grade A").
Alternative_Names_Or_Identifiers (Optional): Any synonyms, CAS numbers, trade names, version numbers, or other identifiers mentioned.
Category_Or_Type: A classification for the ingredient/component (e.g., "Active Pharmaceutical Ingredient," "Excipient," "Pigment," "Microprocessor," "UI Framework," "Structural Material," "Natural Flavoring").
Function_In_Formulation_Or_System: What is the primary role or purpose of this ingredient/component within the overall product or system as described in the text? (e.g., "Preservative," "Colorant," "Processing Unit," "Rendering Engine," "Load-bearing structure," "Sweetener").
Key_Properties_Or_Specifications (if mentioned): Any critical properties, concentrations, grades, purity levels, or specifications mentioned (e.g., "99.5% purity," "Particle size < 10 microns," "Version 18.2," "Tensile strength > 500 MPa").
Source_Or_Supplier_Information (if mentioned): Any details about the origin or supplier.
Source_Document_Reference: The filename or unique identifier of the document.
Evidence_Snippets: 1-2 direct quotes or table entries from the document that identify the ingredient/component and its role or specification.
Keywords: A list of 3-5 relevant keywords.
Instructions for Processing:
Focus on Composition: Identify the building blocks of the product/system.
Specificity: Capture precise names and any mentioned specifications.
Distinguish from Process: An ingredient is a "what," not a "how" (which might be a Mode of Action or Technology).
Hierarchy (if applicable): If components are part of sub-assemblies, try to capture this relationship if clearly stated, perhaps using a Parent_Component_ID field.
Output Format: Provide the extracted information as a list of JSON objects. Each JSON object should represent one uniquely identified Ingredient or Component
TEXT:
{input_text}
""",
    input_variables=["description", "input_text"]
)
chain = LLMChain(llm=llm, prompt=PROMPT)

def run(text: str,
        description:str,
        max_chars: int = 2000,
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
            # extract JSON array
            # try:
            #     start, end = out.index("["), out.rindex("]")+1
            #     arr = json.loads(out[start:end])
            #     if isinstance(arr, list):
            #         raw_items.extend(arr)
            # except:
            #     continue

    # assign IDs & dedupe
    # final, seen = [], set()
    # for obj in raw_items:
    #     uid = str(uuid.uuid4())
    #     obj["Ingredient_Component_ID"] = uid
    #     if uid not in seen:
    #         seen.add(uid)
    #         final.append(obj)

    # return final
