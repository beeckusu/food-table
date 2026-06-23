from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from content.models import Encyclopedia


def make_entry(**kwargs):
    defaults = {'name': 'Test Entry', 'description': 'A test description', 'is_placeholder': False}
    defaults.update(kwargs)
    return Encyclopedia.objects.create(**defaults)


class EncyclopediaSearchViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('searcher', password='pw')
        self.client = Client()
        self.client.login(username='searcher', password='pw')
        self.url = reverse('content:encyclopedia_search')

    def test_exact_name_match_ranks_above_incidental_description_mentions(self):
        """FT-176: searching 'Chinese' should surface the Chinese entry first, not
        dishes that merely mention it several times in their description."""
        make_entry(
            name='Almond Cookies',
            description='<p>A classic Chinese bakery treat. Chinese bakeries sell these '
                         'for Chinese New Year, a Chinese favorite.</p>',
            slug='almond-cookies'
        )
        make_entry(name='Chinese', cuisine_type='Chinese', description='A major East Asian cuisine.', slug='chinese')

        response = self.client.get(self.url, {'q': 'Chinese'})

        self.assertEqual(response.status_code, 200)
        entries = list(response.context['entries'])
        self.assertEqual(entries[0].name, 'Chinese')
