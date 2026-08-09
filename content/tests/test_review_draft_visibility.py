from datetime import date, time

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from content.models import Restaurant, Review


class ReviewDraftVisibilityTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.regular = User.objects.create_user('regular', password='pw')
        self.restaurant = Restaurant.objects.create(name='Noodle House', visited=True)

        self.final_review = Review.objects.create(
            restaurant=self.restaurant,
            visit_date=date(2025, 1, 15),
            entry_time=time(18, 30),
            party_size=2,
            rating=80,
            created_by=self.staff,
        )
        self.draft_review = Review.objects.create(
            restaurant=self.restaurant,
            visit_date=date(2025, 2, 1),
            entry_time=time(19, 0),
            party_size=2,
            rating=70,
            created_by=self.staff,
            is_draft=True,
        )

    def test_list_excludes_drafts_for_non_staff(self):
        client = Client()
        client.login(username='regular', password='pw')
        response = client.get(reverse('content:review_list'))

        reviews = list(response.context['reviews'])
        self.assertIn(self.final_review, reviews)
        self.assertNotIn(self.draft_review, reviews)

    def test_list_includes_drafts_for_staff(self):
        client = Client()
        client.login(username='staff', password='pw')
        response = client.get(reverse('content:review_list'))

        reviews = list(response.context['reviews'])
        self.assertIn(self.final_review, reviews)
        self.assertIn(self.draft_review, reviews)

    def test_total_reviews_count_excludes_drafts_for_non_staff(self):
        client = Client()
        client.login(username='regular', password='pw')
        response = client.get(reverse('content:review_list'))
        self.assertEqual(response.context['total_reviews'], 1)

    def test_total_reviews_count_includes_drafts_for_staff(self):
        client = Client()
        client.login(username='staff', password='pw')
        response = client.get(reverse('content:review_list'))
        self.assertEqual(response.context['total_reviews'], 2)

    def test_detail_404s_for_non_staff_on_draft(self):
        client = Client()
        client.login(username='regular', password='pw')
        response = client.get(reverse('content:review_detail', kwargs={'pk': self.draft_review.pk}))
        self.assertEqual(response.status_code, 404)

    def test_detail_visible_to_staff_on_draft(self):
        client = Client()
        client.login(username='staff', password='pw')
        response = client.get(reverse('content:review_detail', kwargs={'pk': self.draft_review.pk}))
        self.assertEqual(response.status_code, 200)

    def test_related_reviews_excludes_drafts_for_non_staff(self):
        client = Client()
        client.login(username='regular', password='pw')
        response = client.get(reverse('content:review_detail', kwargs={'pk': self.final_review.pk}))
        self.assertEqual(response.status_code, 200)
        related = list(response.context['related_reviews'])
        self.assertNotIn(self.draft_review, related)
