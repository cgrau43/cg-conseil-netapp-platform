# Rapport MCO NetApp — Journalier
**Date :** {{ date }}
**Généré par :** Plateforme MCO CG CONSEIL
**Validation humaine requise avant envoi client**

---

## Synthèse

| Indicateur | Valeur | Statut |
|---|---|---|
| Événements EMS (24h) | {{ ems_count }} | {{ ems_status }} |
| Jobs backup (succès / échec) | {{ backup_ok }} / {{ backup_failed }} | {{ backup_status }} |
| Lag SnapMirror max | {{ snapmirror_lag_max }} | {{ snapmirror_status }} |
| Alertes actives | {{ alert_count }} | {{ alert_status }} |

---

## Événements EMS

{% if ems_events %}
{% for event in ems_events %}
- **[{{ event.business_level }}]** `{{ event.timestamp }}` — {{ event.message }}
  {% if event.auto_action %}> Action recommandée : {{ event.auto_action }}{% endif %}
{% endfor %}
{% else %}
> Aucun événement EMS significatif sur les dernières 24h.
{% endif %}

---

## Jobs de sauvegarde

### SnapCenter
{% if snapcenter_jobs %}
| Job | Statut | Durée | Commentaire |
|---|---|---|---|
{% for job in snapcenter_jobs %}
| {{ job.name }} | {{ job.Status }} | {{ job.duration_seconds }}s | {{ job.error or '' }} |
{% endfor %}
{% else %}
> Aucun job SnapCenter en échec.
{% endif %}

### Veeam
{% if veeam_jobs %}
| Job | Résultat | Durée | Commentaire |
|---|---|---|---|
{% for job in veeam_jobs %}
| {{ job.name }} | {{ job.severity }} | {{ job.duration_seconds }}s | |
{% endfor %}
{% else %}
> Aucun job Veeam en échec.
{% endif %}

---

## Protection des données (SnapMirror)

{% if snapmirror_relations %}
| Relation | Lag | Statut | Alerte |
|---|---|---|---|
{% for rel in snapmirror_relations %}
| {{ rel.destination }} | {{ rel.lag }} | {{ rel.status }} | {{ '⚠️' if rel.alert else '✓' }} |
{% endfor %}
{% else %}
> Aucune anomalie SnapMirror détectée.
{% endif %}

---

## Recommandations

{{ recommendations or '> Aucune recommandation particulière pour cette journée.' }}

---

*Rapport généré automatiquement — Validation ingénieur CG CONSEIL requise avant transmission client.*
*Toute donnée sensible doit être anonymisée avant envoi.*
