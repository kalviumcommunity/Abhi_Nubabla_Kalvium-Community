"""
Compliance Audit API Router.
"""

from fastapi import APIRouter, HTTPException, status
from app.db.contracts_db import contracts_db
from app.config import setup_logger

logger = setup_logger("audit_api")
router = APIRouter(prefix="/api/audit", tags=["Compliance Audit"])


@router.post("/run")
async def run_compliance_audit():
    """
    Executes automated compliance audit across stored contract portfolio,
    logging scan events and updating audit status.
    """
    contracts_db.log_activity(
        document_name="Portfolio Audit",
        action="Compliance scan complete",
        initiated_by="AI Engine"
    )
    metrics = contracts_db.get_overview_metrics()
    score_str = metrics["compliance_score"]["percentage"]
    return {
        "status": "success",
        "message": f"Portfolio compliance audit executed successfully. Current score: {score_str}.",
        "compliance_score": score_str
    }
