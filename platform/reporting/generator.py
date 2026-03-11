"""
generator.py — Générateur de rapports MCO NetApp
CG CONSEIL — Plateforme MCO NetApp

Génère les rapports (journalier, mensuel, PRA) en combinant :
- Les données collectées (EMS, SnapCenter, Veeam)
- Les templates Markdown
- L'IA Claude pour la synthèse et les recommandations
"""

import logging
from datetime import datetime
from pathlib import Path
from string import Template

import anthropic

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


class ReportGenerator:
    """Génère des rapports MCO enrichis par Claude."""

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(api_key=api_key)

    # ------------------------------------------------------------------ #
    # Rapports                                                             #
    # ------------------------------------------------------------------ #

    def generate_daily(self, data: dict) -> str:
        """
        Génère le rapport journalier.

        Args:
            data: Dictionnaire contenant ems_events, snapcenter_jobs,
                  veeam_jobs, snapmirror_relations

        Returns:
            Rapport Markdown prêt à l'envoi (après validation humaine)
        """
        summary = self._ai_executive_summary(data, report_type="daily")
        recommendations = self._ai_recommendations(data)
        data["executive_summary"] = summary
        data["recommendations"] = recommendations
        data["date"] = datetime.now().strftime("%d/%m/%Y")
        return self._render_template("daily_report.md", data)

    def generate_monthly(self, data: dict) -> str:
        """Génère le rapport mensuel."""
        summary = self._ai_executive_summary(data, report_type="monthly")
        recommendations = self._ai_recommendations(data)
        data["executive_summary"] = summary
        data["recommendations"] = recommendations
        data["month"] = datetime.now().strftime("%B")
        data["year"] = datetime.now().year
        return self._render_template("monthly_report.md", data)

    def generate_pra(self, cifs_result: dict, nfs_result: dict, vm_result: dict) -> str:
        """Génère le rapport de test PRA."""
        all_ok = all(r.get("status") == "success" for r in [cifs_result, nfs_result, vm_result])
        data = {
            "cifs": cifs_result,
            "nfs": nfs_result,
            "vm": vm_result,
            "overall_status": "SUCCÈS" if all_ok else "ÉCHEC PARTIEL",
            "test_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "quarter": (datetime.now().month - 1) // 3 + 1,
            "year": datetime.now().year,
            "corrective_actions": self._ai_corrective_actions(cifs_result, nfs_result, vm_result),
        }
        return self._render_template("pra_report.md", data)

    # ------------------------------------------------------------------ #
    # IA — Synthèse et recommandations                                    #
    # ------------------------------------------------------------------ #

    def _ai_executive_summary(self, data: dict, report_type: str) -> str:
        """Génère une synthèse exécutive via Claude."""
        prompt = f"""
Tu es un expert MCO NetApp. Rédige une synthèse exécutive concise (5 lignes max)
pour un rapport {report_type} basé sur ces données :

{self._format_data_for_prompt(data)}

Ton professionnel, adapté à une direction PME/ETI. Anonymise tout nom propre.
"""
        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Erreur génération synthèse : {e}")
            return "Synthèse non disponible — vérifier la connexion API."

    def _ai_recommendations(self, data: dict) -> str:
        """Génère des recommandations actionnables via Claude."""
        prompt = f"""
En tant qu'expert MCO NetApp, génère 3 recommandations concrètes et actionnables
basées sur ces données d'exploitation :

{self._format_data_for_prompt(data)}

Format : liste à puces, une action par ligne, avec priorité (P1/P2/P3).
"""
        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Erreur génération recommandations : {e}")
            return "Recommandations non disponibles."

    def _ai_corrective_actions(self, *results) -> str:
        """Génère les actions correctives post-test PRA."""
        failures = [r for r in results if r.get("status") != "success"]
        if not failures:
            return "Tous les tests PRA ont réussi. Aucune action corrective requise."

        prompt = f"""
En tant qu'expert NetApp, analyse ces échecs de test PRA et génère un plan d'action :

{failures}

Format : liste numérotée avec priorité et délai recommandé.
"""
        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Erreur actions correctives : {e}")
            return "Actions correctives non générées — vérifier l'API."

    # ------------------------------------------------------------------ #
    # Rendu template                                                       #
    # ------------------------------------------------------------------ #

    def _render_template(self, template_name: str, data: dict) -> str:
        """Rend un template Markdown en substituant les variables."""
        template_path = TEMPLATES_DIR / template_name
        content = template_path.read_text(encoding="utf-8")
        # Substitution simple — remplacer par Jinja2 pour les boucles
        for key, value in data.items():
            content = content.replace(f"{{{{ {key} }}}}", str(value))
        return content

    @staticmethod
    def _format_data_for_prompt(data: dict) -> str:
        """Formate les données pour insertion dans un prompt Claude."""
        import json
        # On ne passe que les données scalaires et listes simples
        safe_data = {k: v for k, v in data.items() if not callable(v)}
        return json.dumps(safe_data, indent=2, default=str, ensure_ascii=False)[:3000]
