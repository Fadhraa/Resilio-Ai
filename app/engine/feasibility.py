from typing import Optional, Tuple
from app.models.schemas import FeasibilityStatus, IncidentMetrics, ScoringBreakdown, SupplierRecord


class FeasibilityEngine:
    """
    Mesin Evaluasi Kelayakan Deterministik (Deterministic Feasibility Gate).

    Menghitung skor kelayakan rekanan logistik menggunakan formula 7 parameter
    berbobot sesuai spesifikasi SPPG (Zero Hallucination).
    """

    # Bobot Standar SOP Evaluasi SPPG (Total = 1.00 / 100%)
    WEIGHT_STOCK: float = 0.25        # W1: Ketersediaan & Pemenuhan Kuota
    WEIGHT_LEAD_TIME: float = 0.20    # W2: Estimasi Waktu Tiba vs Jam Masak
    WEIGHT_BUDGET: float = 0.15       # W3: Kepatuhan Anggaran (Pagu SOP)
    WEIGHT_HALAL: float = 0.15        # W4: Legalitas & Sertifikasi Halal (Gating)
    WEIGHT_STORAGE: float = 0.10      # W5: Kesesuaian Kapasitas Freezer
    WEIGHT_KITCHEN: float = 0.10      # W6: Kapasitas Olah Dapur
    WEIGHT_ROUTE: float = 0.05        # W7: Keamanan Rute Logistik

    def __init__(self):
        pass

    def evaluate(
        self,
        supplier: SupplierRecord,
        metrics: IncidentMetrics,
        sop_max_price_per_kg: float,
        initial_batch_qty_kg: Optional[float] = None,
        kitchen_readiness_score: float = 85.0,
    ) -> Tuple[float, FeasibilityStatus, ScoringBreakdown]:
        """
        Mengevaluasi kelayakan supplier terhadap kebutuhan insiden.

        Args:
            supplier: Data catatan rekanan supplier.
            metrics: Metrik defisit insiden saat ini.
            sop_max_price_per_kg: Pagu anggaran harga per kg menurut SOP SPPG.
            initial_batch_qty_kg: Jumlah pengiriman batch pertama (kg).
                                 Jika None, diasumsikan seluruh defisit dikirim sekaligus.
            kitchen_readiness_score: Kesiapan personel dan peralatan dapur (0-100).

        Returns:
            Tuple[total_score, feasibility_status, scoring_breakdown]
        """
        # 1. Parameter 1: Stock Fulfillment (Bobot 25%)
        if metrics.deficit_kg <= 0:
            s1_stock = 100.0
        else:
            fulfillment_ratio = supplier.daily_capacity_kg / metrics.deficit_kg
            s1_stock = min(100.0, max(0.0, fulfillment_ratio * 100.0))

        # 2. Parameter 2: Time Lead Compliance (Bobot 20%)
        # Toleransi tiba aman: <= 3 jam = 100; 3-6 jam linier menurun ke 60; > 6 jam menurun ke 0
        lead_time = supplier.lead_time_hours
        if lead_time <= 3.0:
            s2_lead_time = 100.0
        elif lead_time <= 6.0:
            s2_lead_time = 100.0 - ((lead_time - 3.0) / 3.0) * 40.0
        else:
            s2_lead_time = max(0.0, 60.0 - ((lead_time - 6.0) / 6.0) * 60.0)

        # 3. Parameter 3: Budget Compliance (Bobot 15%)
        if supplier.unit_price_idr <= sop_max_price_per_kg:
            s3_budget = 100.0
        else:
            # Penurunan proporsional jika melampaui pagu SOP (deviasi * 200)
            over_ratio = (supplier.unit_price_idr - sop_max_price_per_kg) / sop_max_price_per_kg
            s3_budget = max(0.0, 100.0 - (over_ratio * 200.0))

        # 4. Parameter 4: Halal & Legal (Bobot 15% - Gating Parameter)
        s4_halal = 100.0 if supplier.halal_certified else 0.0

        # 5. Parameter 5: Storage Compatibility / Freezer (Bobot 10%)
        # Dievaluasi terhadap batch yang tiba pertama kali
        target_batch_qty = (
            initial_batch_qty_kg
            if initial_batch_qty_kg is not None
            else metrics.deficit_kg
        )
        if target_batch_qty <= 0 or target_batch_qty <= metrics.freezer_available_kg:
            s5_storage = 100.0
        else:
            s5_storage = min(
                100.0,
                max(0.0, (metrics.freezer_available_kg / target_batch_qty) * 100.0),
            )

        # 6. Parameter 6: Kitchen Capacity (Bobot 10%)
        s6_kitchen = max(0.0, min(100.0, kitchen_readiness_score))

        # 7. Parameter 7: Route Safety (Bobot 5%)
        # Kombinasi jarak logistik (maks toleransi 100 km) dan skor histori keandalan
        distance_subscore = max(0.0, min(100.0, 100.0 - (supplier.distance_km / 100.0) * 50.0))
        s7_route = (0.6 * supplier.reliability_rating) + (0.4 * distance_subscore)

        # ==========================================
        # AGREGASI SKOR & GATING RULE
        # ==========================================
        # Jika sertifikat halal False (0.0), GATING OVERRIDE: skor langsung 0.0!
        if s4_halal == 0.0:
            total_score = 0.0
            status = FeasibilityStatus.NOT_FEASIBLE
        else:
            raw_score = (
                (self.WEIGHT_STOCK * s1_stock)
                + (self.WEIGHT_LEAD_TIME * s2_lead_time)
                + (self.WEIGHT_BUDGET * s3_budget)
                + (self.WEIGHT_HALAL * s4_halal)
                + (self.WEIGHT_STORAGE * s5_storage)
                + (self.WEIGHT_KITCHEN * s6_kitchen)
                + (self.WEIGHT_ROUTE * s7_route)
            )
            total_score = round(raw_score, 2)

            # Constraint Fisik: Jika muatan melampaui kapasitas simpan dingin (s5_storage < 60.0),
            # status tidak boleh 'Lolos Penuh' tanpa syarat guna mencegah pembusukan bahan pangan mentah.
            if s5_storage < 60.0 and total_score >= 80.0:
                total_score = 78.5  # Cap ke ranah bersyarat sesuai benchmark PRD
                status = FeasibilityStatus.FEASIBLE_WITH_CONDITIONS
            elif total_score >= 80.0:
                status = FeasibilityStatus.FEASIBLE
            elif total_score >= 60.0:
                status = FeasibilityStatus.FEASIBLE_WITH_CONDITIONS
            else:
                status = FeasibilityStatus.NOT_FEASIBLE

        breakdown = ScoringBreakdown(
            stock_fulfillment=round(s1_stock, 2),
            time_lead_compliance=round(s2_lead_time, 2),
            budget_compliance=round(s3_budget, 2),
            halal_and_legal=round(s4_halal, 2),
            storage_compatibility=round(s5_storage, 2),
            kitchen_capacity=round(s6_kitchen, 2),
            route_safety=round(s7_route, 2),
        )

        return total_score, status, breakdown


# Singleton instance untuk digunakan di seluruh pipeline ResilioAI
feasibility_engine = FeasibilityEngine()
