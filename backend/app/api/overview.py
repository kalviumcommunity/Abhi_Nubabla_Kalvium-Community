"""
Overview Dashboard API Router.

Provides dynamic metrics, stats, recent intel & activity feeds, and quick operation triggers.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.db.contracts_db import contracts_db
from app.config import setup_logger

logger = setup_logger("overview_api")
router = APIRouter(prefix="/api/overview", tags=["Overview Dashboard"])


class ActivityLogItem(BaseModel):
    id: str
    document_name: str
    action: str
    initiated_by: str
    date: str


class MetricCard(BaseModel):
    count: str | int
    change: str | None = None
    badge: str | None = None


class OverviewResponse(BaseModel):
    active_contracts: MetricCard
    vetted_suppliers: MetricCard
    pending_renewals: MetricCard
    compliance_score: MetricCard
    recent_activities: List[ActivityLogItem]


@router.get("", response_model=OverviewResponse)
async def get_overview_dashboard():
    """
    Returns dynamic overview metrics, active contracts stats, supplier metrics,
    pending renewal counts, compliance scores, and recent intel activity log.
    """
    try:
        metrics = contracts_db.get_overview_metrics()
        return OverviewResponse(
            active_contracts=MetricCard(
                count=metrics["active_contracts"]["count"],
                change=metrics["active_contracts"]["change"]
            ),
            vetted_suppliers=MetricCard(
                count=metrics["vetted_suppliers"]["count"],
                change=metrics["vetted_suppliers"]["change"]
            ),
            pending_renewals=MetricCard(
                count=metrics["pending_renewals"]["count"],
                badge=metrics["pending_renewals"]["badge"]
            ),
            compliance_score=MetricCard(
                count=metrics["compliance_score"]["percentage"],
                change=metrics["compliance_score"]["change"]
            ),
            recent_activities=[
                ActivityLogItem(**act) for act in metrics["recent_activities"]
            ]
        )
    except Exception as e:
        logger.error(f"Error fetching overview dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load overview data: {str(e)}"
        )
