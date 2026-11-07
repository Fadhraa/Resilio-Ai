import unittest
from fastapi.testclient import TestClient
from app.data.mock_db import SUPPLIERS_DB
from app.main import app
from app.models.schemas import ApprovalAction, DisruptionType


class TestAPIEndpoints(unittest.TestCase):
    """
    Test Suite untuk API Router v1 ResilioAI:
    - Conversational Assistant (Chatbot multi-turn dengan klarifikasi typo & approval).
    - Formal PRD Endpoints (/trigger, /decision, /approve).
    """

    def setUp(self):
        self.client = TestClient(app)

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
        self.assertEqual(len(data_sup["preview_data"]["suppliers"]), len(SUPPLIERS_DB))
        self.assertTrue(
            str(len(SUPPLIERS_DB)) in data_sup["reply"]
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


if __name__ == "__main__":
    unittest.main()

