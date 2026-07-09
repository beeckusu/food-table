from django import forms
from content.models import FoodFestival


class FoodFestivalForm(forms.ModelForm):
    class Meta:
        model = FoodFestival
        fields = ['name', 'city', 'country', 'start_date', 'end_date', 'website']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Food festival name'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }
