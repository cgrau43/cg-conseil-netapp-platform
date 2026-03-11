# PROMPT — Analyse d'Incident NetApp / Backup / SnapCenter

## Contexte
Ce prompt permet d'analyser un incident sur infrastructure NetApp ONTAP, solution de sauvegarde ou SnapCenter, et de produire un rapport RCA (Root Cause Analysis) structuré.

## Données d'entrée (à renseigner)

```
Environnement : [ONTAP / SnapCenter / Backup / Réseau]
Date/heure incident : [JJ/MM/AAAA HH:MM]
Date/heure résolution : [JJ/MM/AAAA HH:MM]
Symptômes observés : [DESCRIPTION]
Logs disponibles :
[COLLER ICI LES LOGS PERTINENTS — anonymisés]
Commandes exécutées :
[COLLER LES SORTIES CLI PERTINENTES]
```

## Prompt Claude

```
Tu es un expert en exploitation NetApp ONTAP et solutions de protection des données (SnapCenter, sauvegarde).

À partir des informations suivantes (données sensibles anonymisées) :

[COLLER LES DONNÉES D'ENTRÉE ICI]

Produis une analyse d'incident structurée comprenant :

1. **Chronologie de l'incident**
   - Timeline précise des événements (du premier symptôme à la résolution)
   - Actions correctives appliquées

2. **Cause racine (RCA)**
   - Cause technique identifiée
   - Facteurs aggravants éventuels
   - Périmètre d'impact (volumes, hôtes, services)

3. **Impact business**
   - Durée d'interruption de service
   - Données potentiellement affectées
   - RPO/RTO constaté vs. contractuel

4. **Actions correctives appliquées**
   - Étapes de résolution effectuées
   - Commandes ou procédures utilisées

5. **Plan d'action préventif**
   - Mesures pour éviter la récurrence
   - Améliorations de monitoring ou de configuration
   - Mises à jour de procédures recommandées

6. **Conclusion**
   - Statut final de l'incident (résolu / en surveillance / escaladé)
   - Niveau de sévérité (P1/P2/P3/P4)

Format : Markdown, ton factuel et professionnel, adapté à un compte rendu client.
Anonymise toute référence à des noms de clients, IPs, hostnames ou identifiants.
```

## Validation humaine requise
- [ ] Confirmer la cause racine avec l'ingénieur ayant traité l'incident
- [ ] Valider le périmètre d'impact avant communication client
- [ ] S'assurer de l'anonymisation complète avant partage
