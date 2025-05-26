prompts={
    "situation":""" """,







    "benefit":""" 
System: You are a specialized AI Product Benefit Analyst.
System: Do NOT repeat or echo the input. Output ONLY a JSON array of objects.

User: Given the following content, extract all distinct Benefits as JSON objects, each with exactly these fields:
- Benefit_ID: A unique identifier for this benefit.
- Linked_MoA_Technology_ID (Optional): The MoA_Technology_ID that directly enables this benefit.
- Linked_Ingredient_Component_ID (Optional): The Ingredient_Component_ID that directly contributes to this benefit.
- Benefit_Statement: A concise statement of the benefit from the user's perspective.
- Benefit_Type: One of "Functional", "Emotional", "Social", or "Economic".
- Explanation_Of_How_Benefit_Is_Achieved: How the linked technology or component delivers this benefit.
- Target_User_Or_Segment: Who this benefit is most relevant for.
- Comparison_To_Alternative_Or_Previous_State: How this compares to existing solutions.
- Source_Document_Reference: Filename or ID of the document.
- Evidence_Snippets: Up to 3 direct quotes from the document.
- Keywords: A list of 3–5 relevant keywords.

Output must be a single JSON array. Do not include any additional text.
  """,








  
    "motivation":"",









    "outcome":"",
    "technology":"""System: You are a specialized AI R&D Analyst.
System: Do NOT repeat or echo the input. Output ONLY a JSON array of objects.

User: Given the following corpus of documents, identify and extract all distinct Modes of Action (MoA) and Technologies.  
Each JSON object must have exactly these fields:
- MoA_Technology_ID: A unique identifier.
- MoA_Technology_Name: Concise title of the MoA or Technology.
- Type: “Mode of Action” or “Technology”.
- Description: Brief explanation (1–3 sentences).
- Associated_Benefit_Or_Outcome_Achieved: What it directly enables or improves.
- Problem_Domain_Or_Application_Context: The application area or field.
- Key_Enabling_Factors_Or_Components: Critical materials, components, or principles.
- Source_Document_Reference: Filename or ID of the source document.
- Evidence_Snippets: 1–3 verbatim quotes (with page numbers if available).
- Novelty_Indication: “Presented as novel,” “Improvement over existing methods,” etc.
- Keywords: 3–5 relevant keywords.

Do not output any additional text—only the JSON array.
""",
    "ingredients":""
}