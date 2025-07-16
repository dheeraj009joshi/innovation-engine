import json
import time
from  dotenv import load_dotenv
import pandas as pd 
import os
from openai import OpenAI
import streamlit as st
from playwright.sync_api import sync_playwright
load_dotenv()

# Access the variables
aii = os.getenv("aii")


class StudyGenerationFromFinalizeSheet:


    def __init__(self,filename,filecategory):
        self.filename=filename
        self.filecategory=filecategory
    


    def prepare_study(self,theme):
           
        desc_prompt = (
            f"Create a comprehensive study description for a theme  called {theme["Theme"]}. "
            f"Theme description details: {theme['Theme Description']} "
            f"Category of theme : {theme['Category']} "
            f"Theme {self.filecategory} : {theme[self.filecategory]}"
            f"Theme {self.filecategory} Description : {theme[self.filecategory+" Description"]}"
            # Team Inputted Prompt
            f""
            "Make this into a 4–5 paragraph response."
        )
        description = self._call_gpt(desc_prompt, max_tokens=400, json_mode=False)


        respondent_orientation_prompt = (
            f"Write a short, friendly orientation message for a research study about the theme '{theme["Theme"]} {theme['Theme Description']}'.\n\n"
            f"Theme overview:\n{theme["Theme"]}\n\n"
             f"Category of theme : {theme['Category']} "
            f"Theme {self.filecategory} : {theme[self.filecategory]}"
            f"Theme {self.filecategory} Description : {theme[self.filecategory+" Description"]}"
            "This message should introduce the participant to the study, explain the purpose in simple terms, "
            "and encourage them to answer honestly and thoughtfully. Keep the tone warm, human, and concise (no more than 2 short paragraphs). "
            "Avoid technical jargon, and focus on making the participant feel comfortable and informed."
        )
        respondent_orientation = self._call_gpt(respondent_orientation_prompt, max_tokens=250, json_mode=False)

    
        q_prompt = (
           f" Theme name    {theme["Theme"]}. "
            f"Theme description details: {theme['Theme Description']} "
            f"Category of theme : {theme['Category']} "
            f"Theme {self.filecategory} : {theme[self.filecategory]}"
            f"Theme {self.filecategory} Description : {theme[self.filecategory+" Description"]}"
            # Team Inputted Questions Prompt
            f"""
            We are interested in understanding the factors that make a person want to adopt or comply with a Theme, experience, or solution. These factors may include physical needs, emotional desires, lifestyle improvements, or other personal motivations.
            You are working with the following:
            Theme name
            Theme description
            Theme details
            For this Theme or concept, create four questions that are relevant to the benefit or experience being offered. For each question, provide four answers in simple English. These answers should be short descriptive statements that reflect what the person using this Theme would say they "want" or "think is important."
            To summarize:
            You know the Theme or concept based on the study name and description provided above.


            You are to ask four relevant questions about the person's everyday life, needs, or hopes. These questions must each begin with the phrase:
            "Describe a situation that is important to you personally..."


            Before generating the question, make sure that the object of the question is radically different for each question. compare each question to each other and make sure they are radically different

            i.e "Describe a situtation that is important you personally...(this part should be radically different from the other questions)"
            
            Each question should have four answers. These answers should reflect:


            What the person experiences in daily life,


            Or what they care about related to the Theme’s purpose,


            Or what they are hoping for over the next few years.


            Keep all language simple, natural, and consumer-friendly.



            """
            "Return a valid JSON object in this format:\n"
            "{ \"questions\": [ { \"question\": \"\", \"options\": [\"\", \"\", \"\", \"\"] } ] }"
        )
        question_data = self._call_gpt(q_prompt, max_tokens=700, json_mode=True)

        
        p_prompt = (
            f" Theme name  :  {theme["Theme"]}. "
            f"Theme description details: {theme['Theme Description']} "
            f"Category of theme : {theme['Category']} "
            f"Theme {self.filecategory} : {theme[self.filecategory]}"
            f"Theme {self.filecategory} Description : {theme[self.filecategory+" Description"]}"
            f"Study questions: {question_data}" 


            # Team Inputted Preliminary Prompt
            f"""
            Read the study questions and all 16 answers. Based on the 16 answers, generate 8 radically different questions that directly ask the user about themselves. Each question must paint a vivid picture of who the user is—what they feel about the Theme, how they see themselves, and how the Theme makes them feel. Each question should be written in the second person and ask the user a question.

            For each question, provide exactly 3 radically different answers . Each answer should be a full sentence with 5-10 words. The answers must be rich with information and should reveal how the user thinks, their rituals, emotions, habits, or worldview in relation to the situation. The answers MUST NOT BE in second person.

            Next, return to the description of the Theme. Create 8 questions that directly ask the user about their experience with the Theme and what it reveals about their life (e.g., if the Theme is a health Theme, ask how it fits into their health rituals or mindset).

            Now, imagine you’re looking at this Theme and asking:
            “What does this Theme reveal about you?”
            Write 8 classification questions that each directly ask the user to identify something about themselves—how they think, act, or feel—through the lens of the Theme.

            Each of the 8 questions should include 3 mutually exclusive and unexpected answers that:

            The first answer is phrased with strong love

            The second answer is phrased with indifference

            The third answer is phrased with strong hate

            The answers should be directly relevant to the question, and be realistic and socially acceptable

            The answers are written as full sentences (max 10 words)

            The answers are rich in meaning and emotionally vivid

            The answers are something distinct and usable for segmentation

            The answers are not in second person


            All questions must speak directly to the user and every answer must help us understand who they are on a deeper level. Avoid generic phrasing—these should feel personal, human, and revealing.




            """
            "Return a valid JSON object which has only questions key which holds the list of all the questions and their answers (no other keys or other data ) in this format:\n"
            "{ \"questions\": [ { \"question\": \"\", \"options\": [\"\", \"\", \"\"] } ] }"
        )
        prelim_json = self._call_gpt(p_prompt, max_tokens=2000, json_mode=True)
        # print({"main questions ": question_data})
        # print({"perlim questions ": prelim_json})

        final_thoughts_prompt = (
            f"Write a closing statement for a research study about the Theme ' {theme["Theme"]}'.\n\n"
            f"Theme description:\n {theme["Theme Description"]}\n\n"
            f"The participant has just completed questions about their needs, lifestyle, mindset, and relationship to the Theme.\n\n"
            "Write 2–3 short paragraphs that:\n"
            "- Thank the participant genuinely for their time and insights\n"
            "- Reinforce why their responses matter to improving the Theme and understanding its users\n"
            "- Reflect the Theme’s tone (warm, human, innovative, or insightful)\n"
            "- Feel personal and intentional, not robotic or generic\n"
            "- End with a line that leaves the participant feeling valued and understood\n"
        )
        final_thoughts = self._call_gpt(final_thoughts_prompt, max_tokens=300, json_mode=False)

        try:
            main_questions = json.loads(question_data)["questions"]
            prelim_questions = json.loads(prelim_json)["questions"]
        except Exception as e:
            
            return

        study_data = {
            "study_name": theme["Theme"],
            "study_description": description,
            "questions": main_questions,
            "prelim_questions": prelim_questions,
            "respondent_orientation":respondent_orientation,
            "final_thoughts":final_thoughts

        }
        return study_data








    def prepare_study_vdemo(self,question_data):




        study_name_prompt = (
            "Generate a professional yet approachable name for a sleep research study based on these questions and concerns:\n"
            f"Questions and concerns: {question_data}\n\n"
            "The name should:\n"
            "- Be 3-7 words long\n"
            "- Include either 'Study', 'Research', or 'Insights'\n"
            "- Reflect the comprehensive nature of sleep research\n"
            "- Capture key themes from the provided questions\n"
            "- Examples: 'Sleep Quality Insights Study', 'Rest Optimization Research'"
        )
        study_name = self._call_gpt(study_name_prompt, max_tokens=100, json_mode=False)




           
        desc_prompt = (
            f"Create a comprehensive 4-5 paragraph study description for a sleep research study based on these participant concerns:\n"
            f"{question_data}\n\n"
            "Structure the description to:\n"
            "1. Introduce the importance of sleep quality\n"
            "2. Explain the study's focus areas derived from the questions\n"
            "3. Describe the research approach\n"
            "4. Highlight the value of participant contributions\n"
            "5. Mention practical applications of the findings"
        )
        
        
        
        description = self._call_gpt(desc_prompt, max_tokens=400, json_mode=False)


        respondent_orientation_prompt = (
            "Write a friendly 2-paragraph orientation message for a sleep study based on these participant concerns:\n"
            f"{question_data}\n\n"
            "The message should:\n"
            "- Welcome participants warmly\n"
            "- Explain the study's purpose in simple terms\n"
            "- Mention key focus areas from the questions\n"
            "- Encourage honest, thoughtful responses\n"
            "- Keep tone conversational and reassuring"
        )
        
        
        respondent_orientation = self._call_gpt(respondent_orientation_prompt, max_tokens=250, json_mode=False)

    

        p_prompt = (
             "Generate insightful questions about sleep habits and preferences based on these existing concerns:\n"
            f"{question_data}\n\n"
            # Team Inputted Preliminary Prompt
            f"""
            Read the study questions and all 16 answers. Based on the 16 answers, generate 8 radically different questions that directly ask the user about themselves. Each question must paint a vivid picture of who the user is—what they feel about the Theme, how they see themselves, and how the Theme makes them feel. Each question should be written in the second person and ask the user a question.

            For each question, provide exactly 3 radically different answers . Each answer should be a full sentence with 5-10 words. The answers must be rich with information and should reveal how the user thinks, their rituals, emotions, habits, or worldview in relation to the situation. The answers MUST NOT BE in second person.

            Next, return to the description of the Theme. Create 8 questions that directly ask the user about their experience with the Theme and what it reveals about their life (e.g., if the Theme is a health Theme, ask how it fits into their health rituals or mindset).

            Now, imagine you’re looking at this Theme and asking:
            “What does this Theme reveal about you?”
            Write 8 classification questions that each directly ask the user to identify something about themselves—how they think, act, or feel—through the lens of the Theme.

            Each of the 8 questions should include 3 mutually exclusive and unexpected answers that:

            The first answer is phrased with strong love

            The second answer is phrased with indifference

            The third answer is phrased with strong hate

            The answers should be directly relevant to the question, and be realistic and socially acceptable

            The answers are written as full sentences (max 10 words)

            The answers are rich in meaning and emotionally vivid

            The answers are something distinct and usable for segmentation

            The answers are not in second person


            All questions must speak directly to the user and every answer must help us understand who they are on a deeper level. Avoid generic phrasing—these should feel personal, human, and revealing.




            """
            "Return a valid JSON object which has only questions key which holds the list of all the questions and their answers (no other keys or other data ) in this format:\n"
            "{ \"questions\": [ { \"question\": \"\", \"options\": [\"\", \"\", \"\"] } ] }"
        )
        
        
        
        
        prelim_json = self._call_gpt(p_prompt, max_tokens=2000, json_mode=True)
        # print({"main questions ": question_data})
        # print({"perlim questions ": prelim_json})

        final_thoughts_prompt = (
            "Write a closing message for a sleep study based on these participant concerns:\n"
            f"{question_data}\n\n"
            "The message should:\n"
            "- Thank participants genuinely\n"
            "- Connect their input to sleep research\n"
            "- Keep tone warm and human\n"
            "- Be 2-3 short paragraphs\n"
            "- End with a sense of appreciation"
        )
        final_thoughts = self._call_gpt(final_thoughts_prompt, max_tokens=300, json_mode=False)

        try:
            # main_questions = json.loads(question_data)["questions"]
            prelim_questions = json.loads(prelim_json)["questions"]
        except Exception as e:
            
            return

        study_data = {
            "study_name": study_name,
            "study_description": description,
            "questions": question_data,
            "prelim_questions": prelim_questions,
            "respondent_orientation":respondent_orientation,
            "final_thoughts":final_thoughts

        }
        return study_data


    def _call_gpt(self, prompt, max_tokens=500, json_mode=False):
        try:
            client = OpenAI(api_key=aii)
            response = client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                response_format={"type": "json_object"} if json_mode else None
            )
            print(response.choices[0].message.content)
            return response.choices[0].message.content
        except Exception as e:
            print("error getting ai response ",e)
            return None
    

    def run_study(self, study_data, username, password,number_of_respondents):



        final_format = {
            "username": username,
            "password": password,
            "study_name": study_data['study_name'],
            "question_1": study_data['questions'][0]['question'],
            "question_1_answers": study_data['questions'][0]['options'],
            "question_2": study_data['questions'][1]['question'],
            "question_2_answers": study_data['questions'][1]['options'],
            "question_3": study_data['questions'][2]['question'],
            "question_3_answers": study_data['questions'][2]['options'],
            "question_4": study_data['questions'][3]['question'],
            "question_4_answers": study_data['questions'][3]['options'],
            }

            # Add classification questions
        for i in range(8):
            q = study_data['prelim_questions'][i]
            final_format[f"classification_question_{i+1}"] = q['question']
            final_format[f"classification_question_{i+1}_answers"] = q['options']

        # Add rest
        final_format.update({
            "respondent_orientation": study_data['respondent_orientation'],
            "rating_scale_question": "Please rate the following according to the scale below:",
            "rating_1": "Strongly Disagree",
            "rating_2": "Disagree",
            "rating_3": "Neutral",
            "rating_4": "Agree",
            "rating_5": "Strongly Agree",
            "final_thoughts": study_data['final_thoughts'],
            "keyword": "invention",
            "respondents": number_of_respondents
        })

        self.create_study_for_user(final_format,"","")

        

    def click_forward_arrow(self,page):
        page.wait_for_selector('div.nav-chevron', timeout=5000)
        clicked = False
        try:
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(0.2)
            right_fa_layers = page.locator('div.nav-chevron').nth(1).locator('div.fa-layers')
            right_fa_layers.scroll_into_view_if_needed(timeout=2000)
            box = right_fa_layers.bounding_box()
            if box:
                page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                time.sleep(0.2)
                page.mouse.down()
                time.sleep(0.2)
                page.mouse.up()
                print("Simulated real mouse click at center of right fa-layers")
                time.sleep(1.5)
                clicked = True
        except Exception as e:
            print(f"Failed mouse click simulation: {e}")
        if not clicked:
            try:
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(0.2)
                right_fa_layers = page.locator('div.nav-chevron').nth(1).locator('div.fa-layers')
                right_fa_layers.scroll_into_view_if_needed(timeout=2000)
                right_fa_layers.click(force=True)
                print("Forced click on right fa-layers after scroll")
                
                time.sleep(1.5)
                clicked = True
            except Exception as e:
                print(f"Failed forced click after scroll: {e}")
        if not clicked:
            print("Could not find or click the right arrow button")
        else:
            print("Forward arrow clicked successfully")

    def fill_answers_screen(self,page, answers, label="answers"):
        time.sleep(2)
        max_wait = 10
        waited = 0
        visible_fields = []
        fields_to_fill = []
        while waited < max_wait:
            all_fields = page.locator('input[type="text"]')
            handles = all_fields.element_handles()
            visible_fields = [h for h in handles if h.is_visible()]
            fields_to_fill = [h for h in visible_fields if not h.get_attribute("placeholder")]
            if len(fields_to_fill) >= 4:
                break
            time.sleep(0.5)
            waited += 0.5
        print(f"[{label}] Found {len(fields_to_fill)} answer fields")
        for idx, (handle, value) in enumerate(zip(fields_to_fill, answers)):
            try:
                handle.fill(value)
                print(f"[{label}] Filled answer {idx+1}: {value}")
            except Exception as e:
                print(f"[{label}] Could not fill answer {idx+1}: {e}")
        if len(fields_to_fill) < 4:
            print(f"[{label}] Warning: Fewer than 4 answer fields found")
        self.click_forward_arrow(page)

    def fill_classification_questions(self,page, data):
        last_idx = 0
        for i in range(1, 9):
            cq_key = f"classification_question_{i}"
            ca_key = f"classification_question_{i}_answers"
            if cq_key in data and data[cq_key]:
                last_idx = i
                page.wait_for_selector('textarea[rows="5"]', timeout=5000)
                textareas = page.locator('textarea[rows="5"]')
                count = textareas.count()
                textarea = textareas.nth(count - 1)
                current_value = textarea.input_value()
                if current_value and current_value == data[cq_key]:
                    print(f"Classification question {i} already filled")
                else:
                    textarea.fill(data[cq_key])
                    print(f"Filled classification question {i}")
                time.sleep(0.5)
                if ca_key in data and isinstance(data[ca_key], list):
                    this_textarea_xpath = f"(//textarea[@rows='5'])[{count}]"
                    input_fields = page.locator(f'{this_textarea_xpath}/following::input[@type="text"]')
                    answer_handles = []
                    for j in range(input_fields.count()):
                        h = input_fields.nth(j)
                        try:
                            if h.is_visible():
                                answer_handles.append(h)
                                if len(answer_handles) == len(data[ca_key]):
                                    break
                        except Exception:
                            continue
                    print(f"Filling {len(answer_handles)} answers for classification {i}")
                    for idx, (h, value) in enumerate(zip(answer_handles, data[ca_key])):
                        h.fill(value)
                        print(f"Filled classification answer {idx+1}: {value}")
                next_cq_key = f"classification_question_{i+1}"
                if next_cq_key in data and data[next_cq_key]:
                    page.locator('span:has-text("Add Classification Question")').click()
                    print(f"Added classification question {i+1}")
                    for attempt in range(20):
                        new_count = page.locator('textarea[rows="5"]').count()
                        if new_count > count:
                            break
                        time.sleep(0.5)
                    time.sleep(1.5)
        print(f"Completed {last_idx} classification questions")
        self.click_forward_arrow(page)

    def wait_for_heading_and_advance(self,page, target_text, progress_bar, status_text, do_fill=None, fill_value=None):
        print(f"Waiting for '{target_text}' screen")
        status_text.info(f"⏳ Transitioning to {target_text}...")
        for attempt in range(30):
            headings = page.locator('h2')
            for idx in range(headings.count()):
                if target_text.upper() in headings.nth(idx).inner_text().strip().upper():
                    print(f"Reached {target_text} screen")
                    if do_fill and fill_value is not None:
                        page.wait_for_selector('div.ql-editor[contenteditable="true"]', timeout=10000)
                        quill_editor = page.locator('div.ql-editor[contenteditable="true"]').first
                        quill_editor.fill("")
                        time.sleep(0.3)
                        quill_editor.fill(fill_value)
                        print(f'Filled: {fill_value}')
                        time.sleep(1.5)
                    self.click_forward_arrow(page)
                    print(f"Advanced from {target_text}")
                    return
            time.sleep(0.5)
        print(f"ERROR: '{target_text}' heading not found")
        self.click_forward_arrow(page)

    def fill_rating_scale(self,page, data, progress_bar, status_text):
        print("Waiting for 'RATING SCALE' screen")
        status_text.info("📊 Configuring rating scale...")
        for attempt in range(20):
            headings = page.locator('h2')
            for idx in range(headings.count()):
                if "RATING SCALE" in headings.nth(idx).inner_text().strip().upper():
                    print("Detected RATING SCALE screen")
                    page.wait_for_selector('textarea[rows="5"]', timeout=10000)
                    page.locator('textarea[rows="5"]').fill(data["rating_scale_question"])
                    print(f"Question: {data['rating_scale_question']}")
                    dropdown = page.locator('select')
                    if dropdown.count() > 0:
                        dropdown.select_option("5")
                        print("Set scale to 5 points")
                    time.sleep(1)
                    select_elem = page.locator('select').first
                    select_handle = select_elem.element_handle()
                    all_inputs = page.locator('input[type="text"]').element_handles()
                    rating_inputs = []
                    found = False
                    if select_handle and select_handle.bounding_box():
                        select_y = select_handle.bounding_box()['y']
                        after = [inp for inp in all_inputs if inp.bounding_box() and inp.bounding_box()['y'] > select_y]
                        rating_inputs = [inp for inp in after if inp.is_visible()][:5]
                        found = True if len(rating_inputs) == 5 else False
                    if not found or len(rating_inputs) < 5:
                        rating_inputs = [inp for inp in all_inputs if inp.is_visible()][:5]
                    for idx, rating_key in enumerate(["rating_1", "rating_2", "rating_3", "rating_4", "rating_5"]):
                        try:
                            rating_inputs[idx].fill(data[rating_key])
                            print(f"{rating_key}: {data[rating_key]}")
                        except Exception as e:
                            print(f"Could not fill {rating_key}: {e}")
                    time.sleep(1.0)
                    self.click_forward_arrow(page)
                    print("Advanced from rating scale")
                    return
            time.sleep(0.5)
        print("ERROR: 'RATING SCALE' screen not found")
        self.click_forward_arrow(page)

    def fill_final_thoughts(self,page, data):
        print("Waiting for 'FINAL THOUGHTS' screen")
        for attempt in range(20):
            headings = page.locator('h2')
            found = False
            for idx in range(headings.count()):
                if "FINAL THOUGHTS" in headings.nth(idx).inner_text().strip().upper():
                    found = True
                    print("Detected FINAL THOUGHTS screen")
                    break
            if found:
                break
            time.sleep(0.5)
        page.wait_for_selector('textarea[rows="5"]', timeout=5000)
        page.locator('textarea[rows="5"]').fill(data.get("final_thoughts", ""))
        print(f"Final thoughts: {data.get('final_thoughts', '')}")
        keyword = data.get("keyword", "")
        page.wait_for_selector('input[placeholder="New keyword"]', timeout=5000)
        kw_input = page.locator('input[placeholder="New keyword"]')
        kw_input.fill(keyword)
        print(f"Keyword: {keyword}")
        add_btn = page.locator('button.add-keyword-button:has-text("Add")')
        if add_btn.count() > 0:
            add_btn.first.click()
            print("Added keyword")
        else:
            print("WARNING: Add button not found")
        time.sleep(1)
        self.click_forward_arrow(page)
        print("Advanced from final thoughts")

    def handle_custom_sample(self,page):
        print("Selecting custom sample")
        for attempt in range(20):
            option = page.locator('span:has-text("I want a custom sample of respondents from BimiLeap")')
            if option.count() > 0 and option.is_visible():
                option.first.click()
                print("Selected custom sample option")
                break
            time.sleep(0.5)
        for attempt in range(20):
            modal_btn = page.locator('button:has-text("Continue")')
            if modal_btn.count() > 0 and modal_btn.is_visible():
                modal_btn.first.click()
                print("Clicked CONTINUE in modal")
                break
            time.sleep(0.5)
        time.sleep(1.5)

    def handle_done_screen(self,page, data, progress_bar, status_text):
        print("Handling final screen")
        status_text.info("🎉 Finalizing study...")
        for attempt in range(20):
            headings = page.locator('h2')
            found = False
            for idx in range(headings.count()):
                text = headings.nth(idx).inner_text().strip().upper()
                if "DONE!" in text:
                    found = True
                    print("Detected DONE! screen")
                    break
            if found:
                break
            time.sleep(0.5)
        num_respondents = str(data.get("respondents", ""))
        page.wait_for_selector('input[placeholder="Number of respondents"]', timeout=5000)
        page.locator('input[placeholder="Number of respondents"]').fill(num_respondents)
        print(f"Respondents: {num_respondents}")
        radio_no = page.locator('input[type="radio"][value="public"]')
        if radio_no.count() > 0:
            radio_no.first.check()
            print("Selected 'No' radio button")
        else:
            print("WARNING: 'No' radio button not found")
        agree_box = page.locator('input[type="checkbox"]#agree-new')
        if agree_box.count() > 0:
            agree_box.first.check()
            print("Checked agreement checkbox")
        else:
            print("WARNING: agreement checkbox not found")
        time.sleep(1)
        publish_btn = page.locator('button:has-text("PUBLISH!")')
        if publish_btn.count() > 0 and publish_btn.is_visible():
            publish_btn.first.click()
            print("Clicked PUBLISH! button")
        else:
            print("WARNING: PUBLISH! button not found")
        print("Waiting for publish confirmation...")
        for attempt in range(20):
            popup = page.locator('text=Your study has been published')
            if popup.count() > 0 and popup.is_visible():
                print("Publish pop-up detected")
                break
            time.sleep(0.5)
        time.sleep(1.0)
        continue_btn = page.locator('button:has-text("CONTINUE")')
        for attempt in range(10):
            if continue_btn.count() > 0 and continue_btn.is_visible():
                with page.expect_navigation(timeout=7000):
                    continue_btn.first.click()
                print("Clicked CONTINUE in pop-up")
                break
            time.sleep(0.5)
        print("Automation complete")
        print("✅ Study published successfully!")

# Main study creation function with UI integration
    def create_study_for_user(self,data, progress_bar, status_text): 
        USERNAME = "mindgenometest@gmail.com"
        PASSWORD = "mindgenome123"
        STUDY_NAME = data["study_name"]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Login process
            progress_bar.progress(5)
            # status_text.info("🚀 Starting study creation...")
            print("Initializing browser")
            
            page.goto("https://www.bimileap.com/")
            print("Navigated to homepage")
            
            page.locator("text=Login").click()
            print("Clicked Login button")
            
            page.wait_for_selector('input[placeholder="Email"]', timeout=5000)
            page.wait_for_selector('input[type="password"]', timeout=5000)
            page.fill('input[placeholder="Email"]', USERNAME)
            page.fill('input[type="password"]', PASSWORD)
            print("Filled credentials")
            
            page.locator("text=SIGN IN").click()
            print("Clicked SIGN IN")
            
            progress_bar.progress(15)
            # status_text.info("🔐 Logging in...")

            try:
                page.wait_for_url("**/dashboard", timeout=10000)
                progress_bar.progress(25)
                # status_text.info("✅ Login successful")
                print("Now on dashboard")
                
                page.locator("text=Create New Study").click()
                print("Clicked 'Create New Study'")
                
                progress_bar.progress(30)
                status_text.info("📝 Creating study...")
                
                page.wait_for_selector('input[placeholder="My Study"]', timeout=5000)
                page.fill('input[placeholder="My Study"]', STUDY_NAME)
                page.keyboard.press('Tab')
                print(f"Study name: {STUDY_NAME}")
                
                page.check('input#agree')
                page.keyboard.press('Tab')
                print("Checked agreement box")
                
                time.sleep(1)
                self.click_forward_arrow(page)
                time.sleep(2)
                
                progress_bar.progress(35)
                status_text.info("❓ Adding questions...")
                
                max_wait = 10
                waited = 0
                visible_fields = []
                fields_to_fill = []
                while waited < max_wait:
                    all_fields = page.locator('input[type="text"]')
                    handles = all_fields.element_handles()
                    visible_fields = [h for h in handles if h.is_visible()]
                    fields_to_fill = [h for h in visible_fields if not h.get_attribute("placeholder")]
                    if len(fields_to_fill) >= 4:
                        break
                    time.sleep(0.5)
                    waited += 0.5
                    
                print(f"Found {len(fields_to_fill)} question fields")
                questions = [
                    data["question_1"],
                    data["question_2"],
                    data["question_3"],
                    data["question_4"]
                ]
                
                for idx, (handle, value) in enumerate(zip(fields_to_fill, questions)):
                    try:
                        handle.fill(value)
                        print(f"Added question {idx+1}: {value}")
                    except Exception as e:
                        print(f"Could not fill question {idx+1}: {e}")
                        
                if len(fields_to_fill) < 4:
                    print("Warning: Fewer than 4 question fields found")
                    
                self.click_forward_arrow(page)
                
                progress_bar.progress(45)
                status_text.info("📝 Adding answers...")
                
                self.fill_answers_screen(page, data["question_1_answers"], "Q1 answers")
                progress_bar.progress(50)
                self.fill_answers_screen(page, data["question_2_answers"], "Q2 answers")
                progress_bar.progress(55)
                self.fill_answers_screen(page, data["question_3_answers"], "Q3 answers")
                progress_bar.progress(60)
                self.fill_answers_screen(page, data["question_4_answers"], "Q4 answers")
                
                progress_bar.progress(65)
                status_text.info("👥 Adding classification questions...")
                self.fill_classification_questions(page, data)
                
                progress_bar.progress(70)
                status_text.info("📋 Configuring pre-presentation...")
                self.wait_for_heading_and_advance(page, "Pre-Presentation", progress_bar, status_text)
                
                progress_bar.progress(75)
                status_text.info("📝 Adding open-ended questions...")
                self.wait_for_heading_and_advance(page, "OPEN ENDED QUESTION", progress_bar, status_text)
                
                progress_bar.progress(80)
                status_text.info("🧭 Setting respondent orientation...")
                self.wait_for_heading_and_advance(
                    page, 
                    "RESPONDENT ORIENTATION", 
                    progress_bar, 
                    status_text, 
                    do_fill=True, 
                    fill_value=data.get("respondent_orientation", "")
                )
                
                progress_bar.progress(85)
                self.fill_rating_scale(page, data, progress_bar, status_text)
                
                progress_bar.progress(90)
                status_text.info("📊 Configuring post-presentation...")
                self.wait_for_heading_and_advance(page, "POST-PRESENTATION", progress_bar, status_text)
                
                progress_bar.progress(92)
                status_text.info("📝 Adding final thoughts...")
                self.wait_for_heading_and_advance(page, "OPEN ENDED QUESTION", progress_bar, status_text)
                
                progress_bar.progress(95)
                status_text.info("👥 Selecting respondents...")
                self.fill_final_thoughts(page, data)
                
                progress_bar.progress(97)
                status_text.info("🔍 Setting sample...")
                self.handle_custom_sample(page)
                
                self.handle_done_screen(page, data, progress_bar, status_text)
                
                # Final delay before closing
                time.sleep(3)
                print("Study creation completed successfully")
                return True
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return False
            finally:
                browser.close()






            
    def process_csv(self):

        df=pd.read_csv(self.filename)
        # return  df.to_json(orient='records')


        # Group answers by question into a dictionary
        question_answer_dict = df.groupby("Question")["Answer"].apply(list).to_dict()

       
        questions=  [
                {"question": q, "options": a} for q, a in question_answer_dict.items()
            ]
       

     
        print(questions)
        return [questions[i:i + 4] for i in range(0, len(questions), 4)]



       

    

if __name__ == "__main__":

    filename="Situations-Study-Final.csv"
    segment_column="Situation"
    number_of_respondents=100
    worker=StudyGenerationFromFinalizeSheet(filename, segment_column)
    # worker_list_csv_objects=json.loads(worker.process_csv())  # for main 
    worker_list_csv_objects=worker.process_csv()  # temp usage 
    for quest in worker_list_csv_objects:
        get_study_data= worker.prepare_study_vdemo(quest)
        print(get_study_data)
        run_study=worker.run_study(get_study_data,"","",number_of_respondents)
   






