# import json


# f=open("test_study.json","r",encoding="utf-8")

# jsn_data=json.loads(f.read())
# print(jsn_data)
# QUESTIONS = []
# OPTIONS = []
# TOTAL = []
# MALE = []
# FEMALE = []
# MINDSET_1OF2 = []
# MINDSET_2OF2 = []
# MINDSET_1OF3 = []
# MINDSET_2OF3 = []
# MINDSET_3OF3 = []

# PRELIM_Q1 = []
# PRELIM_Q2 = []
# PRELIM_Q3 = []
# PRELIM_Q4 = []
# PRELIM_Q5 = []
# PRELIM_Q6 = []
# PRELIM_Q7 = []
# PRELIM_Q8 = []

# # sheets = ["(B) Combined", "(R) Combined", "(T) Combined"]
# sheets = ["(T) Combined"]

# for sheet in sheets:
#         data = jsn_data["study"]["studyData"][sheet]
#         questions = data["Data"]["Questions"]

#         for question in questions:


#                 question_text = question["Question"]

#                 for option in question["options"]:
#                         QUESTIONS.append(question_text)
#                         OPTIONS.append(option.get("optiontext"))
#                         TOTAL.append(option.get("Total", None))
#                         MALE.append(option.get("Gender Segments", {}).get("Male", None))
#                         FEMALE.append(option.get("Gender Segments", {}).get("Female", None))

#                         # Mindsets
#                         mindsets = {k: None for k in [
#                                 "Mindset 1 of 2", "Mindset 2 of 2",
#                                 "Mindset 1 of 3", "Mindset 2 of 3", "Mindset 3 of 3"
#                         ]}
#                         for mindset in option.get("Mindsets", []):
#                                 for k, v in mindset.items():
#                                         mindsets[k] = v

#                         MINDSET_1OF2.append(mindsets["Mindset 1 of 2"])
#                         MINDSET_2OF2.append(mindsets["Mindset 2 of 2"])
#                         MINDSET_1OF3.append(mindsets["Mindset 1 of 3"])
#                         MINDSET_2OF3.append(mindsets["Mindset 2 of 3"])
#                         MINDSET_3OF3.append(mindsets["Mindset 3 of 3"])

#                         # Prelim Questions (up to 8)
#                         prelim_answers = option.get("Prelim-Answer Segments", [])
#                         prelim_values = [list(p.values())[0] for p in prelim_answers[:8]]

#                         # Pad with None if fewer than 8
#                         while len(prelim_values) < 8:
#                                 prelim_values.append(None)

#                         PRELIM_Q1.append(prelim_values[0])
#                         PRELIM_Q2.append(prelim_values[1])
#                         PRELIM_Q3.append(prelim_values[2])
#                         PRELIM_Q4.append(prelim_values[3])
#                         PRELIM_Q5.append(prelim_values[4])
#                         PRELIM_Q6.append(prelim_values[5])
#                         PRELIM_Q7.append(prelim_values[6])
#                         PRELIM_Q8.append(prelim_values[7])


#         import pandas as pd

#         df = pd.DataFrame({
#         "Question": QUESTIONS,
#         "Option": OPTIONS,
#         "Total": TOTAL,
#         "Male": MALE,
#         "Female": FEMALE,
#         "Mindset 1 of 2": MINDSET_1OF2,
#         "Mindset 2 of 2": MINDSET_2OF2,
#         "Mindset 1 of 3": MINDSET_1OF3,
#         "Mindset 2 of 3": MINDSET_2OF3,
#         "Mindset 3 of 3": MINDSET_3OF3,
#         "Prelim Q1": PRELIM_Q1,
#         "Prelim Q2": PRELIM_Q2,
#         "Prelim Q3": PRELIM_Q3,
#         "Prelim Q4": PRELIM_Q4,
#         "Prelim Q5": PRELIM_Q5,
#         "Prelim Q6": PRELIM_Q6,
#         "Prelim Q7": PRELIM_Q7,
#         "Prelim Q8": PRELIM_Q8
#         })
#         df.to_csv("clean.csv")



import pandas as pd

# STEP 1: Load Excel
df = pd.read_excel("Cz̧lean-Deodorant-Raw-Data.xlsx")

# STEP 2: Remove duplicate panelists
df = df.drop_duplicates(subset=["Panelist"])

# STEP 3: Map gender
df["Gender"] = df["Gender"].map({1: "Male", 2: "Female"})
df["THREE MS"] = df["THREE MS"].map({1: "Mindset 1 of 3", 2: "Mindset 2 of 3", 3: "Mindset 3 of 3"})
df["AgeGroup"] = df["AgeGroup"].map({1: "18-17", 2: "18-24", 3: "25-34", 4: "35-44", 5: "45-54", 6: "55-64", 7: "65+"})
print(df["AgeGroup"])