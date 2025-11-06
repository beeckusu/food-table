from django import forms
from content.models import Encyclopedia


class ReviewDishFilterForm(forms.Form):
    """
    Form for filtering and sorting review dishes on the review dish list page.
    """
    # Text search filter - searches across dish name, notes, and encyclopedia name
    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'search',
            'placeholder': 'Search dishes...'
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

    # Restaurant name filter
    restaurant = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'restaurant'})
    )

    # Encyclopedia entry filter
    encyclopedia_entry = forms.ModelChoiceField(
        required=False,
        queryset=Encyclopedia.objects.none(),  # Will be populated in __init__
        empty_label='All Encyclopedia Entries',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'encyclopedia_entry'})
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

    def __init__(self, *args, restaurant_choices=None, encyclopedia_choices=None, **kwargs):
        """
        Initialize form with dynamic choices for restaurant and encyclopedia entries.

        Args:
            restaurant_choices: List of (value, label) tuples for restaurant dropdown
            encyclopedia_choices: QuerySet of Encyclopedia objects for encyclopedia dropdown
        """
        super().__init__(*args, **kwargs)

        # Set restaurant choices
        if restaurant_choices:
            self.fields['restaurant'].widget = forms.Select(
                choices=[('', 'All Restaurants')] + restaurant_choices,
                attrs={'class': 'form-select', 'id': 'restaurant'}
            )

        # Set encyclopedia entry choices
        if encyclopedia_choices:
            self.fields['encyclopedia_entry'].queryset = encyclopedia_choices

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

        # Ensure cost_min is not greater than cost_max
        cost_min = cleaned_data.get('cost_min')
        cost_max = cleaned_data.get('cost_max')
        if cost_min is not None and cost_max is not None and cost_min > cost_max:
            raise forms.ValidationError('Minimum cost must be less than or equal to maximum cost.')

        return cleaned_data
