"""
prompt_rapport_journalier.py — Rapport journalier MCO NetApp (7h00)
CG CONSEIL — Destinataire : Christian Grau (interne)

Flux :
  1. Collecte SSH ONTAP via OntapSSHCollector
  2. Qualification EMS via ems_matrix.json
  3. Appel Claude API → rapport technique 1 page
  4. Affichage console (+ optionnel : écriture fichier)

Usage :
  python prompt_rapport_journalier.py
  python prompt_rapport_journalier.py --output /tmp/rapport_2026-03-13.md
  python prompt_rapport_journalier.py --dry-run   # sans appel Claude
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 sur stdout (Windows cp1252 sinon) — ou lancer avec: python -X utf8
import io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import anthropic
from dotenv import load_dotenv

# ── Chemins ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
EMS_MATRIX_PATH = BASE_DIR / "qualification" / "ems_matrix.json"

load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Qualification EMS ──────────────────────────────────────────────────────────

def load_ems_matrix() -> list[dict]:
    with open(EMS_MATRIX_PATH, encoding="utf-8") as f:
        return json.load(f)["rules"]


def qualify_ems_events(events: list[dict], matrix: list[dict]) -> list[dict]:
    """Enrichit chaque événement EMS avec la règle de qualification correspondante."""
    qualified = []
    for event in events:
        msg = event.get("message_name", "") or event.get("message", "")
        matched_rule = None
        for rule in matrix:
            if rule["pattern"].lower() in msg.lower():
                matched_rule = rule
                break
        event["qualification"] = matched_rule
        qualified.append(event)
    return qualified


# ── Collecte des données ───────────────────────────────────────────────────────

def collect_ontap_data() -> dict:
    """Collecte toutes les données ONTAP via SSH."""
    sys.path.insert(0, str(BASE_DIR / "collector"))
    from ssh_collector import OntapSSHCollector

    host = os.environ["ONTAP_SSH_HOST"]
    user = os.environ["ONTAP_SSH_USER"]
    password = os.environ["ONTAP_SSH_PASSWORD"]
    port = int(os.environ.get("ONTAP_SSH_PORT", "22"))

    logger.info("Connexion SSH ONTAP %s@%s:%s", user, host, port)
    with OntapSSHCollector(host=host, username=user, password=password, port=port) as c:
        data = c.collect_all(ems_hours_back=24, ems_min_severity="warning")

    logger.info("Collecte terminée — %d événements EMS", len(data.get("ems_events", [])))
    return data


# ── Anonymisation ──────────────────────────────────────────────────────────────

_RE_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_RE_HOST = re.compile(r"\b(GSP_NETAPP_PRD01|twentytwo-prod|CLUSTER_PRA_02)\b", re.IGNORECASE)


def anonymize(text: str) -> str:
    text = _RE_IP.sub("[IP]", text)
    text = _RE_HOST.sub("[CLUSTER]", text)
    return text


def anonymize_data(data: dict) -> dict:
    return json.loads(anonymize(json.dumps(data, ensure_ascii=False)))


# ── Construction du contexte pour Claude ──────────────────────────────────────

def build_context(data: dict, qualified_ems: list[dict]) -> str:
    """Sérialise les données collectées en contexte lisible pour Claude."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    # EMS — seulement les événements qualifiés non-ignorés
    ems_actifs = [
        e for e in qualified_ems
        if e.get("qualification") and e["qualification"].get("action") != "ignore"
    ]
    ems_ignores = len(qualified_ems) - len(ems_actifs)

    # Capacité agrégats
    aggr_list = data.get("aggregates", [])
    aggr_critical = [a for a in aggr_list if float(a.get("used_pct", 0)) >= 90]

    # SnapMirror
    sm_list = data.get("snapmirror_relations", [])
    sm_lag_warn = [s for s in sm_list if float(s.get("lag_hours", 0)) > 4]

    # Disques
    disk_list = data.get("disks", [])
    disk_ko = [d for d in disk_list if d.get("state", "").lower() not in ("present", "ok", "")]

    ctx_parts = [
        f"DATE ET HEURE : {now}",
        f"CLIENT : Twenty Two Real Estate",
        f"CLUSTER : [CLUSTER] (ONTAP {data.get('version', 'N/A')})",
        "",
        "=== ÉVÉNEMENTS EMS (24 dernières heures) ===",
        f"Total : {len(qualified_ems)} | Actifs : {len(ems_actifs)} | Ignorés : {ems_ignores}",
    ]

    for e in ems_actifs:
        q = e["qualification"]
        ctx_parts.append(
            f"  [{q['severity']}] {e.get('message_name', e.get('message', '?'))} "
            f"— priorité {q['priority']} — {q['message_fr']}"
        )

    ctx_parts += [
        "",
        "=== CAPACITÉ AGRÉGATS ===",
        f"Total : {len(aggr_list)} agrégat(s) | Critiques (≥90%) : {len(aggr_critical)}",
    ]
    for a in aggr_list:
        flag = " ⚠" if float(a.get("used_pct", 0)) >= 90 else ""
        ctx_parts.append(
            f"  {a.get('name', '?')} — {a.get('used_pct', '?')}% utilisé "
            f"({a.get('used_size', '?')} / {a.get('total_size', '?')}){flag}"
        )

    ctx_parts += [
        "",
        "=== SNAPMIRROR / PRA ===",
        f"Total : {len(sm_list)} relation(s) | Lag > 4h : {len(sm_lag_warn)}",
    ]
    for s in sm_list:
        flag = " ⚠" if float(s.get("lag_hours", 0)) > 4 else ""
        ctx_parts.append(
            f"  {s.get('destination_volume', '?')} — état: {s.get('state', '?')} "
            f"— lag: {s.get('lag_hours', '?')}h{flag}"
        )

    ctx_parts += [
        "",
        "=== DISQUES ===",
        f"Total : {len(disk_list)} | En anomalie : {len(disk_ko)}",
    ]
    for d in disk_ko:
        ctx_parts.append(
            f"  {d.get('name', '?')} — état: {d.get('state', '?')} — type: {d.get('type', '?')}"
        )

    return "\n".join(ctx_parts)


# ── Prompt Claude ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es Christian Grau, consultant expert NetApp ONTAP (CG CONSEIL).
Tu rédiges un rapport technique journalier MCO destiné à ton usage interne.
Style : technique, concis, expert. Maximum 1 page.
Format : Markdown structuré avec sections claires.
Utilise ces indicateurs visuels dans le texte Markdown :
  - 🔴 pour les alertes critiques / actions immédiates
  - 🟠 pour les avertissements / surveiller
  - 🟢 pour les éléments OK / nominaux
Ne répète pas les données brutes : synthétise, interprète, recommande."""

USER_PROMPT_TEMPLATE = """Voici les données collectées ce matin sur le cluster NetApp de Twenty Two Real Estate :

{context}

Génère le rapport journalier MCO avec ces sections :
1. **Résumé exécutif** (3-4 lignes max, état global)
2. **Alertes EMS** (uniquement les actives, triées par priorité)
3. **Capacité** (agrégats, tendances, risques)
4. **Backup & SnapMirror** (état jobs, lag PRA)
5. **Disques** (anomalies uniquement, OK si aucune)
6. **Actions requises** (liste ordonnée par priorité)

Date du rapport : {date}"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Rapport journalier MCO NetApp — CG CONSEIL")
    parser.add_argument("--output", help="Fichier de sortie Markdown (.md)")
    parser.add_argument("--dry-run", action="store_true", help="Sans appel Claude API")
    parser.add_argument(
        "--mock", action="store_true",
        help="Utilise des données fictives (sans connexion ONTAP)"
    )
    args = parser.parse_args()

    # Collecte
    if args.mock:
        logger.info("Mode mock — données fictives")
        data = {
            "version": "9.17.1P2",
            "ems_events": [
                {"message_name": "snapvault.src.snap.miss", "severity": "error", "time": "07:01"},
                {"message_name": "dns.timeout", "severity": "error", "time": "06:45"},
                {"message_name": "monitor.temp.ok", "severity": "warning", "time": "06:30"},
            ],
            "aggregates": [
                {"name": "aggr0_node1", "used_pct": "72", "used_size": "16 TB", "total_size": "22 TB"},
                {"name": "aggr0_node2", "used_pct": "68", "used_size": "15 TB", "total_size": "22 TB"},
            ],
            "snapmirror_relations": [
                {"destination_volume": "vol_vm_pra", "state": "snapmirrored", "lag_hours": "1.5"},
                {"destination_volume": "vol_data_pra", "state": "snapmirrored", "lag_hours": "5.2"},
            ],
            "disks": [],
        }
    else:
        data = collect_ontap_data()

    # Qualification EMS
    matrix = load_ems_matrix()
    qualified_ems = qualify_ems_events(data.get("ems_events", []), matrix)

    # Anonymisation avant envoi Claude
    data_anon = anonymize_data(data)

    # Contexte
    context = build_context(data_anon, qualify_ems_events(
        data_anon.get("ems_events", []), matrix
    ))

    if args.dry_run:
        print("=== [DRY-RUN] CONTEXTE ENVOYÉ À CLAUDE ===")
        print(context)
        return

    # Appel Claude API
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY non définie dans .env")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    date_str = datetime.now().strftime("%d/%m/%Y")

    logger.info("Génération du rapport via Claude API (claude-sonnet-4-20250514)…")
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(context=context, date=date_str),
            }
        ],
    )

    rapport = message.content[0].text
    header = f"# Rapport Journalier MCO — {date_str}\n_Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}_\n\n"
    rapport_final = header + rapport

    # Sortie
    if args.output:
        Path(args.output).write_text(rapport_final, encoding="utf-8")
        logger.info("Rapport écrit : %s", args.output)
    else:
        print(rapport_final)

    logger.info(
        "Terminé — tokens utilisés : input=%d output=%d",
        message.usage.input_tokens,
        message.usage.output_tokens,
    )


if __name__ == "__main__":
    main()
