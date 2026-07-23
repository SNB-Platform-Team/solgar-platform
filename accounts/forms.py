"""
accounts app — authentication forms.

Form validation lives here so views stay thin. No raw SQL: the form
delegates credential checking to Django's authenticate(), which uses the ORM.
"""

from django import forms


class LoginForm(forms.Form):
    """Username + password login form with a hidden reCAPTCHA token."""

    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    recaptcha_token = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_username(self) -> str:
        """Strip surrounding whitespace from the submitted username."""
        return self.cleaned_data["username"].strip()