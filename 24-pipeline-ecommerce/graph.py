import time
import base64
from typing import TypedDict, Optional
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from supabase import create_client
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=1024,
)

# ─── State ───────────────────────────────────────────────────────────────────
class EcommerceState(TypedDict):
    # Action
    action: str  # new_order | update_stock | get_dashboard | check_alerts

    # Commande
    order_id:       Optional[str]
    customer_name:  Optional[str]
    customer_email: Optional[str]
    product_id:     Optional[str]
    quantity:       Optional[int]
    new_status:     Optional[str]

    # Runtime
    orders:         Optional[list]
    products:       Optional[list]
    alerts:         Optional[list]
    summary:        Optional[str]
    alert_sent:     bool

    # Suivi
    errors: list
    status_pipeline: str

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

def _supabase():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def _now():
    return datetime.now(timezone.utc).isoformat()

def _get_gmail_service():
    creds = None
    if os.path.exists(config.GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.GMAIL_TOKEN_FILE, config.GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config.GMAIL_CREDENTIALS_FILE, config.GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(config.GMAIL_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def _send_email(service, to: str, subject: str, body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = config.SENDER_EMAIL
    msg["To"]      = to
    msg.attach(MIMEText(body, "plain", "utf-8"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()

def _stop_on_error(next_node):
    def router(state):
        return END if state["status_pipeline"] == "error" else next_node
    return router

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def route_action(state: EcommerceState) -> EcommerceState:
    valid = ["new_order", "update_status", "get_dashboard", "check_alerts"]
    if state["action"] not in valid:
        return {**state, "errors": [f"Action invalide : {state['action']}"], "status_pipeline": "error"}
    return {**state, "errors": [], "status_pipeline": "routed"}


def new_order(state: EcommerceState) -> EcommerceState:
    """Crée une nouvelle commande."""
    try:
        sb = _supabase()

        # Vérification stock
        product = sb.table(config.PRODUCTS_TABLE).select("*").eq("id", state["product_id"]).execute()
        if not product.data:
            return {**state, "errors": ["Produit introuvable."], "status_pipeline": "error"}

        p = product.data[0]
        if p["stock"] < state["quantity"]:
            return {**state, "errors": [f"Stock insuffisant : {p['stock']} unités disponibles."], "status_pipeline": "error"}

        # Création commande
        total = round(p["price"] * state["quantity"], 2)
        order = sb.table(config.ORDERS_TABLE).insert({
            "customer_name":  state["customer_name"],
            "customer_email": state["customer_email"],
            "product_id":     state["product_id"],
            "product_name":   p["name"],
            "quantity":       state["quantity"],
            "unit_price":     p["price"],
            "total":          total,
            "status":         "En attente",
            "created_at":     _now(),
        }).execute()

        order_id = order.data[0]["id"]

        # Mise à jour stock
        sb.table(config.PRODUCTS_TABLE).update({
            "stock": p["stock"] - state["quantity"]
        }).eq("id", state["product_id"]).execute()

        return {**state, "order_id": order_id, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Nouvelle commande : {e}"], "status_pipeline": "error"}


def update_status(state: EcommerceState) -> EcommerceState:
    """Met à jour le statut d'une commande."""
    try:
        if not state.get("order_id") or not state.get("new_status"):
            return {**state, "errors": ["ID commande et nouveau statut requis."], "status_pipeline": "error"}

        _supabase().table(config.ORDERS_TABLE).update({
            "status":     state["new_status"],
            "updated_at": _now(),
        }).eq("id", state["order_id"]).execute()

        return {**state, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Mise à jour statut : {e}"], "status_pipeline": "error"}


def get_dashboard(state: EcommerceState) -> EcommerceState:
    """Récupère les données et génère un résumé IA."""
    try:
        sb       = _supabase()
        orders   = sb.table(config.ORDERS_TABLE).select("*").order("created_at", desc=True).execute().data
        products = sb.table(config.PRODUCTS_TABLE).select("*").order("stock", desc=False).execute().data

        # Résumé IA
        orders_text   = "\n".join([f"- {o['product_name']} x{o['quantity']} — {o['total']}€ — {o['status']}" for o in orders[:10]])
        products_text = "\n".join([f"- {p['name']} : stock={p['stock']} | prix={p['price']}€" for p in products[:10]])

        prompt = f"""Tu es un expert e-commerce. Analyse ces données et génère un résumé exécutif.

COMMANDES RÉCENTES :
{orders_text or 'Aucune commande'}

STOCK PRODUITS :
{products_text or 'Aucun produit'}

Fournis :
1. Chiffre d'affaires total et tendance
2. Produits les plus vendus
3. Alertes stock critique
4. Recommandations opérationnelles

Français, concis, professionnel.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])

        return {
            **state,
            "orders":   orders,
            "products": products,
            "summary":  response.content,
            "status_pipeline": "completed",
        }

    except Exception as e:
        return {**state, "errors": [f"Dashboard : {e}"], "status_pipeline": "error"}


def check_alerts(state: EcommerceState) -> EcommerceState:
    """Vérifie les alertes stock et commandes importantes."""
    try:
        sb       = _supabase()
        products = sb.table(config.PRODUCTS_TABLE).select("*").execute().data
        orders   = sb.table(config.ORDERS_TABLE).select("*").order("created_at", desc=True).limit(20).execute().data

        alerts = []

        # Alertes stock faible
        for p in products:
            if p["stock"] < config.LOW_STOCK_THRESHOLD:
                alerts.append({
                    "type":    "Stock faible",
                    "level":   "🔴" if p["stock"] == 0 else "🟡",
                    "message": f"{p['name']} : {p['stock']} unités restantes",
                })

        # Alertes commandes haute valeur
        for o in orders:
            if o["total"] >= config.HIGH_VALUE_ORDER:
                alerts.append({
                    "type":    "Commande haute valeur",
                    "level":   "🟢",
                    "message": f"Commande de {o['total']}€ — {o['customer_name']}",
                })

        # Envoi email si alertes critiques
        alert_sent = False
        critical   = [a for a in alerts if a["level"] == "🔴"]

        if critical and config.ALERT_EMAIL and config.SENDER_EMAIL:
            try:
                service    = _get_gmail_service()
                alert_text = "\n".join([a["message"] for a in critical])
                _send_email(
                    service,
                    config.ALERT_EMAIL,
                    "🚨 Alertes stock critique — E-commerce",
                    f"Alertes critiques détectées :\n\n{alert_text}\n\nConnectez-vous au dashboard pour agir.",
                )
                alert_sent = True
            except:
                pass

        return {**state, "alerts": alerts, "alert_sent": alert_sent, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Alertes : {e}"], "status_pipeline": "error"}


# ─── Router ───────────────────────────────────────────────────────────────────
def action_router(state: EcommerceState) -> str:
    if state["status_pipeline"] == "error":
        return END
    return state["action"]


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(EcommerceState)

    g.add_node("route_action",  route_action)
    g.add_node("new_order",     new_order)
    g.add_node("update_status", update_status)
    g.add_node("get_dashboard", get_dashboard)
    g.add_node("check_alerts",  check_alerts)

    g.set_entry_point("route_action")

    g.add_conditional_edges("route_action", action_router, {
        "new_order":     "new_order",
        "update_status": "update_status",
        "get_dashboard": "get_dashboard",
        "check_alerts":  "check_alerts",
        END:              END,
    })

    g.add_edge("new_order",     END)
    g.add_edge("update_status", END)
    g.add_edge("get_dashboard", END)
    g.add_edge("check_alerts",  END)

    return g.compile()


def run_action(action: str, **kwargs) -> EcommerceState:
    initial_state = EcommerceState(
        action         = action,
        order_id       = kwargs.get("order_id"),
        customer_name  = kwargs.get("customer_name"),
        customer_email = kwargs.get("customer_email"),
        product_id     = kwargs.get("product_id"),
        quantity       = kwargs.get("quantity"),
        new_status     = kwargs.get("new_status"),
        orders         = None,
        products       = None,
        alerts         = None,
        summary        = None,
        alert_sent     = False,
        errors         = [],
        status_pipeline = "pending",
    )
    return build_graph().invoke(initial_state)