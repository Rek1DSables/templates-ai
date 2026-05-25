import time
from typing import TypedDict, Optional

import pandas as pd
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
class FinancialState(TypedDict):
    # Input
    company_name:   str
    sector:         str
    financials:     dict   # données financières brutes saisies par l'utilisateur

    # Runtime
    ratios:         Optional[dict]
    comparison:     Optional[dict]
    interpretation: Optional[str]
    recommendation: Optional[str]

    # Suivi
    errors: list
    status: str

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
def validate_input(state: FinancialState) -> FinancialState:
    """Valide les données financières saisies."""
    errors = []
    f = state["financials"]

    required = ["revenue", "gross_profit", "net_income", "total_assets",
                "total_equity", "total_debt", "current_assets", "current_liabilities"]

    for field in required:
        if f.get(field) is None:
            errors.append(f"Champ manquant : {field}")
        elif f.get(field, 0) < 0:
            errors.append(f"Valeur négative non autorisée : {field}")

    if errors:
        return {**state, "errors": errors, "status": "error"}
    return {**state, "errors": [], "status": "pending"}


def calculate_ratios(state: FinancialState) -> FinancialState:
    """Calcule les ratios financiers clés."""
    try:
        f = state["financials"]

        # Protection division par zéro
        def safe_div(a, b):
            return round(a / b, 4) if b and b != 0 else None

        ratios = {
            # Rentabilité
            "gross_margin":   safe_div(f["gross_profit"], f["revenue"]),
            "net_margin":     safe_div(f["net_income"], f["revenue"]),
            "roe":            safe_div(f["net_income"], f["total_equity"]),
            "roa":            safe_div(f["net_income"], f["total_assets"]),

            # Structure financière
            "debt_to_equity": safe_div(f["total_debt"], f["total_equity"]),
            "debt_ratio":     safe_div(f["total_debt"], f["total_assets"]),

            # Liquidité
            "current_ratio":  safe_div(f["current_assets"], f["current_liabilities"]),

            # Valorisation
            "pe_ratio":       safe_div(f.get("market_cap", 0), f["net_income"]) if f.get("market_cap") else None,
        }

        return {**state, "ratios": ratios, "status": "ratios_calculated"}

    except Exception as e:
        return {**state, "errors": [f"Calcul ratios : {e}"], "status": "error"}


def compare_to_benchmark(state: FinancialState) -> FinancialState:
    """Compare les ratios aux benchmarks sectoriels."""
    try:
        benchmark = config.SECTOR_BENCHMARKS.get(state["sector"], {})
        ratios    = state["ratios"]

        comparison = {}
        for key, bench_value in benchmark.items():
            company_value = ratios.get(key)
            if company_value is not None:
                diff_pct = round((company_value - bench_value) / bench_value * 100, 1)
                comparison[key] = {
                    "company":   company_value,
                    "benchmark": bench_value,
                    "diff_pct":  diff_pct,
                    "signal":    "✅" if diff_pct >= 0 else "⚠️",
                }

        return {**state, "comparison": comparison}

    except Exception as e:
        return {**state, "errors": [f"Comparaison benchmark : {e}"], "status": "error"}


def interpret_results(state: FinancialState) -> FinancialState:
    """Génère une interprétation IA des ratios et de la comparaison."""
    try:
        ratios_text = "\n".join([
            f"- {k} : {v}" for k, v in state["ratios"].items() if v is not None
        ])

        comparison_text = "\n".join([
            f"- {k} : entreprise={v['company']} vs benchmark={v['benchmark']} ({v['diff_pct']:+.1f}%) {v['signal']}"
            for k, v in state["comparison"].items()
        ])

        prompt = f"""Tu es un analyste financier expert. Analyse ces données financières.

ENTREPRISE : {state['company_name']}
SECTEUR : {state['sector']}

RATIOS CALCULÉS :
{ratios_text}

COMPARAISON AUX BENCHMARKS SECTORIELS :
{comparison_text}

Fournis une analyse détaillée :
1. Points forts financiers
2. Points de vigilance
3. Position concurrentielle vs le secteur
4. Risques identifiés
5. Opportunités

Réponds en français, ton professionnel, accessible à un dirigeant non-financier.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "interpretation": response.content}

    except Exception as e:
        return {**state, "errors": [f"Interprétation : {e}"], "status": "error"}


def generate_recommendation(state: FinancialState) -> FinancialState:
    """Génère une recommandation d'investissement finale."""
    try:
        prompt = f"""Sur la base de cette analyse financière, génère une synthèse d'investissement.

ENTREPRISE : {state['company_name']}
SECTEUR : {state['sector']}

ANALYSE :
{state['interpretation']}

Fournis :
1. Verdict global : Acheter | Conserver | Vendre | À surveiller
2. Justification en 3-4 phrases
3. Catalyseurs positifs à surveiller (2-3 points)
4. Risques principaux (2-3 points)
5. Horizon d'investissement recommandé

Réponds en français, concis et professionnel.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "recommendation": response.content, "status": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Recommandation : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(FinancialState)

    g.add_node("validate_input",         validate_input)
    g.add_node("calculate_ratios",       calculate_ratios)
    g.add_node("compare_to_benchmark",   compare_to_benchmark)
    g.add_node("interpret_results",      interpret_results)
    g.add_node("generate_recommendation", generate_recommendation)

    g.set_entry_point("validate_input")

    g.add_conditional_edges("validate_input",         _stop_on_error("calculate_ratios"))
    g.add_conditional_edges("calculate_ratios",       _stop_on_error("compare_to_benchmark"))
    g.add_conditional_edges("compare_to_benchmark",   _stop_on_error("interpret_results"))
    g.add_conditional_edges("interpret_results",      _stop_on_error("generate_recommendation"))
    g.add_edge("generate_recommendation", END)

    return g.compile()


def run_analysis(company_name: str, sector: str, financials: dict) -> FinancialState:
    initial_state = FinancialState(
        company_name   = company_name,
        sector         = sector,
        financials     = financials,
        ratios         = None,
        comparison     = None,
        interpretation = None,
        recommendation = None,
        errors         = [],
        status         = "pending",
    )
    return build_graph().invoke(initial_state)