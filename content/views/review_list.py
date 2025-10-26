from django.views.generic import ListView
from django.http import QueryDict
from django.db.models import Count
from datetime import datetime
from content.models import Review, ReviewTag


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
                - tags: List of tags (multi-value parameter)
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

        # Tag filter (multi-value)
        tags = self.request.GET.getlist('tags')
        if tags:
            filter_params['tags'] = tags

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
                if key == 'tags' and isinstance(value, list):
                    # Handle multi-value tags parameter
                    for tag in value:
                        params.appendlist('tags', tag)
                else:
                    params[key] = value

        # Remove page parameter if requested
        if exclude_page and 'page' in params:
            del params['page']

        query_string = params.urlencode()
        return query_string

    def get_queryset(self):
        """
        Return all public reviews ordered by visit date (newest first).
        Applies filters based on URL parameters.
        Optimizes queries with select_related and prefetch_related.
        """
        # Parse and store filter parameters
        self.filter_params = self._parse_filter_params()

        # Base queryset
        queryset = Review.objects.filter(
            is_private=False
        ).select_related(
            'created_by'
        ).prefetch_related(
            'images',
            'review_dishes__images'
        )

        if self.filter_params.get('restaurant'):
            queryset = queryset.filter(restaurant_name__iexact=self.filter_params['restaurant'])

        # Apply rating range filter (FT-37)
        if self.filter_params.get('rating_min'):
            try:
                rating_min = int(self.filter_params['rating_min'])
                if 0 <= rating_min <= 100:
                    queryset = queryset.filter(rating__gte=rating_min)
            except (ValueError, TypeError):
                pass  # Ignore invalid rating values

        if self.filter_params.get('rating_max'):
            try:
                rating_max = int(self.filter_params['rating_max'])
                if 0 <= rating_max <= 100:
                    queryset = queryset.filter(rating__lte=rating_max)
            except (ValueError, TypeError):
                pass  # Ignore invalid rating values

        if self.filter_params.get('date_from'):
            try:
                date_from = datetime.strptime(self.filter_params['date_from'], '%Y-%m-%d').date()
                queryset = queryset.filter(visit_date__gte=date_from)
            except ValueError:
                pass  # Ignore invalid date format

        if self.filter_params.get('date_to'):
            try:
                date_to = datetime.strptime(self.filter_params['date_to'], '%Y-%m-%d').date()
                queryset = queryset.filter(visit_date__lte=date_to)
            except ValueError:
                pass  # Ignore invalid date format

        # Apply tag filter with AND logic (FT-36)
        if self.filter_params.get('tags'):
            selected_tags = self.filter_params['tags']
            # Filter reviews that have ALL selected tags (AND logic)
            queryset = queryset.filter(
                review_tags__tag__in=selected_tags
            ).annotate(
                tag_count=Count('review_tags', distinct=True)
            ).filter(
                tag_count=len(selected_tags)
            )

        return queryset.order_by('-visit_date', '-entry_time')

    def _get_restaurant_options(self):
        """
        Get distinct restaurant names for dropdown (FT-35).
        Returns sorted list of unique restaurant names, excluding empty values.
        """
        restaurants = Review.objects.filter(
            is_private=False
        ).values_list('restaurant_name', flat=True).distinct().order_by('restaurant_name')

        # Filter out None and empty strings
        return [r for r in restaurants if r]

    def _get_tag_options(self):
        """
        Get distinct tags for checkboxes (FT-36).
        Returns sorted list of unique tags from public reviews.
        """
        tags = ReviewTag.objects.filter(
            review__is_private=False
        ).values_list('tag', flat=True).distinct().order_by('tag')

        # Filter out None and empty strings
        return [t for t in tags if t]

    def get_context_data(self, **kwargs):
        """
        Add filter-related data to template context.
        """
        context = super().get_context_data(**kwargs)

        # Add filter parameters to context
        context['filter_params'] = self.filter_params

        # Add filter query string for pagination links
        context['filter_query_string'] = self._build_filter_query_string(exclude_page=True)

        # Add dropdown options (FT-35)
        context['restaurant_options'] = self._get_restaurant_options()

        # Add tag options (FT-36)
        context['tag_options'] = self._get_tag_options()

        return context
