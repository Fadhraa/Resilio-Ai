import {
  IncidentDecisionResponse,
  PurchaseOrderResponse,
  SupplierRecord,
  InventoryItem,
} from "@/types/incident";

/**
 * Mock Data Skenario Nyata SPPG:
 * Gangguan armada supplier utama ayam potong akibat banjir jalur Pantura.
 */
export const mockIncidentDecision: IncidentDecisionResponse = {
  incident_id: "INC-2026-001",
  item_id: "ITEM-AYAM-01",
  item_name: "Daging Ayam Broiler Segar",
  metrics: {
    current_stock_kg: 80.0,
    deficit_kg: 64.0,
    freezer_available_kg: 20.0,
    target_production_portions: 3000,
  },
  recommended_procurement: {
    supplier_id: "SUP-ALT-02",
    supplier_name: "PT Berkah Unggas Jaya",
    unit_price_idr: 36500,
    total_estimated_cost_idr: 2336000,
    halal_certificate_active: true,
    feasibility_score: 78.5,
    feasibility_status: "FEASIBLE_WITH_CONDITIONS",
    scoring_breakdown: {
      stock_fulfillment: 100.0,     // Mampu memasok 100% kuota defisit (64 kg)
      time_lead_compliance: 85.0,  // Tiba tepat waktu sebelum jam masak
      budget_compliance: 90.0,     // Rp 36.500 vs pagu SOP Rp 40.000 (di bawah pagu)
      halal_and_legal: 100.0,      // Sertifikat Halal BPJPH aktif (Wajib 100)
      storage_compatibility: 40.0, // Restriksi fisik: Freezer hanya muat 20 kg
      kitchen_capacity: 80.0,      // Kru dapur siap menerima batch pagi
      route_safety: 70.0,          // Melewati rute alternatif non-banjir
    },
    logistics_strategy: {
      strategy_type: "SPLIT_DELIVERY",
      rationale:
        "Kapasitas freezer gudang hanya tersisa 20 kg. Batch 1 (20 kg) dikirim H-1 pukul 17:00 WIB untuk persiapan malam dan disimpan di freezer. Batch 2 (44 kg) dikirim Hari-H pukul 05:00 WIB dan langsung masuk ke proses pengolahan dapur subuh tanpa membebani fasilitas pendingin.",
      batches: [
        {
          batch_no: 1,
          qty_kg: 20.0,
          eta: "2026-10-04T17:00:00+07:00",
        },
        {
          batch_no: 2,
          qty_kg: 44.0,
          eta: "2026-10-05T05:00:00+07:00",
        },
      ],
    },
  },
  audit_trail: [
    {
      stage: "DATA_AGGREGATION",
      status: "DETERMINISTIC_PASS",
      message:
        "Stok gudang aktual (80 kg) dan defisit (64 kg) dihitung secara matematis presisi tanpa keterlibatan LLM.",
      timestamp: "2026-10-04T10:00:01+07:00",
    },
    {
      stage: "COMPLIANCE_FILTER",
      status: "DETERMINISTIC_PASS",
      message:
        "Katalog supplier difilter: 2 supplier non-halal dan 1 supplier di luar radius logistik langsung dieliminasi.",
      timestamp: "2026-10-04T10:00:02+07:00",
    },
    {
      stage: "STRATEGY_SYNTHESIS",
      status: "AGENT_REASONING_PASS",
      message:
        "Agen LLM mendeteksi keterbatasan kapasitas freezer (hanya 20 kg) dan merumuskan skema mitigasi Split Delivery 2 tahap.",
      timestamp: "2026-10-04T10:00:03+07:00",
    },
    {
      stage: "FEASIBILITY_GATE",
      status: "VERIFIED",
      message:
        "Skor kelayakan 78.5/100 dihitung secara deterministik melalui matriks pembobotan 7 parameter.",
      timestamp: "2026-10-04T10:00:04+07:00",
    },
  ],
};

export const mockPoSuccess: PurchaseOrderResponse = {
  status: "SUCCESS",
  po_number: "PO-SPPG-2026-10-0042",
  incident_id: "INC-2026-001",
  supplier_id: "SUP-ALT-02",
  supplier_name: "PT Berkah Unggas Jaya",
  item_id: "ITEM-AYAM-01",
  approved_qty_kg: 64.0,
  unit_price_idr: 36500,
  total_amount_idr: 2336000,
  approver_name: "Budi Santoso, S.T. (Kepala SPPG)",
  generated_at: new Date().toISOString(),
  po_download_url: "/mock/po/PO-SPPG-2026-10-0042.pdf",
};

export const mockSuppliers: SupplierRecord[] = [
  {
    supplier_id: "SUP-UTAMA-01",
    supplier_name: "PT Unggas Sejahtera Nusantara",
    category: "PROTEIN",
    commodity: "DAGING_AYAM",
    supported_items: ["ITEM-AYAM-01"],
    halal_certified: true,
    halal_cert_number: "ID32110000123450124",
    unit_price_idr: 37500,
    daily_capacity_kg: 300,
    lead_time_hours: 2.5,
    distance_km: 12.0,
    reliability_rating: 96.0,
    is_active: true,
  },
  {
    supplier_id: "SUP-ALT-02",
    supplier_name: "PT Berkah Unggas Jaya",
    category: "PROTEIN",
    commodity: "DAGING_AYAM",
    supported_items: ["ITEM-AYAM-01"],
    halal_certified: true,
    halal_cert_number: "ID32110000897650324",
    unit_price_idr: 36500,
    daily_capacity_kg: 140,
    lead_time_hours: 4.0,
    distance_km: 22.0,
    reliability_rating: 95.0,
    is_active: true,
  },
  {
    supplier_id: "SUP-REG-04",
    supplier_name: "CV Berkah Barokah Tahu",
    category: "PROTEIN",
    commodity: "TAHU",
    supported_items: ["ITEM-TAHU-01"],
    halal_certified: true,
    halal_cert_number: "ID32110000789010124",
    unit_price_idr: 18000,
    daily_capacity_kg: 200,
    lead_time_hours: 2.5,
    distance_km: 14.0,
    reliability_rating: 95.0,
    is_active: true,
  },
  {
    supplier_id: "SUP-REG-05",
    supplier_name: "CV Berkah Tempe Alami",
    category: "PROTEIN",
    commodity: "TEMPE",
    supported_items: ["ITEM-TEMPE-01"],
    halal_certified: true,
    halal_cert_number: "ID32110000789010224",
    unit_price_idr: 16000,
    daily_capacity_kg: 180,
    lead_time_hours: 2.5,
    distance_km: 15.0,
    reliability_rating: 94.0,
    is_active: true,
  },
  {
    supplier_id: "SUP-TELUR-01",
    supplier_name: "CV Sumber Telur Mandiri",
    category: "PROTEIN",
    commodity: "TELUR_AYAM",
    supported_items: ["ITEM-TELUR-01"],
    halal_certified: true,
    halal_cert_number: "ID32110000445560624",
    unit_price_idr: 28500,
    daily_capacity_kg: 500,
    lead_time_hours: 2.0,
    distance_km: 12.0,
    reliability_rating: 93.0,
    is_active: true,
  },
];

export const mockInventory: InventoryItem[] = [
  {
    item_id: "ITEM-AYAM-01",
    item_name: "Daging Ayam Broiler Segar",
    category: "PROTEIN",
    current_stock_kg: 80.0,
    safety_stock_kg: 50.0,
    freezer_capacity_kg: 100.0,
    freezer_occupied_kg: 80.0,
    sop_max_price_per_kg: 40000.0,
  },
  {
    item_id: "ITEM-BERAS-01",
    item_name: "Beras Putih Ramos Premium",
    category: "STAPLE",
    current_stock_kg: 520.0,
    safety_stock_kg: 200.0,
    freezer_capacity_kg: 0.0,
    freezer_occupied_kg: 0.0,
    sop_max_price_per_kg: 16000.0,
  },
  {
    item_id: "ITEM-TELUR-01",
    item_name: "Telur Ayam Negeri Grade A",
    category: "PROTEIN",
    current_stock_kg: 135.0,
    safety_stock_kg: 60.0,
    freezer_capacity_kg: 50.0,
    freezer_occupied_kg: 25.0,
    sop_max_price_per_kg: 32000.0,
  },
  {
    item_id: "ITEM-WORTEL-01",
    item_name: "Sayur Wortel & Bayam Segar",
    category: "VEGETABLE",
    current_stock_kg: 90.0,
    safety_stock_kg: 40.0,
    freezer_capacity_kg: 40.0,
    freezer_occupied_kg: 20.0,
    sop_max_price_per_kg: 18000.0,
  },
];

export const mockCircularLetters: any[] = [];

export const mockPurchaseOrdersList: any[] = [];

