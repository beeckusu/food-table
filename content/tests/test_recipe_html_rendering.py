from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from content.models import Recipe


class RecipeListHtmlStrippingTest(TestCase):
    """FT-177: list card preview must strip Quill-authored HTML before truncating."""

    def setUp(self):
        self.user = User.objects.create_user('searcher', password='pw')
        self.client = Client()
        self.client.login(username='searcher', password='pw')

    def test_list_view_strips_html_from_description_preview(self):
        Recipe.objects.create(
            name='Pad Thai',
            slug='pad-thai',
            description='<p>A <em>classic</em> Thai noodle dish.</p>',
        )

        response = self.client.get(reverse('content:recipe_list'))

        self.assertNotContains(response, '&lt;p&gt;')
        self.assertContains(response, 'classic')
