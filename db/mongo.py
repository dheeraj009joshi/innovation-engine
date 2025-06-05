from pymongo import MongoClient
import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
def get_db():
    try:
        client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
        client.server_info()
        return client["innovation_engine"]
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        st.stop()
