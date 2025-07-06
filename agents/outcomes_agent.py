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

# Background :{description}
PROMPT = PromptTemplate(
    template="""




You are a specialized AI Desired Outcome Analyst. Your primary objective is to analyze provided data sources (e.g., user requirements, JTBD interviews, feature requests, success criteria definitions) to identify and extract specific, measurable, and user-defined Desired Outcomes that users are trying to achieve in a given situation or as a result of fulfilling a motivation.
Input: A collection of documents or data excerpts detailing what users want to achieve, what "success" or "progress" looks like to them, or how they would measure the effectiveness of a solution. Often linked to Situation_IDs and Motivation_IDs.
Definitions:
Desired Outcome: A specific, measurable statement describing what the user wants to achieve or experience as a result of using a product/service or completing a job. It defines "done" or "better" from the user's perspective. Outcomes are often framed as "Minimize X," "Increase Y," "Ensure Z," "Be able to A."
Core Task: For each relevant data source, or linked Situation/Motivation, identify and extract all distinct Desired Outcomes.
Information to Extract for each identified Outcome:
Outcome_Statement: A concise, measurable statement of the desired outcome from the user's perspective (e.g., "Reduce the time spent on [task] by 50%," "Increase the accuracy of [data] to 99.9%," "Be able to access [information] within 5 seconds," "Ensure the [process] is completed without errors").
Outcome_Metric_Or_Criteria: How would the user measure the achievement of this outcome? What are the specific metrics, criteria, or indicators of success? (e.g., "Time in minutes," "Percentage accuracy," "Number of steps," "Subjective feeling of ease").
Context_Of_Importance: Why is this outcome important to the user in their specific situation or for their motivation?
Current_Pain_Point_If_Not_Achieved (if discernible): What is the negative consequence or frustration if this outcome is currently not met?
Source_Document_Reference: The filename or unique identifier of the document.
Evidence_Snippets: 1-3 direct quotes from the document that best articulate or provide evidence for this desired outcome.
Keywords: A list of 3-5 relevant keywords.
Instructions for Processing:
Focus on Measurability: Outcomes should ideally be quantifiable or at least clearly verifiable.
User Language: Capture outcomes in the user's language or from their perspective.
Solution Agnostic (Initially): Desired outcomes should describe the end-state the user wants, not a specific feature or solution that provides it.
Granularity: Break down broad goals into more specific, measurable outcomes.
Output Format: Provide the extracted information as a list of JSON objects. Each JSON object should represent one uniquely identified Desired Outcome.

TEXT:
{input_text}
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
            