import time
from langgraph.types import Command
from app.engine.workflow import build_procurement_workflow
from app.models.schemas import ApprovalAction, DisruptionType, StrategyType


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def run_interactive_simulation():
    print_banner("SIMULASI TERMINAL: RESILIOAI HYBRID MULTI-AGENT ENGINE")
    print("Skenario: Program Satuan Pelayanan Pemenuhan Gizi (SPPG)")
    print("Target: Produksi 3.000 Porsi Makan Bergizi")
    print("-" * 65)

    # 1. Inisialisasi Alur Kerja & Checkpointer
    workflow = build_procurement_workflow()
    thread_id = f"simulasi-terminal-{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}

    # 2. Definisikan Insiden Lapangan
    incident_payload = {
        "incident_id": "INC-SPPG-2026-001",
        "item_id": "ITEM-AYAM-01",
        "disruption_type": DisruptionType.SUPPLIER_DISRUPTION,
        "affected_supplier_id": "SUP-UTAMA-01",
        "estimated_duration_days": 3,
        "incident_notes": "Armada supplier utama (PT Unggas Sejahtera) terjebak banjir di Jalur Pantura.",
        "target_production_portions": 3000,
    }

    print("\n[1/6] 🚨 Memicu Laporan Insiden...")
    print(f"      - ID Insiden      : {incident_payload['incident_id']}")
    print(f"      - Bahan Terdampak : {incident_payload['item_id']} (Daging Ayam Broiler)")
    print(f"      - Disrupsi        : {incident_payload['incident_notes']}")

    # 3. Jalankan pipeline hingga terhenti di Human Approval Gate
    print("\n[2/6] ⚙️  Mengeksekusi Deterministic Pipeline & Agent...")
    workflow.invoke(incident_payload, config=config)

    # Ambil snapshot state saat interrupt
    state = workflow.get_state(config)
    values = state.values
    metrics = values["metrics"]
    rec = values["recommended_procurement"]

    # Tampilkan Hasil Tahap 1: Data Layer
    print("\n[3/6] 📊 Hasil Data Layer Deterministik (Zero Hallucination):")
    print(f"      - Stok Gudang Aktual    : {metrics.current_stock_kg} kg")
    print(f"      - Kebutuhan Riil Dapur  : 144.0 kg (120 kg dasar + Buffer 20%)")
    print(f"      - Defisit Bahan         : {metrics.deficit_kg} kg (Kurang!")
    print(f"      - Sisa Ruang Freezer    : {metrics.freezer_available_kg} kg (Kapasitas Kritis!)")
    print(f"      - Paparan Risiko Finansial: Rp {metrics.financial_risk_exposure_idr:,.2f}")

    # Tampilkan Hasil Tahap 2 & 3: Agent Reasoning & Feasibility Score
    print("\n[4/6] 🧠 Rekomendasi Strategic Agent & Feasibility Score:")
    print(f"      - Rekanan Rekomendasi   : {rec.supplier_name} ({rec.supplier_id})")
    print(f"      - Status Sertifikat Halal: {'AKTIF ✅' if rec.halal_certificate_active else 'TIDAK AKTIF ❌'}")
    print(f"      - Harga Penawaran       : Rp {rec.unit_price_idr:,.2f} / kg")
    print(f"      - Total Estimasi Biaya  : Rp {rec.total_estimated_cost_idr:,.2f}")
    print(f"      - Skor Kelayakan (0-100): {rec.feasibility_score}/100 ➔ [{rec.feasibility_status.value}]")
    print(f"      - Taktik Logistik       : {rec.logistics_strategy.strategy_type.value}")
    print(f"      - Rincian Kloter Kirim  :")
    for batch in rec.logistics_strategy.batches:
        print(f"        * Kloter #{batch.batch_no}: {batch.qty_kg} kg ➔ Tiba: {batch.eta}")
    print(f"      - Alasan / Justifikasi  : {rec.logistics_strategy.rationale}")

    # Tampilkan Rincian Skor 7 Parameter
    breakdown = rec.scoring_breakdown
    print("\n[5/6] 📋 Rapor Skoring 7 Parameter Berbobot:")
    print(f"      1. Ketersediaan Pasokan (25%) : {breakdown.stock_fulfillment}/100")
    print(f"      2. Waktu Tiba / Lead Time (20%): {breakdown.time_lead_compliance}/100")
    print(f"      3. Kepatuhan Anggaran SOP (15%): {breakdown.budget_compliance}/100")
    print(f"      4. Legalitas & Halal (15%)    : {breakdown.halal_and_legal}/100 (Gating Mutlak)")
    print(f"      5. Kesesuaian Freezer (10%)    : {breakdown.storage_compatibility}/100")
    print(f"      6. Kesiapan Dapur SPPG (10%)  : {breakdown.kitchen_capacity}/100")
    print(f"      7. Keamanan Rute Logistik (5%) : {breakdown.route_safety}/100")

    # 4. Human-in-the-Loop: Minta Input Pengguna di Terminal
    print_banner("GERBANG PERSETUJUAN KEPALA SPPG (HUMAN-IN-THE-LOOP)")
    print("Sistem tertahan (paused) menunggu otorisasi keputusan manusia...")
    user_input = input("\nApakah Anda menyetujui pengadaan darurat ini? (Y/n): ").strip().lower()

    if user_input in ["y", "yes", ""]:
        action = ApprovalAction.APPROVE
        approver_notes = "Disetujui via simulasi terminal interaktif."
        print("\n✅ Otorisasi diterima: DISETUJUI. Melanjutkan alur eksekusi...")
    else:
        action = ApprovalAction.REJECT
        approver_notes = "Ditolak oleh pimpinan via terminal."
        print("\n❌ Otorisasi: DITOLAK. Menghentikan alur kerja...")

    # 5. Resume LangGraph dengan Otorisasi Manusia
    approval_payload = {
        "action": action,
        "approved_qty_kg": metrics.deficit_kg,
        "approver_name": "Kepala SPPG (User Demo)",
        "approver_notes": approver_notes,
    }

    workflow.invoke(Command(resume=approval_payload), config=config)

    # 6. Tampilkan Hasil Akhir (PO Resmi)
    final_state = workflow.get_state(config)
    final_values = final_state.values

    if action == ApprovalAction.APPROVE and final_values.get("po_result"):
        po = final_values["po_result"]
        print_banner("DOKUMEN PURCHASE ORDER RESMI BERHASIL DITERBITKAN")
        print(f"  Nomor PO         : {po.po_number}")
        print(f"  Supplier Rekanan : {po.supplier_name}")
        print(f"  Kuantitas        : {po.approved_qty_kg} kg")
        print(f"  Harga Satuan     : Rp {po.unit_price_idr:,.2f}")
        print(f"  Total Transaksi  : Rp {po.total_amount_idr:,.2f}")
        print(f"  Otorisator       : {po.approver_name}")
        print(f"  File Unduhan     : {po.po_download_url}")
        print("-" * 65)

    print("\n📜 Jejak Audit (Immutable Audit Trail):")
    for idx, step in enumerate(final_values.get("audit_trail", []), 1):
        print(f"  {idx}. [{step.stage}] ➔ {step.status}: {step.message}")

    print_banner("SIMULASI TERMINAL SELESAI DENGAN SUKSES!")


if __name__ == "__main__":
    run_interactive_simulation()

