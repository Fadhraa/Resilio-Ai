import unittest
from app.engine.feasibility import FeasibilityEngine, feasibility_engine
from app.models.schemas import FeasibilityStatus, IncidentMetrics, SupplierRecord


class TestFeasibilityEngine(unittest.TestCase):
    """Pengujian Unit untuk Feasibility Scoring Engine (Deterministic Gate)."""

    def setUp(self):
        # Skenario standar SPPG (Defisit 64 kg, Freezer sisa 20 kg, Pagu SOP Rp 42.000)
        self.metrics = IncidentMetrics(
            current_stock_kg=80.0,
            deficit_kg=64.0,
            freezer_available_kg=20.0,
            target_production_portions=3000,
            financial_risk_exposure_idr=2688000.0,
        )
        self.sop_max_price = 42000.0

    def test_evaluate_fully_feasible_supplier(self):
        """
        Supplier prima: Kapasitas besar (150 kg), lead time 2.5 jam,
        harga di bawah pagu (Rp 38.000), halal aktif, dan muatan batch muat di freezer.
        """
        supplier = SupplierRecord(
            supplier_id="SUP-ALT-PRIMA",
            supplier_name="PT Supplier Prima Halal",
            category="PROTEIN",
            halal_certified=True,
            halal_cert_number="ID12345",
            unit_price_idr=38000.0,
            daily_capacity_kg=150.0,
            lead_time_hours=2.5,
            distance_km=15.0,
            reliability_rating=95.0,
        )

        # Batch pertama 20 kg (muat di freezer sisa 20 kg)
        score, status, breakdown = feasibility_engine.evaluate(
            supplier=supplier,
            metrics=self.metrics,
            sop_max_price_per_kg=self.sop_max_price,
            initial_batch_qty_kg=20.0,
        )

        self.assertGreaterEqual(score, 80.0)
        self.assertEqual(status, FeasibilityStatus.FEASIBLE)
        self.assertEqual(breakdown.stock_fulfillment, 100.0)
        self.assertEqual(breakdown.time_lead_compliance, 100.0)
        self.assertEqual(breakdown.budget_compliance, 100.0)
        self.assertEqual(breakdown.halal_and_legal, 100.0)
        self.assertEqual(breakdown.storage_compatibility, 100.0)

    def test_evaluate_halal_gating_override(self):
        """
        Validasi Gating Parameter:
        Meskipun harga sangat murah dan kapasitas besar, jika halal_certified=False,
        maka total skor wajib langsung 0.0 dan status NOT_FEASIBLE.
        """
        non_halal_supplier = SupplierRecord(
            supplier_id="SUP-NON-HALAL",
            supplier_name="UD Non Halal",
            category="PROTEIN",
            halal_certified=False,
            halal_cert_number=None,
            unit_price_idr=25000.0,
            daily_capacity_kg=500.0,
            lead_time_hours=1.0,
            distance_km=5.0,
            reliability_rating=99.0,
        )

        score, status, breakdown = feasibility_engine.evaluate(
            supplier=non_halal_supplier,
            metrics=self.metrics,
            sop_max_price_per_kg=self.sop_max_price,
        )

        self.assertEqual(score, 0.0)
        self.assertEqual(status, FeasibilityStatus.NOT_FEASIBLE)
        self.assertEqual(breakdown.halal_and_legal, 0.0)

    def test_evaluate_storage_constraint_leads_to_conditional(self):
        """
        Pengiriman langsung 64 kg saat freezer hanya sisa 20 kg:
        Storage compatibility menurun drastis, menurunkan skor ke ranah 60-79.9
        (FEASIBLE_WITH_CONDITIONS), menuntut mekanisme split-delivery.
        """
        supplier = SupplierRecord(
            supplier_id="SUP-ALT-02",
            supplier_name="PT Berkah Unggas Jaya",
            category="PROTEIN",
            halal_certified=True,
            halal_cert_number="ID999",
            unit_price_idr=38000.0,
            daily_capacity_kg=120.0,
            lead_time_hours=4.0,
            distance_km=22.0,
            reliability_rating=95.0,
        )

        # Pengiriman langsung 64 kg tanpa split delivery
        score, status, breakdown = feasibility_engine.evaluate(
            supplier=supplier,
            metrics=self.metrics,
            sop_max_price_per_kg=self.sop_max_price,
            initial_batch_qty_kg=64.0,
        )

        self.assertLess(breakdown.storage_compatibility, 40.0)
        self.assertGreaterEqual(score, 60.0)
        self.assertLess(score, 80.0)
        self.assertEqual(status, FeasibilityStatus.FEASIBLE_WITH_CONDITIONS)

    def test_evaluate_split_delivery_improves_score(self):
        """
        Skenario Split Delivery:
        Dengan membagi pengiriman sehingga batch 1 = 20 kg (sesuai freezer),
        skor storage_compatibility naik menjadi 100.0 dan total skor naik.
        """
        supplier = SupplierRecord(
            supplier_id="SUP-ALT-02",
            supplier_name="PT Berkah Unggas Jaya",
            category="PROTEIN",
            halal_certified=True,
            halal_cert_number="ID999",
            unit_price_idr=38000.0,
            daily_capacity_kg=120.0,
            lead_time_hours=4.0,
            distance_km=22.0,
            reliability_rating=95.0,
        )

        score_direct, _, _ = feasibility_engine.evaluate(
            supplier=supplier,
            metrics=self.metrics,
            sop_max_price_per_kg=self.sop_max_price,
            initial_batch_qty_kg=64.0,
        )

        score_split, status_split, breakdown_split = feasibility_engine.evaluate(
            supplier=supplier,
            metrics=self.metrics,
            sop_max_price_per_kg=self.sop_max_price,
            initial_batch_qty_kg=20.0,  # Batch 1 muat di freezer
        )

        self.assertEqual(breakdown_split.storage_compatibility, 100.0)
        self.assertGreater(score_split, score_direct)
        self.assertEqual(status_split, FeasibilityStatus.FEASIBLE)

    def test_evaluate_not_feasible_scenario(self):
        """
        Supplier dengan kapasitas sangat rendah (hanya 10 kg dari defisit 64 kg),
        lead time 10 jam, dan harga melebihi pagu anggaran SOP (Rp 60.000 vs 42.000).
        Total skor < 60 -> NOT_FEASIBLE.
        """
        bad_supplier = SupplierRecord(
            supplier_id="SUP-BAD",
            supplier_name="UD Kurang Sanggup",
            category="PROTEIN",
            halal_certified=True,
            halal_cert_number="ID000",
            unit_price_idr=60000.0,
            daily_capacity_kg=10.0,
            lead_time_hours=10.0,
            distance_km=90.0,
            reliability_rating=50.0,
        )

        score, status, _ = feasibility_engine.evaluate(
            supplier=bad_supplier,
            metrics=self.metrics,
            sop_max_price_per_kg=self.sop_max_price,
        )

        self.assertLess(score, 60.0)
        self.assertEqual(status, FeasibilityStatus.NOT_FEASIBLE)


if __name__ == "__main__":
    unittest.main()

