import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_mistralai import MistralAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

RAW_DOCS_DIR = "data/raw_docs"
INDEX_DIR = "data/faiss_index"

ENTITY_MAP = {
    "1343212208682_PERSONAL_LOAN_MITC_JUL_12.pdf": "SBI",
    "in-personal-loan-most-imp-tnc.pdf": "Standard Chartered Bank",
    "Bank_Home_Loans_consumer_products.pdf": "General/Comparative (multiple banks)",
    "NT642A32A71F06D649B78A9622FB82B8C438.pdf": "RBI (Reserve Bank of India) - NOTE: this circular is marked WITHDRAWN",
}

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = MistralAIEmbeddings(model="mistral-embed")
    return _embeddings


def load_and_chunk_pdf(filepath, filename, entity=None):
    """Load a single PDF, tag it with entity info, and split into chunks."""
    entity = entity or ENTITY_MAP.get(filename, "User Uploaded Document")

    loader = PyPDFLoader(filepath)
    docs = loader.load()
    for doc in docs:
        doc.metadata["source"] = filename
        doc.metadata["entity"] = entity
        doc.page_content = f"[{entity}] {doc.page_content}"

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    return chunks


def load_all_documents():
    all_docs = []
    for filename in os.listdir(RAW_DOCS_DIR):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(RAW_DOCS_DIR, filename)
            print(f"Loading: {filename}")
            chunks = load_and_chunk_pdf(filepath, filename)
            all_docs.extend(chunks)
    return all_docs


def build_index_from_scratch():
    chunks = load_all_documents()
    print(f"Split into {len(chunks)} chunks")

    embeddings = get_embeddings()
    print("Building FAISS index...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(INDEX_DIR, exist_ok=True)
    vectorstore.save_local(INDEX_DIR)
    print(f"Index saved to {INDEX_DIR}")
    return vectorstore


def add_document_to_index(filepath, filename, entity=None):
    """Add a single new PDF to the EXISTING saved index (used by the /upload endpoint)."""
    chunks = load_and_chunk_pdf(filepath, filename, entity=entity)

    embeddings = get_embeddings()
    vectorstore = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    vectorstore.add_documents(chunks)
    vectorstore.save_local(INDEX_DIR)

    return len(chunks)


if __name__ == "__main__":
    build_index_from_scratch()
    print("\n Ingestion complete!")