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
        st.title(":(")
        st.error(f"Your internet connection is not stable ")
        st.error(f"Detailed error : {e}")
        st.stop()
