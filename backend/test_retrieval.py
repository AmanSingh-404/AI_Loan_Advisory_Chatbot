import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from langchain_community.vectorstores import FAISS
from langchain_mistralai import MistralAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

INDEX_DIR = "data/faiss_index"

embeddings = MistralAIEmbeddings(model="mistral-embed")
vectorstore = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)

query = "What is the minimum age for a home loan?"
results = vectorstore.similarity_search(query, k=3)

print(f"Query: {query}\n")
for i, doc in enumerate(results, 1):
    print(f"--- Result {i} (source: {doc.metadata.get('source')}, page: {doc.metadata.get('page')}) ---")
    print(doc.page_content[:300])
    print()