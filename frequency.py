
from fuzzywuzzy import fuzz
import pandas as pd 
file_path="cleaned_outcomes_flattened_fuzz-threshold-0.5_similarity_threshold-0.7_final.csv"
df=pd.read_csv(file_path)


situation_col = "Theme"  # or "Situation Name"

def fuzzy_deduplication(df, columns_applied, threshold):
    df_temp = df.copy()
    for column in columns_applied:
        FUZZY_THRESHOLD = int(threshold * 100)
        if column == situation_col:
            FUZZY_THRESHOLD = 40
        
        print(f"Processing column: {column} with threshold: {FUZZY_THRESHOLD}")
        
        unique_values = df_temp[column].dropna().unique()
        canonical_titles = []
        subtheme_map = {}

        for val in unique_values:
            matched = False
            for canon in canonical_titles:
                if fuzz.token_sort_ratio(val, canon) >= FUZZY_THRESHOLD:
                    subtheme_map[val] = canon
                    matched = True
                    print(matched, val, canon)
                    break
            if not matched:
                subtheme_map[val] = val
                canonical_titles.append(val)

        df_temp[column] = df_temp[column].map(lambda x: subtheme_map.get(x, x))
        print(f"{column} - Merged: {len(subtheme_map)}, Unique: {len(df_temp[column].dropna().unique())}")
    return df_temp



# f_df=fuzzy_deduplication(df, [situation_col], 0.65)
f_df=df


# Count frequency
freq_df = f_df[situation_col].value_counts().reset_index()
freq_df.columns = [situation_col, "Frequency"]

# (Optional) Add percentage column
freq_df["Percentage"] = (freq_df["Frequency"] / freq_df["Frequency"].sum()) * 100

# Save results to CSV
# freq_df.to_csv(f"{situation_col}_frequencies.csv", index=False)
freq_df.to_csv(f"frequencies_{file_path}", index=False)

print(freq_df)