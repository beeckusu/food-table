#!/usr/bin/env python
"""
Database snapshot management for FoodTable

Creates and restores database snapshots using Django's dumpdata/loaddata.

Usage:
    python db_snapshot.py backup [name]      # Create a snapshot
    python db_snapshot.py restore <name>     # Restore a snapshot
    python db_snapshot.py list               # List all snapshots
    python db_snapshot.py delete <name>      # Delete a snapshot
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Snapshot directory
SNAPSHOT_DIR = Path(__file__).parent / 'db_snapshots'
SNAPSHOT_DIR.mkdir(exist_ok=True)


def create_backup(snapshot_name=None):
    """Create a database snapshot"""
    if snapshot_name is None:
        snapshot_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    backup_file = SNAPSHOT_DIR / f"{snapshot_name}.json"

    print(f"Creating snapshot: {snapshot_name}")
    print(f"File: {backup_file}")

    # Run Django dumpdata
    cmd = [
        sys.executable,
        'manage.py',
        'dumpdata',
        '--natural-foreign',
        '--natural-primary',
        '--indent', '2',
        '--output', str(backup_file),
        'content',  # Only content app data
        'auth.User',  # Include users
    ]

    try:
        # Set UTF-8 encoding for Windows
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            size_mb = backup_file.stat().st_size / 1024 / 1024
            print(f"[OK] Snapshot created successfully ({size_mb:.2f} MB)")
            return True
        else:
            print(f"[ERROR] Error creating snapshot:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False


def restore_backup(snapshot_name):
    """Restore a database snapshot"""
    backup_file = SNAPSHOT_DIR / f"{snapshot_name}.json"

    if not backup_file.exists():
        print(f"[ERROR] Snapshot not found: {snapshot_name}")
        print(f"  Looking for: {backup_file}")
        return False

    print(f"WARNING: This will DELETE all existing content data!")
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() != 'yes':
        print("Restore cancelled.")
        return False

    print(f"\nRestoring snapshot: {snapshot_name}")

    # Step 1: Delete all content data
    print("Deleting existing content...")
    delete_cmd = [
        sys.executable,
        'manage.py',
        'shell',
        '-c',
        (
            "from content.models import Review, ReviewDish, EncyclopediaEntry, Image; "
            "Image.objects.all().delete(); "
            "ReviewDish.objects.all().delete(); "
            "Review.objects.all().delete(); "
            "EncyclopediaEntry.objects.all().delete(); "
            "print('Deleted all content data')"
        )
    ]

    result = subprocess.run(delete_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Error deleting data:")
        print(result.stderr)
        return False

    print(result.stdout)

    # Step 2: Load from snapshot
    print("Loading snapshot data...")
    load_cmd = [
        sys.executable,
        'manage.py',
        'loaddata',
        str(backup_file)
    ]

    result = subprocess.run(load_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("[OK] Database restored successfully")
        print(result.stdout)
        return True
    else:
        print(f"[ERROR] Error restoring database:")
        print(result.stderr)
        return False


def list_snapshots():
    """List all available snapshots"""
    snapshots = sorted(SNAPSHOT_DIR.glob('*.json'))

    if not snapshots:
        print("No snapshots found.")
        return

    print(f"\nAvailable snapshots ({len(snapshots)}):")
    print(f"Location: {SNAPSHOT_DIR}")
    print()

    for snapshot in snapshots:
        name = snapshot.stem
        size_mb = snapshot.stat().st_size / 1024 / 1024
        mtime = datetime.fromtimestamp(snapshot.stat().st_mtime)
        print(f"  {name}")
        print(f"    Size: {size_mb:.2f} MB")
        print(f"    Created: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def delete_snapshot(snapshot_name):
    """Delete a snapshot"""
    backup_file = SNAPSHOT_DIR / f"{snapshot_name}.json"

    if not backup_file.exists():
        print(f"[ERROR] Snapshot not found: {snapshot_name}")
        return False

    print(f"Deleting snapshot: {snapshot_name}")
    response = input("Are you sure? (yes/no): ")

    if response.lower() != 'yes':
        print("Delete cancelled.")
        return False

    backup_file.unlink()
    print(f"[OK] Snapshot deleted")
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'backup':
        name = sys.argv[2] if len(sys.argv) > 2 else None
        create_backup(name)

    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Error: Snapshot name required")
            print("Usage: python db_snapshot.py restore <name>")
            sys.exit(1)
        restore_backup(sys.argv[2])

    elif command == 'list':
        list_snapshots()

    elif command == 'delete':
        if len(sys.argv) < 3:
            print("Error: Snapshot name required")
            print("Usage: python db_snapshot.py delete <name>")
            sys.exit(1)
        delete_snapshot(sys.argv[2])

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
