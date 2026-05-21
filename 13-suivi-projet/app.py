import streamlit as st
from graph import run_action
import config

st.set_page_config(
    page_title="Suivi de Projet",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Suivi de Projet Automatisé")
st.caption(f"LangGraph · Supabase · `{config.MODEL_NAME}`")
st.markdown("---")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Tableau de bord", "➕ Ajouter une tâche", "✏️ Modifier / Supprimer"])

# ─── Tab 1 : Tableau de bord ─────────────────────────────────────────────────
with tab1:
    if st.button("🔄 Actualiser", use_container_width=True):
        st.session_state["refresh"] = True

    if st.session_state.get("refresh", True):
        with st.spinner("Chargement des tâches..."):
            result = run_action("get_summary")

            if result["status_pipeline"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                tasks   = result.get("tasks", [])
                summary = result.get("summary", "")

                if tasks:
                    # Métriques
                    total     = len(tasks)
                    done      = len([t for t in tasks if t["status"] == "Terminé"])
                    blocked   = len([t for t in tasks if t["status"] == "Bloqué"])
                    in_progress = len([t for t in tasks if t["status"] == "En cours"])

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("📋 Total",      total)
                    col2.metric("✅ Terminées",  done)
                    col3.metric("🔄 En cours",   in_progress)
                    col4.metric("🚫 Bloquées",   blocked)

                    st.markdown("---")

                    # Résumé IA
                    with st.expander("🤖 Résumé IA", expanded=True):
                        st.markdown(summary)

                    st.markdown("---")

                    # Tableau des tâches
                    st.subheader("📋 Tâches")
                    for t in tasks:
                        status_icon = {
                            "À faire": "⬜", "En cours": "🔄",
                            "En révision": "👁️", "Terminé": "✅", "Bloqué": "🚫"
                        }.get(t["status"], "⬜")

                        priority_icon = {
                            "Haute": "🔴", "Moyenne": "🟡", "Faible": "🟢"
                        }.get(t["priority"], "🟡")

                        st.markdown(
                            f"{status_icon} **{t['task_name']}** {priority_icon} | "
                            f"Assigné : {t.get('assignee') or 'Non assigné'} | "
                            f"Échéance : {t.get('due_date') or 'Non définie'} | "
                            f"`ID : {t['id'][:8]}...`"
                        )
                else:
                    st.info("Aucune tâche pour l'instant. Ajoutez-en une dans l'onglet ➕")

        st.session_state["refresh"] = False

# ─── Tab 2 : Ajouter une tâche ────────────────────────────────────────────────
with tab2:
    with st.form("add_task_form"):
        st.subheader("➕ Nouvelle tâche")

        task_name   = st.text_input("Nom de la tâche *", placeholder="Développer le module de facturation")
        description = st.text_area("Description", height=80, placeholder="Détails de la tâche...")

        col1, col2, col3 = st.columns(3)
        with col1:
            status   = st.selectbox("Statut", config.TASK_STATUSES)
        with col2:
            priority = st.selectbox("Priorité", config.TASK_PRIORITIES)
        with col3:
            assignee = st.text_input("Assigné à", placeholder="Marie Dupont")

        due_date = st.date_input("Date d'échéance", value=None)

        submitted = st.form_submit_button("➕ Ajouter la tâche", use_container_width=True, type="primary")

    if submitted:
        if not task_name:
            st.error("⚠️ Le nom de la tâche est obligatoire.")
        else:
            with st.spinner("Ajout en cours..."):
                result = run_action(
                    "add_task",
                    task_name   = task_name,
                    description = description,
                    status      = status,
                    priority    = priority,
                    assignee    = assignee,
                    due_date    = str(due_date) if due_date else None,
                )
                if result["status_pipeline"] == "error":
                    for err in result["errors"]:
                        st.error(err)
                else:
                    st.success(f"✅ Tâche **{task_name}** ajoutée avec succès !")
                    st.session_state["refresh"] = True

# ─── Tab 3 : Modifier / Supprimer ────────────────────────────────────────────
with tab3:
    st.subheader("✏️ Modifier une tâche")

    with st.form("update_task_form"):
        task_id  = st.text_input("ID de la tâche *", placeholder="Copiez l'ID depuis le tableau de bord")

        col1, col2, col3 = st.columns(3)
        with col1:
            new_status   = st.selectbox("Nouveau statut", [""] + config.TASK_STATUSES)
        with col2:
            new_priority = st.selectbox("Nouvelle priorité", [""] + config.TASK_PRIORITIES)
        with col3:
            new_assignee = st.text_input("Nouvel assigné", placeholder="Jean Martin")

        new_due_date = st.date_input("Nouvelle échéance", value=None)

        update_btn = st.form_submit_button("✏️ Mettre à jour", use_container_width=True, type="primary")

    if update_btn:
        if not task_id:
            st.error("⚠️ L'ID de la tâche est obligatoire.")
        else:
            with st.spinner("Mise à jour..."):
                result = run_action(
                    "update_task",
                    task_id  = task_id,
                    status   = new_status or None,
                    priority = new_priority or None,
                    assignee = new_assignee or None,
                    due_date = str(new_due_date) if new_due_date else None,
                )
                if result["status_pipeline"] == "error":
                    for err in result["errors"]:
                        st.error(err)
                else:
                    st.success("✅ Tâche mise à jour !")
                    st.session_state["refresh"] = True

    st.markdown("---")
    st.subheader("🗑️ Supprimer une tâche")

    with st.form("delete_task_form"):
        delete_id  = st.text_input("ID de la tâche à supprimer *")
        delete_btn = st.form_submit_button("🗑️ Supprimer", use_container_width=True, type="secondary")

    if delete_btn:
        if not delete_id:
            st.error("⚠️ L'ID est obligatoire.")
        else:
            with st.spinner("Suppression..."):
                result = run_action("delete_task", task_id=delete_id)
                if result["status_pipeline"] == "error":
                    for err in result["errors"]:
                        st.error(err)
                else:
                    st.success("✅ Tâche supprimée !")
                    st.session_state["refresh"] = True

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 13 — Suivi de projet · [GitHub](https://github.com/Rek1DSables/templates-ai)")