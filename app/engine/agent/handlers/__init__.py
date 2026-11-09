"""
Handlers Package for ResilioAI Conversational Agent.
"""

from app.engine.agent.handlers.planning_handler import (
    handle_approval,
    handle_procurement_planning,
    handle_revision,
)
from app.engine.agent.handlers.supplier_handler import (
    handle_crud_confirmation,
    handle_list_suppliers,
    handle_supplier_management,
)
from app.engine.agent.handlers.incident_handler import (
    handle_clarification_confirmed,
    handle_incident_report,
)
from app.engine.agent.handlers.doc_handler import (
    handle_clear_documents,
    handle_delete_single_document,
    handle_get_inventory,
)
from app.engine.agent.handlers.general_handler import (
    handle_consultative_chat,
    handle_explain_capabilities,
    handle_greeting,
    handle_out_of_domain,
)

__all__ = [
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

