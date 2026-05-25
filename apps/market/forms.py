from django import forms

from apps.farms.models import FarmProduct

from .models import Listing


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["farm_product", "quantity_available", "unit", "price_per_unit", "notes"]
        widgets = {
            "farm_product": forms.Select(attrs={"class": "form-select"}),
            "quantity_available": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "price_per_unit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, farm=None, **kwargs):
        super().__init__(*args, **kwargs)
        if farm is not None:
            self.fields["farm_product"].queryset = FarmProduct.objects.filter(
                farm=farm, is_active=True
            ).select_related("crop_category")
        # Pre-fill unit from selected farm_product when editing
        if self.instance.pk and self.instance.farm_product_id:
            self.fields["unit"].initial = self.instance.unit
