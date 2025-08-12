from services.auth import AuthService
service=AuthService()
data_=service.theme_results.find_one({"project_id":"07023d8f-a1b1-4eb2-aa60-a37c62ce9798"})

data=data_["results"]
import pandas as pd
def process_agent(agent_key, output_name):
    rows = []
    item_type = agent_key.replace("Agent", "")  # e.g., 'Situation'
    item_type_2 = agent_key.replace("sAgent", "")  # e.g., 'Situation'
    content_list_key = item_type   # e.g., 'Situations'

    for category_block in data.get(agent_key, []):
        category = category_block.get("Theme", "")
        category_description = category_block.get("Description", "")

        for subtheme_block in category_block.get("Subthemes", []):
            print("in subthemes")
            theme = subtheme_block.get("Subtheme", "")
            print(theme)
            subtheme_description = subtheme_block.get("Description", "")

            items = subtheme_block.get(content_list_key, [])
            if not items:
                continue
            print(items)
            first_item = items[0]  # Only the first one

            row = {
                "Category": category,
                "Category Description": category_description,
                "Theme": theme,
                "Subtheme Description": subtheme_description,
                item_type_2: first_item.get(f"{item_type_2} Name", ""),
                f"{item_type_2} Description": first_item.get(f"{item_type_2} Description", ""),
                "Consumer Statement": first_item.get("Consumer Statement", ""),
                "Evidence Snippets": first_item.get("Evidence_Snippets", "")
            }
            print(row)
            rows.append(row)
            print(len(rows))

    df = pd.DataFrame(rows)
    df.to_csv(f"{output_name}.csv", index=False)
    print(f"✅ Exported: {output_name}.csv with {len(rows)} rows.")

# Process each agent for just the first item per subtheme
process_agent("SituationsAgent", "situations_flattened")
process_agent("MotivationsAgent", "motivations_flattened")
process_agent("OutcomesAgent", "outcomes_flattened")