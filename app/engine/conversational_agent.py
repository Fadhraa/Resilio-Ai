"""
Conversational Agent Facade & Orchestrator for ResilioAI.
Arsitektur: Two-Stage Cognitive Agent Loop (Industry Standard 2026).
Menyediakan antarmuka modular yang mendelegasikan tugas ke sub-modul di app.engine.agent:
- router: Cognitive Decision Engine (Stage 1)
- handlers: Deterministic Execution & Multi-Turn State Management (Stage 2 & 3)
- parsers: Entity sanitization & Database Verification Guardrails
- prompts: System instructions & universal persona
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Muat environment variables dari .env
load_dotenv()

from app.engine.agent.parsers import (
    clean_ai_output,
    detect_item_id,
    extract_portions,
    infer_commodity_and_category,
    match_supplier_in_text,
    parse_supplier_create_data,
    verify_and_sanitize_suppliers,
)
from app.engine.agent.prompts import SYSTEM_PROMPTS, UNIVERSAL_PERSONA
from app.engine.agent.router import decide_action, fallback_decide_action
from app.engine.agent.handlers import (
    handle_approval,
    handle_clarification_confirmed,
    handle_clear_documents,
    handle_consultative_chat,
    handle_crud_confirmation,
    handle_delete_single_document,
    handle_explain_capabilities,
    handle_get_inventory,
    handle_greeting,
    handle_incident_report,
    handle_list_suppliers,
    handle_out_of_domain,
    handle_procurement_planning,
    handle_revision,
    handle_supplier_management,
)
from app.models.schemas import ChatActionRequired, ChatIntent, ChatRequest, ChatResponse


class ConversationalAgentManager:
    """
    Orchestrator Facade untuk Chatbot Asisten Rantai Pasok ResilioAI.
    Menghubungkan API endpoint dengan engine modular di package app.engine.agent.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _clean_ai_output(self, text: str) -> str:
        """Membersihkan output teks dari sintaks LaTeX, markdown berantakan, dan salam klise."""
        return clean_ai_output(text)

    def _call_gemini_adaptive(
        self,
        system_instructions: str,
        user_message: str,
        context_data: str = "",
        fallback_text: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
        target_sup_name: Optional[str] = None,
    ) -> str:
        """
        Memanggil LLM Gemini untuk mensintesis respon bahasa alami yang luwes dan adaptif.
        Menjalankan Database Verification Guardrail sebelum mengembalikan respon ke user.
        """
        if not self.api_key or self.api_key.startswith("your_"):
            cleaned = self._clean_ai_output(fallback_text)
            return verify_and_sanitize_suppliers(cleaned, target_sup_name=target_sup_name)

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                transport="rest",
                google_api_key=self.api_key,
                timeout=12,
            )
            prompt = [("system", system_instructions)]
            if history:
                for h in history[-6:]:
                    role = "human" if h.get("role") == "user" else "assistant"
                    prompt.append((role, h.get("content", "")))

            prompt.append((
                "user",
                f"Konteks Data Operasional SPPG Terverifikasi:\n{context_data}\n\n"
                f"Pesan dari Kepala SPPG:\n\"{user_message}\"\n\n"
                f"Berikan jawaban yang adaptif, komunikatif, profesional, dan to-the-point tanpa format LaTeX dan tanpa salam klise berulang.",
            ))
            response = llm.invoke(prompt)
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, list):
                    text_out = "".join([str(p) for p in response.content]).strip()
                else:
                    text_out = str(response.content).strip()
                if len(text_out) > 10:
                    cleaned = self._clean_ai_output(text_out)
                    return verify_and_sanitize_suppliers(cleaned, target_sup_name=target_sup_name)

            cleaned = self._clean_ai_output(fallback_text)
            return verify_and_sanitize_suppliers(cleaned, target_sup_name=target_sup_name)
        except Exception:
            cleaned = self._clean_ai_output(fallback_text)
            return verify_and_sanitize_suppliers(cleaned, target_sup_name=target_sup_name)

    def _respond(self, session: Dict[str, Any], response: ChatResponse) -> ChatResponse:
        """Mencatat respons asisten ke riwayat percakapan sesi dan mengembalikan response."""
        session["history"].append({
            "role": "assistant",
            "content": response.reply,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        try:
            from app.data.sqlite_db import record_chat_message

            record_chat_message(
                session_id=response.session_id,
                role="assistant",
                message=response.reply,
                intent=response.intent.value if hasattr(response.intent, "value") else str(response.intent),
                action_required=response.action_required.value if hasattr(response.action_required, "value") else str(response.action_required),
                preview_data=response.preview_data,
            )
        except Exception:
            pass
        return response

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Mengambil atau menginisialisasi sesi percakapan baru."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "incident_context": {},
                "current_metrics": None,
                "current_recommendation": None,
                "is_approved": False,
                "history": [],
                "pending_crud": None,
                "pending_clarification": None,
                "procurement_plan": None,
                "saved_pos": None,
            }
        return self._sessions[session_id]

    # Helper Wrappers untuk Backward Compatibility
    def _extract_portions(self, text: str, default: int = 3000) -> int:
        return extract_portions(text, default=default)

    def _detect_item_id(self, text: str) -> str:
        return detect_item_id(text)

    def _match_supplier_in_text(self, text: str):
        return match_supplier_in_text(text)

    def _infer_commodity_and_category(self, user_msg: str, name_or_notes: str):
        return infer_commodity_and_category(user_msg, name_or_notes)

    def _parse_supplier_create_data(self, user_msg: str):
        return parse_supplier_create_data(user_msg)

    def _decide_action(self, user_msg: str, session: Dict[str, Any]) -> Dict[str, Any]:
        return decide_action(
            user_message=user_msg,
            session=session,
            api_key=self.api_key,
            model_name=self.model_name,
        )

    def _fallback_decide_action(self, user_msg: str, session: Dict[str, Any]) -> Dict[str, Any]:
        return fallback_decide_action(user_message=user_msg, session=session)

    # Delegasi Handler ke Sub-modul Modular
    def _handle_greeting(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        return handle_greeting(session, request, self._call_gemini_adaptive, self._respond)

    def _handle_list_suppliers(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        return handle_list_suppliers(session, request, params, self._call_gemini_adaptive, self._respond)

    def _handle_get_inventory(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        return handle_get_inventory(session, request, params, self._call_gemini_adaptive, self._respond)

    def _handle_supplier_management(self, session: Dict[str, Any], request: ChatRequest, action: str, params: Dict[str, Any]) -> ChatResponse:
        return handle_supplier_management(session, request, action, params, self._call_gemini_adaptive, self._respond, self.api_key, self.model_name)

    def _handle_crud_confirmation(self, session: Dict[str, Any], request: ChatRequest, is_confirm: bool) -> ChatResponse:
        return handle_crud_confirmation(session, request, is_confirm, self._call_gemini_adaptive, self._respond)

    def _handle_incident_report(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        return handle_incident_report(session, request, params, self._call_gemini_adaptive, self._respond)

    def _handle_clarification_confirmed(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        return handle_clarification_confirmed(session, request, params, self._call_gemini_adaptive, self._respond)

    def _handle_revision(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        return handle_revision(session, request, params, self._call_gemini_adaptive, self._respond)

    def _handle_procurement_planning(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        return handle_procurement_planning(session, request, params, self._call_gemini_adaptive, self._respond)

    def _handle_approval(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        return handle_approval(session, request, params, self._call_gemini_adaptive, self._respond)

    def _handle_consultative_chat(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        return handle_consultative_chat(session, request, self._call_gemini_adaptive, self._respond)

    def _handle_out_of_domain(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        return handle_out_of_domain(session, request, self._respond)

    def _handle_clear_documents(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        return handle_clear_documents(session, request, self._respond)

    def _handle_delete_single_document(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        return handle_delete_single_document(session, request, params, self._respond)

    def _handle_explain_capabilities(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        return handle_explain_capabilities(session, request, self._respond)

    # Main Entry Point Dispatcher
    def process_message(self, request: ChatRequest) -> ChatResponse:
        """Memproses satu giliran pesan dari pengguna dan mengembalikan respons terstruktur."""
        session = self.get_or_create_session(request.session_id)
        user_msg = request.message.strip()

        # Rekam pesan user ke riwayat
        session["history"].append({
            "role": "user",
            "content": user_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        try:
            from app.data.sqlite_db import record_chat_message

            record_chat_message(
                session_id=request.session_id,
                role="user",
                message=user_msg,
            )
        except Exception:
            pass

        # Stage 1: AI Cognitive Decision Engine (Gemini 3.5 Flash-Lite / Fallback)
        decision = self._decide_action(user_msg, session)
        action = decision.get("action", "GENERAL_CHAT")
        params = decision.get("parameters", {})

        # Stage 2 & 3: Deterministic Tool Execution & Natural Synthesis
        if action == "CONFIRM_CRUD":
            return self._handle_crud_confirmation(session, request, is_confirm=True)
        elif action == "CANCEL_CRUD":
            return self._handle_crud_confirmation(session, request, is_confirm=False)
        elif action == "GREETING":
            return self._handle_greeting(session, request)
        elif action == "APPROVE_PO":
            return self._handle_approval(session, request, params)
        elif action == "CONFIRM_CLARIFICATION":
            return self._handle_clarification_confirmed(session, request, params)
        elif action == "REQUEST_REVISION":
            return self._handle_revision(session, request, params)
        elif action in ["REGISTER_SUPPLIER", "UPDATE_SUPPLIER", "DEACTIVATE_SUPPLIER"]:
            return self._handle_supplier_management(session, request, action, params)
        elif action == "LIST_SUPPLIERS":
            return self._handle_list_suppliers(session, request, params)
        elif action == "GET_INVENTORY":
            return self._handle_get_inventory(session, request, params)
        elif action == "REPORT_INCIDENT":
            return self._handle_incident_report(session, request, params)
        elif action == "OUT_OF_DOMAIN":
            return self._handle_out_of_domain(session, request)
        elif action == "CLEAR_DOCUMENTS":
            return self._handle_clear_documents(session, request)
        elif action == "DELETE_DOCUMENT":
            return self._handle_delete_single_document(session, request, params)
        elif action == "PLAN_PROCUREMENT":
            return self._handle_procurement_planning(session, request, params)
        elif action == "EXPLAIN_CAPABILITIES":
            return self._handle_explain_capabilities(session, request)
        else:
            return self._handle_consultative_chat(session, request)


# Singleton instance conversational agent
conversational_agent = ConversationalAgentManager()
