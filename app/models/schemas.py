from datetime import datetime, timezone
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
    category: str = Field(..., description="Kategori makro bahan pangan (PROTEIN, STAPLE, VEGETABLE)")
    commodity: str = Field(default="DAGING_AYAM", description="Komoditas spesifik (misal: DAGING_AYAM, DAGING_SAPI, TELUR_AYAM, BERAS)")
    supported_items: List[str] = Field(default_factory=lambda: ["ITEM-AYAM-01"], description="Daftar ID bahan inventaris yang didukung supplier ini")
    halal_certified: bool = Field(..., description="Status keaktifan sertifikasi halal")
    halal_cert_number: Optional[str] = Field(None, description="Nomor registrasi sertifikat halal")
    unit_price_idr: float = Field(..., gt=0, description="Harga penawaran per kg (IDR)")
    daily_capacity_kg: float = Field(..., gt=0, description="Kapasitas stok harian yang sanggup dikirim")
    lead_time_hours: float = Field(..., gt=0, description="Estimasi waktu pengiriman dari order ke SPPG (jam)")
    distance_km: float = Field(..., ge=0, description="Jarak logistik ke lokasi SPPG (km)")
    reliability_rating: float = Field(..., ge=0, le=100, description="Skor histori performa rekanan (0-100)")
    is_active: bool = Field(default=True, description="Status keaktifan operasional rekanan")

    model_config = ConfigDict(from_attributes=True)


class SupplierCreateRequest(BaseModel):
    """Payload kontrak untuk pendaftaran supplier baru (Onboarding Supplier)."""
    supplier_name: str = Field(..., min_length=3, description="Nama badan usaha / rekanan")
    category: str = Field(default="PROTEIN", description="Kategori makro: PROTEIN, STAPLE, VEGETABLE")
    commodity: str = Field(default="DAGING_AYAM", description="Komoditas spesifik pangan")
    supported_items: List[str] = Field(default_factory=lambda: ["ITEM-AYAM-01"], description="Item ID bahan yang dipasok")
    halal_certified: bool = Field(..., description="Status sertifikasi Halal (wajib terverifikasi untuk SPPG)")
    halal_cert_number: Optional[str] = Field(None, description="Nomor registrasi sertifikat Halal resmi")
    unit_price_idr: float = Field(..., gt=0, description="Harga penawaran per satuan kg")
    daily_capacity_kg: float = Field(..., gt=0, description="Kapasitas harian pasokan (kg)")
    lead_time_hours: float = Field(default=3.0, gt=0, description="Estimasi durasi pengiriman tiba di SPPG (jam)")
    distance_km: float = Field(default=15.0, ge=0, description="Jarak gudang/peternakan ke SPPG (km)")
    reliability_rating: float = Field(default=85.0, ge=0, le=100, description="Rating performa rekam jejak")


class SupplierUpdateRequest(BaseModel):
    """Payload kontrak untuk pembaruan data supplier rekanan."""
    supplier_name: Optional[str] = Field(None, description="Nama baru rekanan")
    commodity: Optional[str] = Field(None, description="Komoditas spesifik")
    supported_items: Optional[List[str]] = Field(None, description="Daftar item didukung")
    halal_certified: Optional[bool] = Field(None, description="Status keaktifan halal")
    halal_cert_number: Optional[str] = Field(None, description="Nomor sertifikat halal")
    unit_price_idr: Optional[float] = Field(None, gt=0, description="Penyesuaian harga per kg")
    daily_capacity_kg: Optional[float] = Field(None, gt=0, description="Penyesuaian kapasitas harian")
    lead_time_hours: Optional[float] = Field(None, gt=0, description="Penyesuaian durasi kirim")
    distance_km: Optional[float] = Field(None, ge=0, description="Penyesuaian jarak")
    reliability_rating: Optional[float] = Field(None, ge=0, le=100, description="Penyesuaian rating")
    is_active: Optional[bool] = Field(None, description="Status aktif / non-aktif rekanan (Soft Delete)")


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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    po_download_url: str


# ==========================================
# 6. KONTRAK CONVERSATIONAL CHATBOT AGENT
# ==========================================

class ChatIntent(str, Enum):
    REPORT_INCIDENT = "REPORT_INCIDENT"
    REQUEST_REVISION = "REQUEST_REVISION"
    CONFIRM_APPROVAL = "CONFIRM_APPROVAL"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"
    MANAGE_SUPPLIER = "MANAGE_SUPPLIER"


class ChatActionRequired(str, Enum):
    NONE = "NONE"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    COMPLETED = "COMPLETED"


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="ID unik sesi obrolan")
    message: str = Field(..., min_length=1, description="Pesan obrolan teks dari pengguna")
    user_role: str = Field(default="Kepala SPPG", description="Peran pengguna dalam organisasi")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: ChatIntent
    action_required: ChatActionRequired
    preview_data: Optional[dict] = None
