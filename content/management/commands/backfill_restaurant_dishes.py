from django.core.management.base import BaseCommand
from content.models import ReviewDish, RestaurantDish


class Command(BaseCommand):
    help = 'Backfill RestaurantDish records from existing ReviewDish entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be created without writing to the database',
        )

    def _safe(self, s):
        enc = getattr(self.stdout, 'encoding', None) or 'ascii'
        return s.encode(enc, errors='replace').decode(enc)

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no records will be created\n'))

        review_dishes = (
            ReviewDish.objects
            .select_related('review__restaurant', 'encyclopedia_entry')
            .all()
        )

        created = 0
        skipped = 0

        for rd in review_dishes:
            dish_name = rd.dish_name or (rd.encyclopedia_entry.name if rd.encyclopedia_entry else '')
            if not dish_name:
                skipped += 1
                continue

            restaurant = rd.review.restaurant

            already_exists = RestaurantDish.objects.filter(
                restaurant=restaurant,
                dish_name=dish_name,
                review=rd.review,
                status=RestaurantDish.STATUS_HAD,
            ).exists()

            if already_exists:
                skipped += 1
                continue

            if not dry_run:
                RestaurantDish.objects.create(
                    restaurant=restaurant,
                    dish_name=dish_name,
                    encyclopedia_entry=rd.encyclopedia_entry,
                    status=RestaurantDish.STATUS_HAD,
                    review=rd.review,
                    source='review',
                )

            self.stdout.write(
                f'  [{"dry" if dry_run else "created"}] '
                f'{self._safe(dish_name)} @ {self._safe(restaurant.name)} (review #{rd.review.id})'
            )
            created += 1

        label = 'would create' if dry_run else 'created'
        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {created} {label}, {skipped} skipped (already exist or no dish name).'
        ))
