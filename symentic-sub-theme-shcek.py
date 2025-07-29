import pandas as pd
from fuzzywuzzy import fuzz
from sentence_transformers import SentenceTransformer, util

def fuzzy_deduplication(df, columns_applied, threshold):
    df_temp = df.copy()
    for column in columns_applied:
        FUZZY_THRESHOLD = int(threshold * 100)
        if column == "Category":
            FUZZY_THRESHOLD = 50
        if column == "Theme":
            FUZZY_THRESHOLD = 50
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
                    break
            if not matched:
                subtheme_map[val] = val
                canonical_titles.append(val)

        df_temp[column] = df_temp[column].map(lambda x: subtheme_map.get(x, x))
        print(f"{column} - Merged: {len(subtheme_map)}, Unique: {len(df_temp[column].dropna().unique())}")
    return df_temp

def semantic_filtering(df, column, similarity_threshold=0.85):
    print(f"\nApplying semantic filtering on column: {column} with threshold: {similarity_threshold}")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    unique_vals = df[column].dropna().unique()
    embeddings = {text: model.encode(text, convert_to_tensor=True) for text in unique_vals}

    to_remove = set()
    visited = set()

    for i, val1 in enumerate(unique_vals):
        if val1 in visited:
            continue
        for j, val2 in enumerate(unique_vals):
            if val1 != val2 and val2 not in visited:
                sim = util.pytorch_cos_sim(embeddings[val1], embeddings[val2])
                if sim.item() >= similarity_threshold:
                    to_remove.add(val2)
                    visited.add(val2)
        visited.add(val1)

    filtered_df = df[~df[column].isin(to_remove)]
    print(f"Removed {len(to_remove)} semantically similar entries in '{column}'")
    return filtered_df

def final_deduplication(df, column):
    before = len(df)
    df_final = df.drop_duplicates(subset=column, keep='first').reset_index(drop=True)
    after = len(df_final)
    print(f"\nFinal deduplication on '{column}': {before - after} rows removed (exact duplicates)")
    return df_final

# ==== CONFIGURATION ======
semantic_column = "Motivation"
input_file = "sleep_Motivations_all_themes.csv"
columns_for_fuzzy = ["Category", "Theme"]

fuzzy_thresholds = 0.5
similarity_threshold = 0.7

# ==== PIPELINE EXECUTION =====
df_original = pd.read_csv(input_file)

# Step 1: Fuzzy deduplication
df_fuzzy = fuzzy_deduplication(df_original, columns_for_fuzzy, fuzzy_thresholds)

# Step 2: Semantic similarity filtering
df_semantic = semantic_filtering(df_fuzzy, semantic_column, similarity_threshold)

# Step 3: Final deduplication
df_final = final_deduplication(df_semantic, semantic_column)

# Output
# Step 4: Reorder columns
# Step 4: Post-processing based on semantic_column
print(f"\n↪ Post-processing output columns for semantic column: '{semantic_column}'")

# # Step 4: Post-processing for all semantic columns
# print(f"\n↪ Post-processing output columns for semantic column: '{semantic_column}'")

# Step 4.1: Drop the original semantic column (if it exists)
if semantic_column in df_final.columns:
    df_final = df_final.drop(columns=[semantic_column])

# Step 4.2: Rename 'Customer Statement' to semantic_column
if 'Consumer Statement' in df_final.columns:
    df_final = df_final.rename(columns={'Consumer Statement': semantic_column})
else:
    print("⚠️ Warning: 'Customer Statement' column not found. Skipping rename.")

# Step 4.3: Prepare column order
base_order = [
    "Category",
    "Theme",
    semantic_column,
    "Category Description",
    "Theme Description",
    f"{semantic_column} Description",
    "Evidence Snippets",
    f"{semantic_column} References"
]

existing_base = [col for col in base_order if col in df_final.columns]
extra_columns = [col for col in df_final.columns if col not in existing_base]
final_columns = existing_base + extra_columns

# Step 4.4: Reorder columns
df_final = df_final[final_columns]


# Save output
output_file = f"cleaned_{input_file.replace('.csv', '')}_fuzz-threshold-{fuzzy_thresholds}_similarity_threshold-{similarity_threshold}_final.csv"
df_final.to_csv(output_file, index=False)
print(f"✅ Final cleaned file saved as: {output_file} with correct columns for '{semantic_column}'")


# output_file = f"cleaned_{input_file.replace('.csv', '')}_fuzz-threshold-{fuzzy_thresholds}_similarity_threshold-{similarity_threshold}_final.csv"
