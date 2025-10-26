"""Show encyclopedia hierarchy"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from content.models import Encyclopedia

def show_tree(entry, level=0):
    indent = '  ' * level
    metadata = entry.metadata or {}
    confluence_id = metadata.get('confluence_page_id', 'N/A')
    print(f'{indent}{entry.name} (ID: {entry.id}, Confluence: {confluence_id})')

    # Show some details for entries with content
    if entry.description:
        desc_preview = entry.description[:60].replace('\n', ' ')
        print(f'{indent}  > Description: {desc_preview}...')

    for child in entry.children.all().order_by('name'):
        show_tree(child, level + 1)

print('='*70)
print('ENCYCLOPEDIA HIERARCHY')
print('='*70)

# Show all root entries (parent=None)
roots = Encyclopedia.objects.filter(parent=None).order_by('name')
print(f'\nTotal entries: {Encyclopedia.objects.count()}')
print(f'Root entries: {roots.count()}\n')

for root in roots:
    show_tree(root)
    print()
