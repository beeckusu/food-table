import json
from datetime import date, time

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from content.models import Restaurant, Review, ReviewDish, RestaurantDish, Image

# 1x1 transparent PNG
TINY_PNG_DATA_URL = (
    'data:image/png;base64,'
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
)


class ReviewEditDataApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.restaurant = Restaurant.objects.create(name='Noodle House', visited=True)
        self.review = Review.objects.create(
            restaurant=self.restaurant,
            visit_date=date(2025, 1, 15),
            entry_time=time(18, 30),
            party_size=2,
            rating=80,
            title='Great meal',
            notes='Loved it',
            created_by=self.staff,
        )
        self.dish = ReviewDish.objects.create(review=self.review, dish_name='Ramen', dish_rating=90)
        self.client = Client()
        self.url = reverse('content:api_review_edit_data', kwargs={'pk': self.review.pk})

    def test_requires_login(self):
        client = Client()
        response = client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_forbidden(self):
        User.objects.create_user('user', password='pw')
        client = Client()
        client.login(username='user', password='pw')
        response = client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_returns_review_shaped_data(self):
        self.client.login(username='staff', password='pw')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()['review']

        self.assertEqual(data['basicInfo']['visitDate'], '2025-01-15')
        self.assertEqual(data['basicInfo']['partySize'], 2)
        self.assertEqual(data['restaurant']['mode'], 'search')
        self.assertEqual(data['restaurant']['id'], self.restaurant.pk)
        self.assertEqual(data['rating']['overall'], 80)
        self.assertEqual(len(data['dishes']), 1)
        self.assertEqual(data['dishes'][0]['name'], 'Ramen')
        self.assertEqual(data['dishes'][0]['id'], self.dish.pk)
        self.assertFalse(data['is_draft'])

    def test_returns_is_draft_true_for_draft_review(self):
        self.review.is_draft = True
        self.review.save()

        self.client.login(username='staff', password='pw')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['review']['is_draft'])


class ReviewUpdateApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.restaurant = Restaurant.objects.create(name='Noodle House', visited=True)
        self.review = Review.objects.create(
            restaurant=self.restaurant,
            visit_date=date(2025, 1, 15),
            entry_time=time(18, 30),
            party_size=2,
            rating=80,
            title='Great meal',
            notes='Loved it',
            created_by=self.staff,
        )
        self.dish = ReviewDish.objects.create(review=self.review, dish_name='Ramen', dish_rating=90)
        self.client = Client()
        self.url = reverse('content:api_review_update', kwargs={'pk': self.review.pk})
        self.client.login(username='staff', password='pw')

    def patch(self, body):
        return self.client.patch(self.url, data=json.dumps(body), content_type='application/json')

    def base_payload(self, **overrides):
        payload = {
            'basicInfo': {'visitDate': '2025-01-16', 'partySize': '3', 'entryTime': '19:00'},
            'restaurant': {'mode': 'search', 'id': self.restaurant.pk, 'name': self.restaurant.name},
            'rating': {'overall': 85, 'title': 'Updated title', 'notes': 'Updated notes', 'ambiance': 70, 'service': 60, 'images': []},
            'dishes': [{'id': self.dish.pk, 'name': 'Ramen Deluxe', 'rating': 95, 'notes': '', 'cost': None, 'encyclopedia_ids': []}],
        }
        payload.update(overrides)
        return payload

    def test_requires_login(self):
        client = Client()
        response = client.patch(self.url, data=json.dumps({}), content_type='application/json')
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_forbidden(self):
        User.objects.create_user('user', password='pw')
        client = Client()
        client.login(username='user', password='pw')
        response = client.patch(self.url, data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_updates_basic_fields(self):
        response = self.patch(self.base_payload())
        self.assertEqual(response.status_code, 200, response.content)

        self.review.refresh_from_db()
        self.assertEqual(self.review.visit_date, date(2025, 1, 16))
        self.assertEqual(self.review.party_size, 3)
        self.assertEqual(self.review.rating, 85)
        self.assertEqual(self.review.title, 'Updated title')

    def test_can_mark_final_review_as_draft(self):
        response = self.patch(self.base_payload(is_draft=True))
        self.assertEqual(response.status_code, 200, response.content)

        self.review.refresh_from_db()
        self.assertTrue(self.review.is_draft)

    def test_can_finalize_draft_review(self):
        self.review.is_draft = True
        self.review.save()

        response = self.patch(self.base_payload(is_draft=False))
        self.assertEqual(response.status_code, 200, response.content)

        self.review.refresh_from_db()
        self.assertFalse(self.review.is_draft)

    def test_omitting_is_draft_preserves_current_state(self):
        self.review.is_draft = True
        self.review.save()

        payload = self.base_payload()
        response = self.patch(payload)
        self.assertEqual(response.status_code, 200, response.content)

        self.review.refresh_from_db()
        self.assertTrue(self.review.is_draft)

    def test_updates_existing_dish_in_place_without_duplicating(self):
        response = self.patch(self.base_payload())
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(ReviewDish.objects.filter(review=self.review).count(), 1)
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.dish_name, 'Ramen Deluxe')
        self.assertEqual(self.dish.dish_rating, 95)

    def test_updating_existing_dish_does_not_recreate_wishlist_reference(self):
        # Existing dish already promoted from a wishlist entry previously
        RestaurantDish.objects.create(
            restaurant=self.restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_HAD, review=self.review
        )
        initial_count = RestaurantDish.objects.filter(restaurant=self.restaurant).count()

        response = self.patch(self.base_payload())
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(RestaurantDish.objects.filter(restaurant=self.restaurant).count(), initial_count)

    def test_adding_new_dish_creates_restaurant_dish(self):
        payload = self.base_payload()
        payload['dishes'].append({'name': 'Gyoza', 'rating': 70, 'notes': '', 'cost': None, 'encyclopedia_ids': []})
        response = self.patch(payload)
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(ReviewDish.objects.filter(review=self.review).count(), 2)
        self.assertTrue(RestaurantDish.objects.filter(restaurant=self.restaurant, dish_name='Gyoza').exists())

    def test_removing_dish_from_payload_deletes_it(self):
        response = self.patch(self.base_payload(dishes=[]))
        self.assertEqual(response.status_code, 400)  # dishes_required=True

    def test_replacing_dish_list_deletes_removed_dish(self):
        second_dish = ReviewDish.objects.create(review=self.review, dish_name='Gyoza', dish_rating=60)
        payload = self.base_payload()  # only references self.dish, not second_dish
        response = self.patch(payload)
        self.assertEqual(response.status_code, 200, response.content)

        self.assertFalse(ReviewDish.objects.filter(pk=second_dish.pk).exists())
        self.assertTrue(ReviewDish.objects.filter(pk=self.dish.pk).exists())

    def test_changing_restaurant_updates_review(self):
        new_restaurant = Restaurant.objects.create(name='Other Place', visited=False)
        response = self.patch(self.base_payload(restaurant={'mode': 'search', 'id': new_restaurant.pk, 'name': new_restaurant.name}))
        self.assertEqual(response.status_code, 200, response.content)

        self.review.refresh_from_db()
        self.assertEqual(self.review.restaurant_id, new_restaurant.pk)
        new_restaurant.refresh_from_db()
        self.assertTrue(new_restaurant.visited)

    def test_review_not_found_returns_404(self):
        url = reverse('content:api_review_update', kwargs={'pk': 999999})
        response = self.client.patch(url, data=json.dumps(self.base_payload()), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_new_dish_image_preserves_original_filename(self):
        payload = self.base_payload(dishes=[{
            'id': self.dish.pk, 'name': 'Ramen Deluxe', 'rating': 95, 'notes': '', 'cost': None,
            'encyclopedia_ids': [], 'image': TINY_PNG_DATA_URL, 'image_filename': 'new-bowl.png',
        }])
        response = self.patch(payload)
        self.assertEqual(response.status_code, 200, response.content)

        image = Image.objects.get(object_id=self.dish.id, content_type__model='reviewdish')
        self.assertEqual(image.image.name.rsplit('/', 1)[-1], 'new-bowl.png')

    def test_new_review_image_preserves_original_filename(self):
        payload = self.base_payload(rating={
            'overall': 85, 'title': 'Updated title', 'notes': 'Updated notes', 'ambiance': 70, 'service': 60,
            'images': [{'id': None, 'src': TINY_PNG_DATA_URL, 'filename': 'new-review-photo.png'}],
        })
        response = self.patch(payload)
        self.assertEqual(response.status_code, 200, response.content)

        image = Image.objects.get(object_id=self.review.id, content_type__model='review')
        self.assertEqual(image.image.name.rsplit('/', 1)[-1], 'new-review-photo.png')
