from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from content.models import Encyclopedia


class EncyclopediaListHtmlStrippingTest(TestCase):
    """FT-177: list/search card previews must strip Quill-authored HTML before truncating."""

    def setUp(self):
        self.user = User.objects.create_user('searcher', password='pw')
        self.client = Client()
        self.client.login(username='searcher', password='pw')

    def test_list_view_strips_html_from_description_preview(self):
        Encyclopedia.objects.create(
            name='Biang Biang Noodles',
            slug='biang-biang-noodles',
            description='<p>Biang biang noodles are <strong>hand-pulled</strong> Chinese noodles.</p>',
        )

        response = self.client.get(reverse('content:encyclopedia_list'))

        self.assertNotContains(response, '&lt;p&gt;')
        self.assertContains(response, 'hand-pulled')

    def test_search_view_strips_html_from_description_preview(self):
        Encyclopedia.objects.create(
            name='Biang Biang Noodles',
            slug='biang-biang-noodles',
            description='<p>Biang biang noodles are <strong>hand-pulled</strong> Chinese noodles.</p>',
        )

        response = self.client.get(reverse('content:encyclopedia_search'), {'q': 'Biang'})

        self.assertNotContains(response, '&lt;p&gt;')
        self.assertContains(response, 'hand-pulled')
