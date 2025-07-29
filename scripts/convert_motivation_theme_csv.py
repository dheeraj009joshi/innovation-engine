
import pandas as pd

data=open("Motivation_test.json", "r", encoding="utf-8").read()
import json
data=json.loads(data)

themes=[]
THEME_NAME=[]
THEME_DESCRIPTION=[]
SUBTHEME_NAME=[]
SUBTHEME_DESCRIPTION=[]
Motivation_NAME=[]
Motivation_DESCRIPTION=[]
CONSUMER_STATEMENT=[]
EVIDENCE_SNIPPETS=[]
Motivation_REFERENCES=[]
for i in data:
    if "Themes" in i:
        for j in i["Themes"]:
            if "Theme" in j:
                themes.append(j)
    else:
        themes.append(i)

for i in themes:
    if "Subthemes" in i:
        for j in i["Subthemes"]: 
            if "Motivations" in j:
                for k in j["Motivations"]:
                    THEME_NAME.append(i.get("Theme", ""))
                    THEME_DESCRIPTION.append(i.get("Description", ""))
                    SUBTHEME_NAME.append(j.get("Subtheme", ""))
                    SUBTHEME_DESCRIPTION.append(j.get("Description", ""))
                    Motivation_NAME.append(k.get("Motivation Name", ""))
                    Motivation_DESCRIPTION.append(k.get("Motivation Description", ""))
                    CONSUMER_STATEMENT.append(k.get("Consumer Statement", ""))
                    EVIDENCE_SNIPPETS.append(k.get("Evidence_Snippets", ""))
                    Motivation_REFERENCES.append(k.get("Motivation References", 0))
df= pd.DataFrame({
    "Category": THEME_NAME,
    "Category Description": THEME_DESCRIPTION,
    "Theme": SUBTHEME_NAME,
    "Subtheme Description": SUBTHEME_DESCRIPTION,
    "Motivation": Motivation_NAME,
    "Motivation Description": Motivation_DESCRIPTION,
    "Consumer Statement": CONSUMER_STATEMENT,
    "Evidence Snippets": EVIDENCE_SNIPPETS,
    "Motivation References": Motivation_REFERENCES
})


print(df)

df.to_csv("sleep_Motivations_all_themes.csv", index=False)
