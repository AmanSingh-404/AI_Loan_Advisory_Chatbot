import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

RAW_DOCS_DIR = "data/raw_docs"
INDEX_DIR = "data/faiss_index"

def load_documents():
    all_docs = []
    for filename in os.listdir(RAW_DOCS_DIR):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(RAW_DOCS_DIR, filename)
            print(f"Loading: {filename}")
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            # Attach clean source filename to metadata for later citation
            ENTITY_MAP = {
    "1343212208682_PERSONAL_LOAN_MITC_JUL_12.pdf": "SBI",
    "in-personal-loan-most-imp-tnc.pdf": "Standard Chartered Bank",
    "Bank_Home_Loans_consumer_products.pdf": "General/Comparative (multiple banks)",
    "NT642A32A71F06D649B78A9622FB82B8C438.pdf": "RBI (Reserve Bank of India) - NOTE: this circular is marked WITHDRAWN",
}

            for doc in docs:
                entity = ENTITY_MAP.get(filename, "Unknown")
                doc.metadata["source"] = filename
                doc.metadata["entity"] = entity
                doc.page_content = f"[{entity}] {doc.page_content}"
            all_docs.extend(docs)

    return all_docs

def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    return chunks

def build_and_save_index(chunks):
    print("Loading embedding model (first run downloads it, may take a minute)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("Building FAISS index...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(INDEX_DIR, exist_ok=True)
    vectorstore.save_local(INDEX_DIR)
    print(f"Index saved to {INDEX_DIR}")

if __name__ == "__main__":
    documents = load_documents()
    print(f"Loaded {len(documents)} pages total")

    chunks = chunk_documents(documents)
    build_and_save_index(chunks)

    print("\n Ingestion complete!")