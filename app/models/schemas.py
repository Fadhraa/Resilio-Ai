from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ==========================================
# 1. ENUMERASI STATUS & TIPE OPERASIONAL
# ==========================================

class DisruptionType(str, Enum):
    SUPPLIER_DISRUPTION = "SUPPLIER_DISRUPTION"
    WEATHER_FLOOD = "WEATHER_FLOOD"
    PRICE_HIKE = "PRICE_HIKE"
    QUALITY_REJECTION = "QUALITY_REJECTION"
    LOGISTICS_BREAKDOWN = "LOGISTICS_BREAKDOWN"


class FeasibilityStatus(str, Enum):
    FEASIBLE = "FEASIBLE"
    FEASIBLE_WITH_CONDITIONS = "FEASIBLE_WITH_CONDITIONS"
    NOT_FEASIBLE = "NOT_FEASIBLE"


class StrategyType(str, Enum):
    DIRECT_DELIVERY = "DIRECT_DELIVERY"
    SPLIT_DELIVERY = "SPLIT_DELIVERY"
    BUFFER_STAGGERED = "BUFFER_STAGGERED"


class ApprovalAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MODIFY = "MODIFY"


# ==========================================
# 2. MODEL DOMAIN (INVENTARIS & SUPPLIER)
# ==========================================

class InventoryItem(BaseModel):
    item_id: str = Field(..., description="ID unik bahan pangan (misal: ITEM-AYAM-01)")
    item_name: str = Field(..., description="Nama bahan pangan")
    category: str = Field(..., description="Kategori: PROTEIN, VEGETABLE, STAPLE")
    current_stock_kg: float = Field(..., ge=0, description="Stok fisik aktual di gudang (kg)")
    safety_stock_kg: float = Field(..., ge=0, description="Batas stok minimum aman (kg)")
    freezer_capacity_kg: float = Field(..., ge=0, description="Kapasitas total penyimpanan dingin (kg)")
    freezer_occupied_kg: float = Field(..., ge=0, description="Kapasitas yang sedang terpakai saat ini (kg)")
    sop_max_price_per_kg: float = Field(..., gt=0, description="Pagu anggaran SOP per kg (IDR)")

    model_config = ConfigDict(from_attributes=True)


class SupplierRecord(BaseModel):
    supplier_id: str = Field(..., description="ID unik supplier (misal: SUP-ALT-02)")
    supplier_name: str = Field(..., description="Nama badan usaha / rekanan supplier")
    category: str = Field(..., description="Kategori bahan yang dipasok")
    halal_certified: bool = Field(..., description="Status keaktifan sertifikasi halal")
    halal_cert_number: Optional[str] = Field(None, description="Nomor registrasi sertifikat halal")
    unit_price_idr: float = Field(..., gt=0, description="Harga penawaran per kg (IDR)")
    daily_capacity_kg: float = Field(..., gt=0, description="Kapasitas stok harian yang sanggup dikirim")
    lead_time_hours: float = Field(..., gt=0, description="Estimasi waktu pengiriman dari order ke SPPG (jam)")
    distance_km: float = Field(..., ge=0, description="Jarak logistik ke lokasi SPPG (km)")
    reliability_rating: float = Field(..., ge=0, le=100, description="Skor histori performa rekanan (0-100)")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. KONTRAK DATA EVENT & DEFISIT
# ==========================================

class IncidentTriggerRequest(BaseModel):
    item_id: str = Field(..., example="ITEM-AYAM-01")
    disruption_type: DisruptionType = Field(default=DisruptionType.SUPPLIER_DISRUPTION)
    affected_supplier_id: str = Field(..., example="SUP-UTAMA-01")
    estimated_duration_days: int = Field(default=3, ge=1)
    incident_notes: Optional[str] = Field(None, description="Catatan laporan insiden lapangan")


class IncidentTriggerResponse(BaseModel):
    incident_id: str
    status: str = "PROCESSING"
    stream_url: str


class IncidentMetrics(BaseModel):
    current_stock_kg: float
    deficit_kg: float
    freezer_available_kg: float
    target_production_portions: int
    financial_risk_exposure_idr: float


# ==========================================
# 4. KONTRAK EVALUASI & REKOMENDASI MITIGASI
# ==========================================

class ScoringBreakdown(BaseModel):
    stock_fulfillment: float = Field(..., ge=0, le=100, description="Bobot 25%: Pemenuhan kuota defisit")
    time_lead_compliance: float = Field(..., ge=0, le=100, description="Bobot 20%: Waktu tiba vs jam masak")
    budget_compliance: float = Field(..., ge=0, le=100, description="Bobot 15%: Kepatuhan harga terhadap pagu SOP")
    halal_and_legal: float = Field(..., ge=0, le=100, description="Bobot 15%: Gating parameter keabsahan sertifikat halal")
    storage_compatibility: float = Field(..., ge=0, le=100, description="Bobot 10%: Kesesuaian volume batch dengan freezer")
    kitchen_capacity: float = Field(..., ge=0, le=100, description="Bobot 10%: Kesiapan olah dapur")
    route_safety: float = Field(..., ge=0, le=100, description="Bobot 5%: Risiko rute logistik")


class DeliveryBatch(BaseModel):
    batch_no: int
    qty_kg: float
    eta: str = Field(..., description="Estimasi waktu kedatangan bahan (ISO string)")


class LogisticsStrategy(BaseModel):
    strategy_type: StrategyType
    rationale: str = Field(..., description="Penjelasan teknis pembagian pengiriman")
    batches: List[DeliveryBatch]


class RecommendedProcurement(BaseModel):
    supplier_id: str
    supplier_name: str
    unit_price_idr: float
    total_estimated_cost_idr: float
    halal_certificate_active: bool
    feasibility_score: float = Field(..., ge=0, le=100)
    feasibility_status: FeasibilityStatus
    scoring_breakdown: ScoringBreakdown
    logistics_strategy: LogisticsStrategy


class AuditTrailStep(BaseModel):
    stage: str
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IncidentDecisionResponse(BaseModel):
    incident_id: str
    item_id: str
    item_name: str
    metrics: IncidentMetrics
    recommended_procurement: Optional[RecommendedProcurement]
    audit_trail: List[AuditTrailStep]


# ==========================================
# 5. KONTRAK HUMAN APPROVAL & PURCHASE ORDER
# ==========================================

class ApprovalRequest(BaseModel):
    incident_id: str
    action: ApprovalAction = Field(default=ApprovalAction.APPROVE)
    approved_qty_kg: float = Field(..., gt=0)
    approver_name: str = Field(..., min_length=3)
    approver_notes: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    status: str = "SUCCESS"
    po_number: str
    incident_id: str
    supplier_id: str
    supplier_name: str
    item_id: str
    approved_qty_kg: float
    unit_price_idr: float
    total_amount_idr: float
    logistics_strategy: LogisticsStrategy
    approver_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    po_download_url: str
