import streamlit as st
from graph import run_analysis
import config

st.set_page_config(
    page_title="Analyse Financière",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Agent d'Analyse Financière")
st.caption(f"LangGraph · Pandas · `{config.MODEL_NAME}`")
st.markdown("---")

st.info(
    "Saisissez les données financières de l'entreprise. Le pipeline va :\n"
    "1. Calculer les ratios financiers clés\n"
    "2. Comparer aux benchmarks sectoriels\n"
    "3. Générer une interprétation IA\n"
    "4. Produire une synthèse d'investissement",
    icon="ℹ️",
)

# ─── Helper ──────────────────────────────────────────────────────────────────
def parse_number(value):
    """Convertit une saisie avec ou sans espaces/virgules en float."""
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except:
        return 0.0

# ─── Formulaire ──────────────────────────────────────────────────────────────
with st.form("financial_form"):
    st.subheader("🏢 Entreprise")
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Nom de l'entreprise *", placeholder="Apple Inc.")
    with col2:
        sector = st.selectbox("Secteur *", config.SECTORS)

    st.markdown("---")
    st.subheader("💰 Compte de résultat (en €)")
    col1, col2, col3 = st.columns(3)
    with col1:
        revenue      = st.text_input("Chiffre d'affaires *", placeholder="394 000 000")
    with col2:
        gross_profit = st.text_input("Marge brute *", placeholder="170 000 000")
    with col3:
        net_income   = st.text_input("Résultat net *", placeholder="97 000 000")

    st.markdown("---")
    st.subheader("🏦 Bilan (en €)")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_assets        = st.text_input("Total actifs *",          placeholder="352 000 000")
        current_assets      = st.text_input("Actifs courants *",       placeholder="143 000 000")
    with col2:
        total_equity        = st.text_input("Capitaux propres *",      placeholder="62 000 000")
        current_liabilities = st.text_input("Passifs courants *",      placeholder="145 000 000")
    with col3:
        total_debt          = st.text_input("Dette totale *",          placeholder="110 000 000")
        market_cap          = st.text_input("Capitalisation boursière (optionnel)", placeholder="2 800 000 000")

    submitted = st.form_submit_button("🚀 Lancer l'analyse", use_container_width=True, type="primary")

# ─── Pipeline ────────────────────────────────────────────────────────────────
if submitted:
    if not company_name or not revenue:
        st.error("⚠️ Le nom de l'entreprise et le chiffre d'affaires sont obligatoires.")
        st.stop()

    financials = {
        "revenue":             parse_number(revenue),
        "gross_profit":        parse_number(gross_profit),
        "net_income":          parse_number(net_income),
        "total_assets":        parse_number(total_assets),
        "total_equity":        parse_number(total_equity),
        "total_debt":          parse_number(total_debt),
        "current_assets":      parse_number(current_assets),
        "current_liabilities": parse_number(current_liabilities),
        "market_cap":          parse_number(market_cap) if market_cap else None,
    }

    with st.status("⚙️ Analyse en cours...", expanded=True) as pipeline_status:
        st.write("🔢 Calcul des ratios...")
        st.write("📊 Comparaison aux benchmarks...")
        st.write("🤖 Interprétation IA...")

        try:
            result = run_analysis(
                company_name = company_name,
                sector       = sector,
                financials   = financials,
            )

            final_status = result.get("status", "error")

            if final_status == "error":
                pipeline_status.update(label="❌ Erreur — pipeline interrompu", state="error")
                for err in result.get("errors", ["Erreur inconnue."]):
                    st.error(err)

            elif final_status == "completed":
                pipeline_status.update(label="✅ Analyse terminée !", state="complete", expanded=False)

                st.success(f"✅ Analyse de **{company_name}** terminée.")
                st.markdown("---")

                # ── Ratios ────────────────────────────────────────────────────
                st.subheader("📊 Ratios financiers")
                ratios = result.get("ratios", {})
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Marge brute",   f"{ratios.get('gross_margin', 0)*100:.1f}%" if ratios.get('gross_margin') else "—")
                col2.metric("Marge nette",   f"{ratios.get('net_margin', 0)*100:.1f}%" if ratios.get('net_margin') else "—")
                col3.metric("ROE",           f"{ratios.get('roe', 0)*100:.1f}%" if ratios.get('roe') else "—")
                col4.metric("Ratio courant", f"{ratios.get('current_ratio', 0):.2f}" if ratios.get('current_ratio') else "—")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Dette/Equity",  f"{ratios.get('debt_to_equity', 0):.2f}" if ratios.get('debt_to_equity') else "—")
                col2.metric("ROA",           f"{ratios.get('roa', 0)*100:.1f}%" if ratios.get('roa') else "—")
                col3.metric("Ratio dette",   f"{ratios.get('debt_ratio', 0)*100:.1f}%" if ratios.get('debt_ratio') else "—")
                col4.metric("P/E",           f"{ratios.get('pe_ratio', 0):.1f}" if ratios.get('pe_ratio') else "—")

                # ── Benchmark ─────────────────────────────────────────────────
                st.markdown("---")
                st.subheader(f"📐 Comparaison benchmark — secteur {sector}")
                comparison = result.get("comparison", {})
                for key, val in comparison.items():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    col1.write(f"**{key}**")
                    col2.write(f"Entreprise : `{val['company']}`")
                    col3.write(f"Benchmark : `{val['benchmark']}`")
                    col4.write(f"{val['signal']} {val['diff_pct']:+.1f}%")

                # ── Analyse ───────────────────────────────────────────────────
                st.markdown("---")
                with st.expander("🤖 Interprétation IA", expanded=True):
                    st.markdown(result.get("interpretation", "—"))

                # ── Recommandation ────────────────────────────────────────────
                st.markdown("---")
                with st.expander("💡 Synthèse d'investissement", expanded=True):
                    st.markdown(result.get("recommendation", "—"))

                # ── Export ────────────────────────────────────────────────────
                rapport = f"""ANALYSE FINANCIÈRE — {company_name}
Secteur : {sector}

RATIOS :
{chr(10).join([f'{k} : {v}' for k, v in ratios.items() if v is not None])}

INTERPRÉTATION :
{result.get('interpretation', '')}

SYNTHÈSE D'INVESTISSEMENT :
{result.get('recommendation', '')}
"""
                st.download_button(
                    label="⬇️ Télécharger le rapport",
                    data=rapport,
                    file_name=f"analyse_{company_name.replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            else:
                pipeline_status.update(label=f"⚠️ Arrêt à l'étape : {final_status}", state="error")
                for err in result.get("errors", []):
                    st.error(err)

        except Exception as e:
            pipeline_status.update(label="❌ Erreur inattendue", state="error")
            st.error(f"Erreur inattendue : {e}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 16 — Analyse financière · [GitHub](https://github.com/Rek1DSables/templates-ai)")