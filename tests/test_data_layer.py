import unittest
from app.services.data_layer import DataLayerService, data_layer_service


class TestDataLayerService(unittest.TestCase):
    """Pengujian Unit untuk DataLayerService SPPG (Deterministic Layer)."""

    def test_get_inventory_item_success(self):
        item = data_layer_service.get_inventory_item("ITEM-AYAM-01")
        self.assertIsNotNone(item)
        self.assertEqual(item.item_id, "ITEM-AYAM-01")
        self.assertEqual(item.category, "PROTEIN")
        self.assertEqual(item.current_stock_kg, 80.0)

    def test_get_inventory_item_not_found(self):
        item = data_layer_service.get_inventory_item("ITEM-TIDAK-ADA")
        self.assertIsNone(item)

    def test_calculate_metrics_chicken_spg_scenario(self):
        """
        Validasi skenario riil SPPG sesuai PRD:
        - Target: 3.000 porsi ayam (@ 0.04 kg = 120 kg)
        - Kebutuhan Buffer 20%: 120 kg * 1.2 = 144.0 kg
        - Stok Gudang: 80.0 kg
        - Defisit = 144.0 - 80.0 = 64.0 kg
        - Freezer: Kapasitas 100 kg, terpakai 80 kg -> sisa 20.0 kg
        - SOP Pagu Harga: Rp 42.000 / kg
        - Exposure Finansial = 64.0 * 42.000 = Rp 2.688.000
        """
        metrics = data_layer_service.calculate_metrics("ITEM-AYAM-01", target_portions=3000)

        self.assertEqual(metrics.current_stock_kg, 80.0)
        self.assertEqual(metrics.deficit_kg, 64.0)
        self.assertEqual(metrics.freezer_available_kg, 20.0)
        self.assertEqual(metrics.target_production_portions, 3000)
        self.assertEqual(metrics.financial_risk_exposure_idr, 2688000.0)

    def test_calculate_metrics_invalid_item(self):
        with self.assertRaises(ValueError):
            data_layer_service.calculate_metrics("ITEM-GHAIB-99", target_portions=3000)

    def test_eligible_suppliers_hard_constraint_halal_filter(self):
        """
        Validasi Hard-Constraint Gate:
        Supplier non-halal (SUP-ALT-03) wajib dieliminasi secara deterministik.
        """
        suppliers = data_layer_service.get_eligible_suppliers(
            category="PROTEIN",
            exclude_supplier_id="SUP-UTAMA-01",
            max_distance_km=100.0,
        )

        supplier_ids = [s.supplier_id for s in suppliers]

        # Supplier non-halal wajib gugur
        self.assertNotIn("SUP-ALT-03", supplier_ids)

        # Supplier terdampak wajib gugur
        self.assertNotIn("SUP-UTAMA-01", supplier_ids)

        # Supplier melebihi radius jarak 100 km wajib gugur
        self.assertNotIn("SUP-ALT-04", supplier_ids)

        # Supplier alternatif halal dan terjangkau harus lolos
        self.assertIn("SUP-ALT-01", supplier_ids)
        self.assertIn("SUP-ALT-02", supplier_ids)

        # Pastikan seluruh supplier yang lolos 100% bersertifikat halal
        for s in suppliers:
            self.assertTrue(s.halal_certified)
            self.assertLessEqual(s.distance_km, 100.0)


if __name__ == "__main__":
    unittest.main()
