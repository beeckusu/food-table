import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from content.models import Restaurant, RestaurantDish
from content.forms import RestaurantForm


def make_restaurant(**kwargs):
    defaults = {'name': 'Test Restaurant', 'city': 'Toronto', 'country': 'Canada'}
    defaults.update(kwargs)
    return Restaurant.objects.create(**defaults)


def make_dish(restaurant, **kwargs):
    defaults = {'dish_name': 'Test Dish', 'status': RestaurantDish.STATUS_WISHLIST}
    defaults.update(kwargs)
    return RestaurantDish.objects.create(restaurant=restaurant, **defaults)


class RestaurantModelTest(TestCase):
    def test_visited_defaults_false(self):
        r = make_restaurant()
        self.assertFalse(r.visited)

    def test_visited_can_be_set(self):
        r = make_restaurant(visited=True)
        self.assertTrue(r.visited)

    def test_str(self):
        r = make_restaurant(name='Ramen Place', city='Toronto', country='Canada')
        self.assertIn('Ramen Place', str(r))


class RestaurantDishModelTest(TestCase):
    def setUp(self):
        self.restaurant = make_restaurant()

    def test_default_status_is_wishlist(self):
        dish = RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Ramen')
        self.assertEqual(dish.status, RestaurantDish.STATUS_WISHLIST)

    def test_status_choices_exist(self):
        self.assertIn(RestaurantDish.STATUS_HAD, dict(RestaurantDish.STATUS_CHOICES))
        self.assertIn(RestaurantDish.STATUS_WISHLIST, dict(RestaurantDish.STATUS_CHOICES))

    def test_str(self):
        dish = make_dish(self.restaurant, dish_name='Pho', status=RestaurantDish.STATUS_HAD)
        self.assertIn('Pho', str(dish))
        self.assertIn(self.restaurant.name, str(dish))

    def test_cascade_delete(self):
        dish = make_dish(self.restaurant)
        self.restaurant.delete()
        self.assertFalse(RestaurantDish.objects.filter(pk=dish.pk).exists())


class RestaurantListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('viewer', password='pw')
        self.client = Client()
        self.client.login(username='viewer', password='pw')
        self.url = reverse('content:restaurant_list')
        make_restaurant(name='Visited Place', visited=True)
        make_restaurant(name='Not Visited', visited=False)

    def test_list_shows_all(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['restaurants'].count(), 2)

    def test_filter_visited(self):
        response = self.client.get(self.url + '?visited=1')
        self.assertEqual(response.status_code, 200)
        for r in response.context['restaurants']:
            self.assertTrue(r.visited)

    def test_filter_not_visited(self):
        response = self.client.get(self.url + '?visited=0')
        self.assertEqual(response.status_code, 200)
        for r in response.context['restaurants']:
            self.assertFalse(r.visited)

    def test_context_counts(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['visited_count'], 1)
        self.assertEqual(response.context['wishlist_count'], 1)
        self.assertEqual(response.context['total_count'], 2)


class RestaurantListSearchTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('searcher', password='pw')
        self.client = Client()
        self.client.login(username='searcher', password='pw')
        self.url = reverse('content:restaurant_list')

    def test_search_by_name_prefix(self):
        make_restaurant(name='Ramen House', city='Toronto', visited=True)
        make_restaurant(name='Pizza Place', city='Vancouver', visited=False)

        response = self.client.get(self.url, {'q': 'Ram'})

        self.assertEqual(response.status_code, 200)
        names = [r.name for r in response.context['restaurants']]
        self.assertIn('Ramen House', names)
        self.assertNotIn('Pizza Place', names)

    def test_search_by_city(self):
        make_restaurant(name='Ramen House', city='Toronto')
        make_restaurant(name='Pizza Place', city='Vancouver')

        response = self.client.get(self.url, {'q': 'Vancouver'})

        names = [r.name for r in response.context['restaurants']]
        self.assertEqual(names, ['Pizza Place'])

    def test_search_composes_with_visited_filter(self):
        make_restaurant(name='Ramen House', city='Toronto', visited=True)
        make_restaurant(name='Ramen Spot', city='Toronto', visited=False)

        response = self.client.get(self.url, {'q': 'Ramen', 'visited': '1'})

        names = [r.name for r in response.context['restaurants']]
        self.assertEqual(names, ['Ramen House'])

    def test_search_with_no_matches_returns_empty(self):
        make_restaurant(name='Ramen House', city='Toronto')

        response = self.client.get(self.url, {'q': 'Nonexistent'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['restaurants']), [])

    def test_query_with_tsquery_special_characters_does_not_500(self):
        make_restaurant(name='Cheese & Crackers', city='Toronto')

        for special_query in ['chee & se', 'chee | se', 'chee:se', "chee's", '(chee)', 'chee!']:
            response = self.client.get(self.url, {'q': special_query})
            self.assertEqual(response.status_code, 200, msg=f'query={special_query!r}')

    def test_empty_query_returns_all(self):
        make_restaurant(name='Ramen House')
        make_restaurant(name='Pizza Place')

        response = self.client.get(self.url, {'q': ''})

        self.assertEqual(response.context['restaurants'].count(), 2)

    def test_query_echoed_into_context(self):
        response = self.client.get(self.url, {'q': 'Ramen'})
        self.assertEqual(response.context['query'], 'Ramen')


class RestaurantDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.restaurant = make_restaurant()
        self.url = reverse('content:restaurant_detail', kwargs={'pk': self.restaurant.pk})

    def test_detail_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.restaurant.name)

    def test_dishes_split_by_status(self):
        make_dish(self.restaurant, dish_name='Had dish', status=RestaurantDish.STATUS_HAD)
        make_dish(self.restaurant, dish_name='Wishlist dish', status=RestaurantDish.STATUS_WISHLIST)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['dishes_had']), 1)
        self.assertEqual(len(response.context['dishes_wishlist']), 1)


class RestaurantToggleVisitedTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.restaurant = make_restaurant(visited=False)
        self.url = reverse('content:restaurant_toggle_visited', kwargs={'pk': self.restaurant.pk})

    def test_toggle_to_visited(self):
        self.client.post(self.url)
        self.restaurant.refresh_from_db()
        self.assertTrue(self.restaurant.visited)

    def test_toggle_back(self):
        self.restaurant.visited = True
        self.restaurant.save()
        self.client.post(self.url)
        self.restaurant.refresh_from_db()
        self.assertFalse(self.restaurant.visited)

    def test_requires_staff(self):
        non_staff = User.objects.create_user('user', password='pw')
        c = Client()
        c.login(username='user', password='pw')
        response = c.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.restaurant.refresh_from_db()
        self.assertFalse(self.restaurant.visited)


class RestaurantDishCRUDTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.restaurant = make_restaurant()

    def test_create_had_dish(self):
        url = reverse('content:restaurant_dish_create', kwargs={'pk': self.restaurant.pk})
        self.client.post(url, {'dish_name': 'Ramen', 'status': 'had', 'source': '', 'source_detail': '', 'notes': ''})
        self.assertTrue(RestaurantDish.objects.filter(restaurant=self.restaurant, dish_name='Ramen', status='had').exists())

    def test_create_wishlist_dish_with_source(self):
        url = reverse('content:restaurant_dish_create', kwargs={'pk': self.restaurant.pk})
        self.client.post(url, {
            'dish_name': 'Tonkotsu', 'status': 'wishlist',
            'source': 'friend', 'notes': ''
        })
        dish = RestaurantDish.objects.get(restaurant=self.restaurant, dish_name='Tonkotsu')
        self.assertEqual(dish.source, 'friend')

    def test_delete_dish(self):
        dish = make_dish(self.restaurant)
        url = reverse('content:restaurant_dish_delete', kwargs={'pk': self.restaurant.pk, 'dish_pk': dish.pk})
        self.client.post(url)
        self.assertFalse(RestaurantDish.objects.filter(pk=dish.pk).exists())

    def test_update_dish(self):
        dish = make_dish(self.restaurant, dish_name='Old Name')
        url = reverse('content:restaurant_dish_update', kwargs={'pk': self.restaurant.pk, 'dish_pk': dish.pk})
        self.client.post(url, {'dish_name': 'New Name', 'status': 'wishlist', 'source': '', 'source_detail': '', 'notes': ''})
        dish.refresh_from_db()
        self.assertEqual(dish.dish_name, 'New Name')


class RestaurantDishMarkTriedTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.restaurant = make_restaurant()
        self.dish = make_dish(self.restaurant, status=RestaurantDish.STATUS_WISHLIST)

    def test_mark_tried_flips_status(self):
        url = reverse('content:restaurant_dish_mark_tried', kwargs={'pk': self.restaurant.pk, 'dish_pk': self.dish.pk})
        self.client.post(url)
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.status, RestaurantDish.STATUS_HAD)


class RestaurantCreateViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.url = reverse('content:restaurant_create')

    def test_get_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def _base_formset_data(self):
        return {
            'had-TOTAL_FORMS': '1', 'had-INITIAL_FORMS': '0', 'had-MIN_NUM_FORMS': '0', 'had-MAX_NUM_FORMS': '1000',
            'had-0-dish_name': '', 'had-0-source': '', 'had-0-source_detail': '', 'had-0-notes': '', 'had-0-DELETE': '',
            'wishlist-TOTAL_FORMS': '1', 'wishlist-INITIAL_FORMS': '0', 'wishlist-MIN_NUM_FORMS': '0', 'wishlist-MAX_NUM_FORMS': '1000',
            'wishlist-0-dish_name': '', 'wishlist-0-source': '', 'wishlist-0-source_detail': '', 'wishlist-0-notes': '', 'wishlist-0-DELETE': '',
        }

    def test_create_restaurant_basic(self):
        data = {'name': 'New Place', 'street_address': '', 'city': 'Toronto', 'province': '', 'country': 'Canada', 'postal_code': ''}
        data.update(self._base_formset_data())
        self.client.post(self.url, data)
        self.assertTrue(Restaurant.objects.filter(name='New Place').exists())

    def test_create_restaurant_with_dishes(self):
        data = {'name': 'Dish Place', 'street_address': '', 'city': '', 'province': '', 'country': '', 'postal_code': ''}
        data.update(self._base_formset_data())
        data.update({
            'had-TOTAL_FORMS': '2',
            'had-0-dish_name': 'Ramen', 'had-0-source': '', 'had-0-source_detail': '', 'had-0-notes': '', 'had-0-DELETE': '',
            'had-1-dish_name': '', 'had-1-source': '', 'had-1-source_detail': '', 'had-1-notes': '', 'had-1-DELETE': '',
            'wishlist-TOTAL_FORMS': '2',
            'wishlist-0-dish_name': 'Tonkotsu', 'wishlist-0-source': 'friend', 'wishlist-0-notes': '', 'wishlist-0-DELETE': '',
            'wishlist-1-dish_name': '', 'wishlist-1-source': '', 'wishlist-1-source_detail': '', 'wishlist-1-notes': '', 'wishlist-1-DELETE': '',
        })
        self.client.post(self.url, data)
        restaurant = Restaurant.objects.get(name='Dish Place')
        self.assertTrue(restaurant.dishes.filter(dish_name='Ramen', status='had').exists())
        self.assertTrue(restaurant.dishes.filter(dish_name='Tonkotsu', status='wishlist', source='friend').exists())


def _review_payload(restaurant_name='Test Place', dishes=None):
    if dishes is None:
        dishes = [{'name': 'Ramen', 'rating': 80}]
    return {
        'basicInfo': {
            'restaurantName': restaurant_name,
            'visitDate': '2024-06-01',
            'entryTime': '18:00',
            'partySize': '2',
        },
        'location': {},
        'rating': {'overall': 75, 'title': '', 'notes': '', 'images': []},
        'dishes': dishes,
    }


class ReviewCreateDishTrackingTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.url = reverse('content:api_review_create')

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_creates_had_dish_record(self):
        response = self._post(_review_payload())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            RestaurantDish.objects.filter(
                dish_name='Ramen',
                status=RestaurantDish.STATUS_HAD,
            ).exists()
        )

    def test_creates_had_dish_for_each_review_dish(self):
        payload = _review_payload(dishes=[
            {'name': 'Ramen', 'rating': 80},
            {'name': 'Gyoza', 'rating': 70},
        ])
        self._post(payload)
        restaurant = Restaurant.objects.get(name='Test Place')
        self.assertEqual(restaurant.dishes.filter(status=RestaurantDish.STATUS_HAD).count(), 2)

    def test_had_dish_linked_to_review(self):
        response = self._post(_review_payload())
        data = json.loads(response.content)
        dish = RestaurantDish.objects.get(dish_name='Ramen', status=RestaurantDish.STATUS_HAD)
        self.assertEqual(dish.review_id, data['review_id'])

    def test_promotes_existing_wishlist_dish(self):
        restaurant = Restaurant.objects.create(name='Test Place', visited=True)
        wishlist_dish = RestaurantDish.objects.create(
            restaurant=restaurant,
            dish_name='Ramen',
            status=RestaurantDish.STATUS_WISHLIST,
        )
        self._post(_review_payload())
        wishlist_dish.refresh_from_db()
        self.assertEqual(wishlist_dish.status, RestaurantDish.STATUS_HAD)
        self.assertIsNotNone(wishlist_dish.review_id)
        # No duplicate created
        self.assertEqual(RestaurantDish.objects.filter(dish_name='Ramen').count(), 1)


class RestaurantPopUpModelTest(TestCase):
    def test_is_pop_up_defaults_false(self):
        r = make_restaurant()
        self.assertFalse(r.is_pop_up)
        self.assertEqual(r.website, '')

    def test_pop_up_skips_geocoding(self):
        r = Restaurant.objects.create(
            name='Mystery Pop-Up',
            is_pop_up=True,
            website='https://example.com',
            street_address='123 Nowhere St',
            city='Toronto',
        )
        self.assertIsNone(r.latitude)
        self.assertIsNone(r.longitude)


class RestaurantFormPopUpTest(TestCase):
    def _data(self, **overrides):
        data = {
            'name': 'Pop-Up Place', 'street_address': '', 'city': '', 'province': '',
            'country': '', 'postal_code': '', 'google_place_id': '', 'is_pop_up': False, 'website': '',
        }
        data.update(overrides)
        return data

    def test_valid_without_website_when_not_pop_up(self):
        form = RestaurantForm(data=self._data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_when_pop_up_without_website(self):
        form = RestaurantForm(data=self._data(is_pop_up=True))
        self.assertFalse(form.is_valid())
        self.assertIn('website', form.errors)

    def test_valid_when_pop_up_with_website(self):
        form = RestaurantForm(data=self._data(is_pop_up=True, website='https://example.com'))
        self.assertTrue(form.is_valid(), form.errors)


class RestaurantCreateViewPopUpTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.url = reverse('content:restaurant_create')

    def _base_formset_data(self):
        return {
            'had-TOTAL_FORMS': '1', 'had-INITIAL_FORMS': '0', 'had-MIN_NUM_FORMS': '0', 'had-MAX_NUM_FORMS': '1000',
            'had-0-dish_name': '', 'had-0-source': '', 'had-0-source_detail': '', 'had-0-notes': '', 'had-0-DELETE': '',
            'wishlist-TOTAL_FORMS': '1', 'wishlist-INITIAL_FORMS': '0', 'wishlist-MIN_NUM_FORMS': '0', 'wishlist-MAX_NUM_FORMS': '1000',
            'wishlist-0-dish_name': '', 'wishlist-0-source': '', 'wishlist-0-source_detail': '', 'wishlist-0-notes': '', 'wishlist-0-DELETE': '',
        }

    def test_create_pop_up_with_website(self):
        data = {
            'name': 'Taco Truck', 'street_address': '', 'city': '', 'province': '', 'country': '', 'postal_code': '',
            'is_pop_up': 'on', 'website': 'https://tacotruck.example.com',
        }
        data.update(self._base_formset_data())
        self.client.post(self.url, data)
        restaurant = Restaurant.objects.get(name='Taco Truck')
        self.assertTrue(restaurant.is_pop_up)
        self.assertEqual(restaurant.website, 'https://tacotruck.example.com')

    def test_create_pop_up_without_website_fails_validation(self):
        data = {
            'name': 'No Website Truck', 'street_address': '', 'city': '', 'province': '', 'country': '', 'postal_code': '',
            'is_pop_up': 'on', 'website': '',
        }
        data.update(self._base_formset_data())
        self.client.post(self.url, data)
        self.assertFalse(Restaurant.objects.filter(name='No Website Truck').exists())


class RestaurantUpdateViewPopUpTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.restaurant = make_restaurant(name='Soon Pop-Up', street_address='', city='', country='')
        self.url = reverse('content:restaurant_edit', kwargs={'pk': self.restaurant.pk})

    def test_update_to_pop_up_with_website(self):
        self.client.post(self.url, {
            'name': 'Soon Pop-Up', 'street_address': '', 'city': '', 'province': '', 'country': '', 'postal_code': '',
            'is_pop_up': 'on', 'website': 'https://example.com',
        })
        self.restaurant.refresh_from_db()
        self.assertTrue(self.restaurant.is_pop_up)
        self.assertEqual(self.restaurant.website, 'https://example.com')

    def test_update_to_pop_up_without_website_is_rejected(self):
        self.client.post(self.url, {
            'name': 'Soon Pop-Up', 'street_address': '', 'city': '', 'province': '', 'country': '', 'postal_code': '',
            'is_pop_up': 'on', 'website': '',
        })
        self.restaurant.refresh_from_db()
        self.assertFalse(self.restaurant.is_pop_up)
        self.assertEqual(self.restaurant.website, '')
