import streamlit as st
import pdfplumber
import docx2txt
from utils.embedding_handler import embed_chunks, search_faiss_index

def upload_section():
    st.header("📁 Upload RND & marketing Files")
    project_name = st.text_input("Enter Project ID", key="project_input")

    if not project_name:
        st.warning("Please enter a project name.")
        return

    uploaded_rnd = st.file_uploader("Upload RND Files", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    uploaded_marketing = st.file_uploader("Upload marketing Files", type=["pdf", "docx", "txt"], accept_multiple_files=True)

    if st.button("Submit Files"):
        all_chunks = []
        all_text_chunks = []
        all_metadata = []

        with st.status("Processing files...", expanded=True) as status:
            for f in uploaded_rnd:
                text = extract_text_from_file(f)
                chunks = basic_chunk_text(text)
                all_chunks.append({"filename": f.name, "category": "rnd", "chunks": chunks})
                st.write(f"✅ Extracted + chunked RND: {f.name} → {len(chunks)} chunks")

            for f in uploaded_marketing:
                text = extract_text_from_file(f)
                chunks = basic_chunk_text(text)
                all_chunks.append({"filename": f.name, "category": "marketing", "chunks": chunks})
                st.write(f"✅ Extracted + chunked marketing: {f.name} → {len(chunks)} chunks")

            for item in all_chunks:
                for chunk in item["chunks"]:
                    all_text_chunks.append(chunk)
                    all_metadata.append({
                        "filename": item["filename"],
                        "category": item["category"],
                        "project": project_name
                    })

            st.write("🔄 Generating embeddings with OpenAI...")
            faiss_index = embed_chunks(all_text_chunks, all_metadata)
            st.success("✅ Embedding complete. FAISS index created.")

        st.subheader("📄 Chunked Preview")
        for file in all_chunks:
            with st.expander(f"{file['category'].upper()} – {file['filename']} ({len(file['chunks'])} chunks)"):
                for i, chunk in enumerate(file["chunks"]):
                    st.markdown(f"**Chunk {i+1}:**")
                    st.text(chunk)

        
def extract_text_from_file(file):
    if file.name.endswith(".pdf"):
        return extract_pdf_text(file)
    elif file.name.endswith(".docx"):
        return docx2txt.process(file)
    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")
    else:
        return "Unsupported file type"


def extract_pdf_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def basic_chunk_text(text, max_chars=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start += max_chars - overlap
    return chunks
