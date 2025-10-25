"""
Management command to import review entries from Confluence export JSON.

Usage:
    python manage.py import_confluence_reviews --dry-run
    python manage.py import_confluence_reviews --json-file confluence_reviews_export.json
    python manage.py import_confluence_reviews --parent-page-id 99811341
"""

from pathlib import Path
from typing import List

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings

from content.models import Review, ReviewDish, Image
from content.utils.importers import ConfluenceAPIImporter, JSONFileImporter
from content.utils.parsers import ConfluenceStorageParser, ConfluenceMarkdownParser
from content.utils.confluence_api import ConfluenceClient


class Command(BaseCommand):
    help = 'Import restaurant reviews from Confluence JSON export'

    def __init__(self):
        super().__init__()
        self.stats = {
            'reviews_created': 0,
            'reviews_skipped': 0,
            'dishes_created': 0,
            'errors': 0,
        }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be imported without creating entries',
        )
        parser.add_argument(
            '--json-file',
            type=str,
            help='Path to Confluence export JSON file',
        )
        parser.add_argument(
            '--parent-page-id',
            type=str,
            help='Fetch reviews from Confluence parent page ID (requires API credentials)',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to set as created_by (default: first superuser)',
        )

    def handle(self, *args, **options):
        # Setup
        self.dry_run = options['dry_run']
        json_file = options.get('json_file')
        parent_page_id = options.get('parent_page_id')

        # Validate arguments: must provide either --json-file or --parent-page-id
        if not json_file and not parent_page_id:
            raise CommandError(
                'Must provide either --json-file or --parent-page-id.\n'
                'Examples:\n'
                '  python manage.py import_confluence_reviews --json-file confluence_reviews_export.json\n'
                '  python manage.py import_confluence_reviews --parent-page-id 99811341'
            )

        if json_file and parent_page_id:
            raise CommandError('Cannot use both --json-file and --parent-page-id. Choose one.')

        # Select and use appropriate importer
        if parent_page_id:
            # Use Confluence API importer
            self.stdout.write(f'Fetching reviews from Confluence parent page: {parent_page_id}')
            importer = ConfluenceAPIImporter(parent_page_id)
        else:
            # Use JSON file importer
            json_path = Path(settings.BASE_DIR) / json_file
            if not json_path.exists():
                raise CommandError(f'JSON file not found: {json_path}')

            self.stdout.write(f'Loading data from: {json_path}')
            importer = JSONFileImporter(json_path)

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

        # Fetch pages from importer
        try:
            pages = importer.fetch_reviews()
            source_info = importer.get_source_info()
        except Exception as e:
            raise CommandError(f'Failed to fetch reviews: {str(e)}')

        total_pages = len(pages)
        self.stdout.write(self.style.SUCCESS(f'Starting import of {total_pages} restaurant reviews'))
        self.stdout.write(f'Source: {source_info.get("source", "Unknown")}')

        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Create parsers
        storage_parser = ConfluenceStorageParser()
        markdown_parser = ConfluenceMarkdownParser()

        try:
            for page_data in pages:
                # Select appropriate parser based on content format
                content_format = page_data.get('format', 'markdown')
                body = page_data.get('body', '')

                if content_format == 'storage':
                    parser = storage_parser
                else:
                    parser = markdown_parser

                self.import_review(page_data, parser)

            # Print statistics
            self.print_stats()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Import failed: {str(e)}'))
            raise

    def import_review(self, page_data, parser):
        """Import a single review page using the provided parser"""
        page_id = page_data.get('id')
        restaurant_name = page_data.get('title', '')
        body = page_data.get('body', '')

        self.stdout.write(f'Processing: {restaurant_name}')

        # Parse content using the provided parser
        parsed_data = parser.parse(page_id, body)

        if not parsed_data:
            self.stdout.write(self.style.ERROR(f'  Could not parse review data for {restaurant_name}'))
            self.stats['errors'] += 1
            return

        if not parsed_data.dishes:
            self.stdout.write(self.style.WARNING(f'  No dishes found in {restaurant_name}'))

        # Build review data for Django model
        review_data = {
            'restaurant_name': restaurant_name,
            'visit_date': parsed_data.visit_date,
            'entry_time': parsed_data.entry_time,
            'party_size': parsed_data.party_size,
            'address': parsed_data.address,
            'location': parsed_data.location,
            'rating': parsed_data.rating,
            'notes': parsed_data.notes,
            'created_by': self.user,
            'metadata': {
                'confluence_page_id': page_id,
                'confluence_url': f'https://gavinlu.atlassian.net/wiki/spaces/CE/pages/{page_id}',
                'website': parsed_data.website,
                'dish_count': len(parsed_data.dishes),
            }
        }

        if self.dry_run:
            self.stdout.write(self.style.SUCCESS(f'  Would create review: {restaurant_name}'))
            self.stdout.write(f'    Visit Date: {parsed_data.visit_date}')
            self.stdout.write(f'    Entry Time: {parsed_data.entry_time}')
            self.stdout.write(f'    Party Size: {parsed_data.party_size}')
            self.stdout.write(f'    Overall Rating: {parsed_data.rating}')
            self.stdout.write(f'    Dishes: {len(parsed_data.dishes)}')
            for dish in parsed_data.dishes:
                # Handle Unicode characters safely
                dish_name = dish.name.encode('ascii', 'replace').decode('ascii')
                self.stdout.write(f'      - {dish_name}: {dish.rating}/100 (${dish.cost})')
            return

        # Check if review already exists (by restaurant name + visit date)
        existing = Review.objects.filter(
            restaurant_name=restaurant_name,
            visit_date=parsed_data.visit_date
        ).first()

        if existing:
            self.stdout.write(self.style.WARNING(f'  Skipping existing review'))
            self.stats['reviews_skipped'] += 1
            return

        # Create review
        try:
            review = Review.objects.create(**review_data)
            self.stdout.write(self.style.SUCCESS(f'  Created review: {restaurant_name}'))
            self.stats['reviews_created'] += 1

            # Create ReviewDish entries
            review_dishes = []
            for dish in parsed_data.dishes:
                try:
                    review_dish = ReviewDish.objects.create(
                        review=review,
                        encyclopedia_entry=None,  # Manual linking later
                        dish_name=dish.name,
                        dish_rating=dish.rating,
                        cost=dish.cost,
                        notes=dish.notes
                    )
                    review_dishes.append((review_dish, dish))
                    self.stats['dishes_created'] += 1
                    # Handle Unicode characters safely
                    dish_name = dish.name.encode('ascii', 'replace').decode('ascii')
                    self.stdout.write(f'    Added dish: {dish_name}')
                except Exception as e:
                    err_dish_name = dish.name.encode('ascii', 'replace').decode('ascii')
                    self.stdout.write(self.style.WARNING(f'    Error adding dish {err_dish_name}: {str(e)}'))

            # Download and attach images if any
            if parsed_data.restaurant_images or any(dish.images for dish in parsed_data.dishes):
                self.download_and_attach_images(page_id, review, review_dishes, parsed_data)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error creating review: {str(e)}'))
            self.stats['errors'] += 1

    def download_and_attach_images(self, page_id, review, review_dishes, parsed_data):
        """
        Download images from Confluence and attach them to Review and ReviewDish objects.

        Args:
            page_id: Confluence page ID
            review: Created Review object
            review_dishes: List of tuples (ReviewDish object, ParsedDish data)
            parsed_data: ParsedReviewData with image paths
        """
        try:
            # Initialize Confluence client
            client = ConfluenceClient()

            # Download all images for this page
            output_dir = Path(settings.MEDIA_ROOT) / 'reviews' / page_id
            downloaded_images = client.download_page_images(page_id, output_dir)

            if not downloaded_images:
                return

            self.stdout.write(f'    Downloaded {len(downloaded_images)} images')

            # Create Image objects for restaurant images
            for img_path in parsed_data.restaurant_images:
                filename = Path(img_path).name
                if filename in downloaded_images:
                    Image.objects.create(
                        image=downloaded_images[filename],
                        caption=f'{review.restaurant_name} - Restaurant',
                        content_object=review,
                        uploaded_by=self.user,
                        order=0
                    )
                    self.stdout.write(f'      Attached restaurant image: {filename}')

            # Create Image objects for dish images
            for review_dish, parsed_dish in review_dishes:
                for img_path in parsed_dish.images:
                    filename = Path(img_path).name
                    if filename in downloaded_images:
                        Image.objects.create(
                            image=downloaded_images[filename],
                            caption=f'{parsed_dish.name}',
                            content_object=review_dish,
                            uploaded_by=self.user,
                            order=0
                        )
                        self.stdout.write(f'      Attached dish image: {filename} to {parsed_dish.name}')

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'    Error downloading images: {str(e)}'))

    def print_stats(self):
        """Print import statistics"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Import Statistics:'))
        self.stdout.write(f'  Reviews created: {self.stats["reviews_created"]}')
        self.stdout.write(f'  Reviews skipped: {self.stats["reviews_skipped"]}')
        self.stdout.write(f'  Dishes created: {self.stats["dishes_created"]}')
        self.stdout.write(f'  Errors encountered: {self.stats["errors"]}')
        self.stdout.write('='*60 + '\n')

        if not self.dry_run and self.stats['reviews_created'] > 0:
            self.stdout.write(self.style.SUCCESS(
                '\nImport complete! Next steps:'
            ))
            self.stdout.write('  - Visit admin to link dishes to encyclopedia entries')
            self.stdout.write('  - Upload images for reviews')
            self.stdout.write('  - Add tags to reviews')
            self.stdout.write('  - Verify reviews display correctly on frontend\n')
