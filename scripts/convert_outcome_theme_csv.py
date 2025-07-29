
import pandas as pd

data=open("../Outcome_test.json", "r", encoding="utf-8").read()
import json
data=json.loads(data)

themes=[]
THEME_NAME=[]
THEME_DESCRIPTION=[]
SUBTHEME_NAME=[]
SUBTHEME_DESCRIPTION=[]
Outcome_NAME=[]
Outcome_DESCRIPTION=[]
CONSUMER_STATEMENT=[]
EVIDENCE_SNIPPETS=[]
Outcome_REFERENCES=[]
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
            if "Outcomes" in j:
                for k in j["Outcomes"]:
                    THEME_NAME.append(i.get("Theme", ""))
                    THEME_DESCRIPTION.append(i.get("Description", ""))
                    SUBTHEME_NAME.append(j.get("Subtheme", ""))
                    SUBTHEME_DESCRIPTION.append(j.get("Description", ""))
                    Outcome_NAME.append(k.get("Outcome Name", ""))
                    Outcome_DESCRIPTION.append(k.get("Outcome Description", ""))
                    CONSUMER_STATEMENT.append(k.get("Consumer Statement", ""))
                    EVIDENCE_SNIPPETS.append(k.get("Evidence_Snippets", ""))
                    Outcome_REFERENCES.append(k.get("Outcome References", 0))
df= pd.DataFrame({
    "Theme Name": THEME_NAME,
    "Theme Description": THEME_DESCRIPTION,
    "Subtheme Name": SUBTHEME_NAME,
    "Subtheme Description": SUBTHEME_DESCRIPTION,
    "Outcome Name": Outcome_NAME,
    "Outcome Description": Outcome_DESCRIPTION,
    "Consumer Statement": CONSUMER_STATEMENT,
    "Evidence Snippets": EVIDENCE_SNIPPETS,
    "Outcome References": Outcome_REFERENCES
})


print(df)

df.to_csv("sleep_Outcomes_all_themes.csv", index=False)
