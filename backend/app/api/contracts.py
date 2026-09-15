"""
Contract Management API Router.

Endpoints to upload corporate contracts (PDF/DOCX/TXT), list stored contracts,
export contract list CSV, and remove contract documents from vector index and DB.
"""

import io
import csv
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.config import AppConfig, setup_logger
from app.ingestion.contract_processor import contract_processor
from app.vector_store.pinecone_store import vector_store
from app.db.contracts_db import contracts_db
from app.rag.generator import get_openrouter_embedding_client

logger = setup_logger("contracts_api")
router = APIRouter(prefix="/api/contracts", tags=["Contract Management"])


class CreateContractManualRequest(BaseModel):
    contract_name: str
    supplier: str
    document_type: str
    annual_value: float
    start_date: str
    end_date: str
    status: str = "Active"


class UpdateContractRequest(BaseModel):
    contract_name: Optional[str] = None
    supplier: Optional[str] = None
    document_type: Optional[str] = None
    annual_value: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None


@router.post("/upload")
async def upload_contract(
    file: UploadFile = File(...),
    supplier: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    annual_value: Optional[float] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    contract_status: Optional[str] = Form(None)
):
    """
    Uploads a corporate contract document (PDF, DOCX, TXT), cleans text, generates token-aware chunks,
    indexes embeddings into Pinecone / Local Vector Store, and stores metadata in Contracts DB.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file filename provided.")

    dest_path = AppConfig.CONTRACT_STORAGE_DIR / file.filename
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving contract file: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save uploaded contract.")

    try:
        # 1. Process contract document
        chunks = contract_processor.process_file(dest_path)
        if not chunks:
            raise ValueError("Document yielded no valid text chunks.")

        contract_meta = chunks[0]["metadata"]
        cid = contract_meta.get("contract_id")

        # Override metadata if explicitly passed in Form
        resolved_supplier = supplier or contract_meta.get("supplier") or "Vendor / Supplier"
        resolved_type = document_type or contract_meta.get("contract_type") or "Master Agreement"
        resolved_value = annual_value if annual_value is not None else 150000.0
        resolved_start = start_date or "2026-01-01"
        resolved_end = end_date or "2027-12-31"
        resolved_status = contract_status or "Active"

        # Update metadata across chunks
        for c in chunks:
            c["metadata"]["supplier"] = resolved_supplier
            c["metadata"]["contract_type"] = resolved_type

        # 2. Embed and index into vector store
        embedding_client = get_openrouter_embedding_client()
        indexed_count = vector_store.add_contract_chunks(chunks, embedding_client)

        # 3. Store record in Contracts Database Manager
        db_record = contracts_db.add_contract({
            "id": cid,
            "contract_name": file.filename,
            "supplier": resolved_supplier,
            "document_type": resolved_type,
            "annual_value": resolved_value,
            "start_date": resolved_start,
            "end_date": resolved_end,
            "status": resolved_status
        })

        return {
            "status": "success",
            "message": f"Contract '{file.filename}' processed and indexed successfully.",
            "contract": db_record,
            "chunks_indexed": indexed_count
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Ingestion Error for {file.filename}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Contract ingestion failed: {str(e)}")


@router.get("/list")
async def list_contracts(
    search: Optional[str] = Query(None, description="Search filter by name or supplier"),
    status: Optional[str] = Query(None, description="Filter by status (Active, Expiring Soon, Expired, Draft)"),
    type: Optional[str] = Query(None, description="Filter by document type"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Returns summary list of all corporate contracts stored in database with filtering and pagination.
    """
    filtered = contracts_db.get_all_contracts(
        search=search,
        status_filter=status,
        type_filter=type
    )

    total_count = len(filtered)
    start_idx = (page - 1) * limit
    paginated = filtered[start_idx : start_idx + limit]

    return {
        "total_contracts": total_count,
        "page": page,
        "limit": limit,
        "contracts": paginated
    }


@router.post("/create")
async def create_contract_manual(req: CreateContractManualRequest):
    """Manually registers a contract record in database."""
    record = contracts_db.add_contract({
        "contract_name": req.contract_name,
        "supplier": req.supplier,
        "document_type": req.document_type,
        "annual_value": req.annual_value,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "status": req.status
    })
    return {"status": "success", "contract": record}


@router.get("/export")
async def export_contracts_csv():
    """Exports entire contract database as a downloadable CSV file."""
    all_contracts = contracts_db.get_all_contracts()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Contract Name", "Supplier", "Document Type", "Annual Value ($)", "Start Date", "End Date", "Status"])

    for c in all_contracts:
        writer.writerow([
            c.get("id"),
            c.get("contract_name"),
            c.get("supplier"),
            c.get("document_type"),
            c.get("annual_value"),
            c.get("start_date"),
            c.get("end_date"),
            c.get("status")
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contracts_portfolio.csv"}
    )


@router.put("/{contract_id}")
async def update_contract(contract_id: str, req: UpdateContractRequest):
    """Updates contract record fields in database."""
    updated = contracts_db.update_contract(contract_id, req.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contract ID '{contract_id}' not found.")
    return {
        "status": "success",
        "message": f"Contract '{contract_id}' updated successfully.",
        "contract": updated
    }


@router.delete("/{contract_id}")
async def delete_contract(contract_id: str):
    """Deletes contract vector index records and DB entry."""
    vector_store.delete_contract(contract_id)
    deleted_db = contracts_db.delete_contract(contract_id)
    if not deleted_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contract ID '{contract_id}' not found.")
    return {
        "status": "success",
        "message": f"Contract '{contract_id}' removed from database and vector index."
    }
