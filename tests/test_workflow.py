import unittest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.engine.workflow import build_procurement_workflow
from app.models.schemas import (
    ApprovalAction,
    DisruptionType,
    StrategyType,
)


class TestProcurementWorkflow(unittest.TestCase):
    """
    Pengujian Integrasi End-to-End untuk LangGraph StateGraph ResilioAI.
    
    Memverifikasi:
    1. Eksekusi alur otomatis dari Ingestion hingga terhenti di Approval Gate (HITL Interrupt).
    2. Persistensi state pada checkpointer (Defisit 64 kg, Split Delivery, Feasibility Score).
    3. Resume alur kerja dengan otorisasi Kepala SPPG hingga penerbitan PO resmi.
    """

    def setUp(self):
        # Buat checkpointer dan workflow instance terisolasi untuk tiap pengujian
        self.checkpointer = MemorySaver()
        self.workflow = build_procurement_workflow(checkpointer=self.checkpointer)
        self.thread_id = "test-thread-spg-001"
        self.config = {"configurable": {"thread_id": self.thread_id}}

    def test_full_pipeline_until_interrupt_and_resume(self):
        # 1. Inisialisasi payload insiden pemicu (Skenario PRD: Banjir Supplier Ayam Utama)
        initial_payload = {
            "incident_id": "INC-2026-001",
            "item_id": "ITEM-AYAM-01",
            "disruption_type": DisruptionType.SUPPLIER_DISRUPTION,
            "affected_supplier_id": "SUP-UTAMA-01",
            "estimated_duration_days": 3,
            "incident_notes": "Armada supplier utama terjebak banjir di jalur logistik Pantura.",
            "target_production_portions": 3000,
        }

        # 2. Jalankan workflow: Harusnya terhenti tepat di gerbang approval (interrupt)
        result = self.workflow.invoke(initial_payload, config=self.config)

        # Cek status state saat ini di checkpointer
        current_state = self.workflow.get_state(self.config)
        self.assertTrue(len(current_state.tasks) > 0)
        self.assertTrue(len(current_state.tasks[0].interrupts) > 0)

        # Verifikasi data metrik pada state
        values = current_state.values
        self.assertEqual(values["item_id"], "ITEM-AYAM-01")
        self.assertEqual(values["metrics"].deficit_kg, 64.0)
        self.assertEqual(values["metrics"].freezer_available_kg, 20.0)

        # Verifikasi agen merumuskan Split Delivery karena defisit (64 kg) > freezer (20 kg)
        rec = values["recommended_procurement"]
        self.assertEqual(rec.logistics_strategy.strategy_type, StrategyType.SPLIT_DELIVERY)
        self.assertEqual(len(rec.logistics_strategy.batches), 2)
        self.assertEqual(rec.logistics_strategy.batches[0].qty_kg, 20.0)
        self.assertEqual(rec.logistics_strategy.batches[1].qty_kg, 44.0)

        # Verifikasi skor kelayakan deterministik (>= 60)
        self.assertGreaterEqual(rec.feasibility_score, 60.0)

        # Verifikasi audit trail terekam dengan benar
        stages = [step.stage for step in values["audit_trail"]]
        self.assertIn("INGESTION", stages)
        self.assertIn("DATA_AGGREGATION", stages)
        self.assertIn("COMPLIANCE_FILTER", stages)
        self.assertIn("STRATEGY_SYNTHESIS", stages)
        self.assertIn("FEASIBILITY_GATE", stages)

        # 3. Resume workflow: Simulasi otorisasi dari Kepala SPPG via Command(resume=...)
        approval_payload = {
            "action": ApprovalAction.APPROVE,
            "approved_qty_kg": 64.0,
            "approver_name": "Budi Santoso (Kepala SPPG)",
            "approver_notes": "Disetujui dengan skema split delivery sesuai rekomendasi sistem.",
        }

        resume_result = self.workflow.invoke(
            Command(resume=approval_payload),
            config=self.config,
        )

        # 4. Verifikasi akhir: Workflow selesai dan Purchase Order resmi terbit
        final_state = self.workflow.get_state(self.config)
        final_values = final_state.values

        self.assertIsNotNone(final_values.get("po_result"))
        po = final_values["po_result"]
        self.assertTrue(po.po_number.startswith("PO-SPPG-2026-"))
        self.assertEqual(po.approved_qty_kg, 64.0)
        self.assertEqual(po.approver_name, "Budi Santoso (Kepala SPPG)")
        self.assertGreater(po.total_amount_idr, 0)
        self.assertTrue(po.po_download_url.endswith(".pdf"))

        # Verifikasi tahapan audit trail terakhir
        final_stages = [step.stage for step in final_values["audit_trail"]]
        self.assertIn("HUMAN_APPROVAL", final_stages)
        self.assertIn("PO_GENERATION", final_stages)


if __name__ == "__main__":
    unittest.main()

