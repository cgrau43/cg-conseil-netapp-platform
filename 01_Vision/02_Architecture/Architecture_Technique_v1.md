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

