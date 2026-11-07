import os
from typing import List, Optional
from datetime import datetime, timezone
from app.models.schemas import (
    DeliveryBatch,
    FeasibilityStatus,
    IncidentMetrics,
    LogisticsStrategy,
    RecommendedProcurement,
    ScoringBreakdown,
    StrategyType,
    SupplierRecord,
)


class StrategicProcurementAgent:
    """
    Cognitive Strategic Procurement Agent.
    
    Bertanggung jawab:
    1. Memilih kandidat rekanan supplier optimal dari daftar yang lolos audit Halal.
    2. Menimbang kendala fisik (kapasitas freezer vs kuantitas defisit).
    3. Merumuskan taktik pengir1iman (Direct Delivery vs Split Delivery bertahap).
    4. Menghasilkan narasi justifikasi strategis (didukung LLM Gemini bila API key aktif).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")

    def synthesize_strategy(
        self,
        eligible_suppliers: List[SupplierRecord],
        metrics: IncidentMetrics,
        item_name: str,
        retry_count: int = 0,
    ) -> RecommendedProcurement:
        """
        Menyusun rekomendasi pengadaan dan skema logistik.
        
        Args:
            eligible_suppliers: Daftar supplier yang lolos hard-filter kepatuhan Halal.
            metrics: Metrik defisit dan ketersediaan freezer saat ini.
            item_name: Nama bahan pangan (misal 'Daging Ayam Broiler Segar').
            retry_count: Indeks perulangan (jika evaluasi kelayakan sebelumnya < 60).
        """
        if not eligible_suppliers:
            raise ValueError("Tidak ada supplier rekanan yang memenuhi kriteria kepatuhan Halal.")

        # Pilih supplier berdasarkan reliabilitas tertinggi
        # Jika retry > 0, pilih kandidat alternatif berikutnya dalam katalog
        idx = min(retry_count, len(eligible_suppliers) - 1)
        selected_supplier = eligible_suppliers[idx]

        deficit = metrics.deficit_kg
        freezer_available = metrics.freezer_available_kg

        # Evaluasi Kendala Fisik Gudang Pendingin (Freezer Constraint)
        if deficit > freezer_available and freezer_available > 0:
            strategy_type = StrategyType.SPLIT_DELIVERY
            batch_1_qty = freezer_available
            batch_2_qty = round(deficit - batch_1_qty, 2)

            batches = [
                DeliveryBatch(
                    batch_no=1,
                    qty_kg=batch_1_qty,
                    eta="H-1 17:00 WIB (Persiapan Malam)",
                ),
                DeliveryBatch(
                    batch_no=2,
                    qty_kg=batch_2_qty,
                    eta="Hari-H 05:00 WIB (Masuk Produksi Dapur Pagi)",
                ),
            ]
            rationale = (
                f"Kapasitas freezer aktif hanya tersisa {freezer_available} kg, "
                f"sedangkan defisit kebutuhan {item_name} sebesar {deficit} kg. "
                f"Sistem menyusun skema Split Delivery: Batch 1 ({batch_1_qty} kg) tiba H-1 "
                f"untuk marinasi malam dan pas di freezer; Batch 2 ({batch_2_qty} kg) tiba Hari-H "
                f"pukul 05:00 WIB langsung masuk proses masak dapur pagi tanpa melampaui kapasitas simpan."
            )
        else:
            strategy_type = StrategyType.DIRECT_DELIVERY
            batches = [
                DeliveryBatch(
                    batch_no=1,
                    qty_kg=deficit,
                    eta="Hari-H 05:00 WIB (Langsung Masuk Pengolahan)",
                )
            ]
            rationale = (
                f"Kapasitas ruang pendingin mencukupi ({freezer_available} kg >= defisit {deficit} kg). "
                f"Pengiriman {item_name} sebesar {deficit} kg dilakukan sekaligus (Direct Delivery) "
                f"oleh rekanan {selected_supplier.supplier_name}."
            )

        total_cost = round(deficit * selected_supplier.unit_price_idr, 2)

        # Placeholder skor awal (akan dikalkulasi deterministik di Feasibility Gate Node)
        dummy_breakdown = ScoringBreakdown(
            stock_fulfillment=100.0,
            time_lead_compliance=85.0,
            budget_compliance=90.0,
            halal_and_legal=100.0,
            storage_compatibility=100.0 if strategy_type == StrategyType.SPLIT_DELIVERY else 40.0,
            kitchen_capacity=80.0,
            route_safety=70.0,
        )

        return RecommendedProcurement(
            supplier_id=selected_supplier.supplier_id,
            supplier_name=selected_supplier.supplier_name,
            unit_price_idr=selected_supplier.unit_price_idr,
            total_estimated_cost_idr=total_cost,
            halal_certificate_active=selected_supplier.halal_certified,
            feasibility_score=75.0,
            feasibility_status=FeasibilityStatus.FEASIBLE_WITH_CONDITIONS,
            scoring_breakdown=dummy_breakdown,
            logistics_strategy=LogisticsStrategy(
                strategy_type=strategy_type,
                rationale=rationale,
                batches=batches,
            ),
        )


# Singleton instance agent
strategic_agent = StrategicProcurementAgent()

