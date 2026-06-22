from django import forms
from content.models import Restaurant, RestaurantDish


class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'street_address', 'city', 'province', 'country', 'postal_code', 'visited', 'google_place_id', 'is_pop_up', 'website']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Restaurant name'}),
            'google_place_id': forms.HiddenInput(),
            'street_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province / State'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal code'}),
            'visited': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_pop_up': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_pop_up') and not cleaned_data.get('website'):
            self.add_error('website', 'Website is required for pop-up restaurants.')
        return cleaned_data


class RestaurantDishForm(forms.ModelForm):
    class Meta:
        model = RestaurantDish
        fields = ['dish_name', 'status', 'source', 'source_detail', 'notes']
        widgets = {
            'dish_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dish name'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. friend, article, Instagram'}),
            'source_detail': forms.TextInput(attrs={'class': 'form-control', 'type': 'url', 'placeholder': 'Link (optional, e.g. Instagram URL)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}),
        }


class RestaurantDishInlineForm(forms.ModelForm):
    """Stripped-down form for inline dish entry in the create form (status set server-side)."""
    class Meta:
        model = RestaurantDish
        fields = ['dish_name', 'source', 'source_detail', 'notes']
        widgets = {
            'dish_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Dish name'}),
            'source': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'e.g. friend, article'}),
            'source_detail': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'type': 'url', 'placeholder': 'Link (optional)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Notes (optional)'}),
        }
