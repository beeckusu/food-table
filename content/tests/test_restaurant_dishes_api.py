import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from content.models import Restaurant, RestaurantDish, RestaurantDishReference


class RestaurantDishesApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.restaurant = Restaurant.objects.create(name='Noodle House', city='Toronto', country='Canada')
        self.client = Client()
        self.client.login(username='staff', password='pw')

    def url(self, source_detail=None):
        base = reverse('content:api_restaurant_dishes', args=[self.restaurant.pk])
        if source_detail is not None:
            return base + '?source_detail=' + source_detail
        return base

    def test_requires_login(self):
        client = Client()
        response = client.get(self.url())
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_forbidden(self):
        User.objects.create_user('user', password='pw')
        client = Client()
        client.login(username='user', password='pw')
        response = client.get(self.url())
        self.assertEqual(response.status_code, 403)

    def test_returns_had_and_wishlist_dishes(self):
        RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_HAD)
        RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Gyoza', status=RestaurantDish.STATUS_WISHLIST)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        names = sorted(d['name'] for d in data['results'])
        self.assertEqual(names, ['Gyoza', 'Ramen'])

    def test_recommended_true_when_reference_matches_source_detail(self):
        ig_url = 'https://www.instagram.com/p/abc123/'
        dish = RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_WISHLIST)
        RestaurantDishReference.objects.create(dish=dish, source='Instagram', source_detail=ig_url)
        response = self.client.get(self.url(source_detail=ig_url))
        data = json.loads(response.content)
        self.assertTrue(data['results'][0]['recommended'])

    def test_recommended_false_when_no_matching_reference(self):
        dish = RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_WISHLIST)
        RestaurantDishReference.objects.create(dish=dish, source='Instagram', source_detail='https://www.instagram.com/p/other/')
        response = self.client.get(self.url(source_detail='https://www.instagram.com/p/abc123/'))
        data = json.loads(response.content)
        self.assertFalse(data['results'][0]['recommended'])

    def test_recommended_false_without_source_detail_param(self):
        dish = RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_WISHLIST)
        RestaurantDishReference.objects.create(dish=dish, source='Instagram', source_detail='https://www.instagram.com/p/abc123/')
        response = self.client.get(self.url())
        data = json.loads(response.content)
        self.assertFalse(data['results'][0]['recommended'])

    def test_nonexistent_restaurant_returns_404(self):
        response = self.client.get(reverse('content:api_restaurant_dishes', args=[999999]))
        self.assertEqual(response.status_code, 404)
