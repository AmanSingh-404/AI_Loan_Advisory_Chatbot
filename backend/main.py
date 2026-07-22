from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import app_graph, reload_vectorstore
from ingest import add_document_to_index
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

        logging.info(f"Q: {request.question} | A: {final_state['answer'][:200]} | Grounded: {final_state['is_grounded']}")

        return ChatResponse(
            answer=final_state["answer"],
            sources=final_state["sources"],
            is_grounded=final_state["is_grounded"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")

RAW_DOCS_DIR = "data/raw_docs"

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), entity: str = Form(None)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    os.makedirs(RAW_DOCS_DIR, exist_ok=True)
    save_path = os.path.join(RAW_DOCS_DIR, file.filename)

    if os.path.exists(save_path):
        raise HTTPException(status_code=400, detail="A file with this name already exists")

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        chunk_count = add_document_to_index(save_path, file.filename, entity=entity)
        reload_vectorstore()

        logging.info(f"UPLOAD: {file.filename} | entity={entity} | chunks={chunk_count}")

        return {
            "filename": file.filename,
            "entity": entity or "User Uploaded Document",
            "chunks_added": chunk_count,
            "status": "success",
        }
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")