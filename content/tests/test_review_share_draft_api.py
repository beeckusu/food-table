import json
import tempfile
from datetime import date, time

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from content.models import Image, MenuItem, Restaurant, Review, ReviewDish

_GIF_BYTES = (
    b'GIF87a\x01\x00\x01\x00\x80\x01\x00\xff\xff\xff\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ReviewShareDraftApiViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.restaurant = Restaurant.objects.create(name='Pizza Cafe')
        self.review = Review.objects.create(
            restaurant=self.restaurant,
            visit_date=date(2026, 1, 1),
            entry_time=time(19, 0),
            party_size=2,
            rating=80,
            notes='Great pizza.',
        )
        menu_item = MenuItem.objects.create(restaurant=self.restaurant, name='Margherita')
        self.dish = ReviewDish.objects.create(review=self.review, menu_item=menu_item)

        self.review_image = Image.objects.create(
            image=SimpleUploadedFile('review.gif', _GIF_BYTES, content_type='image/gif'),
            content_type=ContentType.objects.get_for_model(Review),
            object_id=self.review.id,
            uploaded_by=self.staff,
        )
        self.dish_image = Image.objects.create(
            image=SimpleUploadedFile('dish.gif', _GIF_BYTES, content_type='image/gif'),
            content_type=ContentType.objects.get_for_model(ReviewDish),
            object_id=self.dish.id,
            uploaded_by=self.staff,
        )

        self.client = Client()
        self.url = reverse('content:api_review_share_draft_save', kwargs={'pk': self.review.pk})

    def _post(self, body):
        return self.client.post(self.url, data=json.dumps(body), content_type='application/json')

    def test_requires_login(self):
        response = self._post({'segments': [{'type': 'shared', 'text': 'hi'}]})
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_forbidden(self):
        User.objects.create_user('user', password='pw')
        self.client.login(username='user', password='pw')
        response = self._post({'segments': [{'type': 'shared', 'text': 'hi'}]})
        self.assertNotEqual(response.status_code, 200)

    def test_invalid_json_rejected(self):
        self.client.login(username='staff', password='pw')
        response = self.client.post(self.url, data='not json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_non_list_segments_rejected(self):
        self.client.login(username='staff', password='pw')
        response = self._post({'segments': 'not a list'})
        self.assertEqual(response.status_code, 400)

    def test_non_dict_platforms_rejected(self):
        self.client.login(username='staff', password='pw')
        response = self._post({'segments': [], 'platforms': 'nope'})
        self.assertEqual(response.status_code, 400)

    def test_save_persists_interleaved_segments_and_image_ids(self):
        self.client.login(username='staff', password='pw')
        response = self._post({
            'segments': [
                {'type': 'shared', 'text': 'Came here for dinner.'},
                {'type': 'instagram', 'text': '#pizza'},
                {'type': 'shared', 'text': 'Would recommend.'},
                {'type': 'google', 'text': 'Service was slow.'},
            ],
            'platforms': {
                'instagram': {'image_ids': [self.review_image.id, self.dish_image.id]},
                'google': {'image_ids': []},
                'yelp': {'image_ids': []},
            },
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        self.review.refresh_from_db()
        share_draft = self.review.metadata['share_draft']
        self.assertEqual(
            share_draft['segments'],
            [
                {'type': 'shared', 'text': 'Came here for dinner.'},
                {'type': 'instagram', 'text': '#pizza'},
                {'type': 'shared', 'text': 'Would recommend.'},
                {'type': 'google', 'text': 'Service was slow.'},
            ],
        )
        self.assertEqual(
            sorted(share_draft['platforms']['instagram']['image_ids']),
            sorted([self.review_image.id, self.dish_image.id]),
        )
        self.assertIn('updated_at', share_draft)

    def test_segment_with_invalid_type_dropped(self):
        self.client.login(username='staff', password='pw')
        response = self._post({
            'segments': [
                {'type': 'shared', 'text': 'kept'},
                {'type': 'facebook', 'text': 'dropped — not a known platform'},
                'not a dict',
            ],
        })
        self.assertEqual(response.status_code, 200)
        self.review.refresh_from_db()
        share_draft = self.review.metadata['share_draft']
        self.assertEqual(share_draft['segments'], [{'type': 'shared', 'text': 'kept'}])

    def test_unknown_image_ids_dropped(self):
        self.client.login(username='staff', password='pw')
        bogus_id = self.dish_image.id + 99999
        response = self._post({
            'segments': [],
            'platforms': {
                'instagram': {'image_ids': [bogus_id]},
            },
        })
        self.assertEqual(response.status_code, 200)
        self.review.refresh_from_db()
        share_draft = self.review.metadata['share_draft']
        self.assertEqual(share_draft['platforms']['instagram']['image_ids'], [])

    def test_repost_overwrites_previous_draft(self):
        self.client.login(username='staff', password='pw')
        self._post({'segments': [{'type': 'shared', 'text': 'first'}]})
        self._post({'segments': [{'type': 'shared', 'text': 'second'}]})

        self.review.refresh_from_db()
        self.assertEqual(self.review.metadata['share_draft']['segments'], [{'type': 'shared', 'text': 'second'}])

    def test_missing_platform_keys_default_empty(self):
        self.client.login(username='staff', password='pw')
        response = self._post({'segments': [], 'platforms': {}})
        self.assertEqual(response.status_code, 200)
        self.review.refresh_from_db()
        platforms = self.review.metadata['share_draft']['platforms']
        for platform in ('instagram', 'google', 'yelp'):
            self.assertEqual(platforms[platform], {'image_ids': []})

    def test_missing_segments_defaults_empty(self):
        self.client.login(username='staff', password='pw')
        response = self._post({})
        self.assertEqual(response.status_code, 200)
        self.review.refresh_from_db()
        self.assertEqual(self.review.metadata['share_draft']['segments'], [])

    def test_404_for_missing_review(self):
        self.client.login(username='staff', password='pw')
        url = reverse('content:api_review_share_draft_save', kwargs={'pk': 999999})
        response = self.client.post(url, data=json.dumps({'segments': []}), content_type='application/json')
        self.assertEqual(response.status_code, 404)
