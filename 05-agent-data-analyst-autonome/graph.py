# graph.py
import time
import json
import sqlite3
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    SQL_DEMO_SCHEMA, SQL_DEMO_DATA, DB_URL
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class DataAnalystState(TypedDict):
    question: str
    schema_info: str
    sql_genere: str
    sql_valide: bool
    resultats_bruts: list
    nb_resultats: int
    analyse: str
    visualisation_config: dict
    commentaire_executif: str
    audit_log: list
    erreur: str


def invoke_with_retry(messages: list, system: str, max_tokens: int = 1000, model: str = None) -> str:
    m = model or MODEL_NAME
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=m,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.APIStatusError as e:
            if "overloaded" in str(e).lower() and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise


def log(audit_log: list, etape: str, agent: str, detail: str = "") -> list:
    audit_log.append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "etape": etape,
        "agent": agent,
        "detail": detail,
    })
    return audit_log


def init_demo_db():
    """Initialise la base SQLite de demo."""
    conn = sqlite3.connect(DB_URL)
    conn.executescript(SQL_DEMO_SCHEMA)
    conn.executescript(SQL_DEMO_DATA)
    conn.commit()
    conn.close()


def get_schema_info() -> str:
    """Récupère le schéma de la base de données."""
    try:
        conn = sqlite3.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        schema = []
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            cols_str = ", ".join([f"{c[1]} ({c[2]})" for c in columns])
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            schema.append(f"TABLE {table_name} ({count} lignes) : {cols_str}")

        conn.close()
        return "\n".join(schema)
    except Exception as e:
        return f"Erreur schema : {str(e)}"


def agent_text_to_sql(state: DataAnalystState) -> DataAnalystState:
    """Traduit la question en SQL valide."""
    try:
        audit_log = log(state.get("audit_log", []), "Text-to-SQL", "Agent SQL",
            f"Question : {state['question'][:80]}")

        system = """Tu es un expert SQL et data analyst.
Tu traduis des questions en langage naturel en requetes SQL SQLite valides.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "sql": "SELECT ... FROM ... WHERE ... GROUP BY ... ORDER BY ... LIMIT ...",
  "explication": "Ce que fait la requete en 1 phrase",
  "type_viz": "bar|line|pie|table|scatter",
  "axe_x": "colonne pour axe X",
  "axe_y": "colonne pour axe Y"
}"""

        prompt = f"""Traduis cette question en SQL SQLite :

QUESTION : {state['question']}

SCHEMA DE LA BASE :
{state['schema_info']}

Regles :
- SQL SQLite valide uniquement
- Pas de WITH RECURSIVE
- LIMIT 50 maximum
- Aliases clairs sur toutes les colonnes calculees
- ORDER BY pertinent
JSON uniquement."""

        reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=600)

        reponse_clean = reponse.strip()
        start = reponse_clean.find("{")
        end = reponse_clean.rfind("}") + 1
        if start >= 0 and end > start:
            reponse_clean = reponse_clean[start:end]

        data = json.loads(reponse_clean)
        sql = data.get("sql", "")

        audit_log = log(audit_log, "SQL généré", "Agent SQL", sql[:100])

        return {
            **state,
            "sql_genere": sql,
            "sql_valide": bool(sql),
            "visualisation_config": {
                "type": data.get("type_viz", "table"),
                "axe_x": data.get("axe_x", ""),
                "axe_y": data.get("axe_y", ""),
                "explication": data.get("explication", ""),
            },
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "sql_genere": "", "sql_valide": False, "erreur": f"Erreur SQL : {str(e)}"}


def agent_execution_validation(state: DataAnalystState) -> DataAnalystState:
    """Exécute le SQL et valide les résultats."""
    try:
        audit_log = log(state.get("audit_log", []), "Exécution SQL", "Agent Validation",
            f"SQL : {state['sql_genere'][:80]}")

        if not state["sql_genere"]:
            return {**state, "erreur": "Pas de SQL à exécuter"}

        conn = sqlite3.connect(DB_URL)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(state["sql_genere"])
            rows = cursor.fetchall()
            resultats = [dict(row) for row in rows]
            conn.close()
        except sqlite3.Error as e:
            conn.close()
            # Retry avec correction
            audit_log = log(audit_log, "Erreur SQL — tentative correction", "Agent Validation", str(e))

            system = """Tu es un expert SQL SQLite.
Tu corriges une requete SQL qui a echoue.
Reponds UNIQUEMENT avec le SQL corrige, rien d autre."""

            prompt = f"""Corrige cette requete SQL SQLite :

REQUETE ORIGINALE :
{state['sql_genere']}

ERREUR :
{str(e)}

SCHEMA :
{state['schema_info']}

Reponds uniquement avec le SQL corrige."""

            sql_corrige = invoke_with_retry(
                system=system,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
            )
            sql_corrige = sql_corrige.strip()

            conn2 = sqlite3.connect(DB_URL)
            conn2.row_factory = sqlite3.Row
            cursor2 = conn2.cursor()
            cursor2.execute(sql_corrige)
            rows = cursor2.fetchall()
            resultats = [dict(row) for row in rows]
            conn2.close()

            state = {**state, "sql_genere": sql_corrige}

        audit_log = log(audit_log, "Exécution réussie", "Agent Validation",
            f"{len(resultats)} lignes retournées")

        return {
            **state,
            "resultats_bruts": resultats,
            "nb_resultats": len(resultats),
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "resultats_bruts": [], "nb_resultats": 0, "erreur": f"Erreur exécution : {str(e)}"}


def agent_analyse_insights(state: DataAnalystState) -> DataAnalystState:
    """Analyse les résultats et génère des insights."""
    try:
        audit_log = log(state.get("audit_log", []), "Analyse insights", "Agent Analyse")

        if not state["resultats_bruts"]:
            return {**state, "analyse": "Aucun résultat à analyser.", "erreur": ""}

        system = """Tu es un data analyst senior et consultant business.
Tu analyses des donnees et generes des insights actionnables en francais professionnel.
Tu termines TOUJOURS avant de t arreter."""

        resultats_str = json.dumps(state["resultats_bruts"][:20], ensure_ascii=False, indent=2)

        prompt = f"""Analyse ces resultats de donnees :

QUESTION POSEE : {state['question']}
NOMBRE DE LIGNES : {state['nb_resultats']}

DONNEES :
{resultats_str}

Redige une analyse concise (150 mots max) :
1. OBSERVATION PRINCIPALE : chiffre cle le plus important
2. TENDANCES : 2-3 patterns identifies
3. ANOMALIES : points atypiques si present
4. RECOMMANDATION : 1 action concrete

Termine la recommandation."""

        analyse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            model=MODEL_SONNET,
        )

        audit_log = log(audit_log, "Analyse terminée", "Agent Analyse", f"{len(analyse)} caractères")

        return {**state, "analyse": analyse, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur analyse : {str(e)}"}


def agent_commentaire_executif(state: DataAnalystState) -> DataAnalystState:
    """Génère un commentaire exécutif synthétique."""
    try:
        audit_log = log(state.get("audit_log", []), "Commentaire exécutif", "Agent Executive")

        system = """Tu es un consultant business senior.
Tu rediges des commentaires executifs synthetiques en francais.
Tu termines TOUJOURS avant de t arreter."""

        prompt = f"""Redige un commentaire executif en 3 phrases maximum :

QUESTION : {state['question']}
ANALYSE : {state['analyse'][:400]}

Format :
- Phrase 1 : constat principal chiffre
- Phrase 2 : implication business
- Phrase 3 : recommandation immediate

3 phrases maximum. Termine la 3eme phrase."""

        commentaire = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            model=MODEL_SONNET,
        )

        audit_log = log(audit_log, "Pipeline terminé", "system",
            f"Question traitée en {len(state['audit_log'])} étapes")

        return {**state, "commentaire_executif": commentaire, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur commentaire : {str(e)}"}


def build_graph():
    graph = StateGraph(DataAnalystState)
    graph.add_node("agent_text_to_sql", agent_text_to_sql)
    graph.add_node("agent_execution_validation", agent_execution_validation)
    graph.add_node("agent_analyse_insights", agent_analyse_insights)
    graph.add_node("agent_commentaire_executif", agent_commentaire_executif)

    graph.set_entry_point("agent_text_to_sql")
    graph.add_edge("agent_text_to_sql", "agent_execution_validation")
    graph.add_edge("agent_execution_validation", "agent_analyse_insights")
    graph.add_edge("agent_analyse_insights", "agent_commentaire_executif")
    graph.add_edge("agent_commentaire_executif", END)

    return graph.compile()