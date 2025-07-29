from Themes.motivation_themes import run 
import pandas as pd



text=""
# Motivation_Name,Description,Key_Contextual_Factors,Associated_Problem_Or_Opportunity,Frequency_Or_Commonality_Indication,Source_Document_Reference,Evidence_Snippets,Keywords,Associated_Problem_Or_Challenge,

df=pd.read_csv("MOTIVATIONS_5500POSTS.csv")

for i in df.iterrows():
    row = i[1]
    text += f"""
    Motivation Name: {row['Motivation_Statement']}
    Motivation Type: {row['Motivation_Type']}
    Underlying Need Or Desire: {row['Underlying_Need_Or_Desire']}
    Strength Or Importance Indication: {row['Strength_Or_Importance_Indication']}
    Source Document Reference: {row['Source_Document_Reference']}
    Consumer Statement: {row['Motivation_Statement']}
    Motivation Description: {row['Description']}
    Evidence Snippets: {row['Evidence_Snippets']}
    Source Document Reference: {row['Source_Document_Reference']}
    Keywords: {row['Keywords']}
    \n\n
    """
aa=run(text, "Test Description")

ff=open("Motivation_test.json", "w")
import json
json.dump(aa, ff, indent=4)
ff.close()
print("Done")