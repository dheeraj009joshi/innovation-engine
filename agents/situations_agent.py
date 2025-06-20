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

# load_dotenv()
llm = ChatOpenAI(
    model="gpt-4.1-nano",  # 🔥 specify nano model
    temperature=0.7,
    max_tokens=2000,          # optional
    openai_api_key=aii# or use env variable
)

PROMPT = PromptTemplate(
    template="""
You are a specialized AI User Context Analyst. Your primary objective is to analyze provided data sources (e.g., user interviews, ethnographic studies, customer support logs, forum discussions, product reviews) to identify and extract distinct Situations where target users encounter a specific problem, need, or opportunity relevant to a defined domain.
Input: A collection of documents or data excerpts related to user experiences, pain points, or behaviors within a specific domain or product category.
Definitions:
Situation: The specific context, circumstances, environment, or trigger event that a user experiences, leading them to seek a solution, make progress, or address a challenge. It's the "when" and "where" of a user's need.
Core Task: For each relevant data source, identify and extract all distinct Situations described.
Information to Extract for each identified Situation:
Situation_Name: A concise, descriptive name or title for the situation (e.g., "Commuting to Work During Rush Hour," "Preparing a Quick Weeknight Family Meal," "Last-Minute Gift Shopping Online," "Collaborating on a Document Remotely").
Description: A brief explanation (1-3 sentences) of the circumstances, environment, and key activities or triggers involved in this situation, based on the text.
Key_Contextual_Factors: List any critical environmental, temporal, social, or resource-related factors explicitly mentioned as defining or influencing this situation (e.g., "Time pressure," "Limited budget," "Presence of children," "Unreliable internet connection," "Specific location").
Associated_Problem_Or_Opportunity: What specific problem, challenge, unmet need, or opportunity does the user typically encounter or perceive in this situation?
Frequency_Or_Commonality_Indication (if discernible): Does the source suggest this situation is frequent, rare, or common for the target user? (e.g., "Daily occurrence," "Occasional event," "Commonly reported," "Niche scenario").
Source_Document_Reference: The filename or unique identifier of the document from which this information was extracted.
Evidence_Snippets: 1-3 direct quotes (verbatim excerpts) from the document that best describe or provide evidence for this situation. Include page numbers or timestamps if possible.
Keywords: A list of 3-5 relevant keywords associated with this situation extracted from the text.
Instructions for Processing:
Focus on Context: Prioritize details that describe the user's environment and the circumstances leading to a need.
Distinguish from Motivations/Outcomes: Isolate the situational context itself, separate from why the user acts or what they want to achieve (those are separate elements).
Granularity: Aim for a level of detail that is specific enough to be actionable but not overly narrow. Group very similar minor variations if the core context is identical.
User-Centric View: Extract situations from the user's perspective.
Output Format: Provide the extracted information as a list of JSON objects. Each JSON object should represent one uniquely identified Situation.

TEXT:
{input_text}
""",
    input_variables=["input_text"],
)
chain = LLMChain(llm=llm, prompt=PROMPT)
def run(text: str,
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
        futures = {exe.submit(chain.invoke, {"input_text": c}): c for c in chunks}
        for f in as_completed(futures):
            out = f.result()["text"]
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

    # # assign IDs & dedupe
    # final, seen = [], set()
    # for obj in raw_items:
    #     uid = str(uuid.uuid4())
    #     obj["Situation_ID"] = uid
    #     if uid not in seen:
    #         seen.add(uid)
    #         final.append(obj)

    # return final