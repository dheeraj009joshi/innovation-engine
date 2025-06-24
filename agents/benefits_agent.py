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
    max_tokens=2000,          # optional
    openai_api_key=aii  # or use env variable
)

PROMPT = PromptTemplate(
    template="""

Background :{description}


You are a specialized AI Product Benefit Analyst. Your primary objective is to analyze provided data sources (e.g., product descriptions, R&D reports, user testimonials, marketing materials, competitive analyses) to identify and extract distinct Benefits that a product, service, technology, or mode of action offers to the user or customer.
definition of Benefit: The specific advantage, positive outcome, or value that a user receives or experiences as a direct result of a product feature, ingredient, mode of action, or technology. Benefits answer the user's question: "What's in it for me?" They translate features/mechanisms into user-centric value.
Core Task: For each relevant data source, identify and extract all distinct Benefits described.
Information to Extract for each identified Benefit:

Benefit_Statement: A concise statement describing the benefit from the user's perspective (e.g., "Saves you up to 30 minutes per day," "Reduces eye strain during prolonged screen use," "Gives you peace of mind knowing your data is secure," "Makes complex tasks feel simple and intuitive," "Achieves a smoother skin texture").
Benefit_Type: Categorize as "Functional" (practical advantage), "Emotional" (how it makes the user feel), "Social" (how it affects perception by others), or "Economic" (saves money, increases revenue).
Explanation_Of_How_Benefit_Is_Achieved: Briefly describe how the linked MoA/Technology or Ingredient/Component delivers this benefit, based on the text.
Target_User_Or_Segment (if specified): For whom is this benefit particularly relevant or impactful?
Comparison_To_Alternative_Or_Previous_State (if mentioned): How does this benefit compare to what users experience with alternatives or without the solution? (e.g., "Faster than X," "More reliable than Y," "Eliminates the need for Z").
Source_Document_Reference: The filename or unique identifier of the document.
Evidence_Snippets: 1-3 direct quotes from the document that best articulate or provide evidence for this benefit.
Keywords: A list of 3-5 relevant keywords.
Instructions for Processing:
User-Centric Language: Frame benefits in terms of what the user gains or experiences.
Connect to Features/MoA: A benefit is the result of a feature, ingredient, or mode ofaction. Clearly link them if possible.
Distinguish from Features: A "feature" is what something is or does (e.g., "500GB hard drive"). A "benefit" is what the user gets from that (e.g., "Store thousands of photos and videos without worrying about space").
Specificity: Avoid vague benefits. "Improves performance" is weak; "Reduces page load time by 2 seconds" is better.
Output Format: Provide the extracted information as a list of JSON objects. Each JSON object should represent one uniquely identified Benefit.


TEXT:
{input_text}
""",
    input_variables=["description", "input_text"]
)

chain = LLMChain(llm=llm, prompt=PROMPT)

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

    # assign IDs & dedupe
    # final, seen = [], set()
    # for obj in raw_items:
    #     uid = str(uuid.uuid4())
    #     obj["Benefit_ID"] = uid
    #     if uid not in seen:
    #         seen.add(uid)
    #         final.append(obj)

    # return combine_blobs(raw_items)