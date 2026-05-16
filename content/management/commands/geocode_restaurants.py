from django.core.management.base import BaseCommand
from content.models import Restaurant


class Command(BaseCommand):
    help = 'Geocode restaurants that are missing coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Re-geocode all restaurants, not just those missing coordinates',
        )

    def _safe(self, s):
        enc = getattr(self.stdout, 'encoding', None) or 'ascii'
        return s.encode(enc, errors='replace').decode(enc)

    def handle(self, *args, **options):
        qs = Restaurant.objects.all()
        if not options['all']:
            qs = qs.filter(latitude=None)

        total = qs.count()
        if total == 0:
            self.stdout.write('No restaurants to geocode.')
            return

        self.stdout.write(f'Geocoding {total} restaurant(s)...')
        success = 0
        skipped = 0

        for restaurant in qs:
            old_lat = restaurant.latitude
            restaurant._geocode()
            if restaurant.latitude is not None:
                Restaurant.objects.filter(pk=restaurant.pk).update(
                    latitude=restaurant.latitude,
                    longitude=restaurant.longitude,
                )
                if old_lat is None:
                    self.stdout.write(f'  [OK] {self._safe(restaurant.name)} -> ({restaurant.latitude:.4f}, {restaurant.longitude:.4f})')
                else:
                    self.stdout.write(f'  [updated] {self._safe(restaurant.name)} -> ({restaurant.latitude:.4f}, {restaurant.longitude:.4f})')
                success += 1
            else:
                self.stdout.write(self.style.WARNING(f'  [skip] {self._safe(restaurant.name)} - no address or geocode failed'))
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f'\nDone: {success} geocoded, {skipped} skipped.'))
