"""
asup_parser.py — Parseur de rapports AutoSupport NetApp
CG CONSEIL — Plateforme MCO NetApp

Parse les rapports AutoSupport (ASUP) reçus par email ou déposés sur un
répertoire partagé. Extrait les métriques clés pour alimentation du RAG
et génération de rapports.
"""

import re
import logging
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ASUPReport:
    cluster_id: str = ""          # ID anonymisé du cluster
    generated_at: str = ""
    ontap_version: str = ""
    node_count: int = 0
    aggregate_usage: list[dict] = field(default_factory=list)
    volume_alerts: list[dict] = field(default_factory=list)
    disk_failures: list[str] = field(default_factory=list)
    ems_summary: dict = field(default_factory=dict)
    raw_sections: dict = field(default_factory=dict)


class ASUPParser:
    """
    Parse un fichier AutoSupport texte et extrait les sections pertinentes.

    AutoSupport peut être reçu en format texte brut (email) ou XML.
    Ce parseur cible le format texte.
    """

    # Patterns de sections ASUP standard
    SECTION_PATTERN = re.compile(r"^={3,}\s*(.+?)\s*={3,}$", re.MULTILINE)
    AGGREGATE_PATTERN = re.compile(
        r"(\S+)\s+(\d+)GB\s+(\d+)GB\s+(\d+)%", re.MULTILINE
    )
    VERSION_PATTERN = re.compile(r"ONTAP[- ]Release\s+([\d.]+[A-Z0-9]*)", re.IGNORECASE)

    def parse_file(self, path: str | Path) -> ASUPReport:
        """Parse un fichier ASUP et retourne un rapport structuré."""
        content = Path(path).read_text(encoding="utf-8", errors="replace")
        report = ASUPReport()
        report.cluster_id = self._generate_anonymous_id(str(path))
        report.raw_sections = self._split_sections(content)

        report.ontap_version = self._extract_version(content)
        report.aggregate_usage = self._extract_aggregate_usage(content)
        report.volume_alerts = self._extract_volume_alerts(content)
        report.disk_failures = self._extract_disk_failures(content)

        logger.info(
            f"ASUP parsé : {len(report.raw_sections)} sections, "
            f"ONTAP {report.ontap_version}, "
            f"{len(report.aggregate_usage)} agrégats"
        )
        return report

    def _split_sections(self, content: str) -> dict[str, str]:
        sections = {}
        parts = self.SECTION_PATTERN.split(content)
        for i in range(1, len(parts) - 1, 2):
            sections[parts[i].strip()] = parts[i + 1].strip()
        return sections

    def _extract_version(self, content: str) -> str:
        m = self.VERSION_PATTERN.search(content)
        return m.group(1) if m else "unknown"

    def _extract_aggregate_usage(self, content: str) -> list[dict]:
        results = []
        for m in self.AGGREGATE_PATTERN.finditer(content):
            results.append({
                "aggregate": f"aggr_{hash(m.group(1)) % 9999:04d}",  # anonymisé
                "total_gb": int(m.group(2)),
                "used_gb": int(m.group(3)),
                "percent_used": int(m.group(4)),
                "alert": int(m.group(4)) >= 80,
            })
        return results

    def _extract_volume_alerts(self, content: str) -> list[dict]:
        # Cherche les volumes > 90% dans le contenu ASUP
        alerts = []
        pattern = re.compile(r"(\S+)\s+(\d{2,3})%\s+(?:full|used)", re.IGNORECASE)
        for m in pattern.finditer(content):
            if int(m.group(2)) >= 90:
                alerts.append({"volume": f"vol_{hash(m.group(1)) % 9999:04d}", "percent": int(m.group(2))})
        return alerts

    def _extract_disk_failures(self, content: str) -> list[str]:
        pattern = re.compile(r"disk\s+\S+\s+(?:failed|broken|removed)", re.IGNORECASE)
        return [f"disk_event_{i}" for i, _ in enumerate(pattern.finditer(content))]

    def _generate_anonymous_id(self, path: str) -> str:
        return f"cluster_{abs(hash(path)) % 9999:04d}"
