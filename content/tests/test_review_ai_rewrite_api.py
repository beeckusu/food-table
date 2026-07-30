import json
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from content.services.ai_service import AIServiceError


class ReviewAIRewriteApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.non_staff = User.objects.create_user('regular', password='pw', is_staff=False)
        self.client = Client()
        self.url = reverse('content:api_review_ai_rewrite')

    def post(self, body):
        return self.client.post(self.url, data=json.dumps(body), content_type='application/json')

    def test_requires_login(self):
        response = self.post({'text': 'Some review text.'})
        self.assertNotEqual(response.status_code, 200)

    def test_requires_staff(self):
        self.client.login(username='regular', password='pw')
        response = self.post({'text': 'Some review text.'})
        self.assertNotEqual(response.status_code, 200)

    def test_empty_text_rejected(self):
        self.client.login(username='staff', password='pw')
        response = self.post({'text': '   '})
        self.assertEqual(response.status_code, 400)

    def test_text_too_long_rejected(self):
        self.client.login(username='staff', password='pw')
        response = self.post({'text': 'x' * 5001})
        self.assertEqual(response.status_code, 400)

    @patch('content.views.review_ai_rewrite_api.generate_text')
    def test_ai_service_error_returns_503(self, mock_generate_text):
        mock_generate_text.side_effect = AIServiceError('boom')
        self.client.login(username='staff', password='pw')
        response = self.post({'text': 'Some review text.'})
        self.assertEqual(response.status_code, 503)

    @patch('content.views.review_ai_rewrite_api.generate_text')
    def test_happy_path_returns_rewritten_text(self, mock_generate_text):
        mock_generate_text.return_value = 'Rewritten review text.'
        self.client.login(username='staff', password='pw')
        response = self.post({'text': 'Some review text.'})
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data['rewritten'], 'Rewritten review text.')
        mock_generate_text.assert_called_once()
