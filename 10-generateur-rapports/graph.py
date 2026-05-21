import time
import io
from typing import TypedDict, Optional

import pandas as pd
from fpdf import FPDF
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=2048,
)

# ─── State ───────────────────────────────────────────────────────────────────
class ReportState(TypedDict):
    # Input
    file_bytes:  bytes
    file_name:   str
    context:     str   # contexte métier fourni par l'utilisateur

    # Runtime
    df:               Optional[object]   # DataFrame pandas
    stats_summary:    Optional[str]
    interpretation:   Optional[str]
    recommendations:  Optional[str]
    pdf_bytes:        Optional[bytes]

    # Suivi
    errors: list
    status: str  # pending | loaded | analysed | interpreted | completed | error

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

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def load_file(state: ReportState) -> ReportState:
    """Charge le fichier CSV ou Excel en DataFrame pandas."""
    try:
        file_bytes = state["file_bytes"]
        file_name  = state["file_name"]

        if file_name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif file_name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            return {**state, "errors": ["Format non supporté. Utilisez CSV ou Excel."], "status": "error"}

        if df.empty:
            return {**state, "errors": ["Le fichier est vide."], "status": "error"}

        return {**state, "df": df, "status": "loaded"}

    except Exception as e:
        return {**state, "errors": [f"Chargement fichier : {e}"], "status": "error"}


def compute_stats(state: ReportState) -> ReportState:
    """Calcule les statistiques descriptives du DataFrame."""
    try:
        df = state["df"]

        lines = []
        lines.append(f"Nombre de lignes : {len(df)}")
        lines.append(f"Nombre de colonnes : {len(df.columns)}")
        lines.append(f"Colonnes : {', '.join(df.columns.tolist())}")
        lines.append("")

        # Statistiques numériques
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            lines.append("=== Statistiques numériques ===")
            stats = df[numeric_cols].describe().round(2)
            lines.append(stats.to_string())
            lines.append("")

        # Aperçu des données
        lines.append("=== Aperçu des données (premières lignes) ===")
        lines.append(df.head(config.MAX_ROWS_PREVIEW).to_string())

        stats_summary = "\n".join(lines)
        return {**state, "stats_summary": stats_summary}

    except Exception as e:
        return {**state, "errors": [f"Calcul statistiques : {e}"], "status": "error"}


def interpret_data(state: ReportState) -> ReportState:
    """Interprète les données et identifie les insights clés."""
    try:
        prompt = f"""Tu es un analyste de données expert. Analyse ces données et identifie les insights clés.

CONTEXTE MÉTIER :
{state['context'] or 'Non renseigné'}

STATISTIQUES :
{state['stats_summary']}

Fournis :
1. Une description claire de ce que représentent ces données
2. Les tendances principales observées
3. Les anomalies ou points d'attention
4. Les chiffres clés à retenir

Réponds en français, de manière structurée et professionnelle.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "interpretation": response.content, "status": "analysed"}

    except Exception as e:
        return {**state, "errors": [f"Interprétation données : {e}"], "status": "error"}


def generate_recommendations(state: ReportState) -> ReportState:
    """Génère des recommandations actionnables."""
    try:
        prompt = f"""Sur la base de cette analyse de données, génère des recommandations concrètes.

CONTEXTE MÉTIER :
{state['context'] or 'Non renseigné'}

ANALYSE :
{state['interpretation']}

Fournis 3 à 5 recommandations :
- Chaque recommandation doit être concrète et actionnable
- Indique la priorité (Haute / Moyenne / Faible)
- Explique l'impact attendu

Réponds en français, format structuré.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "recommendations": response.content}

    except Exception as e:
        return {**state, "errors": [f"Génération recommandations : {e}"], "status": "error"}


def generate_pdf(state: ReportState) -> ReportState:
    """Génère le rapport PDF final."""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # ── En-tête ──────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 12, config.REPORT_TITLE, ln=True, align="C")

        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, config.COMPANY_NAME, ln=True, align="C")
        pdf.cell(0, 8, f"Fichier analysé : {state['file_name']}", ln=True, align="C")
        pdf.ln(8)

        # ── Contexte métier ───────────────────────────────────────────────────
        if state["context"]:
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Contexte", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, state["context"])
            pdf.ln(4)

        # ── Statistiques ──────────────────────────────────────────────────────
        df = state["df"]
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Apercu des donnees", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, f"Lignes : {len(df)}  |  Colonnes : {len(df.columns)}  |  Colonnes : {', '.join(df.columns.tolist())}")
        pdf.ln(4)

        # ── Analyse ───────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Analyse et insights", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, state["interpretation"].encode("latin-1", "replace").decode("latin-1"))
        pdf.ln(4)

        # ── Recommandations ───────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Recommandations", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, state["recommendations"].encode("latin-1", "replace").decode("latin-1"))
        pdf.ln(4)

        # ── Footer ────────────────────────────────────────────────────────────
        pdf.set_y(-20)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 8, f"Rapport genere automatiquement par {config.REPORT_AUTHOR}", align="C")

        pdf_bytes = bytes(pdf.output())
        return {**state, "pdf_bytes": pdf_bytes, "status": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Génération PDF : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(ReportState)

    g.add_node("load_file",               load_file)
    g.add_node("compute_stats",           compute_stats)
    g.add_node("interpret_data",          interpret_data)
    g.add_node("generate_recommendations", generate_recommendations)
    g.add_node("generate_pdf",            generate_pdf)

    g.set_entry_point("load_file")

    g.add_conditional_edges("load_file",               _stop_on_error("compute_stats"))
    g.add_conditional_edges("compute_stats",           _stop_on_error("interpret_data"))
    g.add_conditional_edges("interpret_data",          _stop_on_error("generate_recommendations"))
    g.add_conditional_edges("generate_recommendations", _stop_on_error("generate_pdf"))
    g.add_edge("generate_pdf", END)

    return g.compile()


def run_report(file_bytes: bytes, file_name: str, context: str) -> ReportState:
    initial_state = ReportState(
        file_bytes       = file_bytes,
        file_name        = file_name,
        context          = context,
        df               = None,
        stats_summary    = None,
        interpretation   = None,
        recommendations  = None,
        pdf_bytes        = None,
        errors           = [],
        status           = "pending",
    )
    return build_graph().invoke(initial_state)