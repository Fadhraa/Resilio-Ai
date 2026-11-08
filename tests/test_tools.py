import unittest
from app.data.mock_db import SUPPLIERS_DB
from app.engine.tools import (
    deactivate_supplier_tool,
    get_supplier_detail_tool,
    list_all_suppliers_tool,
    register_supplier_tool,
    update_supplier_tool,
)
from app.models.schemas import SupplierCreateRequest, SupplierUpdateRequest
from app.services.data_layer import data_layer_service


class TestSupplierCRUDTools(unittest.TestCase):
    """
    Test Suite untuk Supplier CRUD Tools & Governance Gatekeeper SPPG:
    - Pendaftaran rekanan (Auto-ID, Halal Check, SOP Price Ceiling Warning).
    - Kueri profil rekanan (Detail & Filter Komoditas).
    - Pembaruan data parsial (Partial Update).
    - Soft-delete deaktivasi rekanan dan eksklusi dari pengadaan darurat.
    """

    def setUp(self):
        # Simpan snapshot awal SUPPLIERS_DB untuk di-restore jika dibutuhkan
        self.initial_supplier_keys = set(SUPPLIERS_DB.keys())

    def test_register_supplier_success_with_halal(self):
        """Validasi pendaftaran rekanan baru yang lolos kualifikasi Halal dan Pagu Anggaran."""
        payload = SupplierCreateRequest(
            supplier_name="CV Berkah Mandiri Unggas",
            category="PROTEIN",
            commodity="DAGING_AYAM",
            supported_items=["ITEM-AYAM-01"],
            halal_certified=True,
            halal_cert_number="ID32110000777889900",
            unit_price_idr=37000.0,
            daily_capacity_kg=250.0,
            lead_time_hours=3.0,
            distance_km=15.0,
            reliability_rating=95.0,
        )

        res = register_supplier_tool(payload)
        self.assertEqual(res["status"], "CREATED")
        self.assertTrue(res["supplier_id"].startswith("SUP-REG-"))
        self.assertEqual(res["governance"]["governance_status"], "VERIFIED_ELIGIBLE")
        self.assertFalse(res["governance"]["exceeds_sop_ceiling"])
        self.assertIn(res["supplier_id"], SUPPLIERS_DB)

        # Verifikasi data tersimpan utuh di SUPPLIERS_DB
        saved = SUPPLIERS_DB[res["supplier_id"]]
        self.assertEqual(saved.supplier_name, "CV Berkah Mandiri Unggas")
        self.assertTrue(saved.is_active)
        self.assertEqual(saved.commodity, "DAGING_AYAM")

    def test_register_supplier_tahu_and_json_persistence(self):
        """Verifikasi bahwa komoditas TAHU dipetakan dengan tepat ke ITEM-TAHU-01 dan tersimpan di JSON."""
        import json
        from pathlib import Path
        payload = SupplierCreateRequest(
            supplier_name="CV Berkah Tahu Alami",
            category="PROTEIN",
            commodity="TAHU",
            supported_items=["ITEM-AYAM-01"],  # Disengaja default ayam untuk menguji auto-alignment
            halal_certified=True,
            halal_cert_number="ID3211",
            unit_price_idr=18000.0,
            daily_capacity_kg=200.0,
            lead_time_hours=3.0,
            distance_km=15.0,
            reliability_rating=90.0,
        )

        res = register_supplier_tool(payload)
        self.assertEqual(res["status"], "CREATED")
        sid = res["supplier_id"]
        saved = SUPPLIERS_DB[sid]
        self.assertEqual(saved.commodity, "TAHU")
        self.assertIn("ITEM-TAHU-01", saved.supported_items)

        # Verifikasi berkas JSON
        json_path = Path("app/data/suppliers.json")
        self.assertTrue(json_path.exists())
        with open(json_path, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
        self.assertIn(sid, disk_data)
        self.assertEqual(disk_data[sid]["commodity"], "TAHU")
        self.assertEqual(disk_data[sid]["unit_price_idr"], 18000.0)

    def test_register_supplier_exceeds_sop_price_warning(self):
        """Pendaftaran dengan harga di atas pagu SOP (misal ayam > Rp 42.000) memicu warning."""
        payload = SupplierCreateRequest(
            supplier_name="PT Unggas Sultan Premium",
            category="PROTEIN",
            commodity="DAGING_AYAM",
            supported_items=["ITEM-AYAM-01"],
            halal_certified=True,
            halal_cert_number="ID3211000011223344",
            unit_price_idr=48000.0,  # Pagu SOP Ayam adalah 42.000
            daily_capacity_kg=100.0,
            lead_time_hours=2.0,
            distance_km=10.0,
            reliability_rating=90.0,
        )

        res = register_supplier_tool(payload)
        self.assertEqual(res["status"], "CREATED")
        self.assertTrue(res["governance"]["exceeds_sop_ceiling"])
        self.assertIsNotNone(res["governance"]["price_warning"])
        self.assertIn("melebihi pagu anggaran SOP", res["governance"]["price_warning"])

    def test_register_supplier_non_halal_warning(self):
        """Pendaftaran rekanan non-halal otomatis ditandai status NON_PRIORITY_UNCERTIFIED."""
        payload = SupplierCreateRequest(
            supplier_name="Ternak Rumahan Pak Budi",
            category="PROTEIN",
            commodity="DAGING_AYAM",
            supported_items=["ITEM-AYAM-01"],
            halal_certified=False,
            halal_cert_number=None,
            unit_price_idr=31000.0,
            daily_capacity_kg=80.0,
            lead_time_hours=1.5,
            distance_km=8.0,
            reliability_rating=75.0,
        )

        res = register_supplier_tool(payload)
        self.assertEqual(res["status"], "CREATED")
        self.assertEqual(res["governance"]["governance_status"], "NON_PRIORITY_UNCERTIFIED")
        self.assertIn("TIDAK DAPAT dialokasikan", res["governance"]["halal_note"])

    def test_get_supplier_detail_success_and_not_found(self):
        """Pengujian kueri detail supplier spesifik dan penanganan rekaman yang tidak ada."""
        res_found = get_supplier_detail_tool("SUP-UTAMA-01")
        self.assertEqual(res_found["status"], "FOUND")
        self.assertEqual(res_found["supplier"]["supplier_id"], "SUP-UTAMA-01")
        self.assertEqual(res_found["supplier"]["supplier_name"], "PT Unggas Sejahtera Nusantara")

        res_not_found = get_supplier_detail_tool("SUP-GHAIB-999")
        self.assertEqual(res_not_found["status"], "NOT_FOUND")

    def test_update_supplier_partial_fields(self):
        """Pengujian pembaruan sebagian atribut supplier (partial update)."""
        target_id = "SUP-ALT-02"
        updates = SupplierUpdateRequest(
            unit_price_idr=36500.0,
            daily_capacity_kg=140.0,
        )

        res = update_supplier_tool(target_id, updates)
        self.assertEqual(res["status"], "UPDATED")
        self.assertIn("unit_price_idr", res["updated_fields"])
        self.assertIn("daily_capacity_kg", res["updated_fields"])

        # Verifikasi nilai terupdate di DB
        updated = SUPPLIERS_DB[target_id]
        self.assertEqual(updated.unit_price_idr, 36500.0)
        self.assertEqual(updated.daily_capacity_kg, 140.0)
        # Pastikan atribut lain seperti sertifikat halal tidak tereset
        self.assertTrue(updated.halal_certified)

    def test_deactivate_supplier_soft_delete(self):
        """Verifikasi soft delete: supplier dinonaktifkan tanpa menghapus baris dari memori."""
        target_id = "SUP-ALT-04"
        res = deactivate_supplier_tool(target_id, reason="Audit logistik: rute tidak efisien")
        self.assertEqual(res["status"], "DEACTIVATED")
        self.assertFalse(res["is_active"])

        # Di basis data, status is_active wajib False
        self.assertFalse(SUPPLIERS_DB[target_id].is_active)

        # Di fungsi seleksi pengadaan darurat, supplier non-aktif wajib dieliminasi
        eligible = data_layer_service.get_eligible_suppliers(
            category="PROTEIN",
            item_id="ITEM-AYAM-01",
        )
        eligible_ids = [s.supplier_id for s in eligible]
        self.assertNotIn(target_id, eligible_ids)

    def test_list_all_suppliers_filter(self):
        """Verifikasi fungsi kueri seluruh rekanan dengan filter komoditas."""
        sapi_suppliers = list_all_suppliers_tool(commodity="DAGING_SAPI")
        self.assertTrue(len(sapi_suppliers) >= 1)
        for s in sapi_suppliers:
            self.assertEqual(s["commodity"], "DAGING_SAPI")


if __name__ == "__main__":
    unittest.main()

