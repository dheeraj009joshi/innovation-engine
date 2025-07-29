from agents.Themes.situation_themes import run
import pandas as pd



text=""
# Select,Motivation_Statement,Motivation_Type,Description,Underlying_Need_Or_Desire,Strength_Or_Importance_Indication,Source_Document_Reference,Evidence_Snippets,Keywords

df=pd.read_csv("SITUATIONS_5500POSTS.csv")

for i in df.iterrows():
    row = i[1]
    text += f"""
    Situation Name: {row['Situation_Name']}
    Situation Description: {row['Description']}
    Evidence Snippets: {row['Evidence_Snippets']}
    Key Contextual Factors: {row['Key_Contextual_Factors']}
    Associated Problem Or Opportunity: {row['Associated_Problem_Or_Opportunity']}
    Frequency Or Commonality Indication: {row['Frequency_Or_Commonality_Indication']}
    Source Document Reference: {row['Source_Document_Reference']}
    Keywords: {row['Keywords']}
    \n\n
    """
aa=run(text, "Test Description")

ff=open("situation_test.json", "w")
import json
json.dump(aa, ff, indent=4)
ff.close()
print("Done")