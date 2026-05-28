# app.py
import json
import streamlit as st
from fpdf import FPDF
from graph import build_graph
from config import TYPES_DOCUMENT, MODES, TAUX_TVA


def nettoyer(texte: str) -> str:
    remplacements = {
        "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"',
        "\u00ab": '"', "\u00bb": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...", "\u00a0": " ",
    }
    for src, dst in remplacements.items():
        texte = texte.replace(src, dst)
    resultat = ""
    for char in texte:
        try:
            char.encode("latin-1")
            resultat += char
        except UnicodeEncodeError:
            resultat += " "
    return resultat


def generer_pdf_document(donnees: dict, type_doc: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    # Titre
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.multi_cell(largeur, 12, nettoyer(type_doc.upper()))
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(largeur, 6, nettoyer(f"N° {donnees.get('numero', '')} — Date : {donnees.get('date', '')} — Échéance : {donnees.get('echeance', '')}"))
    pdf.ln(4)

    # Emetteur / Destinataire
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.multi_cell(largeur / 2, 8, nettoyer("EMETTEUR"), border=0)
    pdf.set_font("Helvetica", size=10)
    emetteur = donnees.get("emetteur", {})
    pdf.multi_cell(largeur, 6, nettoyer(emetteur.get("nom", "")))
    pdf.multi_cell(largeur, 6, nettoyer(emetteur.get("adresse", "")))
    pdf.multi_cell(largeur, 6, nettoyer(f"SIRET : {emetteur.get('siret', '')}"))
    pdf.ln(3)

    pdf.set_font("Helvetica", style="B", size=11)
    pdf.multi_cell(largeur, 8, nettoyer("DESTINATAIRE"))
    pdf.set_font("Helvetica", size=10)
    destinataire = donnees.get("destinataire", {})
    pdf.multi_cell(largeur, 6, nettoyer(destinataire.get("nom", "")))
    pdf.multi_cell(largeur, 6, nettoyer(destinataire.get("adresse", "")))
    pdf.multi_cell(largeur, 6, nettoyer(f"SIRET : {destinataire.get('siret', '')}"))
    pdf.ln(4)

    # Lignes
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.multi_cell(largeur, 8, nettoyer("PRESTATIONS"))
    pdf.set_font("Helvetica", size=10)
    for ligne in donnees.get("lignes", []):
        desc = nettoyer(ligne.get("description", ""))
        qte = ligne.get("quantite", 1)
        pu = ligne.get("prix_unitaire", 0)
        tva = ligne.get("tva", 20)
        total = qte * pu
        pdf.multi_cell(largeur, 6, f"- {desc} : {qte} x {pu:.2f} EUR HT (TVA {tva}%) = {total:.2f} EUR HT")
    pdf.ln(4)

    # Totaux
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.multi_cell(largeur, 8, nettoyer("TOTAUX"))
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(largeur, 6, nettoyer(f"Total HT : {donnees.get('montant_ht', 0):.2f} EUR"))
    pdf.multi_cell(largeur, 6, nettoyer(f"TVA : {donnees.get('montant_tva', 0):.2f} EUR"))
    pdf.multi_cell(largeur, 6, nettoyer(f"Total TTC : {donnees.get('montant_ttc', 0):.2f} EUR"))
    pdf.ln(4)

    # Conditions
    if donnees.get("conditions_paiement"):
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.multi_cell(largeur, 8, nettoyer("CONDITIONS DE PAIEMENT"))
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(largeur, 6, nettoyer(donnees.get("conditions_paiement", "")))

    return bytes(pdf.output())


def generer_pdf_texte(contenu: str, titre: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer(titre))
    pdf.ln(4)
    pdf.set_font("Helvetica", size=10)

    for ligne in contenu.split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        if ligne.isupper() or ligne.startswith("#"):
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.multi_cell(largeur, 8, ligne.replace("#", "").strip())
            pdf.set_font("Helvetica", size=10)
        else:
            pdf.multi_cell(largeur, 6, ligne)

    return bytes(pdf.output())


# --- UI ---
st.set_page_config(page_title="Agent Finance & Documents", page_icon="💰", layout="centered")
st.title("💰 Agent Finance & Documents")
st.caption("Analyse de documents financiers + Génération de devis et factures")

mode = st.radio("Mode", MODES, horizontal=True)

if mode == "Analyser un document":
    st.subheader("Analyser un document financier")

    type_document = st.selectbox("Type de document", TYPES_DOCUMENT)

    source = st.radio("Source", ["Coller le texte", "Uploader un PDF"], horizontal=True)
    contenu = ""

    if source == "Coller le texte":
        contenu = st.text_area(
            "Contenu du document",
            placeholder="Colle ici le contenu de ta facture, devis ou document financier...",
            height=250,
        )
    else:
        import pymupdf
        fichier = st.file_uploader("Fichier PDF", type=["pdf"])
        if fichier:
            try:
                pdf_bytes = fichier.read()
                doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
                contenu = ""
                for page in doc:
                    contenu += page.get_text()
                st.success(f"PDF extrait : {len(contenu)} caractères")
            except Exception as e:
                st.error(f"Erreur extraction PDF : {e}")

    if st.button("Analyser", use_container_width=True):
        if not contenu:
            st.error("Merci de fournir le contenu du document.")
        else:
            with st.spinner("Analyse en cours..."):
                try:
                    graph = build_graph()
                    result = graph.invoke({
                        "mode": mode,
                        "type_document": type_document,
                        "contenu_document": contenu,
                        "donnees_extraites": {},
                        "anomalies": [],
                        "document_genere": "",
                        "montant_ht": 0.0,
                        "montant_ttc": 0.0,
                        "taux_tva": 20.0,
                        "client_info": {},
                        "prestataire_info": {},
                        "lignes": [],
                        "erreur": "",
                    })
                except Exception as e:
                    st.error(f"Erreur : {e}")
                    st.stop()

            if result["erreur"]:
                st.warning(result["erreur"])

            donnees = result["donnees_extraites"]
            emetteur = donnees.get("emetteur", {})
            destinataire = donnees.get("destinataire", {})
            lignes = donnees.get("lignes", [])

            col1, col2 = st.columns(2)
            col1.metric("Total HT", f"{donnees.get('montant_ht', 0):.2f} €")
            col2.metric("Total TTC", f"{donnees.get('montant_ttc', 0):.2f} €")

            tab1, tab2, tab3 = st.tabs(["Document", "Anomalies", "Export"])

            with tab1:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Émetteur**")
                    st.markdown(f"🏢 {emetteur.get('nom', '—')}")
                    st.markdown(f"📍 {emetteur.get('adresse', '—')}")
                    st.markdown(f"🔢 SIRET : {emetteur.get('siret', '—')}")
                    st.markdown(f"📧 {emetteur.get('email', '—')}")

                with col_b:
                    st.markdown("**Destinataire**")
                    st.markdown(f"🏢 {destinataire.get('nom', '—')}")
                    st.markdown(f"📍 {destinataire.get('adresse', '—')}")
                    st.markdown(f"🔢 SIRET : {destinataire.get('siret', '—')}")
                    st.markdown(f"📧 {destinataire.get('email', '—')}")

                st.divider()
                st.markdown(f"**N° {donnees.get('numero', '—')}** — Date : {donnees.get('date', '—')} — Échéance : {donnees.get('echeance', '—')}")
                st.markdown(f"Conditions : {donnees.get('conditions_paiement', '—')} — Statut : {donnees.get('statut_paiement', '—')}")
                st.divider()

                st.markdown("**Lignes de facturation**")
                if lignes:
                    import pandas as pd
                    df = pd.DataFrame(lignes)
                    df.columns = ["Description", "Quantité", "Prix unitaire HT (€)", "TVA (%)"]
                    df["Total HT (€)"] = df["Quantité"] * df["Prix unitaire HT (€)"]
                    st.dataframe(df, use_container_width=True, hide_index=True)

                st.divider()
                col_x, col_y, col_z = st.columns(3)
                col_x.metric("Total HT", f"{donnees.get('montant_ht', 0):.2f} €")
                col_y.metric("TVA", f"{donnees.get('montant_tva', 0):.2f} €")
                col_z.metric("Total TTC", f"{donnees.get('montant_ttc', 0):.2f} €")

            with tab2:
                anomalies = result["anomalies"]
                if not anomalies:
                    st.success("Aucune anomalie détectée.")
                else:
                    for a in anomalies:
                        niveau = a.get("niveau", "moyen")
                        icone = "🔴" if niveau == "critique" else "🟠" if niveau == "eleve" else "🟡"
                        with st.expander(f"{icone} {a.get('type', 'Anomalie')}"):
                            st.write(a.get("description", ""))
                            st.info(f"Recommandation : {a.get('recommandation', '')}")

            with tab3:
                st.markdown("**Télécharger le document**")

                col_pdf, col_json = st.columns(2)

                with col_pdf:
                    try:
                        pdf_bytes = generer_pdf_document(donnees, type_document)
                        st.download_button(
                            label="📄 Télécharger PDF",
                            data=pdf_bytes,
                            file_name=f"{type_document.lower().replace(' ', '_')}_{donnees.get('numero', 'export')}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.warning(f"PDF indisponible : {e}")

                with col_json:
                    json_str = json.dumps(donnees, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="📦 Télécharger JSON",
                        data=json_str,
                        file_name=f"{type_document.lower().replace(' ', '_')}_{donnees.get('numero', 'export')}.json",
                        mime="application/json",
                        use_container_width=True,
                    )

else:
    st.subheader(f"Générer un document financier")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Émetteur (vous)**")
        prest_nom = st.text_input("Nom / Raison sociale", placeholder="Jean Martin")
        prest_siret = st.text_input("SIRET", placeholder="123 456 789 00010")
        prest_adresse = st.text_input("Adresse", placeholder="5 avenue Victor Hugo, 69001 Lyon")
        prest_email = st.text_input("Email", placeholder="jean@freelance.fr")

    with col2:
        st.markdown("**Destinataire (client)**")
        client_nom = st.text_input("Nom / Raison sociale ", placeholder="Acme Corp")
        client_adresse = st.text_input("Adresse ", placeholder="12 rue de la Paix, 75001 Paris")
        client_email = st.text_input("Email ", placeholder="contact@acme.com")

    st.markdown("**Prestations**")
    nb_lignes = st.number_input("Nombre de lignes", min_value=1, max_value=10, value=1)

    lignes = []
    for i in range(nb_lignes):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        desc = c1.text_input(f"Description #{i+1}", placeholder="Développement agent IA")
        qte = c2.number_input(f"Qté #{i+1}", min_value=1, value=1)
        pu = c3.number_input(f"Prix HT #{i+1}", min_value=0.0, value=0.0)
        tva = c4.selectbox(f"TVA #{i+1}", TAUX_TVA, index=3)
        lignes.append({"description": desc, "quantite": qte, "prix_unitaire": pu, "tva": tva})

    montant_ht = sum(l["quantite"] * l["prix_unitaire"] for l in lignes)
    taux_tva = lignes[0]["tva"] if lignes else 20.0
    montant_tva = montant_ht * taux_tva / 100
    montant_ttc = montant_ht + montant_tva

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total HT", f"{montant_ht:.2f} €")
    col_b.metric("TVA", f"{montant_tva:.2f} €")
    col_c.metric("Total TTC", f"{montant_ttc:.2f} €")

    type_doc = "Devis" if "devis" in mode.lower() else "Facture"

    if st.button(f"Générer le {type_doc}", use_container_width=True):
        if not prest_nom or not client_nom:
            st.error("Merci de renseigner les informations émetteur et destinataire.")
        else:
            with st.spinner(f"Génération du {type_doc}..."):
                try:
                    graph = build_graph()
                    result = graph.invoke({
                        "mode": mode,
                        "type_document": type_doc,
                        "contenu_document": "",
                        "donnees_extraites": {},
                        "anomalies": [],
                        "document_genere": "",
                        "montant_ht": montant_ht,
                        "montant_ttc": montant_ttc,
                        "taux_tva": taux_tva,
                        "client_info": {
                            "nom": client_nom,
                            "adresse": client_adresse,
                            "email": client_email,
                        },
                        "prestataire_info": {
                            "nom": prest_nom,
                            "siret": prest_siret,
                            "adresse": prest_adresse,
                            "email": prest_email,
                        },
                        "lignes": lignes,
                        "erreur": "",
                    })
                except Exception as e:
                    st.error(f"Erreur : {e}")
                    st.stop()

            if result["erreur"]:
                st.warning(result["erreur"])

            st.divider()
            st.markdown(result["document_genere"])
            st.divider()

            # Export PDF depuis les données structurées
            donnees_export = {
                "numero": f"{type_doc[:3].upper()}-2026-001",
                "date": "2026-06-01",
                "echeance": "2026-07-01",
                "emetteur": {
                    "nom": prest_nom,
                    "siret": prest_siret,
                    "adresse": prest_adresse,
                    "email": prest_email,
                },
                "destinataire": {
                    "nom": client_nom,
                    "adresse": client_adresse,
                    "email": client_email,
                },
                "lignes": lignes,
                "montant_ht": montant_ht,
                "montant_tva": montant_tva,
                "montant_ttc": montant_ttc,
                "conditions_paiement": "30 jours - Virement bancaire",
                "statut_paiement": "En attente",
            }

            col_pdf, col_json = st.columns(2)

            with col_pdf:
                try:
                    pdf_bytes = generer_pdf_document(donnees_export, type_doc)
                    st.download_button(
                        label=f"📄 Télécharger {type_doc} PDF",
                        data=pdf_bytes,
                        file_name=f"{type_doc.lower()}_{prest_nom.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.warning(f"PDF indisponible : {e}")

            with col_json:
                json_str = json.dumps(donnees_export, ensure_ascii=False, indent=2)
                st.download_button(
                    label=f"📦 Télécharger {type_doc} JSON",
                    data=json_str,
                    file_name=f"{type_doc.lower()}_{prest_nom.replace(' ', '_')}.json",
                    mime="application/json",
                    use_container_width=True,
                )