"""
Suppliers Management API Router.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.db.contracts_db import contracts_db
from app.config import setup_logger

logger = setup_logger("suppliers_api")
router = APIRouter(prefix="/api/suppliers", tags=["Supplier Management"])


class CreateSupplierRequest(BaseModel):
    name: str
    category: str


@router.get("")
async def list_suppliers():
    """Lists all registered supplier profiles."""
    return {"suppliers": contracts_db.suppliers}


@router.post("")
async def create_supplier(req: CreateSupplierRequest):
    """Creates a new vendor profile."""
    if not req.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supplier name is required.")
    
    sup = contracts_db.add_supplier(name=req.name.strip(), category=req.category.strip() or "General Vendor")
    return {"status": "success", "supplier": sup}
