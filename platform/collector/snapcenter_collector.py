"""
snapcenter_collector.py — Collecte des jobs SnapCenter via REST API
CG CONSEIL — Plateforme MCO NetApp

Collecte le statut des jobs de sauvegarde et de restauration SnapCenter.
Permet de détecter les échecs, les jobs longs et les anomalies de rétention.
"""

import httpx
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    COMPLETED = "Completed"
    FAILED = "Failed"
    RUNNING = "Running"
    QUEUED = "Queued"
    PARTIAL = "Completed with Warnings"


class SnapCenterCollector:
    """Collecte les jobs SnapCenter via REST API."""

    def __init__(self, server_url: str, token: str, verify_ssl: bool = True):
        self.base_url = f"{server_url}/api/4.7"
        self.client = httpx.Client(
            verify=verify_ssl,
            timeout=30.0,
            headers={
                "Token": token,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    def collect_jobs(self, hours_back: int = 24) -> list[dict]:
        """
        Collecte tous les jobs SnapCenter des dernières N heures.

        Returns:
            Liste des jobs avec statut, durée, ressources concernées
        """
        since = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()

        try:
            resp = self.client.get(
                f"{self.base_url}/jobs",
                params={"StartTime": since, "MaxResults": 500},
            )
            resp.raise_for_status()
            jobs = resp.json()
            logger.info(f"SnapCenter: {len(jobs)} jobs collectés")
            return [self._enrich(j) for j in jobs]
        except httpx.HTTPError as e:
            logger.error(f"Erreur collecte SnapCenter : {e}")
            raise

    def _enrich(self, job: dict) -> dict:
        """Enrichit un job avec des métriques calculées."""
        start = job.get("StartTime")
        end = job.get("EndTime")
        if start and end:
            duration_s = (
                datetime.fromisoformat(end) - datetime.fromisoformat(start)
            ).total_seconds()
            job["duration_seconds"] = int(duration_s)
        job["is_failed"] = job.get("Status") == JobStatus.FAILED
        job["needs_attention"] = job.get("Status") in (
            JobStatus.FAILED, JobStatus.PARTIAL
        )
        return job

    def get_failed_jobs(self, hours_back: int = 24) -> list[dict]:
        """Retourne uniquement les jobs en échec."""
        return [j for j in self.collect_jobs(hours_back) if j["is_failed"]]

    def close(self):
        self.client.close()
