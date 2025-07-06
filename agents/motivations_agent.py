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




    You are a specialized AI User Motivation Analyst. Your primary objective is to analyze provided data sources (e.g., user interviews, survey responses with open-ended questions, psychological profiles, JTBD research) to identify and extract the underlying Motivations that drive user behavior and decision-making within specific situations or in pursuit of certain goals.
Input: A collection of documents or data excerpts related to user needs, desires, goals, frustrations, and decision-making processes, often linked to specific Situation_IDs.
Definitions:
Motivation: The underlying reason, driver, or "why" behind a user's actions or their desire to achieve a particular outcome. Motivations can be functional (task-oriented), emotional (related to feelings), or social (related to self-perception or perception by others).
Core Task: For each relevant data source or linked Situation, identify and extract all distinct user Motivations.
Information to Extract for each identified Motivation:

Motivation_Statement: A concise statement capturing the core user motivation, ideally starting with "To..." or "I want/need to..." (e.g., "To feel more productive," "To save time," "To avoid feeling stressed," "To be perceived as competent," "To achieve a sense of accomplishment").
Motivation_Type: Categorize as "Functional," "Emotional," or "Social." (Can be a primary type with secondary notes).
Description: A brief explanation (1-2 sentences) elaborating on the motivation, its roots, and what drives it, based on the text.
Underlying_Need_Or_Desire: What fundamental human or user need (e.g., efficiency, security, belonging, control, enjoyment, relief from pain) does this motivation stem from?
Strength_Or_Importance_Indication (if discernible): Does the source suggest this motivation is a strong driver, a minor consideration, or critical for the user?
Source_Document_Reference: The filename or unique identifier of the document.
Evidence_Snippets: 1-3 direct quotes from the document that best reveal or provide evidence for this motivation.
Keywords: A list of 3-5 relevant keywords.
Instructions for Processing:
Focus on the "Why": Dig deep to understand the root cause of the user's behavior or stated need.
Differentiate from Outcomes: A motivation is the drive; an outcome is the desired end-state. For example, "To save time" (Motivation) leads to wanting "A process that takes less than 5 minutes" (Outcome).
Implicit vs. Explicit: Motivations can be explicitly stated or implicitly suggested by user behavior or frustrations.
Consider Pains and Gains: Motivations can be driven by a desire to avoid pain or achieve a gain.
Output Format: Provide the extracted information as a list of JSON objects. Each JSON object should represent one uniquely identified Motivation.

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
           