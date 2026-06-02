#!/usr/bin/env python
"""
Sync local database content and media files to Neon + Cloudflare R2.

Requires NEON_DATABASE_URL (or DATABASE_URL) in .env pointing to the Neon instance.

Usage:
    python sync_to_neon.py              # Sync both DB and media
    python sync_to_neon.py --db-only    # Database only
    python sync_to_neon.py --media-only # Media files only
    python sync_to_neon.py --dry-run    # Show what would happen without writing to remote

Tables synced: all content app tables (see SYNC_APPS below).
To add more apps: append to SYNC_APPS.
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
MEDIA_DIR = BASE_DIR / 'media'

# Apps whose data is synced to Neon. Add more app labels here as needed.
SYNC_APPS = ['content']

# Deletion order for clearing Neon content tables (children before parents).
# Review.restaurant has on_delete=PROTECT, so reviews must be deleted before restaurants.
CLEAR_SCRIPT = """\
from content.models import (
    ReviewDraft, Image,
    ReviewDish, ReviewTag, Review,
    RestaurantDish, Restaurant,
    EncyclopediaVersion, EncyclopediaTag, Encyclopedia,
    RecipeVersion, RecipeTag, Recipe, Tag,
)
Image.objects.all().delete()
ReviewDraft.objects.all().delete()
ReviewDish.objects.all().delete()
ReviewTag.objects.all().delete()
Review.objects.all().delete()
RestaurantDish.objects.all().delete()
Restaurant.objects.all().delete()
EncyclopediaVersion.objects.all().delete()
EncyclopediaTag.objects.all().delete()
Encyclopedia.objects.all().delete()
RecipeVersion.objects.all().delete()
RecipeTag.objects.all().delete()
Recipe.objects.all().delete()
Tag.objects.all().delete()
print('Content tables cleared')
"""


def read_dotenv():
    env_path = BASE_DIR / '.env'
    result = {}
    if env_path.exists():
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, val = line.partition('=')
                result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def build_local_env(dotenv):
    """Subprocess env that uses the local Postgres (DB_* vars, no DATABASE_URL)."""
    e = os.environ.copy()
    # Empty string causes settings.py `if env('DATABASE_URL', default=None):` to be falsy,
    # so it falls through to DB_* vars even if .env also has DATABASE_URL.
    e['DATABASE_URL'] = ''
    e['PYTHONIOENCODING'] = 'utf-8'
    e['PYTHONUTF8'] = '1'
    for key in ('DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT'):
        if key not in e and key in dotenv:
            e[key] = dotenv[key]
    return e


def build_neon_env(neon_url):
    """Subprocess env that points to Neon via DATABASE_URL."""
    e = os.environ.copy()
    e['DATABASE_URL'] = neon_url
    e['PYTHONIOENCODING'] = 'utf-8'
    e['PYTHONUTF8'] = '1'
    return e


def run(args, env):
    return subprocess.run(args, env=env, capture_output=True, text=True, encoding='utf-8')


def sync_db(dotenv, neon_url, dry_run):
    print('[DB] Syncing content data: local -> Neon')

    local = build_local_env(dotenv)
    neon = build_neon_env(neon_url)
    dump_file = BASE_DIR / '_sync_dump.json'

    print('  [1/3] Dumping from local database...')
    result = run(
        [sys.executable, 'manage.py', 'dumpdata',
         '--natural-foreign', '--natural-primary', '--indent', '2',
         '--output', str(dump_file)] + SYNC_APPS,
        env=local,
    )
    if result.returncode != 0:
        print('  [ERROR] dumpdata failed:')
        print(result.stderr or result.stdout)
        dump_file.unlink(missing_ok=True)
        return False

    size_mb = dump_file.stat().st_size / 1024 / 1024
    print(f'  Dumped {size_mb:.2f} MB')

    if dry_run:
        print('  [DRY RUN] Skipping Neon clear and load.')
        dump_file.unlink(missing_ok=True)
        return True

    print('  [2/4] Applying migrations on Neon...')
    result = run([sys.executable, 'manage.py', 'migrate', '--run-syncdb'], env=neon)
    if result.returncode != 0:
        print('  [ERROR] migrate failed:')
        print(result.stderr or result.stdout)
        dump_file.unlink(missing_ok=True)
        return False

    print('  [3/4] Clearing content tables on Neon...')
    result = run(
        [sys.executable, 'manage.py', 'shell', '-c', CLEAR_SCRIPT],
        env=neon,
    )
    if result.returncode != 0:
        print('  [ERROR] Failed to clear Neon content tables:')
        print(result.stderr or result.stdout)
        dump_file.unlink(missing_ok=True)
        return False
    print('  ', (result.stdout or '').strip())

    print('  [4/4] Loading data into Neon...')
    result = run(
        [sys.executable, 'manage.py', 'loaddata', str(dump_file)],
        env=neon,
    )
    dump_file.unlink(missing_ok=True)

    if result.returncode != 0:
        print('  [ERROR] loaddata failed:')
        print(result.stderr or result.stdout)
        return False

    print('  ', (result.stdout or '').strip())
    return True


def sync_media(dotenv, dry_run):
    """Upload new/changed local media files to Cloudflare R2 (skips unchanged by size)."""
    import boto3
    from botocore.exceptions import ClientError

    print('[MEDIA] Syncing media files: local -> Cloudflare R2')

    def get(key):
        return os.environ.get(key) or dotenv.get(key, '')

    bucket = get('CLOUDFLARE_R2_BUCKET_NAME')
    endpoint = get('CLOUDFLARE_R2_ENDPOINT_URL')
    access_key = get('CLOUDFLARE_R2_ACCESS_KEY_ID')
    secret_key = get('CLOUDFLARE_R2_SECRET_ACCESS_KEY')

    if not all([bucket, endpoint, access_key, secret_key]):
        print('  [ERROR] Cloudflare R2 credentials missing from .env')
        print('  Required: CLOUDFLARE_R2_BUCKET_NAME, CLOUDFLARE_R2_ENDPOINT_URL,')
        print('            CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY')
        return False

    if not MEDIA_DIR.exists():
        print('  [SKIP] No local media/ directory found')
        return True

    s3 = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    # Index existing R2 objects by key → size for incremental sync
    existing = {}
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get('Contents', []):
                existing[obj['Key']] = obj['Size']
    except ClientError as e:
        print(f'  [ERROR] Failed to list R2 bucket: {e}')
        return False

    local_files = [f for f in MEDIA_DIR.rglob('*') if f.is_file()]
    uploaded = skipped = errors = 0

    for local_path in local_files:
        r2_key = local_path.relative_to(MEDIA_DIR).as_posix()
        local_size = local_path.stat().st_size

        if r2_key in existing and existing[r2_key] == local_size:
            skipped += 1
            continue

        if dry_run:
            print(f'  [DRY RUN] Would upload: {r2_key}')
            uploaded += 1
            continue

        try:
            s3.upload_file(str(local_path), bucket, r2_key)
            uploaded += 1
        except ClientError as e:
            print(f'  [ERROR] Failed to upload {r2_key}: {e}')
            errors += 1

    print(f'  Uploaded: {uploaded}, Skipped (unchanged): {skipped}', end='')
    if errors:
        print(f', Errors: {errors}')
    else:
        print()

    return errors == 0


def main():
    flags = set(sys.argv[1:])
    dry_run = '--dry-run' in flags
    db_only = '--db-only' in flags
    media_only = '--media-only' in flags

    dotenv = read_dotenv()

    # NEON_DATABASE_URL is preferred so local dev can keep DATABASE_URL unset.
    # Falls back to DATABASE_URL if NEON_DATABASE_URL is absent.
    neon_url = (
        os.environ.get('NEON_DATABASE_URL')
        or dotenv.get('NEON_DATABASE_URL')
        or os.environ.get('DATABASE_URL')
        or dotenv.get('DATABASE_URL', '')
    )

    if not neon_url and not media_only:
        print('[ERROR] Neon connection URL not found.')
        print('Add NEON_DATABASE_URL=<your-neon-url> to your .env file.')
        sys.exit(1)

    if dry_run:
        print('--- DRY RUN (no remote changes) ---\n')

    ok = True

    if not media_only:
        ok = sync_db(dotenv, neon_url, dry_run) and ok
        print()

    if not db_only:
        ok = sync_media(dotenv, dry_run) and ok
        print()

    if ok:
        print('[OK] Sync complete!')
    else:
        print('[FAILED] Sync completed with errors.')
        sys.exit(1)


if __name__ == '__main__':
    main()
