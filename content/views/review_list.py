from django.views.generic import ListView
from django.http import QueryDict
from django.db.models import Count
from content.models import Review, ReviewTag
from content.forms import ReviewFilterForm


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

    def _get_filter_form(self):
        """
        Create and validate the filter form with dynamic choices.

        Returns:
            ReviewFilterForm: Validated form instance
        """
        # Get dynamic choices
        restaurant_choices = [(r, r) for r in self._get_restaurant_options()]
        tag_choices = [(t, t) for t in self._get_tag_options()]

        # Create form with GET data and choices
        form = ReviewFilterForm(
            self.request.GET or None,
            restaurant_choices=restaurant_choices,
            tag_choices=tag_choices
        )

        # Validate form (will populate cleaned_data)
        form.is_valid()

        return form

    def _get_sort_order(self, sort_key):
        """
        Get the order_by fields based on sort parameter.

        Args:
            sort_key: Sort key from form cleaned_data

        Returns:
            list: List of field names to pass to order_by()
        """
        # Sort key to Django order_by mapping
        sort_mapping = {
            'rating_desc': ['-rating'],
            'rating_asc': ['rating'],
            'date_desc': ['-visit_date', '-entry_time'],
            'date_asc': ['visit_date', 'entry_time'],
            'name_asc': ['restaurant_name'],
            'name_desc': ['-restaurant_name'],
        }

        # Default to newest first if no sort key
        if not sort_key:
            sort_key = 'date_desc'

        return sort_mapping.get(sort_key, ['-visit_date', '-entry_time'])

    def _build_filter_query_string(self, form, exclude_page=True):
        """
        Build a query string from form cleaned data.

        Args:
            form: The validated ReviewFilterForm instance
            exclude_page: If True, exclude 'page' parameter from query string

        Returns:
            str: Query string with filter parameters (without leading '?')
        """
        params = QueryDict(mutable=True)

        for key, value in form.cleaned_data.items():
            if value:  # Only include non-empty values
                if key == 'tags' and isinstance(value, list):
                    # Handle multi-value tags parameter
                    for tag in value:
                        params.appendlist('tags', tag)
                else:
                    params[key] = str(value)

        # Remove page parameter if requested
        if exclude_page and 'page' in params:
            del params['page']

        query_string = params.urlencode()
        return query_string

    def get_queryset(self):
        """
        Return all public reviews ordered by visit date (newest first).
        Applies filters based on validated form data.
        Optimizes queries with select_related and prefetch_related.
        """
        # Get validated form (store for use in context)
        self.filter_form = self._get_filter_form()

        # Base queryset
        queryset = Review.objects.filter(
            is_private=False
        ).select_related(
            'created_by'
        ).prefetch_related(
            'images',
            'review_dishes__images'
        )

        # Apply filters from cleaned_data (automatically validated)
        cleaned_data = self.filter_form.cleaned_data

        # Restaurant filter
        if cleaned_data.get('restaurant'):
            queryset = queryset.filter(restaurant_name__iexact=cleaned_data['restaurant'])

        # Rating range filters (validated by form)
        if cleaned_data.get('rating_min') is not None:
            queryset = queryset.filter(rating__gte=cleaned_data['rating_min'])

        if cleaned_data.get('rating_max') is not None:
            queryset = queryset.filter(rating__lte=cleaned_data['rating_max'])

        # Date range filters (validated by form)
        if cleaned_data.get('date_from'):
            queryset = queryset.filter(visit_date__gte=cleaned_data['date_from'])

        if cleaned_data.get('date_to'):
            queryset = queryset.filter(visit_date__lte=cleaned_data['date_to'])

        # Tag filter with AND logic
        if cleaned_data.get('tags'):
            selected_tags = cleaned_data['tags']
            queryset = queryset.filter(
                review_tags__tag__in=selected_tags
            ).annotate(
                tag_count=Count('review_tags', distinct=True)
            ).filter(
                tag_count=len(selected_tags)
            )

        # Apply sorting
        order_by_fields = self._get_sort_order(cleaned_data.get('sort'))
        return queryset.order_by(*order_by_fields)

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
        Add filter form and related data to template context.
        """
        context = super().get_context_data(**kwargs)

        # Add the filter form
        context['form'] = self.filter_form

        # Add filter_params for backward compatibility with existing template
        context['filter_params'] = self.filter_form.cleaned_data

        # Add filter query string for pagination links
        context['filter_query_string'] = self._build_filter_query_string(self.filter_form, exclude_page=True)

        # Add dropdown options (still needed for custom rendering)
        context['restaurant_options'] = self._get_restaurant_options()
        context['tag_options'] = self._get_tag_options()

        return context
