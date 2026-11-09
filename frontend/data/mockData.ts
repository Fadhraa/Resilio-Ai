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
    supplier_id: "SUP-ALT-01",
    supplier_name: "CV Berkah Ternak Barokah",
    category: "PROTEIN",
    commodity: "DAGING_AYAM",
    supported_items: ["ITEM-AYAM-01"],
    halal_certified: true,
    halal_cert_number: "ID32110000543210224",
    unit_price_idr: 39500,
    daily_capacity_kg: 150,
    lead_time_hours: 3.5,
    distance_km: 18.0,
    reliability_rating: 92.0,
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
    supplier_id: "SUP-ALT-03",
    supplier_name: "UD Ayam Murah Meriah (Uncertified)",
    category: "PROTEIN",
    commodity: "DAGING_AYAM",
    supported_items: ["ITEM-AYAM-01"],
    halal_certified: false,
    unit_price_idr: 32000,
    daily_capacity_kg: 200,
    lead_time_hours: 2.0,
    distance_km: 10.0,
    reliability_rating: 70.0,
    is_active: true,
  },
  {
    supplier_id: "SUP-SAPI-01",
    supplier_name: "PT Lembu Barokah Nusantara",
    category: "PROTEIN",
    commodity: "DAGING_SAPI",
    supported_items: ["ITEM-SAPI-01"],
    halal_certified: true,
    halal_cert_number: "ID32110000998870424",
    unit_price_idr: 128000,
    daily_capacity_kg: 200,
    lead_time_hours: 4.5,
    distance_km: 28.0,
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
    halal_cert_number: "ID32110000776650524",
    unit_price_idr: 28500,
    daily_capacity_kg: 500,
    lead_time_hours: 2.0,
    distance_km: 15.0,
    reliability_rating: 97.0,
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

export const mockCircularLetters = [
  {
    letter_id: "SE-SPPG-2026-001",
    letter_number: "042/SE/SPPG-SKB/XI/2026",
    title: "Instruksi Mitigasi Defisit Pasokan Daging Ayam Darurat SPPG Sukabumi",
    incident_id: "INC-20261105-01",
    item_id: "ITEM-AYAM-01",
    deficit_kg: 64.0,
    supplier_id: "SUP-ALT-02",
    supplier_name: "PT Berkah Unggas Jaya",
    issued_date: "2026-11-05",
    signer_name: "Fadhra Dzaki, S.T., M.Kom.",
    signer_role: "Kepala Satuan Pelayanan Pemenuhan Gizi (SPPG)",
    content_text:
      "Menindaklanjuti kegagalan pasokan rekanan utama PT Unggas Sejahtera Nusantara akibat kerusakan armada pendingin, dengan ini diinstruksikan pengalihan pasokan 64 kg daging ayam broiler kepada rekanan cadangan PT Berkah Unggas Jaya dengan mekanisme pengiriman bertahap (staggered) 2 batch @ 32 kg guna menjaga kepatuhan kapasitas penyimpanan dingin (freezer) SPPG.",
    status: "ISSUED" as const,
    created_at: "2026-11-05T08:30:00Z",
  },
  {
    letter_id: "SE-SPPG-2026-002",
    letter_number: "043/SE/SPPG-SKB/XI/2026",
    title: "Penetapan Pemasok Beras & Telur Terverifikasi Halal BPJPH Periode Q4 2026",
    incident_id: "INC-20261107-02",
    item_id: "ITEM-TELUR-01",
    deficit_kg: 100.0,
    supplier_id: "SUP-TELUR-01",
    supplier_name: "CV Sumber Telur Mandiri",
    issued_date: "2026-11-07",
    signer_name: "Fadhra Dzaki, S.T., M.Kom.",
    signer_role: "Kepala Satuan Pelayanan Pemenuhan Gizi (SPPG)",
    content_text:
      "Berdasarkan hasil audit deterministik pemenuhan UU No. 33 Tahun 2014 tentang Jaminan Produk Halal, CV Sumber Telur Mandiri ditetapkan sebagai pemasok resmi komoditas telur ras segar dengan kuota alokasi harian 100 kg dan rating keandalan 93%.",
    status: "ISSUED" as const,
    created_at: "2026-11-07T10:15:00Z",
  },
];

export const mockPurchaseOrdersList = [
  {
    po_number: "PO-SPPG-2026-001",
    incident_id: "INC-20261105-01",
    supplier_id: "SUP-ALT-02",
    supplier_name: "PT Berkah Unggas Jaya",
    item_id: "ITEM-AYAM-01",
    approved_qty_kg: 64.0,
    unit_price_idr: 38000.0,
    total_amount_idr: 2432000.0,
    logistics_strategy: {
      strategy_type: "SPLIT_DELIVERY" as const,
      rationale: "Pengiriman dibagi 2 batch agar tidak melebihi sisa kapasitas freezer SPPG (20 kg sedia).",
      batches: [
        { batch_no: 1, qty_kg: 32.0, eta: "2026-11-05T09:30:00Z" },
        { batch_no: 2, qty_kg: 32.0, eta: "2026-11-05T13:00:00Z" },
      ],
    },
    approver_name: "Fadhra Dzaki, S.T., M.Kom.",
    status: "APPROVED",
    po_download_url: "/api/v1/orders/PO-SPPG-2026-001/pdf",
    generated_at: "2026-11-05T08:35:00Z",
  },
  {
    po_number: "PO-SPPG-2026-002",
    incident_id: "INC-20261107-02",
    supplier_id: "SUP-TELUR-01",
    supplier_name: "CV Sumber Telur Mandiri",
    item_id: "ITEM-TELUR-01",
    approved_qty_kg: 100.0,
    unit_price_idr: 28500.0,
    total_amount_idr: 2850000.0,
    logistics_strategy: {
      strategy_type: "DIRECT_DELIVERY" as const,
      rationale: "Pengiriman langsung 1 batch telur segar untuk jadwal sarapan.",
      batches: [{ batch_no: 1, qty_kg: 100.0, eta: "2026-11-07T06:00:00Z" }],
    },
    approver_name: "Fadhra Dzaki, S.T., M.Kom.",
    status: "COMPLETED",
    po_download_url: "/api/v1/orders/PO-SPPG-2026-002/pdf",
    generated_at: "2026-11-07T10:20:00Z",
  },
];

