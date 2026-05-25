import time
import io
from typing import TypedDict, Optional
from datetime import datetime, timezone

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
class AnalyticsState(TypedDict):
    # Input
    file_bytes:  bytes
    file_name:   str
    period:      str
    kpis:        list   # KPIs sélectionnés par l'utilisateur

    # Runtime
    df:               Optional[object]
    stats:            Optional[dict]
    trends:           Optional[dict]
    insights:         Optional[str]
    recommendations:  Optional[str]

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
def load_data(state: AnalyticsState) -> AnalyticsState:
    """Charge le fichier CSV ou Excel."""
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

        # Détection automatique colonne date
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass

        return {**state, "df": df, "status": "loaded"}

    except Exception as e:
        return {**state, "errors": [f"Chargement : {e}"], "status": "error"}


def compute_stats(state: AnalyticsState) -> AnalyticsState:
    """Calcule les statistiques et KPIs."""
    try:
        df    = state["df"]
        stats = {}

        # Stats globales
        stats["rows"]    = len(df)
        stats["columns"] = len(df.columns)
        stats["columns_list"] = df.columns.tolist()

        # Stats numériques
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        stats["numeric"] = {}

        for col in numeric_cols:
            stats["numeric"][col] = {
                "sum":    round(df[col].sum(), 2),
                "mean":   round(df[col].mean(), 2),
                "max":    round(df[col].max(), 2),
                "min":    round(df[col].min(), 2),
                "median": round(df[col].median(), 2),
            }

        # Détection tendances (si colonne date présente)
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
        trends = {}

        if date_cols and numeric_cols:
            date_col = date_cols[0]
            df_sorted = df.sort_values(date_col)

            for num_col in numeric_cols[:3]:
                mid = len(df_sorted) // 2
                first_half  = df_sorted[num_col].iloc[:mid].mean()
                second_half = df_sorted[num_col].iloc[mid:].mean()
                trend_pct   = round((second_half - first_half) / first_half * 100, 1) if first_half != 0 else 0
                trends[num_col] = {
                    "trend_pct": trend_pct,
                    "direction": "↑" if trend_pct > 0 else "↓" if trend_pct < 0 else "→",
                }

        return {**state, "stats": stats, "trends": trends}

    except Exception as e:
        return {**state, "errors": [f"Calcul stats : {e}"], "status": "error"}


def generate_insights(state: AnalyticsState) -> AnalyticsState:
    """Génère des insights IA sur les données."""
    try:
        stats = state["stats"]
        trends = state["trends"]

        numeric_text = "\n".join([
            f"- {col} : total={v['sum']}, moyenne={v['mean']}, max={v['max']}, min={v['min']}"
            for col, v in stats.get("numeric", {}).items()
        ])

        trends_text = "\n".join([
            f"- {col} : {v['direction']} {v['trend_pct']:+.1f}%"
            for col, v in trends.items()
        ]) if trends else "Pas de données temporelles"

        prompt = f"""Tu es un analyste data expert. Analyse ces données et génère des insights actionnables.

FICHIER : {state['file_name']}
PÉRIODE : {state['period']}
LIGNES : {stats['rows']} | COLONNES : {stats['columns']}

MÉTRIQUES CLÉS :
{numeric_text}

TENDANCES :
{trends_text}

Fournis :
1. Les 3 insights les plus importants
2. Les anomalies ou points d'attention
3. Les opportunités identifiées
4. Le contexte business probable de ces données

Français, concis, orienté business.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "insights": response.content, "status": "analysed"}

    except Exception as e:
        return {**state, "errors": [f"Insights : {e}"], "status": "error"}


def generate_recommendations(state: AnalyticsState) -> AnalyticsState:
    """Génère des recommandations basées sur les insights."""
    try:
        prompt = f"""Sur la base de cette analyse de données, génère des recommandations stratégiques.

INSIGHTS :
{state['insights']}

Fournis 3 à 5 recommandations :
- Concrètes et actionnables
- Avec priorité (Haute / Moyenne / Faible)
- Avec impact attendu estimé
- Avec délai de mise en œuvre suggéré

Français, professionnel, orienté décision.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "recommendations": response.content, "status": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Recommandations : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(AnalyticsState)

    g.add_node("load_data",               load_data)
    g.add_node("compute_stats",           compute_stats)
    g.add_node("generate_insights",       generate_insights)
    g.add_node("generate_recommendations", generate_recommendations)

    g.set_entry_point("load_data")

    g.add_conditional_edges("load_data",               _stop_on_error("compute_stats"))
    g.add_conditional_edges("compute_stats",           _stop_on_error("generate_insights"))
    g.add_conditional_edges("generate_insights",       _stop_on_error("generate_recommendations"))
    g.add_edge("generate_recommendations", END)

    return g.compile()


def run_analytics(file_bytes: bytes, file_name: str, period: str, kpis: list) -> AnalyticsState:
    initial_state = AnalyticsState(
        file_bytes      = file_bytes,
        file_name       = file_name,
        period          = period,
        kpis            = kpis,
        df              = None,
        stats           = None,
        trends          = None,
        insights        = None,
        recommendations = None,
        errors          = [],
        status          = "pending",
    )
    return build_graph().invoke(initial_state)