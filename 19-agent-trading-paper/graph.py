# graph.py
import time
import anthropic
import pandas as pd
import numpy as np
import yfinance as yf
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from config import (
    MODEL_NAME, ANTHROPIC_API_KEY,
    CAPITAL_INITIAL, MAX_RETRIES, RETRY_DELAY
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class TradingState(TypedDict):
    actif: str
    strategie: str
    periode: str
    capital_initial: float
    prix: Optional[pd.DataFrame]
    signaux: Optional[pd.DataFrame]
    portefeuille: Optional[pd.DataFrame]
    performance: dict
    analyse: str
    erreur: str


def invoke_with_retry(messages: list, system: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=1500,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.APIStatusError as e:
            if "overloaded" in str(e).lower() and attempt < MAX_RETRIES - 1:
                print(f"[Retry {attempt + 1}/{MAX_RETRIES}] Modele surcharge, attente {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def recuperer_donnees(state: TradingState) -> TradingState:
    try:
        ticker = state["actif"]
        if ticker == "SP500":
            ticker = "^GSPC"

        data = yf.download(ticker, period=state["periode"], auto_adjust=True, progress=False)

        if data.empty:
            return {**state, "erreur": f"Aucune donnee trouvee pour {state['actif']}"}

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data[["Open", "High", "Low", "Close", "Volume"]].copy()
        data.index = pd.to_datetime(data.index)
        data = data.dropna()

        return {**state, "prix": data, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur recuperation donnees : {str(e)}"}


def calculer_signaux(state: TradingState) -> TradingState:
    try:
        df = state["prix"].copy()
        strategie = state["strategie"]

        if strategie == "Moyenne Mobile":
            df["MA_court"] = df["Close"].rolling(window=10).mean()
            df["MA_long"] = df["Close"].rolling(window=30).mean()
            df["signal"] = 0
            df.loc[df["MA_court"] > df["MA_long"], "signal"] = 1
            df.loc[df["MA_court"] < df["MA_long"], "signal"] = -1

        elif strategie == "RSI":
            delta = df["Close"].diff()
            gain = delta.clip(lower=0).rolling(window=14).mean()
            perte = (-delta.clip(upper=0)).rolling(window=14).mean()
            rs = gain / perte.replace(0, np.nan)
            df["RSI"] = 100 - (100 / (1 + rs))
            df["signal"] = 0
            df.loc[df["RSI"] < 30, "signal"] = 1
            df.loc[df["RSI"] > 70, "signal"] = -1

        elif strategie == "Momentum":
            df["momentum"] = df["Close"].pct_change(periods=10)
            df["signal"] = 0
            df.loc[df["momentum"] > 0.02, "signal"] = 1
            df.loc[df["momentum"] < -0.02, "signal"] = -1

        df = df.dropna()
        return {**state, "signaux": df, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur calcul signaux : {str(e)}"}


def simuler_portefeuille(state: TradingState) -> TradingState:
    try:
        df = state["signaux"].copy()
        capital = state["capital_initial"]
        position = 0
        cash = capital
        valeur_portefeuille = []
        trades = []

        for i, (date, row) in enumerate(df.iterrows()):
            prix = float(row["Close"])
            signal = int(row["signal"])

            if signal == 1 and position == 0 and cash > 0:
                position = cash / prix
                cash = 0
                trades.append({"date": date, "type": "ACHAT", "prix": prix, "quantite": position})

            elif signal == -1 and position > 0:
                cash = position * prix
                trades.append({"date": date, "type": "VENTE", "prix": prix, "quantite": position})
                position = 0

            valeur_totale = cash + position * prix
            valeur_portefeuille.append(valeur_totale)

        if position > 0:
            prix_final = float(df["Close"].iloc[-1])
            cash = position * prix_final
            position = 0

        valeur_finale = cash
        rendement = ((valeur_finale - capital) / capital) * 100
        nb_trades = len(trades)

        prix_buy_hold_debut = float(df["Close"].iloc[0])
        prix_buy_hold_fin = float(df["Close"].iloc[-1])
        rendement_buy_hold = ((prix_buy_hold_fin - prix_buy_hold_debut) / prix_buy_hold_debut) * 100

        df["valeur_portefeuille"] = valeur_portefeuille

        performance = {
            "capital_initial": capital,
            "valeur_finale": round(valeur_finale, 2),
            "rendement": round(rendement, 2),
            "rendement_buy_hold": round(rendement_buy_hold, 2),
            "nb_trades": nb_trades,
            "trades": trades,
        }

        return {**state, "portefeuille": df, "performance": performance, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur simulation : {str(e)}"}


def generer_analyse(state: TradingState) -> TradingState:
    try:
        perf = state["performance"]
        system = (
            "Tu es un analyste financier expert en trading algorithmique. "
            "Tu analyses les performances de strategies de trading paper et fournis des insights concrets. "
            "Tu reponds toujours en francais."
        )
        prompt = f"""Analyse les resultats de cette simulation de trading paper :

Actif : {state['actif']}
Strategie : {state['strategie']}
Periode : {state['periode']}
Capital initial : {perf['capital_initial']} USD
Valeur finale : {perf['valeur_finale']} USD
Rendement strategie : {perf['rendement']}%
Rendement Buy & Hold : {perf['rendement_buy_hold']}%
Nombre de trades : {perf['nb_trades']}

Fournis une analyse en 4 parties :
1. PERFORMANCE GLOBALE : evaluation du rendement obtenu
2. COMPARAISON BUY & HOLD : la strategie bat-elle le marche ?
3. ANALYSE DE LA STRATEGIE : forces et faiblesses observees
4. RECOMMANDATIONS : comment ameliorer cette strategie"""

        analyse = invoke_with_retry(
            messages=[{"role": "user", "content": prompt}],
            system=system,
        )
        return {**state, "analyse": analyse, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur analyse : {str(e)}"}


def build_graph():
    graph = StateGraph(TradingState)
    graph.add_node("recuperer_donnees", recuperer_donnees)
    graph.add_node("calculer_signaux", calculer_signaux)
    graph.add_node("simuler_portefeuille", simuler_portefeuille)
    graph.add_node("generer_analyse", generer_analyse)

    graph.set_entry_point("recuperer_donnees")
    graph.add_edge("recuperer_donnees", "calculer_signaux")
    graph.add_edge("calculer_signaux", "simuler_portefeuille")
    graph.add_edge("simuler_portefeuille", "generer_analyse")
    graph.add_edge("generer_analyse", END)

    return graph.compile()