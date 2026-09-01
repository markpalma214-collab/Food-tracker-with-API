from django import forms
from .models import FoodEntry, UserProfile


class FoodEntryForm(forms.ModelForm):
    class Meta:
        model = FoodEntry
        exclude = ['user', 'date']
        widgets = {
            field: forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
            for field in [
                'calories_kcal', 'protein_g', 'fat_g', 'saturated_fat_g',
                'carbs_g', 'fiber_g', 'sugar_g', 'sodium_mg',
                'cholesterol_mg', 'potassium_mg',
            ]
        }
        widgets['food'] = forms.TextInput(attrs={'class': 'form-control'})
        widgets['quantity'] = forms.NumberInput(attrs={'class': 'form-control'})
        widgets['image_url'] = forms.URLInput(attrs={'class': 'form-control'})


class FoodSearchForm(forms.Form):
    """Used by food_create: the user only supplies a name + quantity,
    the nutrition fields are filled in from the Dietly API afterwards."""

    food = forms.CharField(
        max_length=200,
        label="Food",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Greek yogurt'}),
    )
    quantity = forms.IntegerField(
        min_value=1,
        label="Quantity (servings)",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['user']
        widgets = {
            'height_cm': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
        }
