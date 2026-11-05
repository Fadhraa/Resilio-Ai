from typing import List, Optional, TypedDict
from app.models.schemas import (
    ApprovalRequest,
    AuditTrailStep,
    DisruptionType,
    IncidentMetrics,
    PurchaseOrderResponse,
    RecommendedProcurement,
    SupplierRecord,
)


class ProcurementWorkflowState(TypedDict):
    """
    State persisten untuk alur kerja LangGraph ResilioAI.
    
    Menyimpan seluruh konteks eksekusi mulai dari pemicuan insiden,
    perhitungan data layer, filter supplier, rekomendasi agen,
    skoring kelayakan, hingga otorisasi persetujuan dan PO.
    """
    incident_id: str
    item_id: str
    disruption_type: DisruptionType
    affected_supplier_id: str
    estimated_duration_days: int
    incident_notes: Optional[str]
    target_production_portions: int
    metrics: Optional[IncidentMetrics]
    eligible_suppliers: List[SupplierRecord]
    recommended_procurement: Optional[RecommendedProcurement]
    retry_count: int
    approval_status: Optional[str]        # 'WAITING_APPROVAL', 'APPROVED', 'REJECTED'
    approver_decision: Optional[ApprovalRequest]
    po_result: Optional[PurchaseOrderResponse]
    audit_trail: List[AuditTrailStep]
    current_stage: str

