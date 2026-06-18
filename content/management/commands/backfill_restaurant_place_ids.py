import time
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from content.models import Restaurant


class Command(BaseCommand):
    help = 'Backfill google_place_id for restaurants that are missing one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be updated without writing to the database',
        )

    def _safe(self, s):
        enc = getattr(self.stdout, 'encoding', None) or 'ascii'
        return s.encode(enc, errors='replace').decode(enc)

    def _find_place_id(self, restaurant, api_key):
        parts = [restaurant.name]
        if restaurant.street_address:
            parts.append(restaurant.street_address)
        if restaurant.city:
            parts.append(restaurant.city)
        query = ', '.join(parts)

        response = requests.get(
            'https://maps.googleapis.com/maps/api/place/findplacefromtext/json',
            params={
                'input': query,
                'inputtype': 'textquery',
                'fields': 'place_id',
                'key': api_key,
            },
            timeout=10,
        )
        data = response.json()
        if data.get('status') == 'OK' and data.get('candidates'):
            return data['candidates'][0]['place_id']
        return None

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
        if not api_key:
            self.stdout.write(self.style.ERROR('GOOGLE_MAPS_API_KEY is not configured.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no records will be updated\n'))

        restaurants = Restaurant.objects.filter(google_place_id='').exclude(name__regex=r'^\d{4}\.').order_by('name')
        total = restaurants.count()
        self.stdout.write(f'Found {total} restaurants without a place ID.\n')

        updated = 0
        not_found = 0

        for restaurant in restaurants:
            try:
                place_id = self._find_place_id(restaurant, api_key)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  [error] {self._safe(str(restaurant))} - {e}'))
                not_found += 1
                continue

            if place_id:
                if not dry_run:
                    Restaurant.objects.filter(pk=restaurant.pk).update(google_place_id=place_id)
                self.stdout.write(
                    f'  [{"dry" if dry_run else "updated"}] {self._safe(str(restaurant))} -> {place_id}'
                )
                updated += 1
            else:
                self.stdout.write(f'  [not found] {self._safe(str(restaurant))}')
                not_found += 1

            # Stay well within the Places API QPS limit
            time.sleep(0.2)

        label = 'would update' if dry_run else 'updated'
        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {updated} {label}, {not_found} not found / errored.'
        ))
