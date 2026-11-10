import unittest
from app.engine.conversational_agent import conversational_agent
from app.models.schemas import ChatRequest, ChatActionRequired
from app.data.sqlite_db import get_all_suppliers, delete_supplier_permanently_from_db

class TestSupplierMultiTurnRegistration(unittest.TestCase):
    def test_missing_lead_time_and_merge(self):
        session_id = "test-incomplete-supplier-session-01"
        session = conversational_agent.get_or_create_session(session_id)

        # Turn 1: Incomplete registration (no lead time)
        msg1 = (
            "Tolong daftarkan supplier baru UD Sapi Segar Jaya, komoditas daging Sapi, "
            "harga Rp 44.000 per kg, kapasitas harian 200 kg, jarak 12 km, "
            "halal aktif nomor sertifikat ID-HALAL-2026-0088"
        )
        req1 = ChatRequest(session_id=session_id, message=msg1)
        res1 = conversational_agent.process_message(req1)

        self.assertEqual(res1.action_required, ChatActionRequired.CLARIFICATION_NEEDED)
        self.assertIsNone(res1.preview_data)
        self.assertIsNotNone(session.get("pending_supplier_draft"))
        self.assertIsNone(session.get("pending_crud"))
        self.assertTrue(
            "waktu kirim" in res1.reply.lower() or "lead time" in res1.reply.lower()
        )

        # Turn 2: User provides missing lead time
        msg2 = "waktu kirimnya 2 jam"
        req2 = ChatRequest(session_id=session_id, message=msg2)
        res2 = conversational_agent.process_message(req2)

        self.assertEqual(res2.action_required, ChatActionRequired.APPROVAL_PENDING)
        self.assertIsNotNone(res2.preview_data)
        self.assertEqual(res2.preview_data.get("action"), "PREVIEW_CREATE")

        draft = res2.preview_data.get("draft", {})
        self.assertEqual(draft.get("supplier_name"), "UD Sapi Segar Jaya")
        self.assertEqual(draft.get("lead_time_hours"), 2.0)
        self.assertEqual(draft.get("distance_km"), 12.0)
        self.assertEqual(draft.get("unit_price_idr"), 44000.0)
        self.assertEqual(draft.get("daily_capacity_kg"), 200.0)
        self.assertIsNone(session.get("pending_supplier_draft"))
        self.assertIsNotNone(session.get("pending_crud"))

        # Turn 3: User approves registration
        msg3 = "Setuju, daftarkan rekanan ini"
        req3 = ChatRequest(session_id=session_id, message=msg3)
        res3 = conversational_agent.process_message(req3)

        self.assertIsNone(session.get("pending_crud"))

        # Verify saved in SQLite database
        all_sups = get_all_suppliers(include_inactive=True)
        registered = next((s for s in all_sups if s["supplier_name"] == "UD Sapi Segar Jaya"), None)
        self.assertIsNotNone(registered, "Registered supplier should be found in database")
        self.assertEqual(registered["lead_time_hours"], 2.0)
        self.assertEqual(registered["distance_km"], 12.0)
        self.assertEqual(registered["unit_price_idr"], 44000.0)

        # Cleanup test supplier
        if registered:
            delete_supplier_permanently_from_db(registered["supplier_id"])

    def test_duplicate_supplier_prevention(self):
        session_id = "test-dup-supplier-session-02"

        # Try to register an existing supplier: PT Unggas Sejahtera Nusantara
        msg = (
            "Tolong daftarkan supplier baru PT Unggas Sejahtera Nusantara, komoditas daging ayam, "
            "harga Rp 38.000 per kg, kapasitas harian 300 kg, jarak 10 km, lead time 2 jam, halal aktif"
        )
        req = ChatRequest(session_id=session_id, message=msg)
        res = conversational_agent.process_message(req)

        # AI must recognize duplicate and NOT ask to create or show draft
        self.assertEqual(res.action_required, ChatActionRequired.NONE)
        self.assertTrue(
            "sudah terdaftar" in res.reply.lower() or "duplikat" in res.reply.lower()
        )
        self.assertIn("SUP-UTAMA-01", res.reply)
        if res.preview_data:
            self.assertTrue(res.preview_data.get("is_duplicate"))

        # Verify tool raises ValueError on duplicate
        from app.engine.tools import register_supplier_tool
        from app.models.schemas import SupplierCreateRequest
        dup_payload = SupplierCreateRequest(
            supplier_name="PT Unggas Sejahtera Nusantara",
            category="PROTEIN",
            commodity="DAGING_AYAM",
            supported_items=["ITEM-AYAM-01"],
            halal_certified=True,
            unit_price_idr=38000.0,
            daily_capacity_kg=300.0,
            lead_time_hours=2.0,
            distance_km=10.0,
        )
        with self.assertRaises(ValueError) as ctx:
            register_supplier_tool(dup_payload)
        self.assertIn("sudah terdaftar", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
