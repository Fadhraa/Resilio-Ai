import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.engine.agent import strategic_agent
from app.engine.feasibility import feasibility_engine
from app.engine.state import ProcurementWorkflowState
from app.models.schemas import (
    ApprovalAction,
    ApprovalRequest,
    AuditTrailStep,
    PurchaseOrderResponse,
    RecommendedProcurement,
)
from app.services.data_layer import data_layer_service


# ==========================================
# 1. NODE IMPLEMENTATIONS
# ==========================================

def ingestion_node(state: ProcurementWorkflowState) -> dict:
    """Node 1: Menerima payload insiden dan menginisialisasi audit trail."""
    step = AuditTrailStep(
        stage="INGESTION",
        status="COMPLETED",
        message=f"Insiden terdaftar untuk bahan {state['item_id']} dengan status disrupsi {state['disruption_type']}.",
    )
    current_trail = state.get("audit_trail") or []
    return {
        "audit_trail": current_trail + [step],
        "retry_count": state.get("retry_count", 0),
        "current_stage": "DATA_AGGREGATION",
    }


def data_layer_node(state: ProcurementWorkflowState) -> dict:
    """Node 2: Kueri inventaris dan kalkulasi defisit deterministik."""
    target_portions = state.get("target_production_portions", 3000)
    metrics = data_layer_service.calculate_metrics(
        item_id=state["item_id"],
        target_portions=target_portions,
    )
    step = AuditTrailStep(
        stage="DATA_AGGREGATION",
        status="DETERMINISTIC_PASS",
        message=(
            f"Stok gudang {metrics.current_stock_kg} kg, defisit terhitung {metrics.deficit_kg} kg, "
            f"sisa freezer {metrics.freezer_available_kg} kg."
        ),
    )
    return {
        "metrics": metrics,
        "audit_trail": state["audit_trail"] + [step],
        "current_stage": "COMPLIANCE_FILTER",
    }


def compliance_filter_node(state: ProcurementWorkflowState) -> dict:
    """Node 3: Hard-Constraint Filter supplier rekanan (Halal Wajib)."""
    item = data_layer_service.get_inventory_item(state["item_id"])
    if not item:
        raise ValueError(f"Item '{state['item_id']}' tidak ditemukan.")

    eligible = data_layer_service.get_eligible_suppliers(
        category=item.category,
        exclude_supplier_id=state.get("affected_supplier_id"),
        max_distance_km=100.0,
    )
    step = AuditTrailStep(
        stage="COMPLIANCE_FILTER",
        status="DETERMINISTIC_PASS",
        message=f"{len(eligible)} rekanan supplier bersertifikat halal aktif berhasil disaring.",
    )
    return {
        "eligible_suppliers": eligible,
        "audit_trail": state["audit_trail"] + [step],
        "current_stage": "STRATEGY_SYNTHESIS",
    }


def strategic_agent_node(state: ProcurementWorkflowState) -> dict:
    """Node 4: LLM Strategic Agent merumuskan alokasi dan taktik logistik."""
    item = data_layer_service.get_inventory_item(state["item_id"])
    item_name = item.item_name if item else state["item_id"]

    rec = strategic_agent.synthesize_strategy(
        eligible_suppliers=state["eligible_suppliers"],
        metrics=state["metrics"],
        item_name=item_name,
        retry_count=state.get("retry_count", 0),
    )
    step = AuditTrailStep(
        stage="STRATEGY_SYNTHESIS",
        status="AGENT_REASONING_PASS",
        message=(
            f"Agen merumuskan strategi '{rec.logistics_strategy.strategy_type.value}' "
            f"menggunakan supplier rekanan {rec.supplier_name}."
        ),
    )
    return {
        "recommended_procurement": rec,
        "audit_trail": state["audit_trail"] + [step],
        "current_stage": "FEASIBILITY_GATE",
    }


def feasibility_gate_node(state: ProcurementWorkflowState) -> dict:
    """Node 5: Evaluasi kelayakan deterministik matriks 7 parameter."""
    rec: RecommendedProcurement = state["recommended_procurement"]
    metrics = state["metrics"]
    item = data_layer_service.get_inventory_item(state["item_id"])
    sop_max_price = item.sop_max_price_per_kg if item else 50000.0

    # Ambil supplier record dari eligible_suppliers
    selected_supplier = next(
        (s for s in state["eligible_suppliers"] if s.supplier_id == rec.supplier_id),
        state["eligible_suppliers"][0],
    )

    # Kuantitas pengiriman batch pertama untuk evaluasi freezer
    first_batch_qty = (
        rec.logistics_strategy.batches[0].qty_kg
        if rec.logistics_strategy.batches
        else metrics.deficit_kg
    )

    score, status, breakdown = feasibility_engine.evaluate(
        supplier=selected_supplier,
        metrics=metrics,
        sop_max_price_per_kg=sop_max_price,
        initial_batch_qty_kg=first_batch_qty,
    )

    # Update data rekomendasi dengan hasil perhitungan deterministik murni
    updated_rec = rec.model_copy(
        update={
            "feasibility_score": score,
            "feasibility_status": status,
            "scoring_breakdown": breakdown,
        }
    )

    step = AuditTrailStep(
        stage="FEASIBILITY_GATE",
        status="VERIFIED",
        message=f"Skor kelayakan dihitung deterministik: {score}/100 ({status.value}).",
    )
    return {
        "recommended_procurement": updated_rec,
        "audit_trail": state["audit_trail"] + [step],
        "current_stage": "APPROVAL_GATE",
    }


def retry_node(state: ProcurementWorkflowState) -> dict:
    """Node pembantu untuk menambah counter percobaan saat skor < 60."""
    new_count = state.get("retry_count", 0) + 1
    step = AuditTrailStep(
        stage="FEASIBILITY_GATE",
        status="RETRY_TRIGGERED",
        message=f"Skor kelayakan < 60. Memicu siklus evaluasi supplier alternatif (Percobaan #{new_count}).",
    )
    return {
        "retry_count": new_count,
        "audit_trail": state["audit_trail"] + [step],
        "current_stage": "STRATEGY_SYNTHESIS",
    }


def approval_gate_node(state: ProcurementWorkflowState) -> dict:
    """
    Node 6: Human Approval Gate (HITL) menggunakan LangGraph interrupt().
    Menahan alur sampai pengguna (Kepala SPPG) mengirim otorisasi.
    """
    rec: RecommendedProcurement = state["recommended_procurement"]

    # Interrupt menahan eksekusi dan memancarkan data keputusan ke UI frontend
    decision_payload = interrupt({
        "incident_id": state["incident_id"],
        "recommended_procurement": rec.model_dump(),
        "prompt": "Menunggu persetujuan Kepala SPPG untuk penerbitan Purchase Order.",
    })

    # Saat workflow di-resume menggunakan Command(resume=approval_dict), payload masuk ke decision_payload
    if isinstance(decision_payload, dict):
        action = decision_payload.get("action", ApprovalAction.APPROVE)
        approver_name = decision_payload.get("approver_name", "Kepala SPPG")
        approved_qty = decision_payload.get("approved_qty_kg", state["metrics"].deficit_kg)
        approver_notes = decision_payload.get("approver_notes")
    else:
        action = ApprovalAction.APPROVE
        approver_name = "Kepala SPPG"
        approved_qty = state["metrics"].deficit_kg
        approver_notes = None

    approval_request = ApprovalRequest(
        incident_id=state["incident_id"],
        action=action,
        approved_qty_kg=approved_qty,
        approver_name=approver_name,
        approver_notes=approver_notes,
    )

    step = AuditTrailStep(
        stage="HUMAN_APPROVAL",
        status="APPROVED" if action == ApprovalAction.APPROVE else "REJECTED",
        message=f"Keputusan persetujuan diterima dari {approver_name} dengan aksi '{action}'.",
    )
    return {
        "approval_status": action,
        "approver_decision": approval_request,
        "audit_trail": state["audit_trail"] + [step],
        "current_stage": "EXECUTION_PO",
    }


def execution_po_node(state: ProcurementWorkflowState) -> dict:
    """Node 7: Penerbitan Purchase Order resmi dan finalisasi log audit."""
    rec: RecommendedProcurement = state["recommended_procurement"]
    approval = state.get("approver_decision")
    approved_qty = approval.approved_qty_kg if approval else state["metrics"].deficit_kg
    approver_name = approval.approver_name if approval else "Kepala SPPG"

    po_number = f"PO-SPPG-2026-{datetime.now(timezone.utc).strftime('%m%d%H%M%S')}"
    total_amount = round(approved_qty * rec.unit_price_idr, 2)

    po = PurchaseOrderResponse(
        status="SUCCESS",
        po_number=po_number,
        incident_id=state["incident_id"],
        supplier_id=rec.supplier_id,
        supplier_name=rec.supplier_name,
        item_id=state["item_id"],
        approved_qty_kg=approved_qty,
        unit_price_idr=rec.unit_price_idr,
        total_amount_idr=total_amount,
        logistics_strategy=rec.logistics_strategy,
        approver_name=approver_name,
        po_download_url=f"/api/v1/procurement/po/{po_number}.pdf",
    )

    step = AuditTrailStep(
        stage="PO_GENERATION",
        status="SUCCESS",
        message=f"Purchase Order resmi diterbitkan dengan nomor {po_number} senilai Rp {total_amount:,.2f}.",
    )
    return {
        "po_result": po,
        "audit_trail": state["audit_trail"] + [step],
        "current_stage": "COMPLETED",
    }


# ==========================================
# 2. CONDITIONAL ROUTING FUNCTIONS
# ==========================================

def route_feasibility_gate(
    state: ProcurementWorkflowState,
) -> Literal["approval_gate_node", "retry_node", "__end__"]:
    """Menentukan rute berdasarkan skor kelayakan deterministik."""
    rec = state.get("recommended_procurement")
    if not rec:
        return "__end__"

    score = rec.feasibility_score
    if score >= 60.0:
        return "approval_gate_node"

    # Jika skor < 60 dan masih memiliki kuota retry (< 3 kali)
    if state.get("retry_count", 0) < 3:
        return "retry_node"

    return "__end__"


def route_approval_gate(
    state: ProcurementWorkflowState,
) -> Literal["execution_po_node", "__end__"]:
    """Menentukan rute setelah persetujuan manusia."""
    action = state.get("approval_status")
    if action == ApprovalAction.APPROVE:
        return "execution_po_node"
    return "__end__"


# ==========================================
# 3. WORKFLOW BUILDER & SINGLETON
# ==========================================

def build_procurement_workflow(checkpointer: Optional[MemorySaver] = None):
    """Membangun StateGraph alur mitigasi rantai pasok SPPG."""
    builder = StateGraph(ProcurementWorkflowState)

    # 1. Tambah Seluruh Node
    builder.add_node("ingestion_node", ingestion_node)
    builder.add_node("data_layer_node", data_layer_node)
    builder.add_node("compliance_filter_node", compliance_filter_node)
    builder.add_node("strategic_agent_node", strategic_agent_node)
    builder.add_node("feasibility_gate_node", feasibility_gate_node)
    builder.add_node("retry_node", retry_node)
    builder.add_node("approval_gate_node", approval_gate_node)
    builder.add_node("execution_po_node", execution_po_node)

    # 2. Alur Edge Awal
    builder.add_edge(START, "ingestion_node")
    builder.add_edge("ingestion_node", "data_layer_node")
    builder.add_edge("data_layer_node", "compliance_filter_node")
    builder.add_edge("compliance_filter_node", "strategic_agent_node")
    builder.add_edge("strategic_agent_node", "feasibility_gate_node")

    # 3. Conditional Edge: Feasibility Gate
    builder.add_conditional_edges(
        "feasibility_gate_node",
        route_feasibility_gate,
        {
            "approval_gate_node": "approval_gate_node",
            "retry_node": "retry_node",
            "__end__": END,
        },
    )
    builder.add_edge("retry_node", "strategic_agent_node")

    # 4. Conditional Edge: Human Approval Gate
    builder.add_conditional_edges(
        "approval_gate_node",
        route_approval_gate,
        {
            "execution_po_node": "execution_po_node",
            "__end__": END,
        },
    )
    builder.add_edge("execution_po_node", END)

    # 5. Compile dengan Checkpointer untuk Persistensi State & Interrupt
    saver = checkpointer or MemorySaver()
    return builder.compile(checkpointer=saver)


# Global compiled workflow instance
shared_checkpointer = MemorySaver()
procurement_workflow = build_procurement_workflow(checkpointer=shared_checkpointer)
