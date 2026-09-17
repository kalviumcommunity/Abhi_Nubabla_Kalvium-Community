"""
Contract RAG Q&A & AI Intelligent Search API Router.

Endpoints for querying contract repository, performing semantic searches with filters,
and receiving grounded answers or real-time token streaming.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.rag.generator import contract_qa_generator, get_openrouter_embedding_client
from app.vector_store.pinecone_store import vector_store
from app.db.contracts_db import contracts_db
from app.db.supabase import supabase_db
from app.config import setup_logger

logger = setup_logger("rag_api")
router = APIRouter(prefix="/api/query", tags=["Contract RAG Q&A"])


class ChatTurn(BaseModel):
    role: str
    content: str


class ContractQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1500, description="Question regarding stored corporate contracts.")
    history: Optional[List[ChatTurn]] = Field(default=None, description="Previous conversation context turns.")
    contract_id: Optional[str] = Field(default=None, description="Optional target contract ID filter.")
    k: Optional[int] = Field(default=8, ge=1, le=20, description="Top-k chunks to retrieve.")
    score_threshold: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="Similarity score cutoff.")
    user_email: Optional[str] = Field(default=None, description="Email of user asking question.")


class CitationSource(BaseModel):
    chunk_id: str
    contract_title: str
    section_title: str
    score: float
    snippet: Optional[str] = None
    supplier: Optional[str] = None
    document_type: Optional[str] = None
    execution_date: Optional[str] = None


class ContractQueryResponse(BaseModel):
    answer: str
    sources: List[CitationSource]
    chunks_retrieved: int


class SearchResultItem(BaseModel):
    id: str
    document_title: str
    supplier: str
    document_type: str
    confidence_percentage: int
    confidence_label: str
    passage_text: str
    execution_date: str
    chunk_id: str
    section_title: str
    similarity_score: float


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[SearchResultItem]
    counts_by_type: Dict[str, int]
    counts_by_confidence: Dict[str, int]


@router.post("", response_model=ContractQueryResponse)
async def query_contracts(req: ContractQueryRequest):
    """
    Submits a question against stored corporate contracts and returns a grounded answer with explicit citations.
    """
    try:
        history_list = [turn.model_dump() for turn in req.history] if req.history else None
        res = contract_qa_generator.generate_answer(
            question=req.question,
            history=history_list,
            k=req.k or 8,
            contract_id=req.contract_id,
            score_threshold=req.score_threshold or 0.0
        )
        contracts_db.log_ai_query(
            question=req.question,
            answer=res["answer"],
            sources_count=len(res.get("sources", [])),
            sources=res.get("sources", []),
            query_type="AI Q&A",
            user_email=req.user_email
        )

        if req.user_email and supabase_db.is_configured():
            import uuid, datetime
            now = datetime.datetime.now(datetime.timezone.utc)
            history_entry = {
                "id": f"qlog-{uuid.uuid4().hex[:6]}",
                "query_type": "AI Q&A",
                "question": req.question,
                "answer": res["answer"],
                "sources_count": len(res.get("sources", [])),
                "sources": res.get("sources", []),
                "user_email": req.user_email,
                "initiated_by": req.user_email,
                "date": now.strftime("%b %d, %Y - %I:%M %p"),
                "timestamp": now.isoformat()
            }
            try:
                await supabase_db.add_user_history_entry(req.user_email, history_entry)
            except Exception as se:
                logger.error(f"Failed to log user history entry in Supabase: {se}")

        return ContractQueryResponse(
            answer=res["answer"],
            sources=[CitationSource(**s) for s in res["sources"]],
            chunks_retrieved=res["chunks_retrieved"]
        )
    except Exception as e:
        logger.error(f"Contract Q&A error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process query: {str(e)}")


def matches_doc_type(allowed_types: List[str], actual_type: str) -> bool:
    if not allowed_types:
        return True
    actual = actual_type.lower().strip()
    for allowed in allowed_types:
        a = allowed.lower().strip()
        if not a:
            continue
        if a in actual or actual in a:
            return True
        a_singular = a.rstrip("s")
        actual_singular = actual.rstrip("s")
        if a_singular in actual or actual_singular in a or a_singular in actual_singular:
            return True
        if "master" in a and "master" in actual:
            return True
        if "sow" in a and ("sow" in actual or "order" in actual or "service" in actual):
            return True
        if "amend" in a and "amend" in actual:
            return True
        if "nda" in a and ("nda" in actual or "disclosure" in actual):
            return True
    return False


@router.get("/search", response_model=SearchResponse)
async def search_contracts_intelligent(
    q: str = Query("", description="Search term or clause query"),
    doc_types: Optional[str] = Query(None, description="Comma separated doc type filters"),
    confidence: Optional[str] = Query(None, description="Comma separated confidence filters (high, medium, low)"),
    contract_status: Optional[str] = Query(None, description="Comma separated status filters (active, expiring, draft)")
):
    """
    Performs AI Intelligent Search across contract vector chunks and database records.
    Returns matched passages, confidence scores, and dynamic breakdown counts.
    """
    query_str = q.strip()
    embedding_client = get_openrouter_embedding_client()

    # If query string is empty, return 0 matches
    if not query_str:
        return SearchResponse(
            query="",
            total_matches=0,
            results=[],
            counts_by_type={
                "Master Agreements": 0,
                "Amendments": 0,
                "SOWs & Order Forms": 0,
                "NDAs": 0
            },
            counts_by_confidence={
                "High Match (>90%)": 0,
                "Medium Match (70-90%)": 0,
                "Low Match (<70%)": 0
            }
        )

    chunks = vector_store.search_similar_chunks(
        query=query_str,
        client=embedding_client,
        k=15,
        score_threshold=0.0
    )

    all_db_contracts = {c["id"]: c for c in contracts_db.get_all_contracts()}
    title_db_map = {c["contract_name"].lower(): c for c in all_db_contracts.values()}

    results_list: List[SearchResultItem] = []
    
    # Process vector matches
    for idx, c in enumerate(chunks):
        text = c.get("text", "")
        meta = c.get("metadata", {})
        chunk_id = c.get("chunk_id") or f"chunk-{idx}"
        
        raw_score = c.get("similarity_score", 0.85)
        conf_pct = min(99, max(65, int(raw_score * 100) if raw_score <= 1.0 else 90))
        if conf_pct > 90:
            conf_label = "High Match (>90%)"
        elif conf_pct >= 70:
            conf_label = "Medium Match (70-90%)"
        else:
            conf_label = "Low Match (<70%)"

        doc_title = meta.get("contract_title") or meta.get("filename") or "Contract Document"
        
        # Cross reference with DB for supplier, date, type
        db_match = all_db_contracts.get(meta.get("contract_id")) or title_db_map.get(doc_title.lower())
        
        supplier_name = (db_match.get("supplier") if db_match else None) or meta.get("supplier") or "Vendor Inc."
        doc_type = (db_match.get("document_type") if db_match else None) or meta.get("contract_type") or "Master Agreement"
        exec_date = (db_match.get("start_date") if db_match else None) or "Oct 12, 2025"
        status_val = (db_match.get("status") if db_match else "Active")

        # Apply Filters
        if doc_types and isinstance(doc_types, str):
            allowed_types = [t.strip().lower() for t in doc_types.split(",") if t.strip()]
            if allowed_types and not matches_doc_type(allowed_types, doc_type):
                continue

        if confidence and isinstance(confidence, str):
            allowed_conf = [cf.strip().lower() for cf in confidence.split(",")]
            if "high" in allowed_conf and conf_pct <= 90:
                continue
            if "medium" in allowed_conf and (conf_pct < 70 or conf_pct > 90):
                continue
            if "low" in allowed_conf and conf_pct >= 70:
                continue

        if contract_status and isinstance(contract_status, str):
            allowed_stat = [s.strip().lower() for s in contract_status.split(",")]
            if not any(s in status_val.lower() for s in allowed_stat):
                continue

        results_list.append(SearchResultItem(
            id=f"res-{idx+1}",
            document_title=doc_title,
            supplier=supplier_name,
            document_type=doc_type,
            confidence_percentage=conf_pct,
            confidence_label=conf_label,
            passage_text=text,
            execution_date=exec_date,
            chunk_id=chunk_id,
            section_title=meta.get("section_title", "General Clause"),
            similarity_score=raw_score
        ))

    # Fallback to contracts_db records if no vector store chunks match
    if not results_list:
        db_contracts = contracts_db.get_all_contracts(search=query_str)
        for idx, c in enumerate(db_contracts):
            doc_type = c.get("document_type", "Master Agreement")
            status_val = c.get("status", "Active")
            conf_pct = 92
            
            # Apply Filters
            if doc_types and isinstance(doc_types, str):
                allowed_types = [t.strip().lower() for t in doc_types.split(",") if t.strip()]
                if allowed_types and not matches_doc_type(allowed_types, doc_type):
                    continue

            if contract_status and isinstance(contract_status, str):
                allowed_stat = [s.strip().lower() for s in contract_status.split(",") if s.strip()]
                if allowed_stat and not any(s in status_val.lower() for s in allowed_stat):
                    continue

            results_list.append(SearchResultItem(
                id=f"db-res-{idx+1}",
                document_title=c.get("contract_name", "Corporate Agreement"),
                supplier=c.get("supplier", "Vendor Inc."),
                document_type=doc_type,
                confidence_percentage=conf_pct,
                confidence_label="High Match (>90%)",
                passage_text=f"Agreement record '{c.get('contract_name')}' with supplier {c.get('supplier')}. Effective dates: {c.get('start_date')} to {c.get('end_date')}. Status: {status_val}. Annual Commitment: ${c.get('annual_value', 0):,.2f}.",
                execution_date=c.get("start_date", "2026-01-01"),
                chunk_id=f"db-chunk-{idx+1}",
                section_title="Contract Portfolio Record",
                similarity_score=0.92
            ))

    # Compute dynamic breakdown counts for filters based on search results
    type_counts = {
        "Master Agreements": len([r for r in results_list if "master" in r.document_type.lower()]),
        "Amendments": len([r for r in results_list if "amendment" in r.document_type.lower()]),
        "SOWs & Order Forms": len([r for r in results_list if "sow" in r.document_type.lower() or "order" in r.document_type.lower()]),
        "NDAs": len([r for r in results_list if "nda" in r.document_type.lower() or "non-disclosure" in r.document_type.lower()])
    }
    conf_counts = {
        "High Match (>90%)": len([r for r in results_list if r.confidence_percentage > 90]),
        "Medium Match (70-90%)": len([r for r in results_list if 70 <= r.confidence_percentage <= 90]),
        "Low Match (<70%)": len([r for r in results_list if r.confidence_percentage < 70])
    }

    if query_str:
        contracts_db.log_ai_query(
            question=query_str,
            answer=f"AI Intelligent Search executed. {len(results_list)} matching passage(s) retrieved across contract portfolio.",
            sources_count=len(results_list),
            query_type="AI Intelligent Search"
        )

    return SearchResponse(
        query=query_str,
        total_matches=len(results_list),
        results=results_list,
        counts_by_type=type_counts,
        counts_by_confidence=conf_counts
    )


@router.post("/stream")
async def stream_contract_query(req: ContractQueryRequest):
    """
    Streams contract Q&A response token-by-token using Server-Sent Events (SSE).
    """
    generator = contract_qa_generator.generate_stream(
        question=req.question,
        k=req.k or 8,
        contract_id=req.contract_id
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@router.get("/user-history")
async def get_user_query_history(user_email: Optional[str] = Query(None)):
    """
    Retrieves history of questions asked and answers generated for the current user.
    Fetches from Supabase user profile history field when available, with fallback to local db.
    """
    if user_email and supabase_db.is_configured():
        sp_history = await supabase_db.get_user_history(user_email)
        if sp_history:
            return {
                "total": len(sp_history),
                "history": sp_history
            }

    logs = contracts_db.get_ai_query_logs(user_email=user_email)
    return {
        "total": len(logs),
        "history": logs
    }


@router.delete("/user-history")
async def clear_user_query_history(user_email: Optional[str] = Query(None)):
    """
    Clears all AI question history for the current user (or all logs if admin/unfiltered).
    """
    if user_email and supabase_db.is_configured():
        await supabase_db.clear_user_history(user_email)
    
    cleared_count = contracts_db.clear_ai_query_logs(user_email=user_email)
    return {
        "message": "User query history successfully cleared.",
        "cleared_count": cleared_count
    }


@router.delete("/user-history/{log_id}")
async def delete_single_query_history_item(log_id: str, user_email: Optional[str] = Query(None)):
    """
    Deletes a single AI question history entry by ID.
    """
    if user_email and supabase_db.is_configured():
        await supabase_db.delete_user_history_entry(user_email, log_id)

    deleted = contracts_db.delete_ai_query_log(log_id, user_email=user_email)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query history log entry not found.")

    return {
        "message": f"Log entry '{log_id}' successfully deleted.",
        "id": log_id
    }
