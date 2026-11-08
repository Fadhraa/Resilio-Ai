import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.data.mock_db import SUPPLIERS_DB, reset_db_to_default
from app.main import app
from app.models.schemas import ApprovalAction, DisruptionType


class TestAPIEndpoints(unittest.TestCase):
    """
    Test Suite untuk API Router v1 ResilioAI:
    - Conversational Assistant (Chatbot multi-turn dengan klarifikasi typo & approval).
    - Formal PRD Endpoints (/trigger, /decision, /approve).
    """

    def setUp(self):
        reset_db_to_default()
        self.client = TestClient(app)
        from app.engine.conversational_agent import conversational_agent
        self.orig_api_key = conversational_agent.api_key
        conversational_agent.api_key = None
        # Mock network LLM call agar pengujian deterministik dan instan di lingkungan sandbox
        self.gemini_patch = patch(
            "app.engine.conversational_agent.ConversationalAgentManager._call_gemini_adaptive",
            side_effect=lambda **kwargs: kwargs.get("fallback_text", ""),
        )
        self.gemini_patch.start()
        self.addCleanup(self.gemini_patch.stop)

    def tearDown(self):
        from app.engine.conversational_agent import conversational_agent
        conversational_agent.api_key = self.orig_api_key
        reset_db_to_default()

    def test_root_and_health_endpoints(self):
        resp_root = self.client.get("/")
        self.assertEqual(resp_root.status_code, 200)
        self.assertEqual(resp_root.json()["status"], "success")

        resp_health = self.client.get("/health")
        self.assertEqual(resp_health.status_code, 200)
        self.assertEqual(resp_health.json()["status"], "healthy")

    def test_general_inquiry_suppliers_and_stock(self):
        # 0. Sapaan awal (Greeting)
        resp_greet = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": "test-session-greet-01",
                "message": "Halo selamat pagi",
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp_greet.status_code, 200)
        data_greet = resp_greet.json()
        self.assertEqual(data_greet["action_required"], "NONE")
        self.assertIn("ResilioAI Assistant", data_greet["reply"])

        # 1. Inquiry daftar supplier
        resp_sup = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": "test-session-inquiry-01",
                "message": "Saat ini ada berapa suplier di data kita?",
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp_sup.status_code, 200)
        data_sup = resp_sup.json()
        self.assertEqual(data_sup["intent"], "GENERAL_INQUIRY")
        self.assertEqual(data_sup["action_required"], "NONE")
        self.assertIsNotNone(data_sup.get("preview_data"))
        active_suppliers = [s for s in SUPPLIERS_DB.values() if getattr(s, "is_active", True)]
        self.assertEqual(len(data_sup["preview_data"]["suppliers"]), len(active_suppliers))
        self.assertTrue(
            str(len(active_suppliers)) in data_sup["reply"]
            or "supplier" in data_sup["reply"].lower()
            or "rekanan" in data_sup["reply"].lower()
        )

        # 2. Inquiry inventaris & sisa freezer
        resp_inv = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": "test-session-inquiry-01",
                "message": "Cek stok gudang dan sisa freezer",
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp_inv.status_code, 200)
        data_inv = resp_inv.json()
        self.assertEqual(data_inv["intent"], "GENERAL_INQUIRY")
        self.assertIn("Daging Ayam Broiler Segar", data_inv["reply"])

    def test_conversational_incident_flow_multi_turn(self):
        session_id = "test-session-chat-flow-001"

        # 1. Turn 1: Laporan insiden dengan supplier typo ("supplier ayam A")
        resp1 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Hari ini SPPG A mau membuat 5.000 porsi makanan bergizi namun suplier ayam A kebakaran sehingga tidak mensuplai, apa yang harus dilakukan?",
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertEqual(data1["action_required"], "CLARIFICATION_NEEDED")
        self.assertEqual(data1["intent"], "REPORT_INCIDENT")
        self.assertIn("PT Unggas Sejahtera Nusantara", data1["reply"])

        # 2. Turn 2: User mengonfirmasi klarifikasi
        resp2 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Iya betul, PT Unggas Sejahtera Nusantara yang kebakaran.",
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2["action_required"], "APPROVAL_PENDING")
        self.assertIsNotNone(data2["preview_data"])
        metrics = data2["preview_data"]["metrics"]
        self.assertEqual(metrics["target_production_portions"], 5000)
        # 5000 * 0.04 * 1.2 = 240 kg buffer - 80 kg stok = 160 kg defisit
        self.assertEqual(metrics["deficit_kg"], 160.0)

        # 3. Turn 3: User meminta revisi ("bisa ganti ke supplier yang lebih murah?")
        resp3 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Bisa ganti ke supplier yang lebih murah?",
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp3.status_code, 200)
        data3 = resp3.json()
        self.assertEqual(data3["action_required"], "APPROVAL_PENDING")
        self.assertEqual(data3["intent"], "REQUEST_REVISION")
        self.assertIsNotNone(data3.get("preview_data"))
        self.assertIn("recommended_procurement", data3["preview_data"])
        # Verifikasi bahwa supplier termurah yang dipilih (PT Berkah Unggas Jaya Rp 38.000 vs CV Berkah Ternak Rp 39.500)
        self.assertEqual(
            data3["preview_data"]["recommended_procurement"]["supplier_name"],
            "PT Berkah Unggas Jaya",
        )

        # 4. Turn 4: User memberikan persetujuan verbal
        resp4 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Oke saya setuju, terbitkan surat PO resminya.",
                "user_role": "Budi Santoso (Kepala SPPG)",
            },
        )
        self.assertEqual(resp4.status_code, 200)
        data4 = resp4.json()
        self.assertEqual(data4["action_required"], "COMPLETED")
        self.assertEqual(data4["intent"], "CONFIRM_APPROVAL")
        self.assertIsNotNone(data4["preview_data"]["po_result"])
        po = data4["preview_data"]["po_result"]
        self.assertTrue(po["po_number"].startswith("PO-SPPG-2026-"))
        self.assertEqual(po["approved_qty_kg"], 160.0)

    def test_formal_prd_pipeline_endpoints(self):
        # 1. Trigger Incident
        trigger_resp = self.client.post(
            "/api/v1/incidents/trigger",
            json={
                "item_id": "ITEM-AYAM-01",
                "disruption_type": DisruptionType.SUPPLIER_DISRUPTION,
                "affected_supplier_id": "SUP-UTAMA-01",
                "estimated_duration_days": 3,
                "incident_notes": "Banjir Pantura logistik macet.",
            },
        )
        self.assertEqual(trigger_resp.status_code, 200)
        trigger_data = trigger_resp.json()
        incident_id = trigger_data["incident_id"]
        self.assertTrue(incident_id.startswith("INC-"))
        self.assertEqual(trigger_data["status"], "PROCESSING")

        # 2. Get Decision
        decision_resp = self.client.get(f"/api/v1/incidents/{incident_id}/decision")
        self.assertEqual(decision_resp.status_code, 200)
        decision_data = decision_resp.json()
        self.assertEqual(decision_data["incident_id"], incident_id)
        self.assertEqual(decision_data["item_id"], "ITEM-AYAM-01")
        self.assertEqual(decision_data["metrics"]["deficit_kg"], 64.0)
        self.assertIsNotNone(decision_data["recommended_procurement"])
        self.assertGreaterEqual(len(decision_data["audit_trail"]), 4)

        # 3. Approve Decision
        approve_resp = self.client.post(
            f"/api/v1/incidents/{incident_id}/approve",
            json={
                "incident_id": incident_id,
                "action": ApprovalAction.APPROVE,
                "approved_qty_kg": 64.0,
                "approver_name": "Budi Santoso (Kepala SPPG)",
                "approver_notes": "Disetujui via formal PRD API.",
            },
        )
        self.assertEqual(approve_resp.status_code, 200)
        po_data = approve_resp.json()
        self.assertEqual(po_data["status"], "SUCCESS")
        self.assertTrue(po_data["po_number"].startswith("PO-SPPG-2026-"))
        self.assertEqual(po_data["approved_qty_kg"], 64.0)

    def test_suppliers_rest_crud_lifecycle(self):
        """
        Pengujian siklus hidup lengkap REST API CRUD Supplier:
        1. POST /api/v1/suppliers -> Registrasi baru (201 Created).
        2. GET /api/v1/suppliers/{id} -> Kueri detail profil (200 OK).
        3. GET /api/v1/suppliers?commodity=... -> Filter komoditas (200 OK).
        4. PATCH /api/v1/suppliers/{id} -> Partial update (200 OK).
        5. DELETE /api/v1/suppliers/{id} -> Soft-delete deaktivasi (200 OK).
        6. GET /api/v1/suppliers/SUP-TIDAK-ADA -> Penanganan 404 Not Found.
        """
        # 1. POST: Register supplier baru via REST API
        post_resp = self.client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "CV Peternak Unggas Berkah",
                "category": "PROTEIN",
                "commodity": "DAGING_AYAM",
                "supported_items": ["ITEM-AYAM-01"],
                "halal_certified": True,
                "halal_cert_number": "ID3211000998877",
                "unit_price_idr": 37500.0,
                "daily_capacity_kg": 300.0,
                "lead_time_hours": 3.0,
                "distance_km": 14.0,
                "reliability_rating": 94.0,
            },
        )
        self.assertEqual(post_resp.status_code, 201)
        post_data = post_resp.json()
        new_id = post_data["supplier_id"]
        self.assertTrue(new_id.startswith("SUP-REG-"))
        self.assertEqual(post_data["governance"]["governance_status"], "VERIFIED_ELIGIBLE")

        # 2. GET: Detail supplier yang baru dibuat
        get_resp = self.client.get(f"/api/v1/suppliers/{new_id}")
        self.assertEqual(get_resp.status_code, 200)
        detail = get_resp.json()
        self.assertEqual(detail["supplier_name"], "CV Peternak Unggas Berkah")
        self.assertEqual(detail["unit_price_idr"], 37500.0)
        self.assertTrue(detail["is_active"])

        # 3. GET: List dengan filter komoditas
        list_resp = self.client.get("/api/v1/suppliers?commodity=DAGING_SAPI")
        self.assertEqual(list_resp.status_code, 200)
        sapi_list = list_resp.json()
        self.assertTrue(len(sapi_list) >= 1)
        for s in sapi_list:
            self.assertEqual(s["commodity"], "DAGING_SAPI")

        # 4. PATCH: Update harga dan kapasitas
        patch_resp = self.client.patch(
            f"/api/v1/suppliers/{new_id}",
            json={
                "unit_price_idr": 36000.0,
                "daily_capacity_kg": 350.0,
            },
        )
        self.assertEqual(patch_resp.status_code, 200)
        patch_data = patch_resp.json()
        self.assertEqual(patch_data["supplier"]["unit_price_idr"], 36000.0)
        self.assertEqual(patch_data["supplier"]["daily_capacity_kg"], 350.0)

        # 5. DELETE: Soft delete / deaktivasi
        del_resp = self.client.delete(f"/api/v1/suppliers/{new_id}?reason=Audit+gudang+selesai")
        self.assertEqual(del_resp.status_code, 200)
        del_data = del_resp.json()
        self.assertEqual(del_data["status"], "DEACTIVATED")
        self.assertFalse(del_data["is_active"])

        # Verifikasi bahwa default GET /api/v1/suppliers (include_inactive=False) tidak lagi menampilkan supplier ini
        active_list_resp = self.client.get("/api/v1/suppliers")
        active_ids = [s["supplier_id"] for s in active_list_resp.json()]
        self.assertNotIn(new_id, active_ids)

        # 6. Error handling: 404 untuk ID tidak valid
        err_resp = self.client.get("/api/v1/suppliers/SUP-TIDAK-ADA-999")
        self.assertEqual(err_resp.status_code, 404)

    def test_conversational_supplier_management_flow(self):
        """
        Pengujian alur manajemen rekanan supplier interaktif via Conversational AI Chat (/api/v1/chat):
        1. Mendaftarkan supplier baru via instruksi percakapan.
        2. Memperbarui harga penawaran supplier via chat.
        3. Menonaktifkan supplier (Soft Delete) via chat.
        4. Validasi permintaan klarifikasi jika instruksi pendaftaran belum lengkap.
        """
        session_id = f"test-chat-crud-{datetime.now(timezone.utc).timestamp()}"

        # 1. Daftarkan supplier baru via Chat (Turn 1: Draf Preview)
        create_msg = (
            "Tolong daftarkan supplier baru CV Berkah Pangan Mandiri, komoditas daging ayam, "
            "harga Rp 38.500 per kg, kapasitas 250 kg/hari, halal aktif ID-HALAL-9988, lead time 2 jam"
        )
        resp1 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": create_msg,
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertEqual(data1["intent"], "MANAGE_SUPPLIER")
        self.assertEqual(data1["action_required"], "APPROVAL_PENDING")
        self.assertIsNotNone(data1.get("preview_data"))
        self.assertEqual(data1["preview_data"]["action"], "PREVIEW_CREATE")
        self.assertEqual(data1["preview_data"]["draft"]["supplier_name"], "CV Berkah Pangan Mandiri")

        # 1b. Konfirmasi Persetujuan Kepala SPPG (Turn 2: Commit Resmi)
        resp1b = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Setuju, tolong daftarkan supplier ini ke sistem",
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp1b.status_code, 200)
        data1b = resp1b.json()
        self.assertEqual(data1b["intent"], "MANAGE_SUPPLIER")
        self.assertEqual(data1b["action_required"], "NONE")
        created_res = data1b["preview_data"]["result"]
        new_sid = created_res["supplier_id"]
        self.assertTrue(new_sid.startswith("SUP-REG-"))
        self.assertEqual(created_res["supplier"]["supplier_name"], "CV Berkah Pangan Mandiri")
        self.assertEqual(created_res["supplier"]["unit_price_idr"], 38500.0)
        self.assertEqual(created_res["supplier"]["daily_capacity_kg"], 250.0)
        self.assertEqual(created_res["governance"]["governance_status"], "VERIFIED_ELIGIBLE")
        self.assertIn(new_sid, SUPPLIERS_DB)
        self.assertEqual(SUPPLIERS_DB[new_sid].supplier_name, "CV Berkah Pangan Mandiri")

        # 2. Update harga supplier via Chat (Preview -> Confirm)
        update_msg = f"Update harga {new_sid} menjadi Rp 37.000"
        resp2 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": update_msg,
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2["intent"], "MANAGE_SUPPLIER")
        self.assertEqual(data2["action_required"], "APPROVAL_PENDING")
        self.assertEqual(data2["preview_data"]["action"], "PREVIEW_UPDATE")

        resp2b = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Setuju simpan perubahan harga",
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp2b.status_code, 200)
        data2b = resp2b.json()
        self.assertEqual(data2b["intent"], "MANAGE_SUPPLIER")
        self.assertEqual(data2b["action_required"], "NONE")
        self.assertEqual(data2b["preview_data"]["action"], "UPDATE")
        self.assertEqual(data2b["preview_data"]["result"]["supplier"]["unit_price_idr"], 37000.0)
        self.assertEqual(SUPPLIERS_DB[new_sid].unit_price_idr, 37000.0)

        # 3. Nonaktifkan supplier via Chat (Preview -> Confirm)
        deact_msg = f"Tolong nonaktifkan supplier CV Berkah Pangan Mandiri"
        resp3 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": deact_msg,
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp3.status_code, 200)
        data3 = resp3.json()
        self.assertEqual(data3["intent"], "MANAGE_SUPPLIER")
        self.assertEqual(data3["action_required"], "APPROVAL_PENDING")
        self.assertEqual(data3["preview_data"]["action"], "PREVIEW_DEACTIVATE")

        resp3b = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Ya, saya setuju untuk menonaktifkan rekanan ini",
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp3b.status_code, 200)
        data3b = resp3b.json()
        self.assertEqual(data3b["intent"], "MANAGE_SUPPLIER")
        self.assertEqual(data3b["action_required"], "NONE")
        self.assertEqual(data3b["preview_data"]["action"], "DEACTIVATE")
        self.assertFalse(SUPPLIERS_DB[new_sid].is_active)

        # 4. Validasi permintaan kelengkapan jika pendaftaran tidak mencantumkan atribut inti
        incomplete_msg = "Tolong daftarkan supplier baru untuk SPPG"
        resp4 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": incomplete_msg,
                "user_role": "Kepala SPPG",
            },
        )
        self.assertEqual(resp4.status_code, 200)
        data4 = resp4.json()
        self.assertEqual(data4["intent"], "MANAGE_SUPPLIER")
        self.assertEqual(data4["action_required"], "CLARIFICATION_NEEDED")
        self.assertTrue(len(data4["reply"]) > 20)


if __name__ == "__main__":
    unittest.main()

