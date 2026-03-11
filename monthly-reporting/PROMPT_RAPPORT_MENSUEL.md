# PROMPT — Rapport Mensuel NetApp ONTAP

## Contexte
Ce prompt permet de générer un rapport mensuel d'exploitation NetApp ONTAP à partir de données collectées via CLI SSH.

## Données d'entrée (à renseigner)

```
Cluster : [NOM_CLUSTER_ANONYMISÉ]
Période : [MOIS AAAA]
Données CLI :
[COLLER ICI LES SORTIES DES COMMANDES SUIVANTES]
- storage aggregate show
- volume show -fields used,available,percent-used
- system health alert show
- event log show -severity error,warning -time-range [DEBUT]..[FIN]
- snapmirror show -fields status,lag-time
- storage disk show -fields disk-class,model,rpm,type
```

## Prompt Claude

```
Tu es un expert NetApp ONTAP chargé de rédiger un rapport mensuel d'exploitation professionnel.

À partir des données CLI SSH suivantes (toutes données sensibles anonymisées) :

[COLLER LES DONNÉES ICI]

Génère un rapport structuré comprenant :

1. **Synthèse exécutive** (5 lignes max)
   - État général de la plateforme
   - Événements notables du mois
   - Indicateurs clés de performance

2. **Capacité & stockage**
   - Taux d'utilisation par agrégat et volume
   - Tendances de consommation
   - Alertes si utilisation > 80%

3. **Disponibilité & santé**
   - Alertes système rencontrées et résolutions
   - État des disques et contrôleurs
   - Incidents et temps de résolution

4. **Protection des données**
   - État des réplications SnapMirror
   - Vérification des sauvegardes
   - Conformité RPO/RTO

5. **Recommandations**
   - Actions correctives ou préventives à planifier
   - Points d'attention pour le mois suivant

Format : Markdown, ton professionnel, adapté à une présentation client PME/ETI.
Anonymise toute référence à des noms de clients, IPs ou hostnames.
```

## Validation humaine requise
- [ ] Vérifier les seuils d'alerte avant envoi client
- [ ] Valider les recommandations avec l'ingénieur référent
- [ ] Contrôler l'anonymisation complète du document
