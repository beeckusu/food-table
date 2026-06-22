import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from content.models import Restaurant, RestaurantDish


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

    def test_new_restaurant_with_note_appends_link_and_note(self):
        ig_url = 'https://www.instagram.com/p/abc123/'
        response = self.post({
            'url': ig_url,
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': 'Ramen', 'note': 'Get the spicy one'}],
        })
        self.assertEqual(response.status_code, 200)
        dish = RestaurantDish.objects.get(dish_name='Ramen')
        self.assertEqual(dish.source_detail, ig_url)
        self.assertEqual(dish.notes, ig_url + '\nGet the spicy one')

    def test_dish_without_note_only_stores_link(self):
        ig_url = 'https://www.instagram.com/p/abc123/'
        response = self.post({
            'url': ig_url,
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': 'Ramen', 'note': ''}],
        })
        self.assertEqual(response.status_code, 200)
        dish = RestaurantDish.objects.get(dish_name='Ramen')
        self.assertEqual(dish.notes, ig_url)

    def test_dish_without_link_only_stores_note(self):
        response = self.post({
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': 'Ramen', 'note': 'Get the spicy one'}],
        })
        self.assertEqual(response.status_code, 200)
        dish = RestaurantDish.objects.get(dish_name='Ramen')
        self.assertEqual(dish.source_detail, '')
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
        self.assertEqual(dish.notes, ig_url + '\nGet the spicy one')

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
        self.assertEqual(ramen.notes, ig_url + '\nGet the spicy one')
        self.assertEqual(gyoza.notes, ig_url)

    def test_dish_with_blank_name_is_skipped(self):
        response = self.post({
            'restaurant_name': 'Noodle House',
            'dishes': [{'name': '  ', 'note': 'orphan note'}],
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RestaurantDish.objects.exists())
