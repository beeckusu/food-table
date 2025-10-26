from django.views.generic import ListView
from django.http import QueryDict
from content.models import Review


class ReviewListView(ListView):
    """
    List view for restaurant reviews.
    Shows all public reviews ordered by visit date (newest first) with pagination.
    Supports filtering via URL parameters (infrastructure ready for future filters).
    """
    model = Review
    template_name = 'review/list.html'
    context_object_name = 'reviews'
    paginate_by = 50

    def _parse_filter_params(self):
        """
        Parse filter parameters from URL query string.

        Returns:
            dict: Dictionary of filter parameters. Currently supports:
                - rating_min: Minimum rating (0-100)
                - rating_max: Maximum rating (0-100)
                - date_from: Start date for visit_date range (YYYY-MM-DD)
                - date_to: End date for visit_date range (YYYY-MM-DD)
                - restaurant: Restaurant name search term
                - location: Location filter
        """
        filter_params = {}

        # Rating range filters
        if self.request.GET.get('rating_min'):
            filter_params['rating_min'] = self.request.GET.get('rating_min')
        if self.request.GET.get('rating_max'):
            filter_params['rating_max'] = self.request.GET.get('rating_max')

        # Date range filters
        if self.request.GET.get('date_from'):
            filter_params['date_from'] = self.request.GET.get('date_from')
        if self.request.GET.get('date_to'):
            filter_params['date_to'] = self.request.GET.get('date_to')

        # Restaurant name filter
        if self.request.GET.get('restaurant'):
            filter_params['restaurant'] = self.request.GET.get('restaurant')

        # Location filter
        if self.request.GET.get('location'):
            filter_params['location'] = self.request.GET.get('location')

        return filter_params

    def _build_filter_query_string(self, exclude_page=True):
        """
        Build a query string from current filter parameters.

        Args:
            exclude_page: If True, exclude 'page' parameter from query string

        Returns:
            str: Query string with filter parameters (without leading '?')
        """
        params = QueryDict(mutable=True)

        for key, value in self.filter_params.items():
            if value:  # Only include non-empty values
                params[key] = value

        # Remove page parameter if requested
        if exclude_page and 'page' in params:
            del params['page']

        query_string = params.urlencode()
        return query_string

    def get_queryset(self):
        """
        Return all public reviews ordered by visit date (newest first).
        Parses and stores filter parameters but does not apply them yet (infrastructure only).
        Optimizes queries with select_related and prefetch_related.
        """
        # Parse and store filter parameters
        self.filter_params = self._parse_filter_params()

        # Base queryset - filters will be applied in future tickets
        return Review.objects.filter(
            is_private=False
        ).select_related(
            'created_by'
        ).prefetch_related(
            'images',
            'review_dishes__images'
        ).order_by('-visit_date', '-entry_time')

    def get_context_data(self, **kwargs):
        """
        Add filter-related data to template context.
        """
        context = super().get_context_data(**kwargs)

        # Add filter parameters to context
        context['filter_params'] = self.filter_params

        # Add filter query string for pagination links
        context['filter_query_string'] = self._build_filter_query_string(exclude_page=True)

        return context
