# CLAUDE.md — Contexte projet CG CONSEIL

> Ce fichier est lu automatiquement par Claude Code au démarrage de chaque session.
> Il contient tout le contexte nécessaire pour reprendre le travail sans re-expliquer.

---

## Qui je suis

**Christian Grau — Fondateur CG CONSEIL**
Consultant Expert Infrastructure : NetApp ONTAP · SAN Fibre Channel · SnapCenter · PRA · Automatisation
Freelance · Marseille (13) · France entière + Remote
Email : christian.grau@cgconseil.fr
GitHub : github.com/cgrau43

---

## Ce qu'on construit

Une **plateforme de MCO intelligent** pour infrastructures NetApp ONTAP, destinée aux PME/ETI.
Trois piliers :
- **Pilier 1** — Garant de la prod NetApp (supervision, alertes enrichies, détection proactive)
- **Pilier 2** — Garant du Backup (vérification qualité jobs, anomalies rétention)
- **Pilier 3** — Garant du PRA (tests restauration automatisés CIFS/NFS/VM, score PRA Ready)

Le différenciateur : **analyse IA des EMS ONTAP** → rapport journalier automatique en langage direction.

---

## Stack technique validée

| Composant | Solution | Statut |
|---|---|---|
| Orchestration | n8n (Docker) | ✅ En test sur ttref.cg-conseil.com |
| Collecte ONTAP | Python + Paramiko SSH | 🔴 À coder |
| Analyse IA | Claude API (Sonnet) | ✅ Disponible |
| Base vectorielle | PostgreSQL + pgvector | ⚠️ pgvector à installer |
| Hébergement | VPS Hostinger Ubuntu | ✅ En prod |
| Versioning | Git + GitHub (cgrau43) | ✅ Actif |
| Livraison | SMTP + Teams + PDF | 🔴 À configurer |
| Tests PRA | PowerCLI + n8n | 📋 V2 |

---

## Infrastructure VPS

- **OS** : Ubuntu (Hostinger)
- **Installé** : Docker, PostgreSQL, Python 3, n8n
- **URL n8n** : ttref.cg-conseil.com
- **Workflow existant** : NETAPP-INGEST-BASE (webhook POST → PostgreSQL TwentyTwo)
- **À installer** : pgvector

---

## Client actif — Twenty Two Real Estate

- Cluster PROD : `[CLUSTER_PROD]` — alias SSH : `twentytwo-prod`
- Cluster PRA : `CLUSTER_PRA_02` — alias SSH : `twentytwo-pra`
- SVM FC : `SPM3SVM-FC-AUTO`
- 22 To, 50 VMs SnapCenter, 90+ datastores FC
- Interventions hors heures bureaux pour tests PRA

> ⚠️ Anonymiser systématiquement IPs, noms de clusters et credentials avant tout appel Claude API

---

## Repo structure

```
cg-conseil-netapp-platform/
├── platform/
│   ├── collector/          ← Collecteurs ONTAP (SSH Paramiko — PAS REST API)
│   ├── qualification/      ← Matrice EMS JSON + qualifier.py
│   ├── rag/               ← Embeddings + retriever pgvector
│   ├── automation/        ← Workflows n8n + scripts tests restauration
│   ├── reporting/         ← Générateur rapports + templates
│   └── api/               ← FastAPI (V3)
├── monthly-reporting/      ← Prompt templates rapport mensuel
├── incident-analysis/      ← Prompt templates analyse incidents
├── 01_Vision/             ← Architecture technique
├── TODO.md                ← Plan de travail vivant (toujours à jour)
├── CLAUDE.md              ← Ce fichier
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Conventions de code

- **Langage principal** : Python 3
- **Collecte ONTAP** : SSH + CLI (Paramiko) — jamais REST API (pas toujours activée chez les clients)
- **Anonymisation** : toujours anonymiser IPs/credentials/noms clients avant appel LLM
- **Credentials** : dans `.env` uniquement — jamais dans le code
- **Format données** : JSON structuré entre les modules
- **Logs** : horodatés, niveau INFO/WARNING/ERROR
- **Tests** : valider sur Twenty Two hors heures bureaux

---

## Règles de sécurité absolues

1. Aucune IP de production dans le code — utiliser des variables d'env
2. Aucun credential en dur — `.env` uniquement
3. Anonymisation systématique avant tout appel Claude API
4. Validation humaine de chaque livrable avant envoi client
5. `.env` jamais commité — toujours dans `.gitignore`

---

## Fichiers clés produits (hors repo)

| Fichier | Description | Emplacement |
|---|---|---|
| CV_Christian_Grau_ESN_ATS_2026.docx | CV freelance ESN | Google Drive / local |
| Offre_Support_Manage_CG_CONSEIL_2026.docx | Offre commerciale V1 | Google Drive / local |
| Plan_CG_CONSEIL_Mars_2026.docx | Plan de travail synthèse | Google Drive / local |

---

## Priorités actuelles (P1 — cette semaine)

1. Collecteur SSH ONTAP Python (Paramiko) — `platform/collector/`
2. Matrice qualification EMS JSON — `platform/qualification/`
3. Prompt Claude API → rapport journalier — `platform/reporting/`
4. Templates devis + facture CG CONSEIL
5. Compléter placeholders CV

---

## Contacts

- **Comptable** : Henri (accès Google Drive à configurer)
- **Client actif** : Twenty Two Real Estate

---

*Mis à jour : 11 mars 2026*
*Maintenu par Christian Grau + Claude + Claude Code*
