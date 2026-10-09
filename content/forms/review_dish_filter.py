from django import forms


class ReviewDishFilterForm(forms.Form):
    """
    Form for filtering and sorting review dishes on the review dish list page.
    """
    # Which dishes to list: ones tried in reviews, or anticipated (wishlist) ones
    DISH_KIND_TRIED = 'tried'
    DISH_KIND_ANTICIPATED = 'anticipated'
    DISH_KIND_CHOICES = [
        (DISH_KIND_TRIED, 'Tried'),
        (DISH_KIND_ANTICIPATED, 'Anticipated'),
    ]
    dish_kind = forms.ChoiceField(
        required=False,
        choices=DISH_KIND_CHOICES,
        initial=DISH_KIND_TRIED,
        widget=forms.HiddenInput(attrs={'id': 'dish_kind'})
    )

    # Filters that only make sense for tried dishes (anticipated dishes have
    # no rating, cost, or visit date)
    TRIED_ONLY_FIELDS = ['rating_min', 'rating_max', 'cost_min', 'cost_max', 'date_from', 'date_to']

    # ...and the reverse: only anticipated dishes have an excitement score
    ANTICIPATED_ONLY_FIELDS = ['excitement_status']

    # Text search filter - searches across dish name and encyclopedia name
    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'search',
            'placeholder': 'Search dishes...'
        })
    )

    # Restaurant search filter - searches restaurant names
    restaurant_search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'restaurant_search',
            'placeholder': 'Search restaurants...'
        })
    )

    # Link status filter - whether dish is linked to encyclopedia
    LINK_STATUS_CHOICES = [
        ('all', 'All Dishes'),
        ('linked', 'Linked to Encyclopedia'),
        ('unlinked', 'Not Linked'),
    ]
    link_status = forms.ChoiceField(
        required=False,
        choices=LINK_STATUS_CHOICES,
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'link_status'
        })
    )

    # Excitement status filter (anticipated dishes only) - find dishes still to rate
    EXCITEMENT_STATUS_CHOICES = [
        ('all', 'All Dishes'),
        ('rated', 'Rated'),
        ('unrated', 'Not Rated Yet'),
    ]
    excitement_status = forms.ChoiceField(
        required=False,
        choices=EXCITEMENT_STATUS_CHOICES,
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'excitement_status'
        })
    )

    # Dish rating range filters
    rating_min = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.HiddenInput(attrs={'id': 'rating_min'})
    )
    rating_max = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.HiddenInput(attrs={'id': 'rating_max'})
    )

    # Cost range filters
    cost_min = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=8,
        decimal_places=2,
        widget=forms.HiddenInput(attrs={'id': 'cost_min'})
    )
    cost_max = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=8,
        decimal_places=2,
        widget=forms.HiddenInput(attrs={'id': 'cost_max'})
    )

    # Date range filters (for review visit date)
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'date_from'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'date_to'})
    )

    # Sort parameter
    SORT_CHOICES = [
        ('date_desc', 'Date: Newest First'),
        ('date_asc', 'Date: Oldest First'),
        ('rating_desc', 'Dish Rating: High to Low'),
        ('rating_asc', 'Dish Rating: Low to High'),
        ('cost_desc', 'Cost: High to Low'),
        ('cost_asc', 'Cost: Low to High'),
        ('name_asc', 'Dish Name: A-Z'),
        ('name_desc', 'Dish Name: Z-A'),
        ('restaurant_asc', 'Restaurant: A-Z'),
        ('restaurant_desc', 'Restaurant: Z-A'),
        ('link_asc', 'Encyclopedia Link: A-Z'),
        ('link_desc', 'Encyclopedia Link: Z-A'),
        ('excitement_desc', 'Excitement: High to Low'),
        ('excitement_asc', 'Excitement: Low to High'),
    ]

    sort = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='date_desc',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'sort',
            'onchange': 'document.getElementById("filterForm").submit()'
        })
    )

    def clean(self):
        """
        Validate form data and ensure logical consistency.
        """
        cleaned_data = super().clean()

        # Ensure date_from is not after date_to
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Start date must be before end date.')

        # Ensure rating_min is not greater than rating_max
        rating_min = cleaned_data.get('rating_min')
        rating_max = cleaned_data.get('rating_max')
        if rating_min is not None and rating_max is not None and rating_min > rating_max:
            raise forms.ValidationError('Minimum rating must be less than or equal to maximum rating.')

        # Ensure cost_min is not greater than cost_max
        cost_min = cleaned_data.get('cost_min')
        cost_max = cleaned_data.get('cost_max')
        if cost_min is not None and cost_max is not None and cost_min > cost_max:
            raise forms.ValidationError('Minimum cost must be less than or equal to maximum cost.')

        return cleaned_data
