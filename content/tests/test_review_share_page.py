from datetime import date, time

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from content.models import MenuItem, Restaurant, Review, ReviewDish


class ReviewSharePageViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.restaurant = Restaurant.objects.create(name='Pizza Cafe')
        self.review = Review.objects.create(
            restaurant=self.restaurant,
            visit_date=date(2026, 1, 1),
            entry_time=time(19, 0),
            party_size=2,
            rating=80,
            notes='Great <strong>pizza</strong> tonight.',
        )
        menu_item = MenuItem.objects.create(restaurant=self.restaurant, name='Margherita')
        ReviewDish.objects.create(review=self.review, menu_item=menu_item, notes='Crispy crust.')
        self.client = Client()
        self.url = reverse('content:review_share', kwargs={'pk': self.review.pk})

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_forbidden(self):
        User.objects.create_user('user', password='pw')
        self.client.login(username='user', password='pw')
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_staff_get_renders(self):
        self.client.login(username='staff', password='pw')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'review/share.html')

    def test_context_contains_review_and_dishes(self):
        self.client.login(username='staff', password='pw')
        response = self.client.get(self.url)
        self.assertEqual(response.context['review'], self.review)
        self.assertEqual(len(response.context['dishes']), 1)

    def test_page_data_seeds_from_stripped_notes(self):
        self.client.login(username='staff', password='pw')
        response = self.client.get(self.url)
        page_data = response.context['page_data']
        self.assertEqual(page_data['seed_text'], 'Great pizza tonight.')
        self.assertIsNone(page_data['share_draft'])

    def test_404_for_missing_review(self):
        self.client.login(username='staff', password='pw')
        response = self.client.get(reverse('content:review_share', kwargs={'pk': 999999}))
        self.assertEqual(response.status_code, 404)
