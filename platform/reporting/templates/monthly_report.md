# Rapport MCO NetApp — Mensuel
**Période :** {{ month }} {{ year }}
**Client :** [NOM_CLIENT_ANONYMISÉ]
**Rédigé par :** CG CONSEIL — Service MCO NetApp
**Version :** 1.0 — À valider avant envoi

---

## 1. Synthèse exécutive

{{ executive_summary }}

**Indicateurs clés du mois :**

| KPI | Valeur | Objectif | Atteint |
|---|---|---|---|
| Disponibilité globale | {{ availability_percent }}% | 99,5% | {{ '✓' if availability_percent >= 99.5 else '✗' }} |
| Incidents P1/P2 | {{ incidents_p1_p2 }} | 0 | {{ '✓' if incidents_p1_p2 == 0 else '✗' }} |
| Jobs backup (taux succès) | {{ backup_success_rate }}% | ≥ 98% | {{ '✓' if backup_success_rate >= 98 else '✗' }} |
| RPO respecté | {{ rpo_compliant }}% | 100% | {{ '✓' if rpo_compliant == 100 else '✗' }} |
| Reporting automatisé | < 20 min | < 20 min | ✓ |

---

## 2. Capacité & stockage

### Agrégats

| Agrégat | Capacité | Utilisé | % | Tendance |
|---|---|---|---|---|
{% for agg in aggregates %}
| {{ agg.name }} | {{ agg.total_gb }} GB | {{ agg.used_gb }} GB | {{ agg.percent_used }}% | {{ agg.trend }} |
{% endfor %}

### Volumes à surveiller (> 80%)

{% if volume_alerts %}
{% for vol in volume_alerts %}
- `{{ vol.name }}` — {{ vol.percent_used }}% utilisé
{% endfor %}
{% else %}
> Aucun volume en dépassement de seuil ce mois.
{% endif %}

---

## 3. Incidents du mois

{% if incidents %}
{% for inc in incidents %}
### {{ inc.id }} — {{ inc.title }}
- **Date :** {{ inc.date }}
- **Sévérité :** {{ inc.severity }}
- **Durée :** {{ inc.duration }}
- **Cause racine :** {{ inc.root_cause }}
- **Résolution :** {{ inc.resolution }}
{% endfor %}
{% else %}
> Aucun incident enregistré sur la période.
{% endif %}

---

## 4. Protection des données

### Réplications SnapMirror

{{ snapmirror_summary }}

### Sauvegardes

| Semaine | Jobs totaux | Succès | Échecs | Taux |
|---|---|---|---|---|
{% for week in backup_weekly %}
| S{{ week.number }} | {{ week.total }} | {{ week.success }} | {{ week.failed }} | {{ week.rate }}% |
{% endfor %}

---

## 5. Recommandations

{{ recommendations }}

---

## 6. Plan d'action

| Action | Priorité | Responsable | Échéance |
|---|---|---|---|
{% for action in action_plan %}
| {{ action.description }} | {{ action.priority }} | {{ action.owner }} | {{ action.due_date }} |
{% endfor %}

---

*Document généré par la Plateforme MCO CG CONSEIL — Gain de temps : -92% (de 4h à < 20 min)*
*Validation ingénieur obligatoire avant transmission. Données anonymisées.*
