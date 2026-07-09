import json
from datetime import date, time

from django.db import IntegrityError, transaction
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from content.models import FoodFestival, Restaurant, RestaurantDish, Review, ReviewDish


class ReviewModalTemplateRenderTest(TestCase):
    """Renders the page embedding review_modal.html (staff-only markup) to catch template syntax errors."""

    def test_review_list_renders_for_staff(self):
        staff = User.objects.create_user('staff', password='pw', is_staff=True)
        client = Client()
        client.login(username='staff', password='pw')
        response = client.get(reverse('content:review_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'reviewTargetTypeFoodFestival')
        self.assertContains(response, 'group-new-restaurant-name')


class FoodFestivalModelTest(TestCase):
    def test_str_includes_city_and_country(self):
        festival = FoodFestival.objects.create(name='Taste of the City', city='Toronto', country='Canada')
        self.assertEqual(str(festival), 'Taste of the City, Toronto, Canada')

    def test_str_falls_back_to_name_only(self):
        festival = FoodFestival.objects.create(name='Taste of the City')
        self.assertEqual(str(festival), 'Taste of the City')

    def test_restaurants_many_to_many(self):
        festival = FoodFestival.objects.create(name='Taste of the City')
        r1 = Restaurant.objects.create(name='Vendor A')
        r2 = Restaurant.objects.create(name='Vendor B')
        festival.restaurants.add(r1, r2)
        self.assertEqual(festival.restaurants.count(), 2)
        self.assertIn(festival, r1.food_festivals.all())

    def test_search_vector_populated_on_save(self):
        festival = FoodFestival.objects.create(name='Taste of the City')
        festival.refresh_from_db()
        self.assertIsNotNone(festival.search_vector)


class RestaurantDishRestaurantRequiredTest(TestCase):
    def test_dish_with_restaurant_only_is_valid(self):
        restaurant = Restaurant.objects.create(name='Diner')
        dish = RestaurantDish.objects.create(restaurant=restaurant, dish_name='Fries')
        self.assertIsNone(dish.food_festival_id)

    def test_dish_with_restaurant_and_food_festival_is_valid(self):
        restaurant = Restaurant.objects.create(name='Vendor Stall')
        festival = FoodFestival.objects.create(name='Taste of the City')
        dish = RestaurantDish.objects.create(restaurant=restaurant, food_festival=festival, dish_name='Fries')
        self.assertEqual(dish.restaurant_id, restaurant.pk)
        self.assertEqual(dish.food_festival_id, festival.pk)

    def test_dish_without_restaurant_rejected(self):
        festival = FoodFestival.objects.create(name='Taste of the City')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RestaurantDish.objects.create(food_festival=festival, dish_name='Fries')


class ReviewTargetConstraintTest(TestCase):
    def test_review_with_neither_target_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    visit_date=date(2025, 1, 1), entry_time='12:00', party_size=1, rating=50,
                )

    def test_review_with_both_targets_rejected(self):
        restaurant = Restaurant.objects.create(name='Diner')
        festival = FoodFestival.objects.create(name='Taste of the City')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    restaurant=restaurant, food_festival=festival,
                    visit_date=date(2025, 1, 1), entry_time='12:00', party_size=1, rating=50,
                )


class FoodFestivalListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('viewer', password='pw')
        self.client = Client()
        self.client.login(username='viewer', password='pw')

    def test_food_festivals_excluded_from_restaurant_list(self):
        Restaurant.objects.create(name='Diner')
        FoodFestival.objects.create(name='Taste of the City')

        response = self.client.get(reverse('content:restaurant_list'))
        names = [r.name for r in response.context['restaurants']]
        self.assertEqual(names, ['Diner'])

    def test_food_festival_list_view_renders(self):
        FoodFestival.objects.create(name='Taste of the City')
        response = self.client.get(reverse('content:food_festival_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Taste of the City')


class FoodFestivalDetailViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.festival = FoodFestival.objects.create(name='Taste of the City')

    def test_detail_renders(self):
        response = self.client.get(reverse('content:food_festival_detail', kwargs={'pk': self.festival.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Taste of the City')

    def test_dishes_grouped_by_restaurant(self):
        vendor_a = Restaurant.objects.create(name='Vendor A')
        vendor_b = Restaurant.objects.create(name='Vendor B')
        self.festival.restaurants.add(vendor_a, vendor_b)
        RestaurantDish.objects.create(
            restaurant=vendor_a, food_festival=self.festival, dish_name='Poutine', status=RestaurantDish.STATUS_HAD
        )
        RestaurantDish.objects.create(
            restaurant=vendor_a, food_festival=self.festival, dish_name='Corn Dog', status=RestaurantDish.STATUS_WISHLIST
        )
        RestaurantDish.objects.create(
            restaurant=vendor_b, food_festival=self.festival, dish_name='Ramen', status=RestaurantDish.STATUS_HAD
        )

        response = self.client.get(reverse('content:food_festival_detail', kwargs={'pk': self.festival.pk}))
        self.assertEqual(response.status_code, 200)

        groups = {g['restaurant'].name: g for g in response.context['restaurant_groups']}
        self.assertEqual({d.dish_name for d in groups['Vendor A']['dishes_had']}, {'Poutine'})
        self.assertEqual({d.dish_name for d in groups['Vendor A']['dishes_wishlist']}, {'Corn Dog'})
        self.assertEqual({d.dish_name for d in groups['Vendor B']['dishes_had']}, {'Ramen'})
        self.assertEqual(groups['Vendor B']['dishes_wishlist'], [])

        self.assertContains(response, 'Poutine')
        self.assertContains(response, 'Corn Dog')
        self.assertContains(response, 'Ramen')

        # Every restaurant group's accordion body must be expanded by default (not just the
        # first) so all dishes are visible at a glance without having to click to expand.
        self.assertEqual(
            response.content.decode().count('accordion-collapse collapse show'),
            len(response.context['restaurant_groups']),
        )
        self.assertNotContains(response, 'accordion-button collapsed')

    def test_add_restaurant_by_name(self):
        response = self.client.post(
            reverse('content:food_festival_add_restaurant', kwargs={'pk': self.festival.pk}),
            {'restaurant_name': 'Vendor Stall'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.festival.restaurants.count(), 1)
        self.assertEqual(self.festival.restaurants.first().name, 'Vendor Stall')

    def test_add_existing_restaurant_by_id(self):
        restaurant = Restaurant.objects.create(name='Existing Vendor')
        response = self.client.post(
            reverse('content:food_festival_add_restaurant', kwargs={'pk': self.festival.pk}),
            {'restaurant_id': restaurant.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(restaurant, self.festival.restaurants.all())

    def test_remove_restaurant(self):
        restaurant = Restaurant.objects.create(name='Existing Vendor')
        self.festival.restaurants.add(restaurant)
        response = self.client.post(
            reverse('content:food_festival_remove_restaurant', kwargs={'pk': self.festival.pk, 'restaurant_pk': restaurant.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.festival.restaurants.count(), 0)

    def test_dish_create_requires_restaurant(self):
        create_url = reverse('content:food_festival_dish_create', kwargs={'pk': self.festival.pk})
        response = self.client.post(create_url, {'dish_name': 'Poutine', 'status': RestaurantDish.STATUS_WISHLIST, 'notes': ''})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(RestaurantDish.objects.filter(food_festival=self.festival, dish_name='Poutine').exists())

    def test_dish_create_update_delete(self):
        create_url = reverse('content:food_festival_dish_create', kwargs={'pk': self.festival.pk})
        response = self.client.post(create_url, {
            'dish_name': 'Poutine', 'status': RestaurantDish.STATUS_WISHLIST, 'notes': '',
            'restaurant_name': 'Vendor Stall',
        })
        self.assertEqual(response.status_code, 302)
        dish = RestaurantDish.objects.get(food_festival=self.festival, dish_name='Poutine')
        self.assertEqual(dish.restaurant.name, 'Vendor Stall')
        self.assertIn(dish.restaurant, self.festival.restaurants.all())

        mark_tried_url = reverse('content:food_festival_dish_mark_tried', kwargs={'pk': self.festival.pk, 'dish_pk': dish.pk})
        response = self.client.post(mark_tried_url)
        self.assertEqual(response.status_code, 302)
        dish.refresh_from_db()
        self.assertEqual(dish.status, RestaurantDish.STATUS_HAD)

        delete_url = reverse('content:food_festival_dish_delete', kwargs={'pk': self.festival.pk, 'dish_pk': dish.pk})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(RestaurantDish.objects.filter(pk=dish.pk).exists())

    def test_requires_staff(self):
        non_staff = User.objects.create_user('user', password='pw')
        c = Client()
        c.login(username='user', password='pw')
        response = c.post(
            reverse('content:food_festival_add_restaurant', kwargs={'pk': self.festival.pk}),
            {'restaurant_name': 'Vendor Stall'},
        )
        self.assertEqual(response.status_code, 403)


class FoodFestivalAdminSmokeTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'pw')
        self.client = Client()
        self.client.login(username='admin', password='pw')

    def test_admin_list_page_loads(self):
        FoodFestival.objects.create(name='Taste of the City')
        response = self.client.get('/admin/content/foodfestival/')
        self.assertEqual(response.status_code, 200)

    def test_admin_can_add_dish_via_inline(self):
        festival = FoodFestival.objects.create(name='Taste of the City')
        restaurant = Restaurant.objects.create(name='Vendor Stall')
        response = self.client.post(f'/admin/content/foodfestival/{festival.pk}/change/', {
            'name': festival.name,
            'city': '', 'country': '', 'start_date': '', 'end_date': '', 'website': '',
            'restaurants': [],
            'dishes-TOTAL_FORMS': '1',
            'dishes-INITIAL_FORMS': '0',
            'dishes-MIN_NUM_FORMS': '0',
            'dishes-MAX_NUM_FORMS': '1000',
            'dishes-0-dish_name': 'Poutine',
            'dishes-0-restaurant': restaurant.pk,
            'dishes-0-status': RestaurantDish.STATUS_WISHLIST,
            'dishes-0-notes': '',
            'dishes-0-food_festival': festival.pk,
            '_save': 'Save',
        })
        self.assertIn(response.status_code, (200, 302), response.content)
        self.assertTrue(RestaurantDish.objects.filter(food_festival=festival, restaurant=restaurant, dish_name='Poutine').exists())


class ReviewCreateApiFoodFestivalTest(TestCase):
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
            'targetType': 'food_festival',
            'food_festival': {'mode': 'new', 'name': 'Taste of the City', 'city': 'Toronto'},
            'rating': {'overall': 80, 'title': 'Fun day', 'notes': '', 'ambiance': 70, 'service': 60, 'images': []},
            'dishes': [{
                'name': 'Corn Dog', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': [],
                'restaurant': {'mode': 'search', 'name': 'Vendor Stall'},
            }],
        }
        payload.update(overrides)
        return payload

    def test_create_review_with_new_food_festival(self):
        response = self.post(self.base_payload())
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()

        review = Review.objects.get(pk=data['review_id'])
        self.assertIsNone(review.restaurant_id)
        self.assertEqual(review.food_festival.name, 'Taste of the City')

        dish = RestaurantDish.objects.get(review=review)
        self.assertEqual(dish.food_festival, review.food_festival)
        self.assertEqual(dish.restaurant.name, 'Vendor Stall')
        self.assertIn(dish.restaurant, review.food_festival.restaurants.all())

    def test_dish_missing_restaurant_rejected(self):
        response = self.post(self.base_payload(dishes=[{
            'name': 'Corn Dog', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': [],
            'restaurant': {'mode': 'search', 'name': ''},
        }]))
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('dish_0_restaurant', data['errors'])

    def test_dish_with_new_restaurant_mode_fills_address_fields(self):
        response = self.post(self.base_payload(dishes=[{
            'name': 'Corn Dog', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': [],
            'restaurant': {
                'mode': 'new', 'name': 'Vendor Stall', 'isPopUp': False,
                'address': '123 Main St', 'city': 'Toronto', 'province': 'ON',
                'country': 'Canada', 'postalCode': 'M1M1M1', 'googlePlaceId': 'abc123',
            },
        }]))
        self.assertEqual(response.status_code, 200, response.content)

        restaurant = Restaurant.objects.get(name='Vendor Stall')
        self.assertEqual(restaurant.street_address, '123 Main St')
        self.assertEqual(restaurant.city, 'Toronto')
        self.assertEqual(restaurant.google_place_id, 'abc123')

        dish = RestaurantDish.objects.get(dish_name='Corn Dog')
        self.assertEqual(dish.restaurant, restaurant)

    def test_multiple_dishes_sharing_new_restaurant_create_one_restaurant(self):
        shared_restaurant = {
            'mode': 'new', 'name': 'Vendor Stall', 'isPopUp': False,
            'address': '123 Main St', 'city': 'Toronto', 'province': 'ON',
            'country': 'Canada', 'postalCode': 'M1M1M1',
        }
        response = self.post(self.base_payload(dishes=[
            {'name': 'Corn Dog', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': [], 'restaurant': shared_restaurant},
            {'name': 'Poutine', 'rating': 85, 'notes': '', 'cost': None, 'encyclopedia_ids': [], 'restaurant': shared_restaurant},
        ]))
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(Restaurant.objects.filter(name='Vendor Stall').count(), 1)
        restaurant = Restaurant.objects.get(name='Vendor Stall')
        dish_names = set(RestaurantDish.objects.filter(restaurant=restaurant).values_list('dish_name', flat=True))
        self.assertEqual(dish_names, {'Corn Dog', 'Poutine'})

    def test_dish_new_pop_up_restaurant_requires_website(self):
        response = self.post(self.base_payload(dishes=[{
            'name': 'Corn Dog', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': [],
            'restaurant': {'mode': 'new', 'name': 'Vendor Truck', 'isPopUp': True, 'website': ''},
        }]))
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('dish_0_restaurant', data['errors'])

    def test_create_review_with_existing_food_festival_by_id(self):
        festival = FoodFestival.objects.create(name='Taste of the City')
        response = self.post(self.base_payload(food_festival={'mode': 'search', 'id': festival.pk, 'name': festival.name}))
        self.assertEqual(response.status_code, 200, response.content)

        review = Review.objects.get(food_festival=festival)
        self.assertEqual(review.food_festival_id, festival.pk)

    def test_missing_food_festival_name_rejected(self):
        response = self.post(self.base_payload(food_festival={'mode': 'new', 'name': ''}))
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('food_festival', data['errors'])

    def test_dish_promotes_wishlist_entry_to_had(self):
        festival = FoodFestival.objects.create(name='Taste of the City')
        restaurant = Restaurant.objects.create(name='Vendor Stall')
        wishlist_dish = RestaurantDish.objects.create(
            restaurant=restaurant, food_festival=festival, dish_name='Corn Dog', status=RestaurantDish.STATUS_WISHLIST
        )
        response = self.post(self.base_payload(
            food_festival={'mode': 'search', 'id': festival.pk, 'name': festival.name},
            dishes=[{
                'name': 'Corn Dog', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': [],
                'restaurant': {'mode': 'search', 'id': restaurant.pk, 'name': restaurant.name},
            }],
        ))
        self.assertEqual(response.status_code, 200, response.content)

        wishlist_dish.refresh_from_db()
        self.assertEqual(wishlist_dish.status, RestaurantDish.STATUS_HAD)
        self.assertIsNotNone(wishlist_dish.review_id)


class ReviewUpdateApiFoodFestivalTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.festival = FoodFestival.objects.create(name='Taste of the City')
        self.review = Review.objects.create(
            food_festival=self.festival,
            visit_date=date(2025, 1, 15),
            entry_time=time(18, 30),
            party_size=2,
            rating=80,
            title='Fun day',
            created_by=self.staff,
        )
        ReviewDish.objects.create(review=self.review, dish_name='Corn Dog', dish_rating=90)
        self.client = Client()
        self.client.login(username='staff', password='pw')

    def test_edit_data_returns_food_festival_shape(self):
        url = reverse('content:api_review_edit_data', kwargs={'pk': self.review.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()['review']
        self.assertEqual(data['targetType'], 'food_festival')
        self.assertEqual(data['food_festival']['id'], self.festival.pk)
        self.assertEqual(data['restaurant'], {})

    def test_update_keeps_food_festival_target(self):
        url = reverse('content:api_review_update', kwargs={'pk': self.review.pk})
        payload = {
            'basicInfo': {'visitDate': '2025-01-16', 'partySize': '3', 'entryTime': '19:00'},
            'targetType': 'food_festival',
            'food_festival': {'mode': 'search', 'id': self.festival.pk, 'name': self.festival.name},
            'rating': {'overall': 85, 'title': 'Fun day', 'notes': '', 'ambiance': 70, 'service': 60, 'images': []},
            'dishes': [{
                'id': None, 'name': 'Corn Dog', 'rating': 90, 'notes': '', 'cost': None, 'encyclopedia_ids': [],
                'restaurant': {'mode': 'search', 'name': 'Vendor Stall'},
            }],
        }
        response = self.client.patch(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)

        self.review.refresh_from_db()
        self.assertEqual(self.review.food_festival_id, self.festival.pk)
        self.assertIsNone(self.review.restaurant_id)
        self.assertEqual(self.review.party_size, 3)

        dish = RestaurantDish.objects.get(review=self.review)
        self.assertEqual(dish.restaurant.name, 'Vendor Stall')


class ReviewDetailFoodFestivalTest(TestCase):
    """The review detail page must render for food-festival reviews (no restaurant FK to link/lookup)."""

    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.festival = FoodFestival.objects.create(name='Taste of the City', city='Toronto')
        self.vendor_a = Restaurant.objects.create(name='Vendor A')
        self.vendor_b = Restaurant.objects.create(name='Vendor B')
        self.review = Review.objects.create(
            food_festival=self.festival,
            visit_date=date(2025, 1, 15),
            entry_time=time(18, 30),
            party_size=2,
            rating=80,
            created_by=self.staff,
        )
        ReviewDish.objects.create(review=self.review, dish_name='Poutine', dish_rating=90)
        ReviewDish.objects.create(review=self.review, dish_name='Ramen', dish_rating=70)
        RestaurantDish.objects.create(
            restaurant=self.vendor_a, food_festival=self.festival, review=self.review,
            dish_name='Poutine', status=RestaurantDish.STATUS_HAD,
        )
        RestaurantDish.objects.create(
            restaurant=self.vendor_b, food_festival=self.festival, review=self.review,
            dish_name='Ramen', status=RestaurantDish.STATUS_HAD,
        )

    def test_detail_renders_without_crash(self):
        response = self.client.get(reverse('content:review_detail', kwargs={'pk': self.review.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Taste of the City')

    def test_dishes_show_their_own_restaurant(self):
        response = self.client.get(reverse('content:review_detail', kwargs={'pk': self.review.pk}))
        self.assertContains(response, 'Poutine')
        self.assertContains(response, 'Ramen')
        self.assertContains(response, 'Vendor A')
        self.assertContains(response, 'Vendor B')

    def test_related_reviews_scoped_to_same_festival(self):
        other_festival = FoodFestival.objects.create(name='Other Festival')
        Review.objects.create(
            food_festival=other_festival, visit_date=date(2025, 1, 1), entry_time=time(12, 0),
            party_size=1, rating=50, created_by=self.staff,
        )
        response = self.client.get(reverse('content:review_detail', kwargs={'pk': self.review.pk}))
        related_ids = {r.pk for r in response.context['related_reviews']}
        self.assertNotIn(
            Review.objects.get(food_festival=other_festival).pk, related_ids
        )
