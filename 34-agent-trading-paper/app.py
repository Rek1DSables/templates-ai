# app.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from graph import build_graph
from config import CAPITAL_INITIAL, STRATEGIES, PERIODES, ACTIFS

# --- UI ---
st.set_page_config(page_title="Agent Trading Paper AI", page_icon="📈", layout="wide")
st.title("📈 Agent de Trading Paper AI")
st.caption("Simulation de strategies de trading algorithmique avec analyse Claude")

with st.sidebar:
    st.subheader("Parametres")
    actif = st.selectbox("Actif", ACTIFS)
    strategie = st.selectbox("Strategie", STRATEGIES)
    periode = st.selectbox("Periode", PERIODES)
    capital = st.number_input("Capital initial (USD)", value=CAPITAL_INITIAL, step=1000)
    lancer = st.button("Lancer la simulation", use_container_width=True)

if lancer:
    with st.spinner("Simulation en cours..."):
        try:
            graph = build_graph()
            result = graph.invoke({
                "actif": actif,
                "strategie": strategie,
                "periode": periode,
                "capital_initial": float(capital),
                "prix": None,
                "signaux": None,
                "portefeuille": None,
                "performance": {},
                "analyse": "",
                "erreur": "",
            })
        except Exception as e:
            st.error(f"Erreur graph : {e}")
            st.stop()

    if result["erreur"]:
        st.error(result["erreur"])
    else:
        perf = result["performance"]
        df = result["portefeuille"]

        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Capital initial", f"{perf['capital_initial']:,.0f} $")
        col2.metric("Valeur finale", f"{perf['valeur_finale']:,.0f} $")
        col3.metric(
            "Rendement strategie",
            f"{perf['rendement']}%",
            delta=f"{perf['rendement'] - perf['rendement_buy_hold']:.2f}% vs B&H"
        )
        col4.metric("Nombre de trades", perf['nb_trades'])

        st.divider()

        tab1, tab2, tab3 = st.tabs(["Graphiques", "Trades", "Analyse Claude"])

        with tab1:
            # Courbe portefeuille
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=df.index,
                y=df["valeur_portefeuille"],
                name="Portefeuille",
                line=dict(color="royalblue", width=2),
            ))
            fig1.update_layout(
                title=f"Evolution du portefeuille — {actif} ({strategie})",
                xaxis_title="Date",
                yaxis_title="Valeur (USD)",
                height=400,
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Cours avec signaux
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df.index,
                y=df["Close"],
                name="Prix",
                line=dict(color="gray", width=1),
            ))

            achats = [t for t in perf["trades"] if t["type"] == "ACHAT"]
            ventes = [t for t in perf["trades"] if t["type"] == "VENTE"]

            if achats:
                fig2.add_trace(go.Scatter(
                    x=[t["date"] for t in achats],
                    y=[t["prix"] for t in achats],
                    mode="markers",
                    name="Achat",
                    marker=dict(color="green", size=10, symbol="triangle-up"),
                ))
            if ventes:
                fig2.add_trace(go.Scatter(
                    x=[t["date"] for t in ventes],
                    y=[t["prix"] for t in ventes],
                    mode="markers",
                    name="Vente",
                    marker=dict(color="red", size=10, symbol="triangle-down"),
                ))

            fig2.update_layout(
                title=f"Cours et signaux — {actif}",
                xaxis_title="Date",
                yaxis_title="Prix (USD)",
                height=400,
            )
            st.plotly_chart(fig2, use_container_width=True)

        with tab2:
            if perf["trades"]:
                trades_df = pd.DataFrame(perf["trades"])
                trades_df["date"] = pd.to_datetime(trades_df["date"]).dt.strftime("%Y-%m-%d")
                trades_df["prix"] = trades_df["prix"].round(2)
                trades_df["quantite"] = trades_df["quantite"].round(4)
                st.dataframe(trades_df, use_container_width=True)
            else:
                st.info("Aucun trade execute sur cette periode.")

        with tab3:
            st.markdown(result["analyse"])