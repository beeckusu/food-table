import json

from django.test import TestCase, Client
from django.urls import reverse

from content.models import Encyclopedia


def make_entry(**kwargs):
    defaults = {'name': 'Test Entry', 'description': 'A test description', 'is_placeholder': False}
    defaults.update(kwargs)
    return Encyclopedia.objects.create(**defaults)


class EncyclopediaSearchApiViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('content:api_encyclopedia_search')

    def test_empty_query_returns_empty_results(self):
        response = self.client.get(self.url, {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['results'], [])

    def test_multi_word_query_does_not_500(self):
        make_entry(name='Al Pastor', description='A Mexican dish', slug='al-pastor')

        response = self.client.get(self.url, {'q': 'Al Pas'})

        self.assertEqual(response.status_code, 200)
        names = [r['name'] for r in json.loads(response.content)['results']]
        self.assertIn('Al Pastor', names)

    def test_query_with_tsquery_special_characters_does_not_500(self):
        make_entry(name='Cheese', description='Dairy product', slug='cheese')

        for special_query in ['chee & se', 'chee | se', 'chee:se', "chee's", '(chee)', 'chee!']:
            response = self.client.get(self.url, {'q': special_query})
            self.assertEqual(response.status_code, 200, msg=f'query={special_query!r}')

    def test_single_word_prefix_match_still_works(self):
        make_entry(name='Cheese', description='Dairy product', slug='cheese')

        response = self.client.get(self.url, {'q': 'chee'})

        self.assertEqual(response.status_code, 200)
        names = [r['name'] for r in json.loads(response.content)['results']]
        self.assertIn('Cheese', names)

    def test_query_that_sanitizes_to_nothing_returns_empty_results(self):
        response = self.client.get(self.url, {'q': '!!!'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['results'], [])

    def test_ilike_fallback_when_no_fulltext_match(self):
        make_entry(name='Pho', description='Vietnamese noodle soup', slug='pho')

        response = self.client.get(self.url, {'q': 'noodle'})

        self.assertEqual(response.status_code, 200)
        names = [r['name'] for r in json.loads(response.content)['results']]
        self.assertIn('Pho', names)
