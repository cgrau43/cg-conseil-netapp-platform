"""
restore_test_nfs.py — Test automatisé de restauration NFS
CG CONSEIL — Plateforme MCO NetApp

Valide la capacité de restauration depuis un snapshot NetApp sur un
export NFS. Similaire au test CIFS mais adapté aux chemins Unix/NFS.
"""

import logging
import time
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class NFSRestoreTestResult:
    test_type: str = "nfs"
    status: str = "pending"
    started_at: str = ""
    completed_at: str = ""
    duration_seconds: float = 0.0
    mount_point: str = ""
    snapshot_used: str = ""
    restored_file_verified: bool = False
    rto_met: bool = False
    rto_target_seconds: int = 3600
    error_message: str = ""
    steps: list[dict] = field(default_factory=list)


class NFSRestoreTest:
    """
    Test de restauration NFS depuis snapshot NetApp.

    Procédure :
    1. Vérification que le point de montage NFS est accessible
    2. Accès au répertoire .snapshot (visible côté NFS si activé)
    3. Restauration d'un fichier test depuis le snapshot
    4. Vérification de l'intégrité
    5. Nettoyage
    """

    def __init__(
        self,
        mount_point: str,
        test_file_name: str = "pra_test_marker.txt",
        rto_target_seconds: int = 3600,
    ):
        self.mount_point = Path(mount_point)
        self.test_file_name = test_file_name
        self.rto_target_seconds = rto_target_seconds

    def run(self) -> NFSRestoreTestResult:
        result = NFSRestoreTestResult(
            started_at=datetime.utcnow().isoformat(),
            mount_point=str(self.mount_point),
            rto_target_seconds=self.rto_target_seconds,
        )
        start_time = time.time()

        try:
            self._step(result, "Vérification montage NFS", self._check_nfs_mount)
            self._step(result, "Vérification accès .snapshot", self._check_snapshot_access)
            snapshot = self._step(result, "Sélection snapshot récent", self._find_latest_snapshot)
            self._step(result, "Restauration fichier test", lambda: self._restore_file(snapshot))
            self._step(result, "Vérification intégrité", self._verify_restored_file)
            self._step(result, "Nettoyage", self._cleanup)

            result.status = "success"
            result.snapshot_used = str(snapshot)
            result.restored_file_verified = True

        except AssertionError as e:
            result.status = "failure"
            result.error_message = str(e)
        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            logger.exception(f"Erreur test NFS : {e}")
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

    def _check_nfs_mount(self) -> None:
        assert self.mount_point.exists(), f"Point de montage NFS inaccessible : {self.mount_point}"
        # Vérifie que c'est bien un montage NFS actif
        try:
            result = subprocess.run(
                ["mountpoint", "-q", str(self.mount_point)],
                timeout=10,
                check=False,
            )
            assert result.returncode == 0, "Le chemin n'est pas un point de montage actif"
        except FileNotFoundError:
            pass  # mountpoint non disponible sur Windows — on ignore

    def _check_snapshot_access(self) -> None:
        snapshot_dir = self.mount_point / ".snapshot"
        assert snapshot_dir.exists(), (
            "Répertoire .snapshot inaccessible — vérifier 'snapdir visible' sur le volume"
        )

    def _find_latest_snapshot(self) -> Path:
        snapshot_dir = self.mount_point / ".snapshot"
        snapshots = sorted(snapshot_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        assert snapshots, "Aucun snapshot disponible sur ce volume"
        return snapshots[0]

    def _restore_file(self, snapshot: Path) -> None:
        source = snapshot / self.test_file_name
        assert source.exists(), f"Fichier test absent du snapshot : {source}"
        dest = self.mount_point / f"_pra_restored_{self.test_file_name}"
        dest.write_bytes(source.read_bytes())

    def _verify_restored_file(self) -> None:
        dest = self.mount_point / f"_pra_restored_{self.test_file_name}"
        assert dest.exists() and dest.stat().st_size > 0, "Fichier restauré vide ou absent"

    def _cleanup(self) -> None:
        dest = self.mount_point / f"_pra_restored_{self.test_file_name}"
        if dest.exists():
            dest.unlink()
