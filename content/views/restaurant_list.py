from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.conf import settings
from django.urls import reverse
from django.db.utils import ProgrammingError
from django.db.models import Q
from content.models import Restaurant
from content.utils.search import build_prefix_search_query


def _filter_by_search(qs, query):
    """
    Narrow a Restaurant queryset to those matching a free-text query.
    Tries full-text prefix matching first, falling back to ILIKE on
    name/city/street address for short or partial fragments it might miss.
    """
    search_query = build_prefix_search_query(query)
    if search_query is not None:
        try:
            matched_ids = list(qs.filter(search_vector=search_query).values_list('pk', flat=True))
        except ProgrammingError:
            matched_ids = []
        if matched_ids:
            return qs.filter(pk__in=matched_ids)
    return qs.filter(
        Q(name__icontains=query) | Q(city__icontains=query) | Q(street_address__icontains=query)
    )


class RestaurantListView(LoginRequiredMixin, ListView):
    model = Restaurant
    template_name = 'restaurant/list.html'
    context_object_name = 'restaurants'
    paginate_by = 50

    def get_queryset(self):
        qs = Restaurant.objects.prefetch_related('dishes')
        visited_param = self.request.GET.get('visited')
        if visited_param == '1':
            qs = qs.filter(visited=True)
        elif visited_param == '0':
            qs = qs.filter(visited=False)
        query = self.request.GET.get('q', '').strip()
        if query:
            qs = _filter_by_search(qs, query)
        if self.request.GET.get('sort') == 'name':
            qs = qs.order_by('name')
        else:
            qs = qs.order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visited_param = self.request.GET.get('visited', '')
        sort_param = self.request.GET.get('sort', '')
        query = self.request.GET.get('q', '').strip()
        context['visited_filter'] = visited_param
        context['sort'] = sort_param
        context['query'] = query
        context['total_count'] = Restaurant.objects.count()
        context['visited_count'] = Restaurant.objects.filter(visited=True).count()
        context['wishlist_count'] = Restaurant.objects.filter(visited=False).count()

        map_qs = Restaurant.objects.exclude(latitude=None).exclude(longitude=None)
        if visited_param == '1':
            map_qs = map_qs.filter(visited=True)
        elif visited_param == '0':
            map_qs = map_qs.filter(visited=False)
        if query:
            map_qs = _filter_by_search(map_qs, query)
        if sort_param == 'name':
            map_qs = map_qs.order_by('name')
        else:
            map_qs = map_qs.order_by('-created_at')

        context['map_restaurants'] = [
            {
                'name': r.name,
                'lat': r.latitude,
                'lng': r.longitude,
                'visited': r.visited,
                'url': reverse('content:restaurant_detail', args=[r.pk]),
                'city': r.city,
                'country': r.country,
            }
            for r in map_qs
        ]
        context['google_maps_api_key'] = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
        return context
