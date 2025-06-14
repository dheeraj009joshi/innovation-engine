# study_generation.py

import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
from config import aii  # Your OpenAI API key module

class StudyGenerationProcess:
    def __init__(self, auth, currentProduct):
        self.auth = auth
        self.currentProduct = currentProduct

    def run(self):
        if "study_step" not in st.session_state:
            st.session_state.study_step = 1
        if "study_data" not in st.session_state or not st.session_state.study_data:
            st.session_state.study_data = {
                "study_name": "",
                "study_description": "",
                "questions": [],
                "prelim_questions": []
            }

        if st.button("⚙️ Auto Generate Full Study"):
            with st.spinner("Thinking deeply about your product..."):
                self._auto_generate_full_study()
            st.session_state.study_step = 4
            st.rerun()

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

    def _auto_generate_full_study(self):
        product = self.currentProduct
        if not product:
            st.error("No product data found.")
            return

        with st.status("Generating study...", expanded=True) as status:
            status.update(label="🧠 Generating Study Description...")
            desc_prompt = (
                f"Create a comprehensive study description for a product called {product['product_name']}. "
                f"Product details: {product['technical_explanation']} "
                f"Consumer pitch: {product['consumer_pitch']} "
                "Make this into a 4–5 paragraph response."
            )
            description = self._call_gpt(desc_prompt, max_tokens=400, json_mode=False)

            status.update(label="🧪 Generating Main Questions...")
            q_prompt = (
                f"Generate 4 market research questions about {product['product_name']} with 4 mutually exclusive options each. "
                f"Product details: {product['technical_explanation']} "
                "Return a valid JSON object in this format:\n"
                "{ \"questions\": [ { \"question\": \"\", \"options\": [\"\", \"\", \"\", \"\"] } ] }"
            )
            questions_json = self._call_gpt(q_prompt, max_tokens=700, json_mode=True)

            status.update(label="📋 Generating Prelim Questions...")
            p_prompt = (
                "Generate 16 demographic or behavioral questions, each with 3 mutually exclusive options. "
                "Return a valid JSON object in this format:\n"
                "{ \"questions\": [ { \"question\": \"\", \"options\": [\"\", \"\", \"\"] } ] }"
            )
            prelim_json = self._call_gpt(p_prompt, max_tokens=1000, json_mode=True)

            try:
                main_questions = json.loads(questions_json)["questions"]
                prelim_questions = json.loads(prelim_json)["questions"]
            except Exception as e:
                st.error("❌ Failed to parse AI response.")
                return

            st.session_state.study_data = {
                "study_name": product["product_name"],
                "study_description": description,
                "questions": main_questions,
                "prelim_questions": prelim_questions
            }

            status.update(label="✅ Study generated successfully!", state="complete")

    def _step1_setup(self, product):
        study_data = st.session_state.study_data
        default_name = product["product_name"] if product else ""
        study_name = st.text_input("Study Name", value=default_name or study_data["study_name"])

        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_area("Study Description", value=study_data["study_description"], height=200)
        with col2:
            st.write("")
            st.write("")
            if st.button("✨ Generate Description", help="Generate using AI"):
                if product:
                    prompt = f"Create a comprehensive study description for a product called {product['product_name']}. "
                    prompt += f"Product details: {product['technical_explanation']} "
                    prompt += f"Consumer pitch: {product['consumer_pitch']}"
                    prompt += "Make this into a paragraph form and make it of 4-5 paragraphs."
                    generated_desc = self._call_gpt(prompt, max_tokens=300)
                    if generated_desc:
                        st.session_state.study_data["study_description"] = generated_desc
                        st.rerun()

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
                    "study_description": st.session_state.study_data["study_description"]
                })
                st.session_state.study_step = 2
                st.rerun()

    def _step2_questions(self, product):
        study_data = st.session_state.study_data
        st.info(f"Generating questions for: {study_data['study_name']}")

        for i, q in enumerate(study_data["questions"]):
            with st.expander(f"Question #{i+1}: {q['question']}", expanded=False):
                col1, col2 = st.columns([4, 1])
                with col1:
                    question = st.text_input(f"Edit Question {i+1}", value=q["question"], key=f"q_{i}")
                with col2:
                    if st.button("❌ Delete", key=f"del_q_{i}"):
                        study_data["questions"].pop(i)
                        st.rerun()
                options = q["options"]
                for j in range(4):
                    options[j] = st.text_input(f"Option {j+1}", value=options[j], key=f"q_{i}_opt_{j}")

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
        study_data = st.session_state.study_data
        prelim_questions = study_data["prelim_questions"]
        st.info("Add preliminary questions (e.g., demographic questions)")

        for i, q in enumerate(prelim_questions):
            with st.expander(f"Prelim #{i+1}: {q['question']}", expanded=False):
                col1, col2 = st.columns([4, 1])
                with col1:
                    question = st.text_input(f"Prelim Question {i+1}", value=q["question"], key=f"prelim_q_{i}")
                with col2:
                    if st.button("❌", key=f"del_prelim_{i}"):
                        prelim_questions.pop(i)
                        st.rerun()
                options = q["options"]
                for j in range(3):
                    options[j] = st.text_input(f"Option {j+1}", value=options[j], key=f"prelim_{i}_opt_{j}")

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
        study_data = st.session_state.study_data
        st.subheader("🔍 Study Review")
        st.markdown(f"**Study Name:** {study_data['study_name']}")
        st.markdown(f"**Description:** {study_data['study_description']}")

        st.subheader("Main Questions")
        for i, q in enumerate(study_data["questions"]):
            with st.expander(f"Prelim #{i+1}: {q['question']}", expanded=False):
                st.markdown(f"{i+1}. {q['question']}")
                for j, opt in enumerate(q["options"]):
                    st.markdown(f"    {chr(65+j)}. {opt}")

        st.subheader("Preliminary Questions")
        for i, q in enumerate(study_data["prelim_questions"]):
            with st.expander(f"Prelim #{i+1}: {q['question']}", expanded=False):
                st.markdown(f"{i+1}. {q['question']}")
                for j, opt in enumerate(q["options"]):
                    st.markdown(f"    {chr(65+j)}. {opt}")

        if st.button("💾 Save Study"):
            project_id = st.session_state.current_project["_id"]
            success = self.auth.save_study(project_id, study_data)
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
        try:
            client = OpenAI(api_key=aii)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if json_mode else None
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"AI generation failed: {str(e)}")
            return None
