# Enterprise Contract Storage & RAG Backend

A clean, production-ready backend service for corporate contract management and retrieval-augmented generation (RAG) Q&A. Powered by **Supabase** (Authentication and User/Contract Metadata) and **Pinecone Vector Database** (Vector Similarity Indexing & Search with Local Embedded Engine Fallback).

---

## 🏛️ Architecture Overview

```
backend/
├── .env                        # Local environment secrets (OpenAI, Supabase, Pinecone)
├── .env.example                # Template for environment variables
├── main.py                     # Entry point (Starts FastAPI server or CLI mode)
├── requirements.txt            # Python dependencies
├── schema.sql                  # Supabase PostgreSQL schema for auth profiles & roles
├── app/                        # Main Application Package
│   ├── config.py               # Centralized configuration & environment loader
│   ├── main_app.py             # FastAPI app builder with CORS & route registration
│   ├── api/                    # REST API Endpoints
│   │   ├── auth.py             # User & Admin Signup, Login, Profile endpoints
│   │   ├── contracts.py        # Contract PDF/DOCX/TXT upload, listing, and deletion
│   │   └── rag.py              # Grounded Contract Q&A and SSE Streaming endpoints
│   ├── db/                     # Relational Storage & Auth
│   │   └── supabase.py         # Supabase Auth client & profile manager
│   ├── vector_store/           # Vector Search Engine
│   │   └── pinecone_store.py   # Pinecone Vector Store + Local Vector Engine fallback
│   ├── ingestion/              # Ingestion Pipeline
│   │   └── contract_processor.py # PDF/DOCX/TXT text parser, cleaner & token-aware chunker
│   └── rag/                    # RAG Logic Engine
│       ├── prompt_templates.py   # Strict contract-grounded legal system prompts
│       ├── retriever.py          # Vector retrieval & keyword reranking
│       └── generator.py          # Grounded answer synthesis, citations, streaming & token history budget
└── data/                       # Local File Storage
    └── contracts/              # Storage directory for uploaded contracts & vector index
```

---

## 🚀 Key Features

1. **Supabase Integration**:
   - Authentication for standard users and corporate administrators (`/api/auth/signup`, `/api/auth/login`, `/api/auth/admin/login`, `/api/auth/me`).
   - Profile management and role-based access control.

2. **Pinecone Vector Storage & Dual-Mode Search**:
   - Vector indexing in Pinecone Serverless Index with metadata filters (contract ID, title, section name).
   - Seamless **local persistent vector store fallback** (`data/contracts/vector_store.json`) when Pinecone credentials are not configured, enabling zero-setup local testing.

3. **Contract Document Processing Pipeline**:
   - Ingestion for `.pdf`, `.docx`, `.txt`, and `.md` contract files.
   - Text cleaning: strips noise, headers/footers, and page numbers.
   - Token-aware semantic chunking with customizable clause headings and overlap.

4. **Strictly Grounded RAG & Citation Engine**:
   - Prevents hallucinations by forcing answers to be grounded strictly in retrieved contract clauses.
   - Generates explicit inline citations referencing the contract title, section name, and chunk ID.
   - History management with token threshold trimming.
   - Token streaming output via Server-Sent Events (SSE).

5. **Unified Entry Point (`main.py`)**:
   - Running `python main.py` starts the server on `http://127.0.0.1:8000`.
   - Running `python main.py --cli` launches an interactive terminal client for quick contract testing.

---

## 💻 Quick Start

### 1. Install Dependencies

Ensure Python 3.10+ is installed:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

Key environment settings:
- `OPENAI_API_KEY`: OpenAI or Groq API key for embeddings and answer generation.
- `SUPABASE_URL` & `SUPABASE_ANON_KEY`: Supabase project credentials.
- `PINECONE_API_KEY`: Pinecone vector database key (Optional: leave empty to use built-in local vector index).

### 3. Run the Backend

Launch the FastAPI web server:

```bash
python main.py
```

API documentation will be available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

Alternatively, run in CLI interactive mode:

```bash
python main.py --cli
```

---

## 📡 API Reference

### Authentication (`/api/auth`)
- `POST /api/auth/signup`: Register a new corporate user.
- `POST /api/auth/login`: User authentication.
- `POST /api/auth/admin/login`: Admin authentication.
- `GET /api/auth/me`: Fetch authenticated user profile.

### Contract Management (`/api/contracts`)
- `POST /api/contracts/upload`: Upload contract file (`.pdf`, `.docx`, `.txt`) -> automatically parsed, chunked, and indexed.
- `GET /api/contracts/list`: List all stored corporate contracts.
- `DELETE /api/contracts/{contract_id}`: Remove contract and vectors.

### RAG Q&A (`/api/query`)
- `POST /api/query`: Ask question about stored contracts -> returns answer with citations.
- `POST /api/query/stream`: SSE token streaming endpoint.
- `GET /api/query/stream`: SSE GET token streaming endpoint.
