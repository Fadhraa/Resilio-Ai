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

    def tearDown(self):
        # Bersihkan supplier baru hasil registrasi tes dari SQLite agar database tetap steril
        from app.data.sqlite_db import delete_supplier_permanently_from_db, get_all_suppliers
        for s in get_all_suppliers(include_inactive=True):
            if s["supplier_id"].startswith("SUP-REG-") and s["supplier_id"] not in ("SUP-REG-04", "SUP-REG-05"):
                delete_supplier_permanently_from_db(s["supplier_id"])

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

        # Verifikasi persistensi di basis data SQLite resmi
        from app.data.sqlite_db import get_supplier_by_id_from_db
        db_data = get_supplier_by_id_from_db(sid)
        self.assertIsNotNone(db_data)
        self.assertEqual(db_data["commodity"], "TAHU")
        self.assertEqual(db_data["unit_price_idr"], 18000.0)

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
        target_id = "SUP-REG-05"
        res = deactivate_supplier_tool(target_id, reason="Audit logistik: rute tidak efisien")
        self.assertEqual(res["status"], "DEACTIVATED")
        self.assertFalse(res["is_active"])

        # Di fungsi seleksi pengadaan darurat, supplier non-aktif wajib dieliminasi
        eligible = data_layer_service.get_eligible_suppliers(
            category="PROTEIN",
            commodity="TEMPE",
        )
        eligible_ids = [s.supplier_id for s in eligible]
        self.assertNotIn(target_id, eligible_ids)

        # Pulihkan status ke aktif
        from app.engine.tools import update_supplier_tool
        from app.models.schemas import SupplierUpdateRequest
        update_supplier_tool(target_id, SupplierUpdateRequest(is_active=True))

    def test_list_all_suppliers_filter(self):
        """Verifikasi fungsi kueri seluruh rekanan dengan filter komoditas."""
        ayam_suppliers = list_all_suppliers_tool(commodity="DAGING_AYAM")
        self.assertTrue(len(ayam_suppliers) >= 1)
        for s in ayam_suppliers:
            self.assertEqual(s["commodity"], "DAGING_AYAM")

    def test_search_suppliers_sentence_query_exact_match(self):
        """Verifikasi bahwa pencarian rekanan di dalam kalimat deskriptif berhasil mendeteksi exact match."""
        from app.engine.tools import search_suppliers_tool
        msg = "🚨 Laporkan gangguan: Supplier utama PT Unggas Sejahtera Nusantara gagal kirim daging ayam karena kendala armada. Tolong carikan rekanan cadangan yang halal dan buatkan draf mitigasinya."
        res = search_suppliers_tool(msg, category="PROTEIN")
        self.assertEqual(res["status"], "EXACT_MATCH_FOUND")
        self.assertTrue(len(res["suppliers"]) >= 1)
        self.assertEqual(res["suppliers"][0]["supplier_name"], "PT Unggas Sejahtera Nusantara")
        self.assertEqual(res["suppliers"][0]["supplier_id"], "SUP-UTAMA-01")

    def test_incident_report_pipeline_and_confirmation(self):
        """Verifikasi alur mitigasi gangguan: deteksi supplier utama, kalkulasi defisit, rekomendasi rekanan halal, hingga penerbitan PO."""
        from app.engine.conversational_agent import conversational_agent
        from app.models.schemas import ChatActionRequired, ChatIntent, ChatRequest

        session_id = "test-incident-pipeline-01"
        # Turn 1: Laporan Gangguan
        req1 = ChatRequest(
            message="🚨 Laporkan gangguan: Supplier utama PT Unggas Sejahtera Nusantara gagal kirim daging ayam karena kendala armada. Tolong carikan rekanan cadangan yang halal dan buatkan draf mitigasinya.",
            session_id=session_id,
            user_role="Bapak Adam Dzaki",
        )
        res1 = conversational_agent.process_message(req1)
        self.assertEqual(res1.intent, ChatIntent.REPORT_INCIDENT)
        self.assertEqual(res1.action_required, ChatActionRequired.APPROVAL_PENDING)
        self.assertIn("PT Unggas Sejahtera Nusantara", res1.reply)
        self.assertIn("confirm_multi_po", res1.preview_data)

        card = res1.preview_data["confirm_multi_po"]
        self.assertEqual(len(card["po_list"]), 1)
        self.assertTrue(card["po_list"][0]["halal_certified"])
        self.assertEqual(card["po_list"][0]["supplier_name"], "PT Berkah Unggas Jaya")

        # Turn 2: Persetujuan Mitigasi
        req2 = ChatRequest(
            message="Setuju, terbitkan PO mitigasi ini.",
            session_id=session_id,
            user_role="Bapak Adam Dzaki",
        )
        res2 = conversational_agent.process_message(req2)
        self.assertEqual(res2.intent, ChatIntent.CONFIRM_APPROVAL)
        self.assertEqual(res2.action_required, ChatActionRequired.COMPLETED)
        self.assertIn("Otorisasi Diterima", res2.reply)
        self.assertIn("po_results", res2.preview_data)

    def test_multi_item_menu_planning_and_revision_flow(self):
        """
        Verifikasi pengujian skenario perencanaan menu multi-item (Ayam + Telur):
        1. Draf PO multi-item memuat kedua komoditas dan supplier yang sesuai tanpa halusinasi.
        2. Draf TIDAK disimpan secara prematur ke SQLite database sebelum disetujui.
        3. Permintaan penggantian supplier menghitung komparasi dampak (harga, anggaran, kapasitas, halal).
        4. Otorisasi eksplisit mengeksekusi penyimpanan permanen ke SQLite.
        """
        from app.engine.conversational_agent import conversational_agent
        from app.models.schemas import ChatActionRequired, ChatIntent, ChatRequest
        from app.data.sqlite_db import clear_all_documents, get_all_purchase_orders

        clear_all_documents()
        session_id = "test-multi-planning-flow-01"

        # Turn 1: Perencanaan Menu Multi-Item (Ayam dan Telur)
        msg1 = "baik sekarang tolong bantu aku dalam membuat PO, jadi saya berencana membuat makanan bergizi sekitar 3000 porsi bisa dengan menu ayam dan telur bisa tolong kamu suusn??"
        req1 = ChatRequest(message=msg1, session_id=session_id, user_role="Bapak Adam Dzaki")
        res1 = conversational_agent.process_message(req1)

        self.assertEqual(res1.intent, ChatIntent.CONFIRM_APPROVAL)
        self.assertEqual(res1.action_required, ChatActionRequired.APPROVAL_PENDING)
        self.assertIn("confirm_multi_po", res1.preview_data)

        po_list = res1.preview_data["confirm_multi_po"]["po_list"]
        self.assertEqual(len(po_list), 2)
        comms = [p["commodity"] for p in po_list]
        self.assertIn("DAGING_AYAM", comms)
        self.assertIn("TELUR_AYAM", comms)

        telur_entry = next(p for p in po_list if p["commodity"] == "TELUR_AYAM")
        self.assertEqual(telur_entry["supplier_id"], "SUP-TELUR-01")

        # Pastikan tidak ada data yang disimpan prematur ke SQLite
        self.assertEqual(len(get_all_purchase_orders()), 0)

        # Turn 2: Permintaan Revisi Rekanan Ayam
        msg2 = "ganti supplier ayamnya ke PT Berkah Unggas Jaya"
        req2 = ChatRequest(message=msg2, session_id=session_id, user_role="Bapak Adam Dzaki")
        res2 = conversational_agent.process_message(req2)

        self.assertEqual(res2.intent, ChatIntent.REQUEST_REVISION)
        self.assertEqual(res2.action_required, ChatActionRequired.APPROVAL_PENDING)
        rev_po_list = res2.preview_data["confirm_multi_po"]["po_list"]
        rev_ayam = next(p for p in rev_po_list if p["commodity"] == "DAGING_AYAM")
        self.assertEqual(rev_ayam["supplier_id"], "SUP-ALT-02")
        self.assertEqual(rev_ayam["supplier_name"], "PT Berkah Unggas Jaya")
        self.assertEqual(len(get_all_purchase_orders()), 0)

        # Turn 3: Otorisasi Eksplisit
        msg3 = "Setujui terbitkan seluruh PO pengadaan"
        req3 = ChatRequest(message=msg3, session_id=session_id, user_role="Bapak Adam Dzaki")
        res3 = conversational_agent.process_message(req3)

        self.assertEqual(res3.intent, ChatIntent.CONFIRM_APPROVAL)
        self.assertEqual(res3.action_required, ChatActionRequired.COMPLETED)
        self.assertEqual(len(get_all_purchase_orders()), 2)


if __name__ == "__main__":
    unittest.main()

