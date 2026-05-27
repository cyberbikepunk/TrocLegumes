from django import forms

from .models import Farm, FarmProduct


class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ["name", "description", "address", "phone", "logo", "latitude", "longitude"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
        }


class FarmProductForm(forms.ModelForm):
    class Meta:
        model = FarmProduct
        fields = ["name", "crop_category", "description", "default_unit", "default_price", "photo", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "crop_category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "default_unit": forms.Select(attrs={"class": "form-select"}),
            "default_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
