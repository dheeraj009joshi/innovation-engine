import os
import faiss
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
embedder = OpenAIEmbeddings(openai_api_key=openai_key)

def embed_chunks(chunks, metadata_list=None):
    docs = []
    for i, chunk in enumerate(chunks):
        metadata = metadata_list[i] if metadata_list else {}
        docs.append(Document(page_content=chunk, metadata=metadata))
    return FAISS.from_documents(docs, embedder)

def search_faiss_index(index, query, k=5):
    return index.similarity_search(query, k=k)
