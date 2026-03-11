# Plateforme MCO Intelligent NetApp — CG CONSEIL

Plateforme d'exploitation intelligente NetApp pour environnements PME/ETI.
Supervision proactive, qualification IA des événements, génération de rapports automatisée.

**Résultat mesuré : reporting mensuel réduit de 4h à < 20 min (-92%)**

---

## Architecture

```
platform/
├── collector/          Collecte EMS, SnapCenter, Veeam, ASUP
├── qualification/      Requalification métier + matrice criticité
├── rag/                Base de connaissances + retrieval augmenté
├── automation/         Workflows n8n + tests restauration PRA
├── reporting/          Templates + générateur IA (Claude)
└── api/                API FastAPI (endpoints santé, alertes, rapports)
```

## Démarrage rapide

### Prérequis

- Docker & Docker Compose
- Python 3.11+
- Clé API Anthropic (Claude)
- Accès ONTAP REST API (ONTAP 9.6+)

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/cgrau43/cg-conseil-netapp-platform.git
cd cg-conseil-netapp-platform/platform

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# 3. Démarrer la stack
docker-compose up -d

# 4. Vérifier
curl http://localhost:8000/api/health
```

### Accès aux services

| Service | URL | Credentials |
|---|---|---|
| API FastAPI | http://localhost:8000 | — |
| Documentation API | http://localhost:8000/docs | — |
| n8n Workflows | http://localhost:5678 | `.env` N8N_USER/PASSWORD |

## Modules

### Collector
Collecte les données brutes depuis les APIs :
- `ems_collector.py` — Événements EMS ONTAP (REST API)
- `snapcenter_collector.py` — Jobs SnapCenter
- `veeam_collector.py` — Sessions Veeam B&R
- `asup_parser.py` — Rapports AutoSupport

### Qualification
Requalifie les événements en criticité métier (P1→P4) :
- `ems_matrix.json` — Mapping sévérités EMS → niveaux business
- `qualifier.py` — Moteur de qualification
- `rules/` — Règles stockage, backup, PRA

### RAG (Retrieval Augmented Generation)
Enrichit les analyses IA avec la knowledge base :
- `knowledge_base/netapp_kb/` — Articles KB NetApp (à alimenter)
- `knowledge_base/working_instructions/` — Procédures CG CONSEIL
- `knowledge_base/incident_history/` — Historique incidents résolus
- `embeddings.py` — Indexation vectorielle
- `retriever.py` — Recherche par similarité

### Automation
Tests de restauration PRA et workflows n8n :
- `n8n_workflows/` — Rapport journalier, alertes enrichies, test PRA
- `actions/` — Tests restauration CIFS, NFS, VM

### Reporting
Génération de rapports Markdown enrichis par IA :
- Templates : journalier, mensuel, PRA
- `generator.py` — Synthèse et recommandations via Claude

## Principes de sécurité

- **Anonymisation systématique** : IPs, hostnames, noms de clients masqués avant traitement IA
- **Validation humaine** : tous les rapports nécessitent une validation avant envoi
- **Prompts versionnés Git** : traçabilité complète des prompts utilisés
- **Secrets hors code** : variables d'environnement, jamais dans le dépôt

## Roadmap

- [ ] Connexion base vectorielle (pgvector) pour RAG production
- [ ] Dashboard Grafana pour visualisation temps réel
- [ ] Indexation automatique des ASUP entrants
- [ ] Multi-cluster support
- [ ] Authentification OAuth2 sur l'API
