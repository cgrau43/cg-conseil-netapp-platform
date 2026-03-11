"""
reports.py — Endpoint génération de rapports
CG CONSEIL — Plateforme MCO NetApp

Expose les endpoints de génération de rapports (journalier, mensuel, PRA).
Consommé par les workflows n8n et éventuellement un frontend.
"""

import logging
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class ReportResponse(BaseModel):
    report_type: str
    generated_at: str
    report: str           # Contenu Markdown du rapport
    word_count: int
    validation_required: bool = True


@router.post("/reports/daily", response_model=ReportResponse, summary="Génération rapport journalier")
async def generate_daily_report(
    data: dict = Body(..., description="Données EMS, backup, SnapMirror des 24 dernières heures"),
) -> ReportResponse:
    """
    Génère le rapport journalier MCO à partir des données collectées.
    Utilise Claude pour la synthèse exécutive et les recommandations.
    Validation humaine requise avant envoi.
    """
    try:
        from platform.reporting.generator import ReportGenerator
        generator = ReportGenerator(api_key=os.getenv("ANTHROPIC_API_KEY"))
        report_content = generator.generate_daily(data)
    except Exception as e:
        logger.error(f"Erreur génération rapport journalier : {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return ReportResponse(
        report_type="daily",
        generated_at=datetime.utcnow().isoformat(),
        report=report_content,
        word_count=len(report_content.split()),
        validation_required=True,
    )


@router.post("/reports/monthly", response_model=ReportResponse, summary="Génération rapport mensuel")
async def generate_monthly_report(
    data: dict = Body(..., description="Données mensuelles consolidées"),
) -> ReportResponse:
    """
    Génère le rapport mensuel MCO.
    """
    try:
        from platform.reporting.generator import ReportGenerator
        generator = ReportGenerator(api_key=os.getenv("ANTHROPIC_API_KEY"))
        report_content = generator.generate_monthly(data)
    except Exception as e:
        logger.error(f"Erreur génération rapport mensuel : {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return ReportResponse(
        report_type="monthly",
        generated_at=datetime.utcnow().isoformat(),
        report=report_content,
        word_count=len(report_content.split()),
        validation_required=True,
    )


@router.post("/reports/pra", response_model=ReportResponse, summary="Génération rapport test PRA")
async def generate_pra_report(
    cifs_result: dict = Body(...),
    nfs_result: dict = Body(...),
    vm_result: dict = Body(...),
) -> ReportResponse:
    """
    Génère le rapport de test PRA trimestriel à partir des résultats
    des tests de restauration automatisés.
    """
    try:
        from platform.reporting.generator import ReportGenerator
        generator = ReportGenerator(api_key=os.getenv("ANTHROPIC_API_KEY"))
        report_content = generator.generate_pra(cifs_result, nfs_result, vm_result)
    except Exception as e:
        logger.error(f"Erreur génération rapport PRA : {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return ReportResponse(
        report_type="pra",
        generated_at=datetime.utcnow().isoformat(),
        report=report_content,
        word_count=len(report_content.split()),
        validation_required=True,
    )
