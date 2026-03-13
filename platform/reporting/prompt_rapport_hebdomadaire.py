"""
prompt_rapport_hebdomadaire.py — Rapport hebdomadaire MCO NetApp (vendredi 17h00)
CG CONSEIL — Destinataire : Scaprim (si-scaprim@scaprim.com + benjamin.pernin@scaprim.com)

Flux :
  1. Collecte SSH ONTAP via OntapSSHCollector (fenêtre 7 jours)
  2. Qualification EMS via ems_matrix.json
  3. Appel Claude API → rapport professionnel 1 page
  4. Affichage console (+ optionnel : écriture fichier)

Usage :
  python prompt_rapport_hebdomadaire.py
  python prompt_rapport_hebdomadaire.py --output /tmp/rapport_semaine_S11.md
  python prompt_rapport_hebdomadaire.py --dry-run   # sans appel Claude
  python prompt_rapport_hebdomadaire.py --mock      # données fictives
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
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

# ── Destinataires ──────────────────────────────────────────────────────────────
DESTINATAIRES = [
    "si-scaprim@scaprim.com",
    "benjamin.pernin@scaprim.com",
]


# ── Qualification EMS ──────────────────────────────────────────────────────────

def load_ems_matrix() -> list[dict]:
    with open(EMS_MATRIX_PATH, encoding="utf-8") as f:
        return json.load(f)["rules"]


def qualify_ems_events(events: list[dict], matrix: list[dict]) -> list[dict]:
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


def count_by_category(qualified_ems: list[dict]) -> dict:
    """Compte les événements actifs par catégorie."""
    counts: dict = {}
    for e in qualified_ems:
        q = e.get("qualification")
        if not q or q.get("action") == "ignore":
            continue
        cat = q.get("category", "autre")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


# ── Collecte des données ───────────────────────────────────────────────────────

def collect_ontap_data() -> dict:
    """Collecte toutes les données ONTAP via SSH (fenêtre 7 jours pour les EMS)."""
    sys.path.insert(0, str(BASE_DIR / "collector"))
    from ssh_collector import OntapSSHCollector

    host = os.environ["ONTAP_SSH_HOST"]
    user = os.environ["ONTAP_SSH_USER"]
    password = os.environ["ONTAP_SSH_PASSWORD"]
    port = int(os.environ.get("ONTAP_SSH_PORT", "22"))

    logger.info("Connexion SSH ONTAP %s@%s:%s", user, host, port)
    with OntapSSHCollector(host=host, username=user, password=password, port=port) as c:
        data = c.collect_all(ems_hours_back=168, ems_min_severity="warning")  # 7 jours

    logger.info("Collecte terminée — %d événements EMS (7j)", len(data.get("ems_events", [])))
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
    """Sérialise les données de la semaine en contexte lisible pour Claude."""
    now = datetime.now()
    semaine = now.isocalendar()[1]
    date_debut = (now - timedelta(days=6)).strftime("%d/%m/%Y")
    date_fin = now.strftime("%d/%m/%Y")

    # EMS — statistiques semaine
    ems_actifs = [
        e for e in qualified_ems
        if e.get("qualification") and e["qualification"].get("action") != "ignore"
    ]
    ems_ignores = len(qualified_ems) - len(ems_actifs)
    by_category = count_by_category(qualified_ems)
    by_severity = {}
    for e in ems_actifs:
        sev = e["qualification"].get("severity", "?")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    # Capacité agrégats
    aggr_list = data.get("aggregates", [])

    # SnapMirror
    sm_list = data.get("snapmirror_relations", [])
    sm_ok = [s for s in sm_list if s.get("state", "") == "snapmirrored" and float(s.get("lag_hours", 0)) <= 4]
    sm_ko = [s for s in sm_list if s not in sm_ok]

    # Disques
    disk_list = data.get("disks", [])
    disk_ko = [d for d in disk_list if d.get("state", "").lower() not in ("present", "ok", "")]

    ctx_parts = [
        f"PÉRIODE : Semaine S{semaine} — du {date_debut} au {date_fin}",
        f"CLIENT : Twenty Two Real Estate",
        f"CLUSTER : [CLUSTER] (ONTAP {data.get('version', 'N/A')})",
        f"INFRASTRUCTURE : 22 To, ~50 VMs, cluster bi-nœud",
        "",
        "=== BILAN EMS (7 jours) ===",
        f"Total événements : {len(qualified_ems)} | Actifs : {len(ems_actifs)} | Ignorés : {ems_ignores}",
        f"Par sévérité : {json.dumps(by_severity, ensure_ascii=False)}",
        f"Par catégorie : {json.dumps(by_category, ensure_ascii=False)}",
        "",
        "Détail des événements actifs (triés par priorité) :",
    ]

    priority_order = {"highest": 0, "high": 1, "medium": 2, "low": 3}
    ems_sorted = sorted(
        ems_actifs,
        key=lambda e: priority_order.get(e["qualification"].get("priority", "low"), 9)
    )
    for e in ems_sorted[:20]:  # max 20 pour ne pas saturer le contexte
        q = e["qualification"]
        ctx_parts.append(
            f"  [{q['severity']}] {e.get('message_name', e.get('message', '?'))} "
            f"— {q['message_fr']} (priorité: {q['priority']})"
        )
    if len(ems_actifs) > 20:
        ctx_parts.append(f"  ... et {len(ems_actifs) - 20} événements supplémentaires")

    ctx_parts += [
        "",
        "=== CAPACITÉ AGRÉGATS (état actuel) ===",
    ]
    for a in aggr_list:
        used_pct = float(a.get("used_pct", 0))
        tendance = "⚠ CRITIQUE" if used_pct >= 90 else ("SURVEILLER" if used_pct >= 80 else "OK")
        ctx_parts.append(
            f"  {a.get('name', '?')} — {used_pct:.0f}% utilisé "
            f"({a.get('used_size', '?')} / {a.get('total_size', '?')}) — {tendance}"
        )

    ctx_parts += [
        "",
        "=== RÉPLICATION PRA (SnapMirror) ===",
        f"Relations OK (lag ≤4h) : {len(sm_ok)} | En anomalie : {len(sm_ko)}",
    ]
    for s in sm_ko:
        ctx_parts.append(
            f"  KO — {s.get('destination_volume', '?')} — état: {s.get('state', '?')} "
            f"— lag: {s.get('lag_hours', '?')}h"
        )

    ctx_parts += [
        "",
        "=== DISQUES ===",
        f"Total : {len(disk_list)} | Anomalies : {len(disk_ko)}",
    ]
    for d in disk_ko:
        ctx_parts.append(
            f"  {d.get('name', '?')} — état: {d.get('state', '?')} — type: {d.get('type', '?')}"
        )
    if not disk_ko:
        ctx_parts.append("  Aucune anomalie disque détectée.")

    return "\n".join(ctx_parts)


# ── Prompt Claude ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es Christian Grau, consultant expert NetApp ONTAP (CG CONSEIL).
Tu rédiges le rapport MCO hebdomadaire destiné au client Scaprim (gestionnaire immobilier).

Règles strictes :
- Ton : professionnel, valorisant, vulgarisé (pas de jargon technique brut)
- Longueur : maximum 1 page (≈ 400-500 mots)
- Format : Markdown structuré, lisible par un DSI non-technicien
- Valorise les actions MCO réalisées : chaque alerte traitée = une action de maintenance proactive
- Traduis les métriques techniques en impact métier (disponibilité, sécurité des données, PRA)
- Si tout va bien : dis-le clairement et positivement
- Évite les anglicismes techniques non expliqués"""

USER_PROMPT_TEMPLATE = """Voici les données de supervision de la semaine S{semaine} pour l'infrastructure NetApp de Scaprim :

{context}

Génère le rapport hebdomadaire MCO avec ces sections :

1. **Bilan de la semaine** (2-3 lignes, ton positif, état global)
2. **Indicateurs clés**
   - Disponibilité de l'infrastructure
   - État de la protection des données (backups, PRA)
   - Capacité de stockage
3. **Événements et actions réalisées** (synthèse valorisante des interventions MCO)
4. **Tendances et surveillance** (points à surveiller la semaine prochaine)
5. **Recommandations** (1-3 actions concrètes, ordonnées par priorité)

Rappel : ce rapport est envoyé à {destinataires}
Période : {date_debut} au {date_fin}
Numéro de semaine : S{semaine}"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Rapport hebdomadaire MCO NetApp — Scaprim"
    )
    parser.add_argument("--output", help="Fichier de sortie Markdown (.md)")
    parser.add_argument("--dry-run", action="store_true", help="Sans appel Claude API")
    parser.add_argument(
        "--mock", action="store_true",
        help="Utilise des données fictives (sans connexion ONTAP)"
    )
    args = parser.parse_args()

    # Collecte
    if args.mock:
        logger.info("Mode mock — données fictives (7 jours)")
        data = {
            "version": "9.17.1P2",
            "ems_events": [
                {"message_name": "snapvault.src.snap.miss", "severity": "error", "time": "2026-03-10 07:01"},
                {"message_name": "dns.timeout", "severity": "error", "time": "2026-03-11 06:45"},
                {"message_name": "net.tcp.badChecksum", "severity": "warning", "time": "2026-03-12 14:20"},
                {"message_name": "monitor.temp.ok", "severity": "warning", "time": "2026-03-13 06:30"},
                {"message_name": "snapmirror.lag.warn", "severity": "warning", "time": "2026-03-09 02:00"},
            ],
            "aggregates": [
                {"name": "aggr0_node1", "used_pct": "72", "used_size": "16 TB", "total_size": "22 TB"},
                {"name": "aggr0_node2", "used_pct": "68", "used_size": "15 TB", "total_size": "22 TB"},
            ],
            "snapmirror_relations": [
                {"destination_volume": "vol_vm_pra", "state": "snapmirrored", "lag_hours": "1.5"},
                {"destination_volume": "vol_data_pra", "state": "snapmirrored", "lag_hours": "2.1"},
            ],
            "disks": [],
        }
    else:
        data = collect_ontap_data()

    # Qualification EMS
    matrix = load_ems_matrix()
    qualified_ems = qualify_ems_events(data.get("ems_events", []), matrix)

    # Anonymisation
    data_anon = anonymize_data(data)
    qualified_anon = qualify_ems_events(
        data_anon.get("ems_events", []), matrix
    )

    # Contexte
    context = build_context(data_anon, qualified_anon)

    if args.dry_run:
        print("=== [DRY-RUN] CONTEXTE ENVOYÉ À CLAUDE ===")
        print(context)
        print("\n=== DESTINATAIRES ===")
        print("\n".join(DESTINATAIRES))
        return

    # Appel Claude API
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY non définie dans .env")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    now = datetime.now()
    semaine = now.isocalendar()[1]
    date_debut = (now - timedelta(days=6)).strftime("%d/%m/%Y")
    date_fin = now.strftime("%d/%m/%Y")

    logger.info("Génération du rapport hebdomadaire via Claude API (claude-sonnet-4-20250514)…")
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    context=context,
                    semaine=semaine,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    destinataires=", ".join(DESTINATAIRES),
                ),
            }
        ],
    )

    rapport = message.content[0].text
    header = (
        f"# Rapport Hebdomadaire MCO — Semaine S{semaine}\n"
        f"_Période : {date_debut} au {date_fin}_\n"
        f"_Destinataires : {', '.join(DESTINATAIRES)}_\n"
        f"_Généré le {now.strftime('%d/%m/%Y à %H:%M')} par CG CONSEIL_\n\n"
    )
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
