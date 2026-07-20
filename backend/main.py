from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import app_graph

app = FastAPI(title="AI Loan Advisory Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    is_grounded: bool = True


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        initial_state = {
            "question": request.question,
            "retrieved_docs": [],
            "answer": "",
            "is_grounded": False,
            "sources": [],
            "retry_count": 0,
        }
        final_state = app_graph.invoke(initial_state)

        return ChatResponse(
            answer=final_state["answer"],
            sources=final_state["sources"],
            is_grounded=final_state["is_grounded"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")