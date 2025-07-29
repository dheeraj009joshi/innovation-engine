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

from config import AGENT_MAX_TOKENS,MODEL_NAME,MAX_CHUNKS

# load_dotenv()
llm = ChatOpenAI(
    model=MODEL_NAME,  # 🔥 specify nano model
    temperature=0.7,
    max_tokens=AGENT_MAX_TOKENS,          # optional
    openai_api_key=aii # or use env variable
)


PROMPT = PromptTemplate(
    template="""


    You are an expert thematic analyst.
 Your task is to process the Outcomes from the uploaded document and group them into a set of mutually exclusive, radically different high-level themes and, within each theme, a set of mutually exclusive, highly specific subthemes.
Definitions & Instructions:
Theme (Definition):
 A theme is a high-level, unambiguous, and mutually exclusive “bucket” that describes a single, coherent type of Outcome. Each theme must be meaningfully different from all others. The theme’s label and description must clearly capture the core concepts shared by all Outcomes within it.
 Theme labels and descriptions must be distinctive, specific, and never generic or catch-all. Do not use vague or all-encompassing categories.
Subtheme (Definition):
 A subtheme is a specific, mutually exclusive facet within a theme, grouping Outcomes that share a distinct characteristic or angle. Each subtheme must be clear, concrete, and limited in scope so that each Outcome fits only one subtheme within its parent theme.
 Do not use vague, generic, or “miscellaneous” categories such as “General Habits,” “Miscellaneous,” or “Other.” Each subtheme must have a clear, descriptive label that precisely captures what all its Outcomes have in common.
 If you cannot find a clear, unifying trait for a group, split it into more specific subthemes—even if this results in a larger number of more focused subthemes.
Resonance (Definition):
 A Outcome “resonates with” or “fits” a theme/subtheme if all the main words and concepts in the Outcome are explicitly covered by the theme’s and subtheme’s label and description, with no ambiguity and no other fit possible.
Instructions:
For each Outcome in the uploaded document, extract the Outcome Name and Outcome Description fields exactly as written (no changes).


Assign each Outcome to exactly one theme and one subtheme (both mutually exclusive).


For the Consumer Statement and Evidence_Snippets (Exact) fields, use only the content from the "Evidence_Snippets" column in the document. If there are multiple snippets, separate them with a vertical bar (|).


For the Consumer Statement, select one snippet from this column and reword it to correct all spelling errors, fix grammar, and improve readability, ensuring the statement is clear, natural, and professional—but do not change the meaning. Do not include any typos, artifacts, or OCR errors in any output field. Always improve clarity and flow.


For the Outcome References column, provide the count of evidence snippets used for that Outcome.


Do not invent, summarize, merge, or paraphrase the Outcome names or descriptions—only reword the example consumer statement for clarity.


If any subtheme contains more than 12 Outcomes, you MUST split it further into smaller, more specific, and descriptive subthemes. Avoid lumping Outcomes into a single subtheme unless they are truly, specifically related.


Never create a subtheme labeled “General,” “Miscellaneous,” “Other,” or anything similar. Every subtheme must be unambiguous, descriptive, and distinctive.


Theme and subtheme descriptions must be distinctive, specific, and avoid generic or catch-all language.


For each theme and subtheme, provide:
Theme name (short, descriptive)


A one-sentence description of the theme


Subtheme name (short, descriptive)


A one-sentence description of the subtheme


For each Outcome within that subtheme, provide:
Outcome Name (exact, from document)


Outcome Description (exact, from document)


Consumer Statement (reworded for clarity, same meaning, using one snippet from the "Evidence_Snippets" column; all spelling and grammar errors must be fixed)


Evidence_Snippets (Exact; all snippets from the "Evidence_Snippets" column, separated by |)


Outcome References (count of evidence snippets in the "Evidence_Snippets" column)


Special Quality Rule:
 If you find yourself about to create a subtheme with a generic or vague label (e.g., “General,” “Miscellaneous,” “Other,” “General Habits & Environment”), STOP and break the Outcomes into more sharply differentiated, specific subthemes. Each subtheme must be clearly understandable and stand alone on its own label and description.
 All output fields must be free from spelling and grammatical errors.
Example:
Bad Consumer Statement: “Alarm ringing in byout yoyou are never going to wakeyoup again”


Good Consumer Statement: “The alarm keeps ringing, but you never really wake up again.”
 Always produce a “Good” style output—clear, natural, and error-free, but with the original meaning.



Output Format: Provide the extracted information as a list of JSON objects. Each JSON object should represent one uniquely identified Theme.
{{
        "Theme": "Sleep Environment and Posture Optimization",
        "Description": "Outcomes related to creating an optimal sleep environment and maintaining proper posture to improve sleep quality and health.",
        "Subthemes": [
            {{
                "Subtheme": "Sleeping Posture Awareness for Spine Health",
                "Description": "Outcomes focused on awareness and adjustment of sleeping positions to promote spinal health.",
                "Outcomes": [
                    {{
                        "Outcome Name": "Sleeping Posture Awareness for Spine Health",
                        "Outcome Description": "Focuses on increasing awareness about correct sleeping postures to support spine health.",
                        "Consumer Statement": "Increasing awareness about proper sleeping positions to support spinal health.",
                        "Evidence_Snippets": "Focuses on increasing awareness about correct sleeping postures to support spine health.",
                        "Outcome References": 1
                    }}
                ]
            }},
            {{
                "Subtheme": "Interest in Zero-Gravity Sleep Solutions",
                "Description": "Outcomes involving curiosity or desire for sleep solutions that mimic zero-gravity conditions to enhance comfort and reduce pressure.",
                "Outcomes": [
                    {{
                        "Outcome Name": "Interest in Zero-Gravity Sleep Solutions",
                        "Outcome Description": "Expresses interest in sleep systems that simulate zero-gravity to improve sleep comfort.",
                        "Consumer Statement": "Interest in sleep systems that simulate zero-gravity to enhance comfort during sleep.",
                        "Evidence_Snippets": "Interest in sleep systems that simulate zero-gravity to enhance comfort during sleep.",
                        "Outcome References": 1
                    }}
                ]
            }},
            {{
                "Subtheme": "Addressing Snoring and Sleep Disruptions",
                "Description": "Outcomes aimed at reducing snoring and resolving sleep interruptions to improve sleep quality.",
                "Outcomes": [
                    {{
                        "Outcome Name": "Addressing Snoring and Sleep Disruptions",
                        "Outcome Description": "Deals with solutions or concerns related to snoring and sleep disturbances.",
                        "Consumer Statement": "Looking for ways to reduce snoring and minimize sleep disruptions.",
                        "Evidence_Snippets": "Looking for ways to reduce snoring and minimize sleep disruptions.",
                        "Outcome References": 1
                    }}
                ]
            }}
        ]
    }},

    ## sample theme structure make sure all the theme objects has all the keys 

TEXT:
{{input_text}}
""",
    input_variables=["description", "input_text"]
)

chain = LLMChain(llm=llm, prompt=PROMPT)

def run(text: str,
        description:str,
        max_chars: int = MAX_CHUNKS,
        overlap: int = 200,
        max_workers: int = 10
) -> List[Dict]:
    # chunking
    print(text)
    print(len(text))
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i: i+max_chars])
        i += max_chars - overlap
    print(f"Total chunks: {len(chunks)}")
    # parallel calls
    raw_items: List[Dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(chain.invoke, {"input_text": c,"description": description}): c for c in chunks}
        for f in as_completed(futures):
            out = f.result()["text"]
            print(out)
            raw_items.append(out)
        themes=[]
        f_data= combine_blobs(raw_items)
        for i in f_data:
            if "Themes" in i:
                for j in i["Themes"]:
                    if "Theme" in j:
                        themes.append(j)
            else:
                themes.append(i)
        return themes
           