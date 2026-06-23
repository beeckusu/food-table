from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from content.models import Encyclopedia, Recipe, Restaurant, Review


class GlobalSearchHtmlStrippingTest(TestCase):
    """FT-177: Quill-authored HTML in description/notes fields must not leak as visible tags."""

    def setUp(self):
        self.user = User.objects.create_user('searcher', password='pw')
        self.client = Client()
        self.client.login(username='searcher', password='pw')
        self.url = reverse('content:global_search')

    def test_encyclopedia_description_html_is_stripped(self):
        Encyclopedia.objects.create(
            name='Biang Biang Noodles',
            slug='biang-biang-noodles',
            description='<p>Biang biang noodles are <strong>hand-pulled</strong> Chinese noodles.</p>',
        )

        response = self.client.get(self.url, {'q': 'Biang'})

        self.assertNotContains(response, '&lt;p&gt;')
        self.assertContains(response, 'hand-pulled')

    def test_recipe_description_html_is_stripped(self):
        Recipe.objects.create(
            name='Pad Thai',
            slug='pad-thai',
            description='<p>A <em>classic</em> Thai noodle dish.</p>',
        )

        response = self.client.get(self.url, {'q': 'Pad Thai'})

        self.assertNotContains(response, '&lt;p&gt;')
        self.assertContains(response, 'classic')

    def test_review_notes_html_is_stripped(self):
        restaurant = Restaurant.objects.create(name='Ramen House', city='Toronto')
        Review.objects.create(
            restaurant=restaurant,
            visit_date='2026-01-01',
            entry_time='18:00',
            party_size=2,
            rating=80,
            notes='<p>The <strong>broth</strong> was excellent.</p>',
        )

        response = self.client.get(self.url, {'q': 'Ramen'})

        self.assertNotContains(response, '&lt;p&gt;')
        self.assertContains(response, 'broth')


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
