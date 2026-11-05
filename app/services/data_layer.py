from typing import List, Optional
from app.data.mock_db import INVENTORY_DB, PORTION_REQUIREMENTS, SUPPLIERS_DB
from app.models.schemas import IncidentMetrics, InventoryItem, SupplierRecord


class DataLayerService:
    """
    Deterministic Data Layer Service untuk Satuan Pelayanan Pemenuhan Gizi (SPPG).
    
    Menjamin 'Zero Hallucination' dengan memproses kalkulasi inventaris,
    defisit kuantitatif, dan filter kepatuhan sertifikasi Halal secara murni
    pada lapisan program tanpa keterlibatan LLM.
    """

    def __init__(
        self,
        inventory_db: Optional[dict] = None,
        suppliers_db: Optional[dict] = None,
        portion_requirements: Optional[dict] = None,
    ):
        self._inventory = inventory_db if inventory_db is not None else INVENTORY_DB
        self._suppliers = suppliers_db if suppliers_db is not None else SUPPLIERS_DB
        self._portions = portion_requirements if portion_requirements is not None else PORTION_REQUIREMENTS

    def get_inventory_item(self, item_id: str) -> Optional[InventoryItem]:
        """Mengambil data inventaris bahan pangan berdasarkan item_id."""
        return self._inventory.get(item_id)

    def get_portion_ratio(self, item_id: str) -> float:
        """
        Mengambil rasio kebutuhan bahan per porsi (kg/porsi).
        Default fallback 0.05 kg jika tidak terdaftar.
        """
        return self._portions.get(item_id, 0.05)

    def calculate_metrics(
        self,
        item_id: str,
        target_portions: int = 3000,
    ) -> IncidentMetrics:
        """
        Menghitung metrik defisit bahan dan paparan risiko finansial secara matematis.

        Formula:
        1. Kebutuhan Dasar = target_portions * gramasi_per_porsi
        2. Kebutuhan dengan Buffer = Kebutuhan Dasar * 1.2 (Buffer 20% SOP SPPG)
        3. Defisit (kg) = max(0.0, Kebutuhan dengan Buffer - Stok Fisik Aktual)
        4. Sisa Freezer (kg) = max(0.0, Kapasitas Total - Kapasitas Terpakai)
        5. Paparan Risiko Finansial (IDR) = Defisit * Pagu Anggaran SOP per kg
        """
        item = self.get_inventory_item(item_id)
        if not item:
            raise ValueError(f"Item dengan ID '{item_id}' tidak ditemukan dalam basis data inventaris.")

        portion_ratio = self.get_portion_ratio(item_id)
        raw_needed_kg = target_portions * portion_ratio
        buffer_multiplier = 1.2

        # Kalkulasi defisit dengan margin pengaman 20%
        deficit_kg = max(0.0, round((raw_needed_kg * buffer_multiplier) - item.current_stock_kg, 2))

        # Sisa ruang penyimpanan pendingin
        freezer_available_kg = max(0.0, round(item.freezer_capacity_kg - item.freezer_occupied_kg, 2))

        # Estimasi nilai risiko finansial
        financial_risk_exposure = round(deficit_kg * item.sop_max_price_per_kg, 2)

        return IncidentMetrics(
            current_stock_kg=item.current_stock_kg,
            deficit_kg=deficit_kg,
            freezer_available_kg=freezer_available_kg,
            target_production_portions=target_portions,
            financial_risk_exposure_idr=financial_risk_exposure,
        )

    def get_eligible_suppliers(
        self,
        category: str,
        exclude_supplier_id: Optional[str] = None,
        max_distance_km: float = 100.0,
    ) -> List[SupplierRecord]:
        """
        Hard-Constraint Filter untuk supplier rekanan.
        
        Kriteria Seleksi:
        1. Kategori bahan sesuai.
        2. Status Sertifikat Halal Wajib Aktif (Zero Tolerance).
        3. Bukan supplier yang sedang mengalami disrupsi.
        4. Berada dalam radius toleransi logistik maksimal (default 100 km).
        """
        eligible: List[SupplierRecord] = []
        target_cat = category.strip().upper()

        for supplier in self._suppliers.values():
            # 1. Kategori bahan
            if supplier.category.strip().upper() != target_cat:
                continue

            # 2. Hard Gate: Sertifikasi Halal wajib True
            if not supplier.halal_certified:
                continue

            # 3. Exclude supplier terdampak insiden
            if exclude_supplier_id and supplier.supplier_id == exclude_supplier_id:
                continue

            # 4. Batasan jarak logistik
            if supplier.distance_km > max_distance_km:
                continue

            eligible.append(supplier)

        # Diurutkan berdasarkan rating reliabilitas tertinggi lalu harga terendah
        return sorted(
            eligible,
            key=lambda s: (-s.reliability_rating, s.unit_price_idr),
        )


# Global singleton instance untuk reuse di FastAPI & LangGraph Nodes
data_layer_service = DataLayerService()

