"""
veeam_collector.py — Collecte des jobs Veeam Backup & Replication
CG CONSEIL — Plateforme MCO NetApp

Collecte le statut des sessions de sauvegarde Veeam via l'API REST
(Veeam Backup & Replication v12+).
"""

import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Mapping résultat Veeam → criticité interne
RESULT_TO_SEVERITY = {
    "None": "ok",
    "Success": "ok",
    "Warning": "warning",
    "Failed": "critical",
}


class VeeamCollector:
    """Collecte les sessions de sauvegarde Veeam via REST API v1.2."""

    def __init__(self, server_url: str, username: str, password: str, verify_ssl: bool = True):
        self.base_url = f"{server_url}/api/v1"
        self.verify_ssl = verify_ssl
        self._username = username
        self._password = password
        self.client = httpx.Client(verify=verify_ssl, timeout=30.0)
        self._token: str | None = None

    def authenticate(self) -> None:
        """Obtient un token Bearer depuis l'API Veeam."""
        resp = self.client.post(
            f"{self.base_url}/token",
            data={
                "grant_type": "password",
                "username": self._username,
                "password": self._password,
            },
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self._token}"})
        logger.info("Veeam: authentification réussie")

    def collect_sessions(self, hours_back: int = 24) -> list[dict]:
        """
        Collecte les sessions de sauvegarde des dernières N heures.

        Returns:
            Liste des sessions enrichies avec sévérité calculée
        """
        if not self._token:
            self.authenticate()

        since = (datetime.utcnow() - timedelta(hours=hours_back)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )

        try:
            resp = self.client.get(
                f"{self.base_url}/sessions",
                params={"createdAfter": since, "limit": 500, "offset": 0},
            )
            resp.raise_for_status()
            sessions = resp.json().get("data", [])
            logger.info(f"Veeam: {len(sessions)} sessions collectées")
            return [self._enrich(s) for s in sessions]
        except httpx.HTTPError as e:
            logger.error(f"Erreur collecte Veeam : {e}")
            raise

    def _enrich(self, session: dict) -> dict:
        """Ajoute la sévérité métier et masque les données sensibles."""
        result = session.get("result", {}).get("result", "None")
        session["severity"] = RESULT_TO_SEVERITY.get(result, "unknown")
        session["is_failed"] = session["severity"] == "critical"
        # Anonymisation du nom de job (supprime préfixe client éventuel)
        name = session.get("name", "")
        session["name"] = name.split("_", 1)[-1] if "_" in name else name
        return session

    def close(self):
        self.client.close()
