#!/usr/bin/env python
"""
Full database backups for the local FoodTable Postgres container via pg_dump.

Unlike db_snapshot.py (Django dumpdata, content app only), this captures the
entire database -- schema and all tables -- straight from Postgres, so it
restores cleanly even if migrations or models have since changed.

Usage:
    python backup_db.py backup [--keep N]   # Create a backup, then prune to the last N (default 30)
    python backup_db.py restore <file>       # Restore from a backup file (DESTRUCTIVE)
    python backup_db.py list                 # List existing backups
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path(__file__).parent / 'db_backups'
CONTAINER = 'foodtable_db'
DB_NAME = 'foodtable'
DB_USER = 'foodtable_user'
DEFAULT_KEEP = 30


def container_running():
    result = subprocess.run(
        ['docker', 'inspect', '-f', '{{.State.Running}}', CONTAINER],
        capture_output=True, text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == 'true'


def create_backup(keep):
    if not container_running():
        print(f"[ERROR] Container '{CONTAINER}' is not running. Start it first (start_database.py).")
        return False

    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f"foodtable_{timestamp}.sql"

    print(f"Creating backup: {backup_file.name}")
    with open(backup_file, 'wb') as f:
        result = subprocess.run(
            ['docker', 'exec', CONTAINER, 'pg_dump', '-U', DB_USER, DB_NAME],
            stdout=f, stderr=subprocess.PIPE,
        )

    if result.returncode != 0:
        backup_file.unlink(missing_ok=True)
        print(f"[ERROR] pg_dump failed:\n{result.stderr.decode(errors='replace')}")
        return False

    size_mb = backup_file.stat().st_size / 1024 / 1024
    print(f"[OK] Backup created ({size_mb:.2f} MB)")

    prune_old_backups(keep)
    return True


def prune_old_backups(keep):
    backups = sorted(BACKUP_DIR.glob('foodtable_*.sql'), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[keep:]:
        old.unlink()
        print(f"  Pruned old backup: {old.name}")


def list_backups():
    BACKUP_DIR.mkdir(exist_ok=True)
    backups = sorted(BACKUP_DIR.glob('foodtable_*.sql'), reverse=True)

    if not backups:
        print("No backups found.")
        return

    print(f"\nBackups in {BACKUP_DIR} ({len(backups)}):")
    for b in backups:
        size_mb = b.stat().st_size / 1024 / 1024
        mtime = datetime.fromtimestamp(b.stat().st_mtime)
        print(f"  {b.name}  ({size_mb:.2f} MB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")


def restore_backup(path):
    backup_file = Path(path)
    if not backup_file.is_absolute():
        backup_file = BACKUP_DIR / path

    if not backup_file.exists():
        print(f"[ERROR] Backup not found: {backup_file}")
        return False

    if not container_running():
        print(f"[ERROR] Container '{CONTAINER}' is not running. Start it first.")
        return False

    print(f"WARNING: This will ERASE all current data in '{DB_NAME}' and replace it with {backup_file.name}")
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Restore cancelled.")
        return False

    print("Dropping and recreating schema...")
    drop_result = subprocess.run(
        ['docker', 'exec', CONTAINER, 'psql', '-U', DB_USER, '-d', DB_NAME,
         '-c', 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'],
        capture_output=True, text=True,
    )
    if drop_result.returncode != 0:
        print(f"[ERROR] Failed to reset schema:\n{drop_result.stderr}")
        return False

    print(f"Restoring from {backup_file.name}...")
    with open(backup_file, 'rb') as f:
        result = subprocess.run(
            ['docker', 'exec', '-i', CONTAINER, 'psql', '-U', DB_USER, '-d', DB_NAME],
            stdin=f, capture_output=True, text=True,
        )
    if result.returncode != 0:
        print(f"[ERROR] Restore failed:\n{result.stderr}")
        return False

    print("[OK] Database restored successfully")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)

    backup_p = sub.add_parser('backup')
    backup_p.add_argument('--keep', type=int, default=DEFAULT_KEEP)

    restore_p = sub.add_parser('restore')
    restore_p.add_argument('file')

    sub.add_parser('list')

    args = parser.parse_args()

    if args.command == 'backup':
        ok = create_backup(args.keep)
    elif args.command == 'restore':
        ok = restore_backup(args.file)
    else:
        list_backups()
        ok = True

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
