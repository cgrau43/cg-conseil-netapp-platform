"""
ems_collector.py — Collecte des événements EMS via ONTAP REST API
CG CONSEIL — Plateforme MCO NetApp

Collecte les événements EMS (Event Management System) depuis un cluster
ONTAP via l'API REST. Les données sont anonymisées avant stockage.
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class EMSCollector:
    """Collecte les événements EMS depuis ONTAP REST API."""

    def __init__(self, cluster_url: str, username: str, password: str, verify_ssl: bool = True):
        self.base_url = f"{cluster_url}/api"
        self.auth = (username, password)
        self.verify_ssl = verify_ssl
        self.client = httpx.Client(
            auth=self.auth,
            verify=self.verify_ssl,
            timeout=30.0,
            headers={"Accept": "application/json"},
        )

    def collect(self, hours_back: int = 24, min_severity: str = "warning") -> list[dict]:
        """
        Collecte les événements EMS des dernières N heures.

        Args:
            hours_back: Fenêtre temporelle de collecte (défaut : 24h)
            min_severity: Sévérité minimale — emergency, alert, error, warning, notice

        Returns:
            Liste d'événements EMS enrichis et anonymisés
        """
        since = (datetime.utcnow() - timedelta(hours=hours_back)).strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "time.>": since,
            "severity": min_severity,
            "fields": "time,severity,message,node,log_message",
            "max_records": 1000,
            "order_by": "time desc",
        }

        try:
            resp = self.client.get(f"{self.base_url}/support/ems/events", params=params)
            resp.raise_for_status()
            records = resp.json().get("records", [])
            logger.info(f"EMS: {len(records)} événements collectés (last {hours_back}h)")
            return [self._anonymize(r) for r in records]
        except httpx.HTTPError as e:
            logger.error(f"Erreur collecte EMS : {e}")
            raise

    def _anonymize(self, event: dict) -> dict:
        """Anonymise les champs sensibles d'un événement EMS."""
        event.pop("node", None)  # supprime hostname du node
        message = event.get("log_message", "")
        # Masque les IPs (simpliste — à remplacer par regex robuste)
        import re
        event["log_message"] = re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", "[IP_MASQUÉE]", message)
        return event

    def close(self):
        self.client.close()
