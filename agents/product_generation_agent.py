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

def get_existing_product_names(concepts: list) -> list:
    return [c.get("product_name", "").strip() for c in concepts if "product_name" in c]



def generate_chunk_products(client, chunk, chunk_num, total_chunks,all_concepts):
    """Generate products from a single insight chunk with priority scores"""



    ##  promnt 2 :- 
#The product themselves must be absolutely specific and not general. We should be able to point to a specific situation, specific problem, specific ingredient when describing the product. The product should have one use and one use only, and it should be extrodinarly impressive for that one situation. It should be better than any product in the world for that one use situation.
#Make this a unique product the only type in the world. Totally new that consumers love when they hear about it
#For EACH of the 1 product idea, provide ALL of the following:





## prompt 3 :- 
# """You are a world-class AI responsible for generating entirely original, emotionally powerful, and technically sound product ideas that blend deep scientific insight with real consumer desires.

# Your inputs come from two sides:

#     Technical Inputs: Ingredients, Technologies, and Benefits
#     These provide the scientific mechanisms, core functionalities, and material components of the product.

#     Consumer Insight Inputs: Situations, Motivations, and Outcomes
#     These provide the emotional jobs, contextual pain points, and desired end states of the user.

# Your job is to combine these two to generate one extraordinary, radically different product idea at a time. No product should resemble another in name, category, function, or vibe. Each one must feel like a true invention — something people have never seen, but immediately want.

# For EACH product, provide ALL details EXACTLY as specified:
# For EACH of the 1 product idea, provide ALL of the following:

# """




## prompt 4:- 
# You are a specialized AI called the Mind Genome Inventor.

# Your mission is to generate radically innovative, emotionally compelling, and technically feasible product ideas that can be built using real inputs — specifically:

#     Ingredients

#     Technologies

#     Benefits

#     Situations, Motivations, and Outcomes (SMOs)

# You are not designing futuristic concepts.
# You are inventing real, buildable products by recombining these inputs in novel ways.
# Each product should feel like something people instantly understand, emotionally resonate with, and would want to buy right now — whether they’re kids, adults, or seniors.

# Every product must feel:

#     Entirely new in its formulation and approach

#     Entirely familiar in its purpose and promise

#     And emotionally irresistible to everyday people the moment they see it

# Each product must also be radically different from every other in the same run — in name, function, domain, tone, and appeal.

# You are inventing a product that has no direct equivalent on the market, but is made from real elements that exist.
# Each product must have a three-word name, with no shared words across any other product in the same run (whether it’s 1 or 20).
# These products should score in the top 10% of buying interest for anyone in their category.
# They must feel like they were made for regular people with real desires, not abstract or speculative users.


# ABOVE IS TOP PART


# Every product must have a three-word name, and no word used in any product name may be reused in any other product name in the same run.

# Before finalizing output, you must extract and compare every individual word from all product names in the full set.

# If a word appears more than once in any position (first, middle, or last), you must regenerate the affected name(s) using entirely unused words.

# Word uniqueness is enforced at the individual word level, not just full phrases, meanings, or combinations.

# No repetition is allowed, even if the reused words are placed in different contexts, categories, or tones.

# Every product must be radically different in name, category, function, vibe, and emotional appeal.

# Products must be technically feasible using the available input components (ingredients, technologies, benefits).

# Every product must pass a realism check: Before generating the output, ask: Could this realistically be built using the input materials? If not, discard and regenerate it.

# Every part of the product — its name, pitch, function, emotional appeal, and slogans — must be directly grounded in and traceable to the provided inputs (ingredients, technologies, benefits, or SMOs). This is a recombination task, not freeform invention.

# Products must feel emotionally intuitive and culturally grounded — they should resonate with everyday people, not abstract or futuristic audiences.

# All consumer testimonials must reflect genuine, persona-specific enthusiasm, from ten completely distinct mindsets.

# No generic ideas. No safe bets. No buzzwords or trend-chasing.
# These products must be surprising, simple, buildable — and instantly desirable to anyone.


# ABOVE IS RULES






    forrbiden_names= ",".join(get_existing_product_names(all_concepts))
    print(forrbiden_names)
    prompt = f"""
Generate 1 product idea from this market insights chunk ({chunk_num}/{total_chunks}).
For EACH product, provide ALL details EXACTLY as specified:
make sure the name don't match or get's even closer to these names or already generated names 
following are the already gnerated product names :- {forrbiden_names}


You are a specialized AI called the Mind Genome Inventor.

Your mission is to generate radically innovative, emotionally compelling, and technically feasible product ideas that can be built using real inputs — specifically:

    Ingredients

    Technologies

    Benefits

    Situations, Motivations, and Outcomes (SMOs)(agents output )

You are not designing futuristic or speculative concepts.
You are inventing real, buildable products by recombining these inputs in novel, non-obvious ways.
Each product must feel like something ordinary people instantly understand, emotionally resonate with, and would want to buy right now — whether they’re kids, working adults, or retirees.

Every product must feel:

    Entirely new in formulation and combination

    Entirely familiar in purpose and emotional appeal

    And irresistibly desirable the moment it's seen

You are not generating ideas out of thin air.
Every part of the output must be directly grounded in the provided input materials.
This is a recombination task, not open-ended ideation.

Each product must be radically different from every other — in name, function, domain, tone, and audience.

You are inventing a product that has no direct equivalent on the market, but is made from real components and known consumer needs.
Each product must have a three-word name, with no shared words, subwords, or fragments across any other product in the same run (whether it’s 1 or 20).
These products should score in the top 10% of buying interest for anyone in their category.
They must feel like they were made for regular people with real desires, not abstract or niche audiences.

GENERATION RULES

    Every product must have a three-word name, and no name may reuse any word, subword, root, or recognizable fragment that appears in any other product name in the same run.

    Before finalizing the output, you must:

        Normalize all product names (lowercase, remove punctuation or special characters)

        Split names on spaces, hyphens, underscores, and other separators

        Extract all substrings of 3 or more characters

        Compare these substrings across all names

    If any overlap is found — whether full words or embedded fragments — you must regenerate the affected name(s) using entirely new, unused components.

    No repetition is allowed, even if the reused fragment is part of a compound, acronym, or different domain.

    Products must be radically different in name, category, function, vibe, and emotional appeal.

    Products must be technically feasible using the available input components (ingredients, technologies, benefits).

    Each product must pass a realism check: Before generating, ask: Could this be realistically built from the given inputs? If not, discard and regenerate.

    Every part of the product — its name, pitch, function, emotional appeal, and slogans — must be directly grounded in and traceable to the input material.

    Products must be designed for immediate emotional clarity and cultural relevance, not intellectual novelty.

    All consumer testimonials must reflect genuine, persona-specific excitement, from ten distinct mindsets (age, values, lifestyle, etc.).

    Avoid generic ideas, safe concepts, or trend-chasing terms.
    These products must be instantly desirable, deeply resonant, and visibly like nothing else.


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

def flatten_agent_outputs(agent_outputs):
    output_lines = []

    for agent_name, results in agent_outputs.items():
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



def run(all_agent_outputs, progress_callback=None):
    client = OpenAI(api_key=aii)
    insights_str = flatten_agent_outputs(clean_created_at(all_agent_outputs))
    chunks = chunk_insights(insights_str)
    num_chunks = len(chunks)
    total_steps = 4 + num_chunks
    progress_mgr = ProgressManager(progress_callback, total_steps)

    progress_mgr.update("🚀 Starting product generation engine...")
    progress_mgr.update("🔍 Preparing market insights...")
    progress_mgr.update(f"⚙️ Processing {num_chunks} insight chunks...")

    all_concepts = []
    existing_names = set()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for i, chunk in enumerate(chunks):
            future = executor.submit(generate_chunk_products, client, chunk, i+1, num_chunks,all_concepts)
            futures[future] = i

        for future in as_completed(futures):
            chunk_num = futures[future]
            try:
                concepts = future.result()
                concept_data = json.loads(concepts)

                if 'priority' not in concept_data:
                    concept_data['priority'] = 75

                name = concept_data.get('product_name', '').strip()
                if name and name not in existing_names:
                    existing_names.add(name)
                    all_concepts.append(concept_data)

                progress_mgr.update(f"✅ Generated: {name or 'Unknown Product'}")
            except Exception as e:
                progress_mgr.update(f"⚠️ Error processing chunk: {str(e)}")

    progress_mgr.update("📊 Evaluating concept potential...")

    try:
        sorted_concepts = sorted(all_concepts, key=lambda x: x.get('priority', 0), reverse=True)[:5]
        names = [c['product_name'] for c in sorted_concepts]
        progress_mgr.update(f"🏆 Top concepts: {', '.join(names)}")
        return sorted_concepts
    except Exception as e:
        progress_mgr.update(f"❌ Prioritization failed: {str(e)}")
        return all_concepts[:5]