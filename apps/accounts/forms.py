from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "votre@email.com", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"}),
    )


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone")
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+33 6 00 00 00 00"}
            ),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
