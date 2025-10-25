#!/usr/bin/env python
"""Quick script to verify review import"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from content.models import Review, ReviewDish

reviews = Review.objects.filter(metadata__confluence_page_id__isnull=False).order_by('visit_date')

print(f'Total Confluence reviews: {reviews.count()}\n')
print('Imported Reviews:\n')

for review in reviews:
    print(f'{review.restaurant_name}')
    print(f'  -> Visit Date: {review.visit_date}')
    print(f'  -> Entry Time: {review.entry_time}')
    print(f'  -> Party Size: {review.party_size}')
    print(f'  -> Location: {review.location}')
    print(f'  -> Overall Rating: {review.rating}/100')

    dishes = review.review_dishes.all()
    print(f'  -> Dishes: {dishes.count()}')

    for dish in dishes:
        if dish.encyclopedia_entry:
            dish_display = f'Linked to {dish.encyclopedia_entry.name}'
        elif dish.dish_name:
            dish_display = f'"{dish.dish_name}" (Not linked)'
        else:
            dish_display = 'Not linked'
        print(f'      * Rating: {dish.dish_rating}/100, Cost: ${dish.cost}, {dish_display}')
        if dish.notes:
            preview = dish.notes[:80].replace('\n', ' ')
            print(f'        Notes: {preview}...')
    print()
