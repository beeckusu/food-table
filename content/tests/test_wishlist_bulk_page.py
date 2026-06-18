from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class WishlistBulkPageViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.url = reverse('content:wishlist_bulk_add')

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_forbidden(self):
        User.objects.create_user('user', password='pw')
        self.client.login(username='user', password='pw')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_staff_get_renders(self):
        self.client.login(username='staff', password='pw')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wishlist/bulk_add.html')

    def test_context_has_maps_key(self):
        self.client.login(username='staff', password='pw')
        response = self.client.get(self.url)
        self.assertIn('google_maps_api_key', response.context)
