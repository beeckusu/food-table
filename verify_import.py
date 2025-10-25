#!/usr/bin/env python
"""Quick script to verify encyclopedia import"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from content.models import Encyclopedia

# Filter to only show Confluence-imported entries
entries = Encyclopedia.objects.filter(metadata__confluence_page_id__isnull=False).order_by('parent__id', 'name')

print(f'Total Confluence entries: {entries.count()}\n')
print('Imported Hierarchy:\n')

for entry in entries:
    level = 0
    current = entry
    while current.parent:
        level += 1
        current = current.parent

    indent = '  ' * level
    parent_name = entry.parent.name if entry.parent else 'None'
    print(f'{indent}{entry.name}')
    print(f'{indent}  -> Parent: {parent_name}')
    print(f'{indent}  -> Cuisine Type: {entry.cuisine_type}')
    print(f'{indent}  -> Region: {entry.region}')
    print(f'{indent}  -> Description length: {len(entry.description)} chars')
    print()
