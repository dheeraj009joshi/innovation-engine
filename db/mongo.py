from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["agentic_ai"]

def save_project(project_name, categories):
    db.projects.insert_one({
        "project_name": project_name,
        "categories": categories
    })

def save_file_metadata(project_name, filename, category, azure_url):
    db.files.insert_one({
        "project_name": project_name,
        "filename": filename,
        "category": category,
        "azure_url": azure_url
    })
