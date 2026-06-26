import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from content.models import Restaurant, RestaurantDish, RestaurantDishReference


class WishlistBulkCreateApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.url = reverse('content:api_wishlist_bulk_create')
        self.client.login(username='staff', password='pw')

    def post(self, body):
        return self.client.post(self.url, data=json.dumps(body), content_type='application/json')

    def test_requires_login(self):
        client = Client()
        response = client.post(self.url, data=json.dumps({}), content_type='application/json')
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_forbidden(self):
        User.objects.create_user('user', password='pw')
        client = Client()
        client.login(username='user', password='pw')
        response = client.post(self.url, data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_new_restaurant_with_note_stores_link_as_reference_and_note(self):
        ig_url = 'https://www.instagram.com/p/abc123/'
        response = self.post({
            'url': ig_url,
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': 'Ramen', 'note': 'Get the spicy one'}],
        })
        self.assertEqual(response.status_code, 200)
        dish = RestaurantDish.objects.get(dish_name='Ramen')
        ref = dish.references.first()
        self.assertEqual(ref.source, 'Instagram')
        self.assertEqual(ref.source_detail, ig_url)
        self.assertEqual(dish.notes, 'Get the spicy one')

    def test_dish_without_note_stores_link_as_reference(self):
        ig_url = 'https://www.instagram.com/p/abc123/'
        response = self.post({
            'url': ig_url,
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': 'Ramen', 'note': ''}],
        })
        self.assertEqual(response.status_code, 200)
        dish = RestaurantDish.objects.get(dish_name='Ramen')
        self.assertEqual(dish.references.first().source_detail, ig_url)
        self.assertEqual(dish.notes, '')

    def test_dish_without_link_stores_note_only(self):
        response = self.post({
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': 'Ramen', 'note': 'Get the spicy one'}],
        })
        self.assertEqual(response.status_code, 200)
        dish = RestaurantDish.objects.get(dish_name='Ramen')
        self.assertFalse(dish.references.exists())
        self.assertEqual(dish.notes, 'Get the spicy one')

    def test_existing_restaurant_path_persists_notes(self):
        restaurant = Restaurant.objects.create(name='Noodle House', city='Toronto', country='Canada')
        ig_url = 'https://www.instagram.com/p/abc123/'
        response = self.post({
            'url': ig_url,
            'restaurant_id': restaurant.pk,
            'dishes': [{'name': 'Ramen', 'note': 'Get the spicy one'}],
        })
        self.assertEqual(response.status_code, 200)
        dish = RestaurantDish.objects.get(dish_name='Ramen', restaurant=restaurant)
        self.assertEqual(dish.notes, 'Get the spicy one')
        self.assertEqual(dish.references.first().source_detail, ig_url)

    def test_multiple_dishes_with_mixed_notes(self):
        ig_url = 'https://www.instagram.com/p/abc123/'
        response = self.post({
            'url': ig_url,
            'restaurant_name': 'Noodle House',
            'dishes': [
                {'name': 'Ramen', 'note': 'Get the spicy one'},
                {'name': 'Gyoza', 'note': ''},
            ],
        })
        self.assertEqual(response.status_code, 200)
        ramen = RestaurantDish.objects.get(dish_name='Ramen')
        gyoza = RestaurantDish.objects.get(dish_name='Gyoza')
        self.assertEqual(ramen.notes, 'Get the spicy one')
        self.assertEqual(ramen.references.first().source_detail, ig_url)
        self.assertEqual(gyoza.notes, '')
        self.assertEqual(gyoza.references.first().source_detail, ig_url)

    def test_dish_with_blank_name_is_skipped(self):
        response = self.post({
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': '  ', 'note': 'orphan note'}],
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RestaurantDish.objects.exists())

    def test_duplicate_dish_consolidates_reference(self):
        restaurant = Restaurant.objects.create(name='Noodle House', city='Toronto', country='Canada')
        dish = RestaurantDish.objects.create(
            restaurant=restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_WISHLIST,
        )
        RestaurantDishReference.objects.create(dish=dish, source='Instagram', source_detail='https://www.instagram.com/p/old/')
        ig_url = 'https://www.instagram.com/p/new/'
        self.post({'url': ig_url, 'restaurant_id': restaurant.pk, 'dishes': [{'name': 'Ramen', 'note': ''}]})
        self.assertEqual(RestaurantDish.objects.filter(restaurant=restaurant, dish_name='Ramen').count(), 1)
        self.assertEqual(dish.references.count(), 2)

    def test_duplicate_dish_does_not_add_same_reference_twice(self):
        restaurant = Restaurant.objects.create(name='Noodle House', city='Toronto', country='Canada')
        ig_url = 'https://www.instagram.com/p/abc123/'
        dish = RestaurantDish.objects.create(
            restaurant=restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_WISHLIST,
        )
        RestaurantDishReference.objects.create(dish=dish, source='Instagram', source_detail=ig_url)
        self.post({'url': ig_url, 'restaurant_id': restaurant.pk, 'dishes': [{'name': 'Ramen', 'note': ''}]})
        self.assertEqual(dish.references.count(), 1)

    def test_duplicate_dish_appends_new_note(self):
        restaurant = Restaurant.objects.create(name='Noodle House', city='Toronto', country='Canada')
        dish = RestaurantDish.objects.create(
            restaurant=restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_WISHLIST,
            notes='original note',
        )
        self.post({'restaurant_id': restaurant.pk, 'dishes': [{'name': 'Ramen', 'note': 'new note'}]})
        dish.refresh_from_db()
        self.assertIn('original note', dish.notes)
        self.assertIn('new note', dish.notes)

    def test_duplicate_match_is_case_insensitive(self):
        restaurant = Restaurant.objects.create(name='Noodle House', city='Toronto', country='Canada')
        RestaurantDish.objects.create(
            restaurant=restaurant, dish_name='ramen', status=RestaurantDish.STATUS_WISHLIST,
        )
        self.post({'restaurant_id': restaurant.pk, 'dishes': [{'name': 'Ramen', 'note': ''}]})
        self.assertEqual(RestaurantDish.objects.filter(restaurant=restaurant).count(), 1)
