"""
FastAPI Main Application Initialization for Enterprise Contract RAG Backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import AppConfig, setup_logger
from app.api.auth import router as auth_router
from app.api.contracts import router as contracts_router
from app.api.rag import router as rag_router
from app.api.overview import router as overview_router
from app.api.suppliers import router as suppliers_router
from app.api.audit import router as audit_router
from app.vector_store.pinecone_store import vector_store
from app.db.supabase import supabase_db

logger = setup_logger("main_app")

def create_app() -> FastAPI:
    """Builds and configures the unified FastAPI backend application."""
    app = FastAPI(
        title="Enterprise Contract Storage & RAG API",
        description="Unified backend service for storing company contracts and performing grounded legal RAG Q&A using Supabase & Pinecone.",
        version="2.0.0",
        docs_url=None,
        redoc_url=None
    )

    # 1. Enable CORS for Next.js Frontend
    cors_origins = AppConfig.get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Include Routers
    app.include_router(auth_router)
    app.include_router(overview_router)
    app.include_router(contracts_router)
    app.include_router(rag_router)
    app.include_router(suppliers_router)
    app.include_router(audit_router)

    # 3. System Status Endpoint
    @app.get("/", tags=["System Status"])
    async def system_status():
        return {
            "status": "online",
            "service": "Enterprise Contract Storage & RAG Backend",
            "version": "2.0.0",
            "integrations": {
                "supabase_configured": supabase_db.is_configured(),
                "pinecone_enabled": vector_store.use_pinecone,
                "vector_store_type": "Pinecone Vector Store" if vector_store.use_pinecone else "Local Persistent Vector Index",
                "indexed_chunks": len(vector_store.chunks_db)
            }
        }

    @app.on_event("startup")
    async def startup_event():
        """Auto-index stored contracts into vector store if not yet indexed."""
        try:
            from app.ingestion.contract_processor import contract_processor
            from app.rag.generator import get_openrouter_embedding_client
            
            storage_dir = AppConfig.CONTRACT_STORAGE_DIR
            if storage_dir.exists():
                for contract_file in storage_dir.glob("*"):
                    if contract_file.suffix.lower() in (".pdf", ".docx", ".txt") and contract_file.is_file():
                        logger.info(f"Checking startup indexing for contract file: {contract_file.name}")
                        chunks = contract_processor.process_file(contract_file)
                        if chunks:
                            client = get_openrouter_embedding_client()
                            vector_store.add_contract_chunks(chunks, client)
                            logger.info(f"Startup indexed {len(chunks)} chunks for {contract_file.name}")
        except Exception as e:
            logger.error(f"Startup indexing error: {e}")

    return app

app = create_app()
