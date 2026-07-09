from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.utils import ProgrammingError
from django.db.models import Q
from content.models import FoodFestival
from content.utils.search import build_prefix_search_query


def _filter_by_search(qs, query):
    """Narrow a FoodFestival queryset to those matching a free-text query."""
    search_query = build_prefix_search_query(query)
    if search_query is not None:
        try:
            matched_ids = list(qs.filter(search_vector=search_query).values_list('pk', flat=True))
        except ProgrammingError:
            matched_ids = []
        if matched_ids:
            return qs.filter(pk__in=matched_ids)
    return qs.filter(Q(name__icontains=query) | Q(city__icontains=query))


class FoodFestivalListView(LoginRequiredMixin, ListView):
    model = FoodFestival
    template_name = 'food_festival/list.html'
    context_object_name = 'food_festivals'
    paginate_by = 50

    def get_queryset(self):
        qs = FoodFestival.objects.prefetch_related('restaurants', 'dishes')
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
        context['sort'] = self.request.GET.get('sort', '')
        context['query'] = self.request.GET.get('q', '').strip()
        context['total_count'] = FoodFestival.objects.count()
        return context
