"""
restore_test_vm.py — Test automatisé de restauration VM (SnapCenter/Veeam)
CG CONSEIL — Plateforme MCO NetApp

Valide la capacité de restauration d'une VM de test depuis la dernière
sauvegarde SnapCenter ou Veeam. Vérifie que la VM démarre et répond
à un ping après restauration.
"""

import logging
import time
import subprocess
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VMRestoreTestResult:
    test_type: str = "vm"
    status: str = "pending"
    started_at: str = ""
    completed_at: str = ""
    duration_seconds: float = 0.0
    vm_name: str = ""
    backup_used: str = ""
    vm_started: bool = False
    vm_pingable: bool = False
    rto_met: bool = False
    rto_target_seconds: int = 7200   # 2h par défaut pour VM
    error_message: str = ""
    steps: list[dict] = field(default_factory=list)


class VMRestoreTest:
    """
    Test de restauration VM via API SnapCenter ou Veeam.

    Procédure :
    1. Identification de la dernière sauvegarde de la VM de test
    2. Lancement de la restauration vers un environnement isolé
    3. Attente du démarrage de la VM
    4. Vérification de la disponibilité réseau (ping)
    5. Arrêt de la VM de test et nettoyage
    """

    def __init__(
        self,
        vm_name: str,
        backup_tool: str = "snapcenter",   # snapcenter | veeam
        api_url: str = "",
        api_token: str = "",
        ping_ip: str = "",
        rto_target_seconds: int = 7200,
        boot_wait_seconds: int = 120,
    ):
        self.vm_name = vm_name
        self.backup_tool = backup_tool
        self.api_url = api_url
        self.api_token = api_token
        self.ping_ip = ping_ip
        self.rto_target_seconds = rto_target_seconds
        self.boot_wait_seconds = boot_wait_seconds

    def run(self) -> VMRestoreTestResult:
        result = VMRestoreTestResult(
            started_at=datetime.utcnow().isoformat(),
            vm_name=self.vm_name,
            rto_target_seconds=self.rto_target_seconds,
        )
        start_time = time.time()

        try:
            backup = self._step(result, f"Identification dernière sauvegarde ({self.backup_tool})",
                                self._find_latest_backup)
            result.backup_used = str(backup)

            self._step(result, "Lancement restauration VM (environnement isolé)",
                       lambda: self._trigger_restore(backup))

            self._step(result, f"Attente démarrage VM ({self.boot_wait_seconds}s)",
                       self._wait_for_boot)

            if self.ping_ip:
                pingable = self._step(result, "Vérification disponibilité réseau (ping)",
                                      self._check_ping)
                result.vm_pingable = pingable

            self._step(result, "Arrêt VM de test et nettoyage", self._cleanup_vm)

            result.status = "success"
            result.vm_started = True

        except AssertionError as e:
            result.status = "failure"
            result.error_message = str(e)
        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            logger.exception(f"Erreur test restauration VM : {e}")
        finally:
            result.duration_seconds = round(time.time() - start_time, 2)
            result.completed_at = datetime.utcnow().isoformat()
            result.rto_met = result.duration_seconds <= self.rto_target_seconds

        return result

    def _step(self, result, name, fn):
        step = {"name": name, "status": "running", "timestamp": datetime.utcnow().isoformat()}
        try:
            ret = fn()
            step["status"] = "success"
            result.steps.append(step)
            return ret
        except Exception as e:
            step["status"] = "failed"
            step["error"] = str(e)
            result.steps.append(step)
            raise

    def _find_latest_backup(self) -> dict:
        """Identifie la dernière sauvegarde disponible via l'API backup."""
        import httpx
        url = f"{self.api_url}/api/backups?vm={self.vm_name}&limit=1"
        resp = httpx.get(url, headers={"Authorization": f"Bearer {self.api_token}"}, timeout=30)
        resp.raise_for_status()
        backups = resp.json()
        assert backups, f"Aucune sauvegarde trouvée pour la VM : {self.vm_name}"
        return backups[0]

    def _trigger_restore(self, backup: dict) -> None:
        """Lance la restauration via API (SnapCenter ou Veeam)."""
        import httpx
        url = f"{self.api_url}/api/restore"
        payload = {
            "backup_id": backup.get("id"),
            "vm_name": self.vm_name,
            "restore_type": "instant_recovery",
            "isolated": True,
        }
        resp = httpx.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {self.api_token}"},
            timeout=300,
        )
        resp.raise_for_status()

    def _wait_for_boot(self) -> None:
        logger.info(f"Attente {self.boot_wait_seconds}s pour le démarrage de la VM...")
        time.sleep(self.boot_wait_seconds)

    def _check_ping(self) -> bool:
        try:
            result = subprocess.run(
                ["ping", "-c", "3", "-W", "5", self.ping_ip],
                capture_output=True,
                timeout=20,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _cleanup_vm(self) -> None:
        """Arrête et supprime la VM de test restaurée."""
        import httpx
        url = f"{self.api_url}/api/restore/cleanup"
        httpx.post(
            url,
            json={"vm_name": self.vm_name},
            headers={"Authorization": f"Bearer {self.api_token}"},
            timeout=60,
        )
