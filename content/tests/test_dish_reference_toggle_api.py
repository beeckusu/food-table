import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from content.models import Restaurant, RestaurantDish, RestaurantDishReference


class DishReferenceToggleApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.restaurant = Restaurant.objects.create(name='Noodle House', city='Toronto', country='Canada')
        self.dish = RestaurantDish.objects.create(restaurant=self.restaurant, dish_name='Ramen', status=RestaurantDish.STATUS_WISHLIST)
        self.client = Client()
        self.client.login(username='staff', password='pw')
        self.url = reverse('content:api_dish_toggle_reference', args=[self.dish.pk])
        self.ig_url = 'https://www.instagram.com/p/abc123/'

    def post(self, body):
        return self.client.post(self.url, data=json.dumps(body), content_type='application/json')

    def test_requires_login(self):
        client = Client()
        response = client.post(self.url, data=json.dumps({}), content_type='application/json')
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_forbidden(self):
        User.objects.create_user('user', password='pw')
        client = Client()
        client.login(username='user', password='pw')
        response = client.post(self.url, data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_creates_reference_when_none_exists(self):
        response = self.post({'source': 'Instagram', 'source_detail': self.ig_url})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['recommended'])
        self.assertTrue(self.dish.references.filter(source='Instagram', source_detail=self.ig_url).exists())

    def test_removes_matching_reference_when_one_exists(self):
        RestaurantDishReference.objects.create(dish=self.dish, source='Instagram', source_detail=self.ig_url)
        response = self.post({'source': 'Instagram', 'source_detail': self.ig_url})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['recommended'])
        self.assertFalse(self.dish.references.filter(source='Instagram', source_detail=self.ig_url).exists())

    def test_only_matching_reference_is_affected(self):
        other_ref = RestaurantDishReference.objects.create(dish=self.dish, source='Instagram', source_detail='https://www.instagram.com/p/other/')
        self.post({'source': 'Instagram', 'source_detail': self.ig_url})
        self.assertTrue(RestaurantDishReference.objects.filter(pk=other_ref.pk).exists())

    def test_nonexistent_dish_returns_404(self):
        response = self.client.post(
            reverse('content:api_dish_toggle_reference', args=[999999]),
            data=json.dumps({'source': 'Instagram', 'source_detail': self.ig_url}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_missing_source_detail_returns_400(self):
        response = self.post({'source': 'Instagram', 'source_detail': ''})
        self.assertEqual(response.status_code, 400)
