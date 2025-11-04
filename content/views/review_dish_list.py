from django.views.generic import ListView
from django.http import QueryDict
from django.db.models import Count, F, Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from content.models import ReviewDish, Encyclopedia
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
        Create and validate the filter form with dynamic choices.

        Returns:
            ReviewDishFilterForm: Validated form instance
        """
        # Get dynamic choices
        restaurant_choices = [(r, r) for r in self._get_restaurant_options()]
        encyclopedia_choices = self._get_encyclopedia_options()

        # Get GET data - use None if empty to create unbound form
        get_data = self.request.GET if self.request.GET else None

        # Create form with GET data and choices
        form = ReviewDishFilterForm(
            get_data,
            restaurant_choices=restaurant_choices,
            encyclopedia_choices=encyclopedia_choices
        )

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
            'relevance': ['-rank'],  # Only available when search is active
        }

        # Default to relevance when searching, otherwise newest first
        if not sort_key:
            sort_key = 'relevance' if has_search else 'date_desc'

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

        # Search filter
        if cleaned_data.get('search'):
            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['search']
            )
            active_filters.append({
                'label': 'Search',
                'value': cleaned_data['search'],
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

        # Restaurant filter
        if cleaned_data.get('restaurant'):
            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['restaurant']
            )
            active_filters.append({
                'label': 'Restaurant',
                'value': cleaned_data['restaurant'],
                'remove_url': f"?{remove_url}" if remove_url else "?"
            })

        # Encyclopedia entry filter
        if cleaned_data.get('encyclopedia_entry'):
            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['encyclopedia_entry']
            )
            active_filters.append({
                'label': 'Encyclopedia Entry',
                'value': cleaned_data['encyclopedia_entry'].name,
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

        # Photo filter
        if cleaned_data.get('has_photos') is not None:
            remove_url = self._build_filter_query_string(
                self.filter_form,
                exclude_filters=['has_photos']
            )
            value = 'With Photos' if cleaned_data['has_photos'] else 'Without Photos'
            active_filters.append({
                'label': 'Photos',
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

        # Text search filter using PostgreSQL full-text search
        if cleaned_data.get('search'):
            search_query = SearchQuery(cleaned_data['search'])

            # Build search vector from dish_name, notes, and encyclopedia name
            search_vector = SearchVector('dish_name', weight='A')
            search_vector += SearchVector('notes', weight='B')
            search_vector += SearchVector('encyclopedia_entry__name', weight='A')

            queryset = queryset.annotate(
                search_vector_annotated=search_vector,
                rank=SearchRank(F('search_vector_annotated'), search_query)
            ).filter(
                search_vector_annotated=search_query
            )

        # Link status filter
        link_status = cleaned_data.get('link_status')
        if link_status == 'linked':
            queryset = queryset.filter(encyclopedia_entry__isnull=False)
        elif link_status == 'unlinked':
            queryset = queryset.filter(encyclopedia_entry__isnull=True)
        # 'all' means no filter

        # Restaurant filter
        if cleaned_data.get('restaurant'):
            queryset = queryset.filter(review__restaurant_name__iexact=cleaned_data['restaurant'])

        # Encyclopedia entry filter
        if cleaned_data.get('encyclopedia_entry'):
            queryset = queryset.filter(encyclopedia_entry=cleaned_data['encyclopedia_entry'])

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

        # Photo filter
        if cleaned_data.get('has_photos') is not None:
            # Annotate with image count if not already done
            queryset = queryset.annotate(image_count=Count('images'))
            if cleaned_data['has_photos']:
                queryset = queryset.filter(image_count__gt=0)
            else:
                queryset = queryset.filter(image_count=0)

        # Apply sorting
        has_search = bool(cleaned_data.get('search'))
        order_by_fields = self._get_sort_order(cleaned_data.get('sort'), has_search=has_search)
        return queryset.order_by(*order_by_fields)

    def _get_restaurant_options(self):
        """
        Get distinct restaurant names for dropdown.
        Returns sorted list of unique restaurant names from dishes in public reviews.
        """
        restaurants = ReviewDish.objects.filter(
            review__is_private=False
        ).values_list('review__restaurant_name', flat=True).distinct().order_by('review__restaurant_name')

        # Filter out None and empty strings
        return [r for r in restaurants if r]

    def _get_encyclopedia_options(self):
        """
        Get encyclopedia entries that are used in review dishes.
        Returns queryset of Encyclopedia objects ordered by name.
        """
        # Get IDs of encyclopedia entries that are linked to at least one review dish
        used_encyclopedia_ids = ReviewDish.objects.filter(
            review__is_private=False,
            encyclopedia_entry__isnull=False
        ).values_list('encyclopedia_entry_id', flat=True).distinct()

        return Encyclopedia.objects.filter(
            id__in=used_encyclopedia_ids
        ).order_by('name')

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
        context['encyclopedia_options'] = self._get_encyclopedia_options()

        # Add active filters for badge display
        context['active_filters'] = self._get_active_filters()

        # Add total count for "Showing X of Y" indicator
        context['total_dishes'] = ReviewDish.objects.filter(review__is_private=False).count()

        return context
