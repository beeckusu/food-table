from django.views.generic import ListView
from django.http import QueryDict
from django.db.models import Q, Case, When, Value, IntegerField
from content.models import ReviewDish
from content.forms import ReviewDishFilterForm


class ReviewDishListView(ListView):
    """
    List view for review dishes.
    Shows all dishes from public reviews with filtering, sorting, and search.
    Supports comprehensive filtering via URL parameters.
    """
    model = ReviewDish
    template_name = 'review_dish/list.html'
    context_object_name = 'review_dishes'
    paginate_by = 50

    def _get_filter_form(self):
        """
        Create and validate the filter form.

        Returns:
            ReviewDishFilterForm: Validated form instance
        """
        # Get GET data - use None if empty to create unbound form
        get_data = self.request.GET if self.request.GET else None

        # Create form with GET data
        form = ReviewDishFilterForm(get_data)

        # Validate form (will populate cleaned_data)
        # Even if validation fails, cleaned_data will be populated with valid fields
        if form.is_bound:
            form.is_valid()

        # Ensure cleaned_data exists even for unbound forms
        if not hasattr(form, 'cleaned_data'):
            form.cleaned_data = {}

        return form

    def _get_sort_order(self, sort_key, has_search=False):
        """
        Get the order_by fields based on sort parameter.

        Args:
            sort_key: Sort key from form cleaned_data
            has_search: Whether a search query is active

        Returns:
            list: List of field names to pass to order_by()
        """
        # Sort key to Django order_by mapping
        sort_mapping = {
            'rating_desc': ['-dish_rating'],
            'rating_asc': ['dish_rating'],
            'date_desc': ['-review__visit_date', '-review__entry_time'],
            'date_asc': ['review__visit_date', 'review__entry_time'],
            'cost_desc': ['-cost'],
            'cost_asc': ['cost'],
            'name_asc': ['dish_name'],
            'name_desc': ['-dish_name'],
            'restaurant_asc': ['review__restaurant_name'],
            'restaurant_desc': ['-review__restaurant_name'],
            'link_asc': ['encyclopedia_entry__name'],  # Nulls last for asc (unlinked at bottom)
            'link_desc': ['-encyclopedia_entry__name'],  # Nulls first for desc (unlinked at bottom after reversing)
        }

        # Default to newest first
        if not sort_key:
            sort_key = 'date_desc'

        return sort_mapping.get(sort_key, ['-review__visit_date', '-review__entry_time'])

    def _build_filter_query_string(self, form, exclude_page=True, exclude_filters=None):
        """
        Build a query string from form cleaned data.

        Args:
            form: The validated ReviewDishFilterForm instance
            exclude_page: If True, exclude 'page' parameter from query string
            exclude_filters: List of filter keys to exclude from query string

        Returns:
            str: Query string with filter parameters (without leading '?')
        """
        params = QueryDict(mutable=True)
        exclude_filters = exclude_filters or []

        for key, value in form.cleaned_data.items():
            if key in exclude_filters:
                continue
            if value:  # Only include non-empty values
                # Handle special case for encyclopedia_entry ModelChoiceField
                if key == 'encyclopedia_entry':
                    params[key] = str(value.id)
                else:
                    params[key] = str(value)

        # Remove page parameter if requested
        if exclude_page and 'page' in params:
            del params['page']

        query_string = params.urlencode()
        return query_string

    def _get_active_filters(self):
        """
        Generate a list of active filters for badge display.

        Returns:
            list: List of dicts with 'label', 'value', and 'remove_url' keys
        """
        active_filters = []
        cleaned_data = getattr(self.filter_form, 'cleaned_data', {})

        # Dish search filter
        if cleaned_data.get('search'):
            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['search']
            )
            active_filters.append({
                'label': 'Dish Search',
                'value': cleaned_data['search'],
                'remove_url': f"?{remove_url}" if remove_url else "?"
            })

        # Restaurant search filter
        if cleaned_data.get('restaurant_search'):
            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['restaurant_search']
            )
            active_filters.append({
                'label': 'Restaurant',
                'value': cleaned_data['restaurant_search'],
                'remove_url': f"?{remove_url}" if remove_url else "?"
            })

        # Link status filter
        if cleaned_data.get('link_status') and cleaned_data['link_status'] != 'all':
            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['link_status']
            )
            status_display = dict(ReviewDishFilterForm.LINK_STATUS_CHOICES).get(
                cleaned_data['link_status'],
                cleaned_data['link_status']
            )
            active_filters.append({
                'label': 'Link Status',
                'value': status_display,
                'remove_url': f"?{remove_url}" if remove_url else "?"
            })

        # Rating range filter
        rating_min = cleaned_data.get('rating_min')
        rating_max = cleaned_data.get('rating_max')
        if rating_min is not None or rating_max is not None:
            # Only show if different from defaults (0-100)
            if rating_min not in (None, 0) or rating_max not in (None, 100):
                min_val = rating_min if rating_min is not None else 0
                max_val = rating_max if rating_max is not None else 100
                remove_url = self._build_filter_query_string(
                    self.filter_form,
                    exclude_filters=['rating_min', 'rating_max']
                )
                active_filters.append({
                    'label': 'Rating',
                    'value': f"{min_val} - {max_val}",
                    'remove_url': f"?{remove_url}" if remove_url else "?"
                })

        # Cost range filter
        cost_min = cleaned_data.get('cost_min')
        cost_max = cleaned_data.get('cost_max')
        if cost_min is not None or cost_max is not None:
            min_val = f"${cost_min}" if cost_min is not None else "$0"
            max_val = f"${cost_max}" if cost_max is not None else "∞"
            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['cost_min', 'cost_max']
            )
            active_filters.append({
                'label': 'Cost',
                'value': f"{min_val} - {max_val}",
                'remove_url': f"?{remove_url}" if remove_url else "?"
            })

        # Date range filter
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from or date_to:
            if date_from and date_to:
                value = f"{date_from} to {date_to}"
            elif date_from:
                value = f"From {date_from}"
            else:
                value = f"Until {date_to}"

            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['date_from', 'date_to']
            )
            active_filters.append({
                'label': 'Date',
                'value': value,
                'remove_url': f"?{remove_url}" if remove_url else "?"
            })

        # Sort filter (only if not default)
        sort_value = cleaned_data.get('sort')
        if sort_value and sort_value != 'date_desc':
            # Get the display label
            sort_label = dict(self.filter_form.fields['sort'].choices).get(sort_value, sort_value)
            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['sort']
            )
            active_filters.append({
                'label': 'Sort',
                'value': sort_label,
                'remove_url': f"?{remove_url}" if remove_url else "?"
            })

        return active_filters

    def get_queryset(self):
        """
        Return all dishes from public reviews with filtering, sorting, and search.
        Applies filters based on validated form data.
        Optimizes queries with select_related and prefetch_related.
        """
        # Get validated form (store for use in context)
        self.filter_form = self._get_filter_form()

        # Base queryset
        queryset = ReviewDish.objects.filter(
            review__is_private=False
        ).select_related(
            'review',  # Parent review
            'encyclopedia_entry',  # Encyclopedia link (if present)
            'review__created_by'  # Review author
        ).prefetch_related(
            'images'  # Dish images
        )

        # Apply filters from cleaned_data (automatically validated)
        cleaned_data = getattr(self.filter_form, 'cleaned_data', {})

        # Dish search filter - searches dish names and encyclopedia entries
        if cleaned_data.get('search'):
            search_term = cleaned_data['search']
            queryset = queryset.filter(
                Q(dish_name__icontains=search_term) |
                Q(encyclopedia_entry__name__icontains=search_term)
            )

        # Restaurant search filter - searches restaurant names
        if cleaned_data.get('restaurant_search'):
            restaurant_term = cleaned_data['restaurant_search']
            queryset = queryset.filter(
                review__restaurant_name__icontains=restaurant_term
            )

        # Link status filter
        link_status = cleaned_data.get('link_status')
        if link_status == 'linked':
            queryset = queryset.filter(encyclopedia_entry__isnull=False)
        elif link_status == 'unlinked':
            queryset = queryset.filter(encyclopedia_entry__isnull=True)
        # 'all' means no filter

        # Dish rating range filters (validated by form)
        if cleaned_data.get('rating_min') is not None:
            queryset = queryset.filter(dish_rating__gte=cleaned_data['rating_min'])

        if cleaned_data.get('rating_max') is not None:
            queryset = queryset.filter(dish_rating__lte=cleaned_data['rating_max'])

        # Cost range filters (validated by form)
        if cleaned_data.get('cost_min') is not None:
            queryset = queryset.filter(cost__gte=cleaned_data['cost_min'])

        if cleaned_data.get('cost_max') is not None:
            queryset = queryset.filter(cost__lte=cleaned_data['cost_max'])

        # Date range filters (validated by form) - filter by review visit date
        if cleaned_data.get('date_from'):
            queryset = queryset.filter(review__visit_date__gte=cleaned_data['date_from'])

        if cleaned_data.get('date_to'):
            queryset = queryset.filter(review__visit_date__lte=cleaned_data['date_to'])

        # Apply sorting
        has_search = bool(cleaned_data.get('search'))
        sort_key = cleaned_data.get('sort')

        # Special handling for link sorting to ensure unlinked items go to bottom
        if sort_key in ['link_asc', 'link_desc']:
            # Annotate with a field to push nulls to the end
            queryset = queryset.annotate(
                has_link=Case(
                    When(encyclopedia_entry__isnull=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
            if sort_key == 'link_asc':
                # Unlinked last, then sort linked by name ascending
                order_by_fields = ['has_link', 'encyclopedia_entry__name']
            else:  # link_desc
                # Unlinked last, then sort linked by name descending
                order_by_fields = ['has_link', '-encyclopedia_entry__name']
        # Special handling for cost sorting to ensure null costs go to bottom
        elif sort_key in ['cost_asc', 'cost_desc']:
            # Annotate with a field to push nulls to the end
            queryset = queryset.annotate(
                has_cost=Case(
                    When(cost__isnull=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
            if sort_key == 'cost_asc':
                # No cost last, then sort by cost ascending
                order_by_fields = ['has_cost', 'cost']
            else:  # cost_desc
                # No cost last, then sort by cost descending
                order_by_fields = ['has_cost', '-cost']
        else:
            order_by_fields = self._get_sort_order(sort_key, has_search=has_search)

        return queryset.order_by(*order_by_fields)

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

        # Add active filters for badge display
        context['active_filters'] = self._get_active_filters()

        # Add total count for "Showing X of Y" indicator
        context['total_dishes'] = ReviewDish.objects.filter(review__is_private=False).count()

        return context
