#!/usr/bin/env python3
"""
backup_to_usb.py — Sauvegarde des fichiers critiques CG Conseil vers USB/disque externe
"""

import os
import shutil
import string
from datetime import datetime
from pathlib import Path

FILES_TO_BACKUP = [
    r"C:/Users/cgrau/cg-conseil-netapp-platform/platform/.env",
    r"C:/Users/cgrau/.ssh/id_rsa_twentytwo",
    r"C:/Users/cgrau/.ssh/id_rsa_twentytwo.pub",
    r"C:/Users/cgrau/.ssh/config",
    r"C:/Users/cgrau/cg-conseil-netapp-platform/CLAUDE.md",
    r"C:/Users/cgrau/cg-conseil-netapp-platform/TODO.md",
]


def detect_usb_drives():
    """Détecte les disques amovibles disponibles (Windows)."""
    import ctypes
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drive = f"{letter}:\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
            # 2 = DRIVE_REMOVABLE, 3 = DRIVE_FIXED (inclus pour disques externes USB)
            if drive_type in (2, 3) and letter not in ("C",):
                drives.append(drive)
        bitmask >>= 1
    return drives


def main():
    print("=" * 55)
    print("  CG Conseil — Backup fichiers critiques vers USB")
    print("=" * 55)

    # Détection des disques
    drives = detect_usb_drives()
    if not drives:
        print("\n[ERREUR] Aucun disque USB/externe détecté.")
        print("         Branchez votre clé USB et relancez le script.")
        return

    # Sélection du disque
    if len(drives) == 1:
        target_drive = drives[0]
        print(f"\nDisque détecté : {target_drive}")
    else:
        print(f"\nDisques détectés : {', '.join(drives)}")
        target_drive = input("Choisissez la lettre du disque (ex: E): ").strip().upper()
        if not target_drive.endswith(":\\"):
            target_drive = f"{target_drive}:\\"
        if target_drive not in drives:
            print(f"[ERREUR] Disque {target_drive} non trouvé.")
            return

    # Création du dossier de backup
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(target_drive) / f"backup_cgconseil_{date_str}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"Dossier backup : {backup_dir}\n")

    # Copie des fichiers
    copied = []
    missing = []
    errors = []

    for src_path in FILES_TO_BACKUP:
        src = Path(src_path)
        if not src.exists():
            missing.append(str(src))
            print(f"  [MANQUANT]  {src}")
            continue
        try:
            dst = backup_dir / src.name
            shutil.copy2(src, dst)
            size = src.stat().st_size
            print(f"  [OK]        {src.name:<35} ({size:,} octets)")
            copied.append(str(src))
        except Exception as e:
            errors.append(f"{src}: {e}")
            print(f"  [ERREUR]    {src.name} — {e}")

    # Résumé
    print("\n" + "-" * 55)
    print(f"  Copiés   : {len(copied)}/{len(FILES_TO_BACKUP)}")
    if missing:
        print(f"  Manquants: {len(missing)}")
        for f in missing:
            print(f"             - {f}")
    if errors:
        print(f"  Erreurs  : {len(errors)}")
        for e in errors:
            print(f"             - {e}")
    print(f"\n  Backup sauvegardé dans : {backup_dir}")
    print("=" * 55)


if __name__ == "__main__":
    main()
