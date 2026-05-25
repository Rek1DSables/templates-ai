import time
import json
from typing import TypedDict, Optional
from datetime import datetime, timezone

import fitz  # PyMuPDF
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from supabase import create_client

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=1024,
)

# ─── State ───────────────────────────────────────────────────────────────────
class InvoiceState(TypedDict):
    # Input
    file_bytes: bytes
    file_name:  str

    # Runtime
    raw_text:        Optional[str]
    extracted_data:  Optional[dict]
    validated_data:  Optional[dict]
    invoice_id:      Optional[str]

    # Suivi
    errors: list
    status: str  # pending | extracted | validated | saved | completed | error

# ─── Helpers ─────────────────────────────────────────────────────────────────
def invoke_with_retry(chain, input_data):
    for attempt in range(config.MAX_RETRIES):
        try:
            return chain.invoke(input_data)
        except Exception as e:
            if "overloaded" in str(e).lower() and attempt < config.MAX_RETRIES - 1:
                time.sleep(config.RETRY_DELAY)
                continue
            raise

def _supabase():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def _now():
    return datetime.now(timezone.utc).isoformat()

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def extract_text(state: InvoiceState) -> InvoiceState:
    """Extrait le texte de la facture PDF."""
    try:
        doc  = fitz.open(stream=state["file_bytes"], filetype="pdf")
        text = "".join([page.get_text() for page in doc])

        if not text.strip():
            return {**state, "errors": ["PDF vide ou illisible."], "status": "error"}

        return {**state, "raw_text": text}

    except Exception as e:
        return {**state, "errors": [f"Extraction PDF : {e}"], "status": "error"}


def extract_invoice_data(state: InvoiceState) -> InvoiceState:
    """Extrait les données structurées de la facture via LLM."""
    try:
        prompt = f"""Tu es un expert comptable. Extrais les données de cette facture.

FACTURE :
{state['raw_text'][:3000]}

Réponds UNIQUEMENT avec un JSON valide, sans texte autour :
{{
    "supplier_name": "nom du fournisseur",
    "supplier_siret": "numéro SIRET si présent, sinon null",
    "invoice_number": "numéro de facture",
    "invoice_date": "date au format YYYY-MM-DD",
    "due_date": "date d'échéance au format YYYY-MM-DD si présente, sinon null",
    "amount_ht": montant hors taxes en float,
    "tva_rate": taux de TVA en float (ex: 20.0),
    "tva_amount": montant TVA en float,
    "amount_ttc": montant TTC en float,
    "description": "description courte des biens ou services facturés",
    "category": "catégorie parmi : {', '.join(config.EXPENSE_CATEGORIES)}"
}}
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])

        # Nettoyage et parsing JSON
        content = response.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        data    = json.loads(content)

        return {**state, "extracted_data": data, "status": "extracted"}

    except Exception as e:
        return {**state, "errors": [f"Extraction données facture : {e}"], "status": "error"}


def validate_data(state: InvoiceState) -> InvoiceState:
    """Valide et corrige les données extraites."""
    try:
        data   = state["extracted_data"]
        errors = []

        # Champs obligatoires
        if not data.get("supplier_name"):
            errors.append("Fournisseur non identifié.")
        if not data.get("amount_ttc") or data["amount_ttc"] <= 0:
            errors.append("Montant TTC invalide ou manquant.")
        if not data.get("invoice_date"):
            errors.append("Date de facture manquante.")

        # Cohérence montants
        if data.get("amount_ht") and data.get("tva_amount") and data.get("amount_ttc"):
            expected_ttc = round(data["amount_ht"] + data["tva_amount"], 2)
            actual_ttc   = round(data["amount_ttc"], 2)
            if abs(expected_ttc - actual_ttc) > 0.10:
                errors.append(f"Incohérence montants : HT({data['amount_ht']}) + TVA({data['tva_amount']}) ≠ TTC({data['amount_ttc']})")

        if errors:
            return {**state, "errors": errors, "status": "error"}

        return {**state, "validated_data": data, "status": "validated"}

    except Exception as e:
        return {**state, "errors": [f"Validation : {e}"], "status": "error"}


def save_to_supabase(state: InvoiceState) -> InvoiceState:
    """Enregistre la facture validée dans Supabase."""
    try:
        data   = state["validated_data"]
        result = _supabase().table(config.SUPABASE_TABLE).insert({
            "supplier_name":   data.get("supplier_name"),
            "supplier_siret":  data.get("supplier_siret"),
            "invoice_number":  data.get("invoice_number"),
            "invoice_date":    data.get("invoice_date"),
            "due_date":        data.get("due_date"),
            "amount_ht":       data.get("amount_ht"),
            "tva_rate":        data.get("tva_rate"),
            "tva_amount":      data.get("tva_amount"),
            "amount_ttc":      data.get("amount_ttc"),
            "description":     data.get("description"),
            "category":        data.get("category"),
            "file_name":       state["file_name"],
            "created_at":      _now(),
        }).execute()

        invoice_id = result.data[0]["id"]
        return {**state, "invoice_id": invoice_id, "status": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Supabase (save) : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(InvoiceState)

    g.add_node("extract_text",         extract_text)
    g.add_node("extract_invoice_data", extract_invoice_data)
    g.add_node("validate_data",        validate_data)
    g.add_node("save_to_supabase",     save_to_supabase)

    g.set_entry_point("extract_text")

    g.add_conditional_edges("extract_text",         _stop_on_error("extract_invoice_data"))
    g.add_conditional_edges("extract_invoice_data", _stop_on_error("validate_data"))
    g.add_conditional_edges("validate_data",        _stop_on_error("save_to_supabase"))
    g.add_edge("save_to_supabase", END)

    return g.compile()


def run_invoice(file_bytes: bytes, file_name: str) -> InvoiceState:
    initial_state = InvoiceState(
        file_bytes     = file_bytes,
        file_name      = file_name,
        raw_text       = None,
        extracted_data = None,
        validated_data = None,
        invoice_id     = None,
        errors         = [],
        status         = "pending",
    )
    return build_graph().invoke(initial_state)