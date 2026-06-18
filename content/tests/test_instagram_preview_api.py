import json
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
import requests


class InstagramPreviewApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.url = reverse('content:api_instagram_preview')
        self.ig_url = 'https://www.instagram.com/reel/ABC123/'

    def test_requires_login(self):
        client = Client()
        response = client.get(self.url, {'url': self.ig_url})
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_forbidden(self):
        User.objects.create_user('user', password='pw')
        client = Client()
        client.login(username='user', password='pw')
        response = client.get(self.url, {'url': self.ig_url})
        self.assertEqual(response.status_code, 403)

    def test_rejects_non_instagram_url(self):
        response = self.client.get(self.url, {'url': 'https://evil.example.com/'})
        self.assertEqual(response.status_code, 400)

    @patch('content.views.instagram_preview_api.requests.get')
    def test_success_extracts_description(self, mock_get):
        mock_get.return_value = Mock(text=(
            '<html><head>'
            '<meta property="og:description" content="123 likes - Best ramen &amp; noodles in town">'
            '</head></html>'
        ))

        response = self.client.get(self.url, {'url': self.ig_url})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['description'], '123 likes - Best ramen & noodles in town')

    @patch('content.views.instagram_preview_api.requests.get')
    def test_missing_meta_tag_reports_failure(self, mock_get):
        mock_get.return_value = Mock(text='<html><head></head></html>')

        response = self.client.get(self.url, {'url': self.ig_url})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    @patch('content.views.instagram_preview_api.requests.get')
    def test_network_error_reports_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException('boom')

        response = self.client.get(self.url, {'url': self.ig_url})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
