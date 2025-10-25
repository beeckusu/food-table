"""
Management command to export all Confluence reviews to JSON file.

Usage:
    python manage.py export_confluence_reviews --parent-page-id 99811341
    python manage.py export_confluence_reviews --parent-page-id 99811341 --output custom_export.json
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from content.utils.importers import ConfluenceAPIImporter
from content.utils.parsers import ConfluenceStorageParser


class Command(BaseCommand):
    help = 'Export all restaurant reviews from Confluence to JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--parent-page-id',
            type=str,
            required=True,
            help='Confluence parent page ID to export from',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='confluence_reviews_export.json',
            help='Output JSON file name (default: confluence_reviews_export.json)',
        )

    def handle(self, *args, **options):
        parent_page_id = options['parent_page_id']
        output_filename = options['output']
        output_path = Path(settings.BASE_DIR) / output_filename

        self.stdout.write(f'Fetching all pages from Confluence parent page: {parent_page_id}')

        # Fetch all pages using importer
        try:
            importer = ConfluenceAPIImporter(parent_page_id)
            pages = importer.fetch_reviews()
            source_info = importer.get_source_info()
        except Exception as e:
            raise CommandError(f'Failed to fetch pages: {str(e)}')

        self.stdout.write(self.style.SUCCESS(f'Fetched {len(pages)} pages'))

        # Test parsing on each page and add metadata
        parser = ConfluenceStorageParser()
        parseable_count = 0
        unparseable_count = 0
        main_review_count = 0
        followup_count = 0

        for page in pages:
            page_id = page.get('id')
            body = page.get('body', '')
            is_followup = page.get('is_followup', False)

            # Count main reviews vs follow-ups
            if is_followup:
                followup_count += 1
            else:
                main_review_count += 1

            # Try to parse the page
            parsed_data = parser.parse(page_id, body)

            if parsed_data:
                page['_parse_status'] = 'success'
                page['_dish_count'] = len(parsed_data.dishes)
                parseable_count += 1
            else:
                page['_parse_status'] = 'failed'
                page['_dish_count'] = 0
                unparseable_count += 1

        # Build export data
        export_data = {
            'export_info': {
                **source_info,
                'parseable_pages': parseable_count,
                'unparseable_pages': unparseable_count,
                'main_reviews': main_review_count,
                'followup_visits': followup_count,
            },
            'pages': pages
        }

        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f'\nExport complete!'))
        self.stdout.write(f'  Output file: {output_path}')
        self.stdout.write(f'  Total pages: {len(pages)}')
        self.stdout.write(f'    - Main reviews: {main_review_count}')
        self.stdout.write(f'    - Follow-up visits: {followup_count}')
        self.stdout.write(f'  Parseable pages: {parseable_count}')
        self.stdout.write(f'  Unparseable pages: {unparseable_count}')

        if unparseable_count > 0:
            self.stdout.write(self.style.WARNING(
                f'\n{unparseable_count} pages could not be parsed. '
                'They are included in the export with _parse_status="failed".'
            ))
