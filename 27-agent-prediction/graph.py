import time
import io
from typing import TypedDict, Optional

import numpy as np
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
class PredictionState(TypedDict):
    # Input
    file_bytes:   bytes
    file_name:    str
    target_col:   str
    date_col:     str
    model_type:   str
    forecast_periods: int

    # Runtime
    df:           Optional[object]
    df_forecast:  Optional[object]
    metrics:      Optional[dict]
    interpretation: Optional[str]
    recommendations: Optional[str]

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
def load_data(state: PredictionState) -> PredictionState:
    """Charge et prépare les données."""
    try:
        file_bytes = state["file_bytes"]
        file_name  = state["file_name"]

        if file_name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif file_name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            return {**state, "errors": ["Format non supporté."], "status": "error"}

        # Conversion date
        df[state["date_col"]] = pd.to_datetime(df[state["date_col"]])
        df = df.sort_values(state["date_col"]).reset_index(drop=True)

        # Vérification colonne cible
        if state["target_col"] not in df.columns:
            return {**state, "errors": [f"Colonne '{state['target_col']}' introuvable."], "status": "error"}

        return {**state, "df": df, "status": "loaded"}

    except Exception as e:
        return {**state, "errors": [f"Chargement : {e}"], "status": "error"}


def run_forecast(state: PredictionState) -> PredictionState:
    """Applique le modèle de prédiction sélectionné."""
    try:
        df         = state["df"]
        target_col = state["target_col"]
        date_col   = state["date_col"]
        n_periods  = state["forecast_periods"]
        model_type = state["model_type"]
        y          = df[target_col].values

        # Calcul de la fréquence temporelle
        date_diff = (df[date_col].iloc[1] - df[date_col].iloc[0])
        last_date = df[date_col].iloc[-1]
        future_dates = [last_date + date_diff * (i + 1) for i in range(n_periods)]

        # ── Modèles ───────────────────────────────────────────────────────────
        if model_type == "Moyenne mobile":
            window   = min(7, len(y) // 4)
            forecast = [np.mean(y[-window:])] * n_periods
            # IC basé sur std
            std      = np.std(y[-window:])
            lower    = [f - 1.96 * std for f in forecast]
            upper    = [f + 1.96 * std for f in forecast]

        elif model_type == "Régression linéaire":
            x      = np.arange(len(y))
            coeffs = np.polyfit(x, y, 1)
            x_future = np.arange(len(y), len(y) + n_periods)
            forecast = np.polyval(coeffs, x_future).tolist()
            residuals = y - np.polyval(coeffs, x)
            std       = np.std(residuals)
            lower     = [f - 1.96 * std for f in forecast]
            upper     = [f + 1.96 * std for f in forecast]

        else:  # Lissage exponentiel
            alpha    = 0.3
            smoothed = [y[0]]
            for val in y[1:]:
                smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])
            last_smooth = smoothed[-1]
            forecast    = [last_smooth] * n_periods
            std         = np.std(np.array(y) - np.array(smoothed[:len(y)]))
            lower       = [f - 1.96 * std for f in forecast]
            upper       = [f + 1.96 * std for f in forecast]

        # Métriques sur données historiques
        if model_type == "Régression linéaire":
            fitted   = np.polyval(coeffs, np.arange(len(y)))
        elif model_type == "Moyenne mobile":
            window   = min(7, len(y) // 4)
            fitted   = pd.Series(y).rolling(window, min_periods=1).mean().values
        else:
            fitted = np.array(smoothed)

        mae  = round(np.mean(np.abs(y - fitted[:len(y)])), 2)
        rmse = round(np.sqrt(np.mean((y - fitted[:len(y)]) ** 2)), 2)
        mape = round(np.mean(np.abs((y - fitted[:len(y)]) / (y + 1e-10))) * 100, 2)

        metrics = {
            "mae":  mae,
            "rmse": rmse,
            "mape": mape,
            "mean_historical": round(np.mean(y), 2),
            "trend": "↑ Hausse" if forecast[-1] > y[-1] else "↓ Baisse",
            "forecast_end": round(forecast[-1], 2),
        }

        # DataFrame prédictions
        df_forecast = pd.DataFrame({
            "date":     future_dates,
            "forecast": [round(f, 2) for f in forecast],
            "lower":    [round(l, 2) for l in lower],
            "upper":    [round(u, 2) for u in upper],
        })

        return {**state, "df_forecast": df_forecast, "metrics": metrics, "status": "forecasted"}

    except Exception as e:
        return {**state, "errors": [f"Prédiction : {e}"], "status": "error"}


def interpret_forecast(state: PredictionState) -> PredictionState:
    """Interprète les résultats de la prédiction via LLM."""
    try:
        metrics = state["metrics"]
        df_f    = state["df_forecast"]

        prompt = f"""Tu es un expert en data science et business intelligence. Analyse cette prédiction.

SÉRIE : {state['target_col']}
MODÈLE : {state['model_type']}
PÉRIODES PRÉDITES : {state['forecast_periods']}

MÉTRIQUES DU MODÈLE :
- MAE (erreur absolue moyenne) : {metrics['mae']}
- RMSE : {metrics['rmse']}
- MAPE (erreur relative) : {metrics['mape']}%
- Moyenne historique : {metrics['mean_historical']}
- Tendance prédite : {metrics['trend']}
- Valeur prédite fin de période : {metrics['forecast_end']}

PREMIÈRES PRÉDICTIONS :
{df_f.head(5).to_string()}

Fournis :
1. Fiabilité du modèle (interprétation des métriques)
2. Analyse de la tendance prédite
3. Facteurs de risque à surveiller
4. Implications business concrètes

Français, concis, orienté décision.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "interpretation": response.content, "status": "interpreted"}

    except Exception as e:
        return {**state, "errors": [f"Interprétation : {e}"], "status": "error"}


def generate_recommendations(state: PredictionState) -> PredictionState:
    """Génère des recommandations basées sur la prédiction."""
    try:
        prompt = f"""Sur la base de cette prédiction, génère des recommandations stratégiques.

TENDANCE : {state['metrics']['trend']}
INTERPRÉTATION : {state['interpretation']}

Génère 3 à 5 recommandations :
- Concrètes et actionnables
- Adaptées à la tendance prédite
- Avec horizon temporel
- Avec niveau de priorité

Français, professionnel.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "recommendations": response.content, "status": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Recommandations : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(PredictionState)

    g.add_node("load_data",               load_data)
    g.add_node("run_forecast",            run_forecast)
    g.add_node("interpret_forecast",      interpret_forecast)
    g.add_node("generate_recommendations", generate_recommendations)

    g.set_entry_point("load_data")

    g.add_conditional_edges("load_data",          _stop_on_error("run_forecast"))
    g.add_conditional_edges("run_forecast",        _stop_on_error("interpret_forecast"))
    g.add_conditional_edges("interpret_forecast",  _stop_on_error("generate_recommendations"))
    g.add_edge("generate_recommendations", END)

    return g.compile()


def run_prediction(file_bytes: bytes, file_name: str, target_col: str,
                   date_col: str, model_type: str, forecast_periods: int) -> PredictionState:
    initial_state = PredictionState(
        file_bytes       = file_bytes,
        file_name        = file_name,
        target_col       = target_col,
        date_col         = date_col,
        model_type       = model_type,
        forecast_periods = forecast_periods,
        df               = None,
        df_forecast      = None,
        metrics          = None,
        interpretation   = None,
        recommendations  = None,
        errors           = [],
        status           = "pending",
    )
    return build_graph().invoke(initial_state)