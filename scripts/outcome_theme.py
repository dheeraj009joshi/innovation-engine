from Themes.outcome_themes import run 
import pandas as pd



text=""
# Select,Outcome_Statement,Outcome_Metric_Or_Criteria,Context_Of_Importance,Current_Pain_Point_If_Not_Achieved,Source_Document_Reference,Evidence_Snippets,Keywords,Situation_ID,Motivation_ID,Context_Of_Importantce,Context_Of_Important,Desired_Outcome_Statement

df=pd.read_csv("OutcomeS_5500POSTS.csv",on_bad_lines='skip')

for i in df.iterrows():
    row = i[1]
    text += f"""
    Outcome Name: {row['Outcome_Statement']}
    Outcome Metric Or Criteria: {row['Outcome_Metric_Or_Criteria']}
    Context Of Importance: {row['Context_Of_Importance']}
    Current Pain Point If Not Achieved: {row['Current_Pain_Point_If_Not_Achieved']}
    Source Document Reference: {row['Source_Document_Reference']}
    Evidence Snippets: {row['Evidence_Snippets']}   
    Keywords: {row['Keywords']}
    \n\n
    """
aa=run(text, "Test Description")

ff=open("Outcome_test.json", "w")
import json
json.dump(aa, ff, indent=4)
ff.close()
print("Done")