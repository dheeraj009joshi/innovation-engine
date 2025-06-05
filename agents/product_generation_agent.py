import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from queue import Queue
from config import aii
# Thread-safe progress updater
class ProgressManager:
    def __init__(self, progress_callback, total_steps):
        self.progress = 0
        self.lock = threading.Lock()
        self.progress_callback = progress_callback
        self.total_steps = total_steps
        self.completed_steps = 0
        self.increment_per_step = 100 / total_steps if total_steps > 0 else 0
    
    def update(self, message):
        with self.lock:
            self.completed_steps += 1
            self.progress = min(100, self.completed_steps * self.increment_per_step)
            if self.progress_callback:
                self.progress_callback(int(self.progress), message)

def chunk_insights(insights_str, chunk_size=8000):
    """Split insights into manageable chunks"""
    return [insights_str[i:i+chunk_size] for i in range(0, len(insights_str), chunk_size)]

def generate_chunk_products(client, chunk, chunk_num, total_chunks):
    """Generate products from a single insight chunk with priority scores"""
    prompt = f"""
Generate 1 product idea from this market insights chunk ({chunk_num}/{total_chunks}).
For EACH product, provide ALL details EXACTLY as specified:


For EACH of the 1 product idea, provide ALL of the following:

1. **Product Name**: Creative and memorable name
2. **Technical Explanation**: How it works technically
3. **Consumer Pitch**: Why consumers would want it
4. **Competitor Reaction**: What competitors would say
5. **5-Year Projection**: Market performance by 2030
6. **Consumer Discussion**: Town hall meeting discussion (positives/negatives)
7. **Presentation**: EXACTLY 15 sentences for a professional presentation
8. **Consumer Q&A**: EXACTLY 4 questions with EXACTLY 4 answers each (12-16 words per answer)
9. **Investor Evaluation**: Investor perspective with pushback/responses
10. **Advertisor Slogans**: 4 Advertising slogans. For each: 
    - Slogan text
    - 1 paragraph (EXACTLY 4 sentences) describing customer mindset
11. **AI Report card**: 0-100 scores for:
    A) Originality 
    B) Usefulness
    C) Social media talk likelihood
    D) Memorability
    E) Friend talk likelihood
    F) Purchase ease
    G) Excitement generation
    H) Boredom likelihood after 6 months

Requirements:
- Products MUST be distinct from each other
- Use ONLY insights from the provided chunk
- People MUST love these products
- Output PURE JSON ONLY



Output ONLY JSON with this structure:

  {{
    "product_name": "Name",
    "technical_explanation": "Text",
    "consumer_pitch": "Text",
    "competitor_reaction": "Text",
    "five_year_projection": "Text",
    "consumer_discussion": "Text",
    "presentation": ["Sentence 1", ... (EXACTLY 15)],
    "priority":0-100(based on all the factory how much is the possibility of that product to get viral amony all ),
    "consumer_qa": [
      {{"question": "Q1", "answers": ["A1", "A2", "A3", "A4"]}},
      ... (EXACTLY 4 QAs)
    ],
    "investor_evaluation": "Text",
    "advertisor_slogans": [
      {{
        "slogan": "Text",
        "mindset_description": "4-sentence paragraph"
      }},
      ... (EXACTLY 4)
    ],
    "ai_report_card": {{
      "originality": 0-100,
      "usefulness": 0-100,
      "social_media_talk": 0-100,
      "memorability": 0-100,
      "friend_talk": 0-100,
      "purchase_ease": 0-100,
      "excitement": 0-100,
      "boredom_likelihood": 0-100
    }}
  }},
 


make sure you follow this structure  and do not miss any keys and always complete the json structure 
Chunk Insights:
{chunk}

"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a product strategist"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=3000,
        response_format={"type": "json_object"}
    )
    # print("partial products", response.choices[0].message.content)
    return response.choices[0].message.content
def clean_created_at(data):
    agent_data = data.get("ProductGenerationAgent", {})

    # Clean 'generations' list
    if "generations" in agent_data:
        for gen in agent_data["generations"]:
            gen.pop("created_at", None)
            gen.pop("createdAt", None)  # handle camelCase if needed

    # Clean 'latest' dict
    if "latest" in agent_data:
        agent_data["latest"].pop("created_at", None)
        agent_data["latest"].pop("createdAt", None)

    return data
def run(all_agent_outputs, progress_callback=None):
    client = OpenAI(api_key=aii)
    
    # Convert insights to string
    print(all_agent_outputs)
    insights_str = json.dumps(clean_created_at(all_agent_outputs), indent=2)
    
    print("passed the jsin dumps ")

    # Split insights into chunks
    chunks = chunk_insights(insights_str)
    num_chunks = len(chunks)
    
    # Calculate total steps for progress tracking:
    total_steps = 4 + num_chunks  # 1. Start, 2. Prep, 3. Processing, 4. Eval, 5. Final
    progress_mgr = ProgressManager(progress_callback, total_steps)
    
    # Step 1: Initialization
    progress_mgr.update("🚀 Starting product generation engine...")
    
    # Step 2: Preparing insights
    progress_mgr.update("🔍 Preparing market insights...")
    
    # Step 3: Process chunks
    progress_mgr.update(f"⚙️ Processing {num_chunks} insight chunks...")
    
    all_concepts = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for i, chunk in enumerate(chunks):
            future = executor.submit(
                generate_chunk_products, 
                client, chunk, i+1, num_chunks
            )
            futures[future] = i
        
        for future in as_completed(futures):
            chunk_num = futures[future]
            try:
                concepts = future.result()
                concept_data = json.loads(concepts)
                
                # Validate priority exists
                if 'priority' not in concept_data:
                    concept_data['priority'] = 75  # Default priority
                    
                all_concepts.append(concept_data)
                progress_mgr.update(
                    f"✅ Generated: {concept_data.get('product_name', 'Unknown Product')}"
                )
            except Exception as e:
                progress_mgr.update(
                    f"⚠️ Error processing chunk: {str(e)}"
                )
    
    # Step 4: Concept evaluation
    progress_mgr.update("📊 Evaluating concept potential...")
    
    # Step 5: Final prioritization
    try:
        sorted_concepts = sorted(
            all_concepts,
            key=lambda x: x.get('priority', 0),
            reverse=True
        )[:5]
        
        concept_names = [c['product_name'] for c in sorted_concepts]
        progress_mgr.update(
            f"🏆 Top concepts: {', '.join(concept_names)}"
        )
        
        return sorted_concepts
    except Exception as e:
        progress_mgr.update(f"❌ Prioritization failed: {str(e)}")
        # Fallback: return all concepts if sorting fails
        return all_concepts[:5]