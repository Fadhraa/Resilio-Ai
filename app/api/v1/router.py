import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Query, status
from sse_starlette.sse import EventSourceResponse

from app.engine.conversational_agent import conversational_agent
from app.engine.tools import (
    deactivate_supplier_tool,
    get_supplier_detail_tool,
    list_all_suppliers_tool,
    register_supplier_tool,
    update_supplier_tool,
)
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
    SupplierCreateRequest,
    SupplierUpdateRequest,
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


# ==========================================
# 4. SUPPLIER MANAGEMENT CRUD REST ENDPOINTS
# ==========================================

@api_router.get("/suppliers", summary="Katalog Seluruh Rekanan Supplier")
def list_suppliers(
    commodity: str = Query(None, description="Filter komoditas (misal DAGING_AYAM, DAGING_SAPI, TELUR_AYAM)"),
    include_inactive: bool = Query(True, description="Sertakan rekanan yang non-aktif (soft-deleted)"),
) -> list[dict]:
    """
    Mengambil katalog seluruh rekanan supplier yang terdaftar di SPPG.
    Mendukung filter berdasarkan jenis komoditas dan status keaktifan.
    """
    return list_all_suppliers_tool(include_inactive=include_inactive, commodity=commodity)


@api_router.get("/suppliers/{supplier_id}", summary="Detail Profil Rekanan Supplier")
def get_supplier_detail(supplier_id: str) -> dict:
    """Mengambil informasi detail satu rekanan supplier berdasarkan ID."""
    result = get_supplier_detail_tool(supplier_id)
    if result["status"] == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"],
        )
    return result["supplier"]


@api_router.post("/suppliers", status_code=status.HTTP_201_CREATED, summary="Registrasi Rekanan Supplier Baru")
def register_supplier(payload: SupplierCreateRequest) -> dict:
    """
    Mendaftarkan rekanan supplier baru dengan validasi otomatis tata kelola SPPG:
    - Penomoran ID unik terurut otomatis (SUP-REG-XX).
    - Verifikasi kepatuhan sertifikasi Halal (UU JPH No. 33/2014).
    - Verifikasi batas pagu anggaran SOP per kg.
    """
    return register_supplier_tool(payload)


@api_router.patch("/suppliers/{supplier_id}", summary="Pembaruan Data Rekanan Supplier")
def update_supplier(supplier_id: str, updates: SupplierUpdateRequest) -> dict:
    """
    Memperbarui sebagian atribut rekanan supplier (partial update) seperti harga,
    kapasitas harian, atau nomor sertifikat halal.
    """
    result = update_supplier_tool(supplier_id, updates)
    if result["status"] == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"],
        )
    return result


@api_router.delete("/suppliers/{supplier_id}", summary="Deaktivasi Rekanan Supplier (Soft Delete)")
def deactivate_supplier(
    supplier_id: str,
    reason: str = Query("Penonaktifan administratif via REST API", description="Alasan penonaktifan rekanan"),
) -> dict:
    """
    Menonaktifkan rekanan supplier (soft delete / is_active = False)
    tanpa menghapus data fisik untuk menjaga keutuhan audit trail transaksi PO.
    """
    result = deactivate_supplier_tool(supplier_id, reason=reason)
    if result["status"] == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"],
        )
    return result


# ==========================================
# 5. DOKUMEN RESMI (SURAT EDARAN & PURCHASE ORDERS)
# ==========================================

@api_router.get("/circular-letters", summary="Arsip Seluruh Surat Edaran Mitigasi SPPG")
def list_circular_letters() -> list[dict]:
    """Mengambil seluruh arsip surat edaran mitigasi pangan dari basis data SQLite."""
    from app.data.sqlite_db import get_all_circular_letters
    return get_all_circular_letters()


@api_router.get("/circular-letters/{letter_id}", summary="Detail Surat Edaran Mitigasi")
def get_circular_letter_detail(letter_id: str) -> dict:
    """Mengambil rincian teks dan metadata satu surat edaran berdasarkan letter_id."""
    from app.data.sqlite_db import get_circular_letter_by_id
    letter = get_circular_letter_by_id(letter_id)
    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surat Edaran dengan ID '{letter_id}' tidak ditemukan.",
        )
    return letter


@api_router.get("/purchase-orders", summary="Arsip Seluruh Purchase Order (PO) Resmi")
def list_purchase_orders() -> list[dict]:
    """Mengambil seluruh riwayat purchase order yang telah diotorisasi dari SQLite."""
    from app.data.sqlite_db import get_all_purchase_orders
    return get_all_purchase_orders()


# ==========================================
# 6. INVENTARIS GUDANG & RIWAYAT SESI CHAT
# ==========================================

@api_router.get("/inventory", summary="Monitoring Stok Gudang Inventaris SPPG")
def list_inventory() -> list[dict]:
    """Mengambil data inventaris bahan pangan aktif, batas aman, dan kapasitas ruang dingin."""
    from app.data.sqlite_db import get_all_inventory_items
    return get_all_inventory_items()


@api_router.get("/chat/sessions/{session_id}/history", summary="Riwayat Obrolan Sesi")
def get_session_history(session_id: str) -> list[dict]:
    """Mengambil riwayat percakapan untuk sesi tertentu dari basis data SQLite."""
    from app.data.sqlite_db import get_chat_session_history
    return get_chat_session_history(session_id)


