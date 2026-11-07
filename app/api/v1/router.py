import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.engine.conversational_agent import conversational_agent
from app.engine.workflow import build_procurement_workflow
from app.models.schemas import (
    ApprovalAction,
    ApprovalRequest,
    ChatRequest,
    ChatResponse,
    IncidentDecisionResponse,
    IncidentTriggerRequest,
    IncidentTriggerResponse,
    PurchaseOrderResponse,
)
from app.services.data_layer import data_layer_service
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

api_router = APIRouter()

# Global memory cache untuk thread LangGraph insiden formal
incident_workflows: dict[str, dict] = {}
shared_api_checkpointer = MemorySaver()
global_workflow = build_procurement_workflow(checkpointer=shared_api_checkpointer)


# ==========================================
# 1. CONVERSATIONAL AGENT ENDPOINTS (CHATBOT)
# ==========================================

@api_router.post("/chat", response_model=ChatResponse, summary="Obrolan Interaktif Kepala SPPG")
def chat_with_agent(request: ChatRequest) -> ChatResponse:
    """
    Endpoint obrolan bahasa alami untuk pelaporan insiden, verifikasi rekanan,
    dan negosiasi strategi mitigasi secara multi-turn.
    """
    try:
        return conversational_agent.process_message(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan pada mesin agen percakapan: {str(e)}",
        )


@api_router.post("/chat/approve", response_model=PurchaseOrderResponse, summary="Otorisasi Cepat via Tombol Chat")
def approve_from_chat(payload: ApprovalRequest) -> PurchaseOrderResponse:
    """
    Endpoint otorisasi cepat melalui klik tombol [Setujui & Terbitkan PO] di UI Chat.
    """
    session = conversational_agent.get_or_create_session(payload.incident_id)
    if not session.get("current_recommendation"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Belum ada rekomendasi mitigasi yang aktif untuk sesi ini.",
        )

    # Jalankan approval melalui conversational agent
    chat_req = ChatRequest(
        session_id=payload.incident_id,
        message=f"Setujui dan terbitkan PO. Catatan: {payload.approver_notes or 'Disetujui via tombol UI'}",
        user_role=payload.approver_name,
    )
    chat_resp = conversational_agent.process_message(chat_req)

    if session.get("po_result"):
        return session["po_result"]

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Gagal menerbitkan Purchase Order.",
    )


# ==========================================
# 2. DIRECT PIPELINE ENDPOINTS (PRD FORMAL)
# ==========================================

@api_router.post("/incidents/trigger", response_model=IncidentTriggerResponse, summary="Memicu Pipeline Mitigasi")
def trigger_incident(payload: IncidentTriggerRequest) -> IncidentTriggerResponse:
    """
    Memicu alur kerja mitigasi insiden SPPG secara asinkron.
    """
    incident_id = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    config = {"configurable": {"thread_id": incident_id}}

    workflow_input = {
        "incident_id": incident_id,
        "item_id": payload.item_id,
        "disruption_type": payload.disruption_type,
        "affected_supplier_id": payload.affected_supplier_id,
        "estimated_duration_days": payload.estimated_duration_days,
        "incident_notes": payload.incident_notes,
        "target_production_portions": 3000,
    }

    # Jalankan workflow hingga terhenti di Human Approval Gate
    global_workflow.invoke(workflow_input, config=config)

    # Simpan metadata insiden aktif
    incident_workflows[incident_id] = {
        "config": config,
        "status": "PROCESSING",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return IncidentTriggerResponse(
        incident_id=incident_id,
        status="PROCESSING",
        stream_url=f"/api/v1/incidents/{incident_id}/stream",
    )


@api_router.get("/incidents/{incident_id}/decision", response_model=IncidentDecisionResponse, summary="Ambil Keputusan Mitigasi")
def get_incident_decision(incident_id: str) -> IncidentDecisionResponse:
    """
    Mengambil data rekomendasi mitigasi, kalkulasi metrik, dan rekam jejak audit
    saat alur berada di gerbang persetujuan.
    """
    config = {"configurable": {"thread_id": incident_id}}
    state = global_workflow.get_state(config)
    values = state.values

    if not values or not values.get("metrics"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data insiden '{incident_id}' tidak ditemukan atau belum selesai diproses.",
        )

    item = data_layer_service.get_inventory_item(values["item_id"])
    item_name = item.item_name if item else values["item_id"]

    return IncidentDecisionResponse(
        incident_id=incident_id,
        item_id=values["item_id"],
        item_name=item_name,
        metrics=values["metrics"],
        recommended_procurement=values.get("recommended_procurement"),
        audit_trail=values.get("audit_trail", []),
    )


@api_router.post("/incidents/{incident_id}/approve", response_model=PurchaseOrderResponse, summary="Otorisasi Kepala SPPG")
def approve_incident_decision(incident_id: str, payload: ApprovalRequest) -> PurchaseOrderResponse:
    """
    Mengeksekusi persetujuan dari Kepala SPPG dan melanjutkan alur LangGraph untuk menerbitkan PO.
    """
    config = {"configurable": {"thread_id": incident_id}}
    state = global_workflow.get_state(config)

    if not state.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesi insiden '{incident_id}' tidak ditemukan.",
        )

    approval_payload = {
        "action": payload.action,
        "approved_qty_kg": payload.approved_qty_kg,
        "approver_name": payload.approver_name,
        "approver_notes": payload.approver_notes,
    }

    # Resume eksekusi interrupt
    global_workflow.invoke(Command(resume=approval_payload), config=config)

    # Ambil final state
    final_state = global_workflow.get_state(config)
    po = final_state.values.get("po_result")

    if not po:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Persetujuan diproses namun Purchase Order tidak diterbitkan (mungkin aksi Ditolak).",
        )

    return po


@api_router.get("/incidents/{incident_id}/stream", summary="Server-Sent Events Real-time Stream")
async def stream_incident_status(incident_id: str) -> EventSourceResponse:
    """
    Transmisi status per node alur LangGraph secara real-time ke UI frontend via SSE.
    """
    config = {"configurable": {"thread_id": incident_id}}

    async def event_generator() -> AsyncGenerator[dict, None]:
        # Simulasi transmisi status event ke frontend Next.js sesuai PRD
        yield {
            "event": "node_started",
            "data": json.dumps({"node": "deterministic_data_layer", "timestamp": datetime.now(timezone.utc).isoformat()}),
        }
        await asyncio.sleep(0.3)

        state = global_workflow.get_state(config)
        values = state.values
        metrics = values.get("metrics")

        if metrics:
            yield {
                "event": "node_completed",
                "data": json.dumps({
                    "node": "deterministic_data_layer",
                    "deficit_kg": metrics.deficit_kg,
                    "current_stock_kg": metrics.current_stock_kg,
                    "freezer_remaining_kg": metrics.freezer_available_kg,
                }),
            }
            await asyncio.sleep(0.3)

        rec = values.get("recommended_procurement")
        if rec:
            yield {
                "event": "node_started",
                "data": json.dumps({"node": "strategic_procurement_agent", "model": "gemini-2.5-flash"}),
            }
            await asyncio.sleep(0.3)

            yield {
                "event": "node_completed",
                "data": json.dumps({
                    "node": "feasibility_scoring_engine",
                    "score": rec.feasibility_score,
                    "status": rec.feasibility_status.value,
                }),
            }
            await asyncio.sleep(0.2)

        yield {
            "event": "workflow_waiting_approval",
            "data": json.dumps({"incident_id": incident_id, "decision_ready": True}),
        }

    return EventSourceResponse(event_generator())

