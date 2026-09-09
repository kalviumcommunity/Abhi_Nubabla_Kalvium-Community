#!/usr/bin/env python3
"""
RAG Pipeline REST API Backend.

Provides a FastAPI endpoint for querying the RAG pipeline with structured request/response models,
input validation, error handling, and configuration management via environment variables.

Usage:
    python -m src.api
    or
    uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add project root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.rag_pipeline import run_rag_pipeline
from src.similarity_search import VectorStoreRetriever

# ============================================================================
# Configuration Loading from Environment Variables
# ============================================================================

load_dotenv()

class APIConfig:
    """Load and validate API configuration from environment variables."""
    
    # LLM Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
    
    # Vector Store Configuration
    vector_store_path: str = os.getenv("VECTOR_STORE_PATH", "data/embedded_chunks.json")
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "3"))
    retrieval_score_threshold: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.0"))
    
    # API Server Configuration
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_reload: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    api_workers: int = int(os.getenv("API_WORKERS", "1"))
    
    # CORS Configuration
    cors_origins: List[str] = json.loads(
        os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:8000"]')
    )
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Token Limits
    max_context_tokens: int = int(os.getenv("MAX_CONTEXT_TOKENS", "1500"))
    max_answer_tokens: int = int(os.getenv("MAX_ANSWER_TOKENS", "250"))
    answer_temperature: float = float(os.getenv("ANSWER_TEMPERATURE", "0.2"))


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure logging for the API."""
    logger = logging.getLogger("rag_api")
    logger.setLevel(getattr(logging, log_level))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


logger = setup_logging(APIConfig.log_level)

# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for RAG pipeline query endpoint."""
    
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User question to query the RAG pipeline",
        example="What are the password requirements?"
    )
    
    k: Optional[int] = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of chunks to retrieve (1-20)",
        example=3
    )
    
    score_threshold: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold (0.0-1.0)",
        example=0.0
    )
    
    metadata_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filter for retrieval",
        example=None
    )
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate and clean question input."""
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty or whitespace only")
        if len(v) > 1000:
            raise ValueError("Question exceeds maximum length of 1000 characters")
        return v


class SourceMetadata(BaseModel):
    """Metadata for a source document."""
    
    rank: int = Field(..., description="Rank of the source (1 = most relevant)")
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    source_document: str = Field(..., description="Name of the source document")
    section: str = Field(..., description="Section or chapter reference")
    page: Optional[int] = Field(None, description="Page number if available")
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")
    token_count: int = Field(..., description="Number of tokens in the chunk")


class StageMetrics(BaseModel):
    """Execution metrics for RAG pipeline stages."""
    
    query_embed_dimension: int = Field(..., description="Embedding vector dimension")
    retrieved_chunk_count: int = Field(..., description="Number of chunks retrieved")
    top_similarity_score: float = Field(..., description="Highest similarity score")
    context_token_count: int = Field(..., description="Total tokens in assembled context")
    pipeline_execution_ms: float = Field(..., description="Total pipeline execution time in milliseconds")


class QueryResponse(BaseModel):
    """Response model for RAG pipeline query endpoint."""
    
    status: str = Field(
        default="success",
        description="Response status: success, error, or partial",
        example="success"
    )
    
    message: Optional[str] = Field(
        default=None,
        description="Status message or error description",
        example=None
    )
    
    query: str = Field(
        ...,
        description="Echo of the user's question",
        example="What are the password requirements?"
    )
    
    answer: str = Field(
        ...,
        description="Grounded answer from the RAG pipeline",
        example="Passwords must be at least 12 characters long..."
    )
    
    sources: List[SourceMetadata] = Field(
        default_factory=list,
        description="List of retrieved source chunks ranked by relevance"
    )
    
    generation_model: str = Field(
        ...,
        description="LLM model used to generate the answer",
        example="gpt-4-turbo"
    )
    
    stage_metrics: Optional[StageMetrics] = Field(
        default=None,
        description="Performance metrics from RAG pipeline stages"
    )
    
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when response was generated"
    )
    
    request_id: str = Field(
        ...,
        description="Unique identifier for this request"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    
    status: str = Field(default="error", example="error")
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for client handling")
    timestamp: str = Field(...)
    request_id: Optional[str] = Field(default=None)


# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="RAG Pipeline API",
    description="REST API for querying documents via Retrieval-Augmented Generation (RAG) pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=APIConfig.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    expose_headers=["*"],
)

# Global retriever instance (initialized once)
_retriever: Optional[VectorStoreRetriever] = None


def get_retriever() -> VectorStoreRetriever:
    """Get or initialize the global retriever instance."""
    global _retriever
    if _retriever is None:
        logger.info(f"Initializing retriever with vector store: {APIConfig.vector_store_path}")
        _retriever = VectorStoreRetriever(vector_store_path=APIConfig.vector_store_path)
    return _retriever


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify API is running."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "RAG Pipeline API",
        "version": "1.0.0"
    }


@app.get("/config", tags=["Configuration"])
async def get_config():
    """Get current API configuration (sensitive fields redacted)."""
    return {
        "api_host": APIConfig.api_host,
        "api_port": APIConfig.api_port,
        "vector_store_path": APIConfig.vector_store_path,
        "retrieval_k": APIConfig.retrieval_k,
        "retrieval_score_threshold": APIConfig.retrieval_score_threshold,
        "max_context_tokens": APIConfig.max_context_tokens,
        "max_answer_tokens": APIConfig.max_answer_tokens,
        "openai_model": APIConfig.openai_model,
        "cors_origins": APIConfig.cors_origins,
        "api_key_configured": bool(APIConfig.openai_api_key and 
                                   APIConfig.openai_api_key not in ["your_api_key_here", "your_grok_api_key_here"])
    }


# ============================================================================
# Main Query Endpoint
# ============================================================================

@app.post("/query", response_model=QueryResponse, tags=["Query"], status_code=200)
async def query_rag_pipeline(request: QueryRequest) -> QueryResponse:
    """
    Query the RAG pipeline with a question.
    
    Accepts a user question, retrieves relevant document chunks, 
    assembles context, and generates a grounded answer with sources.
    
    Args:
        request: QueryRequest with question and optional retrieval parameters
        
    Returns:
        QueryResponse with answer, sources, metrics, and metadata
        
    Raises:
        HTTPException: For validation errors, configuration issues, or pipeline failures
    """
    import uuid
    
    request_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    try:
        # Validate configuration
        if not APIConfig.openai_api_key:
            logger.warning(f"[{request_id}] No OpenAI API key configured")
        
        logger.info(f"[{request_id}] Received query: {request.question[:100]}...")
        
        # Get retriever instance
        retriever = get_retriever()
        
        # Validate vector store exists
        vector_store_path = Path(APIConfig.vector_store_path)
        if not vector_store_path.exists():
            logger.error(f"[{request_id}] Vector store not found: {APIConfig.vector_store_path}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "error",
                    "message": "Vector store not initialized. Please run indexing pipeline first.",
                    "error_code": "VECTOR_STORE_NOT_FOUND",
                    "timestamp": timestamp,
                    "request_id": request_id
                }
            )
        
        # Run RAG pipeline
        logger.info(f"[{request_id}] Running RAG pipeline with k={request.k}")
        result = run_rag_pipeline(
            query=request.question,
            k=request.k,
            score_threshold=request.score_threshold,
            metadata_filter=request.metadata_filter,
            vector_store_path=APIConfig.vector_store_path,
            retriever=retriever
        )
        
        # Build response
        sources = [SourceMetadata(**source) for source in result.get("returned_sources", [])]
        
        stage_metrics = None
        if "stage_metrics" in result:
            stage_metrics = StageMetrics(**result["stage_metrics"])
        
        response = QueryResponse(
            status="success",
            query=request.question,
            answer=result.get("answer", ""),
            sources=sources,
            generation_model=result.get("generation_model", "Unknown"),
            stage_metrics=stage_metrics,
            timestamp=timestamp,
            request_id=request_id
        )
        
        logger.info(f"[{request_id}] Query completed successfully. Retrieved {len(sources)} sources.")
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": f"Invalid request: {str(e)}",
                "error_code": "VALIDATION_ERROR",
                "timestamp": timestamp,
                "request_id": request_id
            }
        )
    except Exception as e:
        logger.error(f"[{request_id}] Pipeline error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Internal server error processing your request",
                "error_code": "PIPELINE_ERROR",
                "timestamp": timestamp,
                "request_id": request_id
            }
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "error_code": "HTTP_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_SERVER_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "RAG Pipeline API",
        "version": "1.0.0",
        "description": "Retrieval-Augmented Generation pipeline for grounded Q&A",
        "endpoints": {
            "health": "/health",
            "config": "/config",
            "query": "/query",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting RAG API on {APIConfig.api_host}:{APIConfig.api_port}")
    logger.info(f"Vector store: {APIConfig.vector_store_path}")
    logger.info(f"Model: {APIConfig.openai_model}")
    logger.info(f"CORS origins: {APIConfig.cors_origins}")
    
    uvicorn.run(
        "src.api:app",
        host=APIConfig.api_host,
        port=APIConfig.api_port,
        reload=APIConfig.api_reload,
        workers=APIConfig.api_workers,
        log_level=APIConfig.log_level.lower()
    )
