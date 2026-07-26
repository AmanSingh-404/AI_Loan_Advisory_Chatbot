from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import app_graph, add_session_document
from ingest import load_and_chunk_pdf
import tempfile
from fastapi import UploadFile, File, Form
import shutil
import os
import logging
from datetime import datetime

logging.basicConfig(
    filename="chat_logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Silence noisy third-party HTTP logs, keep only our own app logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

app = FastAPI(title="AI Loan Advisory Chatbot API")


allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add your deployed frontend URL once you have it (Step 11.7)
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    is_grounded: bool = True
    answer_type: str = "document"


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
    "session_id": request.session_id,
    "intent": None,
    "calc_params": None,
    "retrieved_docs": [],
    "answer": "",
    "is_grounded": False,
    "sources": [],
    "answer_type": "document",
    "retry_count": 0,
}
        final_state = app_graph.invoke(initial_state)

        logging.info(f"Q: {request.question} | A: {final_state['answer'][:200]} | Grounded: {final_state['is_grounded']}")

        return ChatResponse(
            answer=final_state["answer"],
            sources=final_state["sources"],
            is_grounded=final_state["is_grounded"],
            answer_type=final_state.get("answer_type", "document"),
        )
    except Exception as e:
        logging.exception("Error during chat execution:")
        error_msg = str(e) if str(e) else repr(e)
        raise HTTPException(status_code=500, detail=f"Something went wrong: {error_msg}")

RAW_DOCS_DIR = "data/raw_docs"

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), entity: str = Form(None), session_id: str = Form(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        chunks = load_and_chunk_pdf(tmp_path, file.filename, entity=entity)
        add_session_document(session_id, chunks)

        logging.info(f"SESSION UPLOAD: {file.filename} | session={session_id[:8]}... | entity={entity} | chunks={len(chunks)}")

        return {
            "filename": file.filename,
            "entity": entity or "User Uploaded Document",
            "chunks_added": len(chunks),
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)