from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from content.models import Restaurant


class RestaurantSearchApiViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.url = reverse('content:api_restaurant_search')

    def test_query_matches_by_name(self):
        Restaurant.objects.create(name='Noodle House', city='Toronto', country='Canada')
        response = self.client.get(self.url, {'q': 'noodle'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)

    def test_short_query_returns_empty(self):
        response = self.client.get(self.url, {'q': 'n'})
        self.assertEqual(response.json()['results'], [])

    def test_place_id_matches_restaurant(self):
        restaurant = Restaurant.objects.create(
            name='Noodle House', city='Toronto', country='Canada', google_place_id='abc123',
        )
        response = self.client.get(self.url, {'place_id': 'abc123'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], restaurant.pk)

    def test_place_id_with_no_match_returns_empty(self):
        response = self.client.get(self.url, {'place_id': 'nonexistent'})
        self.assertEqual(response.json()['results'], [])

    def test_place_id_takes_precedence_over_query(self):
        restaurant = Restaurant.objects.create(
            name='Noodle House', city='Toronto', country='Canada', google_place_id='abc123',
        )
        Restaurant.objects.create(name='Other Place', city='Toronto', country='Canada')
        response = self.client.get(self.url, {'place_id': 'abc123', 'q': 'other'})
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], restaurant.pk)
