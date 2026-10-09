import json
from datetime import date, time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from content.models import (
    Encyclopedia, MenuItem, Restaurant, RestaurantDish, Review, ReviewDish,
)


def make_entry(name):
    return Encyclopedia.objects.create(
        name=name, slug=name.lower(), description=f'{name} description', is_placeholder=False,
    )


class RestaurantDishLinkApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.restaurant = Restaurant.objects.create(name='Noodle House')
        self.dish = RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Tonkotsu Ramen')
        self.entry = make_entry('Ramen')
        self.client = Client()
        self.client.login(username='staff', password='pw')

    def url(self, dish_id=None):
        return reverse('content:api_restaurant_dish_link', args=[dish_id or self.dish.pk])

    def post(self, body, dish_id=None):
        return self.client.post(self.url(dish_id), data=json.dumps(body), content_type='application/json')

    def test_requires_login(self):
        response = Client().post(self.url(), data='{}', content_type='application/json')
        self.assertNotEqual(response.status_code, 200)
        self.dish.refresh_from_db()
        self.assertIsNone(self.dish.encyclopedia_entry)

    def test_non_staff_cannot_link(self):
        User.objects.create_user('user', password='pw')
        client = Client()
        client.login(username='user', password='pw')
        response = client.post(self.url(), data=json.dumps({'encyclopedia_id': self.entry.pk}), content_type='application/json')
        self.assertNotEqual(response.status_code, 200)
        self.dish.refresh_from_db()
        self.assertIsNone(self.dish.encyclopedia_entry)

    def test_post_links_entry(self):
        response = self.post({'encyclopedia_id': self.entry.pk})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['dish']['encyclopedia_entry']['name'], 'Ramen')
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.encyclopedia_entry, self.entry)

    def test_delete_unlinks_entry(self):
        self.dish.encyclopedia_entry = self.entry
        self.dish.save()
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, 200)
        self.dish.refresh_from_db()
        self.assertIsNone(self.dish.encyclopedia_entry)

    def test_missing_encyclopedia_id_is_400(self):
        self.assertEqual(self.post({}).status_code, 400)

    def test_invalid_json_is_400(self):
        response = self.client.post(self.url(), data='not json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_unknown_dish_or_entry_is_404(self):
        self.assertEqual(self.post({'encyclopedia_id': self.entry.pk}, dish_id=99999).status_code, 404)
        self.assertEqual(self.post({'encyclopedia_id': 99999}).status_code, 404)


class AnticipatedDishListTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.ramen = make_entry('Ramen')
        self.noodle_house = Restaurant.objects.create(name='Noodle House')
        self.taco_stand = Restaurant.objects.create(name='Taco Stand')

        # Anticipated (wishlist) dishes
        self.linked = RestaurantDish.objects.create(
            restaurant=self.noodle_house, dish_name='Tonkotsu Ramen', encyclopedia_entry=self.ramen,
        )
        self.unlinked = RestaurantDish.objects.create(restaurant=self.taco_stand, dish_name='Al Pastor')
        # Already had: never anticipated
        RestaurantDish.objects.create(
            restaurant=self.noodle_house, dish_name='Gyoza', status=RestaurantDish.STATUS_HAD,
        )

        # A tried (reviewed) dish
        review = Review.objects.create(
            restaurant=self.noodle_house, visit_date=date(2025, 1, 15), entry_time=time(18, 30),
            party_size=2, rating=80, created_by=self.staff,
        )
        self.menu_item = MenuItem.objects.create(restaurant=self.noodle_house, name='Shoyu Ramen')
        ReviewDish.objects.create(review=review, menu_item=self.menu_item, dish_rating=90)

    def get(self, **params):
        return self.client.get(reverse('content:review_dish_list'), params)

    def names(self, response):
        return sorted(d.dish_name for d in response.context['review_dishes'])

    def test_default_lists_tried_dishes_only(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_anticipated'])
        self.assertEqual(self.names(response), ['Shoyu Ramen'])

    def test_anticipated_lists_wishlist_dishes_only(self):
        response = self.get(dish_kind='anticipated')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_anticipated'])
        self.assertEqual(self.names(response), ['Al Pastor', 'Tonkotsu Ramen'])
        self.assertEqual(response.context['total_dishes'], 2)
        self.assertEqual(response.context['anticipated_total'], 2)
        self.assertEqual(response.context['tried_total'], 1)

    def test_anticipated_link_status_filter(self):
        self.assertEqual(self.names(self.get(dish_kind='anticipated', link_status='linked')), ['Tonkotsu Ramen'])
        self.assertEqual(self.names(self.get(dish_kind='anticipated', link_status='unlinked')), ['Al Pastor'])

    def test_anticipated_search_matches_dish_and_classification(self):
        self.assertEqual(self.names(self.get(dish_kind='anticipated', search='pastor')), ['Al Pastor'])
        # "ramen" matches the linked encyclopedia entry too
        self.assertEqual(self.names(self.get(dish_kind='anticipated', search='Ramen')), ['Tonkotsu Ramen'])

    def test_anticipated_restaurant_search(self):
        self.assertEqual(self.names(self.get(dish_kind='anticipated', restaurant_search='taco')), ['Al Pastor'])

    def test_anticipated_ignores_tried_only_filters_and_sorts(self):
        response = self.get(dish_kind='anticipated', rating_min=95, cost_min=10, sort='rating_desc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.names(response), ['Al Pastor', 'Tonkotsu Ramen'])
        labels = [f['label'] for f in response.context['active_filters']]
        self.assertNotIn('Rating', labels)
        self.assertNotIn('Cost', labels)

    def test_anticipated_sorts(self):
        def ordered(sort):
            return [d.dish_name for d in self.get(dish_kind='anticipated', sort=sort).context['review_dishes']]
        self.assertEqual(ordered('name_asc'), ['Al Pastor', 'Tonkotsu Ramen'])
        self.assertEqual(ordered('restaurant_asc'), ['Tonkotsu Ramen', 'Al Pastor'])
        # Unlinked dishes sink to the bottom
        self.assertEqual(ordered('link_asc'), ['Tonkotsu Ramen', 'Al Pastor'])

    def test_anticipated_rows_use_restaurant_dish_link_endpoint(self):
        response = self.get(dish_kind='anticipated')
        self.assertContains(response, reverse('content:api_restaurant_dish_link', args=[self.unlinked.pk]))
        self.assertContains(response, reverse('content:api_restaurant_dish_link', args=[self.linked.pk]))

    def test_toggle_urls_keep_shared_filters(self):
        response = self.get(search='ramen', rating_min=50)
        self.assertEqual(response.context['anticipated_url'], '?search=ramen&dish_kind=anticipated')
        response = self.get(dish_kind='anticipated', search='ramen')
        self.assertEqual(response.context['tried_url'], '?search=ramen')


class RestaurantDetailClassificationTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.restaurant = Restaurant.objects.create(name='Noodle House')
        self.ramen = make_entry('Ramen')

    def test_wishlist_dish_shows_classification_badge(self):
        dish = RestaurantDish.objects.create(
            restaurant=self.restaurant, dish_name='Tonkotsu Ramen', encyclopedia_entry=self.ramen,
        )
        response = self.client.get(reverse('content:restaurant_detail', args=[self.restaurant.pk]))
        self.assertContains(response, 'encyclopedia-badge-linked')
        self.assertContains(response, reverse('content:api_restaurant_dish_link', args=[dish.pk]))
        self.assertContains(response, 'id="encyclopediaLinkModal"')

    def test_mark_tried_carries_classification_to_menu_item(self):
        dish = RestaurantDish.objects.create(
            restaurant=self.restaurant, dish_name='Tonkotsu Ramen', encyclopedia_entry=self.ramen,
        )
        menu_item = MenuItem.objects.create(restaurant=self.restaurant, name='tonkotsu ramen ')
        self.client.post(reverse('content:restaurant_dish_mark_tried', args=[self.restaurant.pk, dish.pk]))
        menu_item.refresh_from_db()
        self.assertEqual(menu_item.encyclopedia_entry, self.ramen)

    def test_mark_tried_does_not_overwrite_existing_menu_item_link(self):
        other = make_entry('Tsukemen')
        dish = RestaurantDish.objects.create(
            restaurant=self.restaurant, dish_name='Tonkotsu Ramen', encyclopedia_entry=self.ramen,
        )
        menu_item = MenuItem.objects.create(
            restaurant=self.restaurant, name='Tonkotsu Ramen', encyclopedia_entry=other,
        )
        self.client.post(reverse('content:restaurant_dish_mark_tried', args=[self.restaurant.pk, dish.pk]))
        menu_item.refresh_from_db()
        self.assertEqual(menu_item.encyclopedia_entry, other)


class RestaurantDishExcitementApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.restaurant = Restaurant.objects.create(name='Noodle House')
        self.dish = RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Tonkotsu Ramen')
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.url = reverse('content:api_restaurant_dish_excitement', args=[self.dish.pk])

    def post(self, body, client=None):
        return (client or self.client).post(self.url, data=json.dumps(body), content_type='application/json')

    def test_sets_and_clears_excitement(self):
        response = self.post({'excitement': 9})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['dish']['excitement'], 9)
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.excitement, 9)

        self.assertEqual(self.post({'excitement': None}).status_code, 200)
        self.dish.refresh_from_db()
        self.assertIsNone(self.dish.excitement)

    def test_rejects_out_of_range_or_non_integer(self):
        for bad in [0, 11, '3', 2.5, True]:
            self.assertEqual(self.post({'excitement': bad}).status_code, 400, bad)
        self.assertEqual(self.post({}).status_code, 400)
        self.dish.refresh_from_db()
        self.assertIsNone(self.dish.excitement)

    def test_non_staff_cannot_set(self):
        User.objects.create_user('user', password='pw')
        client = Client()
        client.login(username='user', password='pw')
        self.assertNotEqual(self.post({'excitement': 5}, client=client).status_code, 200)
        self.dish.refresh_from_db()
        self.assertIsNone(self.dish.excitement)

    def test_restaurant_page_shows_flames(self):
        self.dish.excitement = 3
        self.dish.save()
        response = self.client.get(reverse('content:restaurant_detail', args=[self.restaurant.pk]))
        self.assertContains(response, self.url)
        self.assertContains(response, 'data-value="3"')


class ExcitementSortTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')

        # Spike: a 10 plus a 2 (max 10, avg 6). Steady: 8 and 8 (max 8, avg 8).
        # Mild: one 3. Unrated: no excitement. Had: its 10 is already "had".
        self.spike = Restaurant.objects.create(name='Spike')
        self.steady = Restaurant.objects.create(name='Steady')
        self.mild = Restaurant.objects.create(name='Mild')
        self.unrated = Restaurant.objects.create(name='Unrated')
        self.had = Restaurant.objects.create(name='Had')
        for restaurant, levels in [(self.spike, [10, 2]), (self.steady, [8, 8]), (self.mild, [3]), (self.unrated, [None])]:
            for i, level in enumerate(levels):
                RestaurantDish.objects.create(restaurant=restaurant, dish_name=f'Dish {i}', excitement=level)
        RestaurantDish.objects.create(
            restaurant=self.had, dish_name='Old Favourite', excitement=10, status=RestaurantDish.STATUS_HAD,
        )

    def restaurant_names(self, sort):
        response = self.client.get(reverse('content:restaurant_list'), {'sort': sort})
        self.assertEqual(response.status_code, 200)
        return [r.name for r in response.context['restaurants']]

    def test_sort_by_most_exciting_dish(self):
        names = self.restaurant_names('excitement_max')
        self.assertEqual(names[:3], ['Spike', 'Steady', 'Mild'])
        # Restaurants without anticipated excitement come last
        self.assertCountEqual(names[3:], ['Unrated', 'Had'])

    def test_sort_by_average_excitement(self):
        names = self.restaurant_names('excitement_avg')
        self.assertEqual(names[:3], ['Steady', 'Spike', 'Mild'])
        self.assertCountEqual(names[3:], ['Unrated', 'Had'])

    def test_card_shows_excitement_summary(self):
        response = self.client.get(reverse('content:restaurant_list'), {'sort': 'excitement_max'})
        self.assertContains(response, '10 top &middot; 6.0 avg')

    def test_anticipated_dish_list_sorts_by_excitement(self):
        response = self.client.get(reverse('content:review_dish_list'), {'dish_kind': 'anticipated', 'sort': 'excitement_desc'})
        levels = [d.excitement for d in response.context['review_dishes']]
        self.assertEqual(levels, [10, 8, 8, 3, 2, None])


class ExcitementOnDishCreationTest(TestCase):
    """Excitement can be set wherever a wishlist dish is created or edited."""

    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.restaurant = Restaurant.objects.create(name='Noodle House')

    def test_restaurant_page_add_form(self):
        self.client.post(reverse('content:restaurant_dish_create', args=[self.restaurant.pk]), {
            'dish_name': 'Tonkotsu Ramen', 'status': RestaurantDish.STATUS_WISHLIST, 'notes': '', 'excitement': '8',
        })
        self.assertEqual(RestaurantDish.objects.get(dish_name='Tonkotsu Ramen').excitement, 8)

    def test_restaurant_page_add_form_without_rating(self):
        self.client.post(reverse('content:restaurant_dish_create', args=[self.restaurant.pk]), {
            'dish_name': 'Gyoza', 'status': RestaurantDish.STATUS_WISHLIST, 'notes': '', 'excitement': '',
        })
        self.assertIsNone(RestaurantDish.objects.get(dish_name='Gyoza').excitement)

    def test_edit_form_updates_or_preserves_excitement(self):
        dish = RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Ramen', excitement=5)
        url = reverse('content:restaurant_dish_update', args=[self.restaurant.pk, dish.pk])
        base = {'dish_name': 'Ramen', 'status': RestaurantDish.STATUS_WISHLIST, 'notes': ''}

        # Forms that don't post excitement (e.g. "had" dish edits) keep it
        self.client.post(url, base)
        dish.refresh_from_db()
        self.assertEqual(dish.excitement, 5)

        self.client.post(url, {**base, 'excitement': '9'})
        dish.refresh_from_db()
        self.assertEqual(dish.excitement, 9)

        # An explicitly empty value clears it
        self.client.post(url, {**base, 'excitement': ''})
        dish.refresh_from_db()
        self.assertIsNone(dish.excitement)

    def test_out_of_range_rejected_by_form(self):
        self.client.post(reverse('content:restaurant_dish_create', args=[self.restaurant.pk]), {
            'dish_name': 'Too Hype', 'status': RestaurantDish.STATUS_WISHLIST, 'notes': '', 'excitement': '11',
        })
        self.assertFalse(RestaurantDish.objects.filter(dish_name='Too Hype').exists())

    def test_restaurant_page_renders_pickers(self):
        RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Ramen', excitement=4)
        response = self.client.get(reverse('content:restaurant_detail', args=[self.restaurant.pk]))
        # Add form picker, and the edit modal's picker pre-filled with the saved value
        self.assertContains(response, 'class="excitement-value" name="excitement" value=""')
        self.assertContains(response, 'class="excitement-value" name="excitement" value="4"')
        # 4 lit flames in the list row + 4 in the edit modal
        self.assertContains(response, 'bi-fire text-danger', count=8)

    def test_new_restaurant_page_wishlist_dishes(self):
        url = reverse('content:restaurant_create')
        response = self.client.get(url)
        self.assertContains(response, 'name="wishlist-__prefix__-excitement"')
        self.assertContains(response, 'name="wishlist-0-excitement"')

        self.client.post(url, {
            'name': 'New Place', 'street_address': '', 'city': '', 'province': '', 'country': '', 'postal_code': '',
            'had-TOTAL_FORMS': '1', 'had-INITIAL_FORMS': '0', 'had-MIN_NUM_FORMS': '0', 'had-MAX_NUM_FORMS': '1000',
            'had-0-dish_name': '', 'had-0-notes': '',
            'wishlist-TOTAL_FORMS': '2', 'wishlist-INITIAL_FORMS': '0', 'wishlist-MIN_NUM_FORMS': '0', 'wishlist-MAX_NUM_FORMS': '1000',
            'wishlist-0-dish_name': 'Ramen', 'wishlist-0-source': '', 'wishlist-0-source_detail': '', 'wishlist-0-notes': '',
            'wishlist-0-excitement': '7',
            'wishlist-1-dish_name': 'Gyoza', 'wishlist-1-source': '', 'wishlist-1-source_detail': '', 'wishlist-1-notes': '',
            'wishlist-1-excitement': '',
        })
        restaurant = Restaurant.objects.get(name='New Place')
        self.assertEqual(restaurant.dishes.get(dish_name='Ramen').excitement, 7)
        self.assertIsNone(restaurant.dishes.get(dish_name='Gyoza').excitement)

    def test_food_festival_wishlist_add(self):
        from content.models import FoodFestival
        festival = FoodFestival.objects.create(name='Taste of the City')
        self.client.post(reverse('content:food_festival_dish_create', args=[festival.pk]), {
            'dish_name': 'Poutine', 'status': RestaurantDish.STATUS_WISHLIST, 'notes': '',
            'restaurant_name': 'Vendor Stall', 'excitement': '6',
        })
        self.assertEqual(RestaurantDish.objects.get(dish_name='Poutine').excitement, 6)


class WishlistBulkExcitementTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.url = reverse('content:api_wishlist_bulk_create')

    def post(self, body):
        return self.client.post(self.url, data=json.dumps(body), content_type='application/json')

    def test_new_dishes_get_excitement(self):
        response = self.post({
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': 'Ramen', 'excitement': 9}, {'name': 'Gyoza'}],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RestaurantDish.objects.get(dish_name='Ramen').excitement, 9)
        self.assertIsNone(RestaurantDish.objects.get(dish_name='Gyoza').excitement)

    def test_existing_dish_excitement_updated_only_when_given(self):
        restaurant = Restaurant.objects.create(name='Noodle House')
        dish = RestaurantDish.objects.create(restaurant=restaurant, dish_name='Ramen', excitement=3)

        self.post({'restaurant_id': restaurant.pk, 'dishes': [{'name': 'ramen'}]})
        dish.refresh_from_db()
        self.assertEqual(dish.excitement, 3)

        self.post({'restaurant_id': restaurant.pk, 'dishes': [{'name': 'ramen', 'excitement': 10}]})
        dish.refresh_from_db()
        self.assertEqual(dish.excitement, 10)

    def test_invalid_excitement_rejected_without_creating_anything(self):
        response = self.post({
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': 'Ramen', 'excitement': 11}],
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Restaurant.objects.filter(name='Noodle House').exists())

    def test_page_includes_picker_template(self):
        response = self.client.get(reverse('content:wishlist_bulk_add'))
        self.assertContains(response, 'id="wbExcitementTemplate"')


class ExcitementStatusFilterTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        restaurant = Restaurant.objects.create(name='Noodle House')
        RestaurantDish.objects.create(restaurant=restaurant, dish_name='Rated Ramen', excitement=7)
        RestaurantDish.objects.create(restaurant=restaurant, dish_name='Unrated Gyoza')
        RestaurantDish.objects.create(restaurant=restaurant, dish_name='Unrated Bao')
        RestaurantDish.objects.create(
            restaurant=restaurant, dish_name='Had Udon', status=RestaurantDish.STATUS_HAD,
        )

    def get(self, **params):
        return self.client.get(reverse('content:review_dish_list'), params)

    def names(self, response):
        return sorted(d.dish_name for d in response.context['review_dishes'])

    def test_unrated_filter(self):
        response = self.get(dish_kind='anticipated', excitement_status='unrated')
        self.assertEqual(self.names(response), ['Unrated Bao', 'Unrated Gyoza'])
        self.assertIn('Excitement', [f['label'] for f in response.context['active_filters']])

    def test_rated_filter(self):
        self.assertEqual(self.names(self.get(dish_kind='anticipated', excitement_status='rated')), ['Rated Ramen'])

    def test_unrated_shortcut_link(self):
        response = self.get(dish_kind='anticipated')
        self.assertEqual(response.context['unrated_total'], 2)
        self.assertContains(response, '2 not rated yet')
        self.assertContains(response, 'excitement_status=unrated')
        # Hidden once you're already looking at the unrated dishes
        self.assertNotContains(self.get(dish_kind='anticipated', excitement_status='unrated'), 'not rated yet')

    def test_ignored_in_tried_mode(self):
        response = self.get(excitement_status='unrated')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Excitement', [f['label'] for f in response.context['active_filters']])
        self.assertNotIn('excitement_status', response.context['anticipated_url'])

    def test_switching_to_tried_drops_excitement_filter(self):
        response = self.get(dish_kind='anticipated', excitement_status='unrated', search='bao')
        self.assertEqual(response.context['tried_url'], '?search=bao')
