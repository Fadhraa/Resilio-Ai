// frontend/types/incident.ts

/**
 * ============================================================================
 * RESILIO-AI TYPE CONTRACTS
 * Sinkron 1:1 dengan Backend Schemas (app/models/schemas.py)
 * ============================================================================
 */

// 1. Tipe Gangguan Rantai Pasok (Disruption Type)
// Mengkategorikan jenis masalah yang terjadi di lapangan
export type DisruptionType = 
  | "SUPPLIER_DISRUPTION"   // Pembatalan/keterlambatan dari supplier
  | "WEATHER_FLOOD"         // Cuaca ekstrem/banjir di jalur logistik
  | "PRICE_HIKE"            // Kenaikan harga mendadak melampaui SOP
  | "QUALITY_REJECTION"     // Kualitas bahan tidak lolos uji penerimaan
  | "LOGISTICS_BREAKDOWN";  // Kerusakan armada angkut di jalan

// 2. Status Evaluasi Kelayakan (Feasibility Status)
// Ditentukan oleh Feasibility Scoring Engine (Matrix 7 Parameter)
export type FeasibilityStatus = 
  | "FEASIBLE"                 // Skor >= 80: Lolos penuh, aman dieksekusi
  | "FEASIBLE_WITH_CONDITIONS" // Skor 60-79: Wajib mitigasi split delivery
  | "NOT_FEASIBLE";            // Skor < 60: Ditolak sistem (memicu retry)

// 3. Jenis Strategi Logistik (Strategy Type)
// Ditentukan oleh Strategic Procurement Agent (LLM)
export type StrategyType = 
  | "DIRECT_DELIVERY"   // Pengiriman langsung 1x jika freezer cukup
  | "SPLIT_DELIVERY"    // Pengiriman bertahap (batch) jika freezer terbatas
  | "BUFFER_STAGGERED"; // Pengiriman berkala dengan safety buffer

// 4. Request Payload untuk Memicu Insiden (POST /api/v1/incidents/trigger)
export interface IncidentTriggerRequest {
  item_id: string;                      // ID bahan pangan (misal: "ITEM-AYAM-01")
  disruption_type: DisruptionType;       // Jenis gangguan
  affected_supplier_id: string;          // Supplier yang mengalami masalah
  estimated_duration_days: number;       // Estimasi hari gangguan berlangsung
  incident_notes?: string;               // Catatan bebas laporan lapangan
}

// 5. Response Awal Pemicu Insiden (Synchronous Ack)
export interface IncidentTriggerResponse {
  incident_id: string;  // ID unik tiket insiden (misal: "INC-2026-001")
  status: string;       // "PROCESSING"
  stream_url: string;   // Endpoint SSE untuk memantau progress agent
}

// 6. Matriks Rincian Skor 7 Parameter Deterministik
// Formula: Total = sum(Bobot * Skor)
export interface ScoringBreakdown {
  stock_fulfillment: number;      // Bobot 25%: Kemampuan supplier memenuhi defisit
  time_lead_compliance: number;   // Bobot 20%: Waktu tiba vs jam produksi dapur
  budget_compliance: number;      // Bobot 15%: Kepatuhan harga terhadap pagu SOP
  halal_and_legal: number;        // Bobot 15%: Gating parameter (Wajib 100, jika 0 total 0)
  storage_compatibility: number;  // Bobot 10%: Kesesuaian volume batch dengan sisa freezer
  kitchen_capacity: number;       // Bobot 10%: Kesiapan personel dan peralatan dapur
  route_safety: number;           // Bobot 5%: Keamanan jalur distribusi dari titik suplai
}

// 7. Pengiriman Bertahap (Delivery Batch)
export interface DeliveryBatch {
  batch_no: number;   // Nomor urut pengiriman (1, 2, dst)
  qty_kg: number;     // Kuantitas bahan (kg) per batch
  eta: string;        // Estimasi kedatangan (ISO string format)
}

// 8. Strategi Logistik Terstruktur
export interface LogisticsStrategy {
  strategy_type: StrategyType;
  rationale: string;             // Alasan penalaran logis dari AI Agent
  batches: DeliveryBatch[];      // Jadwal pembagian pengiriman
}

// 9. Rekomendasi Pengadaan Pengganti
export interface RecommendedProcurement {
  supplier_id: string;
  supplier_name: string;
  unit_price_idr: number;
  total_estimated_cost_idr: number;
  halal_certificate_active: boolean;
  feasibility_score: number;
  feasibility_status: FeasibilityStatus;
  scoring_breakdown: ScoringBreakdown;
  logistics_strategy: LogisticsStrategy;
}

// 10. Catatan Audit Jejak Keputusan (Immutable Audit Trail)
export interface AuditTrailStep {
  stage: string;       // Tahapan (DATA_AGGREGATION, COMPLIANCE_FILTER, dsb)
  status: string;      // DETERMINISTIC_PASS, AGENT_REASONING_PASS, dsb
  message: string;     // Pesan penjelasan verifikasi
  timestamp: string;   // Waktu pencatatan
}

// 11. Response Keputusan Lengkap saat Menunggu Persetujuan
// (GET /api/v1/incidents/{incident_id}/decision)
export interface IncidentDecisionResponse {
  incident_id: string;
  item_id: string;
  item_name: string;
  metrics: {
    current_stock_kg: number;
    deficit_kg: number;
    freezer_available_kg: number;
    target_production_portions: number;
  };
  recommended_procurement: RecommendedProcurement | null;
  audit_trail: AuditTrailStep[];
}

// 12. Request Otorisasi Manusia (POST /api/v1/incidents/{incident_id}/approve)
export interface ApprovalRequest {
  incident_id: string;
  action: "APPROVE" | "REJECT" | "MODIFY";
  approved_qty_kg: number;
  approver_name: string;
  approver_notes?: string;
}

// 13. Response Penerbitan Purchase Order Resmi
export interface PurchaseOrderResponse {
  status: string;
  po_number: string;
  generated_at: string;
  po_download_url: string;
}

// 14. Event Schema untuk Real-Time Streaming (SSE)
// (GET /api/v1/incidents/{incident_id}/stream)
export interface PipelineStreamEvent {
  event: 
    | "node_started" 
    | "node_completed" 
    | "workflow_waiting_approval" 
    | "workflow_finished" 
    | "workflow_error";
  node?: string;
  timestamp?: string;
  data?: {
    node?: string;
    deficit_kg?: number;
    current_stock_kg?: number;
    freezer_remaining_kg?: number;
    score?: number;
    status?: string;
    model?: string;
    incident_id?: string;
    decision_ready?: boolean;
    message?: string;
  };
}

