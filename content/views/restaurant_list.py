from django.views.generic import ListView
from django.conf import settings
from django.urls import reverse
from content.models import Restaurant


class RestaurantListView(ListView):
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
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visited_param = self.request.GET.get('visited', '')
        context['visited_filter'] = visited_param
        context['total_count'] = Restaurant.objects.count()
        context['visited_count'] = Restaurant.objects.filter(visited=True).count()
        context['wishlist_count'] = Restaurant.objects.filter(visited=False).count()

        map_qs = Restaurant.objects.exclude(latitude=None).exclude(longitude=None)
        if visited_param == '1':
            map_qs = map_qs.filter(visited=True)
        elif visited_param == '0':
            map_qs = map_qs.filter(visited=False)

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
