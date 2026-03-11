"""
qualifier.py — Requalification métier des événements
CG CONSEIL — Plateforme MCO NetApp

Enrichit les événements bruts (EMS, SnapCenter, Veeam) avec :
- Criticité métier (P1→P4)
- Catégorie fonctionnelle (storage, backup, pra, ha)
- Action recommandée
- Contexte RAG (articles KB associés)
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

RULES_DIR = Path(__file__).parent / "rules"
MATRIX_PATH = Path(__file__).parent / "ems_matrix.json"


@dataclass
class QualifiedEvent:
    source: str                    # ems | snapcenter | veeam
    event_id: str
    timestamp: str
    severity_raw: str              # sévérité d'origine
    business_level: str = "INFO"   # P1 / P2 / P3 / P4 / INFO
    category: str = "unknown"      # storage / backup / pra / ha
    auto_action: str | None = None
    kb_refs: list[str] = field(default_factory=list)
    message: str = ""
    needs_alert: bool = False
    raw: dict = field(default_factory=dict)


class Qualifier:
    """Requalifie les événements bruts en événements métier enrichis."""

    def __init__(self):
        self.matrix = self._load_json(MATRIX_PATH)
        self.storage_rules = self._load_json(RULES_DIR / "storage_rules.json")
        self.backup_rules = self._load_json(RULES_DIR / "backup_rules.json")
        self.pra_rules = self._load_json(RULES_DIR / "pra_rules.json")

    def qualify_ems(self, events: list[dict]) -> list[QualifiedEvent]:
        """Requalifie une liste d'événements EMS."""
        return [self._qualify_single_ems(e) for e in events]

    def qualify_backup_job(self, jobs: list[dict], source: str = "snapcenter") -> list[QualifiedEvent]:
        """Requalifie les jobs de sauvegarde (SnapCenter ou Veeam)."""
        return [self._qualify_single_job(j, source) for j in jobs]

    def _qualify_single_ems(self, event: dict) -> QualifiedEvent:
        event_name = event.get("message", {}).get("name", "")
        raw_severity = event.get("severity", "NOTICE").upper()

        known = self.matrix.get("known_events", {}).get(event_name, {})
        severity = known.get("severity_override", raw_severity)
        level_info = self.matrix.get("severity_levels", {}).get(severity, {})

        return QualifiedEvent(
            source="ems",
            event_id=event.get("index", ""),
            timestamp=event.get("time", ""),
            severity_raw=raw_severity,
            business_level=level_info.get("business_level", "INFO"),
            category=known.get("category", "storage"),
            auto_action=known.get("auto_action"),
            kb_refs=[known["kb_ref"]] if known.get("kb_ref") else [],
            message=event.get("log_message", ""),
            needs_alert=level_info.get("auto_alert", False),
            raw=event,
        )

    def _qualify_single_job(self, job: dict, source: str) -> QualifiedEvent:
        is_failed = job.get("is_failed", False)
        rules = self.backup_rules.get("failure_levels", {})

        business_level = "P3" if is_failed else "INFO"
        # Escalade P2 si job critique (défini dans backup_rules)
        job_name = job.get("name", "")
        for critical_pattern in rules.get("p2_patterns", []):
            if critical_pattern.lower() in job_name.lower():
                business_level = "P2"
                break

        return QualifiedEvent(
            source=source,
            event_id=job.get("id", ""),
            timestamp=job.get("creationTime", job.get("StartTime", "")),
            severity_raw="FAILED" if is_failed else "OK",
            business_level=business_level,
            category="backup",
            needs_alert=is_failed,
            message=job.get("result", {}).get("message", "") if source == "veeam" else job.get("Status", ""),
            raw=job,
        )

    @staticmethod
    def _load_json(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Impossible de charger {path} : {e}")
            return {}
