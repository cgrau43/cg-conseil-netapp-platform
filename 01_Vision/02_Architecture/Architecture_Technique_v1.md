# Architecture Technique v1

## Objectif

Mettre en place une plateforme simple, maîtrisée et évolutive permettant :

- La surveillance intelligente de la production NetApp
- Le contrôle des sauvegardes
- La vérification des RPO (SnapMirror)
- La détection proactive des dérives
- La traçabilité des incidents
- ---

## Flux de Données

1. Le poste Windows collecte les métriques NetApp toutes les 30 minutes :
   - SnapMirror lag
   - Capacité volumes critiques
   - Statut des sauvegardes

2. Les données sont envoyées en HTTPS vers un Webhook n8n (VPS).

3. n8n :
   - Stocke les données dans PostgreSQL
   - Applique les règles de seuil
   - Détermine le statut (OK / WARNING / CRITICAL)

4. En cas de CRITICAL :
   - Création automatique d’un ticket Jira
   - Notification Microsoft Teams
   - Envoi d’un mail technique (vous)
   - Envoi d’un mail synthèse (tu)

5. Chaque matin à 08:00 :
   - Génération d’un mail quotidien de synthèse
   - ---

## Règles & Seuils (MVP)

Les seuils sont définis par client.

### Réplication (SnapMirror)

- Lag > 60 minutes → WARNING
- Lag > 120 minutes → CRITICAL

### Capacité

- Volume > 85% → WARNING
- Volume > 90% → CRITICAL

### Sauvegarde

- Aucun backup réussi depuis 24h → CRITICAL

Ces règles sont appliquées de manière déterministe dans n8n.
L’IA intervient uniquement pour l’explication et la reformulation.
---

## Sécurité (MVP)

- Le poste Windows pousse les données vers le VPS (aucune connexion entrante côté client).
- Le Webhook n8n est protégé par un token secret.
- Les communications sont réalisées en HTTPS.
- PostgreSQL n’est pas exposé publiquement.
- Sauvegarde hebdomadaire de la base de données.
- ---

## Format Standard JSON d’Ingestion (MVP)

Le poste local envoie un JSON structuré vers le Webhook n8n.

Exemple :

```json
{
  "client_id": "client_pilote",
  "timestamp": "2024-06-18T07:30:00Z",
  "metrics": {
    "replication": {
      "snapmirror_lag_minutes": 45,
      "rpo_expected_minutes": 15
    },
    "capacity": {
      "volume_name": "ERP_DATA",
      "used_percent": 82
    },
    "backup": {
      "last_success_hours": 12,
      "status": "OK"
    }
  }
}




