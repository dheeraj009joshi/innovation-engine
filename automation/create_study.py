import time
import streamlit as st
from playwright.sync_api import sync_playwright

def click_forward_arrow(page, log_function):
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
            log_function("Simulated real mouse click at center of right fa-layers")
            time.sleep(1.5)
            clicked = True
    except Exception as e:
        log_function(f"Failed mouse click simulation: {e}")
    if not clicked:
        try:
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(0.2)
            right_fa_layers = page.locator('div.nav-chevron').nth(1).locator('div.fa-layers')
            right_fa_layers.scroll_into_view_if_needed(timeout=2000)
            right_fa_layers.click(force=True)
            log_function("Forced click on right fa-layers after scroll")
            time.sleep(1.5)
            clicked = True
        except Exception as e:
            log_function(f"Failed forced click after scroll: {e}")
    if not clicked:
        log_function("Could not find or click the right arrow button")
    else:
        log_function("Forward arrow clicked successfully")

def fill_answers_screen(page, answers, log_function, label="answers"):
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
    log_function(f"[{label}] Found {len(fields_to_fill)} answer fields")
    for idx, (handle, value) in enumerate(zip(fields_to_fill, answers)):
        try:
            handle.fill(value)
            log_function(f"[{label}] Filled answer {idx+1}: {value}")
        except Exception as e:
            log_function(f"[{label}] Could not fill answer {idx+1}: {e}")
    if len(fields_to_fill) < 4:
        log_function(f"[{label}] Warning: Fewer than 4 answer fields found")
    click_forward_arrow(page, log_function)

def fill_classification_questions(page, data, log_function):
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
                log_function(f"Classification question {i} already filled")
            else:
                textarea.fill(data[cq_key])
                log_function(f"Filled classification question {i}")
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
                log_function(f"Filling {len(answer_handles)} answers for classification {i}")
                for idx, (h, value) in enumerate(zip(answer_handles, data[ca_key])):
                    h.fill(value)
                    log_function(f"Filled classification answer {idx+1}: {value}")
            next_cq_key = f"classification_question_{i+1}"
            if next_cq_key in data and data[next_cq_key]:
                page.locator('span:has-text("Add Classification Question")').click()
                log_function(f"Added classification question {i+1}")
                for attempt in range(20):
                    new_count = page.locator('textarea[rows="5"]').count()
                    if new_count > count:
                        break
                    time.sleep(0.5)
                time.sleep(1.5)
    log_function(f"Completed {last_idx} classification questions")
    click_forward_arrow(page, log_function)

def wait_for_heading_and_advance(page, target_text, progress_bar, status_text, log_function, do_fill=None, fill_value=None):
    log_function(f"Waiting for '{target_text}' screen")
    status_text.info(f"⏳ Transitioning to {target_text}...")
    for attempt in range(30):
        headings = page.locator('h2')
        for idx in range(headings.count()):
            if target_text.upper() in headings.nth(idx).inner_text().strip().upper():
                log_function(f"Reached {target_text} screen")
                if do_fill and fill_value is not None:
                    page.wait_for_selector('div.ql-editor[contenteditable="true"]', timeout=10000)
                    quill_editor = page.locator('div.ql-editor[contenteditable="true"]').first
                    quill_editor.fill("")
                    time.sleep(0.3)
                    quill_editor.fill(fill_value)
                    log_function(f'Filled: {fill_value}')
                    time.sleep(1.5)
                click_forward_arrow(page, log_function)
                log_function(f"Advanced from {target_text}")
                return
        time.sleep(0.5)
    log_function(f"ERROR: '{target_text}' heading not found")
    click_forward_arrow(page, log_function)

def fill_rating_scale(page, data, progress_bar, status_text, log_function):
    log_function("Waiting for 'RATING SCALE' screen")
    status_text.info("📊 Configuring rating scale...")
    for attempt in range(20):
        headings = page.locator('h2')
        for idx in range(headings.count()):
            if "RATING SCALE" in headings.nth(idx).inner_text().strip().upper():
                log_function("Detected RATING SCALE screen")
                page.wait_for_selector('textarea[rows="5"]', timeout=10000)
                page.locator('textarea[rows="5"]').fill(data["rating_scale_question"])
                log_function(f"Question: {data['rating_scale_question']}")
                dropdown = page.locator('select')
                if dropdown.count() > 0:
                    dropdown.select_option("5")
                    log_function("Set scale to 5 points")
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
                        log_function(f"{rating_key}: {data[rating_key]}")
                    except Exception as e:
                        log_function(f"Could not fill {rating_key}: {e}")
                time.sleep(1.0)
                click_forward_arrow(page, log_function)
                log_function("Advanced from rating scale")
                return
        time.sleep(0.5)
    log_function("ERROR: 'RATING SCALE' screen not found")
    click_forward_arrow(page, log_function)

def fill_final_thoughts(page, data, log_function):
    log_function("Waiting for 'FINAL THOUGHTS' screen")
    for attempt in range(20):
        headings = page.locator('h2')
        found = False
        for idx in range(headings.count()):
            if "FINAL THOUGHTS" in headings.nth(idx).inner_text().strip().upper():
                found = True
                log_function("Detected FINAL THOUGHTS screen")
                break
        if found:
            break
        time.sleep(0.5)
    page.wait_for_selector('textarea[rows="5"]', timeout=5000)
    page.locator('textarea[rows="5"]').fill(data.get("final_thoughts", ""))
    log_function(f"Final thoughts: {data.get('final_thoughts', '')}")
    keyword = data.get("keyword", "")
    page.wait_for_selector('input[placeholder="New keyword"]', timeout=5000)
    kw_input = page.locator('input[placeholder="New keyword"]')
    kw_input.fill(keyword)
    log_function(f"Keyword: {keyword}")
    add_btn = page.locator('button.add-keyword-button:has-text("Add")')
    if add_btn.count() > 0:
        add_btn.first.click()
        log_function("Added keyword")
    else:
        log_function("WARNING: Add button not found")
    time.sleep(1)
    click_forward_arrow(page, log_function)
    log_function("Advanced from final thoughts")

def handle_custom_sample(page, log_function):
    log_function("Selecting custom sample")
    for attempt in range(20):
        option = page.locator('span:has-text("I want a custom sample of respondents from BimiLeap")')
        if option.count() > 0 and option.is_visible():
            option.first.click()
            log_function("Selected custom sample option")
            break
        time.sleep(0.5)
    for attempt in range(20):
        modal_btn = page.locator('button:has-text("Continue")')
        if modal_btn.count() > 0 and modal_btn.is_visible():
            modal_btn.first.click()
            log_function("Clicked CONTINUE in modal")
            break
        time.sleep(0.5)
    time.sleep(1.5)

def handle_done_screen(page, data, progress_bar, status_text, log_function):
    log_function("Handling final screen")
    status_text.info("🎉 Finalizing study...")
    for attempt in range(20):
        headings = page.locator('h2')
        found = False
        for idx in range(headings.count()):
            text = headings.nth(idx).inner_text().strip().upper()
            if "DONE!" in text:
                found = True
                log_function("Detected DONE! screen")
                break
        if found:
            break
        time.sleep(0.5)
    num_respondents = str(data.get("respondents", ""))
    page.wait_for_selector('input[placeholder="Number of respondents"]', timeout=5000)
    page.locator('input[placeholder="Number of respondents"]').fill(num_respondents)
    log_function(f"Respondents: {num_respondents}")
    radio_no = page.locator('input[type="radio"][value="public"]')
    if radio_no.count() > 0:
        radio_no.first.check()
        log_function("Selected 'No' radio button")
    else:
        log_function("WARNING: 'No' radio button not found")
    agree_box = page.locator('input[type="checkbox"]#agree-new')
    if agree_box.count() > 0:
        agree_box.first.check()
        log_function("Checked agreement checkbox")
    else:
        log_function("WARNING: agreement checkbox not found")
    time.sleep(1)
    publish_btn = page.locator('button:has-text("PUBLISH!")')
    if publish_btn.count() > 0 and publish_btn.is_visible():
        publish_btn.first.click()
        log_function("Clicked PUBLISH! button")
    else:
        log_function("WARNING: PUBLISH! button not found")
    log_function("Waiting for publish confirmation...")
    for attempt in range(20):
        popup = page.locator('text=Your study has been published')
        if popup.count() > 0 and popup.is_visible():
            log_function("Publish pop-up detected")
            break
        time.sleep(0.5)
    time.sleep(1.0)
    continue_btn = page.locator('button:has-text("CONTINUE")')
    for attempt in range(10):
        if continue_btn.count() > 0 and continue_btn.is_visible():
            with page.expect_navigation(timeout=7000):
                continue_btn.first.click()
            log_function("Clicked CONTINUE in pop-up")
            break
        time.sleep(0.5)
    log_function("Automation complete")
    progress_bar.progress(100)
    status_text.success("✅ Study published successfully!")

# Main study creation function with UI integration
def create_study_for_user(data, progress_bar, status_text, log_function): 
    USERNAME = "dlovej009@gmail.com"
    PASSWORD = "Dheeraj@2006"
    STUDY_NAME = data["study_name"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Login process
        progress_bar.progress(5)
        status_text.info("🚀 Starting study creation...")
        log_function("Initializing browser")
        
        page.goto("https://www.bimileap.com/")
        log_function("Navigated to homepage")
        
        page.locator("text=Login").click()
        log_function("Clicked Login button")
        
        page.wait_for_selector('input[placeholder="Email"]', timeout=5000)
        page.wait_for_selector('input[type="password"]', timeout=5000)
        page.fill('input[placeholder="Email"]', USERNAME)
        page.fill('input[type="password"]', PASSWORD)
        log_function("Filled credentials")
        
        page.locator("text=SIGN IN").click()
        log_function("Clicked SIGN IN")
        
        progress_bar.progress(15)
        status_text.info("🔐 Logging in...")

        try:
            page.wait_for_url("**/dashboard", timeout=10000)
            progress_bar.progress(25)
            status_text.info("✅ Login successful")
            log_function("Now on dashboard")
            
            page.locator("text=Create New Study").click()
            log_function("Clicked 'Create New Study'")
            
            progress_bar.progress(30)
            status_text.info("📝 Creating study...")
            
            page.wait_for_selector('input[placeholder="My Study"]', timeout=5000)
            page.fill('input[placeholder="My Study"]', STUDY_NAME)
            page.keyboard.press('Tab')
            log_function(f"Study name: {STUDY_NAME}")
            
            page.check('input#agree')
            page.keyboard.press('Tab')
            log_function("Checked agreement box")
            
            time.sleep(1)
            click_forward_arrow(page, log_function)
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
                
            log_function(f"Found {len(fields_to_fill)} question fields")
            questions = [
                data["question_1"],
                data["question_2"],
                data["question_3"],
                data["question_4"]
            ]
            
            for idx, (handle, value) in enumerate(zip(fields_to_fill, questions)):
                try:
                    handle.fill(value)
                    log_function(f"Added question {idx+1}: {value}")
                except Exception as e:
                    log_function(f"Could not fill question {idx+1}: {e}")
                    
            if len(fields_to_fill) < 4:
                log_function("Warning: Fewer than 4 question fields found")
                
            click_forward_arrow(page, log_function)
            
            progress_bar.progress(45)
            status_text.info("📝 Adding answers...")
            
            fill_answers_screen(page, data["question_1_answers"], log_function, "Q1 answers")
            progress_bar.progress(50)
            fill_answers_screen(page, data["question_2_answers"], log_function, "Q2 answers")
            progress_bar.progress(55)
            fill_answers_screen(page, data["question_3_answers"], log_function, "Q3 answers")
            progress_bar.progress(60)
            fill_answers_screen(page, data["question_4_answers"], log_function, "Q4 answers")
            
            progress_bar.progress(65)
            status_text.info("👥 Adding classification questions...")
            fill_classification_questions(page, data, log_function)
            
            progress_bar.progress(70)
            status_text.info("📋 Configuring pre-presentation...")
            wait_for_heading_and_advance(page, "Pre-Presentation", progress_bar, status_text, log_function)
            
            progress_bar.progress(75)
            status_text.info("📝 Adding open-ended questions...")
            wait_for_heading_and_advance(page, "OPEN ENDED QUESTION", progress_bar, status_text, log_function)
            
            progress_bar.progress(80)
            status_text.info("🧭 Setting respondent orientation...")
            wait_for_heading_and_advance(
                page, 
                "RESPONDENT ORIENTATION", 
                progress_bar, 
                status_text, 
                log_function, 
                do_fill=True, 
                fill_value=data.get("respondent_orientation", "")
            )
            
            progress_bar.progress(85)
            fill_rating_scale(page, data, progress_bar, status_text, log_function)
            
            progress_bar.progress(90)
            status_text.info("📊 Configuring post-presentation...")
            wait_for_heading_and_advance(page, "POST-PRESENTATION", progress_bar, status_text, log_function)
            
            progress_bar.progress(92)
            status_text.info("📝 Adding final thoughts...")
            wait_for_heading_and_advance(page, "OPEN ENDED QUESTION", progress_bar, status_text, log_function)
            
            progress_bar.progress(95)
            status_text.info("👥 Selecting respondents...")
            fill_final_thoughts(page, data, log_function)
            
            progress_bar.progress(97)
            status_text.info("🔍 Setting sample...")
            handle_custom_sample(page, log_function)
            
            handle_done_screen(page, data, progress_bar, status_text, log_function)
            
            # Final delay before closing
            time.sleep(3)
            log_function("Study creation completed successfully")
            return True
            
        except Exception as e:
            log_function(f"❌ Error: {str(e)}")
            return False
        finally:
            browser.close()