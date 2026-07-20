import os
import time
from typing import TypedDict, List, Optional
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from groq import Groq
from langgraph.graph import StateGraph, END

load_dotenv()

INDEX_DIR = "data/faiss_index"
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 2

# --- Shared resources (loaded once) ---
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def call_llm_with_retry(messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(model=GROQ_MODEL, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

# --- State definition ---
class GraphState(TypedDict):
    question: str
    retrieved_docs: List[dict]
    answer: str
    is_grounded: bool
    sources: List[str]
    retry_count: int


# --- Node 1: Retrieve ---
def retrieve_node(state: GraphState) -> GraphState:
    query = state["question"]
    results = vectorstore.similarity_search(query, k=4)
    retrieved_docs = [
        {"content": doc.page_content, "source": doc.metadata.get("source")}
        for doc in results
    ]
    return {**state, "retrieved_docs": retrieved_docs}


# --- Node 2: Generate ---
GENERATE_PROMPT = """You are a loan advisory assistant. Answer the question using ONLY the context below.

STRICT RULES:
- If the answer is not in the context, say "I don't have that information in the documents provided" — do not guess or use outside knowledge.
- Each piece of context is labeled with its source document. Do NOT mix or combine rules from different source documents into a single statement unless the question explicitly asks you to compare them.
- If different source documents contain different or seemingly conflicting rules, mention each source separately and attribute each rule to its specific document by name.
- Never imply a rule from one document (e.g., an RBI circular) applies to a specific bank's product (e.g., SBI) unless that exact document states so.

Context:
{context}

Question: {question}

Answer:"""

def generate_node(state: GraphState) -> GraphState:
    context = "\n\n".join(
        f"[Source: {d['source']}]\n{d['content']}" for d in state["retrieved_docs"]
    )
    prompt = GENERATE_PROMPT.format(context=context, question=state["question"])
    answer = call_llm_with_retry([{"role": "user", "content": prompt}])
    return {**state, "answer": answer}


# --- Node 3: Validate (LLM self-check) ---
VALIDATE_PROMPT = """You are a strict fact-checker. Given the CONTEXT and the ANSWER below, determine if the ANSWER is fully supported by the CONTEXT.

Rules:
- If the answer says "I don't have that information", that always counts as GROUNDED (it's correctly refusing).
- If the answer states any fact, number, or rule not present in the context, that is NOT grounded.
- If the answer attributes a rule from one source document to a DIFFERENT, unrelated entity (e.g., applying an RBI circular's rule to a specific bank's product without that bank's own document stating it), that is NOT grounded — this counts as misattribution even if both facts individually appear somewhere in the context.

Context:
{context}

Answer:
{answer}

Respond with ONLY one word: "GROUNDED" or "NOT_GROUNDED"."""

def validate_node(state: GraphState) -> GraphState:
    context = "\n\n".join(d["content"] for d in state["retrieved_docs"])
    prompt = VALIDATE_PROMPT.format(context=context, answer=state["answer"])
    verdict = call_llm_with_retry([{"role": "user", "content": prompt}]).strip().upper()
    is_grounded = "NOT_GROUNDED" not in verdict

    is_refusal = "don't have that information" in state["answer"].lower()

    if is_grounded and not is_refusal:
        sources = list(set(d["source"] for d in state["retrieved_docs"]))
    else:
        sources = []

    return {**state, "is_grounded": is_grounded, "sources": sources}


# --- Node 4: Refine (bump retry count before looping back) ---
def refine_node(state: GraphState) -> GraphState:
    return {**state, "retry_count": state["retry_count"] + 1}


# --- Conditional edge logic ---
def route_after_validation(state: GraphState) -> str:
    if state["is_grounded"]:
        return "end"
    if state["retry_count"] < MAX_RETRIES:
        return "retry"
    return "end"  # give up after max retries, return best-effort answer


# --- Build the graph ---
def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("validate", validate_node)
    graph.add_node("refine", refine_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "validate")

    graph.add_conditional_edges(
        "validate",
        route_after_validation,
        {"retry": "refine", "end": END},
    )
    graph.add_edge("refine", "retrieve")

    return graph.compile()


app_graph = build_graph()


if __name__ == "__main__":
    test_questions = [
        "What is the minimum age for a home loan?",
        "What is the current repo rate set by RBI?",
    ]

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        initial_state = {
            "question": q,
            "retrieved_docs": [],
            "answer": "",
            "is_grounded": False,
            "sources": [],
            "retry_count": 0,
        }
        final_state = app_graph.invoke(initial_state)
        print(f"A: {final_state['answer']}")
        print(f"Grounded: {final_state['is_grounded']}")
        print(f"Sources: {final_state['sources']}")
        print(f"Retries used: {final_state['retry_count']}")