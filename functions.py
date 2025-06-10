from concurrent.futures import ThreadPoolExecutor
import json
import ast
import os
import threading
import uuid
from azure.storage.blob import BlobServiceClient
import streamlit as st
from typing import List, Dict, Union

def parse_maybe_json_blob(blob: str) -> Union[Dict, List, None]:
    """
    Try to turn `blob` into a Python object:
    - First via json.loads
    - Then, if that fails, via ast.literal_eval
    Returns dict, list, or None if both fail.
    """
    # 1) strip wrapping quotes if it looks doubly quoted
    if blob.startswith('"') and blob.endswith('"'):
        blob = blob[1:-1]

    # 2) try normal JSON
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        pass

    # 3) try literal_eval for Python‐style literals
    try:
        val = ast.literal_eval(blob)
        # if that gives us a str again, try json.loads one more time
        if isinstance(val, str):
            return json.loads(val)
        return val
    except Exception:
        return None

def combine_blobs(raw_blobs: List[str]) -> List[Dict]:
    combined: List[Dict] = []
    for i, blob in enumerate(raw_blobs):
        obj = parse_maybe_json_blob(blob)
        if obj is None:
            print(obj)
            print(f"⚠️ Skipping blob #{i}: not valid JSON or literal")
            continue

        if isinstance(obj, dict):
            combined.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    combined.append(item)
                else:
                    print(f"⚠️ Skipping non‐dict in list from blob #{i}: {item}")
        else:
            print(f"⚠️ Blob #{i} parsed to {type(obj)}, skipping")

    return combined



AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=printxd;AccountKey=CaL/3SmhK8iKVM02i/cIN1VgE3058lyxRnCxeRd2J1k/9Ay6I67GC2CMnW//lJhNl+71WwxYXHnC+AStkbW1Jg==;EndpointSuffix=core.windows.net"
CONTAINER_NAME = "mf2"

def upload_to_azure(file):
    """Upload file to Azure Blob Storage and return URL"""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        blob_name = str(uuid.uuid4()) + "_" + file.name
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
        
        # Reset file pointer to beginning
        file.seek(0)
        blob_client.upload_blob(file.read(), overwrite=True)
        return f"https://printxd.blob.core.windows.net/mf2/{blob_name}"
    except Exception as e:
        st.error(f"Azure upload failed: {str(e)}")
        return None


from scraper.helper import download_tiktok_video, transcribe_with_whisper
from scraper.scraper import ScraperClient


import queue

def get_scraper_data(hashtag, update_queue=None):
    aa = ScraperClient("1J3SttXjxlZIekKgvbX9sgyWtDQm8Zxh")
    hashtag_id = aa.get_hastag_id_by_tag_name(hashtag)
    posts = aa.get_hastag_posts_by_id(hashtag_id, 20)

    def process_post(post, idx):
        try:
            video_file = download_tiktok_video(post["videoUrl"], f"video{idx}")
            post["transcript"] = transcribe_with_whisper(video_file)
            post["comments"] = aa.get_post_comments_by_post_id(post["id"], 100)
            if os.path.exists(f"video{idx}"):
                try:
                    os.remove(f"video{idx}")
                except:
                    pass
        except Exception as error:
            print(error)
            pass
        return post

    augmented_posts = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(process_post, posts, range(len(posts)))
        for processed in results:
            if update_queue:
                update_queue.put((len(augmented_posts) + 1, len(posts)))
            augmented_posts.append(processed)

    return augmented_posts



# aa=get_scraper_data("sleepgood")
# print(aa)


# utils/localstorage.py
# import streamlit as st
# import streamlit.components.v1 as components

# utils/localstorage.py
import streamlit as st
from streamlit_javascript import st_javascript

def save_token(token: str):
    st.session_state.auth_token = token
    js = f'localStorage.setItem("auth_token", "{token}");'
    st_javascript(js)

def read_token():
    if "auth_token" not in st.session_state:
        token = st_javascript('localStorage.getItem("auth_token");')
        if token and token != "null":
            st.session_state.auth_token = token

def clear_token():
    if "auth_token" in st.session_state:
        del st.session_state.auth_token
    st_javascript('localStorage.removeItem("auth_token");')










def inject_custom_css():
    st.markdown("""
    <style>
                @import url('https://fonts.googleapis.com/css2?family=Anek+Devanagari:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Anek Devanagari', sans-serif !important;
    }
        .main {
            max-width: 1200px;
            padding: 2rem;
        }
        .auth-container {
            max-width: 400px;
            margin: 2rem auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .project-card {
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            transition: transform 0.2s;
        }
        .project-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .wizard-step {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            background: #f0f5f9;
            border: 1px solid #dee2e6;
        }
        .step-completed {
            background: #e8f5e9;
            border-color: #4caf50;
        }
        .step-current {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        .progress-bar {
            height: 8px;
            border-radius: 4px;
            background: #e0e0e0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: #4caf50;
            transition: width 0.3s ease;
        }
        .project-icon {
            font-size: 1.8rem;
            margin-right: 1rem;
        }
        .project-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            background: #e3f2fd;
            color: #2196f3;
        }
        .digester-box {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: white;
        }
        /* NEW STYLES */
        .nav-button {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid #eee;
        }
        .status-badge {
            padding: 0.3rem 0.7rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .status-ready {
            background: #e8f5e9;
            color: #2e7d32;
        }
        .status-waiting {
            background: #fff8e1;
            color: #f57f17;
        }
        .section-header {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-bottom: 1.5rem;
        }
        .section-header h2 {
            margin-bottom: 0;
        }
        .step-container {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
        }
        .file-upload-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .file-upload-box {
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s;
            background: #fafafa;
        }
        .file-upload-box:hover {
            border-color: #2196f3;
            background: #f0f9ff;
        }
        .idea-card {
            border-left: 4px solid #2196f3;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            background: white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        .idea-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .generation-selector {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }
        .generation-btn {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            background: #e3f2fd;
            color: #2196f3;
            border: none;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 500;
        }
        .generation-btn.active {
            background: #2196f3;
            color: white;
        }
        .generation-btn:hover:not(.active) {
            background: #bbdefb;
        }
        .file-status {
            padding: 0.5rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            background: #f0f9ff;
            border-left: 4px solid #2196f3;
        }
        .file-status-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .file-status-title {
            font-weight: 600;
            color: #1565c0;
        }
        .file-status-content {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .file-tag {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            background: #e3f2fd;
            color: #0d47a1;
            font-size: 0.85rem;
        }
        .no-files {
            color: #757575;
            font-style: italic;
        }
        .research-content {
            padding: 1rem;
            background: #f5f5f5;
            border-radius: 8px;
            border-left: 4px solid #4caf50;
            margin-top: 0.5rem;
        }
    details summary {
            font-size: 2.25rem ;
            font-weight: 600 ;
            padding: 0.5rem ;
        }


    </style>
    """, unsafe_allow_html=True)
