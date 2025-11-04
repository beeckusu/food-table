from django import forms


class ReviewFilterForm(forms.Form):
    """
    Form for filtering and sorting reviews on the review list page.
    """
    # Text search filter
    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'search',
            'placeholder': 'Search reviews...'
        })
    )

    # Rating range filters
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

    # Date range filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'date_from'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'date_to'})
    )

    # Restaurant name filter
    restaurant = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'restaurant'})
    )

    # Tag filter (multi-select)
    tags = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    # Sort parameter
    SORT_CHOICES = [
        ('date_desc', 'Date: Newest First'),
        ('date_asc', 'Date: Oldest First'),
        ('rating_desc', 'Rating: High to Low'),
        ('rating_asc', 'Rating: Low to High'),
        ('name_asc', 'Restaurant: A-Z'),
        ('name_desc', 'Restaurant: Z-A'),
    ]

    SORT_CHOICES_WITH_RELEVANCE = [
        ('relevance', 'Relevance'),
    ] + SORT_CHOICES
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

    def __init__(self, *args, restaurant_choices=None, tag_choices=None, **kwargs):
        """
        Initialize form with dynamic choices for restaurant and tags.

        Args:
            restaurant_choices: List of (value, label) tuples for restaurant dropdown
            tag_choices: List of (value, label) tuples for tag checkboxes
        """
        super().__init__(*args, **kwargs)

        # Set restaurant choices
        if restaurant_choices:
            self.fields['restaurant'].widget = forms.Select(
                choices=[('', 'All Restaurants')] + restaurant_choices,
                attrs={'class': 'form-select', 'id': 'restaurant'}
            )

        # Set tag choices
        if tag_choices:
            self.fields['tags'].choices = tag_choices

        # Add relevance sort option if search is active
        if self.data and self.data.get('search'):
            self.fields['sort'].choices = self.SORT_CHOICES_WITH_RELEVANCE
            # Default to relevance when searching
            if not self.data.get('sort'):
                self.initial['sort'] = 'relevance'

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

        return cleaned_data
