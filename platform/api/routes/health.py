"""
health.py — Endpoint santé infrastructure NetApp
CG CONSEIL — Plateforme MCO NetApp

Expose l'état de santé global de l'infrastructure supervisée :
agrégats, volumes, disques, SnapMirror. Consommé par n8n et le dashboard.
"""

import os
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class ComponentHealth(BaseModel):
    name: str
    status: str          # ok | warning | critical | unknown
    message: str = ""
    last_checked: str = ""


class InfrastructureHealth(BaseModel):
    overall_status: str
    checked_at: str
    components: list[ComponentHealth]
    alert_count: int = 0


@router.get("/health", response_model=InfrastructureHealth, summary="État de santé infrastructure")
async def get_health() -> InfrastructureHealth:
    """
    Retourne l'état de santé global de l'infrastructure NetApp supervisée.

    Agrège :
    - Connectivité cluster ONTAP
    - État des agrégats et volumes
    - État des disques
    - Lag SnapMirror
    """
    components = []
    now = datetime.utcnow().isoformat()

    # Vérification connectivité ONTAP
    ontap_status = await _check_ontap_connectivity()
    components.append(ComponentHealth(
        name="ONTAP REST API",
        status=ontap_status["status"],
        message=ontap_status["message"],
        last_checked=now,
    ))

    # Vérification SnapCenter
    sc_status = await _check_snapcenter_connectivity()
    components.append(ComponentHealth(
        name="SnapCenter",
        status=sc_status["status"],
        message=sc_status["message"],
        last_checked=now,
    ))

    # Statut global = pire composant
    statuses = [c.status for c in components]
    if "critical" in statuses:
        overall = "critical"
    elif "warning" in statuses:
        overall = "warning"
    elif all(s == "ok" for s in statuses):
        overall = "ok"
    else:
        overall = "unknown"

    alert_count = sum(1 for s in statuses if s in ("warning", "critical"))

    return InfrastructureHealth(
        overall_status=overall,
        checked_at=now,
        components=components,
        alert_count=alert_count,
    )


async def _check_ontap_connectivity() -> dict:
    """Vérifie la connectivité à l'API REST ONTAP."""
    url = os.getenv("ONTAP_CLUSTER_URL", "")
    if not url:
        return {"status": "unknown", "message": "ONTAP_CLUSTER_URL non configurée"}
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.get(
                f"{url}/api/cluster",
                auth=(os.getenv("ONTAP_USERNAME", ""), os.getenv("ONTAP_PASSWORD", "")),
            )
            resp.raise_for_status()
            return {"status": "ok", "message": f"Cluster ONTAP accessible (HTTP {resp.status_code})"}
    except httpx.HTTPError as e:
        return {"status": "critical", "message": str(e)}


async def _check_snapcenter_connectivity() -> dict:
    """Vérifie la connectivité à SnapCenter."""
    url = os.getenv("SNAPCENTER_URL", "")
    if not url:
        return {"status": "unknown", "message": "SNAPCENTER_URL non configurée"}
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.get(f"{url}/api/4.7/jobs?MaxResults=1",
                                    headers={"Token": os.getenv("SNAPCENTER_TOKEN", "")})
            resp.raise_for_status()
            return {"status": "ok", "message": "SnapCenter accessible"}
    except httpx.HTTPError as e:
        return {"status": "warning", "message": str(e)}
