# import json
# import os
# import threading
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from openai import OpenAI
# from queue import Queue
# from config import aii,product_count
# # Thread-safe progress updater
# class ProgressManager:
#     def __init__(self, progress_callback, total_steps):
#         self.progress = 0
#         self.lock = threading.Lock()
#         self.progress_callback = progress_callback
#         self.total_steps = total_steps
#         self.completed_steps = 0
#         self.increment_per_step = 100 / total_steps if total_steps > 0 else 0
    
#     def update(self, message):
#         with self.lock:
#             self.completed_steps += 1
#             self.progress = min(100, self.completed_steps * self.increment_per_step)
#             if self.progress_callback:
#                 self.progress_callback(int(self.progress), message)

# def chunk_insights(insights_str, chunk_size=8000):
#     """Split insights into manageable chunks"""
#     return [insights_str[i:i+chunk_size] for i in range(0, len(insights_str), chunk_size)]

# def get_existing_product_names(concepts: list) -> list:
#     return [c.get("product_name", "").strip() for c in concepts if "product_name" in c]



# def generate_chunk_products(client, chunk, chunk_num, total_chunks,all_concepts,model):
#     """Generate products from a single insight chunk with priority scores"""


#     forrbiden_names= ",".join(get_existing_product_names(all_concepts))
#     # print(forrbiden_names)
#     prompt = f"""
# Generate 1 product ideas from this insights
# Make sure the product is not same from the products listed in {all_concepts}. the all has to be mutually exclusive  
# For EACH product, provide ALL details EXACTLY as specified:

# You are a specialized AI called the Mind Genome Inventor.

# Your mission is to generate radically innovative, emotionally compelling, and technically feasible product ideas that can be built using real inputs — specifically:

#     Ingredients

#     Technologies

#     Benefits

#     Situations, Motivations, and Outcomes (SMOs)(agents output )

# You are not designing futuristic or speculative concepts.
# You are inventing real, buildable products by recombining these inputs in novel, non-obvious ways.
# Each product must feel like something ordinary people instantly understand, emotionally resonate with, and would want to buy right now — whether they’re kids, working adults, or retirees.

# Every product must feel:

#     Entirely new in formulation and combination

#     Entirely familiar in purpose and emotional appeal

#     And irresistibly desirable the moment it's seen

# You are not generating ideas out of thin air.
# Every part of the output must be directly grounded in the provided input materials.
# This is a recombination task, not open-ended ideation.

# Each product must be radically different from every other — in name, function, domain, tone, and audience.

# You are inventing a product that has no direct equivalent on the market, but is made from real components and known consumer needs.
# Each product must have a three-word name, with no shared words, subwords, or fragments across any other product in the same run (whether it’s 1 or 20).
# These products should score in the top 10% of buying interest for anyone in their category.
# They must feel like they were made for regular people with real desires, not abstract or niche audiences.

# GENERATION RULES

#     Every product must have a three-word name, and no name may reuse any word, subword, root, or recognizable fragment that appears in any other product name in the same run.

#     Before finalizing the output, you must:

#         Normalize all product names (lowercase, remove punctuation or special characters)

#         Split names on spaces, hyphens, underscores, and other separators

#         Extract all substrings of 3 or more characters

#         Compare these substrings across all names

#     If any overlap is found — whether full words or embedded fragments — you must regenerate the affected name(s) using entirely new, unused components.

#     No repetition is allowed, even if the reused fragment is part of a compound, acronym, or different domain.

#     Products must be radically different in name, category, function, vibe, and emotional appeal.

#     Products must be technically feasible using the available input components (ingredients, technologies, benefits).

#     Each product must pass a realism check: Before generating, ask: Could this be realistically built from the given inputs? If not, discard and regenerate.

#     Every part of the product — its name, pitch, function, emotional appeal, and slogans — must be directly grounded in and traceable to the input material.

#     Products must be designed for immediate emotional clarity and cultural relevance, not intellectual novelty.

#     All consumer testimonials must reflect genuine, persona-specific excitement, from ten distinct mindsets (age, values, lifestyle, etc.).

#     Avoid generic ideas, safe concepts, or trend-chasing terms.
#     These products must be instantly desirable, deeply resonant, and visibly like nothing else.


# 1. **Product Name**: Creative and memorable name
# 2. **Technical Explanation**: How it works technically
# 3. **Consumer Pitch**: Why consumers would want it
# 4. **Competitor Reaction**: What competitors would say
# 5. **5-Year Projection**: Market performance by 2030
# 6. **Consumer Discussion**: Town hall meeting discussion (positives/negatives)
# 7. **Presentation**: EXACTLY 15 sentences for a professional presentation
# 8. **Consumer Q&A**: EXACTLY 4 questions with EXACTLY 4 answers each (12-16 words per answer)
# 9. **Investor Evaluation**: Investor perspective with pushback/responses
# 10. **Advertisor Slogans**: 4 Advertising slogans. For each: 
#     - Slogan text
#     - 1 paragraph (EXACTLY 4 sentences) describing customer mindset
# 11. **AI Report card**: 0-100 scores for:
#     A) Originality 
#     B) Usefulness
#     C) Social media talk likelihood
#     D) Memorability
#     E) Friend talk likelihood
#     F) Purchase ease
#     G) Excitement generation
#     H) Boredom likelihood after 6 months

# Requirements:
# - Products MUST be distinct from each other
# - Use ONLY insights from the provided chunk
# - People MUST love these products
# - Output PURE JSON ONLY

# Product must follow the structure below. Output  JSON objects, and return ONLY the JSON — no commentary or text.


#   {{
#     "product_name": "Product Name 1",
#     "technical_explanation": "How it works technically...",
#     "consumer_pitch": "Why people want it...",
#     "competitor_reaction": "What competitors would say...",
#     "five_year_projection": "Expected performance by 2030...",
#     "consumer_discussion": "Public conversation about the product...",
#     "presentation": [
#       "Sentence 1", "Sentence 2", ..., "Sentence 15"
#     ],
#     "priority": 0-100(based on all the factory how much is the possibility of that product to get viral and all ),
#     "consumer_qa": [
#       {{
#         "question": "Question 1?",
#         "answers": ["Answer A", "Answer B", "Answer C", "Answer D"]
#       }},
#       ...
#       (EXACTLY 4 questions)
#     ],
#     "investor_evaluation": "Investor commentary with pushback and counterarguments.",
#     "advertisor_slogans": [
#       {{
#         "slogan": "Catchy phrase here",
#         "mindset_description": "Paragraph (exactly 4 sentences) describing the target mindset"
#       }},
#       ...
#       (EXACTLY 4 slogans)
#     ],
#     "ai_report_card": {{
#       "originality": 0-100,
#       "usefulness": 0-100,
#       "social_media_talk": 0-100,
#       "memorability": 0-100,
#       "friend_talk": 0-100,
#       "purchase_ease": 0-100,
#       "excitement": 0-100,
#       "boredom_likelihood": 0-100
#     }}
#   }}
  

# Do not include any headings, labels, commentary, or formatting.
# Return only valid JSON — nothing else.

#  Insights:
# {chunk}

# """
#     response = client.chat.completions.create(
#         model=model,
#         messages=[
#             {"role": "system", "content": "You are a product strategist"},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.7,
#         max_tokens=10000,
#         response_format={"type": "json_object"}
#     )
#     # print("partial products", response.choices[0].message.content)
#     return response.choices[0].message.content
# # def clean_created_at(data):
# #     agent_data = data.get("ProductGenerationAgent", {})

# #     # Clean 'generations' list
# #     if "generations" in agent_data:
# #         for gen in agent_data["generations"]:
# #             gen.pop("created_at", None)
# #             gen.pop("createdAt", None)  # handle camelCase if needed

# #     # Clean 'latest' dict
# #     if "latest" in agent_data:
# #         agent_data["latest"].pop("created_at", None)
# #         agent_data["latest"].pop("createdAt", None)

# #     return data

def flatten_agent_outputs(agent_outputs):
    output_lines = []

    for agent_name, results in agent_outputs.items():
        print(agent_name)

        output_lines.append(f"=== Agent: {agent_name} ===")
        
        if isinstance(results, list):
            for i, item in enumerate(results):
                output_lines.append(f"-- Item {i+1} --")
                for key, value in item.items():
                    output_lines.append(f"{key}: {value}")
        elif isinstance(results, dict):
            for key, value in results.items():
                output_lines.append(f"{key}: {value}")
        else:
            output_lines.append(str(results))

        output_lines.append("")  # separator between agents

    return "\n".join(output_lines)



# # # def run(all_agent_outputs, progress_callback=None):
# #     client = OpenAI(api_key=aii)
# #     insights_str = flatten_agent_outputs(clean_created_at(all_agent_outputs))
# #     chunks = chunk_insights(insights_str)
# #     num_chunks = len(chunks)
# #     total_steps = 4 + num_chunks
# #     progress_mgr = ProgressManager(progress_callback, total_steps)

# #     progress_mgr.update("🚀 Starting product generation engine...")
# #     progress_mgr.update("🔍 Preparing market insights...")
# #     progress_mgr.update(f"⚙️ Processing {num_chunks} insight chunks...")

# #     all_concepts = []
# #     existing_names = set()

# #     with ThreadPoolExecutor(max_workers=5) as executor:
# #         futures = {}
# #         for i, chunk in enumerate(chunks):
# #             future = executor.submit(generate_chunk_products, client, chunk, i+1, num_chunks,all_concepts)
# #             futures[future] = i

# #         for future in as_completed(futures):
# #             chunk_num = futures[future]
# #             try:
# #                 concepts = future.result()
# #                 concept_data = json.loads(concepts)

# #                 if 'priority' not in concept_data:
# #                     concept_data['priority'] = 75

# #                 name = concept_data.get('product_name', '').strip()
# #                 if name and name not in existing_names:
# #                     existing_names.add(name)
# #                     all_concepts.append(concept_data)

# #                 progress_mgr.update(f"✅ Generated: {name or 'Unknown Product'}")
# #             except Exception as e:
# #                 progress_mgr.update(f"⚠️ Error processing chunk: {str(e)}")

# #     progress_mgr.update("📊 Evaluating concept potential...")

# #     try:
# #         sorted_concepts = sorted(all_concepts, key=lambda x: x.get('priority', 0), reverse=True)[:5]
# #         names = [c['product_name'] for c in sorted_concepts]
# #         progress_mgr.update(f"🏆 Top concepts: {', '.join(names)}")
# #         return sorted_concepts
# #     except Exception as e:
# #         progress_mgr.update(f"❌ Prioritization failed: {str(e)}")
# #         return all_concepts[:5]
    



# # from concurrent.futures import ThreadPoolExecutor, as_completed
# # import json
# # from openai import OpenAI

# def run(all_agent_outputs, progress_callback=None):
#     client = OpenAI(api_key=aii)  # Make sure `aii` is defined somewhere
#     insights_str = flatten_agent_outputs(all_agent_outputs)
#     # print(insights_str)
#     progress_mgr = ProgressManager(progress_callback, total_steps=5)
#     progress_mgr.update("🚀 Starting product generation engine...")
#     progress_mgr.update("🔍 Preparing market insights...")
#     progress_mgr.update("⚙️ Sending insights to GPT-4.1 Nano...")

#     all_concepts = []
#     existing_names = set()

#     try:

#         for i in range(product_count):
#         # Call GPT-4.1 Nano with the full input
#             concepts = generate_chunk_products(
#                 client=client,
#                 chunk=insights_str,  # Now the full insights string
#                 chunk_num=1,
#                 total_chunks=1,
#                 all_concepts=all_concepts,
#                 model="gpt-4.1-nano"  # or use correct model version per your setup
#             )
#             concept_data = json.loads(concepts)
#             print(concept_data)
#             if isinstance(concept_data, dict):
#                 concept_data = [concept_data]

#             for data in concept_data:
#                 if 'priority' not in data:
#                     data['priority'] = 75

#                 name = data.get('product_name', '').strip()
#                 if name and name not in existing_names:
#                     existing_names.add(name)
#                     all_concepts.append(data)

#                 progress_mgr.update(f"✅ Generated: {name or 'Unknown Product'}")

#     except Exception as e:
#         progress_mgr.update(f"⚠️ Error processing insights: {str(e)}")

#     progress_mgr.update("📊 Evaluating concept potential...")

#     try:
#         sorted_concepts = sorted(all_concepts, key=lambda x: x.get('priority', 0), reverse=True)[:5]
#         names = [c['product_name'] for c in sorted_concepts]
#         progress_mgr.update(f"🏆 Top concepts: {', '.join(names)}")
#         return sorted_concepts
#     except Exception as e:
#         progress_mgr.update(f"❌ Prioritization failed: {str(e)}")
#         return all_concepts

import json
from openai import OpenAI
from config import aii

# def generate_single_product(client, insights_str, existing_products, model="gpt-4.1-nano"):
#     """Generate a single product that's unique from existing ones"""
#     # Create list of forbidden names/words
#     forbidden_names = [p['product_name'] for p in existing_products]
#     forbidden_words = []
#     for name in forbidden_names:
#         forbidden_words.extend(name.lower().split())
    
#     prompt = f"""
# You are the Mind Genome Inventor AI. Generate ONE unique product idea that:
# 1. Has a completely unique name (3 words, no shared words/substrings with existing products)
# 2. Is technically feasible and emotionally compelling
# 3. Is distinct from these existing products: {', '.join(forbidden_names)}

# EXISTING PRODUCT WORDS TO AVOID: {', '.join(forbidden_words)}

# Output must contain ALL these elements in EXACT JSON format:
# {{
#   "product_name": "Three Unique Words",
#   "technical_explanation": "How it works...",
#   "consumer_pitch": "Why people want it...",
#   "competitor_reaction": "What competitors would say...",
#   "five_year_projection": "Market outlook...",
#   "consumer_discussion": "Public conversation...",
#   "presentation": ["Sentence 1", "Sentence 2", ..., "Sentence 15"],
#   "priority": 0-100,
#   "consumer_qa": [
#     {{
#       "question": "Question 1?",
#       "answers": ["Answer 1", "Answer 2", "Answer 3", "Answer 4"]
#     }},
#     {{"question": "Question 2?", "answers": [...]}},
#     {{"question": "Question 3?", "answers": [...]}},
#     {{"question": "Question 4?", "answers": [...]}}
#   ],
#   "investor_evaluation": "Investor analysis...",
#   "advertisor_slogans": [
#     {{
#       "slogan": "Catchy phrase",
#       "mindset_description": "4 sentence paragraph"
#     }},
#     ...  # 3 more
#   ],
#   "ai_report_card": {{
#     "originality": 0-100,
#     "usefulness": 0-100,
#     "social_media_talk": 0-100,
#     "memorability": 0-100,
#     "friend_talk": 0-100,
#     "purchase_ease": 0-100,
#     "excitement": 0-100,
#     "boredom_likelihood": 0-100
#   }}
# }}

# VALIDATION REQUIRED:
# 1. Check name against forbidden words: {forbidden_words}
# 2. Ensure no shared words/substrings (3+ characters)
# 3. Verify all fields are present
# 4. Confirm technical feasibility

# Return ONLY valid JSON with no commentary.
# """
#     response = client.chat.completions.create(
#         model=model,
#         messages=[
#             {"role": "system", "content": "You create unique product concepts"},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.75,  # Slightly higher for diversity
#         max_tokens=2500,
#         response_format={"type": "json_object"}
#     )
    
#     try:
#         return json.loads(response.choices[0].message.content)
#     except:
#         return None

# def validate_product(new_product, existing_products):
#     """Ensure product is unique and complete"""
#     if not new_product:
#         return False
    
#     # Check required keys
#     required_keys = [
#         "product_name", "technical_explanation", "consumer_pitch",
#         "competitor_reaction", "five_year_projection", "consumer_discussion",
#         "presentation", "priority", "consumer_qa", "investor_evaluation",
#         "advertisor_slogans", "ai_report_card"
#     ]
#     if not all(key in new_product for key in required_keys):
#         return False
    
#     # Check name uniqueness
#     new_name = new_product["product_name"].lower()
#     existing_names = [p["product_name"].lower() for p in existing_products]
    
#     if new_name in existing_names:
#         return False
    
#     # Check word uniqueness
#     new_words = set(new_name.split())
#     for existing in existing_products:
#         existing_words = set(existing["product_name"].lower().split())
#         if new_words & existing_words:  # Any shared words
#             return False
    
#     return True

# def run(all_agent_outputs, progress_callback=None):
#     client = OpenAI(api_key=aii)
#     insights_str = flatten_agent_outputs(all_agent_outputs)
#     products = []
    
#     # Progress setup
#     total_products = 3
#     progress = 0
#     progress_step = 100 / (total_products * 1.5)  # Account for potential retries
    
#     def update_progress(message):
#         nonlocal progress
#         progress = min(100, progress + progress_step)
#         if progress_callback:
#             progress_callback(int(progress), message)
    
#     update_progress("🚀 Starting product generation...")
    
#     # Generate 3 unique products
#     for i in range(total_products):
#         update_progress(f"⚙️ Generating product {i+1}/3...")
#         attempts = 0
        
#         while attempts < 3:  # Max 3 attempts per product
#             new_product = generate_single_product(
#                 client, 
#                 insights_str, 
#                 products,
#                 model="gpt-4.1-nano"
#             )
            
#             if validate_product(new_product, products):
#                 products.append(new_product)
#                 update_progress(f"✅ Generated: {new_product['product_name']}")
#                 break
                
#             attempts += 1
#             update_progress(f"🔄 Retrying product {i+1} (attempt {attempts})...")
        
#         if attempts >= 3:
#             update_progress(f"⚠️ Failed to generate unique product {i+1}")
    
#     # Final sorting and progress
#     products = sorted(products, key=lambda x: x.get("priority", 0), reverse=True)
#     update_progress(f"🏆 Generated {len(products)} unique products!")
    
#     return products






import json
import time
import threading
from openai import OpenAI
from config import aii
import streamlit as st

class ProgressManager:
    def __init__(self, progress_callback, total_products=3):
        self.progress = 0
        self.lock = threading.Lock()
        self.progress_callback = progress_callback
        self.total_products = total_products
        self.completed_products = 0
        self.last_update_time = time.time()
        self.active = True
        self.status_message = "Starting..."
        
        # Start background updater thread
        self.updater_thread = threading.Thread(target=self.update_thread, daemon=True)
        self.updater_thread.start()
    
    def update_thread(self):
        """Background thread to send progress updates every 2 seconds"""
        while self.active:
            with self.lock:
                current_progress = self.progress
                message = self.status_message
            if self.progress_callback:
                self.progress_callback(int(current_progress), message)
            time.sleep(2)
    
    def update(self, progress_delta, message):
        """Update progress with new information"""
        with self.lock:
            self.progress = min(100, self.progress + progress_delta)
            self.status_message = message
            self.last_update_time = time.time()
    
    def complete_product(self, product_name):
        """Mark a product as completed"""
        with self.lock:
            self.completed_products += 1
            progress_per_product = 100 / self.total_products
            self.progress = min(100, self.completed_products * progress_per_product)
            self.status_message = f"✅ Generated: {product_name}"
    
    def close(self):
        """Clean up resources"""
        self.active = False
        if self.progress_callback:
            self.progress_callback(100, self.status_message)

def generate_single_product(client, insights_str, existing_products, project_description,model="gpt-4.1-nano"):
    """Generate a single product that's unique from existing ones"""
   #     # Create list of forbidden names/words
    forbidden_names = [p['product_name'] for p in existing_products]
    forbidden_words = []
    for name in forbidden_names:
        forbidden_words.extend(name.lower().split())
    
    prompt = f"""
Background :{project_description}


You are the Mind Genome Inventor AI. Generate ONE unique product idea that:
1. Has a completely unique name (3 words, no shared words/substrings with existing products)
2. Is technically feasible and emotionally compelling
3. Is distinct from these existing products: {', '.join(forbidden_names)}

EXISTING PRODUCT WORDS TO AVOID: {', '.join(forbidden_words)}

Output must contain ALL these elements in EXACT JSON format:
{{
  "product_name": "Three Unique Words",
  "technical_explanation": "How it works...",
  "consumer_pitch": "Why people want it...",
  "competitor_reaction": "What competitors would say...",
  "five_year_projection": "Market outlook...",
  "consumer_discussion": "Public conversation...",
  "presentation": ["Sentence 1", "Sentence 2", ..., "Sentence 15"],
  "priority": 0-100,
  "consumer_qa": [
    {{
      "question": "Question 1?",
      "answers": ["Answer 1", "Answer 2", "Answer 3", "Answer 4"]
    }},
    {{"question": "Question 2?", "answers": [...]}},
    {{"question": "Question 3?", "answers": [...]}},
    {{"question": "Question 4?", "answers": [...]}}
  ],
  "investor_evaluation": "Investor analysis...",
  "advertisor_slogans": [
    {{
      "slogan": "Catchy phrase",
      "mindset_description": "4 sentence paragraph"
    }},
    ...  # 3 more
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
}}

VALIDATION REQUIRED:
1. Check name against forbidden words: {forbidden_words}
2. Ensure no shared words/substrings (3+ characters)
3. Verify all fields are present
4. Confirm technical feasibility

Return ONLY valid JSON with no commentary.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Create unique product concepts"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.75,
        max_tokens=1800,
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except:
        return None

def validate_product(new_product, existing_products):
    """Ensure product is unique and complete"""
    if not new_product:
        return False
    
    # Essential keys only for faster validation
    required_keys = [
        "product_name", "technical_explanation", "consumer_pitch",
        "priority", "ai_report_card"
    ]
    if not all(key in new_product for key in required_keys):
        return False
    
    # Check name uniqueness
    new_name = new_product["product_name"].lower()
    existing_names = [p["product_name"].lower() for p in existing_products]
    
    if new_name in existing_names:
        return False
    
    # Check word uniqueness
    new_words = set(new_name.split())
    for existing in existing_products:
        existing_words = set(existing["product_name"].lower().split())
        if new_words & existing_words:
            return False
    
    return True
 
def run(all_agent_outputs,project_description,progress_callback=None):
    client = OpenAI(api_key=aii)
    insights_str = flatten_agent_outputs(all_agent_outputs)
    products = []
    total_products = 3
    
    # Progress tracking without threads
    start_time = time.time()
    last_update_time = time.time()
    progress = 0
    
    def update_progress(new_progress, message):
        nonlocal progress
        progress = new_progress
        if progress_callback:
            progress_callback(int(progress), message)
    
    update_progress(0, "🚀 Starting product generation...")
    
    # Generate products with main-thread updates
    for i in range(total_products):
        # Update progress at least every 2 seconds
        if time.time() - last_update_time > 2:
            update_progress(
                min(90, int(i * 100 / total_products)),
                f"⚙️ Working on product {i+1}/3..."
            )
            last_update_time = time.time()
        
        attempt = 1
        product_generated = False
        
        while not product_generated and attempt <= 3:
            # Send update if it's been more than 2 seconds
            if time.time() - last_update_time > 2:
                update_progress(
                    min(90, int((i * 100 + (attempt-1) * 10) / total_products)),
                    f"🔧 Attempt {attempt} for product {i+1}..."
                )
                last_update_time = time.time()
            
            # Generate product
            new_product = generate_single_product(
                client, 
                insights_str, 
                products,
                project_description,
                model="gpt-4.1-nano"
                
            )
            
            # Validate
            if new_product and validate_product(new_product, products):
                products.append(new_product)
                update_progress(
                    min(90, int((i+1) * 100 / total_products)),
                    f"✅ Generated: {new_product['product_name']}"
                )
                last_update_time = time.time()
                product_generated = True
            else:
                attempt += 1
        
        if not product_generated:
            update_progress(
                min(90, int((i+1) * 100 / total_products)),
                f"⚠️ Couldn't generate product {i+1}"
            )
            last_update_time = time.time()
    
    # Final processing
    products = sorted(products, key=lambda x: x.get("priority", 0), reverse=True)
    total_time = time.time() - start_time
    
    if products:
        names = [p["product_name"] for p in products]
        update_progress(100, f"🏆 Generated in {total_time:.1f}s: {', '.join(names)}")
    else:
        update_progress(100, f"❌ No products generated in {total_time:.1f}s")
    
    return products