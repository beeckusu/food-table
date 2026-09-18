from django.db import migrations


def backfill_menu_items(apps, schema_editor):
    """
    Create/reuse one MenuItem per (restaurant, dish name) and point every
    existing ReviewDish at it, so FT-192's consolidation applies to
    historical reviews too.

    ReviewDish itself never stored which restaurant a dish was tried at
    (that's the whole gap this migration is fixing), so the restaurant has
    to be reconstructed:
      1. A RestaurantDish created alongside the same review/dish name (this
         is how every dish, festival or not, has been tracked since the
         wishlist feature shipped).
      2. The review's own restaurant, for non-festival reviews.
      3. Any RestaurantDish for the same food festival + dish name, ignoring
         the review (covers a dish renamed after creation, since renames
         never touched the original RestaurantDish).
      4. A placeholder "Unknown vendor" restaurant for that festival, as a
         last resort so no dish is ever left without a MenuItem.
    """
    ReviewDish = apps.get_model('content', 'ReviewDish')
    RestaurantDish = apps.get_model('content', 'RestaurantDish')
    MenuItem = apps.get_model('content', 'MenuItem')
    Restaurant = apps.get_model('content', 'Restaurant')

    restaurant_by_review_and_name = {}
    restaurant_by_festival_and_name = {}
    for rd in RestaurantDish.objects.filter(review__isnull=False).only('review_id', 'dish_name', 'restaurant_id'):
        restaurant_by_review_and_name.setdefault((rd.review_id, rd.dish_name), rd.restaurant_id)
    for rd in RestaurantDish.objects.filter(food_festival__isnull=False).only('food_festival_id', 'dish_name', 'restaurant_id'):
        restaurant_by_festival_and_name.setdefault((rd.food_festival_id, rd.dish_name), rd.restaurant_id)

    unknown_vendor_by_festival = {}

    def resolve_restaurant_id(review, dish_name):
        restaurant_id = restaurant_by_review_and_name.get((review.id, dish_name))
        if restaurant_id:
            return restaurant_id
        if review.restaurant_id:
            return review.restaurant_id
        if review.food_festival_id:
            restaurant_id = restaurant_by_festival_and_name.get((review.food_festival_id, dish_name))
            if restaurant_id:
                return restaurant_id
            restaurant_id = unknown_vendor_by_festival.get(review.food_festival_id)
            if restaurant_id is None:
                festival_name = review.food_festival.name
                restaurant, _ = Restaurant.objects.get_or_create(
                    name=f'Unknown vendor ({festival_name})',
                    street_address='',
                )
                restaurant_id = restaurant.id
                unknown_vendor_by_festival[review.food_festival_id] = restaurant_id
            return restaurant_id
        return None

    menu_item_cache = {}

    for rd in ReviewDish.objects.select_related('review', 'review__food_festival', 'encyclopedia_entry').order_by('id'):
        review = rd.review
        name = (rd.dish_name or '').strip()
        if not name and rd.encyclopedia_entry_id:
            name = rd.encyclopedia_entry.name
        if not name:
            name = 'Unnamed Dish'

        restaurant_id = resolve_restaurant_id(review, rd.dish_name)
        name_key = name.lower()
        cache_key = (restaurant_id, name_key)

        menu_item_id = menu_item_cache.get(cache_key)
        if menu_item_id is None:
            menu_item, created = MenuItem.objects.get_or_create(
                restaurant_id=restaurant_id,
                name_key=name_key,
                defaults={'name': name, 'encyclopedia_entry_id': rd.encyclopedia_entry_id},
            )
            if not created and menu_item.encyclopedia_entry_id is None and rd.encyclopedia_entry_id:
                menu_item.encyclopedia_entry_id = rd.encyclopedia_entry_id
                menu_item.save(update_fields=['encyclopedia_entry_id'])
            menu_item_id = menu_item.id
            menu_item_cache[cache_key] = menu_item_id

        rd.menu_item_id = menu_item_id
        rd.save(update_fields=['menu_item_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0036_reviewdish_menu_item'),
    ]

    operations = [
        migrations.RunPython(backfill_menu_items, migrations.RunPython.noop),
    ]
