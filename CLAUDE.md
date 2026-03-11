# CLAUDE.md — Contexte CG CONSEIL / Plateforme MCO NetApp

Ce fichier donne à Claude le contexte complet du projet pour travailler
efficacement dans ce dépôt sans re-expliquer les bases à chaque session.

---

## Qui est CG CONSEIL ?

Bureau d'études informatique indépendant spécialisé en infrastructure NetApp.
Cible : PME / ETI disposant d'environnements NetApp ONTAP en production.

**Offre principale :** MCO (Maintien en Conditions Opérationnelles) NetApp
- Garantie de production (supervision, alertes, incidents)
- Sauvegarde (SnapCenter, Veeam)
- PRA (SnapMirror, tests de bascule trimestriels)

**Compte GitHub :** `cgrau43`
**Repo principal :** `cgrau43/cg-conseil-netapp-platform`

---

## Ce que fait cette plateforme

Supervision intelligente NetApp augmentée par IA (Claude). Elle remplace
un processus manuel de reporting mensuel qui prenait 4h par client.

**Résultat mesuré : -92% de temps de reporting (4h → < 20 min)**

Pipeline complet :
```
Collecte (ONTAP/SnapCenter/Veeam)
  → Qualification métier (P1→P4)
  → Enrichissement RAG (KB NetApp + procédures)
  → Génération rapport IA (Claude)
  → Workflow n8n (envoi, alertes, tests PRA)
```

---

## Structure du dépôt

```
cg-conseil-netapp-platform/
├── CLAUDE.md                          ← ce fichier
├── README.md                          ← présentation publique
├── 01_Vision/
│   ├── README.md
│   └── 02_Architecture/
│       └── Architecture_Technique_v1.md
├── monthly-reporting/
│   └── PROMPT_RAPPORT_MENSUEL.md      ← prompt template rapport mensuel
├── incident-analysis/
│   └── PROMPT_ANALYSE_INCIDENT.md     ← prompt template analyse incident
└── platform/                          ← code de la plateforme
    ├── README.md
    ├── docker-compose.yml
    ├── .env.example
    ├── collector/
    │   ├── ems_collector.py           ← EMS via ONTAP REST API
    │   ├── snapcenter_collector.py    ← jobs SnapCenter
    │   ├── veeam_collector.py         ← sessions Veeam B&R
    │   └── asup_parser.py             ← rapports AutoSupport
    ├── qualification/
    │   ├── ems_matrix.json            ← mapping EMS → P1/P2/P3/P4
    │   ├── qualifier.py               ← moteur de qualification
    │   └── rules/
    │       ├── storage_rules.json
    │       ├── backup_rules.json
    │       └── pra_rules.json
    ├── rag/
    │   ├── embeddings.py
    │   ├── retriever.py
    │   └── knowledge_base/
    │       ├── netapp_kb/             ← articles KB NetApp (à alimenter)
    │       ├── working_instructions/  ← procédures techniques CG CONSEIL
    │       └── incident_history/      ← historique incidents résolus
    ├── automation/
    │   ├── n8n_workflows/
    │   │   ├── daily_report.json
    │   │   ├── alert_enriched.json
    │   │   └── pra_test.json
    │   └── actions/
    │       ├── restore_test_cifs.py
    │       ├── restore_test_nfs.py
    │       └── restore_test_vm.py
    ├── reporting/
    │   ├── generator.py               ← génération via Claude API
    │   └── templates/
    │       ├── daily_report.md
    │       ├── monthly_report.md
    │       └── pra_report.md
    └── api/
        ├── main.py                    ← FastAPI
        └── routes/
            ├── health.py
            ├── alerts.py
            └── reports.py
```

---

## Stack technique

| Composant | Technologie |
|---|---|
| IA / LLM | Claude (Anthropic) — `claude-opus-4-6` |
| API plateforme | FastAPI (Python 3.11+) |
| Orchestration workflows | n8n (self-hosted) |
| Base de données | PostgreSQL 16 |
| Collecte ONTAP | ONTAP REST API (ONTAP 9.6+) |
| Collecte backup | SnapCenter REST API 4.7+ |
| Collecte backup | Veeam B&R REST API v1.2+ |
| Déploiement | Docker Compose |
| Dépendances Python | `httpx`, `fastapi`, `anthropic`, `pydantic` |

---

## Seuils métier de référence

### SnapMirror / Réplication
- Lag > 60 min → WARNING (P4)
- Lag > 4h → ALERT (P2)
- Lag > 24h → EMERGENCY (P1)

### Capacité stockage
- Volume > 80% → WARNING
- Volume > 90% → ALERT
- Agrégat > 85% → ALERT

### Sauvegarde
- Aucun backup réussi depuis 24h → CRITICAL (P2)
- Job backup en échec sur volume prod → P2
- Job backup en échec sur volume dev/test → P3

### RTO/RPO (PRA)
- RPO cible : 4h (volumes standard), 1h (volumes critiques)
- RTO CIFS/NFS : 1h
- RTO VM : 2h

---

## Principes de sécurité — non négociables

1. **Anonymisation systématique** avant tout envoi à l'API Claude :
   IPs, hostnames, noms de clients, identifiants masqués
2. **Validation humaine obligatoire** sur tous les rapports avant envoi client
3. **Secrets hors code** : toujours dans `.env` (jamais dans le dépôt)
4. **Prompts versionnés Git** : traçabilité complète
5. **Données poussées** du client vers le VPS (jamais de connexion entrante)

---

## Conventions de code

- Python 3.11+, type hints obligatoires
- Classes avec `dataclass` pour les structures de données
- Logging avec `logging.getLogger(__name__)` — pas de `print()`
- Méthodes privées préfixées `_`
- Tout champ sensible anonymisé dans `_anonymize()` avant persistance
- Imports groupés : stdlib, tiers, local
- Modèle Claude à utiliser : `claude-opus-4-6`

---

## Conventions Git

- Branches : `main` (production), `dev` (développement)
- Commits en anglais, impératif : `Add`, `Fix`, `Update`, `Remove`
- Remote configuré avec token `gh auth token` dans l'URL
- `.env` et `.embed_cache.json` exclus du dépôt

---

## Roadmap

- [ ] Brancher embeddings (Voyage AI ou sentence-transformers local)
- [ ] Remplacer le cache JSON par pgvector
- [ ] Dashboard Grafana (métriques temps réel)
- [ ] Indexation automatique des ASUP entrants
- [ ] Support multi-cluster
- [ ] Auth OAuth2 sur l'API FastAPI
- [ ] CLI `mco` pour lancer collectes et rapports en ligne de commande

---

## Commandes utiles

```bash
# Lancer la stack complète
cd platform && docker-compose up -d

# Vérifier la santé de l'API
curl http://localhost:8000/api/health

# Lancer les tests PRA manuellement
python -m platform.automation.actions.restore_test_cifs

# Voir les logs API
docker logs mco-api -f

# Voir les logs n8n
docker logs mco-n8n -f
```

---

## À faire avant de coder

1. Lire ce fichier (déjà fait si tu lis ces lignes)
2. Vérifier `platform/.env.example` pour les variables requises
3. Ne jamais modifier les fichiers `platform/rag/knowledge_base/**` sans validation humaine
4. Tout ajout de prompt doit être versionné dans `monthly-reporting/` ou `incident-analysis/`
