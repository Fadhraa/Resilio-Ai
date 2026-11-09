"""
ResilioAI Agent Sub-Package.
Menyediakan modular cognitive agent engine untuk sistem ketahanan rantai pasok SPPG.
"""

from app.engine.agent.strategic import StrategicProcurementAgent, strategic_agent
from app.engine.agent.prompts import SYSTEM_PROMPTS, UNIVERSAL_PERSONA
from app.engine.agent.parsers import (
    clean_ai_output,
    detect_item_id,
    extract_portions,
    infer_commodity_and_category,
    match_supplier_in_text,
    parse_supplier_create_data,
    verify_and_sanitize_suppliers,
)
from app.engine.agent.router import decide_action, fallback_decide_action
from app.engine.agent.handlers import (
    handle_approval,
    handle_clear_documents,
    handle_clarification_confirmed,
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

__all__ = [
    "StrategicProcurementAgent",
    "strategic_agent",
    "UNIVERSAL_PERSONA",
    "SYSTEM_PROMPTS",
    "clean_ai_output",
    "verify_and_sanitize_suppliers",
    "detect_item_id",
    "extract_portions",
    "infer_commodity_and_category",
    "match_supplier_in_text",
    "parse_supplier_create_data",
    "decide_action",
    "fallback_decide_action",
    "handle_procurement_planning",
    "handle_revision",
    "handle_approval",
    "handle_list_suppliers",
    "handle_supplier_management",
    "handle_crud_confirmation",
    "handle_incident_report",
    "handle_clarification_confirmed",
    "handle_get_inventory",
    "handle_clear_documents",
    "handle_delete_single_document",
    "handle_greeting",
    "handle_consultative_chat",
    "handle_out_of_domain",
    "handle_explain_capabilities",
]

