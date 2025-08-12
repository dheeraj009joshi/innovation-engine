import pandas as pd
from collections import Counter
import re

def analyze_word_frequency(product_names, target_words=None):
    """Analyze word frequency in product names"""
    all_words = []
    for name in product_names:
        words = re.findall(r'\b\w+\b', name.lower())
        all_words.extend(words)
    
    if target_words is None:
        word_counts = Counter(all_words)
    else:
        target_words_lower = [w.lower() for w in target_words]
        word_counts = Counter(w for w in all_words if w in target_words_lower)
    
    freq_df = pd.DataFrame.from_dict(word_counts, orient='index', columns=['Count'])
    freq_df.index.name = 'Word'
    freq_df = freq_df.sort_values('Count', ascending=False)
    freq_df['Percentage'] = (freq_df['Count'] / len(product_names)) * 100
    return freq_df.reset_index()

def process_excel(input_file, output_file, special_sheets):
    sheets_dict = pd.read_excel(input_file, sheet_name=None)
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in sheets_dict.items():
            if df.empty or len(df.columns) == 0:
                continue
                
            col_name = df.columns[0]
            clean_df = df.dropna(subset=[col_name])
            product_names = clean_df[col_name].astype(str).tolist()
            
            # Handle special word frequency sheets
            if any(s.lower() in sheet_name.lower() for s in special_sheets):
                target_words = [s for s in sheet_name.split() if s.lower() != 'frequency']
                freq_df = analyze_word_frequency(product_names, target_words)
                freq_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                all_words_df = analyze_word_frequency(product_names)
                all_words_df.to_excel(writer, sheet_name=f"{sheet_name}_all_words", index=False)
            else:
                # FIXED: Normal frequency distribution
                try:
                    # Count occurrences of each exact value
                    freq_df = clean_df[col_name].value_counts().reset_index()
                    freq_df.columns = [col_name, 'Count']
                    total = freq_df['Count'].sum()
                    freq_df['Percentage'] = (freq_df['Count'] / total) * 100
                    
                    # Save with original sheet name
                    freq_df.to_excel(writer, sheet_name=sheet_name, index=False)
                except Exception as e:
                    print(f"Error processing sheet {sheet_name}: {str(e)}")
                    # Save original data if analysis fails
                    clean_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"✅ Analysis complete. Results saved to {output_file}")

# Example usage
input_file = "4Ps_unique_tabs.xlsx"  # Replace with your input file
output_file = "frequency_analysis_results.xlsx"
special_sheets = ["Products", "Propositions","Packaging","Ingredients"]  # Sheets that need word frequency analysis

process_excel(input_file, output_file, special_sheets)