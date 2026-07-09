from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse


class NavbarDishesTabTest(TestCase):
    def test_dishes_link_present_for_logged_in_user(self):
        User.objects.create_user('user', password='pw')
        client = Client()
        client.login(username='user', password='pw')
        response = client.get(reverse('content:review_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('content:review_dish_list'))
