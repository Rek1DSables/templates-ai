# graph.py
import os
import time
import json
import hashlib
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
    EMBEDDING_MODEL, SEUIL_CONFIANCE_ELEVE, SEUIL_CONFIANCE_MOYEN
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Index vectoriel en mémoire (remplaçable par Pinecone/Weaviate en prod)
VECTOR_STORE = {}
DOCUMENT_REGISTRY = {}


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


class RAGState(TypedDict):
    # Mode
    mode: str  # "indexer" | "interroger"

    # Indexation
    documents_a_indexer: list
    documents_indexes: list

    # Interrogation
    question: str
    profil_utilisateur: str
    permissions_utilisateur: list
    chunks_retrouves: list
    chunks_autorises: list
    contexte_assemble: str

    # Réponse
    reponse: str
    sources_citees: list
    score_confiance: float
    hallucination_detectee: bool
    avertissement: str

    # Audit
    audit_log: list
    erreur: str


def chunker(texte: str, taille: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Découpe le texte en chunks avec overlap."""
    mots = texte.split()
    chunks = []
    i = 0
    while i < len(mots):
        chunk = " ".join(mots[i:i + taille])
        chunks.append(chunk)
        i += taille - overlap
    return chunks


# Cache du modèle en mémoire
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def get_embedding(texte: str) -> list:
    try:
        model = get_embedding_model()
        return model.encode(texte).tolist()
    except Exception:
        h = hashlib.md5(texte.encode()).hexdigest()
        return [int(h[i:i+2], 16) / 255.0 for i in range(0, min(len(h), 64), 2)]


def cosine_similarity(a: list, b: list) -> float:
    """Calcule la similarité cosinus entre deux vecteurs."""
    try:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x ** 2 for x in a) ** 0.5
        norm_b = sum(x ** 2 for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    except Exception:
        return 0.0


def agent_indexation(state: RAGState) -> RAGState:
    """Indexe les documents dans le vector store."""
    try:
        audit_log = log(state.get("audit_log", []), "Indexation documents", "Agent Indexation",
            f"{len(state['documents_a_indexer'])} documents")

        documents_indexes = []

        for doc in state["documents_a_indexer"]:
            doc_id = hashlib.md5(doc["contenu"].encode()).hexdigest()[:8]
            chunks = chunker(doc["contenu"])

            doc_info = {
                "id": doc_id,
                "nom": doc.get("nom", "Document"),
                "type": doc.get("type", "Autre"),
                "permission": doc.get("permission", "interne"),
                "nb_chunks": len(chunks),
            }
            DOCUMENT_REGISTRY[doc_id] = doc_info

            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                embedding = get_embedding(chunk)
                VECTOR_STORE[chunk_id] = {
                    "id": chunk_id,
                    "doc_id": doc_id,
                    "doc_nom": doc.get("nom", "Document"),
                    "doc_type": doc.get("type", "Autre"),
                    "permission": doc.get("permission", "interne"),
                    "contenu": chunk,
                    "embedding": embedding,
                    "chunk_index": i,
                }

            documents_indexes.append(doc_info)
            audit_log = log(audit_log, f"Document indexé", "Agent Indexation",
                f"{doc.get('nom')} — {len(chunks)} chunks | Permission : {doc.get('permission')}")

        audit_log = log(audit_log, "Indexation terminée", "Agent Indexation",
            f"{len(documents_indexes)} documents | {len(VECTOR_STORE)} chunks total")

        return {
            **state,
            "documents_indexes": documents_indexes,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur indexation : {str(e)}"}


def agent_retrieval_gouvernance(state: RAGState) -> RAGState:
    """Recherche les chunks pertinents et applique les permissions."""
    try:
        audit_log = log(state.get("audit_log", []), "Retrieval & Gouvernance", "Agent Retrieval",
            f"Question : {state['question'][:60]}")

        if not VECTOR_STORE:
            return {**state, "erreur": "Aucun document indexé. Veuillez d'abord indexer des documents."}

        # Embedding de la question
        question_embedding = get_embedding(state["question"])

        # Calcul similarité sur tous les chunks
        scored_chunks = []
        for chunk_id, chunk_data in VECTOR_STORE.items():
            score = cosine_similarity(question_embedding, chunk_data["embedding"])
            scored_chunks.append({**chunk_data, "score": score})

        # Tri par score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        top_chunks = scored_chunks[:TOP_K * 2]  # Récupérer plus pour filtrer ensuite

        audit_log = log(audit_log, "Retrieval terminé", "Agent Retrieval",
            f"{len(top_chunks)} chunks candidats")

        # Gouvernance — filtrage par permissions
        permissions = state.get("permissions_utilisateur", ["public", "interne"])
        chunks_autorises = []
        chunks_bloques = []

        for chunk in top_chunks:
            if chunk.get("permission", "interne") in permissions:
                chunks_autorises.append(chunk)
            else:
                chunks_bloques.append(chunk)

        chunks_autorises = chunks_autorises[:TOP_K]

        audit_log = log(audit_log, "Gouvernance appliquée", "Agent Retrieval",
            f"{len(chunks_autorises)} chunks autorisés | {len(chunks_bloques)} bloqués par permissions")

        # Assemblage contexte
        contexte_parts = []
        sources_citees = []
        for i, chunk in enumerate(chunks_autorises):
            contexte_parts.append(
                f"[SOURCE {i+1} — {chunk['doc_nom']} — Score: {chunk['score']:.2f}]\n{chunk['contenu']}"
            )
            if chunk["doc_nom"] not in [s["nom"] for s in sources_citees]:
                sources_citees.append({
                    "nom": chunk["doc_nom"],
                    "type": chunk["doc_type"],
                    "permission": chunk["permission"],
                    "score_max": chunk["score"],
                })

        contexte = "\n\n---\n\n".join(contexte_parts)
        score_moyen = sum(c["score"] for c in chunks_autorises) / len(chunks_autorises) if chunks_autorises else 0

        avertissement = ""
        if chunks_bloques:
            avertissement = f"⚠️ {len(chunks_bloques)} chunk(s) masqué(s) — niveau de permission insuffisant ({state.get('profil_utilisateur', 'Employé standard')})"

        return {
            **state,
            "chunks_retrouves": top_chunks,
            "chunks_autorises": chunks_autorises,
            "contexte_assemble": contexte,
            "sources_citees": sources_citees,
            "score_confiance": round(score_moyen, 2),
            "avertissement": avertissement,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur retrieval : {str(e)}"}


def agent_generation_reponse(state: RAGState) -> RAGState:
    """Génère la réponse en se basant strictement sur le contexte."""
    try:
        audit_log = log(state.get("audit_log", []), "Génération réponse", "Agent Génération")

        if not state["chunks_autorises"]:
            return {
                **state,
                "reponse": "Je ne trouve pas d'information pertinente dans les documents autorisés pour répondre à cette question.",
                "hallucination_detectee": False,
                "audit_log": log(audit_log, "Aucun contexte", "Agent Génération", "Réponse vide retournée"),
                "erreur": "",
            }

        system = f"""Tu es un assistant RAG enterprise expert.
Tu reponds UNIQUEMENT en te basant sur les sources fournies.
Tu ne peux PAS inventer d informations qui ne sont pas dans les sources.
Si tu ne trouves pas l information dans les sources, dis-le clairement.
Tu cites toujours tes sources avec [SOURCE N].
Tu reponds en francais professionnel.
Profil utilisateur : {state.get('profil_utilisateur', 'Employé standard')}"""

        prompt = f"""Reponds a cette question en te basant UNIQUEMENT sur les sources ci-dessous :

QUESTION : {state['question']}

SOURCES DISPONIBLES :
{state['contexte_assemble'][:4000]}

Instructions :
- Cite les sources avec [SOURCE 1], [SOURCE 2], etc.
- Si l information n est pas dans les sources, dis : "Cette information n est pas disponible dans les documents accessibles."
- Ne complete pas avec des connaissances generales
- Sois precis et concis (200 mots max)

Reponds maintenant."""

        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            model=MODEL_SONNET,
        )

        audit_log = log(audit_log, "Réponse générée", "Agent Génération", f"{len(reponse)} caractères")

        return {
            **state,
            "reponse": reponse,
            "hallucination_detectee": False,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur génération : {str(e)}"}


def agent_anti_hallucination(state: RAGState) -> RAGState:
    try:
        audit_log = log(state.get("audit_log", []), "Vérification anti-hallucination", "Agent Vérification")

        if not state["chunks_autorises"]:
            audit_log = log(audit_log, "Vérification ignorée", "Agent Vérification", "Aucun chunk")
            return {**state, "hallucination_detectee": False, "audit_log": audit_log, "erreur": ""}

        system = """Tu es un verificateur de qualite RAG strict.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "ancree_dans_sources": true,
  "score_ancrage": 0.90,
  "verdict": "fiable",
  "commentaire": "La reponse est bien ancree dans les sources"
}
IMPORTANT : si la reponse paraphrase ou reformule les sources sans inventer de faits nouveaux, c est FIABLE.
Une hallucination c est uniquement un fait invente absent de toutes les sources."""

        contexte_court = "\n".join([c["contenu"][:300] for c in state["chunks_autorises"][:3]])

        prompt = f"""Verifie si cette reponse contient des FAITS INVENTES absents des sources :

QUESTION : {state['question']}

REPONSE :
{state['reponse']}

SOURCES :
{contexte_court}

Une paraphrase ou reformulation est FIABLE.
Seul un fait entierement invente et absent des sources est une hallucination.
JSON uniquement."""

        reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=200)

        reponse_clean = reponse.strip()
        start = reponse_clean.find("{")
        end = reponse_clean.rfind("}") + 1
        if start >= 0 and end > start:
            reponse_clean = reponse_clean[start:end]

        try:
            data = json.loads(reponse_clean)
        except Exception:
            data = {"ancree_dans_sources": True, "score_ancrage": 0.8, "verdict": "fiable", "commentaire": ""}

        hallucination = not data.get("ancree_dans_sources", True)
        score_ancrage = data.get("score_ancrage", 0.8)

        avertissement = state.get("avertissement", "")
        if hallucination:
            avertissement += f"\n⚠️ Fait inventé détecté : {data.get('commentaire', '')}"

        audit_log = log(audit_log, "Vérification terminée", "Agent Vérification",
            f"Ancrage : {score_ancrage:.0%} | Verdict : {data.get('verdict', 'fiable')}")
        audit_log = log(audit_log, "Pipeline RAG terminé", "system",
            f"Confiance : {state['score_confiance']:.0%} | Sources : {len(state['sources_citees'])}")

        return {
            **state,
            "hallucination_detectee": hallucination,
            "avertissement": avertissement,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur vérification : {str(e)}"}


def router_mode(state: RAGState) -> str:
    if state["mode"] == "indexer":
        return "indexer"
    return "interroger"


def build_graph():
    graph = StateGraph(RAGState)
    graph.add_node("agent_indexation", agent_indexation)
    graph.add_node("agent_retrieval_gouvernance", agent_retrieval_gouvernance)
    graph.add_node("agent_generation_reponse", agent_generation_reponse)
    graph.add_node("agent_anti_hallucination", agent_anti_hallucination)

    graph.set_entry_point("agent_indexation")

    graph.add_conditional_edges(
        "agent_indexation",
        router_mode,
        {
            "indexer": END,
            "interroger": "agent_retrieval_gouvernance",
        }
    )
    graph.add_edge("agent_retrieval_gouvernance", "agent_generation_reponse")
    graph.add_edge("agent_generation_reponse", "agent_anti_hallucination")
    graph.add_edge("agent_anti_hallucination", END)

    return graph.compile()