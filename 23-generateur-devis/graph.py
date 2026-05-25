import time
import re
import json
from typing import TypedDict, Optional
from datetime import datetime, timezone, timedelta

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from supabase import create_client
from fpdf import FPDF

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=2048,
)

# ─── State ───────────────────────────────────────────────────────────────────
class QuoteState(TypedDict):
    client_name:         str
    client_email:        str
    client_company:      str
    project_description: str
    budget_range:        str
    line_items:          Optional[list]
    total_ht:            Optional[float]
    total_tva:           Optional[float]
    total_ttc:           Optional[float]
    quote_number:        Optional[str]
    validity_date:       Optional[str]
    pdf_bytes:           Optional[bytes]
    quote_id:            Optional[str]
    errors:              list
    status:              str

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

def _generate_quote_number() -> str:
    now = datetime.now()
    return f"DEV-{now.year}{now.month:02d}-{now.microsecond % 1000:03d}"

def _parse_json_array(text: str) -> list:
    """Extrait et parse un tableau JSON depuis une réponse LLM."""
    text = text.strip().replace("```json", "").replace("```", "").strip()
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    raise ValueError("Tableau JSON introuvable dans la réponse")

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def generate_line_items(state: QuoteState) -> QuoteState:
    """Génère les lignes du devis via LLM."""
    try:
        prompt = f"""Tu es un expert en chiffrage de projets. Génère un devis détaillé.

Client : {state['client_name']} ({state['client_company']})
Description du projet : {state['project_description']}
Budget indicatif : {state['budget_range']}

Génère des lignes de devis réalistes et professionnelles.

Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant ou après :
[
  {{
    "description": "description de la prestation",
    "quantity": 1,
    "unit": "forfait",
    "unit_price": 1500.00,
    "total": 1500.00
  }}
]

Contraintes :
- 3 à 7 lignes maximum
- Prix cohérents avec le marché français
- Unités : forfait, jour, heure, unité
- Total cohérent avec le budget indicatif
"""
        response   = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        line_items = _parse_json_array(response.content)

        total_ht  = sum(item["total"] for item in line_items)
        total_tva = round(total_ht * config.TVA_RATE / 100, 2)
        total_ttc = round(total_ht + total_tva, 2)

        quote_number  = _generate_quote_number()
        validity_date = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")

        return {
            **state,
            "line_items":    line_items,
            "total_ht":      round(total_ht, 2),
            "total_tva":     total_tva,
            "total_ttc":     total_ttc,
            "quote_number":  quote_number,
            "validity_date": validity_date,
            "status":        "items_generated",
        }

    except Exception as e:
        return {**state, "errors": [f"Génération lignes devis : {e}"], "status": "error"}


def generate_pdf(state: QuoteState) -> QuoteState:
    """Génère le PDF du devis."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ── En-tête ──────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, "DEVIS", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"N deg {state['quote_number']}", ln=True, align="C")
        pdf.cell(0, 6, f"Date : {datetime.now().strftime('%d/%m/%Y')} | Valide jusqu au : {state['validity_date']}", ln=True, align="C")
        pdf.ln(8)

        # ── Infos entreprise & client ─────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(95, 6, "PRESTATAIRE", ln=False)
        pdf.cell(95, 6, "CLIENT", ln=True)

        pdf.set_font("Helvetica", "", 10)
        pdf.cell(95, 5, config.COMPANY_NAME, ln=False)
        pdf.cell(95, 5, state["client_name"], ln=True)
        pdf.cell(95, 5, config.COMPANY_ADDRESS, ln=False)
        pdf.cell(95, 5, state["client_company"], ln=True)
        pdf.cell(95, 5, f"SIRET : {config.COMPANY_SIRET}", ln=False)
        pdf.cell(95, 5, state["client_email"], ln=True)
        pdf.ln(8)

        # ── Tableau lignes ────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(90, 7, "Description", border=1, fill=True)
        pdf.cell(20, 7, "Qte", border=1, fill=True, align="C")
        pdf.cell(20, 7, "Unite", border=1, fill=True, align="C")
        pdf.cell(30, 7, "P.U. HT", border=1, fill=True, align="R")
        pdf.cell(30, 7, "Total HT", border=1, fill=True, align="R", ln=True)

        pdf.set_font("Helvetica", "", 9)
        for item in state["line_items"]:
            desc = item["description"][:55]
            pdf.cell(90, 6, desc, border=1)
            pdf.cell(20, 6, str(item["quantity"]), border=1, align="C")
            pdf.cell(20, 6, item.get("unit", "forfait"), border=1, align="C")
            pdf.cell(30, 6, f"{item['unit_price']:,.2f} {config.CURRENCY}", border=1, align="R")
            pdf.cell(30, 6, f"{item['total']:,.2f} {config.CURRENCY}", border=1, align="R", ln=True)

        pdf.ln(4)

        # ── Totaux ────────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(160, 6, "Total HT", align="R")
        pdf.cell(30, 6, f"{state['total_ht']:,.2f} {config.CURRENCY}", border=1, align="R", ln=True)
        pdf.cell(160, 6, f"TVA ({config.TVA_RATE}%)", align="R")
        pdf.cell(30, 6, f"{state['total_tva']:,.2f} {config.CURRENCY}", border=1, align="R", ln=True)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(160, 8, "TOTAL TTC", align="R")
        pdf.cell(30, 8, f"{state['total_ttc']:,.2f} {config.CURRENCY}", border=1, align="R", ln=True)

        pdf.ln(8)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5, f"Conditions de paiement : {config.PAYMENT_TERMS} jours a reception de facture. Devis valable 30 jours.")

        pdf_bytes = bytes(pdf.output())
        return {**state, "pdf_bytes": pdf_bytes, "status": "pdf_generated"}

    except Exception as e:
        return {**state, "errors": [f"Génération PDF : {e}"], "status": "error"}


def save_to_supabase(state: QuoteState) -> QuoteState:
    """Enregistre le devis dans Supabase."""
    try:
        result = _supabase().table(config.SUPABASE_TABLE).insert({
            "quote_number":        state["quote_number"],
            "client_name":         state["client_name"],
            "client_email":        state["client_email"],
            "client_company":      state["client_company"],
            "project_description": state["project_description"],
            "total_ht":            state["total_ht"],
            "total_tva":           state["total_tva"],
            "total_ttc":           state["total_ttc"],
            "validity_date":       state["validity_date"],
            "status":              "envoye",
            "created_at":          _now(),
        }).execute()

        quote_id = result.data[0]["id"]
        return {**state, "quote_id": quote_id, "status": "completed"}

    except Exception as e:
        return {**state, "status": "completed", "errors": state["errors"] + [f"Supabase (non bloquant) : {e}"]}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(QuoteState)

    g.add_node("generate_line_items", generate_line_items)
    g.add_node("generate_pdf",        generate_pdf)
    g.add_node("save_to_supabase",    save_to_supabase)

    g.set_entry_point("generate_line_items")

    g.add_conditional_edges("generate_line_items", _stop_on_error("generate_pdf"))
    g.add_conditional_edges("generate_pdf",        _stop_on_error("save_to_supabase"))
    g.add_edge("save_to_supabase", END)

    return g.compile()


def run_quote(client_name: str, client_email: str, client_company: str,
              project_description: str, budget_range: str) -> QuoteState:
    initial_state = QuoteState(
        client_name         = client_name,
        client_email        = client_email,
        client_company      = client_company,
        project_description = project_description,
        budget_range        = budget_range,
        line_items          = None,
        total_ht            = None,
        total_tva           = None,
        total_ttc           = None,
        quote_number        = None,
        validity_date       = None,
        pdf_bytes           = None,
        quote_id            = None,
        errors              = [],
        status              = "pending",
    )
    return build_graph().invoke(initial_state)