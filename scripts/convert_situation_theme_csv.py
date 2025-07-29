
import pandas as pd

data=open("situation_test.json", "r", encoding="utf-8").read()
import json
data=json.loads(data)

themes=[]
THEME_NAME=[]
THEME_DESCRIPTION=[]
SUBTHEME_NAME=[]
SUBTHEME_DESCRIPTION=[]
SITUATION_NAME=[]
SITUATION_DESCRIPTION=[]
CONSUMER_STATEMENT=[]
EVIDENCE_SNIPPETS=[]
SITUATION_REFERENCES=[]
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
            if "Situations" in j:
                for k in j["Situations"]:
                    THEME_NAME.append(i.get("Theme", ""))
                    THEME_DESCRIPTION.append(i.get("Description", ""))
                    SUBTHEME_NAME.append(j.get("Subtheme", ""))
                    SUBTHEME_DESCRIPTION.append(j.get("Description", ""))
                    SITUATION_NAME.append(k.get("Situation Name", ""))
                    SITUATION_DESCRIPTION.append(k.get("Situation Description", ""))
                    CONSUMER_STATEMENT.append(k.get("Consumer Statement", ""))
                    EVIDENCE_SNIPPETS.append(k.get("Evidence_Snippets", ""))
                    SITUATION_REFERENCES.append(k.get("Situation References", 0))
df= pd.DataFrame({
    "Theme Name": THEME_NAME,
    "Theme Description": THEME_DESCRIPTION,
    "Subtheme Name": SUBTHEME_NAME,
    "Subtheme Description": SUBTHEME_DESCRIPTION,
    "Situation Name": SITUATION_NAME,
    "Situation Description": SITUATION_DESCRIPTION,
    "Consumer Statement": CONSUMER_STATEMENT,
    "Evidence Snippets": EVIDENCE_SNIPPETS,
    "Situation References": SITUATION_REFERENCES
})


print(df)

df.to_csv("sleep_situations_all_themes.csv", index=False)
