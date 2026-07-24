# LoanSense AI — AI Loan Advisory Chatbot

LoanSense AI is a retrieval-augmented generation (RAG) chatbot that answers loan-related questions using only the content of documents it has been given, such as loan policy PDFs, terms and conditions, and regulatory circulars. Every answer is either traced back to a specific source document or explicitly declined when the information is not available, rather than guessed or inferred from general knowledge.

Live application: https://ai-loan-advisory-chatbot-chi.vercel.app

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [Repository Structure](#repository-structure)
6. [Local Setup](#local-setup)
7. [Environment Variables](#environment-variables)
8. [Dataset](#dataset)
9. [Privacy and Data Handling](#privacy-and-data-handling)
10. [Session-Scoped Document Uploads](#session-scoped-document-uploads)
11. [Deployment](#deployment)
12. [Known Limitations](#known-limitations)
13. [Challenges Encountered During Development](#challenges-encountered-during-development)
14. [Possible Future Improvements](#possible-future-improvements)

---

## Problem Statement

Loan-related documents such as bank policies, terms and conditions, and regulatory circulars are often long, technical, and difficult for an average user to interpret. Manually searching such documents for specific answers, for example on eligibility, EMI rules, or pre-payment charges, is time-consuming and error-prone.

LoanSense AI addresses this by allowing a user to ask a question in natural language and receive a response generated strictly from the relevant sections of the loaded documents. If no loaded document addresses the question, the system states this explicitly instead of producing an unsupported answer.

## Key Features

- Natural language question answering over loan-related PDF documents.
- Retrieval-augmented generation pipeline built with LangChain and orchestrated with LangGraph.
- A validation step that checks whether a generated answer is actually supported by the retrieved context before it is shown to the user, with an automatic retry if it is not.
- Explicit citation of the source document for every grounded answer.
- Explicit refusal ("I do not have that information in the documents provided") when a question cannot be answered from the loaded documents, rather than a fabricated response.
- Ability for a user to upload an additional PDF document during their session and immediately ask questions about it.
- Session-scoped isolation of uploaded documents, so that a document uploaded by one user is not visible to any other user or session.
- A distinct landing page and chat interface, both deployed and publicly accessible.

## Architecture

The system follows a standard retrieve-generate-validate RAG pattern, implemented as a LangGraph state machine:

```
User question
     |
     v
Retrieve   -- similarity search against the base document index
     |         and, if present, the current session's uploaded documents
     v
Generate   -- the language model answers using only the retrieved context
     |
     v
Validate   -- the language model checks whether the answer is supported
     |         by the retrieved context
     v
   Grounded?  -- No, and retries remain --> back to Retrieve with the same query
     |
    Yes (or retries exhausted)
     |
     v
Final answer, with source citation or explicit refusal
```

At startup, the backend loads a permanent, shared FAISS vector index built from a fixed set of loan documents. Documents uploaded by a user during a session are embedded and stored in a separate, in-memory vector index scoped to that session only. Retrieval for a given question searches the shared index and, if applicable, the requesting session's private index, and merges the results before generation.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite), React Router |
| Backend API | FastAPI |
| Orchestration | LangGraph |
| RAG components | LangChain (document loaders, text splitting, vector store integration) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2), run locally |
| Vector store | FAISS |
| Language model | Groq API (Llama 3.3 70B) |
| Backend hosting | Railway |
| Frontend hosting | Vercel |

## Repository Structure

```
AI_Loan_Advisory_Chatbot/
├── backend/
│   ├── data/
│   │   ├── raw_docs/          Source PDF documents (shared base knowledge)
│   │   └── faiss_index/       Generated vector index (not committed to source control)
│   ├── ingest.py               Document loading, chunking, and index construction
│   ├── graph.py                LangGraph pipeline: retrieve, generate, validate nodes
│   ├── main.py                 FastAPI application and API endpoints
│   ├── requirements.txt
│   ├── runtime.txt
│   └── start.sh                Deployment startup script
└── frontend/
    ├── src/
    │   ├── LandingPage.jsx
    │   ├── ChatPage.jsx
    │   └── App.jsx              Application router
    └── package.json
```

## Local Setup

### Prerequisites

- Python 3.13
- Node.js 18 or later
- A Groq API key (https://console.groq.com)

### Backend

```
cd backend
python -m venv venv
venv\Scripts\Activate.ps1        (Windows PowerShell)
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` containing:

```
GROQ_API_KEY=your_key_here
```

Build the document index and start the API server:

```
python ingest.py
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive documentation is available at `http://127.0.0.1:8000/docs`.

### Frontend

```
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:5173`.

## Environment Variables

| Variable | Location | Purpose |
|---|---|---|
| `GROQ_API_KEY` | Backend | Authenticates requests to the Groq language model API |
| `FRONTEND_URL` | Backend | Adds the deployed frontend origin to the CORS allow-list |

## Dataset

The base knowledge set consists of four documents:

1. A general home loan comparison and advisory article covering eligibility, interest rates, and tax benefits.
2. SBI Personal Loan — Most Important Terms and Conditions.
3. Standard Chartered Bank Personal Loan — Most Important Terms and Conditions.
4. A Reserve Bank of India circular on pre-payment charges on loans.

The fourth document is explicitly marked "Withdrawn" by the issuing authority. It is retained in the dataset intentionally, as a test of whether the system can be asked about the standing of a document as well as its content, and to demonstrate that regulatory documents can become superseded over time. Its content should not be treated as a currently applicable regulation.

As permitted by the project brief, this dataset was assembled from a combination of publicly available documents.

## Privacy and Data Handling

The system is designed so that no more information than necessary is sent to any external service:

- Full source documents are never transmitted to the language model. Only the small number of retrieved text passages (chunks) relevant to a specific question are included in any request to the language model provider.
- Document embeddings are generated locally using an open-source model; no document content is sent to a third party for the purpose of embedding.
- The system logs, locally, only the text of a question, a truncated form of the answer, and whether the answer was judged grounded. No personal identifying information is collected or required to use the system.

## Session-Scoped Document Uploads

An earlier version of the upload feature added uploaded documents directly to the shared, permanent index, making them visible to every user of the system. This was identified during testing as a privacy issue: any document uploaded by one user, including personal documents such as a resume, could be queried by any other user.

This was corrected by separating the shared base index from a per-session, in-memory index:

- A random session identifier is generated in the browser and sent with every request.
- Documents uploaded in a given session are embedded and added only to that session's private, in-memory vector store.
- Retrieval for a question searches the shared base index and, if the requesting session has uploaded documents, that session's private index, merging the results.
- A session's uploaded documents are never written to disk and are discarded when the backend process restarts.

This was verified by uploading a document in one browser session and confirming, in a separate incognito session, that the system correctly reports no knowledge of that document.

## Deployment

The backend is deployed on Railway as a persistent Python process. The frontend is deployed on Vercel as a static Vite build. On deployment, the backend rebuilds its base FAISS index from the source PDF documents at startup, since the generated index files are not committed to source control.

## Known Limitations

- The free hosting tier used for the backend may pause the service after a period of inactivity, resulting in a slower first response after idle periods.
- Session-scoped uploaded documents are held only in server memory. A backend restart clears all sessions' uploaded documents; the shared base document set is unaffected.
- Retrieval is based on semantic similarity between the question and document text. Questions that are topically close to an unrelated document, but not actually answered by it, can occasionally cause the correct document to be retrieved alongside irrelevant material. This was observed and mitigated during development (see below) but is not eliminated in principle.
- The system currently supports PDF documents only.
- The application is intended as an advisory and informational tool and does not constitute financial or legal advice.

## Challenges Encountered During Development

The following issues were identified and resolved during the course of building this system, and are documented here as they reflect meaningful design and debugging decisions rather than incidental bugs.

**Cross-document misattribution.** In early testing, the system correctly retrieved relevant passages from two different documents but combined facts from both into a single statement attributed to the wrong entity, for example applying a rule from a Reserve Bank of India circular to a specific bank's product without that bank's own document supporting the claim. Both the answer-generation prompt and the validation prompt were revised to explicitly prohibit combining or attributing rules across unrelated source documents, and to require that differing rules from different sources be presented separately.

**Entity-retrieval gap.** A related issue was found where a question about a specific bank's product retrieved passages that were topically similar but did not explicitly mention that bank, causing the system to decline to answer despite the correct information being present elsewhere in the same document. This was resolved by tagging each ingested chunk with its source entity at ingestion time and embedding that entity tag directly in the indexed text, rather than storing it only as metadata, so that retrieval could match on it directly.

**Shared-index privacy gap.** The initial document upload feature added new documents to the same permanent, shared index used by all users, meaning one user's uploaded document could be queried by any other user. This was corrected by introducing per-session, in-memory vector stores, as described above.

**Dependency resolution during deployment.** The project's local development environment had accumulated an inconsistent set of installed package versions over time, which functioned locally but failed during a clean install on a deployment platform due to incompatible version constraints between LangChain and LangGraph packages. This was resolved by removing unnecessary version pins and allowing the package manager to resolve a mutually compatible set of versions.

**Deployment startup ordering.** The deployed backend requires a vector index that is not committed to source control and must be built at startup. An initial deployment configuration using a chained shell command did not reliably execute the index-building step before starting the API server, causing the application to fail because the index file did not yet exist. This was resolved by introducing an explicit startup script that performs the two steps sequentially and unambiguously.

## Possible Future Improvements

- Persist session-scoped uploads to a lightweight per-user data store rather than server memory, so that uploaded documents survive a backend restart without being exposed to other users.
- Support additional document formats, including scanned PDFs via OCR.
- Restrict the sources shown alongside an answer to only those explicitly cited in the generated text, rather than all documents retrieved during the search step.
- Add user accounts to allow uploaded documents to persist across sessions for a returning user, with appropriate access control.