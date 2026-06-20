from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from content.models import Restaurant


class GlobalSearchRestaurantTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('searcher', password='pw')
        self.client = Client()
        self.client.login(username='searcher', password='pw')
        self.url = reverse('content:global_search')

    def test_restaurant_appears_in_unfiltered_results(self):
        Restaurant.objects.create(name='Ramen House', city='Toronto')

        response = self.client.get(self.url, {'q': 'Ramen'})

        names = [r.name for r in response.context['results'] if r.content_type == 'restaurant']
        self.assertIn('Ramen House', names)

    def test_restaurant_count_in_context(self):
        Restaurant.objects.create(name='Ramen House', city='Toronto')

        response = self.client.get(self.url, {'q': 'Ramen'})

        self.assertEqual(response.context['restaurant_count'], 1)

    def test_type_filter_restaurant_excludes_other_types(self):
        Restaurant.objects.create(name='Ramen House', city='Toronto')

        response = self.client.get(self.url, {'q': 'Ramen', 'type': 'restaurant'})

        for result in response.context['results']:
            self.assertEqual(result.content_type, 'restaurant')

    def test_type_filter_encyclopedia_excludes_restaurant(self):
        Restaurant.objects.create(name='Ramen House', city='Toronto')

        response = self.client.get(self.url, {'q': 'Ramen', 'type': 'encyclopedia'})

        names = [r.name for r in response.context['results'] if r.content_type == 'restaurant']
        self.assertEqual(names, [])
