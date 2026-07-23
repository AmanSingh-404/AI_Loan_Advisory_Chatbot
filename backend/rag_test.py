import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_mistralai import MistralAIEmbeddings
from mistralai.client import Mistral

load_dotenv()

INDEX_DIR = "data/faiss_index"
MISTRAL_MODEL = "mistral-large-latest"

# --- Load vector store ---
embeddings = MistralAIEmbeddings(model="mistral-embed")
vectorstore = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)

# --- Set up Mistral client ---
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

PROMPT_TEMPLATE = """You are a loan advisory assistant. Answer the question using ONLY the context below.
If the answer is not in the context, say "I don't have that information in the documents provided" — do not guess or use outside knowledge.
Always mention which source document your answer comes from.

Context:
{context}

Question: {question}

Answer:"""

def answer_question(question, k=4):
    # Retrieve
    results = vectorstore.similarity_search(question, k=k)
    context = "\n\n".join(
        f"[Source: {doc.metadata.get('source')}]\n{doc.page_content}"
        for doc in results
    )

    # Generate
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response.choices[0].message.content

    sources = list(set(doc.metadata.get("source") for doc in results))
    return answer, sources

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    test_questions = [
        "What is the minimum age for a home loan?",
        "Is there a pre-payment penalty on SBI personal loans?",
        "What is the current repo rate set by RBI?",  # edge case - not in docs
    ]

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        answer, sources = answer_question(q)
        print(f"A: {answer}")
        print(f"Sources: {sources}")