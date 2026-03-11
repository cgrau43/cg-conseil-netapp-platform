"""
alerts.py — Endpoint alertes enrichies
CG CONSEIL — Plateforme MCO NetApp

Expose les alertes qualifiées et enrichies par IA.
Consommé par n8n pour les workflows d'alerte enrichie.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class AlertSummary(BaseModel):
    event_id: str
    source: str          # ems | snapcenter | veeam
    timestamp: str
    business_level: str  # P1 | P2 | P3 | P4 | INFO
    category: str
    message: str
    needs_alert: bool
    auto_action: str | None = None
    kb_refs: list[str] = []


class AlertContext(BaseModel):
    event_id: str
    kb_snippets: list[dict]
    working_instructions: list[dict]
    similar_incidents: list[dict]


class AlertAnalysis(BaseModel):
    event_id: str
    summary: str
    root_cause_hypothesis: str
    recommended_action: str
    urgency: str
    context_used: int


@router.get("/alerts", response_model=list[AlertSummary], summary="Liste des alertes actives")
async def get_alerts(
    source: str | None = Query(None, description="Filtre par source : ems, snapcenter, veeam"),
    hours: int = Query(24, ge=1, le=168, description="Fenêtre temporelle en heures"),
    min_level: str = Query("P4", description="Niveau minimum : P1, P2, P3, P4"),
) -> list[AlertSummary]:
    """
    Retourne les alertes actives qualifiées des dernières N heures.
    Filtrables par source et niveau de criticité.
    """
    # TODO: Brancher sur le qualifier + collecteurs réels
    # Données de démonstration
    demo_alerts = [
        AlertSummary(
            event_id="ems-001",
            source="ems",
            timestamp=datetime.utcnow().isoformat(),
            business_level="P3",
            category="storage",
            message="Volume aggr_0042/vol_0012 à 88% de capacité",
            needs_alert=True,
            auto_action="check_volume_autosize",
            kb_refs=["KB000789"],
        )
    ]

    if source:
        demo_alerts = [a for a in demo_alerts if a.source == source]

    return demo_alerts


@router.get("/alerts/{event_id}/context", response_model=AlertContext, summary="Contexte RAG d'une alerte")
async def get_alert_context(event_id: str) -> AlertContext:
    """
    Retourne le contexte RAG (articles KB, procédures, incidents similaires)
    associé à un événement. Utilisé pour enrichir l'analyse IA.
    """
    # TODO: Brancher sur le Retriever RAG
    return AlertContext(
        event_id=event_id,
        kb_snippets=[],
        working_instructions=[],
        similar_incidents=[],
    )


@router.post("/alerts/analyze", response_model=AlertAnalysis, summary="Analyse IA d'une alerte")
async def analyze_alert(
    event: dict = Body(..., description="Événement qualifié"),
    context: dict = Body(..., description="Contexte RAG"),
) -> AlertAnalysis:
    """
    Génère une analyse enrichie d'une alerte via Claude.
    Combine l'événement qualifié et le contexte RAG pour produire
    un diagnostic et une recommandation actionnables.
    """
    import os
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""
Tu es un expert MCO NetApp. Analyse cet événement et fournis :
1. Un résumé en 1 phrase
2. Une hypothèse de cause racine
3. L'action recommandée immédiate

Événement : {event}
Contexte KB : {context}

Réponds en JSON avec les clés : summary, root_cause_hypothesis, recommended_action, urgency (immediate/today/this_week).
"""
    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        analysis = json.loads(response.content[0].text)
    except Exception as e:
        logger.error(f"Erreur analyse IA : {e}")
        analysis = {
            "summary": event.get("message", "Événement non analysé"),
            "root_cause_hypothesis": "Analyse IA indisponible",
            "recommended_action": event.get("auto_action", "Vérification manuelle requise"),
            "urgency": "today",
        }

    return AlertAnalysis(
        event_id=event.get("event_id", ""),
        context_used=len(context.get("kb_snippets", [])),
        **analysis,
    )
