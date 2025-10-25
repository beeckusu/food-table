"""
Management command to import encyclopedia entries from Confluence export JSON.

Usage:
    python manage.py import_confluence_encyclopedia --dry-run
    python manage.py import_confluence_encyclopedia --json-file confluence_encyclopedia_export.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings

from content.models import Encyclopedia


class Command(BaseCommand):
    help = 'Import encyclopedia entries from Confluence JSON export'

    def __init__(self):
        super().__init__()
        self.stats = {
            'created': 0,
            'skipped': 0,
            'errors': 0,
        }
        self.page_id_to_entry = {}  # Map Confluence page IDs to Encyclopedia entries

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be imported without creating entries',
        )
        parser.add_argument(
            '--json-file',
            type=str,
            default='confluence_encyclopedia_export.json',
            help='Path to Confluence export JSON file (default: confluence_encyclopedia_export.json)',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to set as created_by (default: first superuser)',
        )

    def handle(self, *args, **options):
        # Setup
        self.dry_run = options['dry_run']
        json_file = options['json_file']

        # Load JSON export
        json_path = Path(settings.BASE_DIR) / json_file
        if not json_path.exists():
            raise CommandError(f'JSON file not found: {json_path}')

        self.stdout.write(f'Loading data from: {json_path}')

        with open(json_path, 'r', encoding='utf-8') as f:
            self.export_data = json.load(f)

        # Get user for created_by field
        if options.get('user_id'):
            try:
                user = User.objects.get(id=options['user_id'])
            except User.DoesNotExist:
                raise CommandError(f'User with ID {options["user_id"]} not found')
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                raise CommandError('No superuser found. Create one or specify --user-id')

        self.user = user

        # Start import
        total_pages = self.export_data.get('export_info', {}).get('total_pages', 0)
        self.stdout.write(self.style.SUCCESS(f'Starting import of {total_pages} pages'))

        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        try:
            # Import pages in hierarchical order (level 0, then 1, then 2, etc.)
            pages = self.export_data.get('pages', [])

            # Sort by level to ensure parents are created before children
            pages_by_level = sorted(pages, key=lambda p: p.get('level', 0))

            for page_data in pages_by_level:
                self.import_page(page_data)

            # Print statistics
            self.print_stats()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Import failed: {str(e)}'))
            raise

    def import_page(self, page_data: Dict):
        """Import a single page as an Encyclopedia entry"""
        page_id = page_data.get('id')
        title = page_data.get('title', '')
        level = page_data.get('level', 0)
        body = page_data.get('body', '')
        parent_id = page_data.get('parent_id')

        indent = '  ' * level
        self.stdout.write(f'{indent}Processing: {title} (Level {level})')

        # Generate slug
        slug = slugify(title)

        # Check if entry already exists
        if Encyclopedia.objects.filter(slug=slug).exists():
            self.stdout.write(self.style.WARNING(f'{indent}  Skipping existing entry'))
            self.stats['skipped'] += 1
            # Store reference for children
            self.page_id_to_entry[page_id] = Encyclopedia.objects.get(slug=slug)
            return

        # Get parent entry if exists
        parent_entry = None
        if parent_id and parent_id in self.page_id_to_entry:
            parent_entry = self.page_id_to_entry[parent_id]

        # Parse page body
        sections = self.parse_page_body(body)

        # Determine cuisine_type from hierarchy
        cuisine_type = self.infer_cuisine_type(parent_entry, title, level)

        # Extract region from origin section
        region = self.extract_region(sections.get('origin', ''))

        # Build encyclopedia entry data
        entry_data = {
            'name': title,
            'slug': slug,
            'description': sections.get('description', ''),
            'parent': parent_entry,
            'cuisine_type': cuisine_type,
            'region': region,
            'cultural_significance': sections.get('cultural_significance', ''),
            'popular_examples': sections.get('popular_examples', ''),
            'history': sections.get('history', ''),
            'created_by': self.user,
            'metadata': {
                'confluence_page_id': page_id,
                'confluence_url': f'https://gavinlu.atlassian.net/wiki/spaces/CE/pages/{page_id}',
                'origin': sections.get('origin', ''),
                'variants': sections.get('variants', ''),
                'similar_dishes': sections.get('similar_dishes', ''),
            }
        }

        if self.dry_run:
            self.stdout.write(self.style.SUCCESS(f'{indent}  Would create: {title}'))
            self.stdout.write(f'{indent}    Parent: {parent_entry.name if parent_entry else "None"}')
            self.stdout.write(f'{indent}    Cuisine Type: {cuisine_type}')
            self.stdout.write(f'{indent}    Region: {region}')
            # Store a mock object for dry run so children can reference it
            # We use a simple dict with just the name attribute
            mock_entry = type('MockEntry', (), {'name': title, 'parent': parent_entry})()
            self.page_id_to_entry[page_id] = mock_entry
            return

        # Create entry
        try:
            entry = Encyclopedia.objects.create(**entry_data)
            self.stdout.write(self.style.SUCCESS(f'{indent}  Created: {title}'))
            self.stats['created'] += 1

            # Store reference for children
            self.page_id_to_entry[page_id] = entry

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'{indent}  Error creating entry: {str(e)}'))
            self.stats['errors'] += 1

    def parse_page_body(self, body_content: str) -> Dict[str, str]:
        """Extract structured sections from Confluence page markdown"""
        if not body_content:
            return {}

        sections = {}

        # Extract sections by headers (markdown format)
        section_patterns = {
            'description': r'###\s*\*?\*?Description\*?\*?\s*\n+(.*?)(?=\n###|\n---|\Z)',
            'origin': r'###\s*\*?\*?Origin\*?\*?\s*\n+(.*?)(?=\n###|\n---|\Z)',
            'cultural_significance': r'###\s*\*?\*?Cultural Significance\*?\*?\s*\n+(.*?)(?=\n###|\n---|\Z)',
            'popular_examples': r'###\s*\*?\*?Popular Examples\*?\*?\s*\n+(.*?)(?=\n###|\n---|\Z)',
            'history': r'###\s*\*?\*?History\*?\*?\s*\n+(.*?)(?=\n###|\n---|\Z)',
            'similar_dishes': r'###\s*\*?\*?Similar Dishes.*?\*?\*?\s*\n+(.*?)(?=\n###|\n---|\Z)',
            'variants': r'###\s*\*?\*?Variants\*?\*?\s*\n+(.*?)(?=\n###|\n---|\Z)',
        }

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, body_content, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Clean up excessive whitespace and separators
                content = re.sub(r'\n---+\n', '\n\n', content)
                content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
                sections[section_name] = content[:5000]  # Limit length

        return sections

    def infer_cuisine_type(self, parent_entry: Optional[Encyclopedia], title: str, level: int) -> str:
        """Infer cuisine_type from the hierarchy"""
        # Level 0 is the root "Hello, World Cuisine" - no cuisine type
        # Level 1 are the cuisine categories (European, Asian, American, etc.)
        # Level 2+ inherit from their level 1 ancestor

        if level == 0:
            return ''

        if level == 1:
            # This is a top-level cuisine category
            return title

        # For deeper levels, find the level 1 ancestor
        if parent_entry:
            current = parent_entry
            # Walk up to find level 1 (which has parent but parent's parent is root or None)
            while current and current.parent and current.parent.parent:
                current = current.parent
            # If current.parent exists and current.parent.parent is None or root, current is level 1
            if current and current.parent:
                return current.name
            elif current:
                return current.name

        return ''

    def extract_region(self, origin_text: str) -> str:
        """Extract region/country from origin section"""
        if not origin_text:
            return ''

        # Common patterns for origin text
        # "* Switzerland" -> "Switzerland"
        # "* 1954, Toronto, Canada" -> "Canada"
        # "* United States, late 19th century" -> "United States"

        # Remove bullet points and asterisks
        text = origin_text.strip().lstrip('*').strip()

        # Try to extract country/region (usually the first or last major word/phrase)
        # Split by comma and take meaningful parts
        parts = [p.strip() for p in text.split(',')]

        # Common country/region names to look for
        regions = [
            'Switzerland', 'Canada', 'United States', 'France', 'Italy', 'Germany',
            'China', 'Japan', 'Korea', 'Vietnam', 'Thailand', 'Philippines',
            'Mexico', 'India', 'Spain', 'Greece', 'Turkey', 'Morocco',
        ]

        for part in parts:
            for region in regions:
                if region.lower() in part.lower():
                    return region

        # If no match, try to return first part before a date or long description
        if parts:
            first_part = parts[0]
            # Remove year patterns (4 digits, "century", etc.)
            first_part = re.sub(r'\d{4}', '', first_part)
            first_part = re.sub(r'\b\d+th\s+century\b', '', first_part, flags=re.IGNORECASE)
            first_part = first_part.strip()
            if first_part and len(first_part) < 50:
                return first_part

        return ''

    def print_stats(self):
        """Print import statistics"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Import Statistics:'))
        self.stdout.write(f'  Entries created: {self.stats["created"]}')
        self.stdout.write(f'  Entries skipped: {self.stats["skipped"]}')
        self.stdout.write(f'  Errors encountered: {self.stats["errors"]}')
        self.stdout.write('='*60 + '\n')

        if not self.dry_run and self.stats['created'] > 0:
            self.stdout.write(self.style.SUCCESS(
                '\nImport complete! Visit the admin interface to:'
            ))
            self.stdout.write('  - Review imported entries')
            self.stdout.write('  - Upload images')
            self.stdout.write('  - Add tags')
            self.stdout.write('  - Verify parent/child relationships\n')
