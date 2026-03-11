# Rapport Test PRA NetApp
**Date du test :** {{ test_date }}
**Trimestre :** T{{ quarter }} {{ year }}
**Réalisé par :** CG CONSEIL — Service MCO
**Statut :** {{ overall_status }}

---

## Synthèse

| Type de restauration | Résultat | Durée | RTO cible | RTO respecté |
|---|---|---|---|---|
| CIFS/SMB | {{ cifs.status }} | {{ cifs.duration_seconds }}s | {{ cifs.rto_target_seconds }}s | {{ '✓' if cifs.rto_met else '✗' }} |
| NFS | {{ nfs.status }} | {{ nfs.duration_seconds }}s | {{ nfs.rto_target_seconds }}s | {{ '✓' if nfs.rto_met else '✗' }} |
| VM | {{ vm.status }} | {{ vm.duration_seconds }}s | {{ vm.rto_target_seconds }}s | {{ '✓' if vm.rto_met else '✗' }} |

**Résultat global : {{ overall_status }}**

---

## Détail — Restauration CIFS

**Snapshot utilisé :** {{ cifs.snapshot_used }}
**Intégrité fichier vérifiée :** {{ '✓' if cifs.restored_file_verified else '✗' }}

### Étapes

{% for step in cifs.steps %}
- [{{ step.status }}] {{ step.name }}{% if step.error %} — Erreur : {{ step.error }}{% endif %}

{% endfor %}

---

## Détail — Restauration NFS

**Snapshot utilisé :** {{ nfs.snapshot_used }}
**Intégrité fichier vérifiée :** {{ '✓' if nfs.restored_file_verified else '✗' }}

### Étapes

{% for step in nfs.steps %}
- [{{ step.status }}] {{ step.name }}{% if step.error %} — Erreur : {{ step.error }}{% endif %}

{% endfor %}

---

## Détail — Restauration VM

**Sauvegarde utilisée :** {{ vm.backup_used }}
**VM démarrée :** {{ '✓' if vm.vm_started else '✗' }}
**Disponibilité réseau (ping) :** {{ '✓' if vm.vm_pingable else '✗' }}

### Étapes

{% for step in vm.steps %}
- [{{ step.status }}] {{ step.name }}{% if step.error %} — Erreur : {{ step.error }}{% endif %}

{% endfor %}

---

## Conformité RPO/RTO

| Objectif | Valeur contractuelle | Valeur mesurée | Conforme |
|---|---|---|---|
| RPO (dernier point de restauration) | {{ rpo_target }} | {{ rpo_measured }} | {{ rpo_compliant }} |
| RTO CIFS | {{ cifs.rto_target_seconds }}s | {{ cifs.duration_seconds }}s | {{ '✓' if cifs.rto_met else '✗' }} |
| RTO NFS | {{ nfs.rto_target_seconds }}s | {{ nfs.duration_seconds }}s | {{ '✓' if nfs.rto_met else '✗' }} |
| RTO VM | {{ vm.rto_target_seconds }}s | {{ vm.duration_seconds }}s | {{ '✓' if vm.rto_met else '✗' }} |

---

## Actions correctives

{{ corrective_actions or '> Aucune action corrective requise.' }}

---

## Validation

- [ ] Validé par l'ingénieur CG CONSEIL référent
- [ ] Transmis au responsable client
- [ ] Archivé dans la base documentaire

*Test réalisé automatiquement par la Plateforme MCO CG CONSEIL.*
*Résultats anonymisés — aucune donnée client sensible dans ce document.*
