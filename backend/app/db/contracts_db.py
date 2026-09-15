"""
Contracts, Suppliers, and Activity Storage Engine.

Provides persistent storage for corporate contract records, supplier profiles, and activity logs.
Syncs with Supabase PostgreSQL tables when configured, or persists locally to data/contracts/contracts_db.json.
"""

import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx

from app.config import AppConfig, setup_logger

logger = setup_logger("contracts_db")

# Initial empty database state - users upload their own contracts
INITIAL_CONTRACTS = []
INITIAL_ACTIVITIES = []
INITIAL_SUPPLIERS = []


class ContractsDBManager:
    """Manages persistent contract storage, supplier database, and activity logs."""

    def __init__(self):
        self.storage_path: Path = AppConfig.CONTRACT_STORAGE_DIR / "contracts_db.json"
        self.contracts: List[Dict[str, Any]] = []
        self.activities: List[Dict[str, Any]] = []
        self.suppliers: List[Dict[str, Any]] = []
        self.ai_query_logs: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Loads data from disk or initializes defaults."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.contracts = data.get("contracts", INITIAL_CONTRACTS)
                    self.activities = data.get("activities", INITIAL_ACTIVITIES)
                    self.suppliers = data.get("suppliers", INITIAL_SUPPLIERS)
                    self.ai_query_logs = data.get("ai_query_logs", [])
                    logger.info(f"Loaded {len(self.contracts)} contracts and {len(self.activities)} activities from database.")
                    return
            except Exception as e:
                logger.error(f"Failed to load contracts database file: {e}")

        # Initialize defaults
        self.contracts = list(INITIAL_CONTRACTS)
        self.activities = list(INITIAL_ACTIVITIES)
        self.suppliers = list(INITIAL_SUPPLIERS)
        self.ai_query_logs = []
        self._save_data()

    def _save_data(self):
        """Persists data to JSON file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "contracts": self.contracts,
                "activities": self.activities,
                "suppliers": self.suppliers,
                "ai_query_logs": self.ai_query_logs
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error persisting contracts DB: {e}")

    def get_all_contracts(
        self,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves contracts filtered by search query, status, or type."""
        results = list(self.contracts)

        if status_filter and status_filter.lower() not in ("all", "all statuses"):
            results = [c for c in results if c.get("status", "").lower() == status_filter.lower()]

        if type_filter and type_filter.lower() not in ("all", "all types"):
            results = [c for c in results if type_filter.lower() in c.get("document_type", "").lower()]

        if search:
            query = search.lower().strip()
            keywords = [kw for kw in query.split() if len(kw) > 1]
            results = [
                c for c in results
                if query in c.get("contract_name", "").lower() or
                   query in c.get("supplier", "").lower() or
                   query in c.get("document_type", "").lower() or
                   (keywords and any(
                       kw in c.get("contract_name", "").lower() or
                       kw in c.get("supplier", "").lower() or
                       kw in c.get("document_type", "").lower()
                       for kw in keywords
                   ))
            ]

        return results

    def get_contract_by_id(self, contract_id: str) -> Optional[Dict[str, Any]]:
        for c in self.contracts:
            if c.get("id") == contract_id:
                return c
        return None

    def add_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inserts a new contract record into database."""
        cid = contract_data.get("id") or f"contract-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        record = {
            "id": cid,
            "contract_name": contract_data.get("contract_name") or contract_data.get("filename", "Untitled Contract"),
            "supplier": contract_data.get("supplier") or "Unassigned Supplier",
            "document_type": contract_data.get("document_type") or "General Contract",
            "annual_value": float(contract_data.get("annual_value") or 0.0),
            "start_date": contract_data.get("start_date") or now[:10],
            "end_date": contract_data.get("end_date") or "2027-12-31",
            "status": contract_data.get("status") or "Active",
            "created_at": now
        }

        # Avoid duplicates
        self.contracts = [c for c in self.contracts if c["id"] != cid]
        self.contracts.insert(0, record)

        # Log activity
        self.log_activity(
            document_name=record["contract_name"],
            action="Contract uploaded & intelligence indexed",
            initiated_by="User / AI Engine"
        )

        # Ensure supplier profile exists
        supplier_name = record["supplier"]
        if supplier_name and not any(s.get("name") == supplier_name for s in self.suppliers):
            self.suppliers.append({
                "id": f"sup-{uuid.uuid4().hex[:6]}",
                "name": supplier_name,
                "category": record["document_type"],
                "vetted": True
            })

        self._save_data()
        return record

    def update_contract(self, contract_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates fields of an existing contract record."""
        target = self.get_contract_by_id(contract_id)
        if not target:
            return None

        if "contract_name" in update_data and update_data["contract_name"]:
            target["contract_name"] = update_data["contract_name"]
        if "supplier" in update_data and update_data["supplier"]:
            target["supplier"] = update_data["supplier"]
        if "document_type" in update_data and update_data["document_type"]:
            target["document_type"] = update_data["document_type"]
        if "annual_value" in update_data and update_data["annual_value"] is not None:
            target["annual_value"] = float(update_data["annual_value"])
        if "start_date" in update_data and update_data["start_date"]:
            target["start_date"] = update_data["start_date"]
        if "end_date" in update_data and update_data["end_date"]:
            target["end_date"] = update_data["end_date"]
        if "status" in update_data and update_data["status"]:
            target["status"] = update_data["status"]

        self.log_activity(
            document_name=target.get("contract_name", contract_id),
            action="Contract details updated",
            initiated_by="User"
        )
        self._save_data()
        return target

    def delete_contract(self, contract_id: str) -> bool:
        """Deletes contract record."""
        initial_len = len(self.contracts)
        target = self.get_contract_by_id(contract_id)
        if target:
            self.contracts = [c for c in self.contracts if c["id"] != contract_id]
            self.log_activity(
                document_name=target.get("contract_name", contract_id),
                action="Contract record removed",
                initiated_by="User"
            )
            self._save_data()
            return True
        return False

    def log_activity(self, document_name: str, action: str, initiated_by: str):
        """Adds a new entry to recent activities log."""
        now = datetime.datetime.now(datetime.timezone.utc)
        act = {
            "id": f"act-{uuid.uuid4().hex[:6]}",
            "document_name": document_name,
            "action": action,
            "initiated_by": initiated_by,
            "date": now.strftime("Today, %I:%M %p"),
            "timestamp": now.isoformat()
        }
        self.activities.insert(0, act)
        # Keep recent 20 activities
        self.activities = self.activities[:20]
        self._save_data()

    def log_ai_query(self, question: str, answer: str, sources_count: int, query_type: str = "AI Q&A"):
        """Logs AI question/search and generated answer for admin tracking."""
        now = datetime.datetime.now(datetime.timezone.utc)
        log_entry = {
            "id": f"qlog-{uuid.uuid4().hex[:6]}",
            "query_type": query_type,
            "question": question,
            "answer": answer,
            "sources_count": sources_count,
            "initiated_by": "Enterprise User",
            "date": now.strftime("%b %d, %Y - %I:%M %p"),
            "timestamp": now.isoformat()
        }
        self.ai_query_logs.insert(0, log_entry)
        # Keep up to 100 recent AI query logs
        self.ai_query_logs = self.ai_query_logs[:100]
        self._save_data()

    def get_ai_query_logs(self) -> List[Dict[str, Any]]:
        """Retrieves all logged AI questions and answers."""
        return list(self.ai_query_logs)

    def get_overview_metrics(self) -> Dict[str, Any]:
        """Calculates dynamic overview metrics for Dashboard Overview Page."""
        total_contracts = len(self.contracts)
        active_contracts = len([c for c in self.contracts if c.get("status") == "Active"])
        vetted_suppliers = len([s for s in self.suppliers if s.get("vetted", True)])
        pending_renewals = len([c for c in self.contracts if c.get("status") == "Expiring Soon"])
        
        # Calculate dynamic compliance score
        compliant_contracts = len([c for c in self.contracts if c.get("status") in ("Active", "Draft")])
        if total_contracts > 0:
            score = int((compliant_contracts / total_contracts) * 100)
            score_str = f"{score}%"
            score_change = f"{compliant_contracts} of {total_contracts} Compliant"
        else:
            score_str = "0%"
            score_change = "No contracts uploaded"

        return {
            "active_contracts": {
                "count": active_contracts,
                "change": f"{active_contracts} Active" if active_contracts > 0 else "0 Active"
            },
            "vetted_suppliers": {
                "count": vetted_suppliers,
                "change": f"{vetted_suppliers} Registered" if vetted_suppliers > 0 else "0 Registered"
            },
            "pending_renewals": {
                "count": pending_renewals,
                "badge": f"{pending_renewals} Expiring" if pending_renewals > 0 else "0 Expiring"
            },
            "compliance_score": {
                "percentage": score_str,
                "change": score_change
            },
            "recent_activities": self.activities[:10]
        }

    def add_supplier(self, name: str, category: str) -> Dict[str, Any]:
        """Adds a new supplier profile."""
        sup = {
            "id": f"sup-{uuid.uuid4().hex[:6]}",
            "name": name,
            "category": category,
            "vetted": True
        }
        self.suppliers.append(sup)
        self.log_activity(
            document_name=f"Supplier Profile: {name}",
            action="New vendor recorded",
            initiated_by="User"
        )
        self._save_data()
        return sup


contracts_db = ContractsDBManager()
