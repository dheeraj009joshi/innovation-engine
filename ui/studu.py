import streamlit as st
import json
import uuid
from datetime import datetime

class StudyGenerationProcess:
    def __init__(self, auth,currentProduct):
        self.auth = auth
        self.currentProduct=currentProduct   
        
    def run(self):
        """Main entry point for study generation flow"""
        if "study_step" not in st.session_state:
            st.session_state.study_step = 1
            st.session_state.study_data = {
                "study_name": "",
                "study_description": "",
                "questions": [],
                "prelim_questions": []
            }
        
        # Get current product data
        product_data = self.currentProduct
        
        st.subheader(f"📝 Study Generation (Step {st.session_state.study_step}/4)")
        
        if st.session_state.study_step == 1:
            self._step1_setup(product_data)
        elif st.session_state.study_step == 2:
            self._step2_questions(product_data)
        elif st.session_state.study_step == 3:
            self._step3_prelim_questions()
        elif st.session_state.study_step == 4:
            self._step4_review()
    
    def _get_current_product(self):
        """Retrieve current product from session state"""
        if "ProductGenerationAgent" in st.session_state.agent_outputs:
            current_gen = st.session_state.agent_outputs["ProductGenerationAgent"]["current_generation"]
            if current_gen and current_gen["ideas"]:
                return current_gen["ideas"][0]  # Use first product
        return None
    
    def _step1_setup(self, product):
        """Step 1: Study name and description"""
        study_data = st.session_state.study_data
        print(study_data)
        # Auto-fill product name if available
        default_name = product["product_name"] if product else ""
        study_name = st.text_input("Study Name", value=default_name or study_data["study_name"])
        
        col1, col2 = st.columns([3, 1])
        with col1:
            study_desc = st.text_area(
                "Study Description", 
                value="",
                height=200,
                help="Detailed description of the study"
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("✨ Generate Description", help="Generate using AI"):
                if product:
                    prompt = f"Create a comprehensive study description for a product called {product['product_name']}. "
                    prompt += f"Product details: {product['technical_explanation']} "
                    prompt += f"Consumer pitch: {product['consumer_pitch']}"
                    
                    generated_desc = self._call_gpt(prompt, max_tokens=300)
                    if generated_desc:
                        study_desc = generated_desc
        
        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Cancel"):
                st.session_state.study_step = 0
                st.session_state.study_data = None
                st.rerun()
        with col2:
            if st.button("Next: Generate Questions →"):
                st.session_state.study_data.update({
                    "study_name": study_name,
                    "study_description": study_desc
                })
                st.session_state.study_step = 2
                st.rerun()
    
    def _step2_questions(self, product):
        """Step 2: Generate study questions"""
        study_data = st.session_state.study_data
        
        st.info(f"Generating questions for: {study_data['study_name']}")
        
        if st.button("🧠 Generate Questions with AI"):
            if product:
                prompt = f"Generate 5 market research questions about {product['product_name']} with 4 multiple-choice options each. "
                prompt += f"Product details: {product['technical_explanation']}\n\n"
                prompt += "Format response as JSON: [{'question': '', 'options': []}]"
                
                questions_json = self._call_gpt(prompt, max_tokens=600, json_mode=True)
                if questions_json:
                    try:
                        questions = json.loads(questions_json)
                        if isinstance(questions, list):
                            study_data["questions"] = questions
                            st.success("Questions generated successfully!")
                        else:
                            st.error("Invalid response format from AI")
                    except json.JSONDecodeError:
                        st.error("Failed to parse AI response")
        
        # Display and edit questions
        for i, q in enumerate(study_data["questions"]):
            st.divider()
            st.markdown(f"**Question #{i+1}**")
            
            col1, col2 = st.columns([4, 1])
            with col1:
                question = st.text_input(
                    f"Question {i+1}", 
                    value=q["question"],
                    key=f"q_{i}"
                )
            with col2:
                st.write("")
                if st.button("❌", key=f"del_q_{i}"):
                    study_data["questions"].pop(i)
                    st.rerun()
            
            options = q["options"]
            for j in range(4):
                options[j] = st.text_input(
                    f"Option {j+1}", 
                    value=options[j] if j < len(options) else "",
                    key=f"q_{i}_opt_{j}"
                )
        
        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back"):
                st.session_state.study_step = 1
                st.rerun()
        with col2:
            if st.button("Next: Prelim Questions →"):
                st.session_state.study_step = 3
                st.rerun()
    
    def _step3_prelim_questions(self):
        """Step 3: Add preliminary questions"""
        study_data = st.session_state.study_data
        prelim_questions = study_data["prelim_questions"]
        
        st.info("Add preliminary questions (e.g., demographic questions)")
        
        # Add new question button
        if st.button("➕ Add Preliminary Question"):
            prelim_questions.append({
                "question": "",
                "options": ["", "", ""]
            })
            st.rerun()
        
        # Existing questions
        for i, q in enumerate(prelim_questions):
            st.divider()
            st.markdown(f"**Preliminary Question #{i+1}**")
            
            col1, col2 = st.columns([4, 1])
            with col1:
                question = st.text_input(
                    f"Prelim Question {i+1}", 
                    value=q["question"],
                    key=f"prelim_q_{i}"
                )
            with col2:
                st.write("")
                if st.button("❌", key=f"del_prelim_{i}"):
                    prelim_questions.pop(i)
                    st.rerun()
            
            options = q["options"]
            for j in range(3):
                options[j] = st.text_input(
                    f"Option {j+1}", 
                    value=options[j] if j < len(options) else "",
                    key=f"prelim_{i}_opt_{j}"
                )
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back to Questions"):
                st.session_state.study_step = 2
                st.rerun()
        with col3:
            if st.button("Review Study →"):
                st.session_state.study_step = 4
                st.rerun()
    
    def _step4_review(self):
        """Step 4: Review and save study"""
        study_data = st.session_state.study_data
        
        st.subheader("🔍 Study Review")
        st.markdown(f"**Study Name:** {study_data['study_name']}")
        st.markdown(f"**Description:** {study_data['study_description']}")
        
        st.subheader("Main Questions")
        for i, q in enumerate(study_data["questions"]):
            st.markdown(f"{i+1}. {q['question']}")
            for j, opt in enumerate(q["options"]):
                st.markdown(f"    {chr(65+j)}. {opt}")
        
        st.subheader("Preliminary Questions")
        for i, q in enumerate(study_data["prelim_questions"]):
            st.markdown(f"{i+1}. {q['question']}")
            for j, opt in enumerate(q["options"]):
                st.markdown(f"    {chr(65+j)}. {opt}")
        
        if st.button("💾 Save Study"):
            project_id = st.session_state.current_project["_id"]
            success = self.auth.save_study(
                project_id,
                study_data
            )
            if success:
                st.success("Study saved successfully!")
                st.session_state.study_step = 0
                st.session_state.study_data = None
            else:
                st.error("Failed to save study")
        
        if st.button("← Edit Questions"):
            st.session_state.study_step = 3
            st.rerun()
    
    def _call_gpt(self, prompt, max_tokens=500, json_mode=False):
        """Call GPT API for content generation"""
        # Implementation depends on your API setup
        # This is a placeholder implementation
        try:
            # Example using OpenAI API (needs proper setup)
            from openai import OpenAI
            from config import aii
            # openai.api_key = aii
            client=OpenAI(api_key=aii)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                response_format="json" if json_mode else None  # ✅ Correct param name
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"AI generation failed: {str(e)}")
            return None