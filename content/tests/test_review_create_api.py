import json
from datetime import date

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from content.models import Restaurant, Review, ReviewDish, RestaurantDish, Image

# 1x1 transparent PNG
TINY_PNG_DATA_URL = (
    'data:image/png;base64,'
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
)


class ReviewCreateApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.url = reverse('content:api_review_create')
        self.client.login(username='staff', password='pw')

    def post(self, body):
        return self.client.post(self.url, data=json.dumps(body), content_type='application/json')

    def base_payload(self, **overrides):
        payload = {
            'basicInfo': {'visitDate': '2025-01-15', 'partySize': '2', 'entryTime': '18:30'},
            'restaurant': {'mode': 'search', 'name': 'Noodle House'},
            'rating': {'overall': 80, 'title': 'Great meal', 'notes': 'Loved it', 'ambiance': 70, 'service': 60, 'images': []},
            'dishes': [{'name': 'Ramen', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': []}],
        }
        payload.update(overrides)
        return payload

    def test_requires_login(self):
        client = Client()
        response = client.post(self.url, data=json.dumps({}), content_type='application/json')
        self.assertNotEqual(response.status_code, 200)

    def test_create_review_with_new_restaurant_by_name(self):
        response = self.post(self.base_payload())
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertTrue(data['success'])

        review = Review.objects.get(pk=data['review_id'])
        self.assertEqual(review.restaurant.name, 'Noodle House')
        self.assertEqual(review.visit_date, date(2025, 1, 15))
        self.assertEqual(review.party_size, 2)
        self.assertEqual(review.rating, 80)
        self.assertTrue(review.restaurant.visited)

    def test_create_review_with_existing_restaurant_by_id(self):
        restaurant = Restaurant.objects.create(name='Existing Spot', visited=False)
        response = self.post(self.base_payload(restaurant={'mode': 'search', 'id': restaurant.pk, 'name': restaurant.name}))
        self.assertEqual(response.status_code, 200, response.content)

        restaurant.refresh_from_db()
        review = Review.objects.get(restaurant=restaurant)
        self.assertEqual(review.restaurant_id, restaurant.pk)
        self.assertTrue(restaurant.visited)

    def test_create_review_with_brand_new_restaurant_mode(self):
        response = self.post(self.base_payload(restaurant={
            'mode': 'new',
            'name': 'Brand New Place',
            'isPopUp': False,
            'address': '123 Main St',
            'city': 'Toronto',
            'province': 'ON',
            'country': 'Canada',
            'postalCode': 'M1M1M1',
        }))
        self.assertEqual(response.status_code, 200, response.content)

        restaurant = Restaurant.objects.get(name='Brand New Place')
        self.assertEqual(restaurant.street_address, '123 Main St')
        self.assertEqual(restaurant.city, 'Toronto')
        self.assertTrue(restaurant.visited)

    def test_new_pop_up_restaurant_requires_website(self):
        response = self.post(self.base_payload(restaurant={
            'mode': 'new',
            'name': 'Pop Up Place',
            'isPopUp': True,
            'website': '',
        }))
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('restaurant', data['errors'])
        self.assertFalse(Restaurant.objects.filter(name='Pop Up Place').exists())

    def test_missing_dishes_rejected(self):
        response = self.post(self.base_payload(dishes=[]))
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('dishes', data['errors'])

    def test_future_visit_date_rejected(self):
        response = self.post(self.base_payload(basicInfo={'visitDate': '2999-01-01', 'partySize': '2', 'entryTime': ''}))
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('visit_date', data['errors'])

    def test_dish_promotes_wishlist_entry_to_had(self):
        restaurant = Restaurant.objects.create(name='Noodle House', visited=True)
        wishlist_dish = RestaurantDish.objects.create(
            restaurant=restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_WISHLIST
        )
        response = self.post(self.base_payload(restaurant={'mode': 'search', 'id': restaurant.pk, 'name': restaurant.name}))
        self.assertEqual(response.status_code, 200, response.content)

        wishlist_dish.refresh_from_db()
        self.assertEqual(wishlist_dish.status, RestaurantDish.STATUS_HAD)
        self.assertIsNotNone(wishlist_dish.review_id)

    def test_created_review_has_expected_dish(self):
        response = self.post(self.base_payload())
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()

        review = Review.objects.get(pk=data['review_id'])
        dish = ReviewDish.objects.get(review=review)
        self.assertEqual(dish.dish_name, 'Ramen')
        self.assertEqual(dish.dish_rating, 90)

    def test_create_review_as_draft(self):
        response = self.post(self.base_payload(is_draft=True))
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()

        review = Review.objects.get(pk=data['review_id'])
        self.assertTrue(review.is_draft)

    def test_create_review_without_draft_flag_is_not_draft(self):
        response = self.post(self.base_payload())
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()

        review = Review.objects.get(pk=data['review_id'])
        self.assertFalse(review.is_draft)

    def test_review_image_preserves_original_filename(self):
        response = self.post(self.base_payload(
            rating={
                'overall': 80, 'title': '', 'notes': '', 'ambiance': 70, 'service': 60,
                'images': [{'id': None, 'src': TINY_PNG_DATA_URL, 'filename': 'sunset-ramen.png'}],
            },
        ))
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()

        review = Review.objects.get(pk=data['review_id'])
        image = Image.objects.get(object_id=review.id, content_type__model='review')
        self.assertEqual(image.image.name.rsplit('/', 1)[-1], 'sunset-ramen.png')

    def test_dish_image_preserves_original_filename(self):
        response = self.post(self.base_payload(
            dishes=[{
                'name': 'Ramen', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': [],
                'images': [{'id': None, 'src': TINY_PNG_DATA_URL, 'filename': 'bowl-of-ramen.png'}],
            }],
        ))
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()

        review = Review.objects.get(pk=data['review_id'])
        dish = ReviewDish.objects.get(review=review)
        image = Image.objects.get(object_id=dish.id, content_type__model='reviewdish')
        self.assertEqual(image.image.name.rsplit('/', 1)[-1], 'bowl-of-ramen.png')

    def test_dish_with_multiple_images_saves_all(self):
        response = self.post(self.base_payload(
            dishes=[{
                'name': 'Ramen', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': [],
                'images': [
                    {'id': None, 'src': TINY_PNG_DATA_URL, 'filename': 'first.png'},
                    {'id': None, 'src': TINY_PNG_DATA_URL, 'filename': 'second.png'},
                ],
            }],
        ))
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()

        review = Review.objects.get(pk=data['review_id'])
        dish = ReviewDish.objects.get(review=review)
        images = Image.objects.filter(object_id=dish.id, content_type__model='reviewdish')
        self.assertEqual(images.count(), 2)
        self.assertEqual(
            sorted(img.image.name.rsplit('/', 1)[-1] for img in images),
            ['first.png', 'second.png'],
        )

    def test_review_image_without_filename_falls_back_to_uuid_name(self):
        response = self.post(self.base_payload(
            rating={
                'overall': 80, 'title': '', 'notes': '', 'ambiance': 70, 'service': 60,
                'images': [{'id': None, 'src': TINY_PNG_DATA_URL}],
            },
        ))
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()

        review = Review.objects.get(pk=data['review_id'])
        image = Image.objects.get(object_id=review.id, content_type__model='review')
        self.assertIn('review_', image.image.name)
