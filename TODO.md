# CG CONSEIL — TODO List vivante

> Fichier de pilotage interne — mis à jour à chaque session de travail.
> Dernière mise à jour : 11 mars 2026

---

## Légende

| Statut | Signification |
|---|---|
| ✅ | Fait — livrable disponible |
| ⏳ | En cours |
| 🔲 | À faire |
| 🔴 | Priorité haute — cette semaine |
| ⚠️ | Priorité moyenne — ce mois |
| 📋 | Priorité basse — quand le reste est fait |

---

## ① PLATEFORME TECHNIQUE — CG CONSEIL NetApp AI Platform

### Collecte & Qualification
- ✅ Structure repo GitHub (31 fichiers) — `platform/`
- ✅ Workflow n8n `NETAPP-INGEST-BASE` créé sur `ttref.cg-conseil.com`
- ✅ Connexion PostgreSQL Twenty Two opérationnelle
- ✅ Collecteur SSH ONTAP Python (Paramiko) — collector.py créé, à tester sur Twenty Two
- 🔲 🔴 Matrice qualification EMS (JSON) — niveaux EMERGENCY/ALERT/ERROR/WARNING
- 🔲 🔴 Requalification métier EMS (signal ponctuel vs récurrent)

### Rapport journalier automatique
- 🔲 🔴 Prompt Claude API → analyse EMS + résumé direction
- 🔲 🔴 Génération rapport PDF journalier
- 🔲 🔴 Workflow n8n cron 7h00 → collecte → analyse → livraison
- 🔲 ⚠️ Livraison SMTP (email direction/DSI)
- 🔲 ⚠️ Livraison Teams (webhook + lien PDF)
- 🔲 ⚠️ Git commit automatique des rapports (historique traçable)

### RAG & Base de connaissance
- 🔲 ⚠️ pgvector activé sur PostgreSQL VPS
- 🔲 ⚠️ Ingestion KB NetApp (articles, Working Instructions, historique incidents)
- 🔲 ⚠️ Retriever cosinus — recherche sémantique sur incidents
- 🔲 📋 Feedback loop — enrichissement automatique depuis incidents résolus

### Tests PRA automatisés
- 🔲 ⚠️ Test restauration CIFS automatisé + rapport
- 🔲 ⚠️ Test restauration NFS automatisé + rapport
- 🔲 ⚠️ Test restauration VM automatisé + rapport
- 🔲 📋 Score "PRA Ready" — indicateur synthétique direction
- 🔲 📋 Simulation incident majeur (perte site, corruption snapshot)

### API & Dashboard
- 🔲 📋 FastAPI — endpoints `/health`, `/alerts`, `/reports`
- 🔲 📋 Dashboard supervision (interface web légère)

---

## ② CV & MISSIONS ESN

- ✅ CV ESN/ATS 2026 — `CV_Christian_Grau_ESN_ATS_2026.docx`
- ✅ GitHub profil public — `github.com/cgrau43`
- ✅ Lien GitHub intégré dans le CV
- 🔲 🔴 Compléter placeholders CV (métriques manquantes)
  - Zones Brocade créées chez Twenty Two
  - Délai PRA opérationnel en jours
  - Nb incohérences rétention corrigées (GEODIS/STORDATA)
  - Nb tickets traités (ONET)
  - Nb scripts PowerShell déployés (AIRBUS)
  - Délai mise en prod PRA (SCAPRIM)
  - Nb VMs migrées XenServer→VMware (ASP CONNECT)
  - Nb formations / stagiaires (2003-2006)
- 🔲 ⚠️ Mettre à jour profil LinkedIn
  - Nouveau titre : Consultant Expert Infrastructure NetApp · IA · PRA
  - Résumé aligné avec CV
  - Lien GitHub visible
  - Références chiffrées dans les expériences
- 🔲 ⚠️ Dépôt sur plateformes freelance (Malt, Comet, Freelance.com)
- 🔲 📋 Lettre de mission type (ESN / client direct)

---

## ③ OFFRE COMMERCIALE CG CONSEIL

- ✅ Offre V1 (sans IA) — `Offre_Support_Manage_CG_CONSEIL_2026.docx`
- 🔲 ⚠️ Offre V2 augmentée IA — après validation technique plateforme
  - Rapport journalier automatique comme livrable différenciant
  - Score PRA Ready
  - Références résultats mesurés V1 (Twenty Two)
- 🔲 ⚠️ Grille tarifaire (forfaits par périmètre — S/M/L)
- 🔲 📋 Deck de présentation client (6 slides PowerPoint)
- 🔲 📋 Page GitHub vitrine entreprise enrichie (cas client anonymisé)
- 🔲 📋 Landing page simple CG CONSEIL (1 page HTML)

---

## ④ ADMINISTRATION CG CONSEIL

- ⏳ Arborescence Google Drive CG CONSEIL — en cours (Claude Code)
- 🔲 🔴 Template devis CG CONSEIL (Word/PDF)
- 🔲 🔴 Template facture CG CONSEIL (Word/PDF)
- 🔲 🔴 Template contrat de mission ESN
- 🔲 ⚠️ Accès partagé Henri (comptable) sur Google Drive
- 🔲 ⚠️ Suivi facturation Twenty Two 2025/2026
- 🔲 ⚠️ Processus devis → bon de commande → facture → relance
- 🔲 📋 Automatisation facturation récurrente via n8n

---

## ⑤ INFRASTRUCTURE VPS & OUTILS

- ✅ VPS Hostinger Ubuntu — Docker + PostgreSQL + Python 3
- ✅ n8n en test sur `ttref.cg-conseil.com`
- 🔲 🔴 n8n passer en prod (backup config, HTTPS, monitoring)
- 🔲 ⚠️ pgvector installé sur PostgreSQL
- 🔲 ⚠️ Backup automatique VPS (données + configs n8n)
- 🔲 📋 Monitoring VPS (uptime, alertes)

---

## Historique des mises à jour

| Date | Modifications |
|---|---|
| 2026-03-11 | Création initiale — synthèse journée de travail |
| 2026-03-11 | Collecteur SSH ONTAP créé, CLAUDE.md + TODO.md pushés sur GitHub, Mac Pro 2012 dual boot Ubuntu planifié |

---

*Fichier maintenu par Christian Grau — CG CONSEIL*
*Mis à jour manuellement ou via Claude Code à chaque session*
